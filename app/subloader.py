#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers and integrated code from python-saml3 flask demo
#
#  app/subloader.py
#
#   Application to upload srt file and push into mediahaven.
#   It stores and converts an uploaded srt file to webvtt format,
#   shows preview with flowplayer and subtitles.
#   Metadata is fetched with mediahaven_api using a pid.
#   Authorization is done by feching jwt token from oas.viaa.be and passing
#   jwt between forms and pages as 'token'. This token is verified in the
#   authorization.py module, using decorator @requires_authorization
#

import os
import json

from flask import (Flask, request, render_template, session, make_response,
                   redirect, url_for, send_from_directory)

from flask_api import status
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.config import flask_environment
from app.authorization import (get_token, requires_authorization,
                               verify_token, OAS_APPNAME)
from app.mediahaven_api import MediahavenApi
from app.ftp_uploader import FtpUploader
from app.subtitle_files import (save_subtitles, delete_files, save_sidecar_xml,
                                move_subtitle, get_property, not_deleted)
from app.validation import (pid_error, upload_error, validate_input,
                            validate_upload, validate_conversion)

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils


app = Flask(__name__)
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)

app.config.from_object(flask_environment())

# disables caching of srt and other files
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# TODO: replace these with some ENV vars soon:
# app.config['SECRET_KEY'] = 'onelogindemopytoolkit'
app.config['SECRET_KEY'] = 'meemoo_saml_secret_to_be_set_using_configmap_or_secrets'
app.config['SAML_PATH'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'saml'
)


# ======================== SUBLOADER RELATED ROUTES ===========================
@app.route('/', methods=['GET'])
def index():
    logger.info(
        "configuration = ", dictionary={
            'environment': flask_environment()
        })
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    logger.info("POST login =", dictionary={
        'username': username,
        'password': '[FILTERED]'
    })
    token = get_token(username, password)
    if token:
        if verify_token(token['access_token']):
            return redirect(url_for('.search_media', token=token['access_token']))
        else:
            return render_template(
                'index.html',
                validation_errors=f"Login correct, maar geen toegang tot {OAS_APPNAME}"
            )

    else:
        return render_template('index.html', validation_errors='Fout email of wachtwoord')


@app.route('/search_media', methods=['GET'])
@requires_authorization
def search_media():
    token = request.args.get('token')
    validation_errors = request.args.get('validation_errors')
    logger.info('search_media')

    return render_template('search_media.html', **locals())


@app.route('/search_media', methods=['POST'])
@requires_authorization
def post_media():
    token = request.form.get('token')
    pid = request.form.get('pid')
    department = request.form.get('department')

    if not pid:
        return pid_error(token, pid, 'Geef een PID')
    else:
        logger.info('post_media', data={'pid': pid})
        return redirect(url_for('.get_upload', **locals()))


@app.route('/upload', methods=['GET'])
@requires_authorization
def get_upload():
    logger.info('get_upload')

    token = request.args.get('token')
    pid = request.args.get('pid').strip()
    department = request.args.get('department')
    errors = request.args.get('validation_errors')

    validation_error = validate_input(pid, department)
    if validation_error:
        return pid_error(token, pid, validation_error)

    mh_api = MediahavenApi()
    mam_data = mh_api.find_video(department, pid)
    if not mam_data:
        return pid_error(token, pid, f"PID niet gevonden in {department}")

    return render_template(
        'upload.html',
        token=token,
        pid=pid,
        department=department,
        mam_data=json.dumps(mam_data),
        title=mam_data.get('title'),
        description=mam_data.get('description'),
        created=get_property(mam_data, 'CreationDate'),
        archived=get_property(mam_data, 'created_on'),
        original_cp=get_property(mam_data, 'Original_CP'),
        # for v2 mam_data['Internal']['PathToVideo']
        video_url=mam_data.get('videoPath'),
        flowplayer_token=os.environ.get('FLOWPLAYER_TOKEN', 'set_in_secrets'),
        validation_errors=errors)


@app.route('/upload', methods=['POST'])
@requires_authorization
def post_upload():
    tp = {
        'token': request.form.get('token'),
        'pid': request.form.get('pid'),
        'department': request.form.get('department'),
        'mam_data': request.form.get('mam_data'),
        'video_url': request.form.get('video_url'),
        'subtitle_type': request.form.get('subtitle_type')
    }

    validation_error, uploaded_file = validate_upload(tp, request.files)
    if validation_error:
        return upload_error(tp, validation_error)

    tp['subtitle_file'], tp['vtt_file'] = save_subtitles(
        upload_folder(), tp['pid'], uploaded_file)

    conversion_error = validate_conversion(tp)
    if conversion_error:
        return upload_error(tp, conversion_error)

    logger.info('preview', data={
        'pid': tp['pid'],
        'file': tp['subtitle_file']
    })

    video_data = json.loads(tp['mam_data'])
    tp['title'] = video_data.get('title')
    tp['description'] = video_data.get('description')
    tp['created'] = get_property(video_data, 'CreationDate')
    tp['archived'] = get_property(video_data, 'created_on')
    tp['original_cp'] = get_property(video_data, 'Original_CP')
    tp['flowplayer_token'] = os.environ.get(
        'FLOWPLAYER_TOKEN', 'set_in_secrets')

    return render_template('preview.html', **tp)


def upload_folder():
    return os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])


@app.route('/subtitles/<filename>')
def uploaded_subtitles(filename):
    return send_from_directory(upload_folder(), filename)


@app.route('/cancel_upload')
@requires_authorization
def cancel_upload():
    token = request.args.get('token')
    pid = request.args.get('pid')
    department = request.args.get('department')
    vtt_file = request.args.get('vtt_file')
    srt_file = request.args.get('srt_file')

    delete_files(upload_folder(), {
        'srt_file': srt_file,
        'vtt_file': vtt_file
    })

    return redirect(url_for('.get_upload', token=token, pid=pid, department=department))


@app.route('/send_to_mam', methods=['POST'])
@requires_authorization
def send_to_mam():
    tp = {
        'token': request.form.get('token'),
        'pid': request.form.get('pid'),
        'department': request.form.get('department'),
        'subtitle_type': request.form.get('subtitle_type'),
        'srt_file': request.form.get('subtitle_file'),
        'vtt_file': request.form.get('vtt_file'),
        'xml_file': request.form.get('xml_file'),
        'xml_sidecar': request.form.get('xml_sidecar'),
        'mh_response': request.form.get('mh_response'),
        'mam_data': request.form.get('mam_data'),
        'replace_existing': request.form.get('replace_existing'),
        'transfer_method': request.form.get('transfer_method')
    }

    if tp['replace_existing'] == 'cancel':
        # abort and remove temporary files
        delete_files(upload_folder(), tp)

    # extra check to avoid re-sending if user refreshes page
    if not_deleted(upload_folder(), tp['srt_file']):
        metadata = json.loads(tp['mam_data'])
        if not tp['replace_existing']:
            # first request, generate xml_file
            tp['srt_file'] = move_subtitle(upload_folder(), tp)

            tp['xml_file'], tp['xml_sidecar'] = save_sidecar_xml(
                upload_folder(), metadata, tp)

        if tp['transfer_method'] == 'api':
            mh_api = MediahavenApi()
            if tp['replace_existing'] == 'confirm':
                mh_api.delete_old_subtitle(tp['department'], tp['srt_file'])

            mh_response = mh_api.send_subtitles(upload_folder(), metadata, tp)
            logger.info('send_to_mam', data=mh_response)
            tp['mh_response'] = json.dumps(mh_response)

            if not tp['replace_existing'] and (
                (mh_response.get('status') == 409)
                or
                (mh_response.get('status') == 400)
            ):  # duplicate error can give 409 or 400, show dialog
                return render_template('confirm_replace.html', **tp)
        else:
            # upload subtitle and xml sidecar with ftp instead
            ftp_uploader = FtpUploader()
            ftp_response = ftp_uploader.upload_subtitles(
                upload_folder(), metadata, tp)
            tp['mh_response'] = json.dumps(ftp_response)

        # cleanup temp files and show final page with mh request results
        delete_files(upload_folder(), tp)
        return render_template('subtitles_sent.html', **tp)
    else:
        # user refreshed page (tempfiles already deleted),
        # or user chose 'cancel' above. in both cases show
        # subtitles already sent
        tp['upload_cancelled'] = True
        return render_template('subtitles_sent.html', **tp)


# ========================== SAML Authentication ==============================
def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=app.config['SAML_PATH'])
    return auth


def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'script_name': request.path,
        'get_data': request.args.copy(),
        # Uncomment if using ADFS as IdP,
        # https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'post_data': request.form.copy()
    }


@app.route('/saml_login', methods=['GET', 'POST'])
def saml_login():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    if 'sso' in request.args:
        return redirect(auth.login())
        # If AuthNRequest ID need to be stored in order to later validate it, do instead
        # sso_built_url = auth.login()
        # request.session['AuthNRequestID'] = auth.get_last_request_id()
        # return redirect(sso_built_url)
    elif 'sso2' in request.args:
        return_to = '%sattrs/' % request.host_url
        return redirect(auth.login(return_to))
    elif 'slo' in request.args:
        name_id = session_index = name_id_format = name_id_nq = name_id_spnq = None
        if 'samlNameId' in session:
            name_id = session['samlNameId']
        if 'samlSessionIndex' in session:
            session_index = session['samlSessionIndex']
        if 'samlNameIdFormat' in session:
            name_id_format = session['samlNameIdFormat']
        if 'samlNameIdNameQualifier' in session:
            name_id_nq = session['samlNameIdNameQualifier']
        if 'samlNameIdSPNameQualifier' in session:
            name_id_spnq = session['samlNameIdSPNameQualifier']

        return redirect(
            auth.logout(
                name_id=name_id,
                session_index=session_index,
                nq=name_id_nq,
                name_id_format=name_id_format,
                spnq=name_id_spnq
            )
        )
    elif 'acs' in request.args:
        request_id = None
        if 'AuthNRequestID' in session:
            request_id = session['AuthNRequestID']

        auth.process_response(request_id=request_id)
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()
        if len(errors) == 0:
            if 'AuthNRequestID' in session:
                del session['AuthNRequestID']
            session['samlUserdata'] = auth.get_attributes()
            session['samlNameId'] = auth.get_nameid()
            session['samlNameIdFormat'] = auth.get_nameid_format()
            session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
            session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
            session['samlSessionIndex'] = auth.get_session_index()
            self_url = OneLogin_Saml2_Utils.get_self_url(req)
            if 'RelayState' in request.form and self_url != request.form['RelayState']:
                # To avoid 'Open Redirect' attacks, before execute the redirection confirm
                # the value of the request.form['RelayState'] is a trusted URL.
                return redirect(auth.redirect_to(request.form['RelayState']))
        elif auth.get_settings().is_debug_active():
            error_reason = auth.get_last_error_reason()
    elif 'sls' in request.args:
        request_id = None
        if 'LogoutRequestID' in session:
            request_id = session['LogoutRequestID']

        def dscb(): return session.clear()
        url = auth.process_slo(request_id=request_id, delete_session_cb=dscb)
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                # To avoid 'Open Redirect' attacks, before execute the redirection confirm
                # the value of the url is a trusted URL.
                return redirect(url)
            else:
                success_slo = True
        elif auth.get_settings().is_debug_active():
            error_reason = auth.get_last_error_reason()

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    return render_template(
        'saml_login.html',
        errors=errors,
        error_reason=error_reason,
        not_auth_warn=not_auth_warn,
        success_slo=success_slo,
        attributes=attributes,
        paint_logout=paint_logout,
    )


@app.route('/attrs/')
def attrs():
    paint_logout = False
    attributes = False

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    return render_template('attrs.html', paint_logout=paint_logout,
                           attributes=attributes)


@app.route('/metadata/')
def metadata():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    # make_response is needed here to set correct header and response code
    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
    else:
        resp = make_response(', '.join(errors), 500)
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)


# =================== HEALTH CHECK ROUTES AND ERROR HANDLING ==================
@app.route("/health/live")
def liveness_check():
    return "OK", status.HTTP_200_OK


@app.errorhandler(401)
def unauthorized(e):
    return "<h1>401</h1><p>Unauthorized</p>", 401


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>Page not found</p>", 404

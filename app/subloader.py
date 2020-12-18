#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: app/subloader.py
#  description:
#   Application to upload srt file and push into mediahaven.
#   It stores and converts an uploaded srt file to webvtt format,
#   shows preview with flowplayer and subtitles.
#   Metadata is fetched with mediahaven_api using a pid also submitted in a form.
#   Authorization is done by feching jwt token from oas.viaa.be and passing
#   jwt between forms and pages as 'token'. This token is verified in the authorization.py
#   using decorator requires_authorization
#
from flask import (Flask, request, render_template,
                   redirect, url_for, send_from_directory)
from flask_api import status
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.config import flask_environment
from app.authorization import get_token, requires_authorization
from app.mediahaven_api import MediahavenApi
from app.subtitle_files import (save_subtitles, delete_files, save_sidecar_xml,
                                move_subtitle, get_property, not_deleted)
from app.validation import pid_error, upload_error, validate_input

import os
import json
import time


app = Flask(__name__)
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)

app.config.from_object(flask_environment())
# disables caching of srt and other files
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


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
    logger.info("POST login =",
                dictionary={
                    'username': username,
                    'password': '[FILTERED]'
                }
                )
    token = get_token(username, password)
    if token:
        return redirect(url_for('.search_media', token=token['access_token']))
    else:
        return render_template('index.html',
                               validation_errors='Fout email of wachtwoord')


@app.route('/search_media', methods=['GET'])
@requires_authorization
def search_media():
    auth_token = request.args.get('token')
    errors = request.args.get('validation_errors')
    logger.info('search_media')
    return render_template(
        'search_media.html',
        token=auth_token,
        validation_errors=errors)


@app.route('/search_media', methods=['POST'])
@requires_authorization
def post_media():
    auth_token = request.form.get('token')
    pid = request.form.get('pid')
    department = request.form.get('department')

    if not pid:
        return pid_error(auth_token, pid,
                         'Geef een PID')
    else:
        logger.info('post_media', data={'pid': pid})
        return redirect(
            url_for(
                '.get_upload',
                token=auth_token,
                pid=pid,
                department=department))


@app.route('/upload', methods=['GET'])
@requires_authorization
def get_upload():
    logger.info('get_upload')
    auth_token = request.args.get('token')
    pid = request.args.get('pid').strip()
    department = request.args.get('department')
    errors = request.args.get('validation_errors')

    validation_error = validate_input(pid, department)
    if validation_error:
        return pid_error(auth_token, pid, validation_error)

    mh_api = MediahavenApi()
    mam_data = mh_api.find_video(pid, department)
    if not mam_data:
        return pid_error(auth_token, pid,
                         f"PID niet gevonden in {department}")
    return render_template(
        'upload.html',
        token=auth_token,
        pid=pid,
        department=department,
        mam_data=json.dumps(mam_data),
        title=mam_data.get('title'),
        description=mam_data.get('description'),
        created=get_property(mam_data, 'CreationDate'),
        archived=get_property(mam_data, 'created_on'),
        original_cp=get_property(mam_data, 'Original_CP'),
        video_url=mam_data.get('videoPath'),
        # or in v2 mam_data['Internal']['PathToVideo']
        flowplayer_token=os.environ.get('FLOWPLAYER_TOKEN', 'set_in_secrets'),
        validation_errors=errors)


@app.route('/upload', methods=['POST'])
@requires_authorization
def post_upload():
    auth_token = request.form.get('token')
    pid = request.form.get('pid')
    department = request.form.get('department')
    mam_data = request.form.get('mam_data')
    video_url = request.form.get('video_url')
    subtitle_type = request.form.get('subtitle_type')

    if 'subtitle_file' not in request.files:
        return upload_error(auth_token, pid, department,
                            'Geen ondertitels bestand')
    if not pid:
        return upload_error(auth_token, pid, department,
                            f"Foutieve pid {pid}")

    uploaded_file = request.files['subtitle_file']
    if uploaded_file.filename == '':
        return upload_error(auth_token, pid, department,
                            'Geen ondertitels bestand geselecteerd')

    srt_filename, vtt_filename = save_subtitles(
        upload_folder(),
        pid,
        uploaded_file
    )

    if not srt_filename:
        return upload_error(auth_token, pid, department,
                            'Ondertitels moeten in SRT formaat')

    if not vtt_filename:
        return upload_error(auth_token, pid, department,
                            'Kon niet converteren naar webvtt formaat')

    logger.info('preview', data={
        'pid': pid,
        'file': srt_filename
    })
    video_data = json.loads(mam_data)

    return render_template(
        'preview.html',
        token=auth_token,
        pid=pid,
        department=department,
        mam_data=mam_data,
        subtitle_type=subtitle_type,
        subtitle_file=srt_filename,
        vtt_file=vtt_filename,
        video_url=video_url,
        title=video_data.get('title'),
        description=video_data.get('description'),
        created=get_property(video_data, 'CreationDate'),
        archived=get_property(video_data, 'created_on'),
        original_cp=get_property(video_data, 'Original_CP'),
        flowplayer_token=os.environ.get('FLOWPLAYER_TOKEN', 'set_in_secrets')
    )


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

    delete_files(upload_folder(), srt_file, vtt_file)

    return redirect(
        url_for('.get_upload',
                token=token,
                pid=pid,
                department=department
                )
    )


@app.route('/send_to_mam', methods=['POST'])
@requires_authorization
def send_to_mam():
    auth_token = request.form.get('token')
    pid = request.form.get('pid')
    subtitle_type = request.form.get('subtitle_type')
    srt_file = request.form.get('subtitle_file')
    vtt_file = request.form.get('vtt_file')
    xml_file = request.form.get('xml_file')
    xml_sidecar = request.form.get('xml_sidecar')
    mh_response = request.form.get('mh_response')
    mam_data = request.form.get('mam_data')
    replace_existing = request.form.get('replace_existing')

    metadata = json.loads(mam_data)

    if replace_existing == 'cancel':
        # abort and remove temporary files
        delete_files(upload_folder(), srt_file, vtt_file, xml_file)

    # extra check to avoid re-sending if user refreshes page
    if not_deleted(upload_folder(), srt_file):
        # first request, generate xml_file
        if not replace_existing:
            srt_file = move_subtitle(
                upload_folder(),
                srt_file,
                subtitle_type,
                pid
            )

            xml_file, xml_sidecar = save_sidecar_xml(
                upload_folder(),
                metadata,
                pid,
                srt_file,
                subtitle_type
            )

        mh_api = MediahavenApi()
        if replace_existing == 'confirm':
            mh_api.delete_old_subtitle(srt_file)
            time.sleep(0.8)  # allow mam to catch up for send_subtitles call

        mh_response = mh_api.send_subtitles(
            upload_folder(),
            metadata,
            xml_file,
            srt_file,
            subtitle_type
        )

        logger.info('send_to_mam', data={
            'pid': pid,
            'subtitle_type': subtitle_type,
            'srt_file': srt_file,
            'vtt_file': vtt_file,
            'mh_response': mh_response
        })

        if not replace_existing and (
            (mh_response.get('status') == 409)
            or
            (mh_response.get('status') == 400)
        ):  # duplicate error can give 409 or 400, show dialog
            return render_template('confirm_replace.html',
                                   token=auth_token,
                                   pid=pid,
                                   subtitle_type=subtitle_type,
                                   srt_file=srt_file,
                                   xml_file=xml_file,
                                   vtt_file=vtt_file,
                                   xml_sidecar=xml_sidecar,
                                   mh_response=json.dumps(mh_response),
                                   mam_data=mam_data
                                   )

        # cleanup temp files and show final page with mh request results
        delete_files(upload_folder(), srt_file, vtt_file, xml_file)

        return render_template('subtitles_sent.html',
                               token=auth_token,
                               pid=pid,
                               subtitle_type=subtitle_type,
                               srt_file=srt_file,
                               xml_file=xml_file,
                               xml_sidecar=xml_sidecar,
                               mh_response=json.dumps(mh_response),
                               mam_data=mam_data
                               )
    else:
        # user refreshed page (tempfiles already deleted),
        # or user chose 'cancel' above. in both cases show
        # subtitles already sent
        return render_template('subtitles_sent.html',
                               token=auth_token,
                               pid=pid,
                               subtitle_type=subtitle_type,
                               srt_file=srt_file,
                               upload_cancelled=True
                               )


@app.route("/health/live")
def liveness_check():
    return "OK", status.HTTP_200_OK


@app.errorhandler(401)
def unauthorized(e):
    return "<h1>401</h1><p>Unauthorized</p>", 401


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>Page not found</p>", 404

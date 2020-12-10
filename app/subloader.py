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
from app.upload_worker import UploadWorker

from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, send_from_directory)
from flask_api import status
from viaa.configuration import ConfigParser
from viaa.observability import logging
from app.config import flask_environment
from app.authorization import get_token, requires_authorization
from app.mediahaven_api import MediahavenApi

from flask import abort
from werkzeug.utils import secure_filename
import webvtt  # convert srt into webvtt
import os
import json


app = Flask(__name__)
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)

app.config.from_object(flask_environment())


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


def pid_error(token, pid, msg):
    logger.info('search_media', data={'error': msg})
    return redirect(
        url_for(
            '.search_media',
            token=token,
            pid=pid,
            validation_errors=msg
        )
    )


@app.route('/search_media', methods=['POST'])
@requires_authorization
def post_media():
    auth_token = request.form.get('token')
    subtitle_pid = request.form.get('pid')

    if not subtitle_pid:
        return pid_error(auth_token, subtitle_pid,
                         'Geef een PID')
    else:
        logger.info('post_media', data={'pid': subtitle_pid})
        return redirect(
            url_for(
                '.get_upload',
                token=auth_token,
                pid=subtitle_pid))


@app.route('/upload', methods=['GET'])
@requires_authorization
def get_upload():
    logger.info('get_upload')
    auth_token = request.args.get('token')
    pid = request.args.get('pid')
    errors = request.args.get('validation_errors')

    # TODO: pass department here also (testbeeld) and use in find_video call
    mh_api = MediahavenApi()  # session as param is possible here
    mam_data = mh_api.find_video(pid)
    if not mam_data:
        return pid_error(auth_token, pid,
                         'PID niet gevonden in mediahaven')
    return render_template(
        'upload.html',
        token=auth_token,
        pid=pid,
        mam_data=json.dumps(mam_data),
        title=mam_data.get('title'),
        description=mam_data.get('description'),
        created=mh_api.get_property(mam_data, 'CreationDate'),
        archived=mh_api.get_property(mam_data, 'created_on'),
        original_cp=mh_api.get_property(mam_data, 'Original_CP'),
        video_url=mam_data.get('videoPath'),
        # or mam_data['Internal']['PathToVideo']
        validation_errors=errors)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = ['srt', 'SRT']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_error(token, pid, msg):
    logger.info('upload', data={'error': msg, })
    return redirect(
        url_for(
            '.get_upload',
            token=token,
            pid=pid,
            validation_errors=msg
        )
    )


@app.route('/upload', methods=['POST'])
@requires_authorization
def post_upload():
    auth_token = request.form.get('token')
    subtitle_pid = request.form.get('pid')
    # this is mediahaven data prev request
    mam_data = request.form.get('mam_data')
    video_url = request.form.get('video_url')
    subtitle_type = request.form.get('subtitle_type')

    if 'subtitle_file' not in request.files:
        return upload_error(auth_token, subtitle_pid,
                            'Geen ondertitels bestand')

    file = request.files['subtitle_file']
    if file.filename == '':
        return upload_error(auth_token, subtitle_pid,
                            'Geen ondertitels bestand geselecteerd')

    if file and allowed_file(file.filename):
        srt_filename = secure_filename(file.filename)
        vtt_filename = '.'.join(srt_filename.rsplit('.')[:-1]) + '.vtt'

        # save srt and converted vtt file in uploads folder
        upload_folder = os.path.join(
            app.root_path, app.config['UPLOAD_FOLDER'])
        file.save(os.path.join(upload_folder, srt_filename))
        vtt_file = webvtt.from_srt(os.path.join(upload_folder, srt_filename))
        vtt_file.save()

    if not subtitle_pid:
        return upload_error(auth_token, subtitle_pid,
                            f"Foutieve pid {subtitle_pid}")

    if not srt_filename:
        return upload_error(auth_token, subtitle_pid,
                            'Ondertitels moeten in SRT formaat')

    if not vtt_filename:
        return upload_error(auth_token, subtitle_pid,
                            'Kon niet converteren naar webvtt formaat')

    logger.info('post_upload', data={
        'pid': subtitle_pid,
        'file': srt_filename
    })
    video_data = json.loads(mam_data)
    mh_api = MediahavenApi()

    return render_template(
        'post_upload.html',
        token=auth_token,
        pid=subtitle_pid,
        mam_data=mam_data,
        subtitle_type=subtitle_type,
        subtitle_file=srt_filename,
        vtt_file=vtt_filename,
        video_url=video_url,
        title=video_data.get('title'),
        description=video_data.get('description'),
        created=mh_api.get_property(video_data, 'CreationDate'),
        archived=mh_api.get_property(video_data, 'created_on'),
        original_cp=mh_api.get_property(video_data, 'Original_CP'),
    )


@app.route('/subtitles/<filename>')
def uploaded_subtitles(filename):
    upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(upload_folder, filename)


def delete_file(f):
    try:
        sub_tempfile_path = os.path.join(
            app.root_path, app.config['UPLOAD_FOLDER'], f)
        os.unlink(sub_tempfile_path)
    except FileNotFoundError:
        logger.info(f"Warning file not found for deletion {f}")
        pass


@app.route('/cancel_upload')
@requires_authorization
def cancel_upload():
    token = request.args.get('token')
    pid = request.args.get('pid')
    vtt_file = request.args.get('vtt_file')
    srt_file = request.args.get('srt_file')

    delete_file(srt_file)
    delete_file(vtt_file)

    return redirect(
        url_for('.get_upload',
                token=token,
                pid=pid
                )
    )


@app.route('/send_to_mam', methods=['POST'])
@requires_authorization
def send_to_mam():
    auth_token = request.form.get('token')
    subtitle_pid = request.form.get('pid')
    subtitle_type = request.form.get('subtitle_type')
    srt_file = request.form.get('subtitle_file')
    vtt_file = request.form.get('vtt_file')
    # this is mediahaven data prev request
    mam_data = request.form.get('mam_data')
    video_url = request.form.get('video_url')

    # TODO: make mam request here with the original srt file, pid and supply
    # xml or json here

    logger.info('send_to_mam', data={
        'pid': subtitle_pid,
        'subtitle_type': subtitle_type,
        'srt_file': srt_file,
        'vtt_file': vtt_file
    })

    delete_file(srt_file)
    delete_file(vtt_file)

    return render_template(
        'finished.html',
        token=auth_token,
        pid=subtitle_pid,
        subtitle_type=subtitle_type,
        srt_file=srt_file,
        vtt_file=vtt_file,
        mam_data=mam_data,
        video_url=video_url
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

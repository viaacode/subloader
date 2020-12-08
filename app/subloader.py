#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: app/subloader.py
#  description:
#    routes for the api calls and main flask application initialization
#
from app.upload_worker import UploadWorker

from flask import Flask, request, jsonify, render_template, redirect, session, url_for
from flask_api import status
from viaa.configuration import ConfigParser
from viaa.observability import logging
from app.config import flask_environment
from app.authorization import get_token, requires_authorization
from flask import abort
from werkzeug.utils import secure_filename


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

@app.route('/search_media', methods=['POST'])
@requires_authorization
def post_media():
    auth_token = request.form.get('token')
    subtitle_pid = request.form.get('pid')

    if not subtitle_pid:
        logger.info(
            'post_media',
            data={
                'error': 'invalid pid supplied',
                'tok=': auth_token})
        return render_template(
            'search_media.html',
            token=auth_token,
            validation_errors='Geef een correcte pid in')
    else:
        logger.info('post_media', data={'pid': subtitle_pid})
        return redirect(url_for('.get_upload', token=auth_token, pid=subtitle_pid))



@app.route('/upload', methods=['GET'])
@requires_authorization
def get_upload():
    auth_token = request.args.get('token')
    pid = request.args.get('pid')
    errors = request.args.get('validation_errors')
    logger.info('get_upload')
    return render_template(
        'upload.html',
        token=auth_token,
        pid=pid,
        title='title todo',
        description='todo fetch description from mediahaven api here',
        created='some date here',
        archived='archived date',
        original_cp='cp id here',
        validation_errors=errors)


def allowed_file(filename):
    ALLOWED_EXTENSIONS=['srt', 'SRT']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
@requires_authorization
def post_upload():
    auth_token = request.form.get('token')
    subtitle_pid = request.form.get('pid')
    subtitle_filename = request.form.get('subtitle_file')
    subtitle_file = None

    if 'subtitle_file' not in request.files:
        # flash('Ondertitel bestand ontbreekt')
        # return redirect(request.url)
        return redirect(
            url_for(
                '.get_upload', 
                token=auth_token, 
                pid=subtitle_pid,
                validation_errors='Geen ondertitels bestand'
            )
        )


    file = request.files['subtitle_file']
    if file.filename == '':
        return redirect(
            url_for(
                '.get_upload', 
                token=auth_token, 
                pid=subtitle_pid,
                validation_errors='Geen ondertitels bestand geselecteerd'
            )
        )



    if file and allowed_file(file.filename):
        subtitle_file = secure_filename(file.filename)
        # we don't need to actually store it we can read the contents here
        # and supply it later as template data to post_upload.html
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        subtitle_content = file.stream.readlines()
        subtitle_content = '\n'.join([line.decode('utf-8').strip() for line in subtitle_content])

    if not subtitle_pid:
        logger.info(
            'post_upload',
            data={
                'error': 'invalid pid supplied',
                'tok=': auth_token
            }
        )
        return render_template(
            'upload.html',
            token=auth_token,
            subtitle_file=subtitle_file,
            validation_errors='Geef een correcte pid in'
        )
    elif not subtitle_file:
        logger.info(
            'post_upload',
            data={
                'error': 'invalid file supplied',
                'tok=': auth_token})
        return render_template(
            'upload.html',
            token=auth_token,
            pid=subtitle_pid,
            subtitle_file='',
            validation_errors='Kies een correct ondertitels bestand'
        )
    else:
        logger.info('post_upload', data={'pid': subtitle_pid, 'file': subtitle_file})
        return render_template(
            'post_upload.html', 
            pid=subtitle_pid, 
            subtitle_file=subtitle_file,
            subtitle_content=subtitle_content
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

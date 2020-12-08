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
        return redirect(url_for('.get_upload', token=token['access_token']))
    else:
        return render_template('index.html',
                               validation_errors='Fout email of wachtwoord')


@app.route('/upload', methods=['GET'])
@requires_authorization
def get_upload():
    auth_token = request.args.get('token')
    errors = request.args.get('validation_errors')
    logger.info('get_upload')
    return render_template(
        'upload.html',
        token=auth_token,
        validation_errors=errors)


@app.route('/upload', methods=['POST'])
@requires_authorization
def post_upload():
    auth_token = request.form.get('token')
    subtitle_pid = request.form.get('pid')

    if not subtitle_pid:
        logger.info(
            'post_upload',
            data={
                'error': 'invalid pid supplied',
                'tok=': auth_token})
        # return redirect(url_for('.get_upload', token=auth_token,
        # validation_errors='Error you must supply pid'))
        return render_template(
            'upload.html',
            token=auth_token,
            validation_errors='Geef een correcte pid in')
    else:
        logger.info('post_upload', data={'pid': subtitle_pid})
        return render_template('post_upload.html', pid=subtitle_pid)


@app.route("/health/live")
def liveness_check():
    return "OK", status.HTTP_200_OK


@app.errorhandler(401)
def unauthorized(e):
    return "<h1>401</h1><p>Unauthorized</p>", 401


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>Page not found</p>", 404

# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: app/config.py
#  description: database connection and flags per environment

import os


def flask_environment():
    env = os.environ.get('FLASK_ENV', 'DEVELOPMENT')
    configs = {
        'TESTING': 'app.config.TestConfig',
        'DEVELOPMENT': 'app.config.DevConfig',
        'PRODUCTION': 'app.config.PrdConfig',
    }

    return configs[env]


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'somesecret_key_here234232425223faifaf'
    JOBS_PER_PAGE = 50
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'postgresql://postgres@localhost:5432/syncrator_dev')
    API_KEY = os.environ.get('API_KEY', 'secret123')


class PrdConfig(Config):
    DEBUG = False


class DevConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite://')
    DEVELOPMENT = True
    DEBUG = True

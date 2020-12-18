# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/test_authorization.py
#
import pytest
import os

from app.subloader import app
from app.authorization import verify_token
from .fixtures import jwt_token
from werkzeug.exceptions import Unauthorized

pytestmark = [pytest.mark.vcr(ignore_localhost=True)]


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "record_mode": "once",
        "filter_headers": ["authorization"]
    }


def test_jwt():
    with app.app_context():
        verify_token(jwt_token())


def test_bad_jwt():
    with app.app_context():
        with pytest.raises(Unauthorized):
            verify_token("somethingwrong")


def test_token_signature_bad_decode():
    app.config['TESTING'] = True
    with app.app_context():
        with pytest.raises(Unauthorized):
            os.environ['OAS_JWT_SECRET'] = 'testkey'
            verify_token("Bearer aabbcc")


@pytest.mark.vcr
def test_wrong_credentials(client):
    res = client.post('/login', data=dict(
        username='avo-syncrator',
        password='wrong_pass',
    ), follow_redirects=True)

    assert 'Fout email of wachtwoord' in res.data.decode()


@pytest.mark.vcr
def test_right_credentials(client):
    res = client.post('/login', data=dict(
        username='avo-syncrator',
        password='correct_pass',
    ), follow_redirects=True)

    assert 'Fout email of wachtwoord' not in res.data.decode()

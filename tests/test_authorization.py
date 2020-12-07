# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/test_authorization.py
#
import pytest
import os
import tempfile

from app.syncrator_api import app
from app.authorization import verify_token
from .fixtures import jwt_token
from werkzeug.exceptions import Unauthorized


pytestmark = [pytest.mark.vcr(ignore_localhost=True)]


@pytest.fixture(scope="module")
def vcr_config():
    # return {"record_mode": "all"} #do new record, requires vpn connection
    return {"record_mode": "once"}


def test_jwt():
    assert verify_token(jwt_token())


def test_bad_jwt():
    assert not verify_token("somethingwrong")


def test_token_signature_bad_decode():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    with app.app_context():
        with pytest.raises(Unauthorized):
            os.environ['OAS_JWT_SECRET'] = 'testkey'
            verify_token("Bearer aabbcc")


def test_token_signature():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    with app.app_context():
        os.environ['OAS_JWT_SECRET'] = 'testkey'
        res = verify_token(jwt_token())
        assert res


@pytest.mark.vcr
def test_wrong_credentials(client):
    res = client.post('/login', data=dict(
        username='avo-syncrator',
        password='wrong_pass',
    ), follow_redirects=True)

    # login_data = res.get_json()
    assert res.status_code == 401


@pytest.mark.vcr
def test_right_credentials(client):
    res = client.post('/login', data=dict(
        username='avo-syncrator',
        password='correct_pass',
    ), follow_redirects=True)

    login_data = res.get_json()
    assert res.status_code == 200
    assert 'access_token' in login_data
    assert login_data['expires_in'] == 900

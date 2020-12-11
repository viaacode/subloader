# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/test_app.py
#
import pytest

from flask_api import status
from app.subloader import app
from .fixtures import jwt_token


@pytest.fixture(scope="module")
def setup():
    app.config['TESTING'] = True
    yield setup


def test_home(client):
    res = client.get('/')
    assert res.status_code == status.HTTP_200_OK
    assert b'Login' in res.data


def test_liveness_check(client):
    res = client.get('/health/live')

    assert res.data == b'OK'
    assert res.status_code == status.HTTP_200_OK


def test_authchecks(client):
    res = client.get('/search_media')
    assert res.status_code == 401  # unauthorized


def test_random_404(client, setup):
    resp = client.delete('/somepage')
    assert resp.status_code == 404

    resp = client.get('/somepage')
    assert resp.status_code == 404

    resp = client.post('/somepage')
    assert resp.status_code == 404

    resp = client.put('/somepage')
    assert resp.status_code == 404

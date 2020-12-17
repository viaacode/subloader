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


def test_search_media_security(client):
    res = client.get('/search_media')
    assert res.status_code == 401  # unauthorized


def test_search_media(client):
    res = client.get(f"/search_media?token={jwt_token()}")
    assert res.status_code == 200


def test_wrong_pid_entry(client):
    res = client.post("/search_media", data={
        'token': jwt_token(),
        'department': 'testbeeld',
        'pid': 'abc123'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'PID niet gevonden in testbeeld' in res.data.decode()


def test_invalid_pid_entry(client):
    res = client.post("/search_media", data={
        'token': jwt_token(),
        'department': 'testbeeld',
        'pid': 'abc123#'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'PID formaat foutief' in res.data.decode()


def test_working_pid_search(client):
    res = client.post("/search_media", data={
        'token': jwt_token(),
        'department': 'testbeeld',
        'pid': 'qsxs5jbm5c'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'Ondertitelbestand' in res.data.decode()


def test_random_404(client, setup):
    resp = client.delete('/somepage')
    assert resp.status_code == 404

    resp = client.get('/somepage')
    assert resp.status_code == 404

    resp = client.post('/somepage')
    assert resp.status_code == 404

    resp = client.put('/somepage')
    assert resp.status_code == 404

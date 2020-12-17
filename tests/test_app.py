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
import io
import os
import yaml
import json


@pytest.fixture(scope="module")
def setup():
    app.config['TESTING'] = True
    yield setup


@pytest.fixture(scope="module")
def vcr_config():
    # return {"record_mode": "all"} #do new record, requires vpn connection
    return {"record_mode": "once"}


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


def test_invalid_pid_entry(client):
    res = client.post("/search_media", data={
        'token': jwt_token(),
        'department': 'testbeeld',
        'pid': 'abc123#'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'PID formaat foutief' in res.data.decode()


def test_empty_pid(client):
    res = client.post("/search_media", data={
        'token': jwt_token(),
        'department': 'testbeeld',
        'pid': ''
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'Geef een PID' in res.data.decode()


@pytest.mark.vcr
def test_wrong_pid_entry(client):
    res = client.post("/search_media", data={
        'token': jwt_token(),
        'department': 'testbeeld',
        'pid': 'abc123'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'PID niet gevonden in testbeeld' in res.data.decode()


@pytest.mark.vcr
def test_working_pid_search(client):
    res = client.post("/search_media", data={
        'token': jwt_token(),
        'department': 'testbeeld',
        'pid': 'qsxs5jbm5c'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'Ondertitelbestand' in res.data.decode()
    # assert res.data.decode() == ''


@pytest.mark.vcr
def test_bad_srt_upload(client):
    filename = 'subtitles.srt'

    res = client.post("/upload", data={
        'token': jwt_token(),
        'pid': 'qsxs5jbm5c',
        'department': 'testbeeld',
        'mam_data': '',
        'video_url': 'http://somevideopath',
        'subtitle_type': 'closed',
        'subtitle_file': (io.BytesIO(b"some initial data"), filename)
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'Ondertitels moeten in SRT formaat' in res.data.decode()


@pytest.mark.vcr
def test_invalid_upload(client):
    filename = 'somefile.png'

    res = client.post("/upload", data={
        'token': jwt_token(),
        'pid': 'qsxs5jbm5c',
        'department': 'testbeeld',
        'mam_data': '',
        'video_url': 'http://somevideopath',
        'subtitle_type': 'closed',
        'subtitle_file': (io.BytesIO(b"some initial data"), filename)
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'Ondertitels moeten in SRT formaat' in res.data.decode()


@pytest.mark.vcr
def test_empty_upload(client):
    filename = 'somefile.png'

    res = client.post("/upload", data={
        'token': jwt_token(),
        'pid': 'qsxs5jbm5c',
        'department': 'testbeeld',
        'mam_data': '',
        'video_url': 'http://somevideopath',
        'subtitle_type': 'closed',
        'subtitle_file': None
    }, follow_redirects=True)

    assert res.status_code == 200
    assert 'Geen ondertitels bestand' in res.data.decode()


@pytest.mark.vcr
def test_valid_subtitle(client):
    filename = 'testing_good.srt'
    filepath = os.path.join('./tests/test_subs', filename)

    with open('./tests/test_subs/mam_data.yml', "r") as f:
        mam_data = json.loads(yaml.safe_load(f)['response'])

    res = client.post("/upload", data={
        'token': jwt_token(),
        'pid': 'qsxs5jbm5c',
        'department': 'testbeeld',
        'mam_data': json.dumps(mam_data),
        'video_url': 'http://somevideopath',
        'subtitle_type': 'closed',
        'subtitle_file': (open(filepath, 'rb'), filename)
    }, follow_redirects=True)

    assert res.status_code == 200
    assert '<h1>Ondertitelbestand</h1>' in res.data.decode()
    assert 'qsxs5jbm5c' in res.data.decode()
    assert 'qsxs5jbm5c.srt' in res.data.decode()
    assert 'Toevoegen' in res.data.decode()
    assert 'Wissen' in res.data.decode()


@pytest.mark.vcr
def test_valid_subtitle_capitals(client):
    filename = 'test_good2.SRT'
    filepath = os.path.join('./tests/test_subs', filename)

    with open('./tests/test_subs/mam_data.yml', "r") as f:
        mam_data = json.loads(yaml.safe_load(f)['response'])

    res = client.post("/upload", data={
        'token': jwt_token(),
        'pid': 'qsxs5jbm5c',
        'department': 'testbeeld',
        'mam_data': json.dumps(mam_data),
        'video_url': 'http://somevideopath',
        'subtitle_type': 'closed',
        'subtitle_file': (open(filepath, 'rb'), filename)
    }, follow_redirects=True)

    assert res.status_code == 200
    assert '<h1>Ondertitelbestand</h1>' in res.data.decode()
    assert 'qsxs5jbm5c' in res.data.decode()
    assert 'qsxs5jbm5c.srt' in res.data.decode()
    assert 'Toevoegen' in res.data.decode()
    assert 'Wissen' in res.data.decode()


@pytest.mark.vcr
def test_cancel_upload(client):
    data = {
        'token': jwt_token(),
        'pid': 'abc',
        'department': 'testbeeld',
        'srt_file': 'somefile.srt',
        'vtt_file': 'somefile.vtt',
    }
    res = client.get(
        "/cancel_upload",
        query_string=data,
        follow_redirects=True)
    assert res.status_code == 200
    assert 'PID niet gevonden in testbeeld' in res.data.decode()


@pytest.mark.vcr
def test_subtitle_videoplayer_route(client):
    res = client.get('/subtitles/qsxs5jbm5c.vtt')
    assert res.status_code == 200

    # now cancel this upload
    data = {
        'token': jwt_token(),
        'pid': 'qsxs5jbm5c',
        'department': 'testbeeld',
        'srt_file': 'qsxs5jbm5c.srt',
        'vtt_file': 'qsxs5jbm5c.vtt',
    }
    res = client.get(
        "/cancel_upload",
        query_string=data,
        follow_redirects=True)
    assert res.status_code == 200
    assert 'Ondertitelbestand' in res.data.decode()

    res = client.get('/subtitles/qsxs5jbm5c.vtt')
    assert res.status_code == 404  # as now the files should be deleted

# todo test this send_to_mam (most likely we need the above files to be present...
# @pytest.mark.vcr
# def test_send_to_mam(client):
#     with open('./tests/test_subs/mam_data.yml', "r") as f:
#         mam_data = json.loads(yaml.safe_load(f)['response'])
#
#     res = client.post("/upload", data={
#         'token': jwt_token(),
#         'pid': 'qsxs5jbm5c',
#         'department': 'testbeeld',
#         'mam_data': json.dumps(mam_data),
#         'video_url': 'http://somevideopath',
#         'subtitle_type': 'closed',
#         'subtitle_file': (open(filepath, 'rb'), filename)
#     }, follow_redirects=True)
#
#     assert res.status_code == 200
#     assert '<h1>Ondertitelbestand</h1>' in res.data.decode()
#     assert 'qsxs5jbm5c' in res.data.decode()
#     assert 'qsxs5jbm5c.srt' in res.data.decode()
#     assert 'Toevoegen' in res.data.decode()
#     assert 'Wissen' in res.data.decode()


def test_random_404(client, setup):
    resp = client.delete('/somepage')
    assert resp.status_code == 404

    resp = client.get('/somepage')
    assert resp.status_code == 404

    resp = client.post('/somepage')
    assert resp.status_code == 404

    resp = client.put('/somepage')
    assert resp.status_code == 404

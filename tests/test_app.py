# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/test_app.py
#
import warnings
import tempfile
import pytest
import os

from flask_api import status
from app.syncrator_api import app
from app.models import db

from .fixtures import jobs_fixture
from .fixtures import jwt_token
from sqlalchemy import exc as sa_exc

db_fd = None


@pytest.fixture(scope="module")
def setup():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.app_context():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)
            db.create_all()
            jobs_fixture(db)

    yield setup


@pytest.fixture(scope="module")
def teardown():
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def test_home(client):
    res = client.get('/')
    assert res.status_code == status.HTTP_200_OK
    assert b'Syncrator-API' in res.data


def test_liveness_check(client):
    res = client.get('/health/live')

    assert res.data == b'OK'
    assert res.status_code == status.HTTP_200_OK


def test_dryrun_sync_job(client):
    res = client.get('/sync/avo/qas')
    assert res.status_code == status.HTTP_200_OK

    job = res.get_json()
    assert job['ENV'] == 'qas'
    assert job['ACTION'] == 'sync'
    assert job['TARGET'] == 'avo'
    assert job['OPTIONS'] == '-n 1000 -c 1 --api_job_id dryrun'


def test_dryrun_delta_job(client):
    res = client.get('/delta/avo/qas')
    assert res.status_code == status.HTTP_200_OK

    job = res.get_json()
    assert job['ENV'] == 'qas'
    assert job['ACTION'] == 'delta'
    assert job['TARGET'] == 'avo'
    assert job['OPTIONS'] == '-n 1000 -c 1 --api_job_id dryrun'


def test_dryrun_delete_job(client):
    res = client.get('/delete/avo/qas')
    assert res.status_code == status.HTTP_200_OK

    job = res.get_json()
    assert job['ENV'] == 'qas'
    assert job['ACTION'] == 'delete'
    assert job['TARGET'] == 'avo'
    assert job['OPTIONS'] == '--debug --api_job_id dryrun'


def test_diff_job_dryrun(client):
    res = client.get('/diff/avo/qas')
    assert res.status_code == status.HTTP_200_OK

    job = res.get_json()
    assert job['ENV'] == 'qas'
    assert job['ACTION'] == 'diff'
    assert job['TARGET'] == 'avo'
    assert job['OPTIONS'] == '-n 1000 -c 1 --api_job_id dryrun'


def test_password_filter_api_job_nested(client, setup):
    res = client.get('/jobs/2')
    sjob = res.get_json()

    assert res.status_code == 200
    assert 'dbmaster_pass' not in sjob['sync_job']['target_datastore_url']
    assert 'dbmaster' not in sjob['sync_job']['target_datastore_url']


def test_list_api_jobs(client, setup):
    res = client.get('/jobs')

    assert res.status_code == 200
    assert len(res.get_json()) == 3


def test_list_sync_jobs_and_pass_filter(client, setup):
    res = client.get('/sync_jobs')
    sjobs = res.get_json()

    for sjob in sjobs:
        assert 'dbmaster_pass' not in sjob['target_datastore_url']
        assert 'dbmaster' not in sjob['target_datastore_url']

    assert res.status_code == 200
    assert len(sjobs) == 4


def test_get_unknown_job(client, setup):
    res = client.get('/jobs/123')
    assert res.status_code == 404


def test_get_existing_starting_job(client, setup):
    res = client.get('/jobs/1')
    assert res.get_json()['status'] == 'starting'
    assert res.get_json()['sync_id'] is None


def test_get_existing_completed_job(client, setup):
    res = client.get('/jobs/2')
    assert res.get_json()['status'] == 'completed'
    assert res.get_json()['sync_job']['completed']
    assert res.get_json()['sync_job']['data_source'] == 'mam harvester-AvO'


def test_delete_job(client, setup):
    res = client.get('/jobs/3')
    job_before = res.get_json()
    assert res.status_code == 200
    assert job_before['status'] != 'deleted'

    res = client.delete(
        '/jobs/3',
        headers={'Authorization': jwt_token()}
    )
    job_after = res.get_json()
    assert job_after['status'] == 'deleted'


def test_delete_without_token(client, setup):
    resp = client.delete('/jobs/2000')
    assert resp.status_code == 401


def test_delete_unknown_job(client, setup):
    resp = client.delete(
        '/jobs/2000',
        headers={'Authorization': jwt_token()}
    )
    assert resp.status_code == 404


def test_dryrun_matches_templated_get(client):
    res_generic = client.post('/dryrun',
                              json={
                                  'target': 'avo',
                                  'env': 'qas',
                                  'action_name': 'delta',
                                  'action': 'delta',
                                  'is_tag': 'latest',
                                  'options': '-n 1000 -c 1'
                              })
    assert res_generic.status_code == status.HTTP_200_OK
    generic_data = res_generic.get_json()

    res_delta = client.get('/delta/avo/qas')
    assert res_delta.status_code == status.HTTP_200_OK
    delta_data = res_delta.get_json()

    # they are same but env and target ordering is different
    # not much control over this json is non sortable
    assert len(generic_data['result']) == len(delta_data['result'])

    # we verify that all 6 actual params are same
    del generic_data['result']
    del delta_data['result']

    assert generic_data == delta_data


def test_general_job_run_unauthorized(client):
    # test both should give unauthorized if authorization
    # header is missing
    resp = client.post('/run',
                       json={
                           'target': 'avo',
                           'env': 'qas',
                                  'action_name': 'delta',
                                  'action': 'delta',
                                  'is_tag': 'latest',
                                  'options': '-n 1000 -c 1',
                       })
    assert resp.status_code == 401

    res_delta = client.post('/delta/avo/qas')
    assert res_delta.status_code == 401


# test that a generic run call with correct params gives same results
def test_general_job_run(client):
    resp = client.post('/run',
                       headers={'Authorization': jwt_token()},
                       json={
                           'target': 'avo',
                           'env': 'qas',
                                  'action_name': 'delta',
                                  'action': 'delta',
                                  'is_tag': 'latest',
                                  'options': '-n 1000 -c 1',
                       })
    assert resp.status_code == status.HTTP_200_OK
    generic_data = resp.get_json()

    res_delta = client.post(
        '/delta/avo/qas',
        headers={'Authorization': jwt_token()}
    )
    assert res_delta.status_code == status.HTTP_200_OK
    delta_data = res_delta.get_json()

    assert generic_data['ENV'] == delta_data['ENV']
    assert generic_data['TARGET'] == delta_data['TARGET']
    assert generic_data['ACTION'] == delta_data['ACTION']
    assert generic_data['result'] == 'starting'


def test_dryrun_openshift_commands(client, setup):
    resp = client.post('/dryrun',
                       json={
                           'target': 'avo',
                           'env': 'qas',
                                  'action_name': 'delta',
                                  'action': 'delta',
                                  'is_tag': 'latest',
                                  'options': '-n 1000 -c 1',
                       })

    dryrun = resp.get_json()

    assert dryrun['result'] == ' '.join((
        'oc login https://do-prd-okp-m0.do.viaa.be:8443',
        '-p "configure_user" -u "configure_pass"',
        '--insecure-skip-tls-verify > /dev/null ;',
        'oc project shared-components ;',
        'oc delete jobs syncrator-qas-avo-delta ;',
        'oc process -f syncrator-openshift/job_template.yaml',
        '-p TARGET="avo" -p ENV="qas"',
        '-p ACTION_NAME="delta"',
        '-p ACTION="delta"',
        '-p IS_TAG="latest"',
        '-p OPTIONS="-n 1000 -c 1 --api_job_id dryrun" |',
        'oc create -f -'
    ))


def test_random_404(client, setup):
    resp = client.delete('/somepage')
    assert resp.status_code == 404

    resp = client.get('/somepage')
    assert resp.status_code == 404

    resp = client.post('/somepage')
    assert resp.status_code == 404

    resp = client.put('/somepage')
    assert resp.status_code == 404


def test_diff_job_without_token(client):
    res = client.post('/diff/avo/qas')
    assert res.status_code == 401  # unauthorized


def test_diff_job(client):
    res = client.post(
        '/diff/avo/qas',
        headers={'Authorization': jwt_token()}
    )
    assert res.status_code == status.HTTP_200_OK

    job = res.get_json()
    assert job['ENV'] == 'qas'
    assert job['ACTION'] == 'diff'
    assert job['TARGET'] == 'avo'
    assert job['OPTIONS'] == '-n 1000 -c 1 --api_job_id 5'


def test_missing_template(client):
    resp = client.get('/sync/unknownproject/qas')
    assert resp.status_code == 400

    resp = client.get('/delete/unknownproject/qas')
    assert resp.status_code == 400

    resp = client.get('/delta/unknownproject/qas')
    assert resp.status_code == 400

    resp = client.get('/diff/unknownproject/prd')
    assert resp.status_code == 400

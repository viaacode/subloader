# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/fixtures.py
#

def jwt_token():
    oas_qas_token = 'eyJ0eXAiOiJKV1QiLCJraWQiOiIwMDAxIiwiYWxnIjoiSFMyNTY'
    oas_qas_token += 'ifQ.eyJzdWIiOiJjYmI3NzkxMi05MGI0LTEwMzgtOWFiYi00MW'
    oas_qas_token += 'ZiMjBkODA2YTQiLCJtYWlsIjoidGVzdGplc0BtZWVtb28uYmUi'
    oas_qas_token += 'LCJjbiI6IldhbHRlciBTY2hyZXBwZXJzIiwibyI6Ik9SLXJmNW'
    oas_qas_token += 'tmMjUiLCJhdWQiOlsiY2F0YWxvZ3VzcHJvIiwiZ3dfYXBpIiwi'
    oas_qas_token += 'dnBuYXBwbCIsIm1lZGlhaGF2ZW4iXSwiZXhwIjoxNjA3OTU5Mj'
    oas_qas_token += 'YwLCJpc3MiOiJWSUFBIiwianRpIjoiZDQ0NDEwYTMwMTk5YjBk'
    oas_qas_token += 'MDcyOTE3MjQ3MzVkMGEwOWYifQ.n7BV39PqrR8czpcVQpXTaxB'
    oas_qas_token += '0RKoqZ-BJ0B9JE5hns9g'

    return oas_qas_token


def sidecar_v1_output():
    with open('tests/fixture_data/sidecar_v1.xml', 'r') as xmlfile:
        return xmlfile.read()


def sidecar_v2_output():
    with open('tests/fixture_data/sidecar_v2.xml', 'r') as xmlfile:
        return xmlfile.read()


def sub_params():
    return {
        'pid': 'qsf7664p39',
        'subtitle_type': 'closed',
        'srt_file': 'qsf7664p39_closed.srt',
        'vtt_file': 'qsf7664p39.vtt',
        'xml_file': None,
        'xml_sidecar': None,
        'mh_response': None,
        'mam_data': '{}',
        'replace_existing': None,
        'transfer_method': 'ftp'
    }


def sub_meta():
    return {
        'mediaObjectId': '70af6a77d62e42dfa2c87b037458400f5c1943debc864537b24c31a56c38bbec',
        'externalId': 'qsf7664p39',
        'title': 'QAS 20.1 ingest test - Fietsstraten in centrum Gent',
        'description': 'QAS 20.1 ingest test',
        'date': '2019:05:28 09:34:30',
        'originalFileName': 'qsf7664p39.mp4',
        'type': 'Video',
        'authors': [],
        'lastModifiedDate': '2020-10-15T09:29:28Z',
        'archiveDate': '2020-06-19T10:56:45Z',
        'originalStatus': 'completed',
        'archiveStatus': 'on_disk',
        'workflow': 'borndigital',
        'mdProperties': [
            {'value': [{'value': 'qsvx05z57z',
                          'attribute': 'is_verwant_aan',
                          'dottedKey': None}
                       ],
             'attribute': 'dc_relations',
             'dottedKey': None},
            {'value': 'QAS 20.1 ingest test - Fietsstraten in centrum Gent',
             'attribute': 'dc_title',
             'dottedKey': None},
            {'value': 'OR-h41jm06',
             'attribute': 'Original_CP_ID',
             'dottedKey': None},
            {'value': 'qsf7664p39',
             'attribute': 'PID',
             'dottedKey': None},
            {'value': 'testbeeld',
             'attribute': 'CP',
             'dottedKey': None},
            {'value': '2019:05:28 09:34:30',
             'attribute': 'CreationDate',
             'dottedKey': None},
            {'value': 'AVS',
             'attribute': 'Original_CP',
             'dottedKey': None},
            {'value': 'OR-h41jm1d',
             'attribute': 'CP_id',
             'dottedKey': None},
            {'value': 'borndigital',
             'attribute': 'sp_name',
             'dottedKey': None}
        ]
    }

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  lib/mediahaven_api.py
#
#   Make api calls to hetarchief/mediahaven
#   find_video used to lookup video by pid and tenant
#   get_property is easy helper method to iterate mdProperties inside
#   returned data from find_video call.

import os
# import requests
from requests import Session
from viaa.observability.logging import get_logger
# from json.decoder import JSONDecodeError



class MediahavenApi:
    # Voor v2 is endpoint hier /mediahaven-rest-api/v2/resources/
    # en met oauth ipv basic auth
    API_SERVER = os.environ.get(
        'MEDIAHAVEN_API',
        'https://archief-qas.viaa.be/mediahaven-rest-api')
    API_USER = os.environ.get('MEDIAHAVEN_USER', 'apiUser')
    API_PASSWORD = os.environ.get('MEDIAHAVEN_PASS', 'password')

    def __init__(self, session=None):
        self.logger = get_logger()
        if session is None:
            self.session = Session()
        else:
            self.session = session

    # generic get request to mediahaven api
    # example api.get_proxy('/resources/exportlocations/default')
    def get_proxy(self, api_route):
        get_url = f"{self.API_SERVER}{api_route}"
        headers = {
            'Content-Type': 'application/json',
            # TODO: ENABLE THIS FOR FUTURE compatibility
            # 'Accept': 'application/vnd.mediahaven.v2+json'
        }

        response = self.session.get(
            url=get_url,
            headers=headers,
            auth=(self.API_USER, self.API_PASSWORD)
        )

        return response.json()

    def list_objects(self, search='', offset=0, limit=25):
        return self.get_proxy(
            f"/resources/media?q={search}&startIndex={offset}&nrOfResults={limit}")

    def get_object(self, object_id):
        self.get_proxy(f"/resources/media/{object_id}")

    def find_by(self, object_key, value):
        search_matches = self.list_objects(search=f"+({object_key}:{value})")
        return search_matches

    def list_videos(self, department='testbeeld'):
        matched_videos = self.list_objects(
            search=f"%2B(DepartmentName:{department})"
        )
        return matched_videos

    # test pids qsxs5jbm5c, qs5d8ncx8c
    def find_video(self, pid, department='testbeeld'):
        matched_videos = self.list_objects(
            search=f"%2B(DepartmentName:{department})%2B(ExternalId:{pid})"
        )

        if matched_videos.get('totalNrOfResults') == 1:
            return matched_videos.get('mediaDataList', [{}])[0]
        else:
            return None

    def get_property(self, mam_data, attribute):
        props = mam_data.get('mdProperties')
        result = None
        for prop in props:
            if prop.get('attribute') == attribute:
                return prop.get('value')

        return result

    def send_subtitles(self, upload_folder, metadata, xml_file, srt_file):
        send_url = f"{self.API_SERVER}/resources/media/"

        # adding custom headers breaks call and gives 415 error
        # headers = {
        #     'Content-Type': 'application/json',
        #     # 'Accept': 'application/vnd.mediahaven.v2+json'
        # }

        srt_path = os.path.join(upload_folder, srt_file)
        xml_path = os.path.join(upload_folder, xml_file)

        file_fields = {
            'file': (srt_file, open(srt_path, 'rb')),
            'metadata': (xml_file, open(xml_path, 'rb')),
            
        }
        form_fields = {
            'external_id': metadata['externalId'],  # pid
            'departmentId':'dd111b7a-efd0-44e3-8816-0905572421da',
            'autoPublish': 'true'
        }

        response = self.session.post(
            url=send_url,
            # headers=headers, 
            auth=(self.API_USER, self.API_PASSWORD),
            files=file_fields,
            data=form_fields
        )

        return response.json()


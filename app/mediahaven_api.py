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
import requests
from requests import Session
from viaa.observability.logging import get_logger


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
            # 'Accept': 'application/vnd.mediahaven.v2+json' #TODO: ENABLE THIS FOR FUTURE compatibility
        }

        response = self.session.get(
            url=get_url,
            headers=headers,
            auth=(self.API_USER, self.API_PASSWORD)
        )

        return response.json()

    def list_objects(self, search='', offset=0, limit=25):
        return self.get_proxy(
            f"/resources/media/?q={search}&startIndex={offset}&nrOfResults={limit}")

    def get_object(self, object_id):
        get_proxy(f"/resources/media/{object_id}")

    def find_by(self, object_key, value):
        search_matches = self.list_objects(search=f"+({object_key}:{value})")
        return search_matches

    # test pid qsxs5jbm5c
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

    def send_subtitles(self, metadata, xml_file, srt_file, subtitle_type):
        # curl -X POST -u viaa@testbeeld:{password}
        #     -F "file={external_id.srt}"
        #     -F "metadata={external_id.xml}"
        #     -F "externalId={external_id}"
        #     -F "departmentId=dd111b7a-efd0-44e3-8816-0905572421da"
        #     -F "autoPublish=true"
        #     -v https://archief.viaa.be/mediahaven-rest-api/resources/media/
        #     -H "Accept: application/vnd.mediahaven.v2+json"
        print(
            f"send_subtitles : xml_file={xml_file} subtitle_file={srt_file} type={subtitle_type} ",
            flush=True)

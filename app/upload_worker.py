#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: app/upload_worker.py
#  description: upload subtitle file in background
#  right now we just do it inline, this file will most likely be deprecated
#  as it seems the uploading/saving is fast enough
#
import threading


class UploadWorker(threading.Thread):

    def __init__(self, upload_id, upload_params, logger):
        threading.Thread.__init__(self)
        self.upload_id = upload_id
        self.upload_params = upload_params
        self.logger = logger

    def run(self):
        self.logger.info('Uploadworking uploading subtitle file ', data={
            'upload_id': self.upload_id,
            'upload_params': self.upload_params
        })

        result = 'TODO upload file here'

        self.logger.info(
            'UploadWorker done for upload_id={}'.format(
                self.api_job_id
            ),
            data=result
        )

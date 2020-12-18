# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: app/subtitle_files.py
#   description: methods to create temporary srt, vtt and xml files
#   used for sending to mediahaven and streaming in the flowplayer preview.html
#   get_property is easy helper method to iterate mdProperties inside
#   returned data from find_video call.

import os
import webvtt

from werkzeug.utils import secure_filename
from viaa.configuration import ConfigParser
from viaa.observability import logging
from lxml import etree

logger = logging.get_logger(__name__, config=ConfigParser())


def allowed_file(filename):
    ALLOWED_EXTENSIONS = ['srt', 'SRT']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_subtitles(upload_folder, pid, uploaded_file):
    try:
        if uploaded_file and allowed_file(
                secure_filename(uploaded_file.filename)):
            srt_filename = pid + '.srt'
            vtt_filename = pid + '.vtt'

            # save srt and converted vtt file in uploads folder
            uploaded_file.save(os.path.join(upload_folder, srt_filename))
            vtt_file = webvtt.from_srt(
                os.path.join(
                    upload_folder,
                    srt_filename))
            vtt_file.save()

            return srt_filename, vtt_filename
    except webvtt.errors.MalformedFileError as we:
        logger.info(f"Parse error in srt {we}")
    except webvtt.errors.MalformedCaptionError as we:
        logger.info(f"Parse error in srt {we}")

    return None, None


def delete_file(upload_folder, f):
    try:
        if f and len(f) > 3:
            sub_tempfile_path = os.path.join(upload_folder, f)
            os.unlink(sub_tempfile_path)
    except FileNotFoundError:
        logger.info(f"Warning file not found for deletion {f}")
        pass


def delete_files(upload_folder, *files):
    for f in files:
        delete_file(upload_folder, f)


def move_subtitle(upload_folder, srt_file, subtitle_type, pid):
    # moving it from somename.srt into <pid>_open/closed.srt
    new_filename = f"{pid}_{subtitle_type}.srt"
    orig_path = os.path.join(upload_folder, srt_file)
    new_path = os.path.join(upload_folder, new_filename)

    if not os.path.exists(new_path):
        os.rename(orig_path, new_path)
    return new_filename


def not_deleted(upload_folder, f):
    return os.path.exists(
        os.path.join(upload_folder, f)
    )


def get_property(mam_data, attribute):
    props = mam_data.get('mdProperties', [])
    result = None
    for prop in props:
        if prop.get('attribute') == attribute:
            return prop.get('value')

    return result


def save_sidecar_xml(upload_folder, metadata, pid, srt_file, subtitle_type):
    cp_id = get_property(metadata, 'CP_id')
    cp = get_property(metadata, 'CP')

    root = etree.Element("MediaHAVEN_external_metadata")
    etree.SubElement(root, "title").text = f"{srt_file}"

    description = f"Subtitles for item {pid}"
    etree.SubElement(root, "description").text = description

    mdprops = etree.SubElement(root, "MDProperties")
    etree.SubElement(mdprops, "CP").text = cp
    etree.SubElement(mdprops, "CP_id").text = cp_id
    etree.SubElement(mdprops, "PID").text = f"{pid}_{subtitle_type}"
    etree.SubElement(mdprops, "ExternalId").text = f"{pid}"
    relations = etree.SubElement(mdprops, "dc_relations")
    etree.SubElement(relations, "is_verwant_aan").text = f"{pid}"

    xml_data = etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    ).decode()

    # now write data to correct filename
    xml_filename = f"{pid}_{subtitle_type}.xml"
    sf = open(os.path.join(upload_folder, xml_filename), 'w')
    sf.write(xml_data)
    sf.close()

    return xml_filename, xml_data

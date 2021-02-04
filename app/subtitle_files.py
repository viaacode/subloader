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
            srt_path = os.path.join(upload_folder, srt_filename)
            uploaded_file.save(srt_path)

            # convert <br> into newlines
            fsrt = open(srt_path, 'rt')
            content = fsrt.read()
            content = content.replace('<br>', '\n')
            fsrt.close()
            fsrt = open(srt_path, 'wt')
            fsrt.write(content)
            fsrt.close()

            # create vtt file
            vtt_file = webvtt.from_srt(srt_path)
            vtt_file.save()

            return srt_filename, vtt_filename
    except webvtt.errors.MalformedFileError as we:
        logger.info(f"Parse error in srt {we}")
    except webvtt.errors.MalformedCaptionError as we:
        logger.info(f"Parse error in srt {we}")

    return None, None


def not_deleted(upload_folder, f):
    return os.path.exists(os.path.join(upload_folder, f))


def delete_file(upload_folder, f):
    try:
        if f and len(f) > 3:
            sub_tempfile_path = os.path.join(upload_folder, f)
            os.unlink(sub_tempfile_path)
    except FileNotFoundError:
        logger.info(f"Warning file not found for deletion {f}")
        pass


def delete_files(upload_folder, tp):
    if tp.get('srt_file'):
        delete_file(upload_folder, tp['srt_file'])

    if tp.get('vtt_file'):
        delete_file(upload_folder, tp['vtt_file'])

    if tp.get('xml_file'):
        delete_file(upload_folder, tp['xml_file'])


def move_subtitle(upload_folder, tp):
    # moving it from somename.srt into <pid>_open/closed.srt
    new_filename = f"{tp['pid']}_{tp['subtitle_type']}.srt"
    orig_path = os.path.join(upload_folder, tp['srt_file'])
    new_path = os.path.join(upload_folder, new_filename)

    if not os.path.exists(new_path):
        os.rename(orig_path, new_path)
    return new_filename


def get_property(mam_data, attribute):
    props = mam_data.get('mdProperties', [])
    result = None
    for prop in props:
        if prop.get('attribute') == attribute:
            return prop.get('value')

    return result


def save_sidecar_xml_v1(upload_folder, metadata, tp):
    TESTBEELD_PERM_ID = os.environ.get('TESTBEELD_PERM_ID', 'config_testbeeld_uuid')
    ONDERWIJS_PERM_ID = os.environ.get('ONDERWIJS_PERM_ID', 'config_onderwijs_uuid')
    ADMIN_PERM_ID = os.environ.get('ADMIN_PERM_ID', 'config_admin_uuid')

    cp_id = get_property(metadata, 'CP_id')
    cp = get_property(metadata, 'CP')
    xml_pid = f"{tp['pid']}_{tp['subtitle_type']}"

    root = etree.Element("MediaHAVEN_external_metadata")
    etree.SubElement(root, "title").text = tp['srt_file']

    description = f"Subtitles for item {tp['pid']}"
    etree.SubElement(root, "description").text = description

    # rights = etree.SubElement(root, 'RightsManagement')  # of Structural?
    rights = etree.SubElement(root, 'Structural')
    permissions = etree.SubElement(rights, 'Permissions')
    etree.SubElement(permissions, 'Read').text = TESTBEELD_PERM_ID
    etree.SubElement(permissions, 'Read').text = ONDERWIJS_PERM_ID
    etree.SubElement(permissions, 'Read').text = ADMIN_PERM_ID
    etree.SubElement(permissions, 'Write').text = TESTBEELD_PERM_ID
    etree.SubElement(permissions, 'Write').text = ADMIN_PERM_ID
    etree.SubElement(permissions, 'Export').text = TESTBEELD_PERM_ID
    etree.SubElement(permissions, 'Export').text = ADMIN_PERM_ID

    mdprops = etree.SubElement(root, "MDProperties")
    etree.SubElement(mdprops, "sp_name").text = 'borndigital'
    etree.SubElement(mdprops, "CP").text = cp
    etree.SubElement(mdprops, "CP_id").text = cp_id
    etree.SubElement(mdprops, "PID").text = xml_pid
    etree.SubElement(mdprops, "external_id").text = tp['pid']
    relations = etree.SubElement(mdprops, "dc_relations")
    etree.SubElement(relations, "is_verwant_aan").text = tp['pid']

    xml_data = etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    ).decode()

    # now write data to correct filename
    xml_filename = f"{xml_pid}.xml"
    sf = open(os.path.join(upload_folder, xml_filename), 'w')
    sf.write(xml_data)
    sf.close()

    return xml_filename, xml_data


def sidecar_root():
    MH_NS = 'https://zeticon.mediahaven.com/metadata/20.3/mh/'
    MHS_NS = 'https://zeticon.mediahaven.com/metadata/20.3/mhs/'
    XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'  # version="20.3"

    schema_loc = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    zeticon_mhs = 'https://zeticon.mediahaven.com/metadata/20.3/mhs/'
    zeticon_mhs_xsd = 'https://zeticon.mediahaven.com/metadata/20.3/mhs.xsd'
    zeticon_mh = 'https://zeticon.mediahaven.com/metadata/20.3/mh/'
    zeticon_mh_xsd = 'https://zeticon.mediahaven.com/metadata/20.3/mh.xsd'
    XSI_LOC = f"{zeticon_mhs} {zeticon_mhs_xsd} {zeticon_mh} {zeticon_mh_xsd}"

    NSMAP = {
        'mh': MH_NS,
        'mhs': MHS_NS,
        'xsi': XSI_NS
    }

    root = etree.Element(
        "{%s}Sidecar" % MHS_NS,
        {
            'version': '20.3',
            schema_loc: XSI_LOC
        },
        nsmap=NSMAP
    )

    return root, MH_NS, MHS_NS, XSI_NS


def save_sidecar_xml(upload_folder, metadata, tp):
    TESTBEELD_PERM_ID = os.environ.get('TESTBEELD_PERM_ID', 'config_testbeeld_uuid')
    ONDERWIJS_PERM_ID = os.environ.get('ONDERWIJS_PERM_ID', 'config_onderwijs_uuid')
    ADMIN_PERM_ID = os.environ.get('ADMIN_PERM_ID', 'config_admin_uuid')

    cp_id = get_property(metadata, 'CP_id')
    cp = get_property(metadata, 'CP')
    xml_pid = f"{tp['pid']}_{tp['subtitle_type']}"

    root, MH_NS, MHS_NS, XSI_NS = sidecar_root()

    descriptive = etree.SubElement(root, '{%s}Descriptive' % MHS_NS)
    etree.SubElement(descriptive, '{%s}Title' % MH_NS).text = tp['srt_file']
    description = f"Subtitles for item {tp['pid']}"
    etree.SubElement(descriptive, '{%s}Description' % MH_NS).text = description

    rights = etree.SubElement(root, '{%s}RightsManagement' % MHS_NS)  # of Structural?
    permissions = etree.SubElement(rights, '{%s}Permissions' % MH_NS)
    etree.SubElement(permissions, '{%s}Read' % MH_NS).text = TESTBEELD_PERM_ID
    etree.SubElement(permissions, '{%s}Read' % MH_NS).text = ONDERWIJS_PERM_ID
    etree.SubElement(permissions, '{%s}Read' % MH_NS).text = ADMIN_PERM_ID
    etree.SubElement(permissions, '{%s}Write' % MH_NS).text = TESTBEELD_PERM_ID
    etree.SubElement(permissions, '{%s}Write' % MH_NS).text = ADMIN_PERM_ID
    etree.SubElement(permissions, '{%s}Export' % MH_NS).text = TESTBEELD_PERM_ID
    etree.SubElement(permissions, '{%s}Export' % MH_NS).text = ADMIN_PERM_ID

    mdprops = etree.SubElement(root, "{%s}Dynamic" % MHS_NS)
    relations = etree.SubElement(mdprops, "dc_relations")
    etree.SubElement(relations, "is_verwant_aan").text = tp['pid']
    etree.SubElement(mdprops, "CP_id").text = cp_id
    # mediahaven computes external_id for us.
    # etree.SubElement(mdprops, "external_id").text = xml_pid
    etree.SubElement(mdprops, "PID").text = xml_pid
    etree.SubElement(mdprops, "CP").text = cp
    etree.SubElement(mdprops, "sp_name").text = 'borndigital'

    xml_data = etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    ).decode()

    # now write data to correct filename
    xml_filename = f"{xml_pid}.xml"
    sf = open(os.path.join(upload_folder, xml_filename), 'w')
    sf.write(xml_data)
    sf.close()

    return xml_filename, xml_data

# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: app/subtitle_files.py
# description: methods to create temporary srt, vtt and xml files
# used for sending to mediahaven and streaming in the flowplayer preview.html

import os
import webvtt
from werkzeug.utils import secure_filename


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
        print(f"Parse error in srt {we}", flush=True)
    except webvtt.errors.MalformedCaptionError as we:
        print(f"Parse error in srt {we}", flush=True)

    return None, None


def delete_file(upload_folder, f):
    try:
        sub_tempfile_path = os.path.join(upload_folder, f)
        os.unlink(sub_tempfile_path)
    except FileNotFoundError:
        print(f"Warning file not found for deletion {f}", flush=True)
        pass


def move_subtitle(upload_folder, srt_file, subtitle_type, pid):
    # moving it from somename.srt into <pid>_open/closed.srt
    new_filename = f"{pid}_{subtitle_type}.srt"
    orig_path = os.path.join(upload_folder, srt_file)
    new_path = os.path.join(upload_folder, new_filename)

    if not os.path.exists(new_path):
        os.rename(orig_path, new_path)
    return new_filename


def save_sidecar_xml(upload_folder, metadata, pid, srt_file, subtitle_type):
    xml_data = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml_data += '<MediaHAVEN_external_metadata>\n'
    xml_data += f"  <title>{srt_file}</title>\n"
    xml_data += '  <MDProperties>\n'

    # TODO: <!-- CP tenant, default Testbeeld--></CP>  -> kleine letter mag
    # ook, zit ook in metadata req.
    xml_data += '    <CP>testbeeld</CP>\n'

    # TODO: <!-- testbeeld:OR-h41jm1d--></CP_id> -> overnemen uit de metadata
    # in first request.
    xml_data += '    <CP_id>OR-h41jm1d</CP_id>\n'

    xml_data += f"    <PID>{pid}_{subtitle_type}</PID>\n"

    # TODO:
    # xml_data += '    <dc_identifier_localid><!-- lokale id van origineel
    # item, optioneel--></dc_identifier_localid>

    xml_data += '    <dc_relations>\n'
    xml_data += f"      <is_verwant_aan>{pid}</is_verwant_aan>\n"
    xml_data += '    </dc_relations>\n'
    xml_data += '  </MDProperties>\n'
    xml_data += '</MediaHAVEN_external_metadata>\n'

    # now write data to correct filename
    xml_filename = f"{pid}_{subtitle_type}.xml"
    sf = open(os.path.join(upload_folder, xml_filename), 'w')
    sf.write(xml_data)
    sf.close()

    return xml_filename, xml_data
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/test_sidecar.py
#

import pytest
from app.subtitle_files import save_sidecar_xml_v1
from app.subtitle_files import save_sidecar_xml
from .fixtures import sub_params, sub_meta, sidecar_v1_output, sidecar_v2_output

pytestmark = [pytest.mark.vcr(ignore_localhost=True)]


@pytest.fixture(scope="module")
def vcr_config():
    # important to add the filter_headers here to avoid exposing credentials
    # in tests/cassettes!
    return {
        "record_mode": "once",
        "filter_headers": ["authorization"]
    }


def test_sidecar_v1():
    xml_filename, xml_data = save_sidecar_xml_v1("./tests/test_subs", sub_meta(), sub_params())
    assert xml_data == sidecar_v1_output()


def test_sidecar_v2():
    xml_filename, xml_data = save_sidecar_xml("./tests/test_subs", sub_meta(), sub_params())
    assert xml_data == sidecar_v2_output()

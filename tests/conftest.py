# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: tests/conftest.py
#  description: shared fixtures and basic setup, (also look at __init__.py)
#
import pytest
from app.subloader import app


@pytest.fixture(scope='module')
def client():
    testing_client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()

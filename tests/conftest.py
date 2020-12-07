# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  file: tests/conftest.py
#  description: shared fixtures and basic setup, (also look at __init__.py)
#
import pytest
from app.syncrator_api import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

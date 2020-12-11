# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/fixtures.py
#

def jwt_token():
    token = 'Bearer '
    token += "eyJ0eXAiOiJKV1QiLCJraWQiOiIwMDAxIiwiYWxnIjoiSFMyNTYifQ."
    token += "eyJzdWIiOiIzMTU3ZmZlZS0xOWE4LTEwM2EtOGIyMi1jYjA0NDgzM2"
    token += "E4YTMiLCJtYWlsIjoic2NocmVwcGVyc0BnbWFpbC5jb20iLCJjbiI6"
    token += "IldhbHRlciBTY2hyZXBwZXJzIiwibyI6IjEwMDE3IiwiYXVkIjpbIm"
    token += "9yZ2FuaXNhdGlvbl9hcGkiLCJhZG1pbnMiLCJzeW5jcmF0b3IiLCJh"
    token += "dm8iLCJhY2NvdW50LW1hbmFnZXIiLCJoZXRhcmNoaWVmIiwic3luY3"
    token += "JhdG9yLWFwaSJdLCJleHAiOjE2MDQ1MDQzODUsImlzcyI6IlZJQUEi"
    token += "LCJqdGkiOiI3ZGU4MjM1NjM1ZWE0OTA2NTE1ODQxMWE3ZDJiOTk4MC"
    token += "J9.jCDOO3FxGsrMQxXUcTleIdEt2EvMc4eBRmuSnarTEST"

    return token

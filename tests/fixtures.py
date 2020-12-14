# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#  tests/fixtures.py
#

def jwt_token():
    # token = 'Bearer '
    token = 'eyJ0eXAiOiJKV1QiLCJraWQiOiIwMDAxIiwiYWxnIjoiSFMyNTYifQ.eyJzd'
    token += 'WIiOiI1ZTlkODVhOC1iMmZjLTEwM2EtOTI3NS0wZjc1MWJjZWE1ZGQiLCJt'
    token += 'YWlsIjpudWxsLCJjbiI6ImF2by1zeW5jcmF0b3IiLCJvIjpudWxsLCJhdWQ'
    token += 'iOlsic3luY3JhdG9yIl0sImV4cCI6MTYwNzk1MDQwMSwiaXNzIjoiVklBQS'
    token += 'IsImp0aSI6IjZhZGQwOWE2NmFhNjAyMzk1NjcxODc0ZTdhZjQwNTYwIn0.-'
    token += 'rTSQKhJOePutlPXXQ0CwxjBxyurngRstptouc6DcYw'

    return token

# Imports
from flask import Flask, request
# import requests
# import json
# import sys
# import logging
# import os
# import time


IAM_SERVER_STUB_PORT = 20010
IAM_SERVER_STUB_HOST = "localhost"

# IAM Server non-RESTful API endpoints
IAM_MOD_REGISTER_URI = '/auth/v1.5/target'
IAM_REFRESH_TOKEN_URI = '/auth/v1.5/oauth/token'
IAM_TOKEN_VALIDATE_URI = IAM_REFRESH_TOKEN_URI + '/<token>'
IAM_USER_LOGIN_URI = '/auth/v1.5/oauth/login'
IAM_GET_EP_URI = '/auth/v1.5/endpoints'
IAM_TOKEN_REVOKE_URI = '/auth/v1.5/oauth/revoke-token'


iam_server_stub = Flask(__name__)
# As all interfaces are stubbed, no API is truly RESTful sic:(


@iam_server_stub.route(IAM_MOD_REGISTER_URI, methods=['POST'])
def register():
    print request.headers
    print request.get_json()
    return '', 200


@iam_server_stub.route(IAM_REFRESH_TOKEN_URI, methods=['POST'])
def refresh_token():
    print request.headers
    print request
    return '{"access_token": "qwerty", "refresh_token": "poiu", "scope": "RW", "token_type": "Password", "expires_in": "2000"}', 200


@iam_server_stub.route(IAM_TOKEN_VALIDATE_URI, methods=['GET'])
def token_validate(token):
    print request.headers
    print request
    return '{"dummy": "value"}', 200
    # return '{"error_code": "1013", "error_message": "Access Token
    # expired"}', 401


@iam_server_stub.route(IAM_USER_LOGIN_URI, methods=['POST'])
def login():
    print request.headers
    print request.get_json()
    return '{"access_token": "abcd", "refresh_token": "pqrs", "scope": "RW", "token_type": "Password", "expires_in": "10"}', 200


@iam_server_stub.route(IAM_GET_EP_URI, methods=['GET'])
def get_endpoints():
    print request
    print request.headers
    return '{"Mod A": "http://moda"}', 200


@iam_server_stub.route(IAM_TOKEN_REVOKE_URI, methods=['POST'])
def token_revoke():
    print request
    print request.headers
    return '', 200

if __name__ == '__main__':
    iam_server_stub.run(
        host=IAM_SERVER_STUB_HOST, port=IAM_SERVER_STUB_PORT, debug=True, threaded=True)

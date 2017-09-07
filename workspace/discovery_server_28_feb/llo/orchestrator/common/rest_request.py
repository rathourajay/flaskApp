import logging
import requests

import exceptions


"""
Sends a json request using given method and using X-auth-Token and
data as body. If post attempt fails, None will be returned.
"""


def generic_request(method, url, data=None,
                    auth_token=None, nova_cacert=False):
    logging.debug("url:%s, X-Auth-Token:%s, data:%s" % (url, auth_token,
                                                        data))
    headers = {}
    headers["Content-type"] = "application/json"

    if auth_token:
        headers["X-Auth-Token"] = auth_token

    resp = method(url, headers=headers, data=data, verify=nova_cacert)
    logging.debug("Api request return code:%d" % resp.status_code)

    if resp.status_code in [401]:
        resp_body = resp.json()
        raise exceptions.Forbidden(resp_body['error']['message'])

    if resp.status_code in [403]:
        resp_body = resp.json()
        raise exceptions.Unauthorized(resp_body['error']['message'])

    elif resp.status_code not in [200, 201, 203, 204]:
        raise exceptions.RequestFailed(resp.text)
    return resp


def post_request(url, data, auth_token=None):
    return generic_request(requests.post, url, data, auth_token)


def put_request(url, data, auth_token=None):
    return generic_request(requests.put, url, data, auth_token)


def delete_request(url, auth_token=None):
    return generic_request(requests.delete, url, auth_token=auth_token)


def get_request(url, auth_token=None, nova_cacert=False):
    return generic_request(requests.get, url, auth_token=auth_token,
                           nova_cacert=nova_cacert)

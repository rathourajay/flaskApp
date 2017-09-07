'''
Created on Jan 5, 2017

@author: GUR31246
'''
import logging
import json
# import yaml
import os

import exceptions
import rest_request


"""
Gets a keystone usertoken using the credentials provided by user
"""


def get_user_token(user_name, password, tenant_name, auth_url):
    logging.debug('Getting token for user: %s from url: %s'
                  % (user_name, auth_url))

    url = auth_url + '/tokens'

    creds = {
        'auth': {
            'passwordCredentials': {
                'username': user_name,
                'password': password
            },
            'tenantName': tenant_name
        }
    }

    data = json.dumps(creds)
    resp = rest_request.post_request(url, data=data)
    return resp.json()['access']


"""
To get the base url for given service and region
service: compute, network, image, compute_legacy,
         cloudformation, orchestration, identity
region: service region
endpoint_type: adminURL, publicURL, internalURL
"""


def base_url(service, auth_data, region=None):
    endpoint_type = 'publicURL'
    _base_url = None
    for ep in auth_data['serviceCatalog']:
        if ep["type"] == service:
            for _ep in ep['endpoints']:
                if region and _ep['region'] == region:
                    _base_url = _ep.get(endpoint_type)
            if not _base_url:
                # No region matching, use the first
                _base_url = ep['endpoints'][0].get(endpoint_type)
            break
    if _base_url is None:
        raise exceptions.EndpointNotFound(service)
    return _base_url


# def get_provision_cloudlet_data(template):
#     template_dir = os.path.join(
#         os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'template')
#     template_file = 'heat_template.yaml'
#     file = os.path.join(template_dir, template_file)
#     f = open(file, 'r')
#     yml_template = f.read()
#     json_string = json.dumps(yaml.load(yml_template), sort_keys=True, indent=2)
#     json_dict = json.loads(json_string)
#     version = json_dict['heat_template_version']
#     version_str = str(version)
#     date_format = version_str[0:4] + '-' + \
#         version_str[4:6] + '-' + version_str[6:]
#     json_dict['heat_template_version'] = date_format
#     json_string = json.dumps(json_dict)
#     data = {
#         'stack_name': 'test',
#         'environment': template,
#         'template': json_string
#     }
#     prov_data = json.dumps(data)
#     return prov_data


def get_flavor_details(token, flavor_id, auth_url):
    url = auth_url + '/flavors/' + str(flavor_id)
    resp = rest_request.get_request(url, token)
    return resp.json()

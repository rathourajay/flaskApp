'''
Created on Jan 5, 2017

@author: GUR31246
'''
import constants


def get_edge_details(edge_id=None):
    # todo: fetch edge data from central repo
    edge_data = {
        'username': constants.keystone_username,
        'password': constants.keystone_password,
        'auth_url': constants.keystone_url,
        'tenant_name': constants.keystone_tenant
    }
    return edge_data


# update newly created cloudlet ips for the given edge_id
def update_cloudlet_metadata(edge_id, cloudlet_data):
    return('success')


# fetch cloudlet and edge details from Central repository
def fetch_cloudlet_edge_details(cloudlet_id):
    data = {}
    return data


# update cloudlet state
def updated_cloudlet_status(cloudlet_id, status):
    return('success')


def get_endpoint(service):
    # todo: get endpoint from IAM module for specified service
    return 'abc'

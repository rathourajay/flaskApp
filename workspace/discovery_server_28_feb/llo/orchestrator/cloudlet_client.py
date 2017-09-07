#!flask/bin/python

import json
import time
import os
from common import constants
from common import exceptions
from common import management_api
from common import rest_request


def configure_cloudlet(cloudlet_data):
    # todo: call ansible script to instantiate cloudlet controller service on cloudlet
    data = {}
    configure_url = constants.clc_url + constants.configure_cloudlet + cloudlet_data['cloudlet_id']
    resp = rest_request.post_request(configure_url, data=data)
    return(resp)


def unconfigure_cloudlet(cloudlet_id):
    data = management_api.fetch_cloudlet_edge_details(cloudlet_id)
    configure_url = constants.clc_url + constants.unconfigure_cloudlet + cloudlet_id
    resp = rest_request.post_request(configure_url, data=data)
    return("success")

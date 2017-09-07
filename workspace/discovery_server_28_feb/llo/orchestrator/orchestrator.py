from flask import Flask
from flask import request

import base64
import json
import os
import sys
import time
import requests
# import yaml

import cloudlet_client

from common import constants
from common import exceptions
from common import management_api
from common import rest_request
from common import utils
import urllib

MEC_ORCHESTRATOR_PORT = 0xed03

orchestrator = Flask(__name__)


# @orchestrator.route('/api/v1.0/llo/orchestrator/<edge_id>/cloudlet', methods=['POST'])
# def onboard_cloudlet(edge_id):
#     template = request.args.get('template')
#     template_string = base64.b64decode(template)
# #     template_string = json.dumps(
# #         yaml.load(template_string), sort_keys=True, indent=2)
#     edge_details = management_api.get_edge_details(123)
#     try:
#         auth_data = utils.get_user_token(edge_details['username'], edge_details[
#                                          'password'], edge_details['tenant_name'], edge_details['auth_url'])
#         token = auth_data['token']['id']
#         heat_url = utils.base_url('orchestration', auth_data)
#         data = utils.get_provision_cloudlet_data(template_string)
#         rest_request.post_request(
#             heat_url + constants.create_stack, data, auth_token=token)
#         time.sleep(10)
#         stack_list = rest_request.get_request(
#             heat_url + constants.stack_show, token)
#         while True:
#             if stack_list.json()['stack']['stack_status'] != 'CREATE_IN_PROGRESS':
#                 break
#             time.sleep(10)
#             stack_list = rest_request.get_request(
#                 heat_url + constants.stack_show, token)
#
#         if stack_list.json()['stack']['stack_status'] != 'CREATE_COMPLETE':
#             return("Create Failure: " + stack_list.json()['stack']['stack_status_reason'])
#
#         cloudlet_data = {}
#         cloudlet_data['cloudlet_id'] = constants.cloudlet_id
#         cloudlet_data['clusterInfo'] = {}
#
#         nova_url = utils.base_url('compute', auth_data)
#         template_string = json.loads(template_string)
#         i = 1
#         for output in stack_list.json()['stack']['outputs']:
#             instance = "instance" + str(i)
#             cloudlet_data['clusterInfo'][instance] = {}
#             if output['output_key'] == 'controller_ip':
#                 node_type = 'controller'
#             elif output['output_key'] == 'compute_ip':
#                 node_type = 'compute'
#             elif output['output_key'] == 'service_ip':
#                 node_type = 'service'
#             else:
#                 continue
#
#             cloudlet_data['clusterInfo'][instance][
#                 'ip'] = output['output_value']
#             cloudlet_data['clusterInfo'][instance]['role'] = node_type
#             cloudlet_data['clusterInfo'][instance][
#                 'image'] = template_string['parameters']['image_' + node_type]
#             flavor_details = utils.get_flavor_details(
#                 token, template_string['parameters']["flavor_" + node_type], nova_url)
#             cloudlet_data['clusterInfo'][instance][
#                 'ram'] = flavor_details['flavor']['ram']
#             cloudlet_data['clusterInfo'][instance][
#                 'vcpu'] = flavor_details['flavor']['vcpus']
#             cloudlet_data['clusterInfo'][instance][
#                 'disk'] = flavor_details['flavor']['disk']
#
#             i = i + 1
#             conf_resp = cloudlet_client.configure_cloudlet(cloudlet_data)
#     except (exceptions.Forbidden, exceptions.Unauthorized, exceptions.RequestFailed) as e:
#         return("Exception: " + e._error_string)
#     except Exception as e:
#         return(e)
#     endpoints = conf_resp.text
#     cloudlet_data['endpoints'] = endpoints
#     management_api.update_cloudlet_metadata(edge_id, cloudlet_data)
#     return(json.dumps(cloudlet_data))


@orchestrator.route('/api/v1.0/llo/orchestrator/<edge_id>/cloudlet/<cloudlet_id>', methods=['DELETE'])
def terminate_cloudlet(edge_id, cloudlet_id):
    cloudlet_client.unconfigure_cloudlet(cloudlet_id)
    edge_details = management_api.get_edge_details(123)

    try:
        auth_data = utils.get_user_token(edge_details['username'], edge_details[
                                         'password'], edge_details['tenant_name'], edge_details['auth_url'])
    except (exceptions.Forbidden, exceptions.Unauthorized, exceptions.RequestFailed) as e:
        return("Exception: " + e._error_string)
    except Exception as e:
        return("Exception: " + e.args[0])

    token = auth_data['token']['id']
    heat_url = utils.base_url('orchestration', auth_data)

    try:
        stack_list = rest_request.get_request(
            heat_url + constants.stack_show, token)
        stack_id = stack_list.json()['stack']['id']
        rest_request.delete_request(
            heat_url + constants.stack_show + '/' + str(stack_id), token)
    except (exceptions.Forbidden, exceptions.Unauthorized, exceptions.RequestFailed) as e:
        return("Exception: " + e._error_string)
    except Exception as e:
        return("Exception: " + e.args[0])

    try:
        time.sleep(10)
        stack_list = rest_request.get_request(
            heat_url + constants.stack_show, token)
        while True:
            if not stack_list.json() or stack_list.json()['stack']['stack_status'] != 'DELETE_IN_PROGRESS':
                break
            time.sleep(10)
            stack_list = rest_request.get_request(
                heat_url + constants.stack_show, token)
        return("Delete Failure: " + stack_list.json()['stack']['stack_status_reason'])
    except exceptions.RequestFailed:
        management_api.updated_cloudlet_status(cloudlet_id, 'terminated')
        return('Cloudlet terminated successfully')
    except (exceptions.Forbidden, exceptions.Unauthorized) as e:
        return("Exception: " + e._error_string)
    except Exception as e:
        return(e)


@orchestrator.route('/api/v1.0/llo/orchestrator/<edge_id>/images', methods=['GET'])
def list_cloudlet_images(edge_id):
    edge_details = management_api.get_edge_details(123)
    try:
        auth_data = utils.get_user_token(edge_details['username'], edge_details[
                                         'password'], edge_details['tenant_name'], edge_details['auth_url'])
    except (exceptions.Forbidden, exceptions.Unauthorized, exceptions.RequestFailed) as e:
        return("Exception: " + e._error_string)
    except Exception as e:
        return("Exception: " + e.args[0])

    token = auth_data['token']['id']
    glance_url = utils.base_url('image', auth_data)
    try:
        images_list = rest_request.get_request(
            glance_url + constants.list_images, token)
        return(json.dumps(images_list.json()))
    except (exceptions.Forbidden, exceptions.Unauthorized, exceptions.RequestFailed) as e:
        return("Exception: " + e._error_string)
    except Exception as e:
        return(e)


@orchestrator.route('/api/v1.0/llo/orchestrator/<resource_id>/<tenant_id>/stats', methods=['GET'])
def get_vm_stats(resource_id, tenant_id):
    import pdb
    pdb.set_trace()
    start_time = "2017-01-20T09:30:53.744328"
    end_time = "2017-01-20T09:30:54.328041"
    data = {}
#     edge_details = management_api.get_edge_details()
#     try:
#         auth_data = utils.get_user_token(edge_details['username'], edge_details[
#                                          'password'], edge_details['tenant_name'], edge_details['auth_url'])
#     except (exceptions.Forbidden, exceptions.Unauthorized, exceptions.RequestFailed) as e:
#         return("Exception: " + e._error_string)
#     except Exception as e:
#         return(e)
#
#     token = auth_data['token']['id']

    token = u'b946b74ccaef477aa75db651c833d265'

    print "yes"
# curl -g -i -X 'GET'
# 'http://172.19.74.14:8777/v2/meters/cpu_util?q.field=resource_id&q.op=eq&q.type=&q.value=23630fa2-fc21-4a5b-83e0-12e55a858ca8&limit=1'
# -H 'X-Auth-Token: cc82484bc3d549adb4d33d0a7507fb27'


#     query_params = "?q.field=start_timestamp&q.field=end_timestamp&q.op=ge&q.op=le&q.type=datetime&q.type=datetime&q.value=%s&q.value=%s"
#      %(urllib.parse.quote(start_time),urllib.parse.quote(end_time))
    response = rest_request.get_request(
        ceilometer_url + constants.ceilometer_events + query_params, auth_token=token)
# ?q.field=resource_id&q.op=eq&q.type=&q.value=%s&limit=1
    resp = requests.get(
        'http://172.19.74.14:8777/v2/meters/cpu_util?q.field=resource_id&q.op=eq&q.type=&q.value=%s&limit=1' % resource_id, headers={'Authorization': token})
#     ceilometer_url = utils.base_url('metering', auth_data)
#     query_params = "?q.field=start_timestamp&q.field=end_timestamp&q.op=ge&q.op=le&q.type=datetime&q.type=datetime&q.value=%s&q.value=%s" % (
#         urllib.parse.quote(start_time), urllib.parse.quote(end_time))
#     response = rest_request.get_request(
# ceilometer_url + constants.ceilometer_events + query_params,
# auth_token=token)
#     return response.content
    return 'yes'


if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    orchestrator.run(
        host="0.0.0.0", port=MEC_ORCHESTRATOR_PORT, debug=True, threaded=True)

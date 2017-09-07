import requests
import httplib
from flask import Flask, Response
import sys
import logging

MEC_DISCOVERY_SERVER_PORT = 0xed06

MEC_DISCOVERY_AGENT_IP = "0.0.0.0"
MEC_DISCOVERY_AGENT_PORT = 0xed05

discovery_agent = Flask(__name__)


@discovery_agent.route("/api/v1.0/discover/<cloudlet_id>/register", methods=['PUT'])
def init_register_cloudlet(cloudlet_id):
    try:

        url_register = "http://%s:%s/api/v1.0/discover/%s/register" % (
            MEC_DISCOVERY_SERVER_IP, MEC_DISCOVERY_SERVER_PORT, cloudlet_id)
        response = requests.put(url_register)
        if response.status_code == httplib.OK:  # This is 200
            return Response(response="CLOUDLET [%s] REGISTERED" % cloudlet_id)
        elif response.status_code == httplib.NOT_FOUND:
            return Response(response="CLOUDLET [%s] NOT FOUND" % cloudlet_id, status=httplib.NOT_FOUND)
        else:
            return Response(response="ERROR OCCURED IN DISCOVERY_SERVER", status=httplib.INTERNAL_SERVER_ERROR)
    except requests.ConnectionError:
        return Response(response="DISCOVERY_SERVER SERVICE_UNAVAILABLE", status=httplib.SERVICE_UNAVAILABLE)
    except:
        return Response(response="ERROR OCCURED IN DISCOVERY_AGENT", status=httplib.INTERNAL_SERVER_ERROR)


@discovery_agent.route("/api/v1.0/discover/<cloudlet_id>/deregister", methods=['PUT'])
def init_deregister_cloudlet(cloudlet_id):
    try:

        url_deregister = "http://%s:%s/api/v1.0/discover/%s/deregister" % (
            MEC_DISCOVERY_SERVER_IP, MEC_DISCOVERY_SERVER_PORT, cloudlet_id)
        response = requests.put(url_deregister)
        if response.status_code == httplib.OK:  # This is 200
            return Response(
                response="CLOUDLET [%s] DEREGISTERED" % cloudlet_id)
        elif response.status_code == httplib.NOT_FOUND:
            return Response(response="CLOUDLET [%s] NOT FOUND" % cloudlet_id, status=httplib.NOT_FOUND)
        else:
            return Response(
                response="ERROR OCCURED IN DISCOVERY_SERVER", status=httplib.INTERNAL_SERVER_ERROR)
    except:
        return Response(response="DISCOVERY_SERVER SERVICE_UNAVAILABLE", status=httplib.SERVICE_UNAVAILABLE)

#################### END: API Definition ####################

if len(sys.argv) < 2:
    print("Usage: %s <discovery_server_ip>" % sys.argv[0])
    sys.exit(1)

MEC_DISCOVERY_SERVER_IP = sys.argv[1]

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')


discovery_agent.run(host=MEC_DISCOVERY_AGENT_IP, port=0xed05)

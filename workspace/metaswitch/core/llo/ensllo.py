import os, sys
import logging
import json
import threading
import flask, httplib, requests
from flask import Flask, request, Response, jsonify

ENS_LLO_PORT=0xed03
ENS_CLC_PORT=0xed04

llo = Flask(__name__)

class ENSCloudletRegistry:
    def __init__(self, file):
        self.lock = threading.Lock()
        self.file = file
        self.mtime = 0
        self.load_registry()

    def load_registry(self):
        mtime = os.stat(self.file).st_mtime
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.file) as app_file:
                logging.info("Loading cloudlet registry")
                self.registry = json.load(app_file)["cloudlets"]
                logging.debug(json.dumps(self.registry))

    def find_cloudlet(self, cloudlet_id):
        # Refresh the registry
        self.load_registry()

        if cloudlet_id in self.registry:
            return self.registry[cloudlet_id]
        else:
            return None

@llo.route("/api/llo/<developer_id>/<app_id>/<cloudlet_id>", methods=["POST"])
def provision(developer_id, app_id, cloudlet_id):

    cloudlet = registry.find_cloudlet(cloudlet_id)
    if not cloudlet:
        logging.error("Invalid cloudlet_id %s" % cloudlet_id)
        return Response(status=httplib.BAD_REQUEST)

    metadata = request.get_json()

    if metadata == None:
        logging.error("Missing metadata on LLO provision request")
        return Response(status=httplib.BAD_REQUEST)

    r = requests.post("http://%s:%d/api/clc/%s/%s" % (cloudlet_id, ENS_CLC_PORT, developer_id, app_id),
                      headers={"Content-Type": "application/json"},
                      data=json.dumps(metadata))

    if r.status_code == httplib.OK:
        rsp = jsonify(r.json())
        return rsp
    else:
        return Response(status=r.status_code)

@llo.route("/api/llo/<developer_id>/<app_id>/<cloudlet_id>/<uuid>", methods=["DELETE"])
def delete(developer_id, app_id, cloudlet_id, uuid):

    cloudlet = registry.find_cloudlet(cloudlet_id)
    if not cloudlet:
        return Response(status=httplib.BAD_REQUEST)

    r = requests.delete("http://%s:%d/api/clc/%s/%s/%s" % (cloudlet_id, ENS_CLC_PORT, developer_id, app_id, uuid))

    return Response(status=r.status_code)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

# Create the cloudlet registry
registry = ENSCloudletRegistry(sys.argv[1])

# Start the Flask web server (HTTP)
llo.run(host="0.0.0.0", port=ENS_LLO_PORT, threaded=True)

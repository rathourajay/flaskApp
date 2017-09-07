import os
import sys
import json
import logging
import threading
import flask
import httplib
import requests
from flask import Flask, request, Response, jsonify

MEC_CLOUDLET_CATALOG_IP = "0.0.0.0"
MEC_CLOUDLET_CATALOG_PORT = 0xecba

cloudlet_catalog = Flask(__name__)


class CloudletCatalogDB:

    def __init__(self, file, usage_file):
        self.lock = threading.Lock()
        self.file = file
        self.usage_file = usage_file
        self.mtime = 0

        self.load_db()

    def load_db(self):
        mtime = os.stat(self.file).st_mtime
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.file) as app_file:
                logging.info(
                    "Loading application policy database %s" % self.file)
                self.db = json.load(app_file)
                logging.debug(json.dumps(self.db))

    def load_cloudlets(self):
        self.lock.acquire()
        self.load_db()
        self.lock.release()

    def cloudlets(self):
        self.load_cloudlets()
        return self.db

    def update_status(self, cloudlet_id, status):
        self.db['cloudlets'][cloudlet_id]['status'] = status
        with open(self.file, 'w') as app_file:
            json.dump(self.db, app_file)

    def load_usage(self):
        with open(self.usage_file) as usage_file:
            logging.info(
                "Loading application policy database %s" % self.usage_file)
            self.usage_db = json.load(usage_file)
            logging.debug(json.dumps(self.usage_db))
        return self.usage_db


@cloudlet_catalog.route("/api/v1.0/centralrepo/cloudletcatalog/cloudlets", methods=["GET"])
def cloudlets():
    return json.dumps(cc_db.cloudlets())


@cloudlet_catalog.route("/api/v1.0/centralrepo/cloudletcatalog/<cloudlet_id>", methods=["GET"])
def details(cloudlet_id):
    return json.dumps(cc_db.cloudlets()['cloudlets'][cloudlet_id])


@cloudlet_catalog.route("/api/v1.0/centralrepo/cloudletcatalog/<cloudlet_id>", methods=["PUT"])
def update(cloudlet_id):
    try:
        status = request.args.get('status')
        cc_db.update_status(cloudlet_id, status)
        resp = Response(
            response="CLOUDLET UPDATION SUCCESS", status=httplib.OK)
    except:
        resp = Response(
            response="CLOUDLET UPDATION FAILED", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@cloudlet_catalog.route("/api/v1.0/centralrepo/cloudletcatalog/capacity", methods=['GET'])
def capacity():

    try:
        cloudlet_ids = request.args.get('cloudlet_ids')
        cloudlet_ids = eval(cloudlet_ids)
        data = {}
        for cloudlet_id in cloudlet_ids:
            data[cloudlet_id] = cc_db.cloudlets()['cloudlets'][
                cloudlet_id]['resource']

        resp = json.dumps(data)
    except:
        resp = Response(
            response="UNABLE TO FETCH CAPACITY OF CLOUDLETS", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@cloudlet_catalog.route("/api/v1.0/centralrepo/cloudletcatalog/usage", methods=['GET'])
def usage():

    try:
        usage = cc_db.load_usage()['usage']
        cloudlet_ids = request.args.get('cloudlet_ids')
        cloudlet_ids = eval(cloudlet_ids)
        data = {}
        for cloudlet_id in cloudlet_ids:
            data[cloudlet_id] = usage[cloudlet_id]
        resp = json.dumps(data)

    except:
        resp = Response(
            response="UNABLE TO FETCH USAGE OF CLOUDLETS", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


if len(sys.argv) < 3:
    print("Usage: %s <cloudlet_catalog_db> <cloudlet_usage_db>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

cc_db = CloudletCatalogDB(sys.argv[1], sys.argv[2])


# Start the Flask web server (HTTP)
if __name__ == '__main__':
    cloudlet_catalog.run(
        host="0.0.0.0", port=MEC_CLOUDLET_CATALOG_PORT, debug=True, threaded=True)

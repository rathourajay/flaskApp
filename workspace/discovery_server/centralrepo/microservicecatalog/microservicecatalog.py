import os
import sys
import json
import logging
import threading
import flask
import httplib
import requests
from flask import Flask, request, Response, jsonify

MEC_MICROSERVICE_CATALOG_IP = "0.0.0.0"
MEC_MICROSERVICE_CATALOG_PORT = 0xecb9

app_catalog = Flask(__name__)
logging.basicConfig(
    filename='C:/Users/gur40998/workspace/discovery_server/centralrepo/microserviceCatalog/microservicecatalog.log', level=logging.DEBUG)


class MicroserviceCatalogDB:

    def __init__(self, file):
        self.lock = threading.Lock()
        self.file = file
        self.mtime = 0
        self.load_db()

    def load_db(self):
        mtime = os.stat(self.file).st_mtime
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.file) as app_file:
                logging.info(
                    "Loading microservice database %s" % self.file)
                self.db = json.load(app_file)
                logging.debug(json.dumps(self.db))

    def find_microservice(self, microservice_name):
        microservice_data = None
        self.lock.acquire()
        self.load_db()
        for microservice in self.db:
            if microservice["microServiceName"] == microservice_name:
                microservice_data = microservice
                break
        self.lock.release()
        return microservice_data


@app_catalog.route("/api/v1.0/centralrepo/appcatalog/<microservice_name>", methods=["GET"])
def details(microservice_name):
    logging.debug('So should this')
    return json.dumps(microservice_db.find_microservice(microservice_name))


if len(sys.argv) < 2:
    print("Usage: %s <microservice_catalog_db>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

microservice_db = MicroserviceCatalogDB(sys.argv[1])


# Start the Flask web server (HTTP)
if __name__ == '__main__':
    app_catalog.run(
        host="0.0.0.0", port=MEC_MICROSERVICE_CATALOG_PORT, debug=True, threaded=True)

import os
import sys
import json
import logging
import threading
import flask
import httplib
import requests
from flask import Flask, request, Response, jsonify

MEC_APP_CATALOG_IP = "0.0.0.0"
MEC_APP_CATALOG_PORT = 0xecb9

app_catalog = Flask(__name__)
# logging.basicConfig(
# filename='C:/Users/gur40998/workspace/discovery_server/centralrepo/appCatalog/appcatalog.log',
# level=logging.DEBUG)


class ApplicationCatalogDB:

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
                    "Loading application policy database %s" % self.file)
                self.db = json.load(app_file)
                logging.debug(json.dumps(self.db))

    def find_app(self, app_name):
        app_data = None
        self.lock.acquire()
        self.load_db()

        for app in self.db:
            if app["applicationName"] == app_name:
                app_data = app
                break
        self.lock.release()
        return app_data


@app_catalog.route("/api/v1.0/centralrepo/appcatalog/<app_id>", methods=["GET"])
def details(app_id):
    import pdb
    pdb.set_trace()
    #     logging.debug('This message should go to the log file')
    logging.debug('So should this')
#     logging.warning('And this, too')
    return json.dumps(ac_db.find_app(app_id))


@app_catalog.route("/api/v1.0/centralrepo/appcatalog/resource/<app_id>", methods=['GET'])
def resource(app_id):
    try:
        app_resource = ac_db.find_app(app_id)['resources']

        resp = json.dumps(app_resource)
    except:
        resp = Response(
            response="UNABLE TO FETCH APP REQUIREMENT", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


if len(sys.argv) < 2:
    print sys.argv
    print("Usage: %s <app_catalog_db>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

ac_db = ApplicationCatalogDB(sys.argv[1])


# Start the Flask web server (HTTP)
if __name__ == '__main__':
    app_catalog.run(
        host="0.0.0.0", port=MEC_APP_CATALOG_PORT, debug=True, threaded=True)

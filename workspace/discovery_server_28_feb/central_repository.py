import re
import threading
import flask
from flask import Flask, request, Response, jsonify
import csv
import httplib
from httplib import NOT_FOUND
central_repo = Flask(__name__)
import json
import os

CLOUDLET_STATE_CHANGE_SUCCESS = 'success'
CLOUDLET_NOT_FOUND = 'not_found'
CLOUDLET_STATE_CHANGE_FAILURE = 'failure'


@central_repo.route("/api/CR/change_status", methods=['PUT'])
def change_state():
    try:
        cloudlet_id = request.args.get('cloudlet_id')
        status = request.args.get('status')
        print "Cloudlet to Update:", cloudlet_id, "with status: ", status
        new_list = []
        found = False
        with open('cr_db.csv', 'rb') as mycsvfile:

            thedata = csv.reader(mycsvfile)
            for row in thedata:
                if 'cloudlet_id' in row:
                    continue
                else:
                    if row[0] == cloudlet_id:
                        found = True
                        row[3] = status
                new_list.append(row)
        if found:
            with open('cr_db.csv', 'wb') as mycsvfile1:
                thedatawriter = csv.writer(mycsvfile1)
                thedatawriter.writerow(
                    ["cloudlet_id", "lat", "long", "status"])
                for item in new_list:
                    thedatawriter.writerow(item)
            return CLOUDLET_STATE_CHANGE_SUCCESS
        else:
            return Response(response="NOT FOUND", status=httplib.NOT_FOUND)
    except:
        return CLOUDLET_STATE_CHANGE_FAILURE


@central_repo.route("/api/CR/app_requirement/<app>", methods=['GET'])
def app_requirement(app):
    app_requirement = {'RAM': 10, 'CPU': 3, 'DISK': 90}
    app_requirement = json.dumps(app_requirement)
    return app_requirement


@central_repo.route("/api/CR/cloudletsLocation/", methods=['GET'])
def cloudlet_location():

    cloudlet_location = {'cl13': {'lat': 41.507483, 'long': -99.436554},  # NEBRASKA, USA
                         # KANSAS, USA
                         'cl12': {'lat': 38.504048, 'long': -98.315949},
                         # Aricent Tikri
                         'cl14': {'lat': 28.4269, 'long': 77.0321}
                         }
    cloudlet_location = json.dumps(cloudlet_location)
    return cloudlet_location


@central_repo.route("/api/CR/notifyCapacity", methods=['GET'])
def capacity():
    cloudlet_ids = request.args.get('ids')
    cloudlet_ids = eval(cloudlet_ids)
    try:
        capacity = {}
        data = {
            'ens.aws-as-westindia.edgenet.cloud': {'RAM': 30, 'CPU': 10, 'DISK': 200},
            'ens.aws-as-eastindia.edgenet.cloud': {'RAM': 20, 'CPU': 4, 'DISK': 500},
            'ens.aws-us-east.edgenet.cloud': {'RAM': 30, 'CPU': 60, 'DISK': 400},
            'ens.aws-us-west.edgenet.cloud': {'RAM': 60, 'CPU': 20, 'DISK': 600},
            'ens.aws-eu-ireland.edgenet.cloud': {'RAM': 50, 'CPU': 30, 'DISK': 600},
            'ens.aws-eu-frankfurt.edgenet.cloud': {'RAM': 40, 'CPU': 10, 'DISK': 650}
        }

        for c in cloudlet_ids:
            if data[c]:
                capacity[c] = data[c]
                print "capacity", capacity
        resp = json.dumps(capacity)
    except:
        return_status = {'code': 500, 'error': 'internal server error'}
        resp = json.dumps(return_status)
        print "resp1_capacity_LLO2", resp
    return resp


@central_repo.route("/api/CR/notifyUsage", methods=['GET'])
def usage():
    cloudlet_ids = request.args.get('ids')
    cloudlet_ids = eval(cloudlet_ids)
    try:
        usage = {}
        cloudlet_ids = request.args.get('ids')
        cloudlet_ids = eval(cloudlet_ids)
        print "IDs for usage:", cloudlet_ids
        cloudlet_usage = {
            'ens.aws-as-eastindia.edgenet.cloud': {'RAM': 3, 'CPU': 1, 'DISK': 190},
            'ens.aws-as-westindia.edgenet.cloud': {'RAM': 8, 'CPU': 2, 'DISK': 110},
            'ens.aws-us-east.edgenet.cloud': {'RAM': 4, 'CPU': 4, 'DISK': 290},
            'ens.aws-us-west.edgenet.cloud': {'RAM': 3, 'CPU': 2, 'DISK': 100},
            'ens.aws-eu-ireland.edgenet.cloud': {'RAM': 5, 'CPU': 3, 'DISK': 120},
            'ens.aws-eu-frankfurt.edgenet.cloud': {'RAM': 2, 'CPU': 3, 'DISK': 110}
        }

        for c in cloudlet_ids:
            if cloudlet_usage[c]:
                usage[c] = cloudlet_usage[c]
        resp = json.dumps(usage)
        print "usage1", resp
    except:
        return_status = {'code': 500, 'error': 'internal server error'}
        resp = json.dumps(return_status)
        print "usage2", resp
    return resp


@central_repo.route("/api/CR/fetch_policy", methods=['GET'])
def fetch_data():
    file = "C:/Users/gur40998/workspace/metaswitch/sample/app-policy.db"
    with open(file) as app_file:
        db_data = json.load(app_file)
        return json.dumps(db_data)

central_repo.run(host="0.0.0.0", port=5001, threaded=True)

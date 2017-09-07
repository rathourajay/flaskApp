# fetch app capacity from central repo
# fetch cloudlets_id from central repo first time_ and next time_ cloudlets should be stored in file
# pass these cloudlets_id to llo to get capacity
# fetch usage capacity from llo
# compare/shortlist

#import os
#import sys
import json
#import logging
#import threading
import flask
#import httplib
import requests
from flask import Flask, request, Response, jsonify
from collections import Counter
from haversine import haversine

discovery_server = Flask(__name__)


@discovery_server.route("/api/DS/shortlist", methods=['GET'])
def shortlist_cloudlets():
    try:
        RANGE = 100.0  # in KM
#         import pdb
#         pdb.set_trace()
        app_id = request.args.get('app_id')
        client_lat = float(request.args.get('lat'))
        client_long = float(request.args.get('long'))
        client_lat_long = (client_lat, client_long)

        # fetch app capacity from central repo
        app_requirement = requests.get(
            "http://localhost:5001/api/CR/app_requirement/%s" % app_id).content
        app_requirement = json.loads(app_requirement)
        # fetch cloudlets_id from central repo first time_ and next time_
        # cloudlets should be stored in file
        cloudlet_location = requests.get(
            "http://localhost:5001/api/CR/cloudletsLocation").content

        cloudlet_location_dict = json.loads(cloudlet_location)
        cloudlet_ids = []
        dist_cmp_dict = {}

        for cloudlet_id in cloudlet_location_dict:
            cloudlet_lat = cloudlet_location_dict[cloudlet_id]['lat']
            cloudlet_long = cloudlet_location_dict[cloudlet_id]['long']
            cloudlet_lat_long = (cloudlet_lat, cloudlet_long)
            distance = haversine(client_lat_long, cloudlet_lat_long)
            dist_cmp_dict[cloudlet_id] = distance
            print cloudlet_id, ":", distance

        for i in range(2):
            shortest_cloudlet_id = min(
                dist_cmp_dict, key=lambda k: dist_cmp_dict[k])
            cloudlet_ids.append(str(shortest_cloudlet_id))
            del(dist_cmp_dict[shortest_cloudlet_id])

        print "cloudlet_ids with min distance:", cloudlet_ids

        # pass these cloudlets_id to llo to get capacity
        cloudlets_capacity = requests.get(
            "http://localhost:5003/api/llo/notifyCapacity?ids=%s" % (cloudlet_ids)).content

        # fetch usage capacity from llo
        cloudlets_capacity = json.loads(cloudlets_capacity)

        # Getting cloudlets usage
        cloudlet_usage = requests.get(
            "http://localhost:5003/api/llo/notifyUsage?ids=%s" % (cloudlet_ids)).content
        cloudlet_usage = json.loads(cloudlet_usage)

        print "app_requirement:", app_requirement
        print "cloudlets_capacity:", cloudlets_capacity
        print "cloudlet_usage:", cloudlet_usage

        available_capacity_dict = {}

        # remaining capacity calculation block
        shortlist = []
        for item in cloudlet_ids:
            dict1 = Counter(cloudlet_usage[item])
            dict2 = Counter(cloudlets_capacity[item])
            available_capacity_dict[item] = dict(dict2 - dict1)
            if available_capacity_dict[item]['RAM'] > app_requirement['RAM'] and \
                    available_capacity_dict[item]['CPU'] > app_requirement['CPU'] and \
                    available_capacity_dict[item]['DISK'] > app_requirement['DISK']:
                shortlist.append(item)

        print "available capacity", available_capacity_dict

        #cloudlet_usage = json.dumps(cloudlet_usage)
        resp = {'shortlist': shortlist}
        resp = json.dumps(resp)
        print "resp_shortlist1", resp
    except:
        return_status = {'code': 500, 'error': 'internal server error'}
        resp = json.dumps(return_status)
        print "resp_shortlist2", resp
    return resp


@discovery_server.route("/api/DS/registerCloudlet", methods=['POST'])
def register_cloudlets():
    try:
        cloudlet_id = request.args.get('cloudlet_id')
        data = {
            'cloudlet_id': cloudlet_id,
            'status': 'ACTIVE'
        }
        response = requests.put(
            "http://localhost:5001/api/CR/change_status", params=data)

        status = {'code': 200, 'content': response.content}
        resp = json.dumps(status)
        print "resp1", resp
        return resp
    except:
        return_status = {'code': 500, 'error': 'internal server error'}
        resp = json.dumps(return_status)
    return resp


@discovery_server.route("/api/DS/deregisterCloudlet", methods=['DELETE'])
def deregister_cloudlets():
    try:
        cloudlet_id = request.args.get('cloudlet_id')
        data = {
            'cloudlet_id': cloudlet_id,
            'status': 'INACTIVE'
        }
        response = requests.put(
            "http://localhost:5001/api/CR/change_status", params=data)

        status = {'code': 200, 'content': response.content}
        resp = json.dumps(status)

        return resp
    except:
        return_status = {'code': 500, 'error': 'internal server error'}
        resp = json.dumps(return_status)
    return resp

discovery_server.run(host="0.0.0.0", port=5000, threaded=True)

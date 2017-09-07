import flask
import json
import requests
from flask import Flask, request

llo = Flask(__name__)

#{ cloudlet_ids:[cl1,cl2,cl3]}


@llo.route("/api/llo/notifyCapacity", methods=['GET'])
def capacity():
    #     import pdb
    #     pdb.set_trace()
    cloudlet_ids = request.args.get('ids')
    cloudlet_ids = eval(cloudlet_ids)
    try:
        capacity = {}
        data = {
            'ens.aws-as-eastindia.edgenet.cloud': {'RAM': 20, 'CPU': 4, 'DISK': 500},
            'cl13': {'RAM': 30, 'CPU': 60, 'DISK': 400},
            'cl111': {'RAM': 60, 'CPU': 20, 'DISK': 600},
            'ens.aws-as-westindia.edgenet.cloud': {'RAM': 30, 'CPU': 10, 'DISK': 200},
            'cl10': {'RAM': 50, 'CPU': 30, 'DISK': 600}
        }
#         cloudlet_ids = json.load(cloudlets)
#         cloudlet_list = cloudlet_ids['cloudlet_ids']
#         print "cloudlet_list", cloudlet_list

        for c in cloudlet_ids:
            if data[c]:
                capacity[c] = data[c]
                print "capacity", capacity
        #response = requests.put("http://localhost:5001/api/CR/change_status", params=data)

        #status = {'code': 200, 'content': response.content}
        resp = json.dumps(capacity)
        print "resp_capacity_LLO1", resp
    except:
        return_status = {'code': 500, 'error': 'internal server error'}
        resp = json.dumps(return_status)
        print "resp1_capacity_LLO2", resp
    return resp


@llo.route("/api/llo/notifyUsage", methods=['GET'])
def usage():
    cloudlet_ids = request.args.get('ids')
    cloudlet_ids = eval(cloudlet_ids)
    try:
        #         import pdb
        #         pdb.set_trace()
        usage = {}
        cloudlet_ids = request.args.get('ids')
        cloudlet_ids = eval(cloudlet_ids)
        print "IDs for usage:", cloudlet_ids
        cloudlet_usage = {
            'ens.aws-as-westindia.edgenet.cloud': {'RAM': 8, 'CPU': 2, 'DISK': 110},
            'cl13': {'RAM': 4, 'CPU': 40, 'DISK': 290},
            'cl111': {'RAM': 60, 'CPU': 20, 'DISK': 600},
            'ens.aws-as-eastindia.edgenet.cloud': {'RAM': 3, 'CPU': 1, 'DISK': 190},
            'cl10': {'RAM': 50, 'CPU': 30, 'DISK': 600}
        }
#         cloudlet_ids = json.load(cloudlets)
#         cloudlet_list = cloudlet_ids['cloudlet_ids']
#         print "cloudlet_list", cloudlet_list

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

llo.run(host="0.0.0.0", port=5003, threaded=True)

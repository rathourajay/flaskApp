from flask import Flask, request, Response
import requests
import json
import sys

MEC_APP_CATALOG_IP = "localhost"
MEC_APP_CATALOG_PORT = 0xecb9


MEC_CLOUDLET_CATALOG_IP = "localhost"
MEC_CLOUDLET_CATALOG_PORT = 0xecba

#MEC_CMS_PORT = 0xed02
MEC_CMS_PORT = 0x17d2

cms = Flask(__name__)


@cms.route('/api/v1.0/llo/cms/events', methods=['POST', 'GET'])
#@cms.route('/events',methods=['POST','GET'])
def events():

    eventsdata = json.loads(request.args.get('events_val'))
    repo = eventsdata['target']['repository']
    target_url = eventsdata['target']['url']
    tag = 'ubuntu_new'
    if 'tag' in eventsdata['target']:
        tag = eventsdata['target']['tag']

    # Get cloudlet details from central repository
    url = "http://%s:%d/api/v1.0/centralrepo/cloudletcatalog/cloudlets" % (
        MEC_CLOUDLET_CATALOG_IP, MEC_CLOUDLET_CATALOG_PORT)

    resp = requests.get(url)
    data = json.loads(resp.text)
    endpoints = []
    for cloudlet in data['cloudlets']:
        endpoints.append(data['cloudlets'][cloudlet]['endpoints']['clc'])

    for endpoint in endpoints:
        # Notify cloud controller for the new image
        try:
            payload = {'repository': repo, 'tag': tag, 'url': target_url}
            headers = {'content-type': 'application/json'}
            url = "http://%s:%s/api/v1.0/clc/notify" % (
                "localhost", 60708)

            response = requests.post(
                url, params=payload, headers=headers)
        except:
            pass
    return Response(status=200)


if __name__ == '__main__':
    cms.run(host="0.0.0.0", port=MEC_CMS_PORT, debug=True)

import json
#import string
#import httplib
#import urllib2
import requests
#from flask import Flask, request, Response, jsonify


data = {'cloudlet_id': 'cl122'}
jdata = json.dumps(data)
resp = requests.put(
    "http://localhost:5002/cloudletcontroller/cloudlet/v1.5/register", params=data)

# print resp

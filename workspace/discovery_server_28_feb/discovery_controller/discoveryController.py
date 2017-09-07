import os
import sys
import json
import logging
import threading
import flask
import httplib
import requests
from flask import Flask, request, Response, jsonify

from collections import Counter

MEC_APPCATALOG_SERVICE_IP = "localhost"
# MEC_APPCATALOG_SERVICE_IP = "0.0.0.0"
MEC_APPCATALOG_SERVICE_PORT = '56000'

MEC_CLOUDLETCATALOG_SERVICE_IP = "localhost"
# MEC_CLOUDLETCATALOG_SERVICE_IP = "0.0.0.0"
MEC_CLOUDLETCATALOG_SERVICE_PORT = '56001'

# MEC_DISCOVERY_SERVER_IP = "localhost"
MEC_DISCOVERY_SERVER_IP = "0.0.0.0"
MEC_DISCOVERY_SERVER_PORT = '60000'

discovery_server = Flask(__name__)


class GeoIP:
    continents = {
        "AD": "EU", "AE": "AS", "AF": "AS", "AG": "NA", "AI": "NA", "AL": "EU", "AM": "AS", "AN": "NA", "AO": "AF", "AP": "AS", "AQ": "AN", "AR": "SA", "AS": "OC",
        "AT": "EU", "AU": "OC", "AW": "NA", "AX": "EU", "AZ": "AS", "BA": "EU", "BB": "NA", "BD": "AS", "BE": "EU", "BF": "AF", "BG": "EU", "BH": "AS", "BI": "AF",
        "BJ": "AF", "BL": "NA", "BM": "NA", "BN": "AS", "BO": "SA", "BR": "SA", "BS": "NA", "BT": "AS", "BV": "AN", "BW": "AF", "BY": "EU", "BZ": "NA", "CA": "NA",
        "CC": "AS", "CD": "AF", "CF": "AF", "CG": "AF", "CH": "EU", "CI": "AF", "CK": "OC", "CL": "SA", "CM": "AF", "CN": "AS", "CO": "SA", "CR": "NA", "CU": "NA",
        "CV": "AF", "CX": "AS", "CY": "AS", "CZ": "EU", "DE": "EU", "DJ": "AF", "DK": "EU", "DM": "NA", "DO": "NA", "DZ": "AF", "EC": "SA", "EE": "EU", "EG": "AF",
        "EH": "AF", "ER": "AF", "ES": "EU", "ET": "AF", "EU": "EU", "FI": "EU", "FJ": "OC", "FK": "SA", "FM": "OC", "FO": "EU", "FR": "EU", "FX": "EU", "GA": "AF",
        "GB": "EU", "GD": "NA", "GE": "AS", "GF": "SA", "GG": "EU", "GH": "AF", "GI": "EU", "GL": "NA", "GM": "AF", "GN": "AF", "GP": "NA", "GQ": "AF", "GR": "EU",
        "GS": "AN", "GT": "NA", "GU": "OC", "GW": "AF", "GY": "SA", "HK": "AS", "HM": "AN", "HN": "NA", "HR": "EU", "HT": "NA", "HU": "EU", "ID": "AS", "IE": "EU",
        "IL": "AS", "IM": "EU", "IN": "AS", "IO": "AS", "IQ": "AS", "IR": "AS", "IS": "EU", "IT": "EU", "JE": "EU", "JM": "NA", "JO": "AS", "JP": "AS", "KE": "AF",
        "KG": "AS", "KH": "AS", "KI": "OC", "KM": "AF", "KN": "NA", "KP": "AS", "KR": "AS", "KW": "AS", "KY": "NA", "KZ": "AS", "LA": "AS", "LB": "AS", "LC": "NA",
        "LI": "EU", "LK": "AS", "LR": "AF", "LS": "AF", "LT": "EU", "LU": "EU", "LV": "EU", "LY": "AF", "MA": "AF", "MC": "EU", "MD": "EU", "ME": "EU", "MF": "NA",
        "MG": "AF", "MH": "OC", "MK": "EU", "ML": "AF", "MM": "AS", "MN": "AS", "MO": "AS", "MP": "OC", "MQ": "NA", "MR": "AF", "MS": "NA", "MT": "EU", "MU": "AF",
        "MV": "AS", "MW": "AF", "MX": "NA", "MY": "AS", "MZ": "AF", "NA": "AF", "NC": "OC", "NE": "AF", "NF": "OC", "NG": "AF", "NI": "NA", "NL": "EU", "NO": "EU",
        "NP": "AS", "NR": "OC", "NU": "OC", "NZ": "OC", "O1": "--", "OM": "AS", "PA": "NA", "PE": "SA", "PF": "OC", "PG": "OC", "PH": "AS", "PK": "AS", "PL": "EU",
        "PM": "NA", "PN": "OC", "PR": "NA", "PS": "AS", "PT": "EU", "PW": "OC", "PY": "SA", "QA": "AS", "RE": "AF", "RO": "EU", "RS": "EU", "RU": "EU", "RW": "AF",
        "SA": "AS", "SB": "OC", "SC": "AF", "SD": "AF", "SE": "EU", "SG": "AS", "SH": "AF", "SI": "EU", "SJ": "EU", "SK": "EU", "SL": "AF", "SM": "EU", "SN": "AF",
        "SO": "AF", "SR": "SA", "ST": "AF", "SV": "NA", "SY": "AS", "SZ": "AF", "TC": "NA", "TD": "AF", "TF": "AN", "TG": "AF", "TH": "AS", "TJ": "AS", "TK": "OC",
        "TL": "AS", "TM": "AS", "TN": "AF", "TO": "OC", "TR": "EU", "TT": "NA", "TV": "OC", "TW": "AS", "TZ": "AF", "UA": "EU", "UG": "AF", "UM": "OC", "US": "NA",
        "UY": "SA", "UZ": "AS", "VA": "EU", "VC": "NA", "VE": "SA", "VG": "NA", "VI": "NA", "VN": "AS", "VU": "OC", "WF": "OC", "WS": "OC", "YE": "AS", "YT": "AF",
        "ZA": "AF", "ZM": "AF", "ZW": "AF"
    }

    def __init__(self, ipaddr):
        # http = httplib.HTTPConnection("freegeoip.net", 80)
        # url = "/json/%s" % ipaddr
        #         url = "http://freegeoip.net/json/?q=%s" % ipaddr
        url = "https://ipapi.co/%s/json/" % ipaddr
        rsp = requests.get(url).content
#         import pdb
#         pdb.set_trace()
#         rsp = '{"ip":"24.232.0.0","country_code":"BA","country_name":"India","region_code":"UP","region_name":"Uttar Pradesh","city":"Kanpur","zip_code":"208005","time_zone":"Asia/Kolkata","latitude":26.4667,"longitude":80.35,"metro_code":0}\n'
        import pdb
        pdb.set_trace()
        data = rsp
        logging.debug("freegeoip.net response: %s" % data)
        self.data = json.loads(data)
        self.country = self.data['country']
#         self.country = self.data["country_code"]
        print "self.country", self.country
#         self.latitude = self.data["latitude"]
#         self.longitude = self.data["longitude"]
        #         self.country = "GB"
        #         self.latitude = 0.0
        #         self.longitude = 0.0
        if self.country in GeoIP.continents:
            self.continent = GeoIP.continents[self.country]
        else:
            self.continent = "--"

    def __repr__(self):
        return "country=%s, continent=%s, longitude=%f, latitude=%f" % (self.country, self.continent, self.latitude, self.longitude)


class CentralRepoHelper:

    def __init__(self):
        self.lock = threading.Lock()

    def load_db(self):
        self.db = None
        try:
            url = "http://%s:%s/api/v1.0/centralrepo/cloudletcatalog/cloudlets" % (
                MEC_CLOUDLETCATALOG_SERVICE_IP, MEC_CLOUDLETCATALOG_SERVICE_PORT)
            db_data = requests.get(url)
            logging.info("Loading cloudlets database")
            self.db = json.loads(db_data.content)
        except:
            return Response(response="CLOUDLET-DISCOVERY INTERNAL_SERVER_ERROR",
                            status=httplib.INTERNAL_SERVER_ERROR)

    def find_app(self, app):
        app_data = None

        try:
            url = "http://%s:%s/api/v1.0/centralrepo/appcatalog/%s" % (
                MEC_APPCATALOG_SERVICE_IP, MEC_APPCATALOG_SERVICE_PORT, str(app))
            app_data = requests.get(str(url))
            app_data = json.loads(app_data.content)
        except:
            return Response(response="CLOUDLET-DISCOVERY INTERNAL_SERVER_ERROR find_app",
                            status=httplib.INTERNAL_SERVER_ERROR)

        return app_data

    def cloudlets(self, app, country=None, continent=None):

        app_policy = self.find_app(app)

        if app_policy:
            if app_policy["enabled"] != "Y":
                return {}

            if country and app_policy["client-regions"] and country not in app_policy["client-regions"] and continent not in app_policy["client-regions"]:
                return {}

            if app_policy["low-latency"] == "Y":
                if country:
                    # Choose from low-latency clouds for specific region
                    filter = lambda v: country in v["regions"][
                        "low-latency"] or continent in v["regions"]["low-latency"]
                else:
                    # Choose from all low-latency clouds
                    filter = lambda v: v["regions"]["low-latency"]
            else:
                if country:
                    # Choose from all clouds for specific region
                    filter = lambda v: country in v["regions"][
                        "all"] or continent in v["regions"]["all"]
                else:
                    # Choose from all cloudsn

                    filter = lambda v: v["regions"]["all"]

            self.load_db()
            cloudlets = [
                k for k, v in self.db["cloudlets"].iteritems() if filter(v)]

            cloudlet_dict = {}
            cloudlet_dict['cloud'] = {
                "endpoints": {"app@cloud": "http://165.225.106.222:6880"}}

            if cloudlets:
                cloudlet_dict['cloudlets'] = {}
                for cloudlet_id in cloudlets:
                    cloudlet_dict['cloudlets'][cloudlet_id] = {}
                    cloudlet_dict['cloudlets'][cloudlet_id]['endpoints'] = self.db[
                        "cloudlets"][cloudlet_id]["endpoints"]["probe"]
                return json.dumps(cloudlet_dict)
            else:
                return {}

#################### START: API Definition ####################


@discovery_server.route("/api/v1.0/discover/<developer_id>/<app_id>", methods=['GET'])
def discover_cloudlets(developer_id, app_id):
    client_ip = request.args.get('client')
    if client_ip:
        split_str = client_ip.split('.')
        if len(split_str) != 4:
            return Response(response="Invalid Client IP", status=httplib.BAD_REQUEST)
        elif len(split_str) == 4:
            for item in split_str:
                if int(item) > 255 or int(item) < 0:
                    return Response(response="Invalid Client IP", status=httplib.BAD_REQUEST)

        # Find the country/continent of the client
        logging.debug("Find location for client %s" % client_ip)
        match = GeoIP(client_ip)
#         logging.debug(repr(match))
    else:
        match = None

    # Get the candidate cloudlets for the app (if the app is not enabled this
    # will return an empty list)
    app = "%s.%s" % (developer_id, app_id)

    cr_helper = CentralRepoHelper()
    cloudlets = cr_helper.cloudlets(
        app, match.country, match.continent) if match else cr_helper.cloudlets(app)
    if len(cloudlets) > 0:
        rsp = jsonify(cloudlets)
        return rsp
    else:
        return Response(response="NOT FOUND", status=httplib.NOT_FOUND)


@discovery_server.route("/api/v1.0/discover/<cloudlet_id>/register/", methods=['PUT'])
def register_cloudlets(cloudlet_id):
    try:
        data = {
            'status': 'registered'
        }
        url = "http://%s:%s/api/v1.0/centralrepo/cloudletcatalog/%s" % (
            MEC_CLOUDLETCATALOG_SERVICE_IP, MEC_CLOUDLETCATALOG_SERVICE_PORT, cloudlet_id)
        response = requests.put(url, params=data)
        if response.status_code == httplib.OK:  # This is 200
            resp = Response(
                response="CLOUDLET-REGISTER [%s] SUCCESS" % cloudlet_id)
        else:
            resp = Response(
                response="CLOUDLET-REGISTER [%s] NOT FOUND" % cloudlet_id, status=httplib.NOT_FOUND)
    except:
        resp = Response(
            response="CLOUDLET-REGISTER INTERNAL_SERVER_ERROR", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@discovery_server.route("/api/v1.0/discover/<cloudlet_id>/deregister/", methods=['PUT'])
def deregister_cloudlets(cloudlet_id):
    try:
        data = {
            'status': 'deregistered'
        }
        url = "http://%s:%s/api/v1.0/centralrepo/cloudletcatalog/%s" % (
            MEC_CLOUDLETCATALOG_SERVICE_IP, MEC_CLOUDLETCATALOG_SERVICE_PORT, cloudlet_id)
        response = requests.put(url, params=data)
        if response.status_code == httplib.OK:  # This is 200
            resp = Response(
                response="CLOUDLET-DEREGISTER [%s] SUCCESS" % cloudlet_id)
        else:
            resp = Response(
                response="CLOUDLET-DEREGISTER [%s] NOT FOUND" % cloudlet_id, status=httplib.NOT_FOUND)
    except:
        resp = Response(
            response="CLOUDLET-DEREGISTER INTERNAL_SERVER_ERROR", status=httplib.INTERNAL_SERVER_ERROR)
    return resp

#################### END: API Definition ####################

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

# Start the Flask web server (HTTP)
discovery_server.run(
    host=MEC_DISCOVERY_SERVER_IP, port=MEC_DISCOVERY_SERVER_PORT, threaded=True)

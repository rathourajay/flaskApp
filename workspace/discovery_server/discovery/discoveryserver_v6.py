import sys
import json
import logging
import httplib
import requests
from flask import Flask, request, Response, jsonify
from functools import wraps
from flask import abort
import re
from ConfigParser import SafeConfigParser
import threading
import time
from datetime import datetime

MEC_APP_CATALOG_PORT = 0xecb9
MEC_CLOUDLET_CATALOG_PORT = 0xecba
MEC_DISCOVERY_SERVER_PORT = 0xed06
MEC_IAM_PORT = 0xecc1
CLOUDLET_IP = "localhost"
INTERVAL_TO_CHECK_HEARTBEAT = 5
INTERVAL_TO_DEACTIVATE_CLOUDLET = 20
SUBSCRIBER_FILE = "C:/Users/gur40998/workspace/discovery_server/discovery/subscribers.ini"

# Dictionary to store 'datetime' object of cloudlets on recieving heartbeat
heartbeat_dict = {}
# List to store inactive cloudlets
inactive_cloudlets = []


discoveryserver = Flask(__name__)

# IAM Token Validation decorator


def iam_token_validate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'Authorization' in request.headers:
            print 'Request missing Authorization Token'
            abort(401)

        bearer_data = request.headers[
            'Authorization'].encode('ascii', 'ignore')
        bearer_token = str.replace(str(bearer_data), 'Bearer ', '')

        # Get IAM module to validate the token
        IAM_STUB_API_VERSION = 'v1.5'
        IAM_TOKEN_VALIDATE_URI = "/identity/%s/discoverytoken/" % (
            IAM_STUB_API_VERSION)
        IAM_ENDPOINT = "http://%s:%s" % (MEC_IAM_IP, MEC_IAM_PORT)

        token_validate_url = IAM_ENDPOINT + \
            IAM_TOKEN_VALIDATE_URI + bearer_token
        print 'Validating Token {}'.format(bearer_token)

        response = requests.get(token_validate_url)
        if(response.status_code == 200):
            return f(bearer_token, *args, **kwargs)
        else:
            abort(response.status_code)
    return decorated_function


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
        #url = "http://freegeoip.net/json/?q=%s" % ipaddr
        url = "http://ipapi.co/%s/json" % ipaddr
        rsp = requests.get(url).content
        data = rsp
        logging.debug("ipapi.co response: %s" % data)
        self.data = json.loads(data)
        self.country = self.data["country"]
        self.latitude = self.data["latitude"]
        self.longitude = self.data["longitude"]
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
            url = "http://%s:%d/api/v1.0/centralrepo/cloudletcatalog/cloudlets" % (
                MEC_CLOUDLET_CATALOG_IP, MEC_CLOUDLET_CATALOG_PORT)
            db_data = requests.get(url)
            logging.info("Loading cloudlets database")
            self.db = json.loads(db_data.content)
        except:
            return Response(response="CLOUDLET-DISCOVERY INTERNAL_SERVER_ERROR",
                            status=httplib.INTERNAL_SERVER_ERROR)

    def find_cloudlets_with_env(self, environment):
        cloudlets_with_env = {}
        cloudlets_with_env['cloudlets'] = []
        self.load_db()
        cloudlets = self.db['cloudlets']
        for cloudlet in cloudlets:
            if cloudlets[cloudlet]['environment'] == environment:
                cloudlets_with_env['cloudlets'].append(cloudlet)
        return cloudlets_with_env

    def find_app(self, app):
        app_data = None

        try:
            url = "http://%s:%d/api/v1.0/centralrepo/appcatalog/%s" % (
                MEC_APP_CATALOG_IP, MEC_APP_CATALOG_PORT, str(app))
            app_data = requests.get(str(url))
            app_data = json.loads(app_data.content)
        except:
            return Response(response="CLOUDLET-DISCOVERY INTERNAL_SERVER_ERROR find_app",
                            status=httplib.INTERNAL_SERVER_ERROR)

        return app_data

    def calculate_capacity(self, cloudlets, cloudlets_capacity, cloudlet_usage, app_requirement):
        shortlist = []
        # for item in cloudlets_capacity:
        for item in cloudlets:

            memory = re.findall(
                '\d+', str(cloudlets_capacity[item]['memory']))

            storage = re.findall(
                '\d+', str(cloudlets_capacity[item]['storage']))

            cpu = re.findall(
                '\d+', str(cloudlets_capacity[item]['cpu']))

            memory_capacity = int(memory[0])
            storage_capacity = int(storage[0])
            cpu_capacity = int(cpu[0])

            mem_used = re.findall(
                '\d+', str(cloudlet_usage[item]['memory']))

            storage_used = re.findall(
                '\d+', str(cloudlet_usage[item]['storage']))

            cpu_used = re.findall(
                '\d+', str(cloudlet_usage[item]['cpu']))

            memory_in_use = int(mem_used[0])
            storage_in_use = int(storage_used[0])
            cpu_in_use = int(cpu_used[0])

            available_memory = memory_capacity - \
                (memory_in_use / 100.0) * memory_capacity
            available_storage = storage_capacity - \
                (storage_in_use / 100.0) * storage_capacity
            available_cpu = cpu_capacity - \
                (cpu_in_use / 100.0) * cpu_capacity

            app_req_memory = re.findall(
                '\d+', str(app_requirement['memory']))

            app_req_cpu = re.findall(
                '\d+', str(app_requirement['cpu']))

            app_req_storage = re.findall(
                '\d+', str(app_requirement['storage']))

            if available_memory > int(app_req_memory[0]) and \
                    available_cpu > int(app_req_cpu[0]) and \
                    available_storage > int(app_req_storage[0]):
                shortlist.append(item)
        return shortlist

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
                    filter = lambda v: (country in v["regions"][
                        "low-latency"] or continent in v["regions"]["low-latency"]) and (v["status"] == "registered")
                else:
                    # Choose from all low-latency clouds
                    filter = lambda v: (
                        v["regions"]["low-latency"]) and (v["status"] == "registered")
            else:
                if country:
                    # Choose from all clouds for specific region
                    filter = lambda v: (country in v["regions"][
                        "all"] or continent in v["regions"]["all"]) and (v["status"] == "registered")
                else:
                    # Choose from all clouds

                    filter = lambda v: (v["regions"]["all"]) and (
                        v["status"] == "registered")

            self.load_db()
            cloudlets = [
                k for k, v in self.db["cloudlets"].iteritems() if filter(v)]

            response_dict = {}
            response_dict['cloud'] = {}
            response_dict['cloud']['endpoints'] = {}
            response_dict['cloud'] = {
                "endpoints": {"app@cloud": "http://165.225.106.222:6880"}}
            if app_policy['app_cloud_url']:
                response_dict['cloud']['endpoints']['app@cloud'] = app_policy["app_cloud_url"][
                    "protocol"] + "://" + app_policy["app_cloud_url"]["ip"] + ":" + app_policy["app_cloud_url"]["port"]

            capacity_url = "http://%s:%d/api/v1.0/centralrepo/cloudletcatalog/capacity?cloudlet_ids=%s" % (
                MEC_CLOUDLET_CATALOG_IP, MEC_CLOUDLET_CATALOG_PORT, cloudlets)
            cloudlets_capacity = json.loads(requests.get(capacity_url).content)

            usage_url = "http://%s:%d/api/v1.0/centralrepo/cloudletcatalog/usage?cloudlet_ids=%s" % (
                MEC_CLOUDLET_CATALOG_IP, MEC_CLOUDLET_CATALOG_PORT, cloudlets)
            cloudlet_usage = json.loads(requests.get(usage_url).content)

            app_resource_url = "http://%s:%d/api/v1.0/centralrepo/appcatalog/resource/%s" % (
                MEC_APP_CATALOG_IP, MEC_APP_CATALOG_PORT, app)
            app_requirement = json.loads(
                requests.get(app_resource_url).content)
            shortlist = self.calculate_capacity(
                cloudlets, cloudlets_capacity, cloudlet_usage, app_requirement)
            if shortlist:
                response_dict['cloudlets'] = {}
                for cloudlet_id in shortlist:
                    response_dict['cloudlets'][cloudlet_id] = {}
                    response_dict['cloudlets'][cloudlet_id]['endpoints'] = {}
                    if self.db["cloudlets"][cloudlet_id]["endpoints"]["probe"]:
                        response_dict['cloudlets'][cloudlet_id]['endpoints']['probe'] = self.db["cloudlets"][cloudlet_id]["endpoints"]["probe"][
                            "protocol"] + "://" + self.db["cloudlets"][cloudlet_id]["endpoints"]["probe"]["ip"] + ":" + self.db["cloudlets"][cloudlet_id]["endpoints"]["probe"]["port"]
                return json.dumps(response_dict)

            else:
                return {}


class Event_Subscribers:

    def __init__(self, subscribers_file):
        self.file = subscribers_file

        self.parser = SafeConfigParser()
        self.parser.read(subscribers_file)
        self.event_list = self.parser.sections()

    def notify(self, data_for_subscriber, event):

        #         for e in self.subscribers_list:
        for subscriber, subscriber_url in self.parser.items(event):
            try:
                rsp = requests.put(
                    subscriber_url, params=data_for_subscriber)
                print subscriber, "...Response is ::", rsp
                return True
            except:
                print subscriber_url, " :url not accessible for subscriber ", subscriber
                return False

    def subscribe(self, subscriber_name, subscriber_url, event):
        if event not in self.event_list:
            self.parser.add_section(event)
        if self.parser.has_option(event, subscriber_name):
            return Response(response="%s:ALREADY_SUBSCRIBED" % subscriber_name, status=httplib.CONFLICT)

        else:
            #             self.parser.add_section(subscriber_name)
            self.parser.set(event, subscriber_name, subscriber_url)
            with open(self.file, "w") as cfgfile:
                self.parser.write(cfgfile)
            self.parser.read(self.file)
            self.event_list = self.parser.sections()
            return Response(response="%s:SUBSCRIBE_SUCCESSFULL" % subscriber_name, status=httplib.OK)

    def unsubscribe(self, subscriber_name, event):
        if event not in self.event_list:
            return Response(response="%s:EVENT_DOES_NOT_EXIST" % event, status=httplib.CONFLICT)
        if self.parser.has_option(event, subscriber_name):
            self.parser.remove_option(event, subscriber_name)
            with open(self.file, "w") as cfgfile:
                self.parser.write(cfgfile)
            self.parser.read(self.file)
            self.event_list = self.parser.sections()
            return Response(response="%s:UNSUBSCRIBE_SUCCESSFULL" % subscriber_name, status=httplib.OK)
        else:
            return Response(response="%s:NOT_SUBSCRIBED" % subscriber_name, status=httplib.CONFLICT)


class Heartbeat(threading.Thread):

    def __init__(self, delay):
        threading.Thread.__init__(self)
        self.delay = delay

    def run(self):
        self.check_heartbeat()

    def check_heartbeat(self):

        delay = self.delay
        inactive_data_dict = {
            'status': 'inactive'
        }

        while(True):
            global heartbeat_dict
            global inactive_cloudlets
            print " delay = ", delay, ", heartbeat_dict=", heartbeat_dict
            print "inactive_cloudlet:", inactive_cloudlets
            time.sleep(delay)
            if heartbeat_dict:
                for cloudlet in heartbeat_dict:
                    time_since_last_heartbeat = (
                        datetime.now() - heartbeat_dict[cloudlet]).seconds
                    if (time_since_last_heartbeat > INTERVAL_TO_DEACTIVATE_CLOUDLET) and (cloudlet not in inactive_cloudlets):
                        url_cloudlet_catalog = "http://%s:%d/api/v1.0/centralrepo/cloudletcatalog/%s" % (
                            MEC_CLOUDLET_CATALOG_IP, MEC_CLOUDLET_CATALOG_PORT, cloudlet)
                        try:
                            data_for_subscriber = {
                                'cloudlet': cloudlet, 'status': 'down'}

                            requests.put(
                                url_cloudlet_catalog, params=inactive_data_dict)
                            inactive_cloudlets.append(cloudlet)
                            subscribers.notify(
                                data_for_subscriber, "heartbeat")
                            print "!!!!!", cloudlet, "Down!!!!!"
                        except:
                            print "ERROR in deactivating the cloudlet..."
                    if (time_since_last_heartbeat <= INTERVAL_TO_DEACTIVATE_CLOUDLET) and (cloudlet in inactive_cloudlets):
                        inactive_cloudlets.remove(cloudlet)
                        print "****", cloudlet, "Up again ****"


@discoveryserver.route("/api/v1.0/discover/<developer_id>/<app_id>", methods=['GET'])
@iam_token_validate
def discover_cloudlets(*args, **kwargs):
    #     client_ip = request.headers.get('client_ip')
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
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
            logging.debug(repr(match))
    else:
        match = None

    # Get the candidate cloudlets for the app (if the app is not enabled this
    # will return an empty list)
    developer_id = kwargs['developer_id']
    app_id = kwargs['app_id']
    app = "%s.%s" % (developer_id, app_id)

    cr_helper = CentralRepoHelper()
    cloudlets = cr_helper.cloudlets(
        app, match.country, match.continent) if match else cr_helper.cloudlets(app)

    if len(cloudlets) > 0:
        rsp = jsonify(cloudlets)
        return rsp
    else:
        return Response(response="NOT FOUND", status=httplib.NOT_FOUND)


@discoveryserver.route("/api/v1.0/discover/<cloudlet_id>/register", methods=['PUT'])
def register_cloudlets(cloudlet_id):
    try:
        data = {
            'status': 'registered'
        }
        data_for_subscriber = {
            'cloudlet': cloudlet_id,
            'status': 'registered'
        }
        url_cloudlet_catalog = "http://%s:%d/api/v1.0/centralrepo/cloudletcatalog/%s" % (
            MEC_CLOUDLET_CATALOG_IP, MEC_CLOUDLET_CATALOG_PORT, cloudlet_id)
        response = requests.put(url_cloudlet_catalog, params=data)

        if response.status_code == httplib.OK:  # This is 200
            subscribers.notify(data_for_subscriber, "register")
            resp = Response(
                response="CLOUDLET-REGISTER [%s] SUCCESS" % cloudlet_id)
        else:
            resp = Response(
                response="CLOUDLET-REGISTER [%s] NOT FOUND" % cloudlet_id, status=httplib.NOT_FOUND)

    except:
        resp = Response(
            response="CLOUDLET-REGISTER INTERNAL_SERVER_ERROR", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@discoveryserver.route("/api/v1.0/discover/<cloudlet_id>/deregister", methods=['PUT'])
def deregister_cloudlets(cloudlet_id):
    try:
        data = {
            'status': 'deregistered'
        }
        data_for_subscriber = {
            'cloudlet': cloudlet_id,
            'status': 'deregistered'
        }
        url = "http://%s:%d/api/v1.0/centralrepo/cloudletcatalog/%s" % (
            MEC_CLOUDLET_CATALOG_IP, MEC_CLOUDLET_CATALOG_PORT, cloudlet_id)
        response = requests.put(url, params=data)
        if response.status_code == httplib.OK:  # This is 200
            subscribers.notify(data_for_subscriber, "deregister")
            resp = Response(
                response="CLOUDLET-DEREGISTER [%s] SUCCESS" % cloudlet_id)
        else:
            resp = Response(
                response="CLOUDLET-DEREGISTER [%s] NOT FOUND" % cloudlet_id, status=httplib.NOT_FOUND)
    except:
        resp = Response(
            response="CLOUDLET-DEREGISTER INTERNAL_SERVER_ERROR", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@discoveryserver.route("/api/v1.0/discover/subscribe", methods=['POST'])
def subscribe():
    try:

        subscribing_party = request.args.get('subscriber')
        subscribing_party_url = request.args.get('url')
        subscribing_party_event = request.args.get('event')

        resp = subscribers.subscribe(
            subscribing_party, subscribing_party_url, subscribing_party_event)

    except:
        resp = Response(
            response="SUBSCRIBE_INTERNAL_SERVER_ERROR", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@discoveryserver.route("/api/v1.0/discover/unsubscribe", methods=['POST'])
def unsubscribe():
    try:
        subscribing_party = request.args.get('subscriber')
        subscribing_party_event = request.args.get('event')

        resp = subscribers.unsubscribe(
            subscribing_party, subscribing_party_event)
    except:
        resp = Response(
            response="UNSUBSCRIBE_INTERNAL_SERVER_ERROR", status=httplib.INTERNAL_SERVER_ERROR)
    return resp


@discoveryserver.route('/api/v1.0/discover/heartbeat', methods=['PUT'])
def update_heartbeat_dict():
    print "inside update_heartbeat method"
    heartbeat_recieve_time = datetime.now()
    clc_id = request.args.get('cloudlet')
    heartbeat_dict[clc_id] = heartbeat_recieve_time
#     print heartbeat_dict
    return Response(status=httplib.OK)


@discoveryserver.route('/api/v1.0/discover/environment', methods=['GET'])
def find_cloudlets_with_env():

    environment = request.args.get('environment')
    central_repo_obj = CentralRepoHelper()
    cloudlets_with_env_staging = central_repo_obj.find_cloudlets_with_env(
        environment)
    del central_repo_obj
    resp = json.dumps(cloudlets_with_env_staging)
    return resp

#################### END: API Definition ####################

if len(sys.argv) < 4:
    print("Usage: %s <app_catalog_ip> <cloudlet_catalog_ip> <iam_ip>" %
          sys.argv[0])
    sys.exit(1)

MEC_APP_CATALOG_IP = sys.argv[1]
MEC_CLOUDLET_CATALOG_IP = sys.argv[2]
MEC_IAM_IP = sys.argv[3]

subscribers = Event_Subscribers(SUBSCRIBER_FILE)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

if __name__ == '__main__':

    heartbeat_t = Heartbeat(INTERVAL_TO_CHECK_HEARTBEAT)
    heartbeat_t.setDaemon(True)
    heartbeat_t.start()
    discoveryserver.run(
        host="0.0.0.0", port=MEC_DISCOVERY_SERVER_PORT, threaded=True)

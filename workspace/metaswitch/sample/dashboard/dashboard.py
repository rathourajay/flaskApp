import os
import logging
from optparse import OptionParser
import flask
import json
import httplib
from flask import Flask, request, Response, render_template, jsonify

probe_data = {}
app = Flask(__name__)

class GeoIP:
    continents = {
        "AD": "EU","AE": "AS","AF": "AS","AG": "NA","AI": "NA","AL": "EU","AM": "AS","AN": "NA","AO": "AF","AP": "AS","AQ": "AN","AR": "SA","AS": "OC",
        "AT": "EU","AU": "OC","AW": "NA","AX": "EU","AZ": "AS","BA": "EU","BB": "NA","BD": "AS","BE": "EU","BF": "AF","BG": "EU","BH": "AS","BI": "AF",
        "BJ": "AF","BL": "NA","BM": "NA","BN": "AS","BO": "SA","BR": "SA","BS": "NA","BT": "AS","BV": "AN","BW": "AF","BY": "EU","BZ": "NA","CA": "NA",
        "CC": "AS","CD": "AF","CF": "AF","CG": "AF","CH": "EU","CI": "AF","CK": "OC","CL": "SA","CM": "AF","CN": "AS","CO": "SA","CR": "NA","CU": "NA",
        "CV": "AF","CX": "AS","CY": "AS","CZ": "EU","DE": "EU","DJ": "AF","DK": "EU","DM": "NA","DO": "NA","DZ": "AF","EC": "SA","EE": "EU","EG": "AF",
        "EH": "AF","ER": "AF","ES": "EU","ET": "AF","EU": "EU","FI": "EU","FJ": "OC","FK": "SA","FM": "OC","FO": "EU","FR": "EU","FX": "EU","GA": "AF",
        "GB": "EU","GD": "NA","GE": "AS","GF": "SA","GG": "EU","GH": "AF","GI": "EU","GL": "NA","GM": "AF","GN": "AF","GP": "NA","GQ": "AF","GR": "EU",
        "GS": "AN","GT": "NA","GU": "OC","GW": "AF","GY": "SA","HK": "AS","HM": "AN","HN": "NA","HR": "EU","HT": "NA","HU": "EU","ID": "AS","IE": "EU",
        "IL": "AS","IM": "EU","IN": "AS","IO": "AS","IQ": "AS","IR": "AS","IS": "EU","IT": "EU","JE": "EU","JM": "NA","JO": "AS","JP": "AS","KE": "AF",
        "KG": "AS","KH": "AS","KI": "OC","KM": "AF","KN": "NA","KP": "AS","KR": "AS","KW": "AS","KY": "NA","KZ": "AS","LA": "AS","LB": "AS","LC": "NA",
        "LI": "EU","LK": "AS","LR": "AF","LS": "AF","LT": "EU","LU": "EU","LV": "EU","LY": "AF","MA": "AF","MC": "EU","MD": "EU","ME": "EU","MF": "NA",
        "MG": "AF","MH": "OC","MK": "EU","ML": "AF","MM": "AS","MN": "AS","MO": "AS","MP": "OC","MQ": "NA","MR": "AF","MS": "NA","MT": "EU","MU": "AF",
        "MV": "AS","MW": "AF","MX": "NA","MY": "AS","MZ": "AF","NA": "AF","NC": "OC","NE": "AF","NF": "OC","NG": "AF","NI": "NA","NL": "EU","NO": "EU",
        "NP": "AS","NR": "OC","NU": "OC","NZ": "OC","O1": "--","OM": "AS","PA": "NA","PE": "SA","PF": "OC","PG": "OC","PH": "AS","PK": "AS","PL": "EU",
        "PM": "NA","PN": "OC","PR": "NA","PS": "AS","PT": "EU","PW": "OC","PY": "SA","QA": "AS","RE": "AF","RO": "EU","RS": "EU","RU": "EU","RW": "AF",
        "SA": "AS","SB": "OC","SC": "AF","SD": "AF","SE": "EU","SG": "AS","SH": "AF","SI": "EU","SJ": "EU","SK": "EU","SL": "AF","SM": "EU","SN": "AF",
        "SO": "AF","SR": "SA","ST": "AF","SV": "NA","SY": "AS","SZ": "AF","TC": "NA","TD": "AF","TF": "AN","TG": "AF","TH": "AS","TJ": "AS","TK": "OC",
        "TL": "AS","TM": "AS","TN": "AF","TO": "OC","TR": "EU","TT": "NA","TV": "OC","TW": "AS","TZ": "AF","UA": "EU","UG": "AF","UM": "OC","US": "NA",
        "UY": "SA","UZ": "AS","VA": "EU","VC": "NA","VE": "SA","VG": "NA","VI": "NA","VN": "AS","VU": "OC","WF": "OC","WS": "OC","YE": "AS","YT": "AF",
        "ZA": "AF","ZM": "AF","ZW": "AF"
    }

    def __init__(self, ipaddr):
        http = httplib.HTTPConnection("freegeoip.net", 80)
        url = "/json/%s" % ipaddr
        http.request("GET", url)
        rsp = http.getresponse()
        data = rsp.read()
        self.data = json.loads(data)
        self.country = self.data["country_code"]
        self.latitude = self.data["latitude"]
        self.longitude = self.data["longitude"]
        self.city = self.data["city"]
        self.region = self.data["region_name"]
        if self.country in GeoIP.continents:
            self.continent = GeoIP.continents[self.country]
        else:
            self.continent = "--"

    def __repr__(self):
        return "country=%s, continent=%s, longitude=%f, latitude=%f" % (self.country, self.continent, self.latitude, self.longitude)

@app.route("/", methods=["GET"])
def index():
    # Display map with latest latency measurements
    return render_template("index.html")

@app.route("/probes", methods=["GET"])
def probes():
    # AJAX request to get probe data
    return jsonify(probe_data)

@app.route("/sample", methods=["POST"])
def sample():
    # Receive a latency sample from a latency client
    probe = request.remote_addr
    data = request.get_json()
    if probe not in probe_data:
        match = GeoIP(probe)
        if match:
            probe_data[probe] = {"latitude": match.latitude, "longitude": match.longitude}
            if match.country == "US":
                probe_data[probe]["name"] = match.region
            else:
                probe_data[probe]["name"] = match.city

    if probe in probe_data:
        probe_data[probe]["status"] = data["status"]
        probe_data[probe]["latency"] = data["latency"] if "latency" in data else 0.0
        probe_data[probe]["cloudlet"] = data["cloudlet"] if "cloudlet" in data else ""

    return Response(status=httplib.OK)

if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(asctime)-15s %(levelname)-8s %(message)s')

    # Enable Flask debug logs if required
    if opts.loglevel == logging.DEBUG:
        app.debug = True

    # Start the Flask web server (HTTPS)
    # SERVER_PORT = 443
    #context = ('certs/alexa.accession.metaswitch.com.crt', 'certs/alexa.accession.metaswitch.com.key')
    #app.run(host='0.0.0.0', port=SERVER_PORT, ssl_context=context, threaded=True)

    # Start the Flask web server (HTTP)
    SERVER_PORT=80
    app.run(host='0.0.0.0', port=SERVER_PORT, threaded=True)











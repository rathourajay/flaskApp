import os, sys, socket, time
import threading
import json
import httplib
import logging

ENS_WLM_AUTH    = 0xed00
ENS_WLM_PROBE   = 0xed01
ENS_WLM_SESSION = 0xed02

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
        if self.country in GeoIP.continents:
            self.continent = GeoIP.continents[self.country]
        else:
            self.continent = "--"

    def __repr__(self):
        return "country=%s, continent=%s, longitude=%f, latitude=%f" % (self.country, self.continent, self.latitude, self.longitude)


class ENSAppPolicyDB:
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
                logging.info("Loading application policy database")
                self.db = json.load(app_file)
                logging.debug(json.dumps(self.db))

    def find_app(self, app):
        app_data = None
        self.lock.acquire()

        self.load_db()
        if app in self.db["applications"]:
           app_data = self.db["applications"][app]
        self.lock.release()
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
                    filter = lambda v: country in v["regions"]["low-latency"] or continent in v["regions"]["low-latency"]
                else:
                    # Choose from all low-latency clouds
                    filter = lambda v: v["regions"]["low-latency"]
            else:
                if country:
                    # Choose from all clouds for specific region
                    filter = lambda v: country in v["regions"]["all"] or continent in v["regions"]["all"]
                else:
                    # Choose from all clouds
                    filter = lambda v: v["regions"]["all"]

            cloudlets = [k for k, v in self.db["cloudlets"].iteritems() if filter(v)]
            if cloudlets:
                return {"cloudlets": cloudlets}
            else:
                return {}


class ENSAuthListener(threading.Thread):

    class Responder(threading.Thread):
        def __init__(self, sock, addr):
            threading.Thread.__init__(self)
            self.sock = sock
            self.client = addr[0]
            self.start()

        def run(self):
            req = self.sock.recv(1024)
            logging.debug("Received %s" % req);

            # Extract the app identifier
            params = req.splitlines()[0].split(' ')
            app = params[1]

            # Find the country/continent of the client
            logging.debug("Find location for client %s" % self.client)
            match = GeoIP(self.client)
            #match = geolite2.lookup(self.client)
            logging.debug(repr(match))

            # Get the candidate cloudlets for the app (if the app is not enabled this will return an empty list)
            cloudlets = app_policy_db.cloudlets(app, match.country, match.continent) if match else app_policy_db.cloudlets(app)

            if cloudlets:
                # App is available
                logging.debug("Send ENS-AUTH-OK %s\r\n%s" % (app, json.dumps(cloudlets)))
                self.sock.send("ENS-AUTH-OK %s\r\n%s\r\n" % (app, json.dumps(cloudlets)))
            else:
                # App is not available
                logging.debug("Send ENS-AUTH-UNAVAIL %s" % app)
                self.sock.send("ENS-AUTH-UNAVAIL %s\r\n" % app)

            logging.debug("  Auth connection closed")
            self.sock.close()

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind( ("0.0.0.0", ENS_WLM_AUTH) )
        s.listen(1)
        logging.info("Waiting for auth requests on port %d" % ENS_WLM_AUTH)

        while True:
            conn, addr = s.accept()
            ENSAuthListener.Responder(conn, addr)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

app_policy_db = ENSAppPolicyDB(sys.argv[1])

ENSAuthListener()


import os
import sys
import socket
import time
import logging
import threading
import json
import subprocess
import tempfile
import shutil
import traceback
import copy
import httplib
import requests

ENS_PAAC_PORT = 0xed02
ENS_DISCOVERY_PORT = 0xed06
ENS_LLO_PORT = 0xed03


class ENSAppDB:

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
                logging.info("Loading application database")
                self.db = json.load(app_file)
                logging.debug(json.dumps(self.db))

    def find_app(self, app):
        app_data = None
        self.lock.acquire()

        self.load_db()
        if app in self.db:
            app_data = self.db[app]
        self.lock.release()
        return copy.deepcopy(app_data)


class ENSPAACListener(threading.Thread):

    class SessionCommand(threading.Thread):

        def __init__(self, sock, addr):
            threading.Thread.__init__(self)
            self.sock = sock
            self.client = addr
            self.start()

        def run(self):
            while True:
                try:
                    # Receive a command
                    req = self.sock.recv(1024)

                    if len(req) == 0:
                        # Socket has been closed by client.
                        logging.debug("Socket closed by client")
                        break

                    logging.debug("RX<=%s: %s" % (self.client[0], req))

                    # Start parsing the request
                    params = req.splitlines()[0].split(' ')
                    developer_id, app_id = params[1].split('.')

                    import pdb
                    pdb.set_trace()
                    if params[0] == "ENS-INQUIRE":

                        #                         r = requests.get("http://%s:%d/api/discover/%s/%s?client=%s" %
                        #                                          (core, 5000, developer_id, app_id, self.client[0]))
                        r = requests.get(
                            "http://localhost:5000/api/discover/ens/latency-test?client=127.0.0.1",)

                        if r.status_code == httplib.OK:
                            cloudlets = json.dumps(r.json())
                            logging.debug(
                                "TX=>%s: ENS-INQUIRE-OK %s.%s\r\n%s" % (self.client[0], developer_id, app_id, cloudlets))
                            self.sock.send(
                                "ENS-INQUIRE-OK %s.%s\r\n%s\r\n" % (developer_id, app_id, cloudlets))
                        else:
                            logging.debug("TX=>%s: ENS-INQUIRE-UNAVAIL %s.%s %d" %
                                          (self.client[0], developer_id, app_id, r.status_code))
                            self.sock.send(
                                "ENS-INQUIRE-UNAVAIL %s.%s %d\r\n" % (developer_id, app_id, r.status_code))

                    elif params[0] == "ENS-SERVICE":
                        cloudlet = params[2]
                        probed_rtt = params[3]

                        app_data = app_db.find_app(
                            "%s.%s" % (developer_id, app_id))

                        import pdb
                        pdb.set_trace()
                        r = requests.post("http://%s:%d/api/llo/%s/%s/%s" % (core, ENS_LLO_PORT, developer_id, app_id, cloudlet),
                                          headers={
                                              "Content-Type": "application/json"},
                                          data=json.dumps(app_data))

                        if r.status_code == httplib.OK:
                            rsp_data = r.json()

                            # Extract the client bindings into a succinct list
                            # for the client
                            bindings = {}
                            for ms_name, ms_data in rsp_data.iteritems():
                                for event_name, binding in ms_data.iteritems():
                                    bindings[
                                        ms_name + "." + event_name] = binding

                            logging.debug("TX=>%s: ENS-SERVICE-OK %s.%s\r\n%s" %
                                          (self.client[0], developer_id, app_id, json.dumps(bindings)))
                            self.sock.send(
                                "ENS-SERVICE-OK %s.%s\r\n%s\r\n" % (developer_id, app_id, json.dumps(bindings)))
                        else:
                            logging.debug("TX=>%s ENS-SERVICE-UNAVAIL %s.%s %d" %
                                          (self.client[0], developer_id, app_id, r.status_code))
                            self.sock.send(
                                "ENS-SERVICE-UNAVAIL %s.%s %d\r\n" % (developer_id, app_id, r.status_code))

                except Exception as e:
                    logging.error(
                        "Exception processing platform app@cloud command:\n%s" % traceback.format_exc())
                    break

            logging.debug("Close connection from %s" % self.client[0])
            self.sock.close()

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", ENS_PAAC_PORT))
        s.listen(1)
        logging.info("Waiting for session requests on port %d" % ENS_PAAC_PORT)

        while True:
            conn, addr = s.accept()
            ENSPAACListener.SessionCommand(conn, addr)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

#app_db = ENSAppDB(sys.argv[2])
app_db = ENSAppDB("C:/Users/gur40998/workspace/metaswitch/sample/app.db")

core = sys.argv[1]

ENSPAACListener()

import os, sys, socket, time
import logging
import threading
import json
import subprocess
import tempfile
import shutil
import traceback
import copy

ENS_WLM_SESSION = 0xed02

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


class ENSPortManager:
    def __init__(self, port_ranges):
        self.lock = threading.Lock()
        self.port_map = {}
        self.free_ports = []
        for range in port_ranges:
            for port in xrange(range[0], range[1]+1):
                self.port_map[port] = "free"
                self.free_ports.append(port)

    def assign_port(self):
        self.lock.acquire()
        port = 0
        if self.free_ports:
            port = self.free_ports.pop(0)
            self.port_map[port] = "assigned"
        self.lock.release()
        return port

    def release_port(self, port):
        self.lock.acquire()
        self.port_map[port] = "free"
        self.free_ports.append(port)
        self.lock.release()


class ENSDispatchProgrammer:
    def __init__(self, pipe):
        self.file = open(pipe, 'w')
        logging.info("Connected to dispatcher")

    def send(self, cmd):
        cmdtext = json.dumps(cmd,separators=(',',':'))
        logging.info("Sending dispatcher command: %s" % cmdtext)
        self.file.write("%s\n" % cmdtext)
        self.file.flush()

    def __term__(self):
        self.file.close()


class ENSWorkload:
    def __init__(self, session_id, app, m_service, workload_id, data):
        self.session_id = session_id
        self.workload_id = workload_id
        self.name = "ens.%d.%s.%s.%s" % (session_id, app, m_service, workload_id)
        self.data = data
        self.image = self.data["image"]
        self.proc = None
        self.status = "starting"
        self.container = None

    def start(self):
        # Create a temporary home directory for the workload
        self.tmpdir = tempfile.mkdtemp()

        # Pull the container image from the repository
        cmd = ["docker","pull"]
        cmd.append("repo.edgenet.cloud:5000/ens/%s" % self.image)
        try:
            # Launch the container - grab container ID from first line of output
            subprocess.call(cmd)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to download workload image: %s" % e.output)
            self.status = "failed"
            return

        # Start the container
        cmd = ["docker","run","-d","--name",self.name]
        cmd.append("repo.edgenet.cloud:5000/ens/%s" % self.image)
        cmd.append("%s" % json.dumps({"id": self.session_id, "events": self.data["events"]},separators=(',',':')))
        logging.debug("Launching container %s" % ' '.join(cmd))

        try:
            # Launch the container - grab container ID from first line of output
            self.status = "running"
            self.container = subprocess.check_output(cmd).splitlines()[0]

            # Get the PID of the container.
            cmd = ["docker","inspect","-f","'{{.State.Pid}}'", self.container]
            self.pid = int(subprocess.check_output(cmd).splitlines()[0].strip("'"))
            logging.info("Launched container %s for workload %s, pid %s" % (self.container, self.name, self.pid))

        except subprocess.CalledProcessError as e:
            logging.error("Failed to launch container: %s" % e.output)
            self.status = "failed"

    def stop(self):
        # Stop the container
        if self.status == "running" and self.container:
            cmd = ["docker","stop",self.container]
            try:
                subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info("Stopping container %s for workload %s" % (self.container, self.name))
            except:
                pass

        self.update_status({"status": "stopped"})

    def update_status(self, report):
        if report["status"] != self.status:
            self.status = report["status"]
            self.code = report["code"]
            logging.info("Workload %s status is now %s" % (self.name, self.status))

            if self.status == "stopped":
                # Remove the docker process (do this asynchronously)
                if self.container:
                    cmd = ["docker","rm",self.container]
                    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    logging.info("Removing container %s for workload %s" % (self.container, self.name))


    def event_bindings(self):
        return self.data["events"]

    def __term__(self):
        self.stop()

class ENSMicroservice:
    def __init__(self, session_id, app, m_service, data):
        self.session_id = session_id
        self.app = app
        self.m_service = m_service
        self.data = data
        self.workloads = {}

        # Create workloads
        for k,v in self.data["workloads"].iteritems():
            self.workloads[k] = ENSWorkload(session_id, app, m_service, k, v)

    def start(self):
        # Start the workloads
        logging.info("Starting microservice %s workloads" % self.m_service)
        for w in self.workloads.itervalues():
            w.start()
        logging.info("Started microservice %s workloads" % self.m_service)

    def stop(self):
        # Stop any active workloads
        for workload in self.workloads.itervalues():
            workload.stop()

    def update_status(self, report):
        for workload_report in report:
            if workload_report["workload"] in self.workloads:
                self.workloads[workload_report["workload"]].update_status(workload_report)
        return self.status()

    def status(self):
        status = "running"
        for workload in self.workloads.itervalues():
            if status == "running" and workload.status == "starting":
                status = "starting"
            elif workload.status == "failed":
                status = workload.status
                break
            elif workload.status == "stopped":
                status = "stopped"

        if status == "stopped" or status == "failed":
            # At least one workload has stopped or failed, so stop all of them
            for workload in self.workloads.itervalues():
                if workload.status == "running" or workload.status == "starting":
                    workload.stop()

        return status

    def event_binding(self):
        workload = self.data["event"]["workload"]
        event_id = self.data["event"]["event"]
        return {"event": event_id, "pid": self.workloads[workload].pid}

    def __term__(self):
        self.stop()


class ENSSession:
    def __init__(self, session_id, app, m_service, client, probed_rtt, app_data):
        self.session_id = session_id
        self.app = app
        self.m_service = m_service
        self.client = client
        self.probed_rtt = probed_rtt
        self.app_data = app_data["app-metadata"]["microservices"][m_service]
        self.port = 0
        self.microservice = ENSMicroservice(session_id, app, m_service, app_data["microservice-metadata"][m_service])
        self.last_status = ""

    def start(self):
        # Start the microservice
        logging.info("Starting session for microservice %s (%s)" % (self.m_service, repr(self.app_data)))
        self.microservice.start()

        logging.debug("Started microservice successfully: %s" % repr(self.app_data))

        if self.app_data["exposed"]:
            # Connect the microservice to the dispatcher
            logging.debug("Connect microservice to dispatcher")
            self.port = pm.assign_port()
            logging.info("Assigned port %d" % self.port)
            cmd = {"connect": {"id": self.session_id, "port": self.port, "pid": self.microservice.event_binding()["pid"]}}
            dp.send(cmd)

    def stop(self):
        if self.app_data["exposed"]:
            # Disconnect the microservice from the dispatcher
            logging.debug("Disconnect microservice from dispatcher")
            cmd = {"disconnect": {"id": self.session_id}}
            dp.send(cmd)
            logging.info("Releasing port %d" % self.port)
            pm.release_port(self.port)
            self.port = 0

        # Stop the microservice.
        self.microservice.stop()

    def update_status(self, report):
        status = self.microservice.update_status(report)
        if status != self.last_status:
            logging.info("Microservice %s.%s status is now %s" % (self.app, self.m_service, status))
            self.last_status = status

        if status == "stopped" or status == "failed":
            if self.app_data["exposed"] and self.port != 0:
                # Disconnect the microservice from the dispatcher
                logging.debug("Disconnect microservice from dispatcher")
                cmd = {"disconnect": {"id": self.session_id}}
                dp.send(cmd)
                logging.info("Releasing port %d" % self.port)
                pm.release_port(self.port)
                self.port = 0

    def status(self):
        return self.microservice.status()

    def workloads(self):
        return self.microservice.workloads()

    def client_binding(self):
        if self.app_data["exposed"]:
            return {"port": self.port}
        else:
            return {}

    def __term__(self):
        self.stop()


class ENSSessionManager():
    class WorkloadMonitor(threading.Thread):
        def __init__(self, sm):
            threading.Thread.__init__(self)
            self.sm = sm
            self.cmd = ["docker","ps","-a","--format","\"{{.ID}}:{{.Names}}:{{.Status}}\""]

        def run(self):
            while True:
                # Get status of all containers in the system.
                logging.debug("Starting workload check")
                clist = subprocess.check_output(self.cmd).splitlines()

                # Transform the list into a dictionary of lists indexed on the session_id
                report = {}
                for c in clist:
                    id, name, status = c.split(":")
                    if name.startswith("ens."):
                        try:
                            pre, session_id, app, m_service, workload_id = name.split('.',5)
                            session_id = int(session_id)
                            if session_id not in report:
                                report[session_id] = []
                            status, code, r = status.split(' ',2)
                            code = code[1:-1]
                            if status == "Up":
                                status = "running"
                            elif status == "Exited" and code == "0":
                                status = "stopped"
                            else:
                                status = "failed"

                            workload_report = {"workload": workload_id, "status": status, "code": code}
                            report[session_id].append(workload_report)
                        except:
                            pass

                self.sm.update_status(report)

                logging.debug("Completed workload check, sleeping")
                time.sleep(1)

    def __init__(self):
        self.lock = threading.Lock()
        self.next_session_id = int(time.time())
        self.sessions = {}
        self.session_by_m_service = {}
        self.session_by_client = {}
        self.monitor = ENSSessionManager.WorkloadMonitor(self)
        self.monitor.start()

    def new_session(self, app, m_service, client, probed_rtt):
        app_data = app_db.find_app(app)
        if app_data and m_service in app_data["app-metadata"]["microservices"]:
            # Create the session objects while holding the session manager
            # lock.  None of this should block.
            self.lock.acquire()
            session_id = self.next_session_id
            self.next_session_id = self.next_session_id + 1
            logging.info("Creating session %s" % session_id)
            session = ENSSession(session_id, app, m_service, client, probed_rtt, app_data)
            self.add_session(session_id, session)
            self.lock.release()

            # Start the session without the lock as this involves issuing
            # blocking commands.
            session.start()

            return session
        else:
            return None

    def update_status(self, report):
        # Update status of session workloads.  Do this without the lock.
        for session_id, session_report in report.iteritems():
            if session_id in self.sessions:
                self.sessions[session_id].update_status(session_report)

        # Garbage collect any stopped sessions
        self.lock.acquire()
        for session_id in self.sessions.keys():
            status = self.sessions[session_id].status()
            if status == "failed" or status == "stopped":
                if self.sessions[session_id].status() == "failed":
                    logging.error("Session %d failed" % session_id)
                logging.info("Garbage collect session %d" % session_id)
                self.del_session(session_id, self.sessions[session_id])

        self.lock.release()

    def add_session(self, session_id, session):
        self.sessions[session_id] = session
        m_service_key = "%s.%s" % (session.app, session.m_service)
        if m_service_key not in self.session_by_m_service:
            self.session_by_m_service[m_service_key] = []
        self.session_by_m_service[m_service_key].append(session)
        if session.client not in self.session_by_client:
            self.session_by_client[session.client] = []
        self.session_by_client[session.client].append(session)

    def del_session(self, session_id, session):
        m_service_key = "%s.%s" % (session.app, session.m_service)
        del self.sessions[session_id]
        if m_service_key in self.session_by_m_service:
            self.session_by_m_service[m_service_key].remove(session)
            if not self.session_by_m_service[m_service_key]:
                del self.session_by_m_service[m_service_key]
        if session.client in self.session_by_client:
            self.session_by_client[session.client].remove(session)
            if not self.session_by_client[session.client]:
                del self.session_by_client[session.client]

    def __term__(self):
        pass


class ENSSessionListener(threading.Thread):

    class SessionCommand(threading.Thread):
        def __init__(self, sock, addr):
            threading.Thread.__init__(self)
            self.sock = sock
            self.client = addr
            self.start()

        def run(self):
            try:
                # Receive the command
                req = self.sock.recv(1024)
                logging.debug("Received: %s" % req)

                # Extract the app and microservice identifier
                params = req.splitlines()[0].split(' ')

                if params[0] == "ENS-CONNECT":
                    app, m_service = params[1].split('.')
                    probed_rtt = params[2]
                    logging.debug("Received session request from client %s for %s.%s" % (self.client, app, m_service))

                    session = sm.new_session(app, m_service, self.client, probed_rtt)

                    # Sleep for a second to give the workloads a chance to open ports etc.
                    # @@@ TODO - need to find a better synchronization method
                    time.sleep(1)

                    if session:
                        cbinding = session.client_binding()
                        logging.debug("Send ENS-CONNECT-OK %s.%s\r\n%s" % (app, m_service, json.dumps(cbinding)))
                        self.sock.send("ENS-CONNECT-OK %s.%s\r\n%s\r\n" % (app, m_service, json.dumps(cbinding)))
                    else:
                        logging.debug("Send ENS-CONNECT-UNAVAIL %s.%s" % (app, m_service))
                        self.sock.send("ENS-CONNECT-UNAVAIL %s.%s\r\n" % (app, m_service))
            except Exception as e:
                logging.error("Exception starting microservice:\n%s" % traceback.format_exc())
                pass

            #self.sock.close()

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind( ("0.0.0.0", ENS_WLM_SESSION) )
        s.listen(1)
        logging.info("Waiting for session requests on port %d" % ENS_WLM_SESSION)

        while True:
            conn, addr = s.accept()
            ENSSessionListener.SessionCommand(conn, addr)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

app_db = ENSAppDB(sys.argv[1])

sm = ENSSessionManager()
pm = ENSPortManager([(0xed10, 0xedff)])
dp = ENSDispatchProgrammer('/tmp/ens/dispatcher.pipe')

ENSSessionListener()



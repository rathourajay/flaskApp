import os, sys, time
import logging
import threading
import json
import subprocess
import tempfile

import flask, httplib
from flask import Flask, request, Response, jsonify

ENS_CLC_PORT = 0xed04

clc = Flask(__name__)

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
    def __init__(self, session_id, app_id, ms_name, ms_data, app_ms_data):
        self.session_id = session_id
        self.app_id = app_id
        self.ms_name = ms_name
        self.ms_data = ms_data
        self.app_ms_data = app_ms_data
        self.workloads = {}

        # Create workloads
        for k,v in self.ms_data["workloads"].iteritems():
            self.workloads[k] = ENSWorkload(session_id, app_id, ms_name, k, v)

    def start(self):
        # Start the workloads
        logging.info("Starting microservice %s workloads" % self.ms_name)
        for w in self.workloads.itervalues():
            w.start()
        logging.info("Started microservice %s workloads" % self.ms_name)

    def stop(self):
        # Stop any active workloads
        for workload in self.workloads.itervalues():
            if workload.status == "running" or workload.status == "starting":
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

    def bindings(self):
        workload = self.ms_data["event"]["workload"]
        event_id = self.ms_data["event"]["event"]
        return {"event": event_id, "pid": self.workloads[workload].pid}

    def __term__(self):
        self.stop()


class ENSSession:
    def __init__(self, session_id, app_id, app_data):
        self.session_id = session_id
        self.app_id = app_id
        self.app_data = app_data
        self.microservices = {}
        for ms_name,ms_data in app_data["microservice-metadata"].iteritems():
            if ms_name in app_data["app-metadata"]["microservices"]:
                app_ms_data = app_data["app-metadata"]["microservices"][ms_name]
                self.microservices[ms_name] = ENSMicroservice(session_id, app_id, ms_name, ms_data, app_ms_data)
        self.status = "init"
        self.bindings = {}
        self.client_bindings = {}

    def start(self):
        logging.info("Starting session %d for %s" % (self.session_id, self.app_id))

        # Start the microservices and collect interface bindings
        for microservice in self.microservices.itervalues():
            logging.info("Starting microservice %s" % microservice.ms_name)
            microservice.start()
            self.bindings[microservice.ms_name] = microservice.bindings()
            logging.debug("Started microservice %s" % microservice.ms_name)

        # Program the session and bindings to the event dispatcher and collect
        # bindings to report to the client
        for ms_name, binding in self.bindings.iteritems():
            if self.app_data["app-metadata"]["microservices"][ms_name]["exposed"]:
                binding["port"] = pm.assign_port()
                self.client_bindings[ms_name] = {binding["event"]: public_ip + ":" + str(binding["port"])}
                cmd = {"connect": {"id": self.session_id, "port": binding["port"], "pid": binding["pid"]}}
                dp.send(cmd)

    def stop(self):
        # Stop the microservices.
        for microservice in self.microservices.itervalues():
            microservice.stop()

        # Disconnect the session from the event dispatcher
        logging.debug("Disconnect session from dispatcher")
        cmd = {"disconnect": {"id": self.session_id}}
        dp.send(cmd)

    def update_status(self, report):
        logging.debug("Process status update for session %s: %s" % (self.session_id, report))
        status = "running"
        for microservice in self.microservices.itervalues():
            ms_status = microservice.update_status(report)
            if status == "running" and ms_status == "starting":
                status = "starting"
            elif ms_status == "failed":
                status = "failed"
            elif status != "failed" and ms_status == "stopped":
                status = "stopped"

        if status != self.status:
            self.status = status
            logging.info("Session %d status is now %s" % (self.session_id, self.status))

            if self.status == "stopped" or self.status == "failed":
                # Disconnect the session from the event dispatcher
                logging.debug("Disconnect session from dispatcher")
                cmd = {"disconnect": {"id": self.session_id}}
                dp.send(cmd)

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
                #logging.debug("Starting workload check")
                clist = subprocess.check_output(self.cmd).splitlines()

                # Transform the list into a dictionary of lists indexed on the session_id
                report = {}
                for c in clist:
                    id, name, status = c.split(":")
                    if name.startswith("ens."):
                        try:
                            pre, session_id, developer_id, app_id, m_service, workload_id = name.split('.',5)
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

                #logging.debug("Completed workload check, sleeping")
                time.sleep(1)

    def __init__(self):
        self.lock = threading.Lock()
        self.next_session_id = int(time.time())
        self.sessions = {}
        self.sessions_by_app_id = {}
        self.monitor = ENSSessionManager.WorkloadMonitor(self)
        self.monitor.start()

    def new_session(self, app_id, app_data):
        # Create the session objects while holding the session manager
        # lock.  None of this should block.
        self.lock.acquire()
        session_id = self.next_session_id
        self.next_session_id = self.next_session_id + 1
        logging.info("Creating session %s" % session_id)
        session = ENSSession(session_id, app_id, app_data)
        self.add_session(session_id, session)
        self.lock.release()

        # Start the session without the lock as this involves issuing
        # blocking commands.
        session.start()

        # Wait for one second for workloads to ensure dispatcher and
        # workloads are connected.
        time.sleep(1)

        return session

    def update_status(self, report):
        # Update status of session workloads.  Do this without the lock.
        logging.debug("Workload report: %s" % report)
        for session_id, session_report in report.iteritems():
            if session_id in self.sessions:
                self.sessions[session_id].update_status(session_report)

        # Garbage collect any stopped sessions
        self.lock.acquire()
        for session_id in self.sessions.keys():
            status = self.sessions[session_id].status
            if status == "failed" or status == "stopped":
                if self.sessions[session_id].status == "failed":
                    logging.error("Session %d failed" % session_id)
                logging.info("Garbage collect session %d" % session_id)
                self.del_session(session_id, self.sessions[session_id])

        self.lock.release()

    def add_session(self, session_id, session):
        self.sessions[session_id] = session
        app_id = session.app_id
        if app_id not in self.sessions_by_app_id:
            self.sessions_by_app_id[app_id] = []
        self.sessions_by_app_id[app_id].append(session)

    def del_session(self, session_id, session):
        app_id = session.app_id
        del self.sessions[session_id]
        if app_id in self.sessions_by_app_id:
            self.sessions_by_app_id[app_id].remove(session)
            if not self.sessions_by_app_id[app_id]:
                del self.sessions_by_app_id[app_id]

    def __term__(self):
        pass


@clc.route("/api/clc/<developer_id>/<app_id>", methods=["POST"])
def provision(developer_id, app_id):

    metadata = request.get_json()

    if metadata == None:
        return Response(status=httplib.BAD_REQUEST)

    app = "%s.%s" % (developer_id, app_id)

    session = sm.new_session(app, metadata)

    rsp = jsonify(session.client_bindings)
    return rsp

@clc.route("/api/clc/<developer_id>/<app_id>/<uuid>", methods=["DELETE"])
def delete(developer_id, app_id, uuid):

    return Response(status=httplib.BAD_REQUEST)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

public_ip = sys.argv[1]

sm = ENSSessionManager()
pm = ENSPortManager([(0xed10, 0xedff)])
dp = ENSDispatchProgrammer('/tmp/ens/dispatcher.pipe')

# Start the Flask web server (HTTP)
clc.run(host="0.0.0.0", port=ENS_CLC_PORT, threaded=True)

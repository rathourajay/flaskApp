import os
import sys
import time
import logging
import threading
import json
import subprocess
import tempfile
import demjson
import logging
import requests
import uuid
import socket

import paramiko
import flask
import httplib
from flask import Flask, request, Response, jsonify

import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# TODO:
# 1. WorkloadMonitor need to change as per following:
# https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
#
# 2. Pod 'restartPolicy' -- Never
#
# 3. Even API gaterway support
##

#public_ip = '172.19.74.243'
public_ip = '127.0.0.1'

CLC_PORT = 0xed04

# This port is used by cloudlet controller to register EVENT API's to
# EVENT API Gateway
EAGW_PORT = 0xed05

# This port is used by cloudlet controller to register HTTP API's to HTTP
# API Gateway
HAGW_PORT = 32336

# Access to client is provided through HTTP API Gateway Proxy Port.
HAGWP_PORT = 30558

EAGW_IP = "172.19.74.226"

COMPUTE_USERNAME = 'root'
COMPUTE_PASSWORD = 'ubuntu'

CRLF = "\r\n"

public_ips = {}
public_ips['kube-master-test1'] = '172.19.74.219'
public_ips['kube-slave-test1'] = '172.19.74.226'


from flask import Flask, request, Response
import requests
import json
import os

MEC_CLC_PORT = 0xed24
DOCKER_GLOBAL_REG_UNAME = 'testuser'
DOCKER_GLOBAL_REG_PASS = 'testpassword'
DOCKER_LOCAL_REG_UNAME = 'testuser'
DOCKER_LOCAL_REG_PASS = 'testpassword'
LOCAL_REG_URL = '10.206.86.46:20000'
GLOBAL_REG_URL = '10.206.86.27:33000'


clc = Flask(__name__)


class PortManager:

    def __init__(self, port_ranges):
        self.lock = threading.Lock()
        self.port_map = {}
        self.free_ports = []
        for range in port_ranges:
            for port in xrange(range[0], range[1] + 1):
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


"""
A TCP Client Class.
"""


class TCPClient:

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # set TCP_NODELAY to 1 to disable Nagle i.e. make it non-block
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self.sock.connect((host, port))
        self.rfile = self.sock.makefile("rb")  # buffered

    def writeline(self, line):
        self.sock.send(line + CRLF)  # unbuffered write

    def read(self, maxbytes=None):
        if maxbytes is None:
            return self.rfile.read()
        else:
            return self.rfile.read(maxbytes)

    def readline(self):
        s = self.rfile.readline()
        if not s:
            raise EOFError
        if s[-2:] == CRLF:
            s = s[:-2]
        elif s[-1:] in CRLF:
            s = s[:-1]
        return s

    def close(self):
        if self.rfile:
            self.rfile.close()
            self.sock.close()
            self.rfile = self.sock = None

    def __term__(self):
        close(self)

"""
Class for registering Event API with Event API Gateway
"""


class EventApiGateway:

    def __init__(self, ip, port):
        self.client = TCPClient(ip, port)
        logging.info("Connected to Event API Gateway")

    def send(self, cmd):
        cmdtext = json.dumps(cmd, separators=(',', ':'))
        logging.info("Sending Event API Gateway command: %s" % cmdtext)
        self.client.writeline(cmdtext)
        rsp = self.client.readline()
        logging.info("Response: %s" % rsp)

    def __term__(self):
        self.client.close()


"""
Class for regitering HTTP API with  HTTP API Gateway

TODO:
1. Error handling
"""


class HttpApiGateway:

    def __init__(self, ip, port):
        self.hagw_ip = ip
        self.hagw_port = port

    def ip(self):
        return self.hagw_ip

    def port(self):
        return self.hagw_port

    def endpoint(self):
        ep = "http://%s:%d" % (self.hagw_ip, HAGWP_PORT)
        return ep

    def create_consumer(self, app_id):
        url = "http://%s:%d/consumers" % (self.hagw_ip, self.hagw_port)
        data = {
            'username': app_id
        }

        resp = requests.post(url, data=data)
        logging.debug("<---- Consumer Creation Response ------>")
        logging.debug(resp.text)

        data = resp.json()
        return data.get('key')

    def delete_consumer(self, app_id):
        url = "http://%s:%d/consumers/%s" % (self.hagw_ip,
                                             self.hagw_port, app_id)
        resp = requests.delete(url)

        logging.debug("<---------- Consumer Delete Response -------------->")
        logging.debug(resp.text)

    def check_plugin(self):
        url = "http://%s:%d/plugins" % (self.hagw_ip, self.hagw_port)
        resp = requests.get(url)
        data = resp.json()
        plugins = data.get('data')
        is_present = 0

        for plugin in plugins:
            if (plugin['name'] == 'key-auth'):
                is_present = 1
                break

        return is_present

    def auth_plugin(self, api, consumer_id):
        url = "http://%s:%d/apis/%s/plugins/" % (
            self.hagw_ip, self.hagw_port, api)
        data = {
            'name': 'key-auth',
            'config.key_names': 'API-KEY',
            'consumer_id': consumer_id
        }

        resp = requests.post(url, data=data)
        logging.debug("<---- Plugin Creation Response ------>")
        logging.debug(resp.text)

    def token(self, app_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        url = "http://%s:%d/consumers/%s/key-auth" % (
            self.hagw_ip, self.hagw_port, app_id)

        data = {}
        resp = requests.post(url, data=data, headers=headers)

        logging.debug("<---- Auth Key Response ------>")
        logging.debug(resp.text)

        data = resp.json()
        return data.get('key')

    def apis(self, uuid):
        url = "http://%s:%d/apis" % (self.hagw_ip, self.hagw_port)
        resp = requests.get(url)
        data = resp.json()
        return data.get('data')

    def register_api(self, api_context_name, upstream_url, request_path):
        url = "http://%s:%d/apis" % (self.hagw_ip, self.hagw_port)
        data = {
            'name': api_context_name,
            'upstream_url': upstream_url,
            'request_path': request_path,
            'strip_request_path': 'true'
        }

        resp = requests.post(url, data=data)
        logging.debug("<---- API Register Response Response ------>")
        logging.debug(resp.text)

    def unregister_api(self, api):
        url = "http://%s:%d/apis/%s" % (HAGW_IP, HAGW_PORT, api)
        resp = requests.delete(url)
        logging.debug("<---- API UnRegister Response ------>")
        logging.debug(resp.text)


class KubeClient:

    class KubeWorkloads:

        def __init__(self, pod):
            self.pod = pod

        def get_container_status(self, cn_name):
            for container_status in self.pod.status.container_statuses:
                if container_status.name == cn_name:
                    return container_status

            return None

        def get_container_id(self, cn_name):
            container_status = self.get_container_status(cn_name)
            if container_status:
                return container_status.container_id.split('//')[1]

            return None

        def get_host_ip(self, cn_name):
            return self.pod.status.host_ip

        def get_node_name(self):
            return self.pod.spec.node_name

        def get_pid(self, cn_name):
            container_id = self.get_container_id(cn_name)
            if container_id:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(public_ips[
                               self.get_node_name()], username=COMPUTE_USERNAME, password=COMPUTE_PASSWORD)

                stdin, stdout, stderr = client.exec_command(
                    "docker inspect -f '{{.State.Pid}}' " + container_id)
                for line in stdout:
                    pid = line.strip('\n')
                    break

                client.close()

                return pid

            return None

        def dump(self):
            logging.info("<------------ POD Data ---------------->")
            logging.info(self.pod)

    def __init__(self, kconfig_file=None):
        if kconfig_file == None:
            kconfig_file = '/etc/kubernetes/admin.conf'

        # Kubernetes configuration file
        config.load_kube_config(kconfig_file)

        # Kubernetes Access Token. This token is generated at the time we configure Kubernetes Master and remains same unless we tear down the cluster
        # TODO: Should read from the environment or configuration file
        client.configuration.api_key_prefix['authorization'] = 'Bearer'
        client.configuration.api_key[
            'authorization'] = "ZXlKaGJHY2lPaUpTVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUprWldaaGRXeDBJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpXTnlaWFF1Ym1GdFpTSTZJbVJsWm1GMWJIUXRkRzlyWlc0dFluTndjV1lpTENKcmRXSmxjbTVsZEdWekxtbHZMM05sY25acFkyVmhZMk52ZFc1MEwzTmxjblpwWTJVdFlXTmpiM1Z1ZEM1dVlXMWxJam9pWkdWbVlYVnNkQ0lzSW10MVltVnlibVYwWlhNdWFXOHZjMlZ5ZG1salpXRmpZMjkxYm5RdmMyVnlkbWxqWlMxaFkyTnZkVzUwTG5WcFpDSTZJbUl5TlRCak5qZzVMV1poTURJdE1URmxOaTFpTURNMExXWmhNVFl6WldNM056UmxZeUlzSW5OMVlpSTZJbk41YzNSbGJUcHpaWEoyYVdObFlXTmpiM1Z1ZERwa1pXWmhkV3gwT21SbFptRjFiSFFpZlEuYS1FcHAwTmJQY1dSR0RadzQwcEFIYi1sa090OElqakdiZk1qd20wU29lSGVfME00a2VtMXREelktZklfc3ZXaFRUY2RkbjM4WHIwSl9tV1BES3ltNnp1My0tN0t1TXVtQmo2YjZWYzFiNGtwVTh5VmpSeGJpYUNkMHVoUkYtWWVwZi0tWkwyWXp5cktPV2hDZno1V0JUSXpOT2NlMG52aU9ab1pnVjhjdlJfZEpheXBWdFlfYWNSU09VVGVoQlNKcGh0ZzNvRjRqUElhUzdULTZsZEVhcW96LWFGWG9PVXQ1cHhCX0hLQ3NjNm1XellaRENndjAtbVJ4eS1wMzFPeTRKOFJEVS1pWlhqa1lKTUtBVWZCYjlaZXN0M0IzWXRMaG4wRVJVUXFYUk43SE52dlJYem9FTG5KS0dZUmRLTU85QThjdWVDQndkZW5rc3ZOX3dWdWNB"

        self.v1 = kubernetes.client.CoreV1Api()

    def create_namespace(self, ns_name, ns_labels):
        ns_metadata = kubernetes.client.models.V1ObjectMeta(
            name=ns_name, labels=ns_labels)
        body = kubernetes.client.V1Namespace(metadata=ns_metadata)
        try:
            response = self.v1.create_namespace(body)
            logging.info(
                "<------------ Namespace Creation Response ---------------->")
            logging.info(response)
        except ApiException as e:
            logging.error("Error in Namespace Creation: %s" % e)

    def delete_namespace(self, ns_name):
        body = kubernetes.client.V1DeleteOptions()

        try:
            response = self.v1.delete_namespace(ns_name, body)
            logging.info(
                "<---------------- Namespace Deletion Response ----------------->")
            logging.info(response)
        except ApiException as e:
            logging.error("Error in Namespace Deletion: %s" % e)

    def create_service(self, ns_name, svc_name, svc_ports, is_exposed, svc_selector):
        created_svc_ports = []

        if (is_exposed == 'True'):
            svc_type = 'NodePort'
        else:
            svc_type = 'ClusterIP'

        for svc_port in svc_ports:
            svc_port_name = "%s-%s" % (svc_name, str(svc_port))
            created_svc_port = kubernetes.client.models.V1ServicePort(
                name=svc_port_name, port=svc_port)
            created_svc_ports.append(created_svc_port)

        logging.info(created_svc_ports)
        logging.info(
            "<------------------------------- EVENT Service Creation ---------------------------------->")

        svc_spec = kubernetes.client.models.V1ServiceSpec(
            type=svc_type, ports=created_svc_ports, selector=svc_selector)

        svc_metadata = kubernetes.client.models.V1ObjectMeta(name=svc_name)
        body = client.V1Service(metadata=svc_metadata, spec=svc_spec)

        try:
            response = self.v1.create_namespaced_service(ns_name, body)
            logging.info(
                "<------------ Service Creation Response ---------------->")
            logging.info(response)

            return response
        except ApiException as e:
            logging.error("Error in Service Creation: %s" % e)

        return None

    def create_container(self, cn_name, cn_image, res_limits, cn_args=None):
        resource_req = kubernetes.client.models.V1ResourceRequirements(
            limits=res_limits)

        try:
            if cn_args:
                response = kubernetes.client.models.V1Container(
                    name=cn_name, image=cn_image, args=cn_args)
            else:
                response = kubernetes.client.models.V1Container(
                    name=cn_name, image=cn_image)

            logging.info(
                "<------------ Container Creation Response ---------------->")
            logging.info(response)

            return response
        except ApiException as e:
            logging.error("Error in Container Creation: %s" % e)

        return None

    def create_replication_controller(self, ns_name, pod_labels, pod_containers):
        try:
            pod_metadata = kubernetes.client.models.V1ObjectMeta(
                labels=pod_labels)
            pod_spec = kubernetes.client.models.V1PodSpec(
                containers=pod_containers)
            pod_template_spec = kubernetes.client.models.V1PodTemplateSpec(
                metadata=pod_metadata, spec=pod_spec)

            rc_name = pod_labels['microservice_id'] + '-rc-' + \
                pod_labels['developer_id'] + "-" + pod_labels['application_id']
            rc_selector = {'developer_id': pod_labels['developer_id'], 'application_id': pod_labels[
                'application_id'], 'session_id': pod_labels['session_id']}
            rc_meta = kubernetes.client.models.V1ObjectMeta(name=rc_name)
            rc_spec = kubernetes.client.models.V1ReplicationControllerSpec(
                selector=rc_selector, template=pod_template_spec)

            body = kubernetes.client.V1ReplicationController(
                metadata=rc_meta, spec=rc_spec)

            response = self.v1.create_namespaced_replication_controller(
                ns_name, body)

            # TODO:
            # 1. sleep() should not be used; instead we should query the pod
            # status from the Kubernetes
            time.sleep(10)

            #logging.info("<------------ ReplicationController/POD Creation Response ---------------->")
            #kw = kc.get_KubeWorkloads(ns_name, pod_labels)
            # kw.dump()

            return response
        except ApiException as e:
            logging.error(
                "Error in ReplicationController/POD Creation: %s" % e)

            return None

    def get_KubeWorkloads(self, ns_name, labels):
        if 'developer_id' not in labels.keys():
            logging.error("Invalid label")
            return None

        response = self.v1.list_namespaced_pod(ns_name)
        if response:
            pod_data = []
            for item in response.items:
                if (item.metadata.labels != None):
                    if 'developer_id' in item.metadata.labels.keys():
                        if (item.metadata.labels['developer_id'] == labels['developer_id'] and item.metadata.labels['application_id'] == labels['application_id'] and item.metadata.labels['session_id'] == labels['session_id'] and item.metadata.labels['microservice_id'] == labels['microservice_id']):
                            pod_data.append(item)

            if len(pod_data) > 0:
                return KubeClient.KubeWorkloads(pod_data[0])

        return None


class KubeBuilder:

    def __init__(self, deployment_id, microservices):
        logging.info("KubeBuilder init started")

        self.deployment_id = deployment_id

        self.developer_id = deployment_id['developer-id']
        self.application_id = deployment_id['app-id']
        self.session_id = deployment_id['uuid']

        self.microservices = microservices

        self.ns_name = self.application_id + "-" + self.session_id
        self.ns_labels = {'developer_id': self.developer_id,
                          'application_id': self.application_id, 'session_id': self.session_id}

    def namespace_name(self):
        return self.ns_name

    def namespace_labels(self):
        return self.ns_labels

    def start(self):
        kc.create_namespace(self.namespace_name(), self.namespace_labels())

        # Start the microservices and collect interface bindings
        for microservice in self.microservices.itervalues():
            logging.info("Starting microservice %s" % microservice.ms_name)

            for w in microservice.get_workloads().itervalues():
                self.create_service(w)

                # Allocate external ports for each event interface
                self.assign_events_port(w)

            self.create_replication_controller(microservice)
            logging.debug("Started microservice %s" % microservice.ms_name)

    def assign_events_port(self, workload):
        # Allocate external ports for each event interface.
        workload_events = workload.events()
        for event in workload_events:
            event["port"] = pm.assign_port()
        workload.set_events(workload_events)

    def release_events_port(self, workload):
        # Release any external ports allocated to event interfaces.
        workload_events = workload.events()
        for event in workload_events.itervalues():
            if "port" in event and event["port"] != 0:
                pm.release_port(event["port"])
                del event["port"]
        workload.set_events(workload_events)

    # TODO :
    # 1. Stop microservice POD
    # 2. Test the both if and else part
    def stop(self, microservice=None):
        if microservice:
            # At least one workload has stopped or failed, so stop all of them

            # TODO:
            # Stop microservice POD

            for workload in microservice.get_workloads().itervalues():
                # Release ports allocated to the workload.
                self.release_events_port(workload)

        else:
            # Release ports allocated to the workload.
            for microservice in microservices.itervalues():
                for workload in microservice.get_workloads().itervalues():
                    # Release ports allocated to the workload.
                    self.release_events_port(workload)

            # Stop the microservices.
            kc.delete_namespace(self.namespace_name())

    def create_service(self, workload):
        service_selector = {'developer_id': self.developer_id,
                            'application_id': self.application_id, 'session_id': self.session_id}

        http_port = workload.http_port()
        if http_port:
            int_ports = [int(http_port)]
            response = kc.create_service(
                self.ns_name, workload.name(), int_ports, 'False', service_selector)

        if workload.get_exposed_ports():
            # service name length < 63 and must match the regex
            # [a-z0-9]([-a-z0-9]*[a-z0-9])?
            service_name = workload.name() + '-nb-exp-ext'
            response = kc.create_service(
                self.ns_name, service_name, workload.get_exposed_ports(), 'True', service_selector)
            if response:
                for sport in response.spec.ports:
                    network_binding = workload.exp_ext_network_binding(
                        sport.port)
                    network_binding["external-port"] = sport.node_port
                    workload.set_exp_ext_network_binding(network_binding)

        if workload.get_external_ports():
            service_name = self.workload_id + '-nb-exp-int'
            response = kc.create_service(
                self.ns_name, service_name, workload.get_external_ports(), 'False', service_selector)
            if response:
                for sport in response.spec.ports:
                    network_binding = workload.exp_int_network_binding(
                        sport.port)
                    network_binding["external-port"] = sport.port
                    network_binding['address'] = response.spec.cluster_ip
                    workload.set_exp_int_network_binding(network_binding)

    def create_replication_controller(self, microservice):
        try:
            v1Containers = []
            for w in microservice.get_workloads().itervalues():
                if w.get_cn_args():
                    v1Container = kc.create_container(
                        w.name(), w.get_image(), w.get_res_limits(), w.get_cn_args())
                else:
                    v1Container = kc.create_container(
                        w.name(), w.get_image(), w.get_res_limits())
                v1Containers.append(v1Container)
            logging.info(
                "<------------- Containers List which are to be created--------------->")
            logging.info(v1Containers)

            labels = {'microservice_id': microservice.name(), 'developer_id': self.developer_id,
                      'application_id': self.application_id, 'session_id': self.session_id}
            response = kc.create_replication_controller(
                self.ns_name, labels, v1Containers)
            if response:
                kw = kc.get_KubeWorkloads(self.ns_name, labels)
                self.update_workloads(microservice, kw)
                logging.info("Started microservice %s workloads" %
                             microservice.name())
        except:
            logging.error(
                "Failed to launch microservice %s workloads" % microservice.name())
            for w in microservice.get_workloads().itervalues():
                w.update_status({"status": "failed"})

    def update_workloads(self, microservice, kubeWorkloads):
        for w in microservice.get_workloads().itervalues():
            self.update_workload(w, kubeWorkloads)

    def update_workload(self, workload, kubeWorkloads):
        pid = kubeWorkloads.get_pid(workload.name())
        workload.set_pid(pid)

        cid = kubeWorkloads.get_container_id(workload.name())
        workload.set_cid(cid)
        workload.set_node_name(kubeWorkloads.get_node_name())

        exp_ext_network_bindings = workload.get_exp_ext_network_bindings()
        for network_binding in exp_ext_network_bindings.itervalues():
            network_binding['address'] = kubeWorkloads.get_node_name()
        workload.set_exp_ext_network_bindings(exp_ext_network_bindings)

        workload.update_status({"status": "running"})


class Workload:

    def __init__(self, microservice, workload_id, data):
        self.ms_resources = microservice.resources()
        self.ms_networks = microservice.networks()

        self.ns_name = microservice.namespace()

        self.developer_id = microservice.developer_id()
        self.application_id = microservice.application_id()
        self.session_id = microservice.session()
        self.ms_name = microservice.name()
        self.workload_id = workload_id

        self.ws_type = microservice.app_type()
        self.data = data
        self.image = self.data["image"]
        cpu_limit = data["resources"][0]["cpu"]
        mem_limit = data["resources"][0]["memory"]
        self.res_limits = {'cpu': cpu_limit, 'memory': mem_limit}

        self.cn_args = None
        if ((self.ws_type).lower() == "event"):
            self.cn_args = []
            self.cn_args.append("%s" % json.dumps(
                {"id": int(self.session_id), "events": self.events()}, separators=(',', ':')))

        self.pid = None
        self.cid = None

        self.exposed_ports = []
        self.exposed_ports_dict = {}
        self.external_ports = []
        self.external_ports_dict = {}

        for workload_network in self.data["networks"]:
            if microservice.is_network_external(workload_network["name"]):
                port = workload_network["port"]
                if microservice.is_network_exposed(workload_network["name"]):
                    self.exposed_ports.append(int(port))
                    self.exposed_ports_dict[port] = workload_network["name"]
                else:
                    self.external_ports.append(int(port))
                    self.external_ports_dict[port] = workload_network["name"]

        self.exp_ext_network_bindings = {}
        self.exp_int_network_bindings = {}
        self.status = "starting"

    def set_pid(self, pid):
        self.pid = int(pid)

    def set_cid(self, cid):
        self.cid = cid

    def set_node_name(self, node_name):
        self.node_name = node_name

    def get_node_name(self):
        return self.node_name

    def get_cn_args(self):
        return self.cn_args

    def update_status(self, report):
        if report["status"] != self.status:
            self.status = report["status"]
            if 'code' in report.keys():
                self.code = report["code"]

        logging.info("Workload %s status is now %s" %
                     (self.workload_id, self.status))

    def name(self):
        return self.workload_id

    def get_image(self):
        return self.image

    def get_res_limits(self):
        return self.res_limits

    def get_exposed_ports(self):
        return self.exposed_ports

    def get_external_ports(self):
        return self.external_ports

    def exp_int_network_binding(self, port):
        return self.data["networks"][self.external_ports_dict[str(port)]]

    def set_exp_int_network_binding(self, network_binding):
        network_name = self.external_ports_dict[network_binding['port']]
        self.exp_int_network_bindings[network_name] = network_binding

    def get_exp_int_network_bindings(self):
        return self.exp_int_network_bindings

    def set_exp_int_network_bindings(self, network_bindings):
        for k, v in network_bindings.iteritems():
            network_name = self.external_ports_dict[v['port']]
            self.exp_int_network_bindings[network_name] = v

    def exp_ext_network_binding(self, port):
        for network in self.data["networks"]:
            if network["name"] == self.exposed_ports_dict[str(port)]:
                return network

    def set_exp_ext_network_binding(self, network_binding):
        network_name = self.exposed_ports_dict[network_binding['port']]
        self.exp_ext_network_bindings[network_name] = network_binding

    def get_exp_ext_network_bindings(self):
        return self.exp_ext_network_bindings

    def set_exp_ext_network_bindings(self, network_bindings):
        for k, v in network_bindings.iteritems():
            network_name = self.exposed_ports_dict[v['port']]
            self.exp_ext_network_bindings[network_name] = v

    def http_apis(self):
        return self.data["httpApis"]

    def http_port(self):
        if ((self.ws_type).lower() == "event"):
            return None
        return self.data["httpApis"]["port"]

    def events(self):
        return self.data["events"]

    def set_events(self, events):
        self.data["events"] = events

    def networks(self):
        return self.data["networks"]

    # def __term__(self):
    #    self.stop()


class Microservice:

    def __init__(self, deployment_id, app_type, ms_name, ms_data, app_ms_data):
        self.deployment_id = deployment_id
        self.ns_name = self.deployment_id[
            "app-id"] + "-" + deployment_id["uuid"]
        self.session_id = deployment_id["uuid"]
        self.app_id = deployment_id["app-id"]
        self.ms_name = ms_name
        self.ms_data = ms_data
        self.app_ms_data = app_ms_data
        self.workloads = {}
        self.ms_type = app_type

        # Create workloads
        # for k,v in self.ms_data["workloads"][0].iteritems():
        #self.workloads[k] = Workload(self, k, v)
        self.workloads[self.ms_data["workloads"][0]["workloadName"]] = Workload(
            self, self.ms_data["workloads"][0]["workloadName"], self.ms_data["workloads"][0])

    def get_workloads(self):
        return self.workloads

    def namespace(self):
        return self.ns_name

    def session(self):
        return self.deployment_id['uuid']

    def developer_id(self):
        return self.deployment_id['developer-id']

    def application_id(self):
        return self.deployment_id['app-id']

    def name(self):
        return self.ms_name

    def app_type(self):
        return self.ms_type

    def resources(self):
        return self.app_ms_data["resources"][0]

    def http_apis(self):
        return self.ms_data["external"]["httpApis"]

    def is_http_api_external(self, http_api):
        return http_api in self.ms_data["external"]["httpApis"]

    def is_http_api_exposed(self, http_api):
        return http_api in self.app_ms_data["exposed"]["httpApis"]

    def events(self):
        return self.ms_data["external"]["events"]

    def networks(self):
        return self.ms_data["external"]["networks"]

    def is_network_external(self, network):
        return network in self.ms_data["external"]["networks"]

    def is_network_exposed(self, network):
        for exposed_network in self.app_ms_data["exposed"]["networks"]:
            if network == exposed_network["name"]:
                return True
        return False

    def exposed_to(self, exposed_name, client):
        if (self.app_type() == "event"):
            if self.app_ms_data["exposed"]["events"][exposed_name] == client:
                return True
        if ((self.app_type()).lower() == "http"):
            if self.app_ms_data["exposed"]["httpApis"][exposed_name] == client:
                return True

        return False

    def update_status(self, report):
        for workload_report in report:
            if workload_report["workload"] in self.workloads:
                self.workloads[workload_report["workload"]].update_status(
                    workload_report)
        # return self.status()

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

        # if status == "stopped" or status == "failed":
        #    self.kb.stop(self)

        return status

    def local_workloads(self):
        workloads = {}
        for k, v in self.workloads.iteritems():
            workloads[k] = {"pid": v.pid}
        return workloads

    def events(self):
        events = {}
        for w in self.workloads.itervalues():
            for item in w.events():
                events[item["name"]] = {"microservice": self.ms_name,
                                        "workload": w.workload_id,
                                        "binding": {"address": public_ips[w.get_node_name()],
                                                    "port": item["port"]}}
        return events

    def http_apis(self):
        access_token = hagw.token(self.app_id)
        refresh_token = "%s%s" % (access_token, "-refresh")
        hagw_url = hagw.endpoint()

        http_apis = {}
        for w in self.workloads.itervalues():
            for k, v in w.http_apis().iteritems():
                if k == "endpoints":
                    for items in v:
                        http_apis[items["name"]] = {"microservice": self.ms_name,
                                                    "workload": w.workload_id,
                                                    "binding": {"http-api-id": items["name"],
                                                                "endpoint": hagw_url,
                                                                "access-token": access_token,
                                                                "expires-in": '900',
                                                                "refresh-token": refresh_token}}
        return http_apis

    def network_bindings(self):
        bindings = {}
        for w in self.workloads.itervalues():
            for k, v in w.get_exp_ext_network_bindings().iteritems():
                bindings[k] = {"microservice": self.ms_name,
                               "workload": w.workload_id,
                               "binding": {"protocol": v["protocol"],
                                           "address": public_ips[w.get_node_name()],
                                           "port": v["external-port"]}}
        return bindings

    # def __term__(self):
    #    self.stop()


class AppInstance:

    def __init__(self, deployment_id, app_data):
        self.deployment_id = deployment_id
        self.app_id = self.deployment_id["app-id"]
        self.app_data = app_data

        api_key = "%s_%s_%s" % (self.deployment_id[
                                "developer-id"], self.deployment_id["app-id"], self.deployment_id["uuid"])
        self.api_key = api_key.encode("hex")
        self.microservices = {}
        ms_name = app_data["microserviceMetadata"][0]["microServiceName"]
        ms_data = app_data["microserviceMetadata"][0]["metadata"]
        app_ms_data = app_data["appMetadata"]["microservices"][0]
        self.microservices[ms_name] = Microservice(self.deployment_id, app_data[
                                                   "appMetadata"]["applicationType"], ms_name, ms_data, app_ms_data)
        self.status = "init"

    def start(self):
        logging.info("Starting application instance %s" %
                     json.dumps(self.deployment_id))

        self.kb = KubeBuilder(self.deployment_id, self.microservices)
        self.kb.start()
        # Program the application and bindings to the Event API Gateway
        if ((self.app_data["appMetadata"]["applicationType"]).lower() == "event"):
            workloads = {}
            events = {}
            for ms in self.microservices.itervalues():
                workloads.update(ms.local_workloads())
                for k, v in ms.events().iteritems():
                    fqevent = "%s.%s" % (ms.ms_name, k)
                    events[fqevent] = v
            cmd = {"connect": {
                "deployment-id": self.deployment_id, "workloads": workloads, "events": events}}
            eagw.send(cmd)

        if ((self.app_data["appMetadata"]["applicationType"]).lower() == "http"):
            api_paths = self.register_apis(self.kb.namespace_name())
            consumer_id = hagw.create_consumer(self.app_id)
            for api in api_paths:
                hagw.auth_plugin(api, consumer_id)

    def stop(self):
        # Stop the microservices.
        self.kb.stop()

        # Disconnect the application instance from the Event API Gateway
        logging.debug("Disconnect application instance from Event API Gateway")
        cmd = {"disconnect": {"deployment-id": self.deployment_id}}
        eagw.send(cmd)

    def register_apis(self, namespace):
        paths = []
        for ms in self.microservices.itervalues():
            for w in ms.get_workloads().itervalues():
                for api_context_name, api_context in w.http_apis().iteritems():
                    api_name = ms.name() + "." + api_context_name
                    if (ms.is_http_api_external(api_name) and ms.is_http_api_exposed(api_name)):
                        if ms.exposed_to(api_name, "app@client"):
                            api_context_name = "%s~%s" % (
                                api_context_name, self.api_key)
                            upstream_url = "http://%s.%s.svc.cluster.local:%s%s" % (
                                w.name(), namespace, w.http_port(), api_context)
                            request_path = "/%s%s" % (self.api_key,
                                                      api_context)
                            hagw.register_api(
                                api_context_name, upstream_url, request_path)
                            paths.append(api_context_name)
        return paths

    def deregister_apis(self):
        apis = hagw.apis()
        for api in apis:
            if self.api_key in api['name']:
                hagw.unregister_api(api['name'])

    def update_status(self, report):
        #logging.debug("Process status update for application %s: %s" % (self.deployment_id, report))
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
            logging.info("Application %s status is now %s" %
                         (self.deployment_id, self.status))

            if self.status == "stopped" or self.status == "failed":
                # Disconnect the application instance from the Event API
                # Gateway
                logging.debug(
                    "Disconnect application instance from Event API Gateway")
                cmd = {"disconnect": {"deployment-id": self.deployment_id}}
                eagw.send(cmd)

    def __term__(self):
        self.stop()


class AppManager():

    class WorkloadMonitor(threading.Thread):

        def __init__(self, sm):
            threading.Thread.__init__(self)
            self.sm = sm
            self.cmd = ["docker", "ps", "-a", "--format",
                        "\"{{.ID}}:{{.Names}}:{{.Status}}\""]

        def run(self):
            while True:
                # Get status of all containers in the system.
                #logging.debug("Starting workload check")
                clist = subprocess.check_output(self.cmd).splitlines()

                # Transform the list into a dictionary of lists indexed on the
                # uuid
                report = {}
                for c in clist:
                    id, name, status = c.split(":")
                    if name.startswith("ens."):
                        try:
                            pre, uuid, developer_id, app_id, m_service, workload_id = name.split(
                                '.', 5)
                            if uuid not in report:
                                report[uuid] = []
                            status, code, r = status.split(' ', 2)
                            code = code[1:-1]
                            if status == "Up":
                                status = "running"
                            elif status == "Exited" and code == "0":
                                status = "stopped"
                            else:
                                status = "failed"

                            workload_report = {
                                "workload": workload_id, "status": status, "code": code}
                            report[uuid].append(workload_report)
                        except:
                            pass

                self.sm.update_status(report)

                #logging.debug("Completed workload check, sleeping")
                time.sleep(1)

    def __init__(self):
        self.lock = threading.Lock()
        self.cloudlet_id = public_ip
        self.next_uuid = int(time.time())
        self.apps = {}
        self.apps_by_app_id = {}

        #self.monitor = AppManager.WorkloadMonitor(self)
        # self.monitor.start()

    def new_app_instance(self, developer_id, app_id, app_data):
        # Create the application instance objects while holding the manager
        # lock.  None of this should block.
        self.lock.acquire()

        uuid = str(self.next_uuid)
        self.next_uuid = self.next_uuid + 1

        deployment_id = {"cloudlet-id": self.cloudlet_id,
                         "developer-id": developer_id, "app-id": app_id, "uuid": uuid}
        logging.info("Creating application instance %s" %
                     json.dumps(deployment_id))
        app_instance = AppInstance(deployment_id, app_data[app_id])
        self.add_app_instance(deployment_id, app_instance)
        self.lock.release()
        # Start the application instance without the lock as this involves issuing
        # blocking commands.
        app_instance.start()

        # Wait for one second for workloads to ensure Event API Gateway and
        # workloads are connected.
        time.sleep(1)

        return app_instance

    def update_status(self, report):
        # Update status of application workloads.  Do this without the lock.
        #logging.debug("Workload report: %s" % report)
        for uuid, app_report in report.iteritems():
            if uuid in self.apps:
                self.apps[uuid].update_status(app_report)

        # Garbage collect any stopped application instance
        self.lock.acquire()
        for uuid in self.apps.keys():
            status = self.apps[uuid].status
            if status == "failed" or status == "stopped":
                if self.apps[uuid].status == "failed":
                    logging.error("Application %s failed" % uuid)
                logging.info("Garbage collect application %s" % uuid)
                self.del_app_instance(self.apps[uuid])

        self.lock.release()

    def add_app_instance(self, deployment_id, app_instance):
        self.apps[deployment_id["uuid"]] = app_instance
        app_fqid = "%s.%s" % (
            deployment_id["developer-id"], deployment_id["app-id"])
        if app_fqid not in self.apps_by_app_id:
            self.apps_by_app_id[app_fqid] = []
        self.apps_by_app_id[app_fqid].append(app_instance)

    def del_app_instance(self, app_instance):
        app_fqid = "%s.%s" % (
            app_instance.deployment_id["developer-id"], app_instance.deployment_id["app-id"])
        del self.apps[app_instance.deployment_id["uuid"]]
        if app_fqid in self.apps_by_app_id:
            self.apps_by_app_id[app_fqid].remove(app_instance)
            if not self.apps_by_app_id[app_fqid]:
                del self.apps_by_app_id[app_fqid]

    def __term__(self):
        pass

#*************************************************************************
# @def    Provisions Application and Associated Microservices
# @params developer_id : Developer ID
# @params app_id       : Application ID
# @params client_id    : Client ID
# @method POST
#*************************************************************************


@clc.route('/api/v1.0/clc/<developer_id>/<app_id>',  methods=["POST"])
def provision_application(developer_id, app_id):
    logging.info("Provisioning started with DEVELOPER_ID=%s APPLICATION_ID=%s" % (
        str(developer_id), str(app_id)))
    metadata = request.get_json()
    """
    metadata = {
"applications":{
"mec.latency-test":{
"app_cloud_url":{
"protocol":"http",
"ip":"172.19.74.249",
"port":"65000"
},
"enabled":"Y",
"client-regions":[
"NA",
"EU"
],
"low-latency":"Y",
"metadata":{
"app-metadata":{
"type":"event",
"microservices":{
"latencyresponder":{
"exposed":{
"http-apis":{
},
"events":{
"latencyresponder.ping":"app@client"
},
"networks":{
"latency-test-network":"app@client"
}
},
"resources":"default"
}
}
},
"microservice-metadata":{
"latencyresponder":{
"tenancy":"single",
"external":{
"http-apis":[
],
"events":[
"latencyresponder.ping"
],
"networks":[
"latency-test-network"
]
},
"workloads":{
"latencyresponder":{
"image":"anuyog27/latencyresponder",
"http-apis":{
},
"events":{
"ping":{
"fn":"latencyresponder.event_handler"
}
},
"networks":{
"latency-test-network":{
"port":"10004",
"protocol":"udp"
}
},
"resources":{
"default":{
"cpu":"250m",
"memory":"256Mi"
}
}
}
}
}
}
}
},
"mec.service-time":{
"app_cloud_url":{
"protocol":"http",
"ip":"172.19.74.249",
"port":"65000"
},
"enabled":"Y",
"client-regions":[
"NA",
"AS"
],
"low-latency":"Y",
"metadata":{
"app-metadata":{
"type":"http",
"microservices":{
"service-time":{
"exposed":{
"http-apis":{
"service-time.service-time.context1":"app@client"
},
"events":{
},
"networks":{
"service-time-network":"app@client"
}
},
"resources":"default"
}
}
},
"microservice-metadata":{
"service-time":{
"tenancy":"single",
"external":{
"events":[
],
"http-apis":[
"service-time.service-time.context1"
],
"networks":[
"service-time-network"
]
},
"workloads":{
"service-time":{
"image":"anuyog27/service-time",
"port":"10002",
"http-apis":{
"service-time.context1":"/time"
},
"events":{
},
"networks":{
"service-time-network":{
"port":"10004",
"protocol":"udp"
},
"service-time-network1":{
"port":"10003",
"protocol":"tcp"
}
},
"resources":{
"default":{
"cpu":"250m",
"memory":"256Mi"
}
}
}
}
}
}
}
}
}
}
"""
    #metadata = {app_id:metadata["applications"]["%s.%s" %(developer_id, app_id)]['metadata']}
    if metadata == None:
        return Response(status=httplib.BAD_REQUEST)

    app_instance = sm.new_app_instance(developer_id, app_id, metadata)

    rsp_data = {"deployment-id": app_instance.deployment_id,
                "microservices": []}
    print rsp_data
    for ms in app_instance.microservices.itervalues():
        ms_name = ms.ms_name
        for microservice in app_instance.app_data["appMetadata"]["microservices"]:
            if microservice["microServiceName"] == ms_name:
                app_ms_data = microservice
                app_ms_events = app_ms_data["exposed"]["events"]
                app_ms_network = app_ms_data["exposed"]["networks"]
                app_ms_http_apis = app_ms_data["exposed"]["httpApis"]

        ms_data = {
            "name": ms_name,
            "uuid": app_instance.deployment_id["uuid"],
            "http-gateway": [],
            "event-gateway": [],
            "network-binding": []
        }

        # TODO:
        # Currently passing back http-api, event and network binding exposed only to 'app@client'
        # Need to add support for CIDR
        for k, v in ms.events().iteritems():
            event = "%s.%s" % (ms_name, k)
            if event in app_ms_events and "app@client" in app_ms_events[event]:
                ms_data["event-gateway"].append({"event-id": k, "endpoint": "tcp://" + v[
                                                "binding"]["address"] + ":" + str(v["binding"]["port"])})

        for k, v in ms.network_bindings().iteritems():
            binding = "%s" % (k)
            for ms_net in app_ms_network:
                if binding in ms_net["name"] and "app@client" in ms_net["exposedTo"]:
                    ms_data["network-binding"].append({"network-id": v["microservice"], "endpoint": v["binding"][
                                                      "protocol"] + "://" + v["binding"]["address"] + ":" + str(v["binding"]["port"])})
        for ms_http_apis in ms.http_apis().itervalues():
            http_api = "%s" % (ms_http_apis["binding"]["http-api-id"])
            for app_ms_http_api in app_ms_http_apis:
                if http_api in app_ms_http_api["name"] and "app@client" in app_ms_http_api["exposedTo"]:
                    ms_data["http-gateway"].append({"http-api-id": http_api, "endpoint": ms_http_apis["binding"]["endpoint"] + "/" + app_instance.api_key, "access-token": ms_http_apis[
                                                   "binding"]["access-token"], "expires-in": ms_http_apis["binding"]["expires-in"], "refresh-token": ms_http_apis["binding"]["refresh-token"]})

        rsp_data["microservices"].append(ms_data)

    rsp = jsonify(rsp_data)
    logging.info("<--------------- Client Response ------------------>")
    logging.info(rsp)

    return rsp

#*************************************************************************
# @def    Delete Application and Associated microservices
# @params developer_id : Developer ID
# @params app_id       : Application ID
# @params uuid         : Deployment ID
# @method POST
#*************************************************************************


@clc.route("/api/v1.0/clc/<developer_id>/<app_id>/<uuid>", methods=["DELETE"])
def delete(developer_id, app_id, uuid):
    decoded_uuid = uuid.decode("hex")
    labels = decoded_uuid.split('_')

    logging.debug("uuid -- %s" % labels)
    return Response(status=httplib.BAD_REQUEST)


def generic_request(method, url, data=None,
                    auth_token=None, nova_cacert=False, content_type=None):
    #    logging.debug("url:%s, X-Auth-Token:%s, data:%s" % (url, auth_token,
    #                                                        data))
    headers = {}
    headers["Content-type"] = "application/json"
    if(content_type):
        headers["Content-type"] = content_type

    if auth_token:
        headers["X-Auth-Token"] = auth_token

    resp = method(url, headers=headers, data=data, verify=nova_cacert)
    logging.debug("Api request return code:%d" % resp.status_code)

    if resp.status_code in [401]:
        resp_body = resp.json()
        raise exceptions.Forbidden(resp_body['error']['message'])

    if resp.status_code in [403]:
        resp_body = resp.json()
        raise exceptions.Unauthorized(resp_body['error']['message'])

    elif resp.status_code not in [200, 201, 203, 204]:
        raise exceptions.RequestFailed(resp.text)
    return resp


def get_request(url, auth_token=None, nova_cacert=False):
    return generic_request(requests.get, url, auth_token=auth_token,
                           nova_cacert=nova_cacert)


def post_request(url, data, auth_token=None):
    return generic_request(requests.post, url, data, auth_token)


def get_user_token(user_name, password, tenant_name, auth_url):
    logging.debug('Getting token for user: %s from url: %s'
                  % (user_name, auth_url))

    url = auth_url + '/tokens'

    creds = {
        'auth': {
            'passwordCredentials': {
                'username': user_name,
                'password': password
            },
            'tenantName': tenant_name
        }
    }

    data = json.dumps(creds)
    resp = post_request(url, data=data)
    return resp.json()['access']


def base_url(service, auth_data, region=None):
    endpoint_type = 'publicURL'
    _base_url = None
    for ep in auth_data['serviceCatalog']:
        if ep["type"] == service:
            for _ep in ep['endpoints']:
                if region and _ep['region'] == region:
                    _base_url = _ep.get(endpoint_type)
            if not _base_url:
                # No region matching, use the first
                _base_url = ep['endpoints'][0].get(endpoint_type)
            break
    if _base_url is None:
        raise exceptions.EndpointNotFound(service)
    return _base_url


def hostname_to_ip(url, keystone_url):
    keystone_ip = keystone_url.split(':')[1]
    url_tokens = url.split(':')
    modified_url = url_tokens[0] + ":" + keystone_ip
    for i in range(2, len(url_tokens)):
        modified_url = modified_url + ":" + url_tokens[i]
    return modified_url


@clc.route('/api/clc/stats', methods=['GET'])
def get_vm_stats():

    keystone_username = 'admin'
    keystone_tenant = 'admin'
    keystone_password = 'mypass'
    keystone_url = 'http://172.19.74.14:5000/v2.0'
    clc_url = 'http://10.206.27.129:60676'
    edge_id = 'ens.aws-as-eastindia.edgenet.cloud'
    # edge_details = management_api.get_edge_details(edge_id)i
    try:
        auth_data = get_user_token(
            keystone_username, keystone_password, keystone_tenant, keystone_url)

    except (exceptions.Forbidden, exceptions.Unauthorized, exceptions.RequestFailed) as e:
        return("Exception: " + e._error_string)
    except Exception as e:
        return(e)
    token = auth_data['token']['id']
    nova_url = base_url('compute', auth_data)
    nova_url = hostname_to_ip(nova_url, keystone_url)
    resp = get_request(nova_url + '/servers/detail', auth_token=token)
    vm_details = resp.json()
    vm_data = []
    for server in vm_details['servers']:
        if server['status'] == 'ACTIVE':
            resource_id = server['id']
            tenant_id = server['tenant_id']
            ceilometer_url = base_url('metering', auth_data)
            ceilometer_url = hostname_to_ip(ceilometer_url, keystone_url)
            cpu_util_url = '/v2/meters/cpu_util?q.field=resource_id&q.op=eq&q.type=&q.value=%s&limit=1' % resource_id
            disk_usage_url = '/v2/meters/disk.usage?q.field=resource_id&q.op=eq&q.type=&q.value=%s&limit=1' % resource_id
            memory_usage_url = '/v2/meters/memory.usage?q.field=resource_id&q.op=eq&q.type=&q.value=%s&limit=1' % resource_id
            response_cpu_util = get_request(
                ceilometer_url + cpu_util_url, auth_token=token)
            uptime_url = '/os-simple-tenant-usage/%s' % (tenant_id)

            resp_cpu_util = eval(response_cpu_util.content)
            if resp_cpu_util:
                cpu_util = resp_cpu_util[0]['counter_volume']
                vm_name = resp_cpu_util[0]['resource_metadata']['display_name']
            else:
                cpu_util = "N/A"
                vm_name = "N/A"

            response_disk_usage = get_request(
                ceilometer_url + disk_usage_url, auth_token=token)
            resp_disk_usage = eval(response_disk_usage.content)
            if resp_disk_usage:
                disk_usage = resp_disk_usage[0]['counter_volume']
                total_disk_gb = int(
                    resp_disk_usage[0]['resource_metadata']['disk_gb'])
                total_disk_bytes = total_disk_gb * 1024 * 1024 * 1024
                disk_usage_percent = (disk_usage * 100) / total_disk_bytes
            else:
                disk_usage_percent = "N/A"

            response_memory_usage = get_request(
                ceilometer_url + memory_usage_url, auth_token=token)
            resp_memory_usage = eval(response_memory_usage.content)
            if resp_memory_usage:
                memroy_usage = resp_memory_usage[0]['counter_volume']
                total_memory = int(
                    resp_disk_usage[0]['resource_metadata']['memory_mb'])
                memory_usage_percent = (memroy_usage * 100) / total_memory
            else:
                memory_usage_percent = "N/A"
            nova_url = base_url('compute', auth_data)
            nova_url = hostname_to_ip(nova_url, keystone_url)
            response_uptime = get_request(
                nova_url + uptime_url, auth_token=token)
            resp_uptime_content = json.loads(
                (response_uptime.content).decode('utf-8'))

            vm_uptime_list = resp_uptime_content[
                "tenant_usage"]["server_usages"]
            if vm_uptime_list:
                for item in vm_uptime_list:
                    if item["instance_id"] == resource_id:
                        vm_uptime = item["uptime"]
                    else:
                        continue
            else:
                vm_uptime = "N/A"
            stats_dict = {}
            stats_dict["cpu_usage"] = cpu_util
            stats_dict["memory_usage"] = memory_usage_percent
            stats_dict["disk_usage"] = disk_usage_percent
            stats_dict["vm_name"] = vm_name
            stats_dict["instance_uptime"] = vm_uptime
            stats_dict["instance_id"] = resource_id
            vm_data.append(stats_dict)

    return json.dumps(vm_data)


@clc.route('/api/v1.0/clc/notify', methods=['POST'])
def update_docker_registry():
    image_tag = request.json['tag']
    docker_image_name = request.json['repository']
   # image_tag = "latest"
   # docker_image_name = "hello-world3"
    GLOBAL_REG_URL = request.json['url']

    image_catalog_url = "http://%s:%s@%s/v2/_catalog" % (
        DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL)
    tag_list_url = "http://%s:%s@%s/v2/%s/tags/list" % (
        DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL, docker_image_name)
    image_catalog_dict = json.loads(requests.get(image_catalog_url).content)
    if docker_image_name in image_catalog_dict:
        image_tag_dict = json.loads(requests.get(tag_list_url).content)

    if (docker_image_name not in image_catalog_dict['repositories']) or \
            (docker_image_name in image_catalog_dict['repositories'] and image_tag not in image_tag_dict['tags']):

        ### Commands for PULLING image from global registry ###
        login_cmd_global_reg = 'sudo docker login -u %s -p %s -e "\n" %s' % (
            DOCKER_GLOBAL_REG_UNAME, DOCKER_GLOBAL_REG_PASS, GLOBAL_REG_URL)

#        pull_cmd = 'sudo docker pull %s/%s:%s' % (
#            GLOBAL_REG_URL, docker_image_name, image_tag)
        image_tag_global = GLOBAL_REG_URL + \
            '/' + docker_image_name + ':' + image_tag

        pull_cmd = 'sudo docker pull %s' % (image_tag_global)

        logout_cmd_global_reg = "sudo docker logout %s" % (GLOBAL_REG_URL)

        ### Commands for PUSHING image to locaal registry ###
        login_cmd_local_reg = 'sudo docker login -u %s -p %s -e "\n" %s' % (
            DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL)
        create_tag_cmd = "sudo docker tag %s %s/%s:%s" % (
            image_tag_global, LOCAL_REG_URL, docker_image_name, image_tag)

        push_cmd = "sudo docker push %s/%s:%s" % (
            LOCAL_REG_URL, docker_image_name, image_tag)

        logout_cmd_local_reg = "sudo docker logout %s" % (LOCAL_REG_URL)

        print "Pulling image from global registry ========="
        os.system(
            login_cmd_global_reg + ";" + pull_cmd + ";" + logout_cmd_global_reg)
        print "Pushing Image with tag %s" % image_tag
        os.system(login_cmd_local_reg + ";" + create_tag_cmd +
                  ";" + push_cmd + ";" + logout_cmd_local_reg)
        return Response(status=200)
    else:
        response_str = "Image [", docker_image_name, "/", image_tag, "] already present in local registry"
        return Response(response=response_str, status=200)


@clc.route('/api/v1.0/clc/docker_images', methods=['GET'])
def list_docker_images():
    try:
        #list_images = 'curl -H GET "http://testuser:testpassword@10.206.86.6:20000/v2/_catalog'
        #list_tags = 'curl -H GET "http://testuser:testpassword@10.206.86.6:20000/v2/%s/tags/list"' %repo_name
        list_images_url = "http://%s:%s@%s/v2/_catalog" % (
            DOCKER_LOCAL_REG_UNAME, DOCKER_LOCAL_REG_PASS, LOCAL_REG_URL)

        image_dict = requests.get(list_images_url).content

        return image_dict
    except:
        return Response(response="ERROR_IN_FETCHING_IMAGES_LIST", status=500)


#*************************************************************************
# @def    Configure cloudlet provisioned by LLO
# NOTE:   For the moment we are just registering the cloudlet with Discovery Server.
# TODO:   Complete Configuration which involves configuring Kubernetes, API Gateway and Discovery Agent
# @params developer_id : Developer ID
# @params app_id       : Application ID
# @params client_id    : Client ID
# @method POST
#*************************************************************************
@clc.route('/api/v1.0/clc/configure/<cloudlet_id>',  methods=["POST"])
def configure(cloudlet_id):

    url = "http://%s:%d/api/v1.0/discover/%s/register" % (
        DISCOVERY_SERVER_IP, 60678, cloudlet_id)
    data = {}
    resp = requests.put(url, params=data)
    return resp.content


#*************************************************************************
# @def    Unconfigure cloudlet provisioned by LLO
# NOTE:   For the moment we are just de-registering the cloudlet with Discovery Server.
# TODO:   Complete De-Configuration which involves deconfiguring Kubernetes, API Gateway and Discovery Agent
# @params developer_id : Developer ID
# @params app_id       : Application ID
# @params client_id    : Client ID
# @method POST
#*************************************************************************
@clc.route('/api/v1.0/clc/unconfigure/<cloudlet_id>',  methods=["DELETE"])
def unconfigure(cloudlet_id):
    url = "http://%s:%d/api/v1.0/discover/%s/deregister" % (
        DISCOVERY_SERVER_IP, 60678, cloudlet_id)
    data = {}
    resp = requests.put(url, params=data)
    return resp.content


if len(sys.argv) < 3:
    print("Usage: %s <http_gateway_ip> <discovery_server_ip>" % sys.argv[0])
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

HAGW_IP = sys.argv[1]
DISCOVERY_SERVER_IP = sys.argv[2]

sm = AppManager()
pm = PortManager([(0xed10, 0xedff)])
#eagw = EventApiGateway(EAGW_IP, EAGW_PORT)
hagw = HttpApiGateway(HAGW_IP, HAGW_PORT)
kc = KubeClient('/etc/kubernetes/admin.conf')


if __name__ == '__main__':
    clc.run(host="0.0.0.0", port=CLC_PORT, debug=True, threaded=True)

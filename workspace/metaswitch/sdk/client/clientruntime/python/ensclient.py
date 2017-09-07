import logging
import asyncore, socket
import struct
import time
import json

ENS_PROBE_PORT = 0xed01
ENS_PAAC_PORT  = 0xed02

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)-15s %(levelname)-8s %(message)s')

header = struct.Struct('>I I')

class ENSSession():
    def __init__(self, app, cloudlet, interface, binding):
        logging.info("Create ENSSession to interface %s on application %s" % (interface, app))
        self.app = app
        self.cloudlet = cloudlet
        self.interface = interface
        self.binding = binding
        self.conn = None

    def connect(self):
        # Connect to port in the interface binding.
        logging.info("Connecting to ENS interface %s at %s" % (self.interface, self.binding))
        try:
            addr = self.binding.split(':')[0]
            port = int(self.binding.split(':')[1])
            self.conn = socket.create_connection( (addr, port) )
            self.conn.send(header.pack(0,1))
            rsp = header.unpack(self.conn.recv(8))
            return True
        except socket.error as e:
            logging.error("Failed to connect session: %s" % e)
            return False

    def request(self, data):
        if self.conn:
            s = json.dumps(data)
            self.conn.sendall(header.pack(len(s), 0) + s)
            hdr = header.unpack(self.conn.recv(header.size))
            rsp = self.conn.recv(hdr[0])
            return json.loads(rsp);
        else:
            return None

    def event(self, data):
        if self.conn:
            self.conn.send(json.dumps(data))

    def close(self):
        if self.conn:
            self.conn.close()
        self.conn = None

    def __term__ (self):
        close(self)


class ENSClient():

    # Prober class probes a cloudlet by opening a connection to the cloudlet
    # WLM and repeatedly measuring the round trip time until it is manually
    # destroyed.
    class Probe(asyncore.dispatcher):
        def __init__(self, cloudlet, app):
            asyncore.dispatcher.__init__(self)
            logging.info("Probe cloudlet %s for application %s" % (cloudlet, app))
            self.app = app
            self.cloudlet = cloudlet
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.connect( (self.cloudlet, ENS_PROBE_PORT) )
            except socket.error:
                pass
            self.buffer = "ENS-PROBE %s\r\n" % self.app
            self.sampling = False
            self.samples = []

        def handle_connect(self):
            pass

        def handle_error(self):
            pass

        def handle_close(self):
            logging.debug("Closing probe for cloudlet %s" % self.cloudlet)
            self.close()

        def handle_read(self):
            self.end_time = time.time()
            rsp = self.recv(8192)
            logging.debug("Received (%s): %s" % (self.cloudlet, rsp))

            if not self.sampling:
                # Check that the microservice is supported
                params = rsp.splitlines()[0].split(' ')
                if params[0] == "ENS-PROBE-OK":
                    # Microservice is supported, so save microservice data
                    self.buffer = "ENS-RTT %s\r\n" % self.app
                    self.sampling = True
                else:
                    # Microservice is not supported, so just close the socket
                    # and wait for other probes to finish.
                    self.close()
            else:
                # Must be doing RTT estimation
                rtt = self.end_time - self.start_time
                logging.debug("RTT = %f" % rtt);
                self.samples.append(rtt)
                if len(self.samples) < 10:
                    self.buffer = "ENS-RTT %s\r\n" % self.app
                else:
                    logging.debug("Completed 10 RTT probes to %s" % self.cloudlet)

        def writable(self):
            return (len(self.buffer) > 0)

        def handle_write(self):
            self.start_time = time.time()
            sent = self.send(self.buffer)
            logging.debug("Sent (%s): %s" % (self.cloudlet, self.buffer))
            self.buffer = self.buffer[sent:]

        def rtt(self):
            if len(self.samples):
                return sum(self.samples) / float(len(self.samples))
            else:
                return -1


    def __init__(self, edge_domain, app):
        self.paac = [r[4] for r in socket.getaddrinfo(edge_domain, ENS_PAAC_PORT, 0, socket.SOCK_STREAM) if r[0] == socket.AF_INET or r[0] == socket.AF_INET6]
        logging.info("Platform app@cloud locations = %s" % ','.join(["%s:%d" % (c[0], c[1]) for c in self.paac]))
        self.app = app
        self.cloudlet = ""
        self.bindings = {}
        self.probed_rtt = 0.0

    def init(self):
        # Do the inquire flow to get a candidate list of cloudlets for the app
        for paac in self.paac:
            try:
                s = socket.create_connection( paac )
                logging.debug("TX=>%s: ENS-INQUIRE %s" % (paac[0], self.app))
                s.send("ENS-INQUIRE %s\r\n" % self.app)
                rsp = s.recv(8192);
                logging.debug("RX<=%s: %s" % (paac[0], rsp))
                s.close()
                try:
                    params = rsp.splitlines()[0].split(' ')
                    if params[0] == "ENS-INQUIRE-OK":
                        cloudlets = json.loads(rsp.splitlines()[1])["cloudlets"]
                        break
                    else:
                        logging.error("Discovery server error");
                        return False
                except:
                    logging.error("Discovery server exception")
                    return False

            except socket.error as e:
                pass

        if len(cloudlets) == 0:
            logging.info("No cloudlets to probe")
            return False

        # Create probes for each cloudlet
        logging.debug("Probe cloudlets %s" % ', '.join(cloudlets))
        probes = [ENSClient.Probe(str(c), self.app) for c in cloudlets]

        # Run the probes for one second
        start = time.time()
        while (time.time() - start) < 1:
            asyncore.loop(timeout=1, count=1, use_poll=True)

        logging.info("Probes completed");
        for probe in probes:
            probe.close()

        # Pick the probe with the shortest RTT
        rtts = [(p.rtt(), p.cloudlet) for p in probes if p.rtt() != -1]
        rtts = sorted(rtts, key=lambda p: p[0])
        logging.debug(repr(rtts))

        if len(rtts) == 0:
            return False

        self.cloudlet = rtts[0][1]
        self.probed_rtt = rtts[0][0]

        # Send a service request to platform app@cloud to instantiate the application and microservices.
        for paac in self.paac:
            try:
                s = socket.create_connection( paac )
                logging.debug("TX=>%s: ENS-SERVICE %s %s %s" % (paac[0], self.app, self.cloudlet, self.probed_rtt))
                s.send("ENS-SERVICE %s %s %s\r\n" % (self.app, self.cloudlet, self.probed_rtt))
                rsp = s.recv(8192);
                logging.debug("RX<=%s: %s" % (paac[0], rsp))
                s.close()

                try:
                    params = rsp.splitlines()[0].split(' ')
                    if params[0] == "ENS-SERVICE-OK":
                        # Set up a connection for the event binding.
                        self.bindings = json.loads(rsp.splitlines()[1])
                        return True
                    else:
                        logging.error("Failed to initialize application: %s" % rsp)
                        return False
                except:
                    return False

            except socket.error:
                pass

        return False


    def connect(self, interface):
        # Check there is a binding for the requested interface
        if interface not in self.bindings:
            logging.error("Cannot connect to unknown interface %s" % interface)
            return None

        # Create an ENSSession object for the connection
        session = ENSSession(self.app, self.cloudlet, interface, self.bindings[interface])
        if session.connect():
            return session
        else:
            return None

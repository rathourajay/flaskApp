import os, sys, socket, time
import logging
import threading

ENS_WLM_PROBE   = 0xed01

class ENSProbeListener(threading.Thread):

    class Responder(threading.Thread):
        def __init__(self, sock, addr):
            threading.Thread.__init__(self)
            self.sock = sock
            self.addr = addr
            self.start()

        def run(self):
            try:
                req = self.sock.recv(1024)

                # Extract the app and microservice identifier
                params = req.splitlines()[0].split(' ')
                app, m_service = params[1].split('.')
                logging.info("Received probe request from %s for %s.%s" % (self.addr[0], app, m_service))

                # Send probe response
                logging.debug("Send ENS-PROBE-OK %s.%s" % (app, m_service))
                self.sock.send("ENS-PROBE-OK %s.%s\r\n" % (app, m_service))

                # Loop responding to RTT probe packets until the client disconnects
                while True:
                    try:
                        req = self.sock.recv(1024)
                        if len(req) > 0:
                            self.sock.send(req)
                        else:
                            break;
                    except socket.error as e:
                        logging.error("Socket error on probe responder: %s" % repr(e))
                        break
            except:
                pass

            logging.debug("Probe connection closed")
            self.sock.close()

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind( ("0.0.0.0", ENS_WLM_PROBE) )
        s.listen(10)
        logging.info("Waiting for probes on port %d" % ENS_WLM_PROBE)

        while True:
            conn, addr = s.accept()
            ENSProbeListener.Responder(conn, addr)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(filename)-16s %(lineno)4d %(message)s')

ENSProbeListener()


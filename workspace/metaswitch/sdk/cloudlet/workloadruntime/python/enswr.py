import threading
import socket
import json
import time
import ensiwc

class ENSSingleThreadReactor(threading.Thread):
    # Single threaded reactor implementation suitable only for single tenant
    # workloads that process requests sequentially
    def __init__(self, id, event):
        threading.Thread.__init__(self)

        # Parse the configuration to get the id for the shared memory interface
        # and link to the event function
        mod, fn = event["fn"].rsplit('.', 1)
        self.fn = getattr(__import__(mod), fn);
        self.iwc = ensiwc.Workload(id, 4, 10000);

    def run(self):
        while True:
            try:
                print("Waiting for data")
                data = self.iwc.recv()
                print("Received data %s" % data)
                if len(data) > 0:
                    req = json.loads(data.decode("UTF-8"))
                    rsp = json.dumps(self.fn(req)).encode("UTF-8")
                    self.iwc.send(rsp)
                    print("Sent response")
                else:
                    break
            except Exception as e:
                print("Exception processing data: %s" % e)
                break

        print("Workload scheduler for interface %s exiting" % self.fn)

class ENSWorkloadRuntime:
    def __init__(self, config):
        # Parse the configuration JSON structure
        self.config = json.loads(config)

        # Create reactors for each binding
        print("id = %d" % self.config["id"])
        self.reactors = [ENSSingleThreadReactor(self.config["id"], v) for k, v in self.config["events"].iteritems()]

    def run(self):
        for r in self.reactors:
            r.start()

        while len(self.reactors) > 0:
            time.sleep(1)
            self.reactors = [r for r in self.reactors if r.is_alive()]

        print("Exiting workload")



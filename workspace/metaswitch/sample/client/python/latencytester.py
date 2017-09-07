import sys
import time
import httplib
import json
from ensclient import ENSClient, ENSSession

if len(sys.argv) < 2:
    print("Usage: %s <dashboard host>" % sys.argv[0])
    sys.exit(1)

dashboard = sys.argv[1]

while True:
    report = {"status": "down", "cloudlet": "", "latency": 0.0}

    # Auth with  ENS platform
    #c = ENSClient("ens.edgenet.cloud", "ens.latency-test")
    c = ENSClient("127.0.0.1", "ens.latency-test")

    cumulative_time = 0.0

    if not c.init():
        print("Failed to initialize")
        report["status"] = "auth-error"
    else:
        s = c.connect("latencyresponder.ping")

        if not s:
            print("Failed to connect to microservice")
            report["status"] = "sess-error"
        else:
            report["status"] = "active"
            report["cloudlet"] = s.cloudlet
            for i in xrange(1, 11):
                data = {"iteration": i}
                start_time = time.time()
                rsp = s.request(data)
                end_time = time.time()
                if rsp != data:
                    print("Response error %s" % repr(rsp))
                print("Latency = %f" % (end_time - start_time))
                cumulative_time += (end_time - start_time)
                sys.stdout.flush()
                time.sleep(0.1)
            s.close()
            report["latency"] = cumulative_time / 10.0

    # Send the report
#     try:
#         http = httplib.HTTPConnection(dashboard, 80)
#         headers = {"Content-Type": "application/json"}
#         url = "/sample"
#         body = json.dumps(report)
#         print("Sending report: %s" % body)
#         http.request("POST", url, body, headers)
#         rsp = http.getresponse()
#     except:
#         pass

    # Sleep for five seconds then attempt to reconnect
    time.sleep(5)

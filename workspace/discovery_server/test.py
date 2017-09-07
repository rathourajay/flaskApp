import time
from datetime import datetime

heartbeat_dict = datetime.now()
time.sleep(5)
date_now = datetime.now()
time_since_last_heartbeat = (date_now - heartbeat_dict).seconds

print "now=%s, heartbeat = %s, diff= %s" % (date_now, heartbeat_dict, time_since_last_heartbeat)
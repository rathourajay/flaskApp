import time
import sys
import datetime


# time.sleep(5)
now = datetime.datetime.now()
print str(now)
time.sleep(5)
now1 = datetime.datetime.now()
print str(now1.second)
# print "Dfference:"
# diff = now1 - now
# print diff
# print "diff sec:", diff.seconds
#
# t_stored_time = datetime.datetime.now()
#
#
# def update():
#
#     while True:
#         send_heart_beat('I am up')
#         time.sleep(2)
#
#
# def send_heart_beat(msg):
#
#     print t_stored_time
#
# #     import pdb
# #     pdb.set_trace()
#     print msg
#     t_current_time = datetime.datetime.now()
#     print t_current_time
#
#     diff = t_current_time - t_stored_time
#     if diff.seconds > 10:
#         print "inactive"
#     else:
#         print "active"
#     t_stored_time = t_current_time


#     print t_stored_time
#     # for first time
#     if ((t_current_time == 0) and (t_stored_time - time.time() < 10)):
#         t_current_time = time.time()
#         print t_current_time
#         print "Cloudlet is up"
#     elif ((t_current_time != 0) and (t_stored_time - t_current_time < 10)):
#         t_current_time = t_stored_time
#         print "cloudlet is up"
#     else:
#         print "cloudlet is down - Failed"
#         sys.exit()
#
# update()
# import time
# import os
#
#
# def ping_cloudlet():
#     hostname = "1.2.3.4"
# #     hostname = "1.2.3.4"  # example
#     response = os.system("ping -n 2 " + hostname)
#
# # and then check the response...
#     if response == 0:
#         print hostname, 'is up!'
#     else:
#         print response
#         print "inside else"
#         for i in range(3):
#             response = os.system("ping -n 1 " + hostname)
#             time.sleep(2)
#         if response != 0:
#             print hostname, 'is down!'
#     while True:
#         #             if counter > 2:
#         #             return_val = os.system("ping -n 1 %s" % CLOUDLET_IP)
#         #             print "1. Return value of ping:%s" % return_val
#         #             else:
#         return_val = os.system("ping 10.27.3.3")
#         print "2. Return value of ping:%s" % return_val
#         time.sleep(1)


heartbeat_dict = {'clc1:'}


# update_heartbeat_dict()

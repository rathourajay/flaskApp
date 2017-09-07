import json
# '''
# Created on Dec 28, 2016
#
# @author: gur40998
# '''

#host = "www.mywbsite.fr/sport/multiplex.aspx"
# params='"isLeftColumn":"false","liveID":"-1","userIpCountryCode":"FR","version":"null","languageCode":"fr","siteCode":"frfr","Quotation":"eu"'


#url = 'https://localhost:5000/api/DS'
# payload = {
#    "cloudlet": "cloudlet111"
#}
# Adding empty header as parameters are being sent in payload
#headers = {}
#r = requests.get(url, data=json.dumps(payload), headers=headers)
# print(r.content)
################################
# best_food_chains = ["Taco Bell", "Shake Shack", "Chipotle"]
# print(type(best_food_chains))
#
# best_food_chains_string = json.dumps(best_food_chains)
# print(type(best_food_chains_string))

# print(type(json.loads(best_food_chains_string)))

# # fast_food_franchise = {
# #    "Subway": 24722, "McDonalds": 14098, "Starbucks": 10821, "Pizza Hut": 7600}
# fast_food_franchise = {"code": "200", "cloudlets": [
#     {"cloudletID": "cloudlet1", "couldletIP": "12.23.12.2"}, {"cloudletID": "cloudlet2", "couldletIP": "1.1.1.1"}]}
#
# # We can also dump a dictionary to a string and load it.
# fast_food_franchise_string = json.dumps(fast_food_franchise)
# print(type(fast_food_franchise_string))
#
# load_food = json.loads(fast_food_franchise_string)
# print "load_", type(load_food)

# import re
# client_ip = '1244jkhg'
# split_str = client_ip.split('.')
# if len(split_str) != 4:
#     print "fail"
# elif len(split_str) == 4:
#     for item in split_str:
#         if int(item) > 255 or int(item) < 0:
#             print "afile"

#
# import threading
# import time_
#
#
# def execute_request(str):
#     print str
#     for req in range(4):
#         print req
#
# #         req.get()
# #         req.post()
#
#
# threads = []
# for i in range(100):
#     t = threading.Thread(target=execute_request("Thread no. %s" % i))
#     threads.append(t)
#     t.start()

a = raw_input("Enter:")

dict1 = {'ja': 1, 'ka': 2, 'ha': 3}
# dict1.update('ja', 'na')
print dict1

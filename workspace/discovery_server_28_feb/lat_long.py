# from math import radians, cos, sin, asin, sqrt
#
#
# def haversine(lon1, lat1, lon2, lat2):
#     # Decimal Degrees = Degrees + minutes/60 + seconds/3600
#     # convert decimal degrees to radians
#     lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
#     # haversine formula
#     dlon = lon2 - lon1
#     dlat = lat2 - lat1
#     a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#     c = 2 * asin(sqrt(a))
#     km = 6367 * c
#     return km
#
#
# #distance = haversine(50.06638888888889, -5.714722222222222, 58.64388888888889, -3.0700000000000003)
# #distance = haversine(28.4492555, 76.9857082, 28.510705, 77.0730293)
# distance = haversine(4.8422, 45.7597, 2.3508, 48.8567)
# print distance, " KM"
# ##############################
# from haversine import haversine
# # lyon = (45.7597, 4.8422)
# # paris = (48.8567, 2.3508)
# lyon = (45.7597, 4.8422)
# paris = (48.8567, 2.3508)
# dis = haversine(lyon, paris)
# # 392.00124794121825  # in kilometers
# print dis, " km"
# dis = haversine(lyon, paris, miles=True)
# print dis, " miles"
# # 243.589575470673  # in miles
# #############################################
# cloudlet_ids = []
# dist_cmp_dict = {'c1': 1233, 'c2': 2313, 'c3': 543, 'c4': 5444}
# for i in range(2):
#     shortest_cloudlet_id = min(
#         dist_cmp_dict, key=lambda k: dist_cmp_dict[k])
#     cloudlet_ids.append(shortest_cloudlet_id)
# # key = lambda k: dist_cmp_dict[k]

#
# class Foo:
#
#     def __call__(self):
#         print 'called'
#
#     def getitem(self):
#         print "ajay"
#
# foo_instance = Foo()
# foo_instance.getitem()
# foo_instance()
# print "cloudlet_ids:", cloudlet_ids

from lxml import html

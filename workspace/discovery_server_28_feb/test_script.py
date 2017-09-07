# from collections import Counter
# import pdb
# pdb.set_trace()
# cloudlet_usage = Counter({u'RAM': 32, u'DISK': 190, u'CPU': 50}
#                          )
#
#
# cloudlet_usage1 = Counter({u'CPU': 51, u'DISK': 196, u'RAM': 51}
#                           )
#
# print dict(cloudlet_usage1 - cloudlet_usage)
#
#
# # from collections import Counter
# # d1 = Counter({'a': 10, 'b': 9, 'c': 8, 'd': 7})
# # d2 = Counter({'a': 1, 'b': 2, 'c': 3, 'e': 2})
# # d3 = d1 - d2
# # print d3
#
# cloudlets_capacity: {u'cl14': {u'RAM': 30, u'DISK': 200, u'CPU': 10}, u'cl12': {u'RAM': 20, u'DISK': 500, u'CPU': 40}, u'cl13': {u'RAM': 30, u'DISK': 400, u'CPU': 60}}
# cloudlet_usage: {u'cl14': {u'RAM': 3, u'DISK': 190, u'CPU': 50}, u'cl12': {u'RAM': 8, u'DISK': 110, u'CPU': 90}, u'cl13': {u'RAM': 4, u'DISK': 290, u'CPU': 40}}
# {u'cl14': {u'RAM': 27, u'DISK': 10}, u'cl12': {u'RAM': 12, u'DISK': 390}, u'cl13': {u'RAM': 26, u'DISK': 110, u'CPU': 20}}
from geopy.geocoders import Nominatim
geolocator = Nominatim()
location = geolocator.reverse("52.509669, 13.376294")
print location.address
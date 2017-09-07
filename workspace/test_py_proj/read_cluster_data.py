# import json
# def get_cluster_name():
#         with open('test_json.txt', 'r') as infile:
#             cluster_data = json.load(infile)
#             print cluster_data
#  
# #         proxy_name = cluster_data['vcenter']['name']
#         cluster_name = "%s(%s)" %(cluster_data['glossary']['title'],cluster_data['glossary']['name'])
#         return cluster_name
#  
#  
#  
# name = get_cluster_name()
# print name


# import json
# from pprint import pprint
# 
# with open('new_json.json') as data_file:    
#     data = json.load(data_file)
# 
# # pprint(data)
# 
# print "%s(%s)" %(data["masks"]["id"],data["maps"][0]["id"])
# print data["maps"][0]["id"]
# print data["masks"]["id"]
# print data["om_points"]


            #Fetch cluster name
cluster_data = 'glossary(xyz)'
#TODO: print out the cluster we are migrating in each while loop
if cluster_data:
    cluster_name = cluster_data.split('(')[1].\
        split(')')[0].strip()
    msg = 'Migration of networking for cluster: ' + str(cluster_name)
    print msg

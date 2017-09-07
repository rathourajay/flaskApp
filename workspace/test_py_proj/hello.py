# data_list = [u'_uuid               : 36906100-4008-40ed-a734-478ea6065103\n', u'description         : ""\n', u'name                : "f2"\n', u'port_fault_status   : []\n', u'vlan_bindings       : {1101=3ed68a5a-0b74-4a98-8e7b-27a2e58b166f}\n', u'vlan_stats          : {}\n', u'\n', u'_uuid               : 02ca9e49-4a33-4aa4-a4c3-ef2c9c328fe6\n', u'description         : ""\n', u'name                : "i3"\n', u'port_fault_status   : []\n', u'vlan_bindings       : {}\n', u'vlan_stats          : {}\n', u'\n', u'_uuid               : 308201b9-236d-4eb1-bfc3-678037c9eec7\n', u'description         : ""\n', u'name                : "f1"\n', u'port_fault_status   : []\n', u'vlan_bindings       : {}\n', u'vlan_stats          : {}\n', u'\n', u'_uuid               : 811ab33f-0fba-4f15-9cb1-75bf1880ed1e\n', u'description         : ""\n', u'name                : "i1"\n', u'port_fault_status   : []\n', u'vlan_bindings       : {1102=543bbd29-117d-4137-b6bc-f9fe9e5547a7}\n', u'vlan_stats          : {}\n']
# 
# name_list = []
# binding_list = []
# for item in data_list:
#     if 'name' in item:
#         name_list.append(item)
#     if 'binding' in item:
#         binding_list.append(item)
#         
# list_dicts = []
# for name,bindings in zip(name_list,binding_list):
#     dict_name = {}
#     dict_name['name'] = name
#     dict_name['bindings'] = bindings
#     list_dicts.append(dict_name)
# print list_dicts
    
    
    
    
    
    
d1 = {u'l2_gateways': [{u'tenant_id': u'a54d1a3b8ef048fda8af8167d5e5318b', u'id': u'7ea9d996-69dc-4574-a031-bd69713602ad', u'devices': [{u'interfaces': [{u'segmentation_id': 1101, u'name': u'f2'}], u'id': u'd7936276-e3c8-4767-9a5c-b9efbd1aa7ca', u'device_name': u'final1'}], u'name': u'final_gateway2'}, {u'tenant_id': u'a54d1a3b8ef048fda8af8167d5e5318b', u'id': u'd26e28ee-0156-4b81-b8b6-7db4961c6fe2', u'devices': [{u'interfaces': [{u'segmentation_id': 1100, u'name': u'f1'}], u'id': u'2180baf6-8ed4-47b1-af04-b6a987b4ffaf', u'device_name': u'final1'}], u'name': u'final_gateway1'}, {u'tenant_id': u'a54d1a3b8ef048fda8af8167d5e5318b', u'id': u'f3ebd310-a462-4a04-ade5-59a991583e26', u'devices': [{u'interfaces': [{u'segmentation_id': 1102, u'name': u'i3'}], u'id': u'8ab49683-ff57-403f-8368-47926bba5fde', u'device_name': u'switch2'}, {u'interfaces': [{u'segmentation_id': 1102, u'name': u'i1'}], u'id': u'f69e525b-a70e-4360-8bb6-40f20abfc726', u'device_name': u'switch1'}], u'name': u'gw1'}]}
# print len(d1['l2_gateways'] )

port_dict_bindings = [{'bindings': u'vlan_bindings       : {1101=3ed68a5a-0b74-4a98-8e7b-27a2e58b166f}\n', 'name': u'name                : "f2"\n'}, {'bindings': u'vlan_bindings       : {}\n', 'name': u'name                : "i3"\n'}, {'bindings': u'vlan_bindings       : {}\n', 'name': u'name                : "f1"\n'}, {'bindings': u'vlan_bindings       : {1102=543bbd29-117d-4137-b6bc-f9fe9e5547a7}\n', 'name': u'name                : "i1"\n'}]

for item in   d1['l2_gateways']:
    for i in item['devices']:
        seg_id =  i['interfaces'][0]['segmentation_id']
        port_name =  i['interfaces'][0]['name']
        for data in port_dict_bindings:
            if str(seg_id) in data['bindings'] and port_name in data['name']:
                print port_name, str(seg_id),"mapped with vlan"
                
            else:
                print port_name, str(seg_id),"not mapped with vlan"

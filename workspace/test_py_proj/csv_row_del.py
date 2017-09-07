# to_del_param_dict = {}
# to_del_param_list = []
# to_del_param_dict['network_id'] = 'net1'
# to_del_param_dict['connectn_id'] = 'coin1'
# to_del_param_dict['tenant_id'] = 'tan1'
# to_del_param_dict['l2_gateway_id'] = 'gw1'
# to_del_param_dict['seg_id'] = 'sg1'
# to_del_param_list.append(to_del_param_dict)
# # print to_del_param_list
# 
# for each_dict in to_del_param_list:
#     for item in each_dict.itervalues():
#         print item
#     net_id = each_dict['network_id']
#     tenant_id = each_dict['tenant_id']
#     conn_id = each_dict['connectn_id']
#     gw_id = each_dict['l2_gateway_id']
#     seg_id = each_dict['seg_id']
#     print net_id
#     print ten_id
#     print con_id
#     print gw_id
#     print seg_id
# import os
# os.remove('C:/Users/gur40998/workspace/test_py_proj/test_json.txt')
# print "done"


#  
# param_dict = {'tennt_id': ['a54d1a3b8ef048fda8af8167d5e5318b', 'a54d1a3b8ef048fda8af8167d5e5318b'], 'gw_id': ['4723f45d-7445-45ce-897f-cb911886ebcf', 'cd6baa36-c907-4459-af76-794991a696db'], 'connection_id': ['e8901391-be77-45a5-b055-ff98216284df', 'f4369c8c-aaae-4e05-930c-d97a2bc1fa29'], 'seg_id': ['', '1101'], 'net_id': ['970b5f5c-b2d4-4c6d-8693-5f5b385e08e4', 'c4e8e791-fa2a-4466-a0b5-fe3df09beecb']}
# gw_seg_mapper = {}
# for i in range(len(param_dict['seg_id'])):
#     if param_dict['seg_id'][i]!= '':
#         print param_dict['seg_id'][i]  
#         print param_dict['gw_id'][i]

# for c in ['a','c','b']:
#     if c not in d:
#         d[c] = 1
#     else:
#         d[c] = d[c] + 1
# print d
port_list = []
mapped_port_list = []


l2_gw_dict = {}
 
l2_gw_dict['l2_gateways'] = [{u'tenant_id': u'a54d1a3b8ef048fda8af8167d5e5318b', u'id': u'3a32080a-09e6-476a-8c15-a50497adfc24', u'devices': [{u'interfaces': [{u'segmentation_id': 1102, u'name': u'vtep_port1'}], u'id': u'32f16b97-5596-4023-a2db-ef462aea3575', u'device_name': u'vtep-switch2'}, {u'interfaces': [{u'segmentation_id': 1102, u'name': u'vtep_port1'}], u'id': u'397d6a4c-04a6-466d-991e-c99b002ff639', u'device_name': u'vtep-switch1'}], u'name': u'vtep_gw1'}]
 
switch_details = [{'sw_name': u'name                : "vtep-switch2"\n', 'ports': u'ports               : [ef639ea5-8701-46a3-8fe1-8dcb03a7f594]\n'}, {'sw_name': u'name                : "vtep-switch1"\n', 'ports': u'ports               : [4756a403-083d-4eee-9147-783811d50e33]\n'}]

port_dict_bindings = [{'bindings': u'vlan_bindings       : {1102=a80cec2f-e573-4d8d-ba6b-a80f8160192d}\n', 'port_id': u'_uuid               : ef639ea5-8701-46a3-8fe1-8dcb03a7f594\n', 'name': u'name                : "vtep_port1"\n'}, {'bindings': u'vlan_bindings       : {1102=a80cec2f-e573-4d8d-ba6b-a80f8160192d}\n', 'port_id': u'_uuid               : 4756a403-083d-4eee-9147-783811d50e33\n', 'name': u'name                : "vtep_port1"\n'}]


sw_list = []


for sw_dict in switch_details:
    switch_port_details = dict()
    switch_port_details['switch_name'] = str(sw_dict['sw_name'].split(':')[1]).replace('\n','')
    switch_port_details['ports'] =  (sw_dict['ports'].split(':')[1]).replace('\n','')
    sw_list.append(switch_port_details)
print sw_list

sw_list[0]['ports'] = u' [ef639ea5-8701-46a3-8fe1-8dcb03a7f594,ef]'
print sw_list


port_id_name = {}

for item in l2_gw_dict['l2_gateways']:
    print "**************************************"
    l2_gw_id = item['id']
    for i in item['devices']:
        switch_name = str(i['device_name'])#vtep_switch2
        seg_id = i['interfaces'][0]['segmentation_id']
#         if not seg_id:
#             seg_id = self.get_seg_id(l2_gw_id)
        port_name = i['interfaces'][0]['name']#vtep_port1
#         if port_name not in port_list:
#             port_list.append(port_name)
        
        for data in port_dict_bindings:
            port_id = str(data['port_id'].split(':')[1].replace('\n','')).strip()#ef639ea5-8701-46a3-8fe1-8dcb03a7f594
            if port_id not in port_list:
                port_list.append(port_id)
            for val in sw_list:
                if switch_name in val['switch_name'] and port_id in val['ports']:
                    if str(seg_id) in data['bindings'] and port_name in data['name']:
                        mapped_port_list.append(port_id)
port_list.append('ef')
print port_list
unmapped_port_list = [port for port in port_list if port not in mapped_port_list]
print "unmapped ports are:",unmapped_port_list
print "mapped ports are:",mapped_port_list

sw_port_lst = []
for port in unmapped_port_list:
    for sw in sw_list:
        if port in sw['ports']:
            sw_port_dct = dict()
            sw_port_dct['switch_name'] = sw['switch_name']
            sw_port_dct['ports'] = port
            sw_port_lst.append(sw_port_dct)
print sw_port_lst
            
            
            



















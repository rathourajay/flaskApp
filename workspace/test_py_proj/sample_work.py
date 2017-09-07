# import urllib2
# from lxml import html
# import csv
# 
# fp = open('image_logo.csv', 'wb')
# writer = csv.writer(fp)
# writer.writerow(["website", "image_logo_url"])
# 
# websites_list = ['http://www.livingyourspanish.com','http://armenianvolunteer.org']
# 
# for url in websites_list:
#     data_list = []
#     html_source = urllib2.urlopen(url).read()
#     parsed_source = html.fromstring(html_source)
#     img_src = parsed_source.xpath("//img[contains(@src,'logo.')]/@src")
#     complete_image =  url+''+img_src[0]
#     data_list.append(url)
#     data_list.append(complete_image)
#     writer.writerow(data_list)
# fp.close()
# 
# from csv_row_del import port_dict_bindings
"""
str1 = u'4c3276f5-31fa-468c-b4bf-ab01e3e6ca7a\ttest_switch2\t6630336c-b9b5-485a-aa8f-e1a58826633dd\ttest_port1\n'
str2 = u'4c3276f5-31fa-468c-b4bf-ab01e3e6ca7a\ttest_switch2\t6630336c-b9b5-485a-aa8f-e1a588266ddd\ttest_port2\n'


str3 = u'4c3276f5-31fa-48c-b4bf-ab01e3e6caa\ttest_switch2\t6630336c-b9b5-485a-aa8f-e1a588266dd6767\ttest_port2\t1102\n'
str4 = u'4c3276f5-31fa-468c-b4bf-ab01e3e6ca7a\ttest_switch2\t6630336c-b9b5-485a-aa8f-e1a588266ddd\ttest_port2\t1101\n'


# str2 = str(str1.split('\t')[0])
sw_port_dict = dict()
spv = {}
port_list = []
list1 = [str3,str4]
for line in list1:
    
#     spv  = dict()
    sw_id = str(line.split('\t')[0])
    port_id = str(line.split('\t')[2])
    vlan_id = str(line.split('\t')[4])
    sw_port_dict.setdefault(port_id, []).append(vlan_id)
    spv.setdefault(sw_id,{})[port_id] = [vlan_id]
#     d2.setdefault(key, {})[value] = 1
print spv    
"""
#     print port_id
#     if sw_id in sw_port_dict:
#         sw_port_dict[sw_id].append(port_id)
#     else:
#         sw_port_dict[sw_id] = port_id

# print spv
# sw_list = ['abc','bcd']
# for sw in sw_list:
#     if sw not in sw_port_dict.keys():
#         sw_port_dict.setdefault(sw,[])
# print sw_port_dict

# sw_port_dict = {}
# {s1:[p1,p2],s2:[p2,p3]}


# s1:{}
# 
# sw_port_dict = {'s1': ['p1', 'p2'], 
# 's2': [], 
# 's3': ['p3'],
# 's4': ['p4']}
# 
# spv = {'s1': {'p2': ['1102\n']}, 's4': {'p4': ['1101\n']}}
# 
# for sw in sw_port_dict.keys():
#     if sw not in spv.keys():
#         temp = {}
#         for value in sw_port_dict[sw]:
#             temp[value]=[]
#         spv[sw]=temp
#     else:
#         for value in sw_port_dict[sw]:
#             port = spv[sw]
#             if value not in port.keys():
#                 port[value]=[]    
#         
# print spv
#     print sw[1]
#     for item in sw[1]:
#         print item
#     for port in sw[1]:
#         print port
#     for port in sw:
#         print port



#from mysql
spv = {'test_switch1': {'dd9718b5-2fda-445b-9447-6feda384e647': [], '982d0568-4912-4197-88ad-28fd4c708a83': ['1107','1110','1104']},
        'ovsdb2_switch1': {'3d409c3c-a5d3-4dd3-b46d-b205c59618f3': ['1106']},
         'test_switch2': {'6630336c-b9b5-485a-aa8f-e1a588266ddd': ['1108']},
         'test_switch5': {}}
  

#from ovsdb
port_dict_bindings = [{'bindings': u'vlan_bindings       : {1101=edb9157a-62f6-4664-9b03-4e09facbc616}\n', 'port_id': u'_uuid               : 6630336c-b9b5-485a-aa8f-e1a588266ddd\n', 'name': u'name                : "test_port2"\n'},
                       {'bindings': u'vlan_bindings       : {1109=bd404214-0a89-4a2897c-0fe0ee4672d4,1100=bd404214-0a89-4a25-897c-0fe0ee4672d4, 1106=03cc6a79-2190-4825-940c-ed11778b9fd7}\n', 'port_id': u'_uuid               : 982d0568-4912-4197-88ad-28fd4c708a83\n', 'name': u'name                : "test_port1"\n'},
                        {'bindings': u'vlan_bindings       : {1105=hkjghig}\n', 'port_id': u'_uuid               : dd9718b5-2fda-445b-9447-6feda384e647\n', 'name': u'name                : "new_port1"\n'}]


switch_details = [{'sw_name': u'name                : "test_switch2"\n', 'ports': u'ports               : [6630336c-b9b5-485a-aa8f-e1a588266ddd]\n'},
 {'sw_name': u'name                : "test_switch1"\n', 'ports': u'ports               : [982d0568-4912-4197-88ad-28fd4c708a83, dd9718b5-2fda-445b-9447-6feda384e647]\n'},
  {'sw_name': u'name                : "test_switch5"\n', 'ports': u'ports               : []\n'}]

sw_list = []
for sw_dict in switch_details:
    switch_port_details = dict()
    switch_port_details['switch_name'] = str(sw_dict['sw_name'].split(':')[1]).replace('\n','')
    switch_port_details['ports'] =  (sw_dict['ports'].split(':')[1]).replace('\n','')
    sw_list.append(switch_port_details)
# print sw_list
# 
# test_switch1 dd9718b5-2fda-445b-9447-6feda384e647 None
# test_switch1 982d0568-4912-4197-88ad-28fd4c708a83 1100
# test_switch1 982d0568-4912-4197-88ad-28fd4c708a83 1109
# ovsdb2_switch1 3d409c3c-a5d3-4dd3-b46d-b205c59618f3 1102
# test_switch2 6630336c-b9b5-485a-aa8f-e1a588266ddd 1101
def unbind_data(switch_name_ovsdb,port_id,ovs_vlan_list):
    if ovs_vlan_list:
        print switch_name_ovsdb,port_id,ovs_vlan_list

def compare_fun(sw_list,sw_name,port,port_vlan_dict):
    ovs_vlan_list = [] 
    count = 0
    for vlan in port_vlan_dict:
        count = count + 1 
        vlan_bind = vlan#     import pdb;pdb.set_trace()
        for sw_dict in sw_list:
            switch_name_ovsdb = sw_dict['switch_name']
            ovsdb_ports = sw_dict['ports'].replace('[','').replace(']','').strip()
            if sw_name == switch_name_ovsdb.replace('"','').strip():
                ovsdb_ports_list = ovsdb_ports.split(',')
                for ovs_port in ovsdb_ports_list:
                    flag = False
                    for data in port_dict_bindings:
                        port_id = str(data['port_id'].split(':')[1].replace('\n','').strip())
                          
                        if str(ovs_port.strip()) == str(port_id.strip()):
                            if port_id.strip() == port.strip():
                                if not flag :
                                    flag = True 
                                    ovs_vlan = str(data['bindings'].split(':')[1]).replace('{','').replace('}','').replace('\n','').strip()
                                    if len(ovs_vlan_list) == 0 :
                                            ovs_vlan_list = ovs_vlan.split(',')
                                if ovs_vlan_list:
                                    for item in ovs_vlan_list:
                                        if vlan_bind in item:
                                            ovs_vlan_list.remove(item)
                                if count == len(port_vlan_dict):
                                    unbind_data(switch_name_ovsdb,port_id,ovs_vlan_list)
            

def start_bckup():
        for sw_name in spv.keys():
            port_vlan_dict = spv[sw_name]
            for port in port_vlan_dict.keys():
                if port_vlan_dict[port]:
                    compare_fun(sw_list,sw_name,port,port_vlan_dict[port])
                #else:
                    #compare_fun(sw_list,sw_name,port,port_vlan_dict[port])
                    
if __name__ =='__main__':
    start_bckup()
















# def validate_vlan_bindings():
#     mig_obj = MigrationScript()
#     host_ip = '10.8.20.51'
#     req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (host_ip)
#     headers = mig_obj.get_headers()
#     gw_list = requests.get(req_url, headers=headers)
#     l2_gw_list = gw_list.text
#     l2_gw_dict = json.loads(l2_gw_list)
#     port_list = []
#     mapped_port_list = []
#     sw_list = []
#     vtep_obj = vtep_command_manager()
#     port_dict_bindings,switch_details = vtep_obj.get_ovsdb_bindings()
#     
#     for sw_dict in switch_details:
#         switch_port_details = dict()
#         switch_port_details['switch_name'] = str(sw_dict['sw_name'].split(':')[1]).replace('\n','')
#         switch_port_details['ports'] =  (sw_dict['ports'].split(':')[1]).replace('\n','')
#         sw_list.append(switch_port_details)
#         spv = fetch_t1_timestamp_data()
#         import pdb; pdb.set_trace()
#         for item in l2_gw_dict['l2_gateways']:
#             l2_gw_id = item['id']
#             for i in item['devices']:
#                 switch_name = str(i['device_name'])
#                 seg_id = i['interfaces'][0]['segmentation_id']
#                 if not seg_id:
#                     seg_id = self.get_seg_id(l2_gw_id)
#                 port_name = i['interfaces'][0]['name']
#                 for data in port_dict_bindings:
#                     port_id = str(data['port_id'].split(':')[1].replace('\n','')).strip()
#                     if port_id not in port_list:
#                         port_list.append(port_id)
#                     for val in sw_list:
#                         if switch_name in val['switch_name'] and port_id in val['ports']:
#                             if str(seg_id) in data['bindings'] and port_name in data['name']:
#                                 mapped_port_list.append(port_id)
#         unmapped_port_list = [port for port in port_list if port not in mapped_port_list]
#         sw_port_lst = []
#         for port in unmapped_port_list:
#             for sw in sw_list:
#                 if port in sw['ports']:
#                     sw_port_dct = dict()
#                     sw_port_dct['switch_name'] = sw['switch_name']
#                     sw_port_dct['ports'] = port
#                     sw_port_lst.append(sw_port_dct)
#         return sw_port_lst
#     
# 
# 
# def get_ovsdb_bindings(self):
#         '''
#         This method retruns vlan_bindings wrt port name and ports list along with switch
#         '''
#         client = self.connect_host(self.ovsdb_host_ip,self.ovsdb_host_uname,self.ovsdb_host_pwd)
#         command_vtep = "cd /home/ubuntu;./vtep-ctl list Physical_Port"
#         command_vtep_switches = "cd /home/ubuntu;./vtep-ctl list Physical_Switch"
#         #command_vtep = "cd ~;./vtep-ctl list Physical_Port"
#         #command_vtep_switches = "cd ~;./vtep-ctl list Physical_Switch"
#         stdin, stdout, stderr = client.exec_command(command_vtep)
#         name_list = []
#         port_id_list = []
#         binding_list = []
#         for item in stdout.readlines():
#             if '_uuid' in item:
#                 port_id_list.append(item)
#             if 'name' in item:
#                 name_list.append(item)
#             if 'binding' in item:
#                 binding_list.append(item)
# 
#         list_dicts = []
#         for name,bindings,port_id in zip(name_list,binding_list,port_id_list):
#             dict_name = {}
#             dict_name['name'] = name
#             dict_name['bindings'] = bindings
#             dict_name['port_id'] = port_id
#             list_dicts.append(dict_name)
# 
#         stdin, stdout, stderr = client.exec_command(command_vtep_switches)
#         port_list = []
#         sw_name_list = []
#         switch_details = {}
# 
#         for i in stdout.readlines():
#             switch_details = dict()
#             if 'name' in i:
#                 sw_name_list.append(i)
#             if 'ports' in i:
#                 port_list.append(i)
#         sw_detail_list  = []
#         for name,port in zip(sw_name_list,port_list):
#             sw_dict = {}
#             sw_dict['sw_name'] = name
#             sw_dict['ports'] = port
#             sw_detail_list.append(sw_dict)
#         return list_dicts,sw_detail_list






















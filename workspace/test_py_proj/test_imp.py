# # from advance_practice import foo
# # import advance_practice
# # 
# # def test():
# #     print "this is my test in new file"
# #     
# # if __name__ == '__main__':
# #     print advance_practice.__name__
# # #     print __name__
# #     test()
# 
# 
# #a,b,n,s,t,f
#  
# # import re
# # text = "ad/gur"
# # # if '\\' in text:
# # #     text = text.replace('\\','\\\\')
# # 
# # data = re.sub(r'\W+', '@', text,1)
# # user =  data
# # print user
# # if '@' in user:
# #     text1 = user.split('@')
# #     text2 = text1[1]+'@'+text1[0]
# #     print text2
# 
# 
# 
# 
# 
# # import ConfigParser
# # 
# # config = ConfigParser.RawConfigParser()
# # 
# # config.add_section('Section1')
# # config.set('Section1', 'an_int', '112')
# # config.set('Section1', 'a_bool', 'true')
# # config.set('Section1', 'a_float', '3.1415')
# # config.set('Section1', 'baz', 'fun')
# # config.set('Section1', 'bar', 'Python')
# # config.set('Section1', 'foo', '%(bar)s is %(baz)s!')
# # 
# # # Writing our configuration file to 'example.cfg'
# # with open('example1.cfg', 'wb') as configfile:
# #     config.write(configfile)
# 
# # str = "ajay singh rathour 1245 jjjj"
# # after_split = str.split('singh')[-1]
# # print after_split
# 
# # 
# # l1 = ['10.20.30.40/24:100.100.0.1']
# # if ':' in l1[0]:
# #     print "matched"
# #     
# # else:
# #     print "not matched"
# 
# 
# 
# 
# # import os
# # import time
# # import datetime
# # import logging
# # class Logger :
# #     def myLogger(self):
# #         logger = logging.getLogger('ProvisioningPython')
# #         logger.setLevel(logging.DEBUG)
# #         now = datetime.datetime.now()
# #         handler=logging.FileHandler('/test_py_proj'+ now.strftime("%Y-%m-%d") +'.log')
# #         formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# #         handler.setFormatter(formatter)
# #         logger.addHandler(handler)
# #         print logger.handlers
# #         logger.handlers = []
# #         print logger.handlers
# #         return logger
# #     
# # log = Logger()
# # logger = log.myLogger()
# 
# 
# # def xyz():
# #     print "called"
# #     
# # results = [None]
# # if  results !=[None]:
# #     xyz()
# # else:
# #     print "not called"
# 
# # 
# # x = False
# # if not x:
# #     print "ajay"
# # else:
# #     print "something"
# 
# 
# 
#  
# # host_ip_map = {}
# # if host_ip_map:
# #     print "yes"
# # else:
# #     print "No"
# # host_ip_map['host1'] = '10.20.30.40'
# # host_ip_map['host2'] = '100.200.300.400'
# # # print host_ip_map
# # exec_args = [('session', 'datacenter', host, 'is_new_host', ip)\
# #                             for host, ip in host_ip_map.iteritems()]
# #   
# # print exec_args
# 
# # 
# # dict = {'a':10,'b':'11'}
# # for v in dict.itervalues():
# #     print v
# 
# 
# # def ab(count,ip):
# #     print count
# # ab(1,'abc')
# '''
# sample = {'ObjectInterpolator': 1629,  'PointInterpolator': 1675, 'RectangleInterpolator': 2042}
# 
# import json
# with open('result.json', 'w') as fp:
#     json.dump(sample, fp)
# '''
# 
# 
# 
# 
# 
# 
# 
# #from mysql
# 
# # spv = {'test_switch1': {'dd9718b5-2fda-445b-9447-6feda384e647': [], '982d0568-4912-4197-88ad-28fd4c708a83': ['1107','1100','1104']},
# #         'ovsdb2_switch1': {'3d409c3c-a5d3-4dd3-b46d-b205c59618f3': ['1106']},
# #          'test_switch2': {'6630336c-b9b5-485a-aa8f-e1a588266ddd': ['1108']},
# #          'test_switch5': {}}
# #    
# #  
# # #from ovsdb
# # port_dict_bindings = [{'bindings': u'vlan_bindings: {1101=edb9157a-62f6-4664-9b03-4e09facbc616}\n', 'port_id': u'_uuid : 6630336c-b9b5-485a-aa8f-e1a588266ddd\n', 'name': u'name                : "test_port2"\n'},
# #                        {'bindings': u'vlan_bindings       : {1109=bd404214-0a89-4a2897c-0fe0ee4672d4,1100=bd404214-0a89-4a25-897c-0fe0ee4672d4, 1106=03cc6a79-2190-4825-940c-ed11778b9fd7}\n', 'port_id': u'_uuid               : 982d0568-4912-4197-88ad-28fd4c708a83\n', 'name': u'name                : "test_port1"\n'},
# #                         {'bindings': u'vlan_bindings       : {1107=hhnbnhnh}\n', 'port_id': u'_uuid               : dd9718b5-2fda-445b-9447-6feda384e647\n', 'name': u'name                : "new_port1"\n'},
# #                         {'bindings': u'vlan_bindings       : {}\n', 'port_id': u'_uuid               : trftgrtgt\n', 'name': u'name                : "new_port3"\n'},
# #                         {'bindings': u'vlan_bindings       : {}\n', 'port_id': u'_uuid               : dd9718b5\n', 'name': u'name                : "new_port4"\n'}]
# #  
# #  
# # switch_details = [{'sw_name': u'name: "test_switch2"\n', 'ports': u'ports : [6630336c-b9b5-485a-aa8f-e1a588266ddd]\n'},
# #  {'sw_name': u'name                : "test_switch1"\n', 'ports': u'ports               : [982d0568-4912-4197-88ad-28fd4c708a83, dd9718b5-2fda-445b-9447-6feda384e647]\n'},
# #   {'sw_name': u'name                : "test_switch5"\n', 'ports': u'ports               : [trftgrtgt,dd9718b5]\n'}]
# 
# 
# 
# spv = {'ovsdb2_switch1': {'3d409c3c-a5d3-4dd3-b46d-b205c59618f3': ['1102']},
#         'test_switch1': {'dd9718b5-2fda-445b-9447-6feda384e647': [], '982d0568-4912-4197-88ad-28fd4c708a83': ['1104']},
#          'ovsdb2_switch2': {'6a514f2c-704a-44f4-85d8-58337d84b4f5': ['1105']}, 
#          'test_switch5': {}, 'demo1': {'bb9d79eb-74a8-4a6d-89d9-49d313d91a56': ['1107']}, 
#          'test_switch2': {'6630336c-b9b5-485a-aa8f-e1a588266ddd': []}, 'sw1': {}}
#   
# port_dict_bindings =[{'bindings': u'vlan_bindings       : {1101=edb9157a-62f6-4664-9b03-4e09facbc616}\n', 'port_id': u'_uuid               : 6630336c-b9b5-485a-aa8f-e1a588266ddd\n', 'name': u'name                : "test_port2"\n'},
#                       {'bindings': u'vlan_bindings       : {1104=03cc6a79-2190-4825-940c-ed11778b9fd7}\n', 'port_id': u'_uuid               : 982d0568-4912-4197-88ad-28fd4c708a83\n', 'name': u'name                : "test_port1"\n'},
#                        {'bindings': u'vlan_bindings       : {}\n', 'port_id': u'_uuid               : dd9718b5-2fda-445b-9447-6feda384e647\n', 'name': u'name                : "new_port1"\n'},
#                         {'bindings': u'vlan_bindings       : {1107=9c3204e4-ae6a-4dc0-813f-473efa36cecc}\n', 'port_id': u'_uuid               : bb9d79eb-74a8-4a6d-89d9-49d313d91a56\n', 'name': u'name                : "p1"\n'},
#                         {'bindings': u'vlan_bindings       : {}\n', 'port_id': u'_uuid               : fgfgdf\n', 'name': u'name                : "p111"\n'},
#                         {'bindings': u'vlan_bindings       : {1103=jnfj}\n', 'port_id': u'_uuid               : abcd\n', 'name': u'name                : "p12"\n'}]
#   
#   
# switch_details = [{'sw_name': u'name                : "test_switch2"\n', 'ports': u'ports               : [6630336c-b9b5-485a-aa8f-e1a588266ddd, abcd]\n'},
#                    {'sw_name': u'name                : "test_switch1"\n', 'ports': u'ports               : [982d0568-4912-4197-88ad-28fd4c708a83, dd9718b5-2fda-445b-9447-6feda384e647]\n'},
#                     {'sw_name': u'name                : "demo1"\n', 'ports': u'ports               : [bb9d79eb-74a8-4a6d-89d9-49d313d91a56]\n'},
#                      {'sw_name': u'name                : "test_switch5"\n', 'ports': u'ports               : [fgfgdf]\n'}]
# 
# 
# 
# def compare(spv,switch_final):
#     switch_diff={}
#     sw_port  ={}
#     for switch in spv:
# #         import pdb;pdb.set_trace()
#         if switch_final.has_key(switch):
#             switch_diff[switch]={}
# #             import pdb;pdb.set_trace()
#             if not spv[switch]:
#                 sw_port[switch]=switch_final[switch]
#                 
#             for port in spv[switch]:
#                 switch_diff[switch][port]=list(set(switch_final[switch][port]) - set(spv[switch][port]))
#             
#             sw_port[switch]=list(set(switch_final[switch]) - set(spv[switch]))
#                 
#     return switch_diff,sw_port
#             
# 
# def switch_dict(switch_details,port_vlan):
#     
#     switch_port_details = dict()
#     switch_final = {}
#     for sw_dict in switch_details:
#         switch_name = str(sw_dict['sw_name'].split(':')[1]).replace('\n','').replace('"','').replace(' ','')
#         port_name= str(sw_dict['ports'].split(':')[1]).replace('\n','').replace('[','').replace(']','').replace(' ','')
#         switch_port_details[switch_name] = {}
#         switch_port_details[switch_name]= port_name.split(',')
#         switch_final[switch_name] = {}
#         if port_name !='':
#             for port in switch_port_details[switch_name]:
#                 switch_final[switch_name][port]=[]
#                 switch_final[switch_name][port]=port_vlan[port]
#     
#     unbind_vlan_dict,del_port_dict = compare(spv,switch_final)
#     print "vlan to unbind",unbind_vlan_dict
# #     print "port to delete",del_port_dict
#     
#     for sw in unbind_vlan_dict:
#         for port in unbind_vlan_dict[sw]:
# #             print "port_id",port
#             
#             for item in port_dict_bindings:
#                 if str(item['port_id'].split(':')[1].strip()) == port:
#                     port_name =  str(item['name'].split(':')[1].strip())
#             if unbind_vlan_dict[sw][port]:
#                 if len(unbind_vlan_dict[sw][port][0])>0:
#                     vlan_lst =  unbind_vlan_dict[sw][port]
#                     print port_name
# #                     unbind_ls(sw,port,vlan_lst)
# 
# 
# def vlan_dict(port_dict_bindings):
#     port_vlan = {}
#     for port_dict in port_dict_bindings:
#         
#         port_nm = (port_dict['port_id'].split(':')[1]).replace('\n','').replace('[','').replace(']','').replace(' ','')
#         temp_str = str(port_dict['bindings'].replace(' ','').replace('vlan_bindings','').replace('\n','').replace(':',''))
#         vlist = str(temp_str.split('=')).split(',')
#         vlan_list=[]
#         for ele in vlist:
#             if len(ele) <10:
#                 vlan_list.append(ele.replace('{','').replace('}','').replace('\'','').replace('\"','').replace('[','').replace(']',''))
#         port_vlan[port_nm]=vlan_list
#     
#     switch_dict(switch_details,port_vlan)

       
# if __name__ == '__main__':
# #    fetch_t1_timestamp_data()
#     #ovsdb_data()
#     vlan_dict(port_dict_bindings)


ls_id = u'0a14abf5-da57-47a0-938d-102003e49021'
ls_ovsdb_data = [{'name': u'name                : "38f75b3a-5b22-481f-8079-310de544d767"\n', 'uuid': u'_uuid               : 4a9b3cf4-a5fd-41e2-9353-09133e207597\n'},
 {'name': u'name                : "5c12d66e-4ae4-4584-8853-e78b8310e487"\n', 'uuid': u'_uuid               : 0a14abf5-da57-47a0-938d-102003e49021\n'}] 




def get_ls_name_ovsdb(ls_id,ls_ovsdb_data):
    print ls_id
    print ls_ovsdb_data
    for item in ls_ovsdb_data:
        if ls_id in item['uuid']:
            ls_name =  item['name'].split(':')[1].replace('\n','').strip()


if __name__ == '__main__':
    get_ls_name_ovsdb(ls_id,ls_ovsdb_data)

































    
        






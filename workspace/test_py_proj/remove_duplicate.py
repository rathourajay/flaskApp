    def create_connection(self,param_dict,req_url,file_exist,headers):
        retry_flag = False
        to_del_param_list = []
        to_del_param_dict = {}
        for i in range(len(param_dict['net_id'])):
            flag = False
            network_id = param_dict['net_id'][i]
            tenant_id = param_dict['tennt_id'][i]
            l2_gateway_id = param_dict['gw_id'][i]
            seg_id = param_dict['seg_id'][i]
            connectn_id = param_dict['connection_id'][i]
            #import pdb;pdb.set_trace()
            payload = {"l2_gateway_connection": {"network_id": network_id, "l2_gateway_id": l2_gateway_id}}
            if seg_id:
                payload["l2_gateway_connection"]["segmentation_id"] = seg_id
            create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
            #import pdb;pdb.set_trace()
            if not(create_conn.ok):

                #added from here till break
                for i in range(3):
                    sys.stdout.write(("Retry attempt %s...\n") % (i+1))
                    self.log.info("Retrying for connection %s" %(connectn_id))
                    create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
                    if create_conn.ok:
                        flag = True
                        self.log.info("Connection %s  creation successful" %(connectn_id))
                        break

                if not flag:
                    to_del_param_dict = dict()
                    retry_flag = True
                    to_del_param_dict['network_id'] = network_id
                    to_del_param_dict['connectn_id'] = connectn_id
                    to_del_param_dict['tenant_id'] = tenant_id
                    to_del_param_dict['l2_gateway_id'] = l2_gateway_id
                    to_del_param_dict['seg_id'] = seg_id
                    to_del_param_list.append(to_del_param_dict)
                #self.create_failure_file(connectn_id, network_id , tenant_id, seg_id, l2_gateway_id )

        if retry_flag == True:
            self.delete_csv_entries(to_del_param_list)
            sys.stdout.write("Migration NOT Successfull after retry!!!\n")
            #param_flddict = self.read_data_file(self.DATA_EXC_FILE)
            #self.create_failed_connection(param_flddict,req_url,headers=headers)

        #if to_del_param_list:
        #    self.delete_csv_entries(to_del_param_list)
        #    sys.stdout.write("Migration NOT Successfull after retry!!!\n")
        else:
            print "all connection created successfully"
            if file_exist:
                print "deleting file"
                os.remove(self.DATA_EXC_FILE)
            self.log.info("Connection Created successfully\n")
            
            
            
            
            
    def execute_migration(self):
        file_exist = False
        req_url = "http://%s:9696/v2.0/l2-gateway-connections.json"  % (self.controller_ip)
        headers = self.get_headers()
        if not(os.path.isfile(self.DATA_EXC_FILE)): #or os.stat(self.DATA_EXC_FILE).st_size==0:
            """
            Executing L2GW migration steps
            """
            self.log.info("Executing Migration")
            self.log.info("Fetching Connection list")
            count = 0
            try:
                socket.inet_aton(self.controller_ip)
                ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$',self.controller_ip)
                if not ip_pat:
                    raise migration_exceptions.InvalidIpAddress('IP validation failed')

                sys.stdout.write("Step 1. Fetching Connection List\n")
                connection_list = self.get_connections_list(req_url,headers)
                #import pdb;pdb.set_trace()
                if not connection_list:
                    sys.stdout.write("No connection available on source #### No migration will happen####\n")
                    self.log.info("No Connection available on source #### No migration will happen####")
                    sys.exit()
                else:
                    self.log.info("Connection list %s" % (connection_list))
                    gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.controller_ip)
                #self.validate_vlan_bindings(gw_lst_req_url,headers)

                    sys.stdout.write("Step 2. Populating data file\n")
                    self.populate_data_file(connection_list)
                    self.log.info("##Datafile populated##")

                    #To autoconfigure neutron db creds:
                    #self.neutron_obj.fetch_credentials()
                    sys.stdout.write("Step 3. Deleting Entry from MySql\n")
                    db_obj = database_connection.db_connection()
                    self.log.info("##Connected to database##")
                    db_obj.read_connection_uuid()
                    self.log.info("##Deleting connection data from database##")
                    self.log.info("##Creating Connection on destination##")
                    sys.stdout.write("Step 4. Creating Connection\n")
                    param_dict = self.read_data_file(self.DATA_FILE)
                    #import pdb;pdb.set_trace()

                    self.create_connection(param_dict,req_url,file_exist,headers=headers)
                    if (os.path.isfile(self.DATA_EXC_FILE)):
                        self.log.info("##Error occurred in migration. Please check failed_switch.csv file for further details##")
                        sys.stdout.write("Migration not completed successfully. Please check logs foe further details\n")
                    else:
                        sys.stdout.write("Step 5. Connection created succesfully \n")
                        sys.stdout.write("    Migration Successfull!!!!!! \n")
                    #self.update_l2gwagent_ini()

                    #gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.controller_ip)
                    #self.validate_vlan_bindings(gw_lst_req_url,headers)

            sys.stdout.write("Migration Successfull\n")
            
            
            
            except migration_exceptions.InvalidIpAddress as e:
                self.log.exception("Error in IP address"
                                   "Reason: %s" % (e))
                sys.stderr.write(e._error_string+'\n')
                sys.exit()

            except socket.error as e:
                sys.stderr.write("IPV4 address validation failed" + '\n')
                self.log.exception("Error in IPV4 address"
                                   "Reason: %s" % (e))
                sys.exit()

            except (requests.exceptions.HTTPError) as e:
                print "An HTTPError:", e.message
                self.log.exception("An HTTPError:"
                                   "Reason: %s" % (e))

            except webob.exc.HTTPError() as e:
                self.log.exception("webob.exc.HTTPError()"
                                   "Reason: %s" % (e))
                raise webob.exc.HTTPError(e)

            except migration_exceptions.NoMappingFound as e:
                self.log.exception("Complete Mapping not created"
                                   "Reason: %s" % (e))
                sys.stderr.write(e._error_string+'\n')

            except Exception as e:
                self.log.exception("UnhandeledException :::"
                                   "Reason: %s" % (e))
                raise UnhandeledException(e)

            except IOError as e:
                self.log.exception("Invalid config file format"
                                   "Reason: %s" % (e))
                sys.stderr.write("Invalid config file format" + '\n')
                sys.exit()

        else:
            print "inside else, file exist"
            file_exist = True
            param_flddict = self.read_data_file(self.DATA_EXC_FILE)
            self.create_connection(param_flddict,req_url,file_exist,headers=headers)



            


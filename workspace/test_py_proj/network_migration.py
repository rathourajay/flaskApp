# (C) Copyright 2015 HP Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import time
import json
from csmigrate.common import common_names
#from csmigrate.steps.cs8_5.activate_cluster import write_failed_cluster
from csmigrate.esxi.hp_ovsvapp_migration.installer.create_ovs_vapp_vm \
    import CreateOVSvApp
from csmigrate.esxi.hp_ovsvapp_migration.cleanup.cleanup \
    import DestroyOVSvApp
from csmigrate.esxi.hp_ovsvapp_migration.util.vapp_constants \
    import JSON_DICT
from csmigrate.esxi.hp_ovsvapp_migration.installer.vapp_installer \
    import VappInstaller
from pyVmomi import vim, vmodl
from csmigrate.esxi.hp_ovsvapp_migration.util.validate_inputs \
    import ValidateInputs
from csmigrate.esxi.hp_ovsvapp_migration.util.vapp_error \
    import EsxiMigrationError, OVSvAppValidationError, OVSvAppError
from csmigrate.esxi.hp_ovsvapp_migration.migration.migration_lib \
    import NetworkMigrationLib
from csmigrate.esxi.hp_ovsvapp_migration.validation.token_validate.validation \
    import GetAuthorizationToken
#from csmigrate.networking.networking_api_client import NetworkingApiClient
#from csmigrate.networking.config_file_builder import ConfigFileBuilder
#from netaddr import IPNetwork
from csmigrate.esxi.hp_ovsvapp_migration.util import i18n
_ = i18n.language.gettext


class NetworkMigration:

    def __init__(self, conf_file):
        self.lib_obj = NetworkMigrationLib(conf_file)
        self.settings = self.lib_obj.settings
        self.logger = self.lib_obj.logger
        self.util = self.lib_obj.util
        self.dvs_config = self.lib_obj.dvs_config
        self.vapp_installer_inst = VappInstaller(self.settings, self.util)
        self.create_vapp = CreateOVSvApp(self.logger, self.settings)
        self.uuid_list = {}

    def _write_failed_clusters(self):
        '''
         This function add the failed cluster name to failed cluster list.
        '''
        with open(common_names.EON_STEP_PATH) as infile:
            cluster_data = json.load(infile)
            infile.close()

        if cluster_data:
            write_failed_cluster(cluster_data)
            msg = ("Unable to migrate networking for cluster %s"
                   %cluster_data['cluster']['name'])
            self.logger.warn(msg)
            sys.stdout.write(msg)

    def _do_OVSvApp_cleanup(self, host_list):
        '''
        This funciton deletes the OVSvApps
        on failure
        '''
        msg = (_("OVSvApp Installation not successful "
                 "for hosts: %s."
                 " Skipping migration. \n") % (host_list))
        sys.stdout.write(msg)
        self.logger.error(msg)
        DestroyOVSvApp().\
            destroy_ovsvapp_system_migration(self.settings['clusters'])
        #NetworkingApiClient().delete_ipam_dcm(mgmt_ip_list_del)
        raise OVSvAppError(msg)

    def start_migration(self):
        '''
         This function migrates the networking of virtual machines from
         VSS or DVS to DVS and then clone and create the OVSvApp VM

        '''
        try:
            self.logger.info("\n============================================\n"
                             "*****    Starting Network Migration     *****\n"
                             "===========================================\n\n")
            sys.stdout.write(_("Starting Network Migration") + "\n")

            session, datacenter, network_folder, vm_folder, clusters,\
                hosts, fresh_hosts = self.lib_obj.establish_dc_connection()
            dvs_type = vim.DistributedVirtualSwitch
            mgmt_ip_list = ['100.100.200.219']
            mgmt_ip_list_del = []
            if not self.settings['enable_dcm_dhcp']:
                '''
                allocation = None
                ip_user = self.settings['vcenter_name'] + '-' + \
                    self.settings['clusters'][0]
                allocation = NetworkingApiClient().\
                    post_ipam_dcm(len(fresh_hosts), ip_user)
                for x in allocation:
                    mgmt_ip_list.append(str(x['address']))
                '''
                mgmt_ip_list_del = mgmt_ip_list[:]
                
                self.logger.debug("IP list recieved from server: %s" % mgmt_ip_list)
                if len(mgmt_ip_list) < len(fresh_hosts):
                    self.logger.exception("start_migration - Exit - as "
                                          "management IP range is "
                                          "less than the number of "
                                          "ESXi hosts.")
                    raise Exception(_("Management IP range is less "
                                    "than the number of ESXi hosts. Can't "
                                    "proceed further! Rerun the ESXi "
                                    "migration after making proper changes "
                                    "IP allocation server."))
                '''
                client = NetworkingApiClient()
                dcm = client.get_dcm_network()
                dcm_network = IPNetwork(dcm['cidr'])
                '''
                self.settings['netmask'] = '255.255.0.0'
                self.settings['gateway_ip'] = '100.100.0.1'
                self.logger.debug("Netmask recieved: %s" % self.settings['netmask'])
                self.logger.debug("Gateway recieved: %s" % self.settings['gateway_ip'])

            # Step-1: Detect migration type and create all VDS with
            # respective PGs execute always
            if not hosts:
                self.logger.warn("Nothing to migrate as"
                                 " host list is empty!")
                sys.stdout.write(_("Nothing to migrate as"
                                   " host list is empty!") + "\n")
                return 0

            mgmt_switch_obj, vmk_pg_obj = self.lib_obj.\
                _detect_mgmt_dvSwitch(network_folder, hosts)
            self.vapp_installer_inst.mgmt_switch_obj = mgmt_switch_obj
            self.vapp_installer_inst.mgmt_pg_obj = vmk_pg_obj

            self.logger.info("\n======================== Processing Step 1"
                             " ========================\n"
                             "\nCreating mgmt, uplink and trunk DVS\n")
            sys.stdout.write(_("Creating Managament, Uplink and "
                               "Trunk DVS") + "\n")
            self.vapp_installer_inst.\
                create_dvswitch_and_portgroup_for_migration(
                    session, network_folder, hosts)
            #Step-2: Migrate the Management network
            if self.settings['migrate_mgmt']:
                sys.stdout.write(_("Migrating Management Network") + "\n")
                self.logger.info("\n======================== Processing Step 2"
                                 " ========================\n"
                                 "\nMigrating Management Network\n")
                #Migrating vCNS VMs, with flag kept as True
                self.lib_obj.migrate_virtual_machines(session, hosts,
                                                      network_folder,
                                                      vm_folder, True)

                self.lib_obj.update_vmkernel_networking(session,
                                                        network_folder,
                                                        hosts)
            else:
                self.logger.info("\n======= migrate_mgmt value is False"
                                 " ========================\n"
                                 "\n Not migrating Management Network\n")

            # Step-3: install OVSvApp
            # execute always
            self.logger.info("\n======================== Processing Step 3"
                             " ========================\n"
                             "\nInstalling OVSvApp\n")
            sys.stdout.write(_("Installing OVSvApp") + "\n")

            self.util.process_ovsvapp_template(session, clusters,
                                               self.settings['template_name'],
                                               vm_folder)
            is_new_host = False
            exec_args = [(session, datacenter, host, is_new_host, ip)\
                            for host, ip in zip(fresh_hosts, mgmt_ip_list)]

            results = self.util.\
                exec_multiprocessing(self.create_vapp.create_vm_wrapper,
                                     exec_args)

            # Dump OVSvApp creation status in ovs_vap.json
            self.util.dump_json_data(JSON_DICT)

            #Handling to check the OVSvAPP status on Hosts;
            '''
            failed_OVSvApps = {}
            failed_OVSvApps = self.lib_obj.\
                _parse_json_dict(JSON_DICT, fresh_hosts)
            
            if failed_OVSvApps:
                host_list = []
                for key in failed_OVSvApps.keys():
                    host_list.append(key)
                self._do_OVSvApp_cleanup(host_list)

            # Active Host check for OVSvApp
            
            auth = GetAuthorizationToken(self.settings)
            final_active_host, final_inactive_host = auth.get_hpvcn_status(
                hosts)
            host_list = []
            if len(final_inactive_host) != 0:
                for host in final_inactive_host:
                    host_list.append(host['name'])
                self._do_OVSvApp_cleanup(host_list)

            self.logger.debug("Active Host List is %s" % final_active_host)
            hosts = final_active_host
            time.sleep(120)

            #Updating OVSvAPP VM
            if self.settings['do_update'] and results != [None]:
                self.logger.debug("Proceeding to update OVSvAPP VMs!.")
                self.vapp_installer_inst.update_ovsvapp(results)

            # Dump cluster activation status in ovs_vap.json
            self.util.get_cluster_activation_status()
            self.util.dump_json_data(JSON_DICT)

            # Port binding status check for ovsvapps
            self.logger.info("Port binding status check for ovsvapps.")
            auth = GetAuthorizationToken(self.settings)
            token = auth.get_user_token()
            token_id = token['token']['id']
            ports = auth.get_port_list(token_id)

            for host in hosts:
                prefix = 'ovsvapp-'
                suffix = str(host['name']).replace('.', '-')
                ovsvapp = prefix + suffix
                for vm in host['obj'].vm:
                    black_listed_ports = []
                    for item in ports['ports']:
                        device_id_match = False
                        if item['device_id'] != str(vm.config.name):
                            continue
                        else:
                            device_id_match = True
                        if device_id_match:
                            if item['binding:host_id'] != ovsvapp:
                                black_listed_ports.append(item['id'])

                    if black_listed_ports:
                        msg = (_('ovsvapp "%s" binding is not completed on '
                                 'port %s on VM %s.\n') % (ovsvapp,
                                                           black_listed_ports,
                                                           vm.config.name))
                        self.logger.warning(msg)
                        sys.stdout.write(msg)

            '''
            self.logger.info("Processing for creation of PGs on \
                trunk VDS")
            # Step-4-1: Update network configuration of hosts
            # to disconnect uplink from trunk VDS and add uplinks
            # to uplinkVDS
            # execute when data_network_migration_type is vds2vds
            if self.settings['data_network_migration_type'] == 'vds2vds':
                self.logger.info("\n======================== Processing Step 4"
                                 " ========================\n"
                                 "\nMigrating uplinks from trunk DVS to "
                                 "uplink DVS\n")
                sys.stdout.write(_("Migrating uplinks from trunk DVS to "
                                   "uplink DVS") + "\n")
                self.lib_obj.update_host_network_configuration(
                    session,
                    network_folder,
                    active_host=hosts)

            # Step-4-2: Adding trunk PGs to trunk VDS
            # execute when data_network_migration_type is vss2vds
            if self.settings['data_network_migration_type'] == 'vss2vds':
                self.logger.info("\n======================== Processing Step 4"
                                 " ========================\n"
                                 "\nAdding trunk PGs to trunk DVS\n")
                sys.stdout.write(_("Adding trunk PGs to trunk DVS") + "\n")
                trunk_dvs_name = self.settings['trunk_dvs_name']
                trunk_dv_switch = network_folder.find_by_name(
                    trunk_dvs_name, dvs_type)
                self.lib_obj.create_PG_to_VDS(session, network_folder,
                                              hosts, trunk_dv_switch,
                                              'trunk',
                                              self.settings['vssname'])
            # Step-5: move only one uplink pnic from data trunk VSS
            # to uplinkVDS
            # execute when data_network_migration_type is vss2vds
            if self.settings['data_network_migration_type'] == 'vss2vds':
                self.logger.info("======================== Processing Step 5"
                                 " ========================\n"
                                 "\nMigrating first uplink from uplink VSS "
                                 "to uplink DVS\n")
                sys.stdout.write(_("Migrating first uplink from uplink VSS "
                                   "to uplink DVS") + "\n")
                uplink_dvs_name = self.settings['uplink_dvs_name']
                dvs_uplink = network_folder.find_by_name(uplink_dvs_name,
                                                         dvs_type)
                self.lib_obj.move_uplink(dvs_uplink,
                                         self.settings['uplink_dvs_name'],
                                         session, hosts,
                                         self.settings['vssname'],
                                         is_first_round=True)

            # Step-6: migrate all vms to created DVS.
            # execute when data_network_migration_type is vss2vds
            if self.settings['data_network_migration_type'] == 'vss2vds':
                self.logger.info("\n======================== Processing Step 6"
                                 " ========================\n"
                                 "\nMigrating all VMs\n")
                sys.stdout.write(_("Migrating all VMs") + "\n")
                self.lib_obj.migrate_virtual_machines(session, hosts,
                                                      network_folder,
                                                      vm_folder)

                self.logger.warn("Security group rules will not be created"
                                 " for migrated VMs in same network on same host.")
                sys.stdout.write(_("Security group rules will not be created for "
                                   "migrated VMs in same network on "
                                   "same host.") + "\n")

                # Step-7: move all uplink pnics from data trunk VSS
                # to uplinkVDS
                # execute when data_network_migration_type is vss2vds
                self.logger.info("\n======================== Processing Step 7"
                                 " =======================\n"
                                 "\nMigrating remaining uplinks from uplink "
                                 "VSS to uplink DVS\n")
                sys.stdout.write(_("Migrating remaining uplinks from uplink "
                                   "VSS to uplink DVS") + "\n")
                self.lib_obj.move_uplink(dvs_uplink,
                                         self.settings['uplink_dvs_name'],
                                         session, hosts,
                                         self.settings['vssname'],
                                         is_first_round=False)
            #Populating the trunk VDS ports details config file
            self.lib_obj.\
                _populate_ports_rollback_config(network_folder)

        except EsxiMigrationError as e:
            #self._write_failed_clusters()
            self.logger.exception("\n\n \033[31m Caught exception: %s "
                                  "\033[31m  \033[0m\n\n" % e)
            sys.stderr.write(_("Caught exception : %s") % e)
            sys.stdout.write("\n")
            raise e

        except vmodl.MethodFault as e:
            #self._write_failed_clusters()
            self.logger.error("Caught VMware API fault: %s" % e.msg)
            sys.stderr.write(_("Caught VMware API fault: %s") % e.msg)
            sys.stdout.write("\n")
            raise e

        except OVSvAppValidationError as e:
            #self._write_failed_clusters()
            self.logger.exception("\n\n \033[31m Caught exception: %s "
                                  "\033[31m  \033[0m\n\n" % e.msg)
            sys.stderr.write(_("Caught exception : %s") % e.msg)
            sys.stdout.write("\n")
            raise e

        except OVSvAppError as e:
            #self._write_failed_clusters()
            self.logger.exception("\n\n \033[31m Caught exception: %s "
                                  "\033[31m  \033[0m\n\n" % e.msg)
            sys.stderr.write(_("Caught exception : %s") % e.msg)
            sys.stdout.write("\n")
            raise e

        except Exception as e:
            #self._write_failed_clusters()
            self.logger.exception("\n\n \033[31m Unknown exception occurred: %s "
                                  "\033[31m  \033[0m\n\n" % e)
            sys.stderr.write(_("Unknown exception occurred, check logs for more detail: %s") % e)
            sys.stdout.write("\n")
            raise e

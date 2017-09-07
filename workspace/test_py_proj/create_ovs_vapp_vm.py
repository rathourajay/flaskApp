# (C) Copyright 2014-2015 HP Development Company, L.P.

import itertools
import threading
import base64
import time
from pyVmomi import vim, vmodl
from csmigrate.esxi.hp_ovsvapp_migration.installer.configure_ovsvapp \
    import ConfigureOVSvApp
from csmigrate.esxi.hp_ovsvapp_migration.installer.disable_HA_on_ovsvapp \
    import DisableHAOnOvsvapp
from csmigrate.esxi.hp_ovsvapp_migration.util.vapp_util import OVSvAppUtil
from csmigrate.esxi.hp_ovsvapp_migration.util.vapp_constants import ( \
    OVS_VAPP_PREFIX,
    OVS_VAPP_ANNOTATION,
    IP_CATALOG,
    OVS_VAPP_USER,
    OVS_VAPP_SECRET)
from csmigrate.esxi.hp_ovsvapp_migration.util.status_messages import get_status
VRSTATUS_FILE = '/var/log/neutron/hpvcn-agent/vrstatus'


class CreateOVSvApp:

    def __init__(self, logger, settings):
        self.logger = logger
        self.util = OVSvAppUtil(logger, settings)
        self.settings = settings

    def _get_available_network(self, host, pg_name):
        """
        Verify and return the requested port group object / network
        @return: Port Group Object/Network
        """
        networks = {}
        if self.settings['is_auto_dvs']:
            all_nets = host['obj'].network
        else:
            all_nets = host['network']
        for net in all_nets:
            networks[net.name] = net
        network = networks.get(pg_name, None)
        if not network:
            self.logger.error("Either the port group '%s' is not part of host "
                              "'%s' Or the port group doesn't exist ! OVSvApp "
                              "won't be deployed on this host"
                              % (pg_name, host['name']))
            msg = get_status(503, status='failed',
                             host=self.util.get_mo_id(host['obj']))
            cluster_key = self.util.get_json_value(host['parent'].name)
            cluster_key[host['name']] = msg
        return network

    def _get_pci_passthrough_config(self, content, host, cluster):
        """
        Create Virtual PCI pass through config spec
        @return: Virtual PCI pass through spec
        """
        pci_info = cluster.environmentBrowser.QueryConfigTarget(host['obj']). \
            pciPassthrough
        if not pci_info:
            self.logger.warn("PCI Pass through is not activated on Esxi "
                             "host '%s' . OVSvApp won't be installed on this "
                             "host" % host['name'])
            return None
        pcispec = vim.vm.device.VirtualDeviceSpec()
        pcispec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        pcispec.device = vim.vm.device.VirtualPCIPassthrough()
        pcispec.device.backing = vim.vm.device.VirtualPCIPassthrough. \
            DeviceBackingInfo()
        pcispec.device.backing.deviceId = "0"
        pcispec.device.backing.id = pci_info[0].pciDevice.id
        pcispec.device.backing.systemId = pci_info[0].systemId
        pcispec.device.backing.vendorId = pci_info[0].pciDevice.vendorId
        pcispec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        pcispec.device.connectable.startConnected = True
        pcispec.device.connectable.allowGuestControl = True
        return pcispec

    def _get_dv_ports(self):
        dv_ports = {}
        dv_ports['trunk_interface'] = self.settings['trunk_port_name']
        if not self.settings['is_pci']:
            dv_ports['data_interface'] = self.settings['data_port_name']
            dv_ports['dcm_interface'] = self.settings['dcm_port_name']
            dv_ports['clm_interface'] = self.settings['clm_port_name']
        return dv_ports

    def _get_nic_config(self, cluster_name, host):
        """
        Create Virtual NIC spec
        @return: VNIC spec
        """
        devices = []
        count = 0
        pgs = {}
        dv_ports = self._get_dv_ports()
        for key in dv_ports.keys():
            nicspec = vim.vm.device.VirtualDeviceSpec()
            nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nicspec.device = vim.vm.device.VirtualVmxnet3()
            nicspec.device.wakeOnLanEnabled = True
            nicspec.device.deviceInfo = vim.Description()
            pg_name = dv_ports.get(key)
            if (self.settings['tenant_network_type'] == 'vxlan'
                    and key == 'trunk_interface'):
                datacenter_cluster = "_".join([self.settings['datacenter'],
                                               cluster_name])
                if datacenter_cluster in self.settings['trunk_port_name']:
                    pg_name = self.settings['trunk_port_name']
                else:
                    pg_name = "_".join([self.settings['trunk_port_name'],
                                        datacenter_cluster])
            pg_obj = self._get_available_network(host, pg_name)
            pgs[key] = pg_obj
            if not pg_obj:
                return None
            dvs_port_connection = vim.dvs.PortConnection()
            dvs_port_connection.portgroupKey = pg_obj.key
            dvs_port_connection.switchUuid = \
                pg_obj.config.distributedVirtualSwitch.uuid
            self.logger.debug("Configuring eth%d with network %s"
                              % (count, pg_name))
            nicspec.device.backing = vim.vm.device. \
                VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nicspec.device.backing.port = dvs_port_connection
            nicspec.device.connectable = \
                vim.vm.device.VirtualDevice.ConnectInfo()
            nicspec.device.connectable.startConnected = True
            nicspec.device.connectable.allowGuestControl = True
            count += 1
            devices.append(nicspec)
        self.settings['port_groups'] = pgs
        return devices

    def _get_vm_config(self, devices):
        vmconf = vim.vm.ConfigSpec(deviceChange=devices)
        if self.settings['num_cpu']:
            vmconf.numCPUs = int(self.settings['num_cpu'])
        else:
            self.logger.warn("Number of CPU for OVSvAPP has not "
                             "been provided. OVSvAPP will be installed"
                             " with default 4 CPU")
        if self.settings['memory_mb']:
            vmconf.memoryMB = long(self.settings['memory_mb'])
        else:
            self.logger.warn("Number of RAM for OVSvAPP has not "
                             "been provided. OVSvAPP will be installed"
                             " with default 4048 MB of RAM")
        vmconf.annotation = OVS_VAPP_ANNOTATION
        return vmconf

    def _get_ovsvapp_name(self, host_name):
        if self.util.is_valid_ip(host_name):
            ovs_vm_name = "-".join([OVS_VAPP_PREFIX,
                                    host_name.
                                    replace('.', '-')])
        else:
            ovs_vm_name = "-".join([OVS_VAPP_PREFIX,
                                    host_name])
        return ovs_vm_name

    def _wait_for_ip_to_populate(self, vm, timeout=300):
        timeout = abs(int(timeout))
        start_time = time.time()
        while (time.time() - start_time) <= timeout:
            vapp_ips = []
            vapp_ipv4 = []
            nic_infos = vm.guest.net
            if nic_infos:
                for nic in nic_infos:
                    vapp_ips.append(nic.ipAddress)
                vapp_ips = list(itertools.chain(*vapp_ips))
                vapp_ipv4 = [ip for ip in vapp_ips if
                             self.util.is_valid_ip(ip)]
            if vapp_ipv4:
                if ((self.settings['tenant_network_type'] == 'vlan' and
                     len(vapp_ipv4) == 2) or
                    (self.settings['tenant_network_type'] == 'vxlan' and
                     len(vapp_ipv4) == 3)):
                    return True
            self.logger.info("Waiting for OVSvApp IPs to populate ...")
            time.sleep(10)
        self.logger.error("Timed out while for both DCM and CLM IP's to be "
                          "populated. Installation/Update may or may not "
                          "work !")

    def _read_vrstatus_file(self, status, host, cluster_key):
        rabbit_mq = 'rabbitmq:ok'
        bridge_flows = 'br_pt_flows:ok'
        vcenter = 'vcenter:ok'
        hpvcn_agent = 'hpvcn-neutron-agent:ok'
        if hpvcn_agent not in status:
            self.logger.error("unable to start hpvcn-neutron-agent")
            msg = get_status(529, status='failed',
                             host=self.util.get_mo_id(host['obj']))
            cluster_key[host['name']] = msg
            return False
        if rabbit_mq not in status:
            self.logger.info("unable to connect to rabbitmq server")
            msg = get_status(526, status='failed',
                             host=self.util.get_mo_id(host['obj']))
            cluster_key[host['name']] = msg
            return False
        if bridge_flows not in status:
            self.logger.error("OVS bridges,ports and security group"
                              " flows doesn't exists")
            msg = get_status(527, status='failed',
                             host=self.util.get_mo_id(host['obj']))
            cluster_key[host['name']] = msg
            return False
        if vcenter not in status:
            self.logger.error("hpvcn-neutron-agent is not able to"
                              " connect to vcenter")
            msg = get_status(531, status='failed',
                             host=self.util.get_mo_id(host['obj']))
            cluster_key[host['name']] = msg
            return False
        return True


    def wait_for_controller_connection(self, ovs_vm_name, timeout=120):
        neutron_client = self.util.get_neutron_client()
        import time
        timeout = abs(int(timeout))
        start_time = time.time()
        while (time.time() - start_time) <= timeout:
            response = neutron_client.list_agents(agent_type='HP VCN L2 Agent')
            if response and 'agents' in response:
                agent_list = response['agents']
                for agent in agent_list:
                    if agent['host'] == ovs_vm_name and agent['alive']:
                        return True
            time.sleep(10)
        self.logger.error("Timed out while waiting for controller connection")
    def create_vm_wrapper(self, args):
        return self.create_vm(*args)

    def create_vm(self, session, datacenter, host, new_hosts, vm_ip):
        """
        Clone the appliance and create OVSvApp on each host
        """
        try:
            is_ip = None
            host_name = host['name']
            cluster = host['cluster']
            if not new_hosts:
                vm_folder = datacenter['vmFolder']
                net_folder = datacenter['networkFolder']
                resource_pool = cluster['resourcePool']
            else:
                vm_folder = datacenter.vmFolder
                net_folder = datacenter.networkFolder
                resource_pool = host['obj'].parent.resourcePool
            devices = self._get_nic_config(cluster['name'], host)
            if devices:
                if self.settings['is_pci']:
                    pci_spec = self. \
                        _get_pci_passthrough_config(session['content'],
                                                    host,
                                                    cluster['obj'])
                    if pci_spec:
                        devices.append(pci_spec)
                vmconf = self._get_vm_config(devices)
                location = self.util.get_relocation_spec(host['obj'],
                                                         resource_pool)
                ovs_vm_name = self._get_ovsvapp_name(host_name)
                self.logger.debug("Cloning and creating "
                                  "%s ..." % ovs_vm_name)
                template = host['cluster'].get('template')
                cloned_vm = self.util.clone_vm(session['si'], template,
                                               location, ovs_vm_name,
                                               vm_folder, vmconf, False)
                cluster_key = self.util.get_json_value(cluster['name'])
                if isinstance(cloned_vm, vim.VirtualMachine):
                    self.logger.info("'%s' has been created on host '%s'" %
                                     (ovs_vm_name, host_name))
                    if not new_hosts:
                        DisableHAOnOvsvapp(self.logger, self.util). \
                            disable_ha_on_ovsvapp(session['si'],
                                                  cloned_vm, cluster,
                                                  host)
                    ConfigureOVSvApp(self.logger, self.util). \
                        customize_ovsvapp_vm(session['content'],
                                             net_folder, cloned_vm,
                                             cluster, host,
                                             self.settings,
                                             vm_ip)
                    is_ip = self._wait_for_ip_to_populate(cloned_vm)
                    is_configured = False
                    if is_ip:
                        time.sleep(60)
                        vmware_status = ConfigureOVSvApp(self.logger, self.util). \
                            _wait_for_vmware_tools(cloned_vm, host)
                        if not vmware_status: 
                            raise Exception
                        creds = vim.vm.guest. \
                            NamePasswordAuthentication(username=OVS_VAPP_USER,
                                                       password=base64.
                                                       b64decode
                                                       (OVS_VAPP_SECRET))
                        response = self.util.download_file(session['content'],
                                                           cloned_vm, creds,
                                                           VRSTATUS_FILE)
                        if response is not None:
                            response_content = response.content
                            if response_content:
                                is_configured = self. \
                                    _read_vrstatus_file(response_content,
                                                        host,
                                                        cluster_key)
                        else:
                            self.logger.error("Configuration status is empty"
                                              " unable to get configuration"
                                              " status or download fails")
                            msg = get_status(530, status='failed',
                                             ovsvapp=ovs_vm_name,
                                             host=self.util.
                                             get_mo_id(host['obj']))
                            cluster_key[host['name']] = msg
                    else:
                        self.logger.error("Couldn't retrieve IPs within 5mins."
                                          " Declaring a failure installation!")
                        msg = get_status(528, status='failed',
                                         ovsvapp=ovs_vm_name,
                                         host=self.util.get_mo_id(host['obj']))
                        cluster_key[host['name']] = msg
                    if new_hosts:
                        if not is_configured:
                            err = True
                        else:
                            err = False
                        if err:
                            self.util. \
                                destroy_failed_commissioned_vapps(host,
                                                                  session
                                                                  ['si'])
                        self.util.move_host_back_to_cluster(session['si'],
                                                            host, err)
                        if not err:
                            DisableHAOnOvsvapp(self.logger, self.util). \
                                disable_ha_on_ovsvapp(session['si'],
                                                      cloned_vm, cluster,
                                                      host)
                    if not is_configured:
                        return
                    if not self.settings['do_update']:
                        msg = get_status(204, status='success',
                                         ovsvapp=ovs_vm_name,
                                         host=self.util.get_mo_id(host['obj']))
                        cluster_key[host['name']] = msg
                    lock = threading.Lock()
                    with lock:
                        IP_CATALOG = self.util. \
                            update_json_data({ovs_vm_name: vm_ip})
                        self.util.dump_json_data(IP_CATALOG, True)
                else:
                    self.logger.error("Error occurred while cloning %s on "
                                      "host %s" % (ovs_vm_name, host_name))
                    msg = get_status(502, status='failed',
                                     host=self.util.get_mo_id(host['obj']))
                    if new_hosts:
                        self.util.move_host_back_to_cluster(session['si'],
                                                            host, True)
                    cluster_key[host['name']] = msg
                return {ovs_vm_name: host}
        except vmodl.MethodFault as e:
            # Vmware related exceptions
            self.logger.exception("Caught VMware API fault: %s" % e.msg)
            return
        except Exception as e:
            # Unknown exceptions
            self.logger.exception("Caught exception: %s" % e)
            return

def _create_host_config_spec(self, hosts, pnic_device):
        dvs_host_configs = []
        api_versions = []
        for host in hosts:
            pnic_spec = []
            dvs_host_config = vim.dvs.HostMember.ConfigSpec()
            dvs_host_config.operation = vim.ConfigSpecOperation.add
            cluster_key = self.util.get_json_value(host['parent'].name)
            if pnic_device:
                dvs_host_config.backing = vim.dvs.HostMember.PnicBacking()
                phys_nic = self._get_free_physical_nic(host, pnic_device)
                if not phys_nic:
                    msg = get_status(324, status='failed',
                                     host=self.util.get_mo_id(host['obj']))
                    cluster_key[host['name']] = msg
                    continue
                for pnic in phys_nic:
                    pnic_spec.append(vim.dvs.HostMember.
                                     PnicSpec(pnicDevice=pnic.lower()))
                dvs_host_config.backing.pnicSpec = pnic_spec
            dvs_host_config.host = host['obj']
            dvs_host_configs.append(dvs_host_config)
            api_versions.append(host['config.product.apiVersion'])
        return dvs_host_configs, api_versions
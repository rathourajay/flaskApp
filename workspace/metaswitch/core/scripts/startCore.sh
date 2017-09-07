echo Starting ENS Core >>/var/log/ens/ens.log
nohup python /opt/ens/ensllo.py /etc/ens/policy/app-policy.db >>/var/log/ens/ens.log 2>&1 &
nohup python /opt/ens/ensdiscover.py /etc/ens/policy/app-policy.db >>/var/log/ens/ens.log 2>&1 &
nohup python /opt/ens/enspaac.py ens.edgenet.cloud /etc/ens/repo/app.db >>/var/log/ens/ens.log 2>&1 &

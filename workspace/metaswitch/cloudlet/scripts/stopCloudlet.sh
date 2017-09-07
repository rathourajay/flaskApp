echo Stopping ENS Cloudlet >>/var/log/ens/ens.log
sudo kill -9 `ps --no-header -C python -o pid,cmd | grep ensproberesponder.py | awk -e '{print $1}'`
sudo kill -9 `ps --no-header -C python -o pid,cmd | grep ensclc.py | awk -e '{print $1}'`
sudo kill -9 `ps --no-header -C ensdispatcher -o pid`

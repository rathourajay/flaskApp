echo Stopping ENS Core >>/var/log/ens/ens.log
sudo kill -9 `ps --no-header -C python -o pid,cmd | grep enspaac.py | awk -e '{print $1}'`
sudo kill -9 `ps --no-header -C python -o pid,cmd | grep ensdiscover.py | awk -e '{print $1}'`
sudo kill -9 `ps --no-header -C python -o pid,cmd | grep ensllo.py | awk -e '{print $1}'`

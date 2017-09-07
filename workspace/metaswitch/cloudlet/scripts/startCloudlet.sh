mkdir -p /tmp/ens
chmod 777 /tmp/ens
if [ ! -e /tmp/ens/dispatcher.pipe ]
then
  mkfifo /tmp/ens/dispatcher.pipe
fi
echo Starting ENS Cloudlet >>/var/log/ens/ens.log
PUBLIC_IP=`curl -s http://169.254.169.254/latest/meta-data/public-ipv4`
nohup sudo /opt/ens/ensdispatcher < /tmp/ens/dispatcher.pipe >>/var/log/ens/ens.log 2>&1 &
nohup python /opt/ens/ensclc.py $PUBLIC_IP >>/var/log/ens/ens.log 2>&1 &
nohup python /opt/ens/ensproberesponder.py >>/var/log/ens/ens.log 2>&1 &

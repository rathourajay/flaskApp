# Pull Core files from build server to a temporary directory
echo Pulling Core image from www.edgenet.cloud
TMP=`mktemp -d`
scp -r ubuntu@www.edgenet.cloud:ensbuild/core/build/out/* $TMP >/dev/null

# Copy Core files to /opt/ens
sudo mkdir -p /opt/ens
sudo cp $TMP/opt/* /opt/ens

# Create directory for logs
sudo mkdir -p /var/log/ens
sudo chmod 777 /var/log/ens

# Create configuration directory
sudo mkdir -p /etc/ens/policy
sudo chmod 777 /etc/ens/policy

# Create symlinks in /usr/local/bin
if [ ! -h /usr/local/bin/stopCore ]
then
  sudo ln -s /opt/ens/startCore.sh /usr/local/bin/startCore
fi
if [ ! -h /usr/local/bin/stopCore ]
then
  sudo ln -s /opt/ens/stopCore.sh /usr/local/bin/stopCore
fi
if [ ! -h /usr/local/bin/updateCore ]
then
  sudo ln -s /opt/ens/updateCore.sh /usr/local/bin/updateCore
fi

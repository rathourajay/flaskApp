echo 127.0.0.1 $HOSTNAME | sudo tee --append /etc/hosts

# Install docker and set up repository
`(dirname "$0")`/install-docker.sh

# Install pre-requisites for RESTful interface
sudo apt-get install -y --force-yes python-pip
sudo pip install flask

# Pull Cloudlet files from build server to a temporary directory
echo Pulling Cloudlet image from www.edgenet.cloud
TMP=`mktemp -d`
scp -r ubuntu@www.edgenet.cloud:ensbuild/cloudlet/build/out/* $TMP >/dev/null

# Copy Cloudlet files to /opt/ens
sudo mkdir -p /opt/ens
sudo cp $TMP/opt/* /opt/ens

# Create directory for logs
sudo mkdir -p /var/log/ens
sudo chmod 777 /var/log/ens

# Create configuration directory
sudo mkdir -p /etc/ens/repo
sudo chmod 777 /etc/ens/repo

# Create symlinks in /usr/local/bin
if [ ! -h /usr/local/bin/startCloudlet ]
then
  sudo ln -s /opt/ens/startCloudlet.sh /usr/local/bin/startCloudlet
fi
if [ ! -h /usr/local/bin/stopCloudlet ]
then
  sudo ln -s /opt/ens/stopCloudlet.sh /usr/local/bin/stopCloudlet
fi
if [ ! -h /usr/local/bin/updateCloudlet ]
then
  sudo ln -s /opt/ens/updateCloudlet.sh /usr/local/bin/updateCloudlet
fi

# Remove the temporary directory
rm -rf $TMP

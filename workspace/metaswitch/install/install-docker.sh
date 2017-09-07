# Test for docker install
sudo docker -v >/dev/null 2>&1
if [ "$?" == "127" ]
then
  # Docker is not installed, so install it
  echo Installing Docker
  sudo apt-get update
  sudo apt-get install -y --force-yes apt-transport-https ca-certificates
  sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
  echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" | sudo tee --append /etc/apt/sources.list.d/docker.list
  sudo apt-get update
  sudo apt-get install -y --force-yes linux-image-extra-$(uname -r) linux-image-extra-virtual
  sudo apt-get install -y --force-yes docker-engine
  sudo groupadd docker
  sudo usermod -aG docker ubuntu
else
  # Docker already installed
  echo Docker already installed
fi

# Pull certificate file from build server to a temporary directory
echo Pulling certificate from www.edgenet.cloud
TMP=`mktemp -d`
scp -r ubuntu@www.edgenet.cloud:ensbuild/common/certs/domain.crt $TMP >/dev/null

# Set up certificates for private Docker repository
sudo mkdir -p /etc/docker/certs.d/edgenet.cloud:5000
sudo cp $TMP/domain.crt /etc/docker/certs.d/edgenet.cloud:5000/ca.crt

# Delete temporary directory
rm -rf $TMP


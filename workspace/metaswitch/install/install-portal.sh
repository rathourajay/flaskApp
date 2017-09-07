# Install docker and set up repository
`(dirname "$0")`/install-docker.sh

# Pull Portal image from build server to a temporary directory
echo Pulling Portal image from www.edgenet.cloud
TMP=`mktemp -d`
scp -r ubuntu@www.edgenet.cloud:ensbuild/portal/app/* $TMP >/dev/null

# Install pre-requisites for portal
sudo apt-get install -y --force-yes python-pip
sudo apt-get install -y --force-yes python-dev
sudo apt-get install -y --force-yes libffi-dev
sudo pip install flask
sudo pip install flask-wtf
sudo pip install flask-login
sudo pip install flask-sqlalchemy
sudo pip install bcrypt

# Copy the portal application and other files
sudo cp $TMP/app/* ~/ensportal

# Remove the temporary directory
rm -rf $TMP


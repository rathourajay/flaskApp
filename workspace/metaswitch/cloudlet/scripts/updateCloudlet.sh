# Pull updated image from build server to a temporary directory
echo Pulling Cloudlet image from www.edgenet.cloud
TMP=`mktemp -d`
scp -r ubuntu@www.edgenet.cloud:ensbuild/cloudlet/build/out/* $TMP >/dev/null

# Stop cloudlet
echo Stopping ENS Cloudlet
stopCloudlet

# Copy updated files
echo Updating
sudo -E cp $TMP/opt/* /opt/ens

# Restart cloudlet
echo Restarting ENS Cloudlet
startCloudlet

# Remove temporary directory
rm -rf $TMP

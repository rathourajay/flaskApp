# Pull updated image from build server to a temporary directory
echo Pulling Core image from www.edgenet.cloud
TMP=`mktemp -d`
scp -r ubuntu@www.edgenet.cloud:ensbuild/core/build/out/* $TMP >/dev/null

# Stop core
echo Stopping ENS Core
stopCore

# Copy updated files
echo Updating
sudo -E cp $TMP/opt/* /opt/ens

# Restart core
echo Restarting ENS Core
startCore

# Remove temporary directory
rm -rf $TMP

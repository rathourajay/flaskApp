# Check the language is supported
if [ "$1" = "C" ] || [ "$1" = "c" ] || [ "$1" = "C++" ] || [ "$1" = "c++" ]
then
    RUNTIME=runtimecpp
elif [ "$1" = "Python" ] || [ "$1" = "python" ]
then
    RUNTIME=runtimepy
else
    echo Unsupported language $1
    exit 1
fi

# Make a temporary directory to build the image
TMP=`mktemp -d`
mkdir $TMP/workload

# Copy the specified workload files to the temporary directory
cp $3/* $TMP/workload

# Create a Dockerfile
echo "FROM repo.edgenet.cloud:5000/ens/$RUNTIME:latest" >> $TMP/Dockerfile
echo "COPY workload/* /opt/ens/" >> $TMP/Dockerfile

# Build the image
docker build -t repo.edgenet.cloud:5000/ens/$2 $TMP
docker push repo.edgenet.cloud:5000/ens/$2

# Remove the temporary directory and contents
rm -rf $TMP


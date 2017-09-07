# Make a temporary directory to build the image
TMP=`mktemp -d`
mkdir -p $TMP/runtime

# Copy the Python workload script to the temporary directory
cp ../workloadruntime/python/workloadPy.sh $TMP/runtime

# Make the Python extension module
mkdir -p $TMP/build
cp ../../../common/iwc/* $TMP/build
cp ../workloadruntime/python/ensiwcpython.cpp $TMP/build
cp ../workloadruntime/python/setup.py $TMP/build
(cd $TMP/build; python setup.py build --build-base=$TMP/build --build-temp=$TMP/build)
cp $TMP/build/lib.linux-x86_64-2.7/ensiwc.so $TMP/runtime

# Copy the Python runtime to the temporary directory
cp ../workloadruntime/python/enswmain.py $TMP/runtime
cp ../workloadruntime/python/enswr.py $TMP/runtime

# Copy the Python runtime Dockerfile to the temporary directory
cp ../workloadruntime/python/DockerfilePy $TMP/Dockerfile

# Build the image
docker build -t repo.edgenet.cloud:5000/ens/runtimepy $TMP
docker push repo.edgenet.cloud:5000/ens/runtimepy

# Remove the temporary directory and contents
rm -rf $TMP


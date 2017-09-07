# Make a temporary directory to build the image
TMP=`mktemp -d`
mkdir $TMP/runtime

# Copy the C/C++ workload script to the temporary directory
cp ../workloadruntime/cpp/workloadCpp.sh $TMP/runtime

# Make the IWC shared library
g++ -g -Wall -std=c++0x -fpic -shared -o $TMP/runtime/libensiwc.so -I../../../common/iwc ../../../common/iwc/ensiwcworkload.cpp ../../../common/iwc/enslog.cpp ../../../common/iwc/ensiwcmem.cpp -pthread

# Make the C/C++ runtime
g++ -g -Wall -std=c++0x -o $TMP/runtime/enscppruntime -I../../../common/iwc -I../../../jsoncpp/dist ../workloadruntime/cpp/enscppruntime.cpp ../../../common/iwc/enslog.cpp ../../../jsoncpp/dist/jsoncpp.cpp -pthread -L$TMP/runtime -ldl -lensiwc

# Copy the C/C++ runtime Dockerfile to the temporary directory
cp ../workloadruntime/cpp/DockerfileCpp $TMP/Dockerfile

# Build the image
docker build -t repo.edgenet.cloud:5000/ens/runtimecpp $TMP
docker push repo.edgenet.cloud:5000/ens/runtimecpp

# Remove the temporary directory and contents
rm -rf $TMP

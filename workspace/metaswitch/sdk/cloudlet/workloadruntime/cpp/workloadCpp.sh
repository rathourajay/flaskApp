#!/bin/bash

# ENS C/C++ workload launcher

cd /opt/ens
export LD_LIBRARY_PATH=/opt/ens
echo Starting C++ runtime $1
./enscppruntime $1



#!/bin/bash

# ENS Python workload launcher

cd /opt/ens
export LD_LIBRARY_PATH=/opt/ens
echo Starting Python runtime $1
python2.7 enswmain.py $1



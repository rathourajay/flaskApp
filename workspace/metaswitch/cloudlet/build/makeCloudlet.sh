mkdir -p out/opt
rm out/opt/*
./makedispatcher.sh
cp ../clc/*.py out/opt
cp ../proberesponder/*.py out/opt
cp ../scripts/*Cloudlet.sh out/opt

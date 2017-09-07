mkdir -p obj
g++ -g -Wall -std=c++0x -fpic -shared -o obj/latencyresponder.so -I. latencyresponder.cpp

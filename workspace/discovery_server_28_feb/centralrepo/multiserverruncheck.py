import threading
import thread
import flask
from flask import Flask, request, Response, jsonify
import SocketServer
import os
app_catalog = Flask(__name__)


def MyUDPHandler():
    print "xsdklfjkldsj"


def xyz():
    print "2"
    server = SocketServer.UDPServer(("0.0.0.0", 46543), MyUDPHandler)
    server.serve_forever()
    print "3"


if __name__ == '__main__':
    data = os.system("lsof -i:46543")
    print "data is ", data
    if not data:
        thread.start_new_thread(xyz, ())
    app_catalog.run(
        host="0.0.0.0", port=46546, debug=True, threaded=True)

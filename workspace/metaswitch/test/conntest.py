import sys
import socket
import struct

handshake = struct.Struct('<I I')
event = struct.Struct('<I I 5s')
conn = socket.create_connection( (sys.argv[1], sys.argv[2]) )

# Send handshake and receive response.
print("Sending handshake")
conn.send(handshake.pack(0,1))
rsp = handshake.unpack(conn.recv(8))
print("Received handshake response");

while (True):
    s = "Hello"
    print("Sending: %s" % s)
    conn.send(event.pack(len(s), 0, s))
    rsp = event.unpack(conn.recv(100))
    print("Received: %s" % rsp[2])
    sleep(1.0)

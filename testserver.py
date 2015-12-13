import socket
import sys
import json
import cPickle as pickle

recvsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

recvsock.bind(("", int(sys.argv[1])))

result = recvsock.recvfrom(4096)

recovered = pickle.loads(result[0])

print "sender = " + str(result[1])
print "recovered entry = " + str(recovered)


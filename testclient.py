import socket


sendsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sendsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sendsock.bind(("", 8179))
sendsock.sendto("Hello", ('localhost', 8181))
print sendsock.recvfrom(4096)





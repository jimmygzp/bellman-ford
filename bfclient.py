import sys
import socket
import select
from time import time
from collections import defaultdict
import cPickle as pickle
import datetime
import copy

## LISTS TO KEEP:
## LIST OF NEIGHBORS, VALUE = [ip_addr, port]

'''
global neighbors 

neighbors = []
'''
## DICTS TO KEEP:
## DICT OF COSTS, KEY = [ip_addr, port], VALUE = cost (int)
costs = {}
## DICT OF LAST_CONTACT = [ip_addr, port], VALUE = timestamp
last_contact = {}

## DICT OF UPLINK, KEY = [ip_addr, port], VALUE = 1 for true, 0 for false
uplink = {}##defaultdict(int)

## DICT OF DISTANCE VECTORS, KEY = DESTINATION [ip_addr, port], VALUE = [link[ip_addr, port], cost (int)]
dv = {}
BUFFER_SIZE = 4096

me = (0,0)

DEBUG = 1

DEBUG2 = 0

last_broadcast = time()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setblocking(0)

my_addr = socket.gethostbyname(socket.gethostname())


MAX_COST = float("inf")

## PSEUDOCODE:
## WHILE TRUE:
##		FOR NEIGHBOR IN NEIGHBORS: (IF UPLINK)
## 			IF NEIGHBOR TIMES OUT... MARK DOWNLINK AND LINK UPDATE TO ALL
##      IF WE NEED TO REBROADCAST (OWN TIMEOUT REACHED), THEN WE BROADCAST
##		IF WE RECEIVE A MESSAGE IN DGRAM SOCKET:
##		IF FROM A NEW NEIGHBOR:
##				THEN ADD NEW NEIGHBOR, BROADCAST COSTS
##		IF WE RECEIVE A NEW MESSAGE, THEN WE UPDATE OUR COSTS AND BROADCAST
##		IF WE RECEIVED KEYBOARD COMMAND, HANDLE THAT
##			IF LINKDOWN:
##				MARK DOWNLINK, REBROADCAST COSTS
##			ELIF LINKUP:
##				MARK LINKUP:
##			ELIF SHOWRT:
##				SHOW ROUTE
##			ELIF CLOSE:
##				SHUTDOWN

def kill_link(client):

	sock.sendto('DOWN', client)


def add_neighbor_initial(client, weight):
	## client = (ip_addr, port)
	##global neighbors
	##neighbors.append(client)
	costs[client] = float(weight)
	last_contact[client]= time()
	
	uplink[client] = 1

	dv[me][client] = [client, float(weight)]

	dv[client] = {}

	dv[client][client] = [client, 0] ## must start off by assuming its alive


def add_neighbor_new(client, vector):

	## we are here if the sender of the message is new and unkonwn
	## 1. we determine what the sender thinks the cost between us and the sender is
	## -->add to neighbors, costs
	## 2. update dv graph accordingly
	##neighbors.append(client)


	dv[client] = vector ## add another member to dv
	dv[me][client] = [client, dv[client][me][1]]
	costs[client] = float(dv[client][me][1])

	## update_dv()


def broadcast():
	## for all current connections with uplink:
		## send our dv
	

	print dv[me]

	print uplink

	##global neighbors
	for neighbor, vector in dv.iteritems():
		if neighbor is not me:
			if DEBUG2:
				print neighbor
				print uplink[neighbor]
			if uplink[neighbor]==1:
				if DEBUG2:
					print "broadcast: sending to client " + str(neighbor)
				
				## now we know what the neighbor is. we need to poison the dv
				dv_poisoned = copy.deepcopy(dv[me])

				for dest, path in dv[me].iteritems():
					if path[0] == neighbor and dest != neighbor:
						##print "dv_poisoned[dest][1] = " + str(dv_poisoned[dest][1])
						dv_poisoned[dest][1] = MAX_COST

				print "poisoned message to neighbot %s : %s" % (neighbor, dv_poisoned)
				print "actual dv[me] " + str(dv[me])
				sock.sendto(pickle.dumps(dv_poisoned), neighbor)
	
	last_broadcast = time()
	pass

def showroute():

	print str(datetime.datetime.now()) + ", Current Distance Vector is:"
	for dest, path in dv[me].iteritems():
		if dest is not me:
			if DEBUG:
				print "dest = " + str(dest)
				print "path = " + str(path)
			print "Destination=%s:%d, Cost = %.1f, Link = (%s:%d)" % (dest[0], dest[1], float(path[1]), path[0][0], path[0][1])


def update_dv(): 

	path = ("UNREACHABLE", 0)
	changed = 0
	
	for dest, cost in dv[me].iteritems():
		if dest is not me:
			if DEBUG:
				print "----updating distance to dest : " + str (dest)
				print "----old cost = " + str(cost)

			## KEEP REALITY CHECK; THE COSTS MAY HAVE CHANGE ALREADY
			## BEFORE FINDING "BEST ROUTE", WE NEED TO KNOW HOW WE ARE REALLY DOING

			try:			
				if DEBUG:
					print "^^^^^^^^^^^^^^ TRYING INITIAL CLEANUP"
					print "dv[me][dest]" + str(dv[me][dest])
					print "dv[cost[0]]" + str(dv[cost[0]])
					print "dv[cost[0]][dest] " + str(dv[cost[0]][me][1])
				dv[me][dest][1] = dv[cost[0]][me][1] + dv[cost[0]][dest][1]
			except:
				pass
			oldcost = dv[me][dest][1]
			min_cost= MAX_COST
			## dv[me][dest] = (link, cost)
			for neighbor, links in dv.iteritems():

				if uplink[neighbor] and neighbor != me:
					if DEBUG:
						print "-neighbor is not me, neighbor = " + str(neighbor)
						print "-me: " + str(me)
					
					try:
						neighbor_to_dest = dv[neighbor][dest][1]

					except:
						
						neighbor_to_dest = MAX_COST
					
					if DEBUG:
						print "-dv[me] = " + str(dv[me])
						print "-dv[me][neighbor] = " + str(dv[me][neighbor])
						print "-dv[me][neighbor][1] = " + str(dv[me][neighbor][1])
						print "-dv[neighbor][dest][1] = " + str(neighbor_to_dest)
						print "-oldcost = " + str(oldcost)

					## DONT leT IT TO EASY! UPDATE THE OLD PATH FIRST!!

					if neighbor != dest:
						me_to_neighbor = dv[me][neighbor][1]
					else:
						me_to_neighbor = costs[neighbor]
					
					if me_to_neighbor + neighbor_to_dest < min_cost:
						if DEBUG:
							print "-route discovered, dv[%s][%s] + dv[%s][%s] = %s" % (me, neighbor, neighbor, dest, dv[me][neighbor][1]+ neighbor_to_dest)
						min_cost = me_to_neighbor + neighbor_to_dest
						path = neighbor

			if oldcost != min_cost:
				if DEBUG:
					print "====New route superior; CHANGE RECORDED"
					print "====oldcost = " + str(oldcost)
					print "====min_cost = " +str(min_cost)
					print "====destination = " + str(dest)
					print "====via path" + str(path)
				
				changed = 1
				dv[me][dest] = [path, min_cost]
				##costs[dest] = min_cost

			if DEBUG:
				print "===================================================="
	return changed

def linkdown(client_input):  ## also used for timeout event
	

	client = client_input
	if client[0] == 'localhost' or client[0] == '127.0.0.1':
		client = (my_addr, client_input[1])

	uplink[client] = 0
	
	costs[client] = dv[me][client][1]
	
	dv[me][client] = [("DOWN", 0), MAX_COST]
	dv[client][me] = [("DOWN", 0), MAX_COST]
	

	## first, the dv is dead to me
	## any current path that relies on the path must be labeled down as well
	if DEBUG2:
		print dv[me]

	for dest, path in dv[me].iteritems():
		if DEBUG:
			print "****killing intermediary... dest = " + str(dest)
			print "path[1] = " + str(path[1])
		if path[1] == client:
			if DEBUG:
				print "this path needs to be recalculated..."
			dv[me][dest] = [("ALSO DOWN", 0), MAX_COST]

	update_dv()

	kill_link(client)
	
	broadcast()

def linkup(client_input):
	
	client = client_input
	
	if client[0] == 'localhost' or client[0] == '127.0.0.1':
		client = (my_addr, client_input[1])
	
	uplink[client] = 1
	dv[me][client] = [client, costs[client]]

	update_dv()
	broadcast()


def handle_incoming_message(packet):


	sender = packet[1]
	if packet[0] == 'DOWN':
		costs[sender] = dv[me][sender][1]
		dv[me][sender][1] = MAX_COST
		dv[sender][me][1] = MAX_COST
		uplink[sender] = 0
		update_dv()
		broadcast()
	
	else: 
		
		changed = 0
		new_dv = pickle.loads(packet[0])
		last_contact[sender] = time()

		if sender not in dv.keys():## we dont know this dude, but it connected directly! gotta update costs
			add_neighbor_new(sender, new_dv)
			uplink[sender] = 1

			for dest, path in dv[sender].iteritems():
				if dest not in dv[me].keys():
					dv[me][dest] = [("UNKNOWN", 0), MAX_COST]

			costs[sender] = dv[sender][me][1] ## original cost
			dv[me][sender] = [sender,  costs[sender]]

			## make sure we have a (fresher) start

			if update_dv():
				broadcast()

		else:## we know this dude... reuse old cost, you say?
			dv[sender] = new_dv
			for dest, path in dv[sender].iteritems():
				if dest not in dv[me].keys():
					dv[me][dest] = [("UNKNOWN", 0), MAX_COST]
			
			if not uplink[sender]: ## did you just come back alive? if so, restore initial connection
				dv[me][sender] = [sender, costs[sender]]

			uplink[sender] = 1

			if update_dv():
				broadcast()

	
	## IF sender is not in neighbors, use add_neighbor_new()
	## then update cost

		if changed:
			broadcast()


def handle_keyboard_message(message):
	arg = message.split()

	if arg[0].upper() == 'SHOWRT':
		showroute()
	elif arg[0].upper() == 'LINKDOWN':
		linkdown((arg[1], int(arg[2])))
	elif arg[0].upper() == 'LINKUP':
		linkup((arg[1], int(arg[2])))
	elif arg[0].upper() == 'BROADCAST':
		broadcast()
	else:
		print "Syntax error"
		pass

def client_parser(argv):

	global me;

	length = len(argv)
	
	if length%3:
		print "Syntax error - length of argv is not divisible by 3"
		return 0

	i = 0;

	while i < length-2: ## i = 0, length = 6, length-2 = 4, i = i+3
		if argv[i] == 'localhost' or argv[i] == '127.0.0.1':
			addr = socket.gethostbyname(socket.gethostname())
			'''IMPORTANT
			ANYTHING LOCAL (127.0.0.1, localhost) is converted to actual IP address to ensure consistency
			'''
		else:
			addr = argv[i]
		add_neighbor_initial((addr, int(argv[i+1])), argv[i+2])
		i = i+3

	return 1

if __name__ == "__main__":



	my_port = int(sys.argv[1])
	my_timeout = int(sys.argv[2])

	sock.bind(("", my_port))

	me = (my_addr, my_port)
	
	dv[me] = {}
	dv[me][me] = [(my_addr, my_port), 0]
	uplink[me] = 1
	
	if DEBUG:
		print "my port = %d, my timeout = %d, my address = %s" % (my_port, my_timeout, my_addr)

	if client_parser(sys.argv[3:]) != 1:
		print "Syntax error. Format = localport timeout [ipaddress1 port1 weight1 ...]"

	broadcast()
	last_broadcast = time()

	while True:

		pipe_list = [sys.stdin, sock]
		readable = select.select(pipe_list, [], [], 0)[0]
		if not readable:
			for neighbor, vector in dv.iteritems():

				if uplink[neighbor] and neighbor is not me:
					if time()- last_contact[neighbor] > my_timeout*3:
						if DEBUG:
							"#######" + str(neighbor) + "has timed out."
						linkdown(neighbor)
			
			if time() - last_broadcast > my_timeout:
				
				if DEBUG:
					print "I am starting to broadcast to the neighbors..."
				broadcast()
				last_broadcast = time() ## because currently braodcast() does not update properly

		else:
			for a_socket in readable:
				if a_socket == sock:
					if DEBUG:
						print "see what the packet is... could be nothing"
					handle_incoming_message(a_socket.recvfrom(BUFFER_SIZE))
				elif a_socket == sys.stdin:
					message = sys.stdin.readline()
					handle_keyboard_message(message)
				else:
					print "DONT KNOW WHY IM HERE"
					pass

			



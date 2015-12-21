README.txt
zg2171

For Networks PA3

Usage: 

python bfclient.py [your port] [your timeout] [[neighbor 1 address] [neighbor 1 port] [neighbor 1 cost] [neighbor 2 address] ...]

See PA3 assignemnt instructions.

Example:
You can run each of these commands in a different terminal window on the same machine to emulate a network topology.

python bfclient.py 8181 20 127.0.0.1 8182 1 127.0.0.1 8183 3 127.0.0.1 8184 2
python bfclient.py 8182 20 127.0.0.1 8181 1 127.0.0.1 8183 3
python bfclient.py 8183 20 127.0.0.1 8181 3 127.0.0.1 8185 5 127.0.0.1 8184 1
python bfclient.py 8184 20 127.0.0.1 8181 2 127.0.0.1 8183 1 127.0.0.1 8185 2
python bfclient.py 8185 20 127.0.0.1 8184 2 127.0.0.1 8183 5


The topology can be visualized below: (node n corresponds to port 818n)

		  1
1 -------------------- 2
| \                    |
|   \                  |
|     \                |
|       \              |
|		  \	3		   |
|2		    \          | 3
|		      \        |
|		        \      |
|		          \    |
|		            \  |
|		   1          \|
4----------------------3
 \                    /
  \                  /
   \                /
    \              /
   2 \            / 5
      \          /
            . 
            . 
            . 
            \/
            5



*** regarding the significance of 127.0.0.1, see NOTE 1 below for clarifications

LINKUP and LINKDOWN are supported based on the syntax in PA3 instructions

ROUTE_UPDATE protocol/format is very simple. It is a pickled dictionary with destination as a key, and (path, cost) as the value for each reachable node at my client.

When my client closes a connecction via LINKDOWN, in addition to updating my DV, the client will send to the relevant neighbor a packet with string 'DOWN' as the only payload. That way, the affected client will also know the link is down before the timeout hits, in which case it will voluntarily mark the link as down anyway.



*******************IMPORTANT NOTES******************************
0. For VERBOSE output, set DEBUG = 1 on line 9.

1. In order to distinguish local connections and network connections, this program uses a handler for the result of socket.gethostbyname(socket.gethostname()). See below code on line 29 of bfclient.py:

my_addr = socket.gethostbyname(socket.gethostname())

if my_addr[:3] == '127':
	my_addr = '127.0.0.1'

If socket.gethostbyname(socket.gethostname()) returns either 127.0.0.1 or 127.0.1.1 (the latter is possible if if gethostname() returns the machine name, as opposed to 'localhost'), the address will be converted to 127.0.0.1 for consistency. In most other cases, such as on CLIC, socket.gethostbyname(socket.gethostname()) should return the actual IP address of the machine, which will not be a problem for this particular implementation.

For the purpose of testing on a single machine, 127.0.0.1 may still be used to denote the neighbor's address in the input argument, but anything starting with '127' will be replaced with my_addr, which may either be the network address of this computer, or a consistent '127.0.0.1'.

2. POISONED INVERSE is implemented. To see the original ROUTE_UPDATE and the new ROUTE_UPDATE, set DEBUG = 1 in the beginning of the code. You can see that for broadcast to each given neighbor, if that neighbor is used as a hope to my particular destination, then my client will tell the heighbor that my cost to the destination is MAX_COST, which is currently set to MAX_COST. This can avoid some cases of count to infinity problem, but not all. When more than two nodes are in a loop, it's possible that they bite on each other's tail (A via B, B via C, C via A, etc). This may be mitigated by storing multiple hops, opposed to one, for each destination.

3. LINKDOWN and LINKUP - With LINKDOWN, an updated DV with MAX_COST to the neighbor is given out.  With LINKUP or LINKDOWN is summoned at my client, broadcast() is summoned 5 times, with a 0.2 second of pause in between them. This is to give each neighbor enough time to update their respective DVs to clear out any erroneous values, before my client starts taking in any new DVs. THEREFORE, there may be a slight lag of 1 second after each LINKUP command is given.



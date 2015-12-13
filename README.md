Current progress:

 - Normal topology works (every route specified)
 
 
 does not work properly:
 - linkdown: how does one node that kills the link notify the node on the other end, without poison reverse? Does it have to wait for a timeout, and then trigger count to infinity?
 - adding new, un-preloaded nodes to the network (new path, new cost
 



# bellman-ford

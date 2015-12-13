Current progress:

 - Normal topology works (every route specified)
 - New neighbors not specified in initial command line
 
 does not work properly:
 - linkdown: how does one node that kills the link notify the node on the other end, without poison reverse? Does it have to wait for a timeout, and then trigger count to infinity?
 

Need to implement catching keyboard interrupt 

# bellman-ford

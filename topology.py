#! usr/bin/env python

"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo
from	mininet.net 	import	Mininet			
from	mininet.log	 import	setLogLevel
from mininet.link import TCLink
#from mininet.node import OVSSwitch, RemoteController, OpenFlow14


class ICNSDNTopology(Topo):
    "Simple topology example."

    def __init__(self):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        H = [1, 2, 3,4,6,8]
        S = [1, 2, 3,4,5,6,7,8,9]
        P = [44,66,88]
        #S = xrange(1, 10)
        switches = {'s%i' % i: self.addSwitch('s%i' % i) for i in S}
        hosts = {'h%i' % i: self.addHost('h%i' % i) for i in H}
        publishers = {'h%i' % i: self.addHost('h%i' % i) for i in P}
        
        # Merge switches and hosts
        nodes = {}
        nodes.update(switches)
        nodes.update(hosts)
        nodes.update(publishers)
        # Add a host service for each switch
        host_services = {'sh%i' % i: self.addHost('sh%i' % i) for i in H}
        #nodes.update(host_services)
        links = [('s1','s2'), ('s2','s3'),('s3', 's4'), ('s4', 's5'), ('s3', 's5'),('s6','s7'),
                 ('s7','s8'), ('s1','s8'),('s8','s9'),('s9','s5'),('s3','s9'),('s2','s8'),
                  ('h2','s2'),('h1','s1'),('h4','s4'),('h6','s6'),('h8','s8'),('h3','s3'),
                    ('h44','s4'),('h66','s6'),('h88','s8')] # ('s5', 's6'),
      

        for link in links:
            self.addLink(nodes[link[0]], nodes[link[1]],bw=100, delay='10ms')
        # Add link between each switch and its corresponding service host
        for i in H:
            self.addLink(nodes['s%i' % i], host_services['sh%i' % i], 100,100,bw=100,delay='1ms')
            self.addLink(nodes['s%i' % i], host_services['sh%i' % i], 101,101,bw=100,delay='1ms')
            
        #self.publishers = {'sh4','sh6'}    
        
topos = {'mytopo': (lambda: ICNSDNTopology())}
            
#def	runExperiment(hosts,publishers):			
#    "Create	and	test	a	simple	experiment"			
#    topo_icn	=	ICNSDNTopology()			
#    net	=	Mininet(switch=OVSSwitch(protocols=OpenFlow14), topo=topo_icn) 
##                      link=TCLink('tc,bw=1,delay=10ms'))
#    
#    net.addController('VICN.py', controller=RemoteController, ip='127.0.0.1', port=9999)
#    net.start()			
# 
##    print	"Dumping	host	connections"			
##    dumpNodeConnections(net.hosts)			
#    print	"Running the experiment"			
#    for h in net.hosts: 
#        id = str(h)[len(str(h))-1]
#        if int(id) in publishers:
#            h.cmd('python3 ServiceHost.py repo -p repo -i '+id)
#        else:
#            h.cmd('python3 ServiceHost.py -i '+id)
#            h.cmd('python3 producer.py -p content_files -r files'+id)
#            
##    for h in net.hosts:
##        h.cmd('python3 consumer.py -i '+str(h))
#        
##    net.stop()	
# 
#if	__name__	==	'__main__':			
#    #	Tell	mininet	to	print	useful	information			
#    setLogLevel('info')			
#    runExperiment([1,2,3,8],[4,6])	



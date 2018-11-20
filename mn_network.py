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
from optparse import OptionParser
#from subprocess import call
from mininet.node import OVSSwitch, OVSKernelSwitch, RemoteController
import time
from mininet.cli import CLI
import commands
import threading


class TaskThread(threading.Thread):
    """Thread that executes a task every N seconds"""
    
    def __init__(self, interval, task):
        threading.Thread.__init__(self)
        self._finished = threading.Event()
        self._interval = interval
        self.task = task
    
    def setInterval(self, interval):
        """Set the number of seconds we sleep between executing our task"""
        self._interval = interval
    
    def shutdown(self):
        """Stop this thread"""
        self._finished.set()
    
    def run(self):
        while 1:
            if self._finished.isSet(): return
            self.task()
            
            # sleep for interval or until shutdown
            self._finished.wait(self._interval)
   
    
class ICNSDNTopology(Topo):
    "Simple topology example."
    
        
    def __init__(self, d_s, d_sh):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        H = [1, 2, 3,4,6,8]           #hosts 
        S = [1, 2, 3,4,5,6,7,8,9]     #switches
        P = [44,66,88]                #publishers
        
        switches = {'s%i' % i: self.addSwitch(name='s%i' % i, cls=OVSKernelSwitch, protocols='OpenFlow14') for i in S}
                        
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
            self.addLink(nodes[link[0]], nodes[link[1]], delay=d_s)
#            self.addLink(nodes[link[1]], nodes[link[0]], delay=d_s)
            
        # Add link between each switch and its corresponding service host
        for i in H:
            self.addLink(nodes['s%i' % i], host_services['sh%i' % i], 100,100,delay=d_sh)
            self.addLink(nodes['s%i' % i], host_services['sh%i' % i], 101,101,delay=d_sh)
        
        
            
   
#topos = {'mytopo': ICNSDNTopology}
    
#the function for checking if the experimnet is finished or not
def is_finished_exp(consumers, finished_num, out_path):
    finished = True
    new_num = dict()
    for h in consumers:
        #check if it is a long time that no new download is finished 
        new_num[h] = commands.getstatusoutput('wc -l < '+ out_path + 'down_time_'+h[1:]+'_e' )
        if finished_num[h]!=new_num[h]:
            finished = False
  
    return finished, new_num
    

#the function for executing an experiment with the custom topology        
def	runExperiment(switches, publishers, consumers, protocol, delay_sw, delay_sh, smpl):			
    "Create	and	test	a	simple	experiment"		
#    mn --custom topology.py --topo mytopo,$delay_sw,$delay_sh  --controller=remote,port=9999 --switch=ovsk,protocols=OpenFlow14 --mac --arp --link=tc --post experiment_icn
#    switch=OVSSwitch(protocols='OpenFlow14')
    
    icsdn_topo	=	ICNSDNTopology(delay_sw, delay_sh)	
    icsdn_controller = RemoteController(name='NDSDN',ip='127.0.0.1', port=9999)
    net	=	Mininet(controller=icsdn_controller, topo=icsdn_topo, autoStaticArp=True, autoSetMacs = True, link=TCLink)
    
    
    net.start()			
    time.sleep(50)  
    exp = 'ds' + delay_sw + '_dsh' + delay_sh    
    if protocol=='icn':
        out_path = './Out/icn/'+exp+'/'+smpl+'/'
               
       #execute all service hosts connected to the switches
        for s in switches:
            s_num = s[2:]
            time.sleep(2)
            net.get(s).cmd('python3 ServiceHost.py -i '+s_num+' -p icn -e '+exp+' -s '+smpl+' > ' + out_path + 'SH_'+s_num+'.log &')
        
        #execute all the publishers. For each publisher a Service host and a producer are required to register the contents
        for p in publishers:
            p_num = p[1:]
            time.sleep(2)
            net.get(p).cmd('python3 ServiceHost.py repo -r repo -i '+p_num + ' -p icn -e '+ exp + ' -s '+ smpl+
                                ' > ' + out_path + 'SH_repo_'+p_num+'.log &')
            time.sleep(2)
            net.get(p).cmd('python3 producer.py -c content_files -r files'+p_num+'   > ' + out_path + 'producer_'+p_num+'.log &')
            
        #execute all the consumers    
#        time.sleep(30)
#        for h in consumers:
#            h_num = h[1:]
#            time.sleep(2)
#            net.get(h).cmd('python3 consumer.py -i '+h_num+' -p icn -e '+exp+' -s '+smpl+' > ' + out_path + 'consumer_'+h_num+'.log &')
        net.startTerms()
    else:
       
#       in the case of traditional IP routing (without ICN switches) no Service host is required.
        time.sleep(2)
        out_path = './Out/noicn/'+exp+'/'+smpl+'/'   
        for p in publishers:
            p_num = p[1:]
            time.sleep(2)
            net.get(p).cmd('python3 ServiceHost.py repo -r repo -i '+p_num + ' -p noicn -e '+ exp + ' -s '+ smpl+
                                ' > ' + out_path + 'SH_repo_'+p_num+'.log &')
            time.sleep(2)
            net.get(p).cmd('python3 producer.py -c content_files -r files'+p_num+'   > ' + out_path + 'producer_'+p_num+'.log &')
            
        time.sleep(60)
        for h in consumers:
            h_num = h[1:]
            net.get(h).cmd('python3 consumer.py -i '+h_num+' -p noicn -e '+exp+' -s '+smpl+' > ' + out_path + 'consumer_'+h_num+'.log &')
           

   # CLI(net)
    finished_num = dict()
    for c in consumers:
        finished_num[c] = 0
    e = threading.Event()
    while(True):
        e.wait(300)
        finished, finished_num = is_finished_exp(consumers,finished_num,out_path)
        if finished:
            net.stop()
            commands.getstatusoutput('killall ryu-manager')
            commands.getstatusoutput('killall python3')
            exit(0)
  
if	__name__	==	'__main__':		
    
    parser = OptionParser()
    parser.add_option("-d", "--delay_sw", dest="delay_sw",
                      help="delay between the switches")
    parser.add_option("-e", "--delay_sh", dest="delay_sh",
                      help="delay between a switche and its service host")
    parser.add_option("-p", "--protocol", dest="protocol",
                      help="protocol (icn/noicn)")
    parser.add_option("-s", "--sample", dest="smpl",
                      help="sample name")
                      
    (options, args) = parser.parse_args()
    #	Tell	mininet	to	print	useful	information			
    setLogLevel('info')	
    
    #specify the active nodes in the experiment and run the experiment
    switches = [ 'sh2', 'sh3', 'sh4']#[ 'sh1', 'sh2', 'sh3', 'sh4', 'sh6', 'sh8']#
    publishers = ['h66']
    consumers = ['h2','h1']
    
    runExperiment(switches, publishers, consumers, options.protocol, options.delay_sw, options.delay_sh, options.smpl)	



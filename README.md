# NDSDN
Implementing NDN using SDN

The required steps for executing a sample experiment are described at the following.

1- execute controller (the customized module is written in VICN.py)
   -sudo ryu-manager --ofp-tcp-listen-port 9999 VICN.py  ryu.app.ofctl_rest --observe-links

2- execute mininet    (the customized topology is determind in VICN.py)
   -sudo mn --custom topology.py --controller=remote,port=9999 --switch=ovsk,protocols=OpenFlow14 --topo mytopo --mac --arp --link=tc,bw=1,delay=10ms

3- execute the experiment from the mininet terminal (experiment is the commands for executing codes on variouse terminals)
   -source experiment

	(at the controller terminal, we can see logs about the net topology and executed codes, then comming packets to each switch or the registration commands)
    (contenets are in <content_files> folder. producer.py use them)
	
4- logs from the experiment are recorded in the files in <Out> folder
   -using draw.py, you can see the diagrams

5- to see the tables or flow tables in the switches execute:
   -sudo ovs-ofctl -O OpenFlow14  dump-tables s1
   -sudo ovs-ofctl -O OpenFlow14  dump-flows s1

6- to see the network in mininet execute below commands in mininet terminal:
   -net
   -nodes
   -dump

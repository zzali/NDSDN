sudo ryu-manager --ofp-tcp-listen-port 9999   --observe-links VICN.py > VICN_out &
sudo mn --custom $1.py --controller=remote,port=9999 --switch=ovsk,protocols=OpenFlow14 --topo mytopo --mac --arp  

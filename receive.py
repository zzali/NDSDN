from scapy.all import sniff
import re
from os import system
#from scapy.contrib.mpls import MPLS
from scapy.layers.inet import IP 
def service_packet(packet):
        """
        handle an input packet in service host
        :param packet: the packet that service host has recieved
        :return: None
        """
        
        if packet.haslayer(IP):
            proto = packet[IP].proto
            if proto == 150:
                print ('Interest packet ')
                
            elif proto == 151:
                print ('Data packet ')
                packet.show()
            else:
                print ('Not NDN packet')
                
if __name__ == '__main__':
    f = system('ifconfig > ifconfig')
    f = open('ifconfig', 'r').read()
    mac_regex = re.compile("(?:[0-9a-fA-F]:?){12}")
    eth_src = mac_regex.findall(f)[0]

    sniff(prn=lambda x: service_packet(x))#, lfilter=lambda x: eth_src in x.summary())
    # sniff(prn=lambda x: str(x)+'\n-------------\n')

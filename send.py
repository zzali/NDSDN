from scapy.layers.inet import Ether, IP
from scapy.contrib.mpls import MPLS
from scapy.all import sendp
import re
import os
from optparse import OptionParser
import hashlib
import pyndn as ndn


INTEREST_LIFETIME = 5000 #ms

def encode_in_2bytes(field):
    print(type(field))
    field_len=len(field)
    data = bytearray()
    data.append(field_len)
    data = data + bytearray(field, 'utf8')
    print("encodeing: ", data)
    return data
#Int packet: {content_name_len(2bytes)+content_name+chunk_numlen(2bytes)+chunk_num}
def send_packet(et_src, et_dst, content_name, chunk_num, ip_src, 
                 ip_proto=150, mpls_ttl=10):
    
    ether = Ether(src=et_src, dst=et_dst)
    
    label = hashlib.sha256()
    label.update(content_name.encode())
    name_bytes = label.digest()
    mpls_label = name_bytes[0]*4096 + name_bytes[1]*16 + (name_bytes[2]>>4)#first 20 bits 
    mpls = MPLS(label=mpls_label, ttl=mpls_ttl)
    
#    name = ndn.Name(ndn.Name.Component(content_name))
#    name.appendSegment(chunk_num)
#    interest = ndn.Interest(name)
#    interest.setInterestLifetimeMilliseconds(INTEREST_LIFETIME)
#    data=interest.wireEncode().buf().tobytes()
    
    #creating Interest packet
    data=encode_in_2bytes(content_name)
    data = data + encode_in_2bytes(str(chunk_num))
    ip = IP(src=ip_src, proto=ip_proto)  
    packet = ether / mpls / ip / data.decode()

    packet.show()
    sendp(packet)
    
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-l", "--label", dest="name",
                      help="Name label")
    parser.add_option("-i", "--ip", dest="src_ip",
                      help="source ip")
    parser.add_option("-e", "--eth", dest="src_eth",
                      help="source ethernet")
                      
    parser.add_option("-d", "--destination", dest="eth_dst",
                      help="Ethernet destination addr")
                      
    parser.add_option("-p", "--protocol", dest="protocol",
                      help="NDN protocol number")
    
    (options, args) = parser.parse_args()
   
    
    f = os.system('ifconfig > ifconfig')
    f = open('ifconfig', 'r+').read()
    # f = open('/proc/net/arp', 'r').read()sc
    mac_regex = re.compile("(?:[0-9a-fA-F]:?){12}")
    eth_src = mac_regex.findall(f)[0]
    os.system('hostname -I > hostname')
    ip_src = open('hostname', 'r+').read().strip()
    
    ip_src = (options.src_ip) if options.src_ip else ip_src
    print (ip_src)
    eth_src = (options.src_eth) if options.src_eth else eth_src
    print (eth_src)
    eth_dst = (options.eth_dst) if options.eth_dst else 'ff:ff:ff:ff:ff:ff'
    ip_proto = int(options.protocol) if options.protocol else 150
            
    send_packet(eth_src, eth_dst, options.name, 1, ip_src, ip_proto)


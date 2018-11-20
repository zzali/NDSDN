# -*- coding: utf-8 -*-
"""
Created on Sun Jun  4 11:23:45 2017

@author: root
"""

from scapy.layers.inet import Ether,IP 
from scapy.all import *
import threading
import socket
from threading import Thread
from optparse import OptionParser
import hashlib
#import pyndn as ndn
import netifaces

ETH_TYPE_IP = 0x0800

def encode_ip(content_name, chunk_num):
    '''
    inputs
    ------
    content_name: str as the name of the content
    chunk_num: chunk number between 0 and 255
    
    output
    ------
    ip: corresponding ip address
    '''
    label = hashlib.sha256()
    label.update(content_name.encode())
    binary_ip = format(int(label.hexdigest()[:6], 16), 'b')
    #print(binary_ip)
    diff = '0'*(24- len(binary_ip))
    binary_ip = diff + binary_ip
    #print(binary_ip)        
    binary_ip += format(chunk_num, 'b')
    #print(binary_ip)
    ip = ''
    for i in range(4):
        ip += str(int(binary_ip[i*8: (i+1)*8], 2))
        if i < 3:
            ip += '.'
    #print ip
    return ip

def decode_ip(ip):
    '''
    input
    -----
    ip: customized ip address with first 24bits of content name and 8 last bits for the chunk num

    output
    ------
    content_name: a number as the hashed content name
    chunk_num: number of the chunk between 0 and 255
    '''
    binary_number = ''
    for i in ip.split('.'):
        n = format(int(i), 'b')
        binary_number += '0' * (8-len(n)) + n
    content_name = int(binary_number[:24], 2)
    chunk_num = int(binary_number[24:], 2)
    return content_name, chunk_num

INT_PROTO = 150
DATA_PROTO = 152
REG_PROTO = 153

class CS(object):
    def __init__(self, s_id, repo_path=None, chunk_size=None,eth_src=None):
     
        self.MAX_STORAGE_SIZE = 5000
        self.logfile=open('./Out/cache_log_'+s_id,'w')
        self.hit_num = 0
        if repo_path is not None:
            self.chunk_size = chunk_size
            self.repo_path = repo_path
            self.eth_src = eth_src
        else:
            self.repo_path = None
        self.storage = defaultdict(str)             #represents content store: {'content_name''chunk_num':data_chunk}
        self.storage_free = self.MAX_STORAGE_SIZE   #size of free storage in cache
        #self.storage = list()                      #each element of this list is a chunk of a data
        self.lru = defaultdict(int)                 #tm value for each content key
        self.tm = 0
       
    
    def create_packet(self,data, content_id, et_src, ip_proto=DATA_PROTO):
        #print('begin creating packet, et_src:'+str(et_src)+', ip_src: '+str(ip_src))
        ether = Ether(src=et_src)#, dst=et_dst)
        ip = IP(src=content_id, dst='127.0.0.1',proto=ip_proto, ttl=0, tos = 0)  
        packet = ether / ip / data
        #packet.show()
        return packet
    
    def lookup(self,content_name,content_id):
        """
        look up a content in cache
        :param content_name: tag name of the content
        :param chunk_num: chunk number of the requested content
        :return: if hit in repository return correspondent data 
                 else return None 
        """
        #print('content_id', content_id)         
        if content_id in self.storage and self.storage[content_id]!=None:
            self.hit_num += 1
            self.lru[content_id] = self.tm
            self.tm += 1
            #print("Hit in cache for ", self.hit_num)# , ' times', file=self.logfile)
            return self.storage[content_id]
        if self.repo_path is None:
            return None
        content_name, chunk_num = decode_ip(content_id)
        content_name_str = str(content_name)
        #print("requested content label: ",content_name_str, chunk_num)
        file_path = self.repo_path+'/'+ content_name_str
        if os.path.exists(file_path):
            #print('content is available in the repo')
            f = open(file_path, 'r')
            chunk = f.read(self.chunk_size)
            ch_num = 1
            while chunk:   
                c_id = content_id[:content_id.rfind('.')] + '.' + str(int(format(ch_num, 'b'), 2))
                data_packet = self.create_packet(chunk, c_id, self.eth_src)
                #data_packet.show()
                self.add(c_id,data_packet)
                #print('c_id',c_id)
                ch_num = ch_num + 1
                chunk = f.read(self.chunk_size)
            #print (self.storage[content_id])
            return self.storage[content_id]
        return None
    
    def add(self,content_id,data):
        """
        add a chunk of a content to the cache
        :param content_name: tag name of the content
        :param chunk_num: chunk number of the requested content
        :param data: data to be cached
        :return: None
        """
        if self.storage_free<=0:
            #print('Replacement in cache',file=self.logfile)                   #replace with LRU cache replacement policy 
            old_key = min(self.lru.keys(), key=lambda k:self.lru[k])
            self.storage.pop(old_key)
            self.lru.pop(old_key)
            replaced_id = old_key
        else:
            replaced_id = None
        self.storage.update({content_id:data})
        self.lru.update({content_id: self.tm})
        self.tm += 1
        self.storage_free -= 1
        return replaced_id
        #print('data have been added to the cache: ', key)
        
    
class cache_service(object):
    def __init__(self, switch_id, repo_path=None):
        
        self.CONTROLLER_ETH = '1c:6f:65:ca:15:df'
        self.CONTROLLER_IP = ''
        self.REPO_PORT = 5000
        self.REPO_PATH = repo_path
        self.CHUNK_SIZE = 1000
        self.MPLS_TTL = 10
        self.INT_PROTO = 150
        self.DATA_PROTO = 152
        self.REG_PROTO = 153
        self.CACHE_IN_PORT = 100
        self.CACHE_OUT_PORT = 101
        self.SWITCH_PORTNUM = 3
        self.rx = 0    #number of recieved packets
        self.tx = 0    #number of transfered packets 
        self.sniffed_num = 0
        self.skip_next_packet=False
        self.CACHE_IN_FACE = str()
        self.CACHE_IN_IP = str()
        self.CACHE_IN_ETH = str()
        self.CACHE_OUT_FACE = str()
        #self.SH_OUT_IP = str()
        self.CACHE_OUT_ETH = str()
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if iface.endswith('100'):
                self.CACHE_IN_FACE = iface
                self.CACHE_IN_IP = addrs[netifaces.AF_INET][0]['addr']
                self.CACHE_IN_ETH = addrs[netifaces.AF_LINK][0]['addr']
                print("IN port:",self.CACHE_IN_FACE, self.CACHE_IN_IP, self.CACHE_IN_ETH)
            elif iface.endswith('101'):
                self.CACHE_OUT_FACE = iface
                #self.SH_OUT_IP = addrs[netifaces.AF_INET][0]['addr']
                self.CACHE_OUT_ETH = addrs[netifaces.AF_LINK][0]['addr']
                print("OUT port:",self.CACHE_OUT_FACE,  self.CACHE_OUT_ETH)
            elif iface.endswith('eth0'):
                self.CACHE_OUT_FACE = self.CACHE_IN_FACE = iface
                self.CACHE_IN_IP = addrs[netifaces.AF_INET][0]['addr']
                self.CACHE_IN_ETH = self.CACHE_OUT_ETH = addrs[netifaces.AF_LINK][0]['addr']
                print("IN port:",self.CACHE_IN_FACE, self.CACHE_IN_IP, self.CACHE_IN_ETH)
                
        if repo_path is None:
            self.cache = CS(switch_id, chunk_size=self.CHUNK_SIZE)
            self.switch= True
        else:
            self.cache = CS(switch_id, repo_path,self.CHUNK_SIZE, self.CACHE_IN_ETH)
            self.switch = False
        self.s_dpid = switch_id
        self.rest_add=[]
        self.rest_remove=[]
        os.system('sudo ovs-vsctl -- set bridge s'+str(self.s_dpid)+' protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13,OpenFlow14')
                
    def decode_packet(self, packet):
        """
        decode a ndn packet and extract its required fields
        :param packet_ndn: the ndn packet (data or interest + IP header)
        :return: {'content_name':ndn content name, 'proto':the protocol of next layer after IP,
                  'chunk_num':data or requested data chunk num, 
                  'src_ip':source IP address,'dst_ip':dsttination IP address}
        """
        #packet.show()
        fields = dict()
        fields['proto'] = packet[IP].proto
        fields['in_port'] = packet[IP].tos
        if fields['proto'] == -1:
            return fields
        content_name, chunk_num = decode_ip(packet[IP].src)
        fields.update({'content_id':packet[IP].src})
        fields.update({'content_name':content_name})
        fields.update({'chunk_num':chunk_num})
        fields.update({'flow_id':packet[IP].dst})
        if fields['proto']==self.DATA_PROTO:
            fields.update({'data':packet[IP].load})       
        else:
            fields.update({'data':''})       
        return fields
    
    def service_interest(self, int_packet, int_pac_fields, eth_src, eth_dst):
        """
        handle an interest packet
        :param int_packet: interest packet to be handled 
        :return: None
        """   
        #chunk_num = int_pac_fields['chunk_num']
        content_name = int_pac_fields['content_name']
        #if chunk_num==1:
            #print('int time for content_name ', content_name, ':', time.time())
        data = self.cache.lookup(content_name, int_pac_fields['content_id'])
        if data is not None and len(data)>0:
            #print('data time for', chunk_num,':',time.time())
            #send data
            #print('data:',data)
            data[IP].tos = int_pac_fields['in_port']
            data[IP].ttl = 1
            data[IP].dst = int_pac_fields['flow_id']
            #print('data is returned from cache')
            sendp(data,iface=self.CACHE_OUT_FACE)
        
    def send_update_cs_rest(self):
        while True:
            for c in range(len(self.rest_remove)):
                #print('delete flow for content ', c, 'in ', self.s_dpid)
                content_id = self.rest_remove.pop()
                for port in range(self.SWITCH_PORTNUM):
                    #time.sleep(10)
                    cmd = 'ovs-ofctl del-flow s'+str(self.s_dpid)+' table=1,in_port='+str(port)+',dl_type='+str(ETH_TYPE_IP)+',nw_proto='+str(self.INT_PROTO)+',nw_src='+content_id+',actions='+'mod_nw_tos:'+str(port*4)+',output:'+str(self.CACHE_IN_PORT)
                    os.system(cmd)
            
                
            for c in range(len(self.rest_add)):
                #send interest to cache if matched in CS, in_port is keeped in ToS field 
                #in order to enabling content forwarding back from the Cache. 
                #print('add flow for content ', c, 'in ', self.s_dpid)
                content_id = self.rest_add.pop()
                for port in range(self.SWITCH_PORTNUM):
                    #time.sleep(10)
                    cmd = 'ovs-ofctl add-flow s'+str(self.s_dpid)+' table=1,in_port='+str(port)+',dl_type='+str(ETH_TYPE_IP)+',nw_proto='+str(self.INT_PROTO)+',nw_src='+content_id+',actions='+'mod_nw_tos:'+str(port*4)+',output:'+str(self.CACHE_IN_PORT)
                    os.system(cmd)
        
    def service_data(self,data_packet, data_pac_fields, eth_src, eth_dst):
        """
        handle an data packet
        :param data_packet: data packet to be handled
        :return: None
        """  
        replaced_content = self.cache.add(data_pac_fields['content_id'],data_packet)
        self.rest_add.append(data_pac_fields['content_id'])
        if replaced_content is not None:
            self.rest_remove.append(replaced_content)
            
   
    def service_packet_thread(self, packet):
        self.sniffed_num = self.sniffed_num + 1
        eth_src = packet[Ether].src
        eth_dst = packet[Ether].dst
        ndn_pack_fields = self.decode_packet(packet)
        if ndn_pack_fields['proto'] == self.INT_PROTO:
            #print('int time for', ndn_pack_fields['chunk_num'],':',time.time())
            self.service_interest(packet, ndn_pack_fields, eth_src,eth_dst)
        elif ndn_pack_fields['proto'] == self.DATA_PROTO and self.switch:
            #print('data time for', ndn_pack_fields['chunk_num'],':',time.time())
            self.service_data(packet, ndn_pack_fields, eth_src,eth_dst)
            
    def service_packet(self,packet):
        """
        handle an input packet in service host
        :param packet: the packet that service host has recieved
        :return: None
        """
        if packet.haslayer(IP):
            t_service_packet = threading.Thread(target=self.service_packet_thread, args=(packet,))
            t_service_packet.start()
                
    def send_register_packet(self, content_name, src_ip):
        ether = Ether(src=self.CACHE_IN_ETH, dst=self.CONTROLLER_ETH)
        ip = IP(src=content_name, dst=src_ip, proto=self.REG_PROTO)  
        data = "register"
        packet = ether / ip / data
        #packet.show()
        sendp(packet)
                                
    def repo(self, repo_port,repo_path, ip_src):
        #print (repo_port)
        BUFFER_SIZE = 50
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to a public host, and a well-known port
        serversocket.bind(('127.0.0.1', repo_port))
        # become a server socket
        serversocket.listen(1)
        #print('after listen')
        (client_socket, address) = serversocket.accept() 
        while True:
            r = client_socket.recv(BUFFER_SIZE).decode()
            if len(r)==0:
                continue
            fields = r.split('|')
            i = 0
            while(i<len(fields)):
                data_file_path =  fields[i].rstrip()
                pure_name = fields[i+1].rstrip()
                print('Registering content ', pure_name)
                content_name = encode_ip(pure_name,1)
                cmd_cp_to_repo = 'cp ' + data_file_path + '  ' + repo_path+'/'+ str(decode_ip(content_name)[0])
                os.system(cmd_cp_to_repo)
                self.send_register_packet(content_name,ip_src)
                i += 2

    

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-p", "--path",
                      dest="path",
                      help="repository complete path")
    parser.add_option("-i", "--host", dest="host_id",
                      help="Host ID")
    (options, args) = parser.parse_args()
    s_id = (options.host_id) if options.host_id else 1
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if iface.startswith('lo'):
            continue
        else:
            addrs = netifaces.ifaddresses(iface)
            ip_src = addrs[netifaces.AF_INET][0]['addr']
            break
    if len(args)>0 and args[0]=='repo':
        #print(options.path)
        cache = cache_service(s_id, options.path)
        BUFFER_SIZE = 2048
        t = Thread(target=cache.repo, args=(cache.REPO_PORT,cache.REPO_PATH,ip_src))
        t.start()
    else:
        cache = cache_service(s_id)
    
    t_rest = threading.Thread(target=cache.send_update_cs_rest, args=())
    t_rest.start()
    sniff( iface=cache.CACHE_IN_FACE, prn=lambda x: cache.service_packet(x))#,lfilter=lambda x: eth_src in x.summary())
    
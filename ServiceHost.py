# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 14:30:08 2016

# -*- coding: utf-8 -*-
@author: Zali
"""

from scapy.layers.inet import Ether,IP 
from scapy.contrib.mpls import MPLS
from scapy.all import *
from copy import deepcopy
import os
from Storage import CS,PIT
import threading
import time
import socket
import queue
#from multiprocessing import Queue
from threading import Thread
from optparse import OptionParser
import hashlib
#import pyndn as ndn
import netifaces
#import psutil
from log import Log

LIFETIME= 1 # s
T=0

    
def encode_in_2bytes(field):
    #print(type(field))
    field_len=len(field)
    data = bytearray()
    data.append(field_len)
    data = data + bytearray(field, 'utf8')
    #print("encodeing: ", data)
    return data
    
def name2label(name):
    label = hashlib.sha256()
    label.update(name.encode())
    name_bytes = label.digest()
    return str(name_bytes[0]*4096+name_bytes[1]*16+(name_bytes[2]>>4))#first 20 bits
    
   
def decode_ndn(ndn_bytes):
    content_name_len=int(ndn_bytes[0])
    content_name=(ndn_bytes[1:content_name_len+1]).decode('utf-8')
    chunk_len = ndn_bytes[content_name_len+1]
    data_indx = content_name_len+2+chunk_len
    chunk=int((ndn_bytes[content_name_len+2:data_indx]).decode('utf-8'))
    data=(ndn_bytes[data_indx:]).decode('utf-8')
    return content_name,chunk,data
    
class Service_Host(object):
    def __init__(self,exp,s_id, repo_path=None):
        self.OUT_PATH = './Out/'+exp+'/'
        self.CONTROLLER_ETH = '1c:6f:65:ca:15:df'
        self.CONTROLLER_IP = ''
        self.REPO_PORT = 5000
        self.REPO_PATH = repo_path
        self.CHUNK_SIZE = 1000
        self.BUFF_SIZE = 1000
        self.q_task = queue.Queue(self.BUFF_SIZE)
        self.MPLS_TTL = 10
        self.INT_PROTO = 150
        self.DATA_PROTO = 151
        self.rx = 0    #number of recieved packets
        self.tx = 0    #number of transfered packets 
        self.sniffed_num = 0
        self.skip_next_packet=False
        self.SH_IN_FACE = str()
        self.SH_IN_IP = str()
        self.SH_IN_ETH = str()
        self.SH_OUT_FACE = str()
        #self.SH_OUT_IP = str()
        self.SH_OUT_ETH = str()
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if iface.endswith('100'):
                self.SH_IN_FACE = iface
                self.SH_IN_IP = addrs[netifaces.AF_INET][0]['addr']
                self.SH_IN_ETH = addrs[netifaces.AF_LINK][0]['addr']
                print("IN port:",self.SH_IN_FACE, self.SH_IN_IP, self.SH_IN_ETH)
            elif iface.endswith('101'):
                self.SH_OUT_FACE = iface
                #self.SH_OUT_IP = addrs[netifaces.AF_INET][0]['addr']
                self.SH_OUT_ETH = addrs[netifaces.AF_LINK][0]['addr']
                print("OUT port:",self.SH_OUT_FACE,  self.SH_OUT_ETH)
            elif iface.endswith('eth0'):
                self.SH_OUT_FACE = self.SH_IN_FACE = iface
                self.SH_IN_IP = addrs[netifaces.AF_INET][0]['addr']
                self.SH_IN_ETH = self.SH_OUT_ETH = addrs[netifaces.AF_LINK][0]['addr']
                print("IN port:",self.SH_IN_FACE, self.SH_IN_IP, self.SH_IN_ETH)
                
        if repo_path is None:
            self.isRepo = False
            self.cache = CS(s_id,chunk_size=self.CHUNK_SIZE, ip_src=self.SH_IN_IP)
            self.send_register_packet(self.name2label(''))
        else:
            self.isRepo = True
            self.cache = CS(s_id,repo_path,self.CHUNK_SIZE, self.SH_IN_ETH,self.SH_IN_IP)
            
        self.pit = PIT(exp,self.SH_IN_IP,s_id)
        self.log_delay_int = Log(self.OUT_PATH+'delay_int_e',100)
        self.log_delay_data = Log(self.OUT_PATH+'delay_data_s',100)
        
        ##A thread running tasks in the queue
        Thread(target=self.process_queue, args=()).start()

    def process_queue(self):
        while True:
            time.sleep(0.0001)
            task = self.q_task.get()
            if task is None:
                continue
            else:
                task.start()
        
    def decode_packet(self,packet):
        """
        decode a ndn packet and extract its required fields
        :param packet_ndn: the ndn packet (data or interest + IP header)
        :return: {'content_name':ndn content name, 'proto':the protocol of next layer after IP,
                  'chunk_num':data or requested data chunk num, 
                  'src_ip':source IP address,'dst_ip':dsttination IP address}
        """
        fields = defaultdict()
        fields['proto'] = packet[IP].proto
        fields['in_port'] = packet[IP].tos
        fields['src_ip'] = packet[IP].src
        if fields['proto'] == self.INT_PROTO or fields['proto']==self.DATA_PROTO:
            #print('****',fields['ndn_header'] )
            fields['content_name'],fields['chunk_num'], fields['data'] = decode_ndn(packet[IP].load)
            fields.update({'key':fields['content_name']+':'+str(fields['chunk_num'])})
            fields['flow_id'] = packet[IP].dst
            return fields
        return fields
        
    #Data packet: {content_name_len(2bytes)+content_name+chunk_numlen(2bytes)+chunk_num+data}    
    def create_packet(self,data, flow_id, oport,et_src, ip_src, ip_proto=151):
        #print('begin creating packet, et_src:'+str(et_src)+', ip_src: '+str(ip_src))
        ether = Ether(src=et_src)#, dst=et_dst)
        ip = IP(src=ip_src, dst =flow_id, tos=oport, proto=ip_proto, ttl=65)  
        #print('data packet bytes',data_bytes)
        packet = ether / ip / data
        
        return packet
        
    
    def service_interest(self, int_packet, int_pac_fields, eth_src, eth_dst):
        """
        handle an interest packet
        :param int_packet: interest packet to be handled 
        :return: None
        """   
     
        chunk_num = int_pac_fields['chunk_num']
        content_name = int_pac_fields['content_name']
        #print(content_name,chunk_num)
        data = self.cache.lookup(content_name, chunk_num)
        if data is not None and len(data)>0:
            #print('data in cache or repo')
            packet = self.create_packet(data,int_pac_fields['flow_id'],
                                        int_pac_fields['in_port'],self.SH_IN_ETH,self.SH_IN_IP)
            #print('+++',packet[IP].load)
            self.log_delay_int.save(content_name, chunk_num,int_pac_fields['data'])
            sendp(packet,iface=self.SH_OUT_FACE)
        else:
            if self.pit.add(content_name, chunk_num, LIFETIME, int_pac_fields['in_port'])<0:
                #send interest
                sendp(int_packet, iface=self.SH_OUT_FACE) 
        #self.elog.save(int_pac_fields['content_name'],int_pac_fields['chunk_num'])
    
    def service_data(self,data_packet, data_pac_fields, eth_src, eth_dst):
        """
        handle an data packet
        :param data_packet: data packet to be handled
        :return: None
        """  
        #print('data packet')
        self.cache.add(data_pac_fields['content_name'],data_pac_fields['chunk_num'],data_packet[IP].load.decode())
        faces = self.pit.lookup(data_pac_fields['content_name'], data_pac_fields['chunk_num'])
        if faces is not None:
            #print('forward data')
            self.pit.remove(data_pac_fields['content_name'],data_pac_fields['chunk_num'])
            #print('remove from pit')
            for face in faces:
                #print('forward data to face ', face)
                data_packet[IP].tos = face
                #self.log_delay_data.save(data_pac_fields['content_name'], data_pac_fields['chunk_num'])
                sendp(data_packet, iface=self.SH_OUT_FACE)
        
   
    def service_packet_thread(self, packet):
        self.sniffed_num = self.sniffed_num + 1
        eth_src = packet[Ether].src
        eth_dst = packet[Ether].dst
        ndn_pack_fields = self.decode_packet(packet)
        #self.slog.save(ndn_pack_fields['content_name'], ndn_pack_fields['chunk_num'])
        if ndn_pack_fields['proto'] == self.INT_PROTO:
            #print('int time for', ndn_pack_fields['chunk_num'],':',time.time())
            self.service_interest(packet, ndn_pack_fields, eth_src,eth_dst)
        elif ndn_pack_fields['proto'] == self.DATA_PROTO:
            #print(time.time())
            self.service_data(packet, ndn_pack_fields, eth_src,eth_dst)
        self.q_task.task_done()
            
    def service_packet(self,packet):
        """
        handle an input packet in service host
        :param packet: the packet that service host has recieved
        :return: None
        """
        if packet.haslayer(IP):
            if self.q_task.full() is not True:
                self.q_task.put(threading.Thread(target=self.service_packet_thread, args=(packet,)))
            
                
    def send_register_packet(self, content_name):
        
        ether = Ether(src=self.SH_IN_ETH, dst= self.CONTROLLER_ETH)
        
        mpls = MPLS(label=content_name, ttl=10)
        
        ip = IP(src=self.SH_IN_IP, proto=152)  
        
        data = "register"
            
        packet = ether / mpls / ip / data
        
        #packet.show()
        sendp(packet)
                
    def name2label(self, name):
        label = hashlib.sha256()
        label.update(name.encode())
        name_bytes = label.digest()
        return name_bytes[0]*4096+name_bytes[1]*16+(name_bytes[2]>>4)#first 20 bits 
                
    def repo(self, repo_port,repo_path):
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
                content_name = self.name2label(fields[i+1].rstrip())
                #print("plain name:",fields[i+1])
                cmd_cp_to_repo = 'cp ' + data_file_path + '  ' + repo_path+'/'+ str(content_name)
                os.system(cmd_cp_to_repo)
                self.send_register_packet(content_name)
                #print('content is registered ', content_name)
                i += 2

    

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-p", "--path",
                      dest="path",
                      help="repository complete path")
    parser.add_option("-i", "--s_id",
                      dest="s_id",
                      help="switch id")
    parser.add_option("-e", "--experiment", dest="exp",
                      help="experiment name")
    
    (options, args) = parser.parse_args()
    s_id = options.s_id
    exp = (options.exp) if options.exp else 'topo_0'

    if len(args)>0 and args[0]=='repo':
        #print(options.path)
        sh = Service_Host(exp,s_id,options.path)
        BUFFER_SIZE = 2048
        t = Thread(target=sh.repo, args=(sh.REPO_PORT,sh.REPO_PATH))
        t.start()
    else:
        sh = Service_Host(exp,s_id)
        
    sniff( iface=sh.SH_IN_FACE, prn=lambda x: sh.service_packet(x))#,lfilter=lambda x: eth_src in x.summary())
    
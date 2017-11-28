# -*- coding: utf-8 -*-
"""
Created on Tue May 23 16:15:31 2017

@author: root
"""
from __future__ import print_function
from scapy.layers.inet import Ether, IP
from scapy.contrib.mpls import MPLS
from scapy.all import sendp
from optparse import OptionParser
import hashlib
import threading
from threading import Timer
from time import sleep
import time
import netifaces
from scapy.all import sniff
from collections import defaultdict
from log import Log
#from multiprocessing import Queue
import queue
#import psutil
      
class consumer():
    def __init__(self, experiment,host_id, src_eth, src_ip):
        self.flow_num = 0
        self.int_num = 0
        self.PATTERN_PATH = './Requests/'
        self.OUTPUT_PATH = './Out/'+experiment+'/'
        self.CHUNK_SIZE = 1000#Bytes
        self.CHUNK_NUM = 10
        self.TIMEOUT = 10 #s
        self.LIFETIME = 1  #s 
        self.BUFF_SIZE = 10000
        self.q_input_task = queue.Queue(self.BUFF_SIZE)
        self.q_output_task = queue.Queue(self.BUFF_SIZE)
        self.recieved_data=defaultdict()
        self.recieved_data_lock = threading.Lock()
#        self.threadq_waiting=[]
#        self.MAX_THREAD = 1000
#        self.MAX_FD = 16384
#        self.threadq_running=0
        self.slog_delay_int=Log(self.OUTPUT_PATH+'delay_int_s',100)
        self.slog_delay_data=Log(self.OUTPUT_PATH+'delay_data_e',100)
        slog=Log(self.OUTPUT_PATH+'down_time_'+host_id+'_s',20)
        elog=Log(self.OUTPUT_PATH+'down_time_'+host_id+'_e',20)
        hop_log=Log(self.OUTPUT_PATH+'hop_count_'+host_id,100)
        
#        t_threadExecution = threading.Thread(target=self.start_threads, args=())
#        t_threadExecution.start()
#        self.req_num = 0
#        threading.Thread(target=self.packet_in_rate).start()
            
        reqs,times=self.read_requests(host_id)
        
        t_in_task = threading.Thread(target=self.send_req, args=())
        t_in_task.start()
        
        t_out_task = threading.Thread(target=self.get_reply, args=())
        t_out_task.start()
        
        t_generator = threading.Thread(target=self.generate_requests, args=(src_eth, src_ip, host_id,slog, reqs, times))
        t_generator.start()
        
        t_consumer = threading.Thread(target=self.consume_requests, args=(src_eth, host_id,elog,hop_log))
        t_consumer.start()

        
    def send_req(self):
        while True:
#           time.sleep(0.0001)
           task = self.q_input_task.get()
           if task is None:
               continue
           else:
               task.start()
               #print('thread num: ',threading.active_count())
                
    def get_reply(self):
        while True:
#           time.sleep(0.0001)
           task = self.q_output_task.get()
           if task is None:
               continue
           else:
               task.start()
               print('thread num: ',threading.active_count())
                
    def timeout_callback(self,host_id,content, chunk, flow_num, src_eth, src_ip):
        print ('timeout')
        self.recieved_data_lock.acquire()
       # print('after lock')
        if flow_num not in self.recieved_data[content]:
            self.recieved_data_lock.release()
            #print('lock release')
            return
        if time.time()-self.recieved_data[content][flow_num]['stime']>=self.TIMEOUT:
            print('timeout: ', flow_num)
            del self.recieved_data[content][flow_num]        
            #self.recieved_data[content].pop(flow_num)
            self.recieved_data_lock.release()
            #print('lock release')
            return
        self.recieved_data_lock.release()
        #print('lock release')
        timer = Timer(min(self.LIFETIME, time.time()-self.recieved_data[content][flow_num]['stime'])
                        , self.timeout_callback,args=(host_id,content,chunk,flow_num,src_eth, src_ip, ))
        self.recieved_data[content][flow_num].update({chunk:[timer,0]}) #[timer,hop_count]
        self.int_num += 1
        self.q_output_task.put(threading.Thread(target=self.send_packet,
             args=(host_id+str(self.int_num),src_eth, 'ff:ff:ff:ff:ff:ff', content, chunk, flow_num, src_ip)),True)
                                                
                        
    def packet_in_rate(self):
        T = float(5)
        while (True):
            time.sleep(T)
            f = open('./Out/rate_log','a')
            print('h', self.req_num, time.time(),file=f)
            f.close()
            
    def decode_ndn(self,ndn_bytes):
        content_name_len=int(ndn_bytes[0])
        content_name=(ndn_bytes[1:content_name_len+1]).decode('utf-8')
        chunk_len = ndn_bytes[content_name_len+1]
        data_indx = content_name_len+2+chunk_len
        chunk=int((ndn_bytes[content_name_len+2:data_indx]).decode('utf-8'))
        data=(ndn_bytes[data_indx:]).decode('utf-8')
        return content_name,chunk,data
        
    def encode_in_2bytes(self,field):
        #print(type(field))
        field_len=len(field)
        data = bytearray()
        data.append(field_len)
        data = data + bytearray(field, 'utf-8')
        #print("encodeing: ", data)
        return data
    
    #Int packet: {content_name_len(2bytes)+content_name+chunk_numlen(2bytes)+chunk_num}
    def send_packet(self,req_id, et_src, et_dst, content_name, chunk_num, flow_num, ip_src, 
                     ip_proto=150, mpls_ttl=10):
        
        ether = Ether(src=et_src, dst=et_dst)
        
        label = hashlib.sha256()
        label.update(content_name.encode())
        name_bytes = label.digest()
        mpls_label = name_bytes[0]*4096 + name_bytes[1]*16 + (name_bytes[2]>>4)#first 20 bits 
        #print('content name ' ,content_name, 'mpls label:', mpls_label)
        mpls = MPLS(label=mpls_label, ttl=mpls_ttl)
          
        #creating Interest packet
        data=self.encode_in_2bytes(content_name)
        data = data + self.encode_in_2bytes(str(chunk_num))
        data = data + (req_id).encode('utf-8')
        ip = IP(src=ip_src, proto=ip_proto)  
        packet = ether / mpls / ip / data.decode()
        self.recieved_data[content_name][flow_num][chunk_num][0].start()
        self.slog_delay_int.save(content_name, chunk_num,str(req_id))
        sendp(packet)
        print ('task num:',self.q_output_task.qsize())     
        self.q_output_task.task_done()    
        
        
    def read_requests(self,h_id):
        f_req = open(self.PATTERN_PATH+'requests_'+str(h_id))
        reqs = []
        line = f_req.readline()
        while (line):
            reqs.append(str(int(line.rstrip())))
            line = f_req.readline()
            
        f_time=open(self.PATTERN_PATH+'times_'+str(h_id))
        times = []
        line = f_time.readline()
        while (line):
            times.append(int(line.rstrip()))
            line = f_time.readline()
        return reqs,times
        
    
    def generate_requests(self,src_eth, src_ip, s_id, slog, reqs, times):
        #chunk=bytearray([255]*CHUNK_SIZE)
        
        for r in reqs:
            sleep(0.001*times.pop(0)) # Time in seconds.
            #f=open(self.OUTPUT_PATH+str(s_id)+'_log.txt','a')
            #print('request for content: '+str(r),file=f)
            #f.close()
            #print('interest time for ', r, ':',time.time())
            flow_num = self.flow_num            
            self.flow_num += 1
            self.recieved_data.setdefault(r,dict())
            slog.save(r,0,str(flow_num))     
            self.recieved_data[r].update({flow_num:dict()})
            self.recieved_data[r][flow_num].update({'finished':set()})
            self.recieved_data[r][flow_num].update({'stime':time.time()})
            for k in range(1, self.CHUNK_NUM+1):
                #self.req_num += 1
                #self.slog_delay_int.save(r, k)
                timer = Timer(self.LIFETIME, self.timeout_callback,args=(s_id,r,k,flow_num,src_eth, src_ip, ))
                self.recieved_data[r][flow_num].update({k:[timer,0]}) #[timer,hop_count]
                self.int_num += 1
                self.q_output_task.put(threading.Thread(target=self.send_packet,
                                                      args=(s_id+str(self.int_num),src_eth, 'ff:ff:ff:ff:ff:ff', r, k, flow_num, src_ip)),True)
                            
    def decode_packet(self, packet):
        """
        decode a ndn packet and extract its required fields
        :param packet_ndn: the ndn packet (data or interest + IP header)
        :return: {'content_name':ndn content name, 'proto':the protocol of next layer after IP,
                  'chunk_num':data or requested data chunk num, 
                  'src_ip':source IP address,'dst_ip':dsttination IP address}
        
        """
        fields = dict()
        if packet[IP].proto == 150:
            fields['proto'] = 150
            fields['in_port'] = packet[IP].tos
        elif packet[IP].proto == 151:
            fields['proto'] = 151
        else:
            fields['proto'] = -1
            return fields
        content_name,chunk,data=self.decode_ndn(packet[IP].load)
        fields.update({'content_name':content_name})
        fields.update({'src_ip':packet[IP].src})
        fields.update({'dst_ip':packet[IP].dst})
        fields.update({'chunk_num':chunk})
        fields.update({'data':data})
        fields.update({'hop_count':64-packet[IP].ttl})
        return fields        
        
    def service_packet_thread(self, s_id, packet, elog,hop_log):
        #eth_src = packet[Ether].src
        #eth_dst = packet[Ether].dst
        data_pack_fields = self.decode_packet(packet)
        if data_pack_fields['proto'] == 151:
            #print ('Data packet from: ', data_pack_fields['src_ip'],\
            #        ' to ', data_pack_fields['dst_ip'])
            #print ('data')
            content_name = data_pack_fields['content_name']
            chunk_num = data_pack_fields['chunk_num']
            #self.slog_delay_data.save(content_name, chunk_num)
            #print('number of reqs for name ', content_name, ': ', len(recieved_data[content_name]))
            
            #print('data time for ', chunk_num, ':',time.time())
            self.recieved_data_lock.acquire()
            #print('after lock in data')
            for flow in self.recieved_data[content_name].copy():
                if chunk_num not in self.recieved_data[content_name][flow]['finished']:
                    self.recieved_data[content_name][flow][chunk_num][1] = data_pack_fields['hop_count']
                    self.recieved_data[content_name][flow][chunk_num][0].cancel()
                    self.recieved_data[content_name][flow]['finished'].add(chunk_num)
                    #hop_log.save(flow, content_name,chunk_num,str(data_pack_fields['hop_count']))
                    if (len(self.recieved_data[content_name][flow]['finished'])==self.CHUNK_NUM):
        #               avg_hop_count = (sum(d for d in recieved_data[content_name][i].values())-recieved_data[content_name][i]['stime'])/float(CHUNK_NUM)
                        #print('save to file')
                        elog.save(content_name,0,str(flow))
                        self.recieved_data[content_name].pop(flow)
            self.recieved_data_lock.release()
            #print('after lock release in data')
        self.q_input_task.task_done()
                                        
                    
    def service_packet(self, s_id, packet,elog, hop_log):
        if packet.haslayer(IP):
            self.q_input_task.put(threading.Thread(target=self.service_packet_thread, 
                                                     args=(s_id, packet,elog,hop_log, )),True)
                                   
                
    def consume_requests( self, src_eth, s_id, elog, hop_log):
       sniff(prn=lambda x: self.service_packet(s_id, x, elog, hop_log))#, lfilter=lambda x: eth_src in x.summary())
      
#    def start_threads(self):
#        while True:
#            if len(self.threadq_waiting)>0:
#                if psutil.Process().num_fds()>self.MAX_FD:#len(self.threadq_running>self.MAX_THREAD):
#                    time.sleep(0.000001)
#                else:
#                    self.threadq_running += 1
#                    self.threadq_waiting.pop(0).start()
                
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--host", dest="host_id",
                      help="Host ID")
    parser.add_option("-e", "--experiment", dest="exp",
                      help="experiment name")
    (options, args) = parser.parse_args()
    host_id = (options.host_id) if options.host_id else '1'
    exp = (options.exp) if options.exp else 'topo_0'
    
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if iface.startswith('lo'):
            continue
        else:
            addrs = netifaces.ifaddresses(iface)
            src_eth = addrs[netifaces.AF_LINK][0]['addr']
            src_ip = addrs[netifaces.AF_INET][0]['addr']
            break
    consumer_host = consumer(exp,host_id,src_eth,src_ip)
    
    
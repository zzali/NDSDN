# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 13:56:07 2016

@author: Zeinab Zali
"""
from __future__ import print_function
from collections import defaultdict
import os
from scapy.layers.inet import Ether, IP
import time
from threading import Timer
import threading 
import hashlib
from copy import deepcopy
#from log import Log
#import pyndn as ndn

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
    
class CS(object):
        
    def __init__(self, s_id, repo_path=None, chunk_size=None,eth_src=None,ip_src=None):
        if repo_path==None:
            self.MAX_STORAGE_SIZE = 1000
        else:
            self.MAX_STORAGE_SIZE = 3000
        #self.logfile=open('./Out/SH_log_'+ip_src,'w')
        self.hit_num = 0
        if repo_path is not None:
            self.chunk_size = chunk_size
            self.repo_path = repo_path
            self.eth_src = eth_src
            self.ip_src = ip_src
        else:
            self.repo_path = None
        self.storage = defaultdict(str)     #represents content store: {'content_name':'chunk_num':data_chunk}
        self.storage_free = self.MAX_STORAGE_SIZE   #size of free storage in cache
#        print("Storage size: ", self.storage_free)
        #self.storage = list()  #each element of this list is a chunk of a data
        self.lru = defaultdict(int)      #tm value for each content key
        self.tm = 0
        self.storage_lock = threading.Lock()
#        self.slog=Log('start_'+str(s_id),2)
#        self.elog=Log('end_'+str(s_id),2)
    
    def lookup(self,content_name,chunk_num):
        """
        look up a content in cache
        :param content_name: tag name of the content
        :param chunk_num: chunk number of the requested content
        :return: if hit in repository return correspondent data 
                 else return None 
        """
                   
        key = content_name+':' + str(chunk_num)
        #print('key',key)
        self.storage_lock.acquire() 
#        print ("looking ", key, "in ", self.storage.keys())
        if key in self.storage:# and len(self.storage[key])>0:
            self.hit_num += 1
            self.lru[key] = self.tm
            self.tm += 1
#            print("Hit in cache for ", key )
            data = self.storage[key]
            self.storage_lock.release()
            return data
        if self.repo_path is None:
            self.storage_lock.release()
            return None
        self.storage_lock.release()
        label = name2label(content_name)
#        print("requested content label: ",label, chunk_num, content_name)
        file_path = self.repo_path+'/'+ label
        if os.path.exists(file_path):
#            print('content is available in the repo')
            f = open(file_path, 'r')
            f.seek(chunk_num*self.chunk_size)
            chunk = f.read(self.chunk_size)
            name_bytes = encode_in_2bytes(content_name)
            data = (name_bytes + encode_in_2bytes(str(chunk_num))+chunk.encode('utf-8')).decode()
            self.add(content_name,chunk_num,data)
            return data
        return None
    
    def add(self,content_name,chunk_num,data):
        """
        add a chunk of a content to the cache
        :param content_name: tag name of the content
        :param chunk_num: chunk number of the requested content
        :param data: data to be cached
        :return: None
        """
        datac = deepcopy(data)
        key = content_name + ':' + str(chunk_num)
        self.storage_lock.acquire()
        if key in self.storage:
            self.storage_lock.release()
            return
#        print ("add to storage: ", key)    
        if self.storage_free==0:
#            print('Replacement in cache')                   #replace with LRU cache replacement policy 
            old_key = min(self.lru, key=lambda k:self.lru[k])
            self.lru.pop(old_key)
            self.storage.pop(old_key)
        else:    
            self.storage_free -= 1
        self.storage_lock.release()           
        self.storage[key]=datac
        self.lru[key]=self.tm
        self.tm += 1
        
        #print('data have been added to the cache: ', key)
        
class PIT(object):
    def __init__(self,exp,ip_src,s_id):
        self.table = defaultdict()  #list of {'content_name''chunk_num':{port1:[timeout1,timer1]},{port2:[timeout2,timer2]},...}
        self.table_lock = threading.Lock()
        self.droped_int = 0
        self.satisfied_int = 0
        self.id = str(s_id)
        #self.OUT_PATH = './Out/'+exp+'/'
        #self.logfile=open(self.OUT_PATH+'SH_log_'+self.id,'w') 
        #self.logfile.close()
        self.timeout_num = 0
       
        
    def timeout_callback(self,key,port):
        if key in self.table:
            if port in self.table[key]:
                self.timeout_num += 1
                #self.logfile=open(self.OUT_PATH+'SH_log_'+self.id,'a') 
                #print('timeout interests for name: ' + key + ' from port ' +str(port) + 
                #        'for ' + str(self.timeout_num) + ' times',file=self.logfile)
                #self.logfile.close()
                self.droped_int = self.droped_int + 1
                self.table_lock.acquire()
                self.table[key].pop(port)
                if len(self.table[key])<=0:
                    self.table.pop(key)
                self.table_lock.release()
        
            
    def add(self,content_name, chunk_num, lifetime, in_port):
        key = content_name + ':' + str(chunk_num)
        timeout = time.time() + lifetime
        timer = Timer(lifetime, self.timeout_callback,args=(key,in_port,))
        self.table_lock.acquire()        
        if key in self.table:
            if in_port in self.table[key]:
                #print("update pit table for key ",key)
                if self.table[key][in_port][0]<timeout:
                    #update timeout
                    self.table[key][in_port][1].cancel()
                    self.table[key][in_port]=[timeout,timer];
                    self.table[key][in_port][1].start()
                    #self.table[key].update({in_port:[timeout,timer]})
                else:
                    #print("update pit table for new port for key ",key)
                    self.table[key].update[in_port]=[timeout,timer]
                    self.table[key][in_port][1].start()
                    #self.table[key].update({in_port:[timeout,timer]})
                self.table_lock.release()
                return 0
        else:
            #print("update pit table for new key and new port for key ",key)
            self.table[key]=dict({in_port:[timeout,timer]})
            self.table[key][in_port][1].start()
            #self.table.update({key:dict({in_port:[timeout,timer]})})
            self.table_lock.release()
        return -1
        
        
        
    def remove(self,content_name, chunk_num):
        key = str(content_name) + ':' + str(chunk_num)
        self.table_lock.acquire()
        if key in self.table:
            self.satisfied_int = self.satisfied_int + len(self.table[key])
            self.table.pop(key)
        self.table_lock.release()
            
    def lookup(self,content_name, chunk_num):
        key = str(content_name) + ':' + str(chunk_num)
        #print("requested data: ",key)
        self.table_lock.acquire()
        if key in self.table:
            faces = self.table[key].keys()
            self.table_lock.release()
            return faces
        self.table_lock.release()
        return None
        
        
    
        



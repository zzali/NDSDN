# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 13:41:14 2016

@author: root
"""

from collections import defaultdict

class Registration(object):
    '''    
    Each content is registered in the controller through the first switch
    which recieves the registration message.
    It has an entry in a dictionary in form {content_name:eth_src}
    eth_mac is the mac address of the publisher
    
    
    '''
        
    def __init__(self):
        self.DB_file_path = './contents_DB' #for saving content database on the disk storage
        self.contents_tab = defaultdict()          #{label:eth_src}
        self.flows_tab = defaultdict()
        self.flows_path = defaultdict()
        
    def add(self, content_name, ip_src, eth_src ):
        print('add ', content_name)
        if content_name in self.contents_tab.keys():
            self.contents_tab[content_name].setdefault(ip_src,eth_src)
        else:
            new_pub = dict({ip_src:eth_src})
            self.contents_tab.update({content_name:new_pub})
        
    def lookup(self, content_name):
        if content_name in self.contents_tab.keys():
            print('find in controller tabel')
            #return only first publisher
            for pub in self.contents_tab[content_name]:
                print pub
                ret = dict({'ip': pub})
                ret.update({'eth': self.contents_tab[content_name][pub]})
                print ret
                break;
            return ret
        else:
            return None
            
    def add_flow(self,flow_id, in_port, path):
        if flow_id in self.flows_tab:
            if in_port in self.flows_tab[flow_id]:
                return -1
        self.flows_tab.setdefault(flow_id,[]).append(in_port)
        self.flows_path.setdefault(flow_id,path)
        return 0
        
    def get_flow_path(self, flow_id):
        return self.flows_path[flow_id]
        
        
    
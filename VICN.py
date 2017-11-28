# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, mpls
from ryu.lib.packet import ether_types
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
import networkx as nx
import os
import re
from registration import Registration
from ryu.ofproto import ofproto_v1_4
import threading
import time



SH_IN_PORT = 100
SH_OUT_PORT = 101

class ICSDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    '''
    This file implement the controller.
    Ryu is an event-driven controller that you can handle events separately.

    ==============================
    =========== Events ===========
    Events are defined with a python decorator "@set_ev_cls" and it takes
    two arguments:
        - Event: (EventOFPxxxxx)
            + EventOFPSwitchFeatures: Controller response on switch establishment
            + EventOFPPacketIn: Controller receive message from a switch
        - Event argument:
            + CONFIG_DISPATCHER: Ignore events before handshake

    ==============================
    ========= Parameters =========
    In this section important parameters are described:
        - datapath: Controller-switch negotiation path
        - datapath.ofproto: OpenFlow definitions
        - datapath.ofproto_parser: Wire message for encoder/decoder

    ==============================
    ======== Our protocol ========

    -- get "protocol" field in IP header
    -- case protocol:
    ---- 150 : NDN interest packet
    ---- 151 : NDN data packet
    ---- else: other tcp/ip packets
    '''

    def __init__(self, *args, **kwargs):
        super(ICSDNController, self).__init__(*args, **kwargs)
        self.switches = []
        self.links = []
        self.mac_to_port = {}
        self.topology_api_app = self
        self.net = nx.DiGraph()  # Directional graph to set output_port
        self.INTEREST_PROTOCOL = 150
        self.DATA_PROTOCOL = 151
        self.REGISTER_PROTOCOL = 152
        self.HELLO_LABEL = 932620
        f = os.system('ifconfig > ifconfig')
        f = open('ifconfig', 'r+').read()
        # f = open('/proc/net/arp', 'r').read()sc
        mac_regex = re.compile("(?:[0-9a-fA-F]:?){12}")
        self.CONTROLLER_ETH = mac_regex.findall(f)[0]
        
        self.INTEREST_PORT = 9997
        self.DATA_PORT = 9998
        self.RIB = Registration()
        self.switches_dp=dict()
        self.icn_switches = []
        self.packet_in_num = 0
        threading.Thread(target=self.packet_in_rate).start()
        
        # self.nodes = {}
        # self.links = {}
        # self.no_of_nodes = 0
        # self.no_of_links = 0
        # self.i = 0

    def packet_in_rate(self):
        T = float(10)
        f = open('./Out/icn/controller_log','w')
        f.close()
        pre_num = 0
        while (True):
            time.sleep(T)
            rate = (self.packet_in_num - pre_num)/T
            pre_num = self.packet_in_num
            f = open('./Out/icn/controller_log','a')
            print(rate,file=f)
            f.close()
            
            
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Handle switch features reply to install table miss flow entries.
        TIP: You can keep this function without any change and reuse it.
        :param ev: Event
        :return:
        """
        
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.switches_dp.update({datapath.id:datapath})
        if datapath.id in self.icn_switches:
            print("insert initial rules in ICN switch "+str( datapath.id))
            
            # install table-miss flow entry
            #
            # We specify NO BUFFER to max_len of the output action due to
            # OVS bug. At this moment, if we specify a lesser number, e.g.,
            # 128, OVS will send Packet-In with invalid buffer_id and
            # truncated packet data. In that case, we cannot output packets
            # correctly.  The bug has been fixed in OVS v2.1.0.
    
            match = parser.OFPMatch()   # Match everything
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
    
            '''
            Add a flow(role) with priority 0 (lowest priority) in order to
            send mismatched requests to the controller
            '''
            self.add_flow(datapath, 0, 0, match, actions)
            self.add_flow(datapath, 1, 0, match, actions)
            self.add_flow(datapath, 2, 0, match, actions)
            self.add_flow(datapath, 3, 0, match, actions)
            
    
            # Add a role to goto table 1 for first interest packets from clients
            # and goto table 2 for other INT and Data packets
            ins = [parser.OFPInstructionGotoTable(table_id=1)]
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_MPLS)
            self.add_flow(datapath, 0, 2, match, None, instruction=ins)
    
            ins = [parser.OFPInstructionGotoTable(table_id=2)]
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ip_proto=self.INTEREST_PROTOCOL)
            self.add_flow(datapath, 0, 2, match, None, instruction=ins)
    
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ip_proto=self.DATA_PROTOCOL)
            self.add_flow(datapath, 0, 2, match, None, instruction=ins)
            
            ins = [parser.OFPInstructionGotoTable(table_id=3)]
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ip_proto=self.INTEREST_PROTOCOL)
            self.add_flow(datapath, 2, 1, match, None, instruction=ins)
    
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ip_proto=self.DATA_PROTOCOL)
            self.add_flow(datapath, 2, 1, match, None, instruction=ins)
    #        
    #        ins = [parser.OFPInstructionGotoTable(table_id=1)]
    #        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_MPLS,
    #                                ip_proto=self.DATA_PROTOCOL)
    #        self.add_flow(datapath, 0, 3, match, None, instruction=ins)
    
            ## Send to controller if incoming packet is a registration one
            match = parser.OFPMatch(eth_dst = self.CONTROLLER_ETH, eth_type=ether_types.ETH_TYPE_MPLS)
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 0, 2, match, actions)
        else:
            print("insert initial rules in legacy switch "+str( datapath.id))
            match = parser.OFPMatch()   # Match everything
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
    
            '''
            Add a flow(role) with priority 0 (lowest priority) in order to
            send mismatched requests to the controller
            '''
            self.add_flow(datapath, 0, 0, match, actions)
            self.add_flow(datapath, 1, 0, match, actions)
            ins = [parser.OFPInstructionGotoTable(table_id=1)]
            match = parser.OFPMatch()
            self.add_flow(datapath, 0, 1, match, None, instruction=ins)
      
        
        
    def add_flow(self, datapath, table_id, priority, match, actions, instruction=None):
        """
        Add entry to switch table
        :param datapath: target switch
        :param table_id: id of table!
        :param priority: higher number means higher priority
        :param match: which flows match this entry
        :param actions: what to do for matched flow
        :param instruction: set for instruction commands such as GotoTable
        :return: null
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if not instruction:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 actions)]
            mod = parser.OFPFlowMod(datapath=datapath, table_id=table_id,
                                    priority=priority,
                                    match=match, instructions=inst)

        elif not actions:
            mod = parser.OFPFlowMod(datapath=datapath, table_id=table_id,
                                    priority=priority, command=ofproto.OFPFC_ADD,
                                    match=match,  instructions=instruction)
        else:
            action_list = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 actions)]
            inst = action_list + instruction
                                                 
            mod = parser.OFPFlowMod(datapath=datapath, table_id=table_id,
                                    priority=priority, command=ofproto.OFPFC_ADD,
                                    match=match,  instructions=inst)
        datapath.send_msg(mod)
        
        
    def packet_decode(self,pkt):
        """
        Decode a packet and create a dictionary of its fields
        :param pkt: target packet
        :return: if packet is a LLDP it returns None, 
                 otherwise it returns the dictionary of its fields
        """
        fields = dict()
        
        ########################################
        # Layer2 information of packet(Ethernet)
        eth = pkt.get_protocol(ethernet.ethernet)

        fields['eth_type'] = eth.ethertype
        # Ignore lldp(Link Layer Discovery Protocol) packet
        if fields['eth_type'] == ether_types.ETH_TYPE_LLDP:
            return None
          
        # ethernet src and dst of packet
        fields['eth_dst'] = eth.dst
        fields['eth_src'] = eth.src


        #############
        # MPLS header
        mpls_header = pkt.get_protocol(mpls.mpls)
        if mpls_header:
            print ('mpls header')
            fields['mpls_label'] = mpls_header.label
            print (fields['mpls_label'])
        else: 
            fields['mpls_label'] = -1            
        ip = pkt.get_protocol(ipv4.ipv4)
        if ip:
            print('ip payload:')
            fields['ip_src'] = ip.src
            fields['ip_dst'] = ip.dst
            fields['ip_protocol'] = ip.proto
        else:
            fields['ip_protocol'] = -1
                              
        return fields
                   

    def lookup_out_port(self,msg_data_path, ip_src, content_label=None, ip_dst=None):
        if content_label is not None:
            print ('searching ', content_label)
            publisher = self.RIB.lookup(content_label)
        else:
            publisher = dict({'ip':ip_dst})
        if publisher is not None and publisher['ip'] in self.net:
            print('lookup path for ' + str(publisher['ip']))
            print(' from ' + str(ip_src))
                        
            path = nx.shortest_path(self.net, ip_src, publisher['ip'])

            # for switch in path[1:]:
            #dpid = msg_data_path.id
            return publisher['ip'], path
#            next_hop = path[path.index(dpid)+1]
#            #dpid = next_hop
#            #datapath = api.get_datapath(self, dpid)
#            print ('forward to: ',out_port)
#            return [out_port,publisher['ip']]
        else:
            print ('flood')
            #out_port = msg_data_path.ofproto.OFPP_FLOOD
            #if pkt_fields['eth_dst'] != "ff:ff:ff:ff:ff:ff":
            #return  [out_port,'']  
            return '',msg_data_path.ofproto.OFPP_FLOOD
            
    def encode_flow_id(self, ip_src,ip_dst):
        fields_src=ip_src.split(".")
        fields_dst=ip_dst.split(".")
        return fields_src[3]+'.'+fields_src[2]+'.'+ fields_dst[3]+'.' + fields_dst[2]
    
    def lookup_flow_id_path(self, flow_id):
        return self.RIB.get_flow_path(flow_id)
        
    def create_mpls_datapath(self, msg, pkt_fields):
            
        """
        Add a flow in table 1 for pop mpls header and set appropriate 
        IP destination and then goto table2
        In table 2 for interest packets, tos field is set to be the in_port
        and then interest and data packets goto table 3 
        In table 3 forwarding rules for interest or data packets are added
        :param msg: target incoming msg
        :param pkt_fields: the fields of incoming interest packet
        :param oport: the port to forward packet on if necessary
        :return: created packet_out
        """
        msg_datapath = msg.datapath
        parser = msg_datapath.ofproto_parser
        iport = msg.match['in_port']
        
        
        ip_dst, next_ports = self.lookup_out_port(msg_datapath, pkt_fields['ip_src'], 
                                        content_label=pkt_fields['mpls_label'])
        
        if ip_dst=='':
            return    
        flow_id = self.encode_flow_id(pkt_fields['ip_src'],ip_dst)   
        print('path: ', flow_id, ': ', next_ports)          
        #add a rule to remove mpls and set ip_desAddr to publisher ip
        if msg_datapath.id in self.icn_switches:              
            ins = [parser.OFPInstructionGotoTable(table_id=2)]
            actions = [parser.OFPActionPopMpls(ethertype=2048),
                       parser.OFPActionSetField(ipv4_dst=flow_id)]
            
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_MPLS,
                                    mpls_label=pkt_fields['mpls_label'])      
            self.add_flow(msg_datapath, 1, 1, match, actions, instruction=ins)
            
            #send back the packet to the switch for matching operations
            #data = None
    #        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
    #            print("data_mpls=msg.data")
    #            data = msg.data
            actions.append(parser.OFPActionSetField(ip_dscp=iport))
            actions.append(parser.OFPActionOutput(SH_IN_PORT))
            #actions.append(parser.OFPActionOutput(oport))
            out = parser.OFPPacketOut(datapath=msg_datapath, buffer_id=msg.buffer_id,
                                      in_port=iport, actions=actions)   
                                      
        else:
            next_hop = next_ports[2]
            oport = self.net[msg_datapath.id][next_hop]['port']
            ins = [parser.OFPInstructionGotoTable(table_id=1)]
            actions = [parser.OFPActionPopMpls(ethertype=2048),
                       parser.OFPActionSetField(ipv4_dst=flow_id)]
            
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_MPLS,
                                    mpls_label=pkt_fields['mpls_label'])      
            self.add_flow(msg_datapath, 0, 2, match, actions, instruction=ins)
            
            actions.append(parser.OFPActionOutput(oport))
            out = parser.OFPPacketOut(datapath=msg_datapath, buffer_id=msg.buffer_id,
                                      in_port=iport, actions=actions)  
        #config table 2 flows and defaut flows of table 3 to goto SH
        if self.RIB.add_flow(flow_id,iport, next_ports)==0:
            self.create_ndn_datapath(msg,pkt_fields,flow_id,next_ports)
                      
        return out    
        
    
    def create_ndn_datapath(self, msg, pkt_fields,flow_id, next_ports):
        msg_datapath = msg.datapath
        parser = msg_datapath.ofproto_parser
        iport = msg.match['in_port']
        #add a rule to set ip_tos to in_port
        ss = next_ports.index(msg_datapath.id)
        for switch in next_ports[ss:len(next_ports)-1]:
            msg_datapath = self.switches_dp[switch]
            next_hop = next_ports[next_ports.index(switch)+1]
            oport = self.net[switch][next_hop]['port']
            if switch in self.icn_switches:
                #print('add flow for switch ', switch)
                ins = [parser.OFPInstructionGotoTable(table_id=3)]
                actions = [parser.OFPActionSetField(ip_dscp=iport)]
                
                match = parser.OFPMatch(in_port=iport, eth_type=ether_types.ETH_TYPE_IP,
                                        ip_proto=self.INTEREST_PROTOCOL) 
                self.add_flow(msg_datapath, 2, 2, match, actions, instruction=ins)
                
                    
                match = parser.OFPMatch(in_port=oport, eth_type=ether_types.ETH_TYPE_IP,
                                        ip_proto=self.DATA_PROTOCOL) 
                self.add_flow(msg_datapath, 2, 2, match, None, instruction=ins)                                
                                         
                # send interest packets to SH        
                actions = [parser.OFPActionOutput(SH_IN_PORT)]
                #actions = [parser.OFPActionOutput(oport)]
                #print('add flow for table 3 in switch ', switch)
                match = parser.OFPMatch(in_port=iport,eth_type=ether_types.ETH_TYPE_IP,
                                        ip_proto=self.INTEREST_PROTOCOL)        
                self.add_flow(msg_datapath, 3, 1, match, actions)
                
                # send data packets on backward path to the service host      
                actions = [parser.OFPActionOutput(SH_IN_PORT)]
                #actions = [parser.OFPActionOutput(iport)]
                
                match = parser.OFPMatch(in_port=oport,eth_type=ether_types.ETH_TYPE_IP,
                                        ip_proto=self.DATA_PROTOCOL)        
                self.add_flow(msg_datapath, 3, 2, match, actions)
                
                # Add Forward interest path to the destination
                actions = [parser.OFPActionOutput(oport)]
                match = parser.OFPMatch(in_port=SH_OUT_PORT, eth_type=ether_types.ETH_TYPE_IP, 
                                        ip_proto=self.INTEREST_PROTOCOL, ipv4_dst=flow_id)
                #match = parser.OFPMatch(mpls_label=mpls_label, in_port=SH_PORT)
                self.add_flow(msg_datapath, 3, 3, match, actions)     
             
                # Add backward data path to the source
                actions = [parser.OFPActionDecNwTtl(),parser.OFPActionOutput(iport)]
                match = parser.OFPMatch(in_port=SH_OUT_PORT, eth_type=ether_types.ETH_TYPE_IP, 
                                        ip_proto=self.DATA_PROTOCOL, ip_dscp=iport)
                                        
                self.add_flow(msg_datapath, 3, 4, match, actions)
                
            else:
                print('Create channel for forwarding on virtual link in order to forward in non ICN switch')
                print('flow_id:', flow_id, ',switch:', switch, ',next_switch:',next_hop ,',in port: ', iport, 'oport:', oport)
                #for interests
                actions = [parser.OFPActionOutput(oport)]
                match = parser.OFPMatch(in_port=iport, eth_type=ether_types.ETH_TYPE_IP, ip_proto=self.INTEREST_PROTOCOL,
                                        ipv4_dst=flow_id)
                self.add_flow(msg_datapath, 1, 1, match, actions)
                #for data
                actions = [parser.OFPActionDecNwTtl(), parser.OFPActionOutput(iport)]
                match = parser.OFPMatch(in_port=oport, eth_type=ether_types.ETH_TYPE_IP, ip_proto=self.DATA_PROTOCOL,
                                        ipv4_dst=flow_id)
                self.add_flow(msg_datapath, 1, 1, match, actions)
            if 'port' in self.net[next_hop][switch]:
                iport= self.net[next_hop][switch]['port']
            
        #send back the packet to the switch for matching operations
        oport = self.net[msg.datapath.id][next_ports[next_ports.index(msg.datapath.id)+1]]['port']
#        data = None
#        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
#            print("data_ndn=msg.data")
#            data = msg.data
        #actions = actions.append(parser.OFPActionOutput(SH_IN_PORT))
        actions = [parser.OFPActionSetField(ip_dscp=iport), parser.OFPActionOutput(SH_IN_PORT)]
        out = parser.OFPPacketOut(datapath=msg.datapath, buffer_id=msg.buffer_id,
                                  in_port=iport, actions=actions)                         
        return out
      
      
    def create_legacy_datapath(self,msg, pkt_fields):
        """
        forward any other packets except NDN packets
        :param msg: target incoming msg
        :param out_port: the port to forward packet on if necessary
        :return: created packet_out
        """
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']  # Input port of switch (to the source)
        
        if pkt_fields['ip_dst'] in self.net:
            # print 'it is'
            path = nx.shortest_path(self.net, pkt_fields['ip_src'], pkt_fields['ip_dst'])

            # for switch in path[1:]:
            next_hop = path[path.index(dpid)+1]
            out_port = self.net[dpid][next_hop]['port']
        else:
            out_port = ofproto.OFPP_FLOOD
            if pkt_fields['eth_dst'] != "ff:ff:ff:ff:ff:ff":
                return
        
        actions = [parser.OFPActionOutput(out_port, ofproto.OFPCML_NO_BUFFER)]
        match = parser.OFPMatch(eth_type=pkt_fields['eth_type'], ipv4_dst=pkt_fields['ip_dst'])
        self.add_flow(datapath, 0, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=actions, data=data)   
        return out
            
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Packet_In event; Mismatched in switch and it asks controller
        :param ev: Event
        :return:
        """
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id  # Switch id
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        pkt_fields = self.packet_decode(pkt)
        
        if pkt_fields is None or pkt_fields['ip_protocol']==-1:
            return
            
        self.packet_in_num += 1
        # Add hosts to the net graph
        if pkt_fields['ip_src'] not in self.net:
            print ('add '+ pkt_fields['ip_src'])
            self.net.add_node(pkt_fields['ip_src'])
            self.net.add_edge(dpid, pkt_fields['ip_src'], port=in_port)
            self.net.add_edge(pkt_fields['ip_src'], dpid)
            
        # 
        if pkt_fields['ip_protocol'] == self.REGISTER_PROTOCOL:
            if pkt_fields['mpls_label']==self.HELLO_LABEL:
                print('add switch %i as an ICN switch' %dpid)
                self.icn_switches.append(dpid)
                self.switch_features_handler(ev)
            else:
                print ('New data registration in %i' % dpid)
                self.RIB.add(pkt_fields['mpls_label'],pkt_fields['ip_src'],pkt_fields['eth_src'])

            return

        # install a flow(role) to avoid packet_in next time
        # Interest packets
        if pkt_fields['ip_protocol'] == self.INTEREST_PROTOCOL:
        # if dst_port == self.INTEREST_PORT:
            """
            Interest packets has special ip_protocol number (150)
            If ip_protocol == 150 -> Interest packet
            """
            print ('New interest in %i ' % dpid )
            if (pkt_fields['mpls_label']>0):
                out = self.create_mpls_datapath(msg, pkt_fields)
            else:
                print('packet flow_id: ', pkt_fields['ip_dst'])
                path = self.lookup_flow_id_path(pkt_fields['ip_dst'])
                out = self.create_ndn_datapath(msg, pkt_fields,pkt_fields['ip_dst'],path)
                
            datapath.send_msg(out)

        elif pkt_fields['ip_protocol'] == self.DATA_PROTOCOL:
            """
            Data packets has special ip_protocol number (151)
            If ip_protocol == 151 -> Data packet
            """
            print ('New data in %i' % dpid)
            print ('in_port:',in_port)
            
        
        elif pkt_fields['ip_protocol'] != -1:
            """
            Other packets forward normally based on SDN
            """
            print ('Not NDN packet %i' % dpid)
            # self.logger.info("s%s from:%s to:%s sport:%s dport:%s",
            #                  dpid, et_src, et_dst, in_port, out_port)
            out = self.create_legacy_datapath(msg,pkt_fields)
            if out is not None:
                datapath.send_msg(out)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        s_id = ev.switch.dp.id        
        print('new switch:',s_id)
        links_list = get_link(self,s_id)
        while(len(links_list)==0):
            links_list = get_link(self,s_id)
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no})
                 for link in links_list]
        print (links)
        self.links.extend(links)
        self.switches.append(s_id)
        print('all links')
        print(self.links)
        self.net.add_nodes_from(self.switches)
        self.net.add_edges_from(self.links)
        
#        switches = get_switch(self.topology_api_app, None)
#        links_list = get_link(self.topology_api_app,None)
##        print (links_list)
#        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no})
#                 for link in links_list]
##        print(switches)
#        print(links)
#        self.net.add_nodes_from(switches)
#        self.net.add_edges_from(links)

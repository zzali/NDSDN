# -*- coding: utf-8 -*-
"""
Created on Fri May 26 16:04:49 2017

@author: root
"""
from __future__ import print_function
import ryufunc
import time
import threading 
from optparse import OptionParser

TIME_INTERVAL=float(10) #s
OUT_PATH='./Out/'

def get_tx_rx_switch(s_dpid):
    desc = ryufunc.get_port_stats(s_dpid)
    in_bytes=0
    out_bytes=0
    in_packs=0
    out_packs=0
    SH_in_bytes = SH_out_bytes = SH_in_packs = SH_out_packs = 0
    for item in desc[str(s_dpid)]:
        #print(item)
        if item['port_no']==100:
            SH_in_bytes = item['tx_bytes']        
            SH_in_packs = item['tx_packets']        
        elif item['port_no']==101:
            SH_out_bytes = item['rx_bytes']        
            SH_out_packs = item['rx_packets']         
        else:
            out_bytes += item['tx_bytes']        
            out_packs += item['tx_packets']         
            in_bytes += item['rx_bytes']        
            in_packs += item['rx_packets'] 
    return [SH_in_bytes,SH_out_bytes,SH_in_packs, SH_out_packs],[in_bytes,out_bytes,in_packs,out_packs]
    
def dump_in_out_switches_stats(proto):
    s_ids = ryufunc.get_switches()
    SH_pre=dict()
    others_pre=dict()
    SH_rate_f=dict()
    others_rate_f=dict()
    opath = OUT_PATH + proto +'/'
    for s in s_ids:
        print(s)
        SH_pre.setdefault(s,[0,0,0,0])
        others_pre.setdefault(s,[0,0,0,0])
        SH_rate_f.setdefault(s, opath+str(s)+'_SH_rate')
        f = open(SH_rate_f[s],'w')
        f.close()
        others_rate_f.setdefault(s, opath+str(s)+'_switch_rate')
        f = open(others_rate_f[s],'w')
        f.close()
    time.sleep(60)
    while True:
        time.sleep(TIME_INTERVAL)
        for s in s_ids:
            SH,others = get_tx_rx_switch(s)
            SH_rate=[]
            others_rate=[]
            for i in range(4):
                SH_rate.append((SH[i]-SH_pre[s][i])/TIME_INTERVAL)
                others_rate.append((others[i]-others_pre[s][i])/TIME_INTERVAL)
            f=open(SH_rate_f[s],'a')
            print (str(SH_rate[0]/float(1000))+ ' ' + str(SH_rate[1]/float(1000)) + ' ' + str(SH_rate[2]) + ' ' + str(SH_rate[3]),file=f)#in_bytes out_bytes in_packets out_packets
            f.close()
            f=open(others_rate_f[s],'a')
            print (str(others_rate[0]) + ' ' + str(others_rate[1]) + ' ' + str(others_rate[2]) + ' ' + str(others_rate[3]),file=f)#in_bytes out_bytes in_packets out_packets            
            f.close()
            SH_pre[s] = SH
            others_pre[s] = others
            
#            print('SH stats in ',s_id, ': ', SH_in_bytes,SH_out_bytes,SH_in_packs, SH_out_packs)
#            print('switch stats in ',s_id, ': ', in_bytes,out_bytes,in_packs,out_packs)
#            print('--------------------------------------------------------------------')

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-p", "--protocol", dest="protocol",
                      help="protocol(udp,tcp,icn)")
    (options, args) = parser.parse_args()
    
    dump_t = threading.Thread(target=dump_in_out_switches_stats, args=(options.protocol,))
    dump_t.start()
            
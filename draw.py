# -*- coding: utf-8 -*-
"""
Created on Fri May 26 18:02:10 2017

@author: root
"""
from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib import font_manager
import ryufunc
import numpy as np
from optparse import OptionParser
import log
import collections

OUTPATH='./Out/'
LINESTYLES=['-', '--','-.', ':',' ']
MARKERS=['.','s','d','x','p','o','P']
COLORS=['b', 'r', 'b', 'c', 'm', 'y', 'k']
OUTPUT_PATH='./Out/'

def octaveAverage(vector, max_count):
    avg = []
    x=[1,3,6,12,24,48,96,192,384,768,1500]
    max_class=0
    while x[max_class]<=max_count:
        max_class += 1
    print (max_class)
    for i in range(1,max_class+1):
        if i==1:
           a=1;
           b=1;
        elif i==2:
           a=2;
           b=4;
        elif i==3:
           a=4;
           b=8;  
        elif i==4:
           a=9;
           b=16;  
        elif i==5:
           a=17;
           b=32;  
        elif i==6:
           a=33;
           b=64;  
        elif i==7:
           a=65;
           b=128;  
        elif i==8:
           a=129;
           b=256; 
        elif i==9:
           a=257;
           b=512;  
        elif i==10:
           a=513;
           b=1000; 
        elif i==11:
           a=1001;
           b=1500; 
           
        temp=[vector[j-1] for j in range(a,min(b+1,max_count)) if vector[j-1]!=None]
        #if i==9:
        #    print(temp) 
        if len(temp)>0:
            avg.append((sum(temp)/float(len(temp))))
        else:
            avg.append(0)
        #print (round(avg[i-1],2))
    return avg,x[0:max_class]


def draw(data_x,data_y,x_label,y_label,xtick, legend, color, linestyle, marker, fig_name,out_path):
    plt.ion()
    fig, ax = plt.subplots()
    plt.gcf().subplots_adjust(bottom=0.1)
    plt.gcf().subplots_adjust(left=0.1)
    ticks_font = font_manager.FontProperties(family='sans-serif', style='normal',\
                    size=10, weight='normal', stretch='normal')
    for label in ax.get_xticklabels():
        label.set_fontproperties(ticks_font)
    for label in ax.get_yticklabels():
        label.set_fontproperties(ticks_font)   
   
    n = len(data_y)
    diag=[]
    for i in range(n):
        if len(data_y[i])==0:
            return
        diag.append(ax.plot(data_x[i] , data_y[i] ,color= color[i], linestyle=linestyle[i],marker=marker[i],linewidth = 3,label=legend[i]))
#        print(data_x[i])
#        print(data_y[i])
    #ax.set_xscale('log')
    ax.set_xlabel(x_label,fontsize=10)
    ax.set_ylabel(y_label,fontsize=10)
    n = len(data_x[0])
    plt.xticks(xtick)
    ax.legend(loc=0,fontsize=14) 
    print(legend)
    fig.savefig(out_path + fig_name+ '.pdf',format='PDF',dpi=5)
    
def load_rate_stats(file_path):
    f = open(file_path)
    line = f.readline().rstrip()
    bit_rate_in=[]
    bit_rate_out=[]
    pack_rate_in=[]
    pack_rate_out=[]
    while(line):
        items = line.split(' ')
        bit_rate_in.append(float(items[0])/10000)
        bit_rate_out.append(float(items[1])/10000)
        pack_rate_in.append(float(items[2])/1000000)
        pack_rate_out.append(float(items[3])/1000000)
        line = f.readline().rstrip()
    return bit_rate_in, bit_rate_out, pack_rate_in, pack_rate_out
        
def plot_rate_stats(proto):
    s_ids = ryufunc.get_switches()
    for s in s_ids:
        x_bit, y_bit, x_pack, y_pack = load_rate_stats(OUTPATH+str(s)+'_SH_rate_'+'icn')
        x_bit_udp, y_bit_udp, x_pack_udp, y_pack_udp = load_rate_stats(OUTPATH+str(s)+'_SH_rate_'+'udp')
        draw([x_bit,x_bit_udp],[y_bit,y_bit_udp], 'Input byte rate per second', 'Output byte rate per second',['test','ideal'], ['b','r'], ['-.','-'], ['','.'], str(s)+'_SH_bitrate_'+proto)
        draw([x_pack,x_pack_udp],[y_pack,y_pack_udp], 'Input packet rate per second', 'Output packet rate per second',['test','ideal'], ['b','r'], ['-.','-'], ['','.'], str(s)+'_SH_packrate_'+proto)
        
        x_bit, y_bit, x_pack, y_pack = load_rate_stats(OUTPATH+str(s)+'_switch_rate_'+'icn')
        x_bit_udp, y_bit_udp, x_pack_udp, y_pack_udp = load_rate_stats(OUTPATH+str(s)+'_switch_rate_'+'udp')
        draw([x_bit,x_bit_udp],[y_bit,y_bit_udp], 'Input byte rate per second', 'Output byte rate per second',['test','ideal'], ['b','r'], ['-.','-'], ['','.'], str(s)+'_switch_bitrate_'+proto)
        draw([x_pack,x_pack_udp],[y_pack,y_pack_udp], 'Input packet rate per second', 'Output packet rate per second',['test','ideal'], ['b','r'], ['-.','-'], ['','.'], str(s)+'_switch_packrate_'+proto)
        
def read_RT_delay(host_id, proto):
    f = open(OUTPATH+str(host_id)+'_log_'+proto+'.txt')
    RT=dict()
    delay=dict()
    line = f.readline().rstrip()
    while line:
        if line.startswith('download complete for :'):
            fields=line.split(':')
            if proto=='icn':
                delay.setdefault(int(fields[1]),[]).append(float(fields[2]))
                print(float(fields[3]))
                RT.setdefault(int(fields[1]),[]).append(float(fields[3]))
            else:
                RT.setdefault(int(fields[1]),[]).append(float(fields[2]))
        line = f.readline().rstrip()
    if proto=='icn':
        for key in delay.keys():
            delay[key] = sum(d for d in delay[key])/float(len(delay[key]))
    for key in RT.keys():
        RT[key] = sum(r for r in RT[key])/float(len(RT[key]))
    print('RT average:', sum(RT.values())/float(len(RT)))
    return RT, delay
   
def plot_SH_processT():
    res = log.read_corresponding_times('SH_process_s','SH_process_e')
    draw([range(1,len(res)+1)],[res],'content ID','time (ms)',['icn'], ['r'], ['-'], ['.'], 'SH_process')
    
#def plot_delay(protocol, host_id, delay_dict):
#    x = np.arange(len(delay_dict.keys()))        
#    y = np.array(delay_dict.values()).astype(np.float)
#    y_mask = np.isfinite(y)
#    draw([x[y_mask]],[y[y_mask]], 'Content IDs', 'Hop Count',[''], ['b'], ['-'], ['.'], str(host_id)+'_'+protocol+'_delay')    
    
def plot_RT(protocol, host_ids,out_path):
    res=dict()
    x=dict()
    xtick=[200,400,600,800,1000,1200,1400,1600]
    for h in host_ids:
        items_main = log.read_corresponding_extra(out_path+protocol+'_down_time_'+h+'_s',out_path+protocol+'_down_time_'+h+'_e')
        items = collections.OrderedDict(sorted(items_main.items()))
        print(items_main)
        print(items)
        print('')
        print(items.values())
        print('')
        print(items.keys())
        print('')
        res.update({h:items.values()})
        x.update({h:items.keys()})
    draw(x.values(),res.values(),'content ID','time (s)',xtick,res.keys(), COLORS[:len(x)], LINESTYLES[:len(x)], MARKERS[:len(x)], 'down_time_'+protocol,out_path)
    
def plot_RT_topo(host_ids,out_path):
    res=dict()
    x=dict()
    for h in host_ids:
       
        items_main = log.read_corresponding_extra(out_path+'icn/down_time_'+h+'_s',out_path+'icn/down_time_'+h+'_e')
        items = collections.OrderedDict(sorted(items_main.items()))
        value,key = octaveAverage(items.values(),max(items.keys()))
        res.update({'icn':value})
        x.update({'icn':key})
        
        items_main = log.read_corresponding_extra(out_path+'noicn/down_time_'+h+'_s',out_path+'noicn/down_time_'+h+'_e')
        items = collections.OrderedDict(sorted(items_main.items()))
        value,key = octaveAverage(items.values(),max(items.keys()))
        res.update({'noicn':value})
        x.update({'noicn':key})
     
        xtick = key
        draw(x.values(),res.values(),'content ID','time (s)',xtick,x.keys(), COLORS[:len(x)], LINESTYLES[:len(x)], MARKERS[:len(x)], 'down_time_'+h,out_path)
    #['']*len(x)

def plot_delay(out_path, host_id):
    res=dict()
    x=dict()
    
    temp = log.read_corresponding_extra('./Out/icn/'+'delay_int_s','./Out/icn/'+'delay_int_e')
    value,key = octaveAverage(temp.values(), max(temp.keys()))
    res.update({'icn':value})
    x.update({'icn':key})
    temp = log.read_corresponding_extra('./Out/noicn/'+'delay_int_s','./Out/noicn/'+'delay_int_e')
    value,key = octaveAverage(temp.values(), max(temp.keys()))
    res.update({'noicn':value})
    x.update({'noicn':key})    
    draw(x.values(),res.values(),'content ID','time (s)',key,x.keys(), COLORS[:len(x)], LINESTYLES[:len(x)], MARKERS[:len(x)], 'delay_int',out_path)
    ##
#    res=dict()
#    x=dict()
#    res.update({host_id:log.read_corresponding_times('./Out/icn/'data_s',out_path+'delay_data_e')})
#    x.update({host_id:range(1,len(res[host_id])+1)})
#    res.update({host_id:log.read_corresponding_times(OUTPUT_PATH+'noicn_delay_data_s',out_path+'delay_data_e')})
#    x.update({host_id:range(1,len(res[host_id])+1)})
#    draw(x.values(),res.values(),'content ID','time (s)',['Interest','Data'], COLORS[:len(x)], LINESTYLES[:len(x)], MARKERS[:len(x)], 'delay_data',out_path)
    
def plot_hop(protocol, host_ids,out_path):
    res=dict()
    x=dict()
    for h in host_ids:
        info = log.read_corresponding_extra(out_path+protocol+'_hop_count_'+h)
        res.update({h:info.values()})
        x.update({h:info.keys()})
    
    draw(x.values(),res.values(),'content ID','hop count',res.keys(), COLORS[:len(x)], ['']*len(x), MARKERS[:len(x)], 'hop_count_'+protocol,out_path)
    
def plot_controller_rate(out_path):
    f = open(out_path+'controller_log')
    r = f.readline().rstrip()
    rates=[]
    while r:
        rates.append(float(r))
        r = f.readline()
    x = range(1,len(rates)+1)
    xtick = x[1:len(x):len(x)/10]
    draw([x],[rates],'time','packet-in rate per second',xtick,[''], ['b'], ['-'], ['o'], 'controller_rate', out_path)
    
def plot_SH_rate(out_path):
    for s in range(1,4):
        sh = str(s)
        f = open(out_path+sh+'_SH_rate')
        r = f.readline().rstrip()
        rates = []
        rates.append([])
        rates.append([])        
        while r:
            fields = r.split()
            rates[0].append(float(fields[0]))
            rates[1].append(float(fields[1]))
            r = f.readline()
        x = [range(1,len(rates[0])+1)]
        x.append(range(1,len(rates[1])+1))
        xtick = x[0][1:len(x[0]):len(x[0])/10]
        draw(x,rates,'time','Byte per second',xtick,['Input','Output'], ['b','k'], ['-','-.'], ['o','s'], 'sh_rate_'+sh, out_path)
    
    
#def plot_RT(protocol, host_id, RT_dict):
#    x = np.arange(len(RT_dict.keys()))        
#    y = np.array(RT_dict.values()).astype(np.float)
#    y_mask = np.isfinite(y)
#    draw([x[y_mask]],[y[y_mask]], 'Content IDs', 'RT (ms)',[''], ['b'], ['-'], ['.'], str(host_id)+'_'+protocol+'_RT')    
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--host", dest="host_id",
                      help="Host ID")
#    parser.add_option("-o", "--outpath", dest="outpath",
#                      help="outpath")
    (options, args) = parser.parse_args()
    host_ids = options.host_id.split(',')
#    out_path=options.outpath if options.outpath else OUTPATH
#    plot_RT(options.protocol, host_ids ,out_path)
#    plot_hop(options.protocol, host_ids, out_path)
    plot_controller_rate('./Out/icn/')
    
    plot_RT_topo(host_ids,'./Out/')
    #plot_SH_rate(out_path)
    plot_delay('./Out/', host_ids[0])
    


    #RT, delay = read_RT_delay(host_id, options.protocol)
    #if options.protocol=='icn':
        #plot_delay(options.protocol,host_id,delay)
    #    plot_rate_stats(options.protocol)

    #plot_SH_processT(options.protocol, host_id)
    
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
import commands

OUTPATH='./Out/'
LINESTYLES=['-', '--','-.', ':',' ']
MARKERS=['.','s','d','x','p','o','P']
COLORS=['b', 'r', 'g', 'c', 'm', 'y', 'k']
OUTPUT_PATH='./Out/'

def octaveAverage(vector, max_count):
    avg = []
    x=[1,3,6,12,24,48,96,192,384,768,1500]
    
    max_class=0
    while x[max_class]<=max_count:
        max_class += 1
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
    
        if len(temp)>0:
            avg.append((sum(temp)/float(len(temp))))
        else:
            avg.append(0)
       
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

    ax.set_xlabel(x_label,fontsize=10)
    ax.set_ylabel(y_label,fontsize=10)
    n = len(data_x[0])
    plt.xticks(xtick)
    ax.legend(loc=0,fontsize=14) 

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
        
     
  
    
def compute_avg_RT(host_ids,exp,failedDL, smpl):
    for h in host_ids:
        icn_down_s_f = './Out/icn/'+exp+'/'+smpl+'/down_time_'+h+'_s'
        icn_down_e_f = './Out/icn/'+exp+'/'+smpl+'/down_time_'+h+'_e'
        noicn_down_s_f = './Out/noicn/'+exp+'/'+smpl+'/down_time_'+h+'_s'
        noicn_down_e_f = './Out/noicn/'+exp+'/'+smpl+'/down_time_'+h+'_e'
        
        if failedDL:
            items_main_icn, items_main_noicn  = log.read_corresponding_download_withFailed(icn_down_s_f, icn_down_e_f, noicn_down_s_f, noicn_down_e_f)
        else:
            items_main_icn = log.read_corresponding_extra(icn_down_s_f, icn_down_e_f)
            items_main_noicn = log.read_corresponding_extra(noicn_down_s_f, noicn_down_e_f)
        
        items_icn = collections.OrderedDict(sorted(items_main_icn.items()))

        value,key = octaveAverage(items_icn.values(),max(items_icn.keys()))
        f = open('./Out/icn/' + options.exp + '/for_plot/' + smpl_str + '/down_time_'+h, 'w')
        for i in range(len(key)):            
            f.write(str(key[i])+ ' ' +str(value[i]) +'\n')
        f.close()
        items_noicn = collections.OrderedDict(sorted(items_main_noicn.items()))

        value,key = octaveAverage(items_noicn.values(),max(items_noicn.keys()))
        f = open('./Out/noicn/' + options.exp + '/for_plot/' + smpl_str + '/down_time_'+h, 'w')
        for i in range(len(key)):            
            f.write(str(key[i])+ ' ' +str(value[i]) +'\n')
        f.close()
 

def compute_avg_delay(host_ids, exp, failedInt, smpl):
    for h in host_ids:
        icn_delay_s_f = './Out/icn/'+exp+'/'+smpl+'/delay_int_'+h+'_s'
        icn_delay_e_f = './Out/icn/'+exp+'/'+smpl+'/delay_int'+'_e_'+h
        noicn_delay_s_f = './Out/noicn/'+exp+'/'+smpl+'/delay_int_'+h+'_s'
        noicn_delay_e_f = './Out/noicn/'+exp+'/'+smpl+'/delay_int'+'_e_' +h
        
        if failedInt:
            temp = log.read_corresponding_delay_withFailed(icn_delay_s_f, icn_delay_e_f)
        else:
            temp = log.read_corresponding_extra(icn_delay_s_f, icn_delay_e_f)
        value,key = octaveAverage(temp.values(), max(temp.keys()))
        f = open('./Out/icn/' + options.exp + '/for_plot/' +  smpl_str + '/delay_' + h, 'w')
        for i in range(len(key)):            
            f.write(str(key[i])+ ' ' +str(value[i]) +'\n')
        f.close()
        if failedInt:    
            temp = log.read_corresponding_delay_withFailed(noicn_delay_s_f, noicn_delay_e_f)
        else:
            temp = log.read_corresponding_extra(noicn_delay_s_f, noicn_delay_e_f)
        value,key = octaveAverage(temp.values(), max(temp.keys()))
        f = open('./Out/noicn/' + options.exp + '/for_plot/' +  smpl_str + '/delay_' + h, 'w')
        for i in range(len(key)):            
            f.write(str(key[i])+ ' ' +str(value[i]) +'\n')
        f.close()

    
def compute_avg_hop(host_ids, exp, smpl):

    smpl_str = str(smpl)
    for h in host_ids:
        icn_hop_f = './Out/icn/'+exp+'/'+smpl+'/hop_count_'+ h
        noicn_hop_f = './Out/noicn/'+exp+'/'+smpl+'/hop_count_'+ h
                
        info = log.read_corresponding_extra(icn_hop_f)
        value,key = octaveAverage(info.values(), max(info.keys()))
        with open('./Out/icn/' + options.exp +  '/for_plot/'  + smpl_str + '/hop_'+ h, 'w') as f:
            for i in range(len(key)):            
                f.write(str(key[i])+ ' ' +str(value[i]) +'\n')
                
        info = log.read_corresponding_extra(noicn_hop_f)
        value,key = octaveAverage(info.values(), max(info.keys()))
        with open('./Out/noicn/' + options.exp + '/for_plot/' + smpl_str + '/hop_'+ h, 'w') as f:
            for i in range(len(key)):            
                f.write(str(key[i])+ ' ' +str(value[i]) +'\n')
    
def plot_controller_rate(exp, smpl):
    out_path = './Out/icn/' + exp + '/' + smpl + '/'
    f = open(out_path+'controller_log')
    r = f.readline().rstrip()
    rates=[]
    while r:
        rates.append(float(r))
        r = f.readline()
    
def get_avg_of_smpls(path, file_name):
    values = dict()
    for smpl in range(1,smpl_num + 1):
        f = open(path + str(smpl) + '/' + file_name, 'r')
        line_str = f.readline().rstrip()
        while line_str:
            fields = line_str.split()
            x = int(fields[0])
            if x in values.keys():
                values[x] += float(fields[1])
            else:
                values.update({x:float(fields[1])})
            line_str = f.readline().rstrip()
            
    for x in values.keys():
        values[x] = values[x]/float(smpl_num)
    return collections.OrderedDict(sorted(values.items())) 
    
def plot(file_name, exp, smpl_num, y_label, diagram_name):
    dgrm_x = dict()
    dgrm_y = dict()
    values = get_avg_of_smpls('./Out/icn/'+options.exp+'/for_plot/', file_name)
    dgrm_x.update({'icn':values.keys()})
    dgrm_y.update({'icn':values.values()})
    values = get_avg_of_smpls('./Out/noicn/'+options.exp+'/for_plot/', file_name)
    dgrm_x.update({'noicn':values.keys()})
    dgrm_y.update({'noicn':values.values()})
          
    commands.getstatusoutput('mkdir -p ./Out/plots/'+exp)
    draw(dgrm_x.values(), dgrm_y.values(),'content ID',y_label, dgrm_x['icn'], dgrm_x.keys(), COLORS[:2], ['-']*2, MARKERS[:2], diagram_name ,'./Out/plots/'+exp+'/')

    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--host", dest="host_id",
                      help="Host ID")
    parser.add_option("-f", "--withFailed", dest="withFailed",
                      help="considering failed interests or downloads")
    parser.add_option("-e", "--experiment", dest="exp",
                      help="experiment_name")
    parser.add_option("-s", "--sample", dest="smpl_num",
                      help="sample_num")

    (options, args) = parser.parse_args()
    host_ids = options.host_id.split(',')

       
    if options.withFailed=='yes':
        failed = True
    else:
        failed = False
       
    smpl_num = int(options.smpl_num)
  
    #compute average of each parameter for some content sets according to octave_avg
    for smpl in range(1,smpl_num+1):
        smpl_str = str(smpl)
        commands.getoutput('mkdir -p ./Out/icn/' + options.exp + '/for_plot/' + smpl_str + '/')
        commands.getoutput('mkdir -p ./Out/noicn/' + options.exp + '/for_plot/' + smpl_str + '/')
        compute_avg_RT(host_ids, options.exp, failed, smpl_str)
        compute_avg_delay(host_ids, options.exp, failed, smpl_str)
        
    #compute the average of each parameter for all the samples and plot the average diagram
    for h in host_ids:    
        plot('delay_'+h, options.exp, smpl_num, 'Average delay (s)', 'delay_' + h )
        plot('down_time_'+h, options.exp, smpl_num, 'Average download time (s)' , 'down_time_' + h )
    
    #RT, delay = read_RT_delay(host_id, options.protocol)
   
    
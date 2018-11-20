# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 17:35:23 2017

@author: Zeinab Zali
"""
from __future__ import print_function
from stats_zipf import TruncatedZipfDist
import random 
import numpy as np
import os

PATTERN_PATH = './Requests/'
REPO_PATH = './content_files/'
SAMPLE_NUM = 50
CONTENTS_NUM = 300
CONTENT_SIZE = 10000 #10KB
SWITCH_IDs = [1,2]
PUBLISHERS = [66]
REQ_RATE = float(1)/1000
ALPHA = 0.8

def get_zipf_prob(alpha, n_contents):
    ret = []
    H_zipf = 0
    for n in range(1,n_contents+1):
        H_zipf = H_zipf + (1/n**alpha);
     
    for n in range(1,n_contents+1):
        ret.append((1/( (n**alpha) * H_zipf)))
    return ret
    

if __name__=='__main__':

    P_zipf = get_zipf_prob(ALPHA , CONTENTS_NUM)
    duration = 1/(REQ_RATE*P_zipf[CONTENTS_NUM-1]);      #each content is requestes at least one time
    print (duration)
    req_num = int(REQ_RATE * duration);
    print(req_num)
    for s in SWITCH_IDs:
        reqf = open(PATTERN_PATH + 'requests_' + str(s),'w');
        reqf.close()
    #content files
    for i in range(1,CONTENTS_NUM+1):
        f=open(REPO_PATH+str(i),'w')
        for j in range(CONTENT_SIZE/2):
            print(j%10,file=f)
        f.close()
    #publishers files
    p_num = len(PUBLISHERS)
    p_file = []
    for p in PUBLISHERS:
        p_file.append(open(REPO_PATH+'files'+str(p),'w'))
    d = CONTENTS_NUM / len(PUBLISHERS)
    offset = 1
    for f in p_file:
        for c in range(offset,offset+d):
            if c<=CONTENTS_NUM:
                print(c,file=f)
            else:
                break
        e = offset + d
        offset += d
    for f in p_file:
        f.close()
        
    #request files
    for i in range(1,SAMPLE_NUM+1):
        zipf= TruncatedZipfDist(ALPHA, CONTENTS_NUM)
        if not os.path.exists(os.path.dirname(PATTERN_PATH +str(i)+'/')):
            os.makedirs(os.path.dirname(PATTERN_PATH +str(i)+'/'))
        for s in SWITCH_IDs:
            reqf = open(PATTERN_PATH +str(i)+ '/requests_' + str(s),'w');
            for k in range(req_num):
                content = int(zipf.rv())
                print (content,file=reqf)
            reqf.close()
                    
        #request times
        for s in SWITCH_IDs:
            timef = open(PATTERN_PATH +str(i)+'/times_' + str(s),'w');
            e_time = 0
            print('num:',req_num)
            for k in range(req_num):
                interval = int(round((1/REQ_RATE) * abs(np.log(random.uniform(0, 1)))))
                e_time = e_time + interval/float(1000)
                print(interval,file=timef)
            timef.close()
        
    
   
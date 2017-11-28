# -*- coding: utf-8 -*-
"""
Created on Thu May 25 09:43:17 2017

@author: root
"""
from __future__ import print_function
CHUNK_SIZE = 1000
CHUNK_NUM = 100
FILE_NUM = 100
FOLDER_PATH = './content_files/'

fnames=open(FOLDER_PATH+'files','w')
for i in range(1,FILE_NUM+1):
    f=open(FOLDER_PATH+str(i),'w')
    content=str(str(i)[0]*CHUNK_NUM*CHUNK_SIZE)
    print(content,file=f)
    print(i,file=fnames)
    f.close()
fnames.close()

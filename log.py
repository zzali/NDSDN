# -*- coding: utf-8 -*-
import time
import numpy as np
import threading
#from matplotlib.pyplot import plot

class Log():
    def __init__(self, event_name, save_mode):
        self.event_name = event_name
        self.history = []
        #self.saveTime = time.time()
        self.UPDATE_INTERVAL = 300 #300s = 5min
        with open(self.event_name, 'w+') as f:
            f.write('')
            f.close()
        self.history_len = 0
        self.save_mode = save_mode
        self.dump_log_lock = threading.Lock()
        threading.Thread(target=self.dump_log, args=()).start()

    def dump_log(self):
        while(True):
            time.sleep(self.UPDATE_INTERVAL)
            self.dump_log_lock.acquire()
            with open(self.event_name, 'a+') as f:
                for event in self.history:
                    f.write(event + '\n')
                f.close()   
            self.dump_log_lock.release()
            self.history = []
            self.history_len = 0

    def save(self, content_name, chunk_number, extra=''):
        self.history.append('%s,%i,%s%s' % (content_name, chunk_number, extra+',', time.time()))
        self.history_len += 1
        if self.history_len == self.save_mode or self.save_mode == -1 :
            self.dump_log_lock.acquire()
            with open(self.event_name, 'a+') as f:
                for event in self.history:
                    f.write(event + '\n')
                f.close()
            self.dump_log_lock.release()
            self.history = []
            self.history_len = 0
            
def read_corresponding_times(start_file, end_file):
    start_times = [line.split(',') for line in open(start_file).read().split('\n') if line.strip()]
    end_times = [line.split(',') for line in open(end_file).read().split('\n') if line.strip()]

    stime = {}
    for content, chunk, _, t in start_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in stime:
            stime[content].append(t)
        else:
            stime.setdefault(content,[t])
    etime = {}
    for content, chunk, _, t in end_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in etime:
            etime[content].append(t)
        else:
            etime.setdefault(content,[t])
    #diffs = []
    diffs = dict()
    max_countent = 0
    for c in etime:
        summ = 0
        #print (c)
        for i in range(len(etime[c])):
            summ += etime[c][i]-stime[c][i]
        if int(c)>max_countent:
            max_countent = int(c)
        diffs.setdefault(c,summ/float(len(etime[c])))
    #print diffs
    for c in range(1,max_countent+1):
        if c in diffs:
            #print(c,diffs[c])
            continue
        else:
            diffs.setdefault(c,None)
    
    return diffs


def read_corresponding_extra(start_file,end_file):
    start_times = [line.split(',') for line in open(start_file).read().split('\n') if line.strip()]
    end_times = [line.split(',') for line in open(end_file).read().split('\n') if line.strip()]
    stime = {}
    for content, chunk, e_id, t in start_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in stime:
            stime[content].setdefault(e_id,t)
        else:
            stime.setdefault(content,dict({e_id:t}))
    etime = {}
    for content, chunk, e_id, t in end_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in etime:
            etime[content].setdefault(e_id,t)
        else:
            etime.setdefault(content,dict({e_id:t}))
    #diffs = []
    diffs = dict()
    max_countent = 0
    for c in etime:
        summ = 0
        cnt = 0
        if c in stime:
            for e in etime[c]:
                if e in stime[c]: 
                    summ += etime[c][e]-stime[c][e]
                    cnt += 1
        if int(c)>max_countent:
            max_countent = int(c)
        diffs.setdefault(c,summ/float(cnt))
    #print diffs
    for c in range(1,max_countent+1):
        if c in diffs:
            #print(c,diffs[c])
            continue
        else:
            diffs.setdefault(c,None)
    
    return diffs
    
# same as read_corresponding_extra except that failed interests (if lifetime expired) and downloads (if timeout expired) 
# are considered in computing the average
def read_corresponding_delay_withFailed(start_file,end_file):
    lifetime = 0.2
    start_times = [line.split(',') for line in open(start_file).read().split('\n') if line.strip()]
    end_times = [line.split(',') for line in open(end_file).read().split('\n') if line.strip()]
    stime = {}
    for content, chunk, e_id, t in start_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in stime:
            stime[content].setdefault(e_id,t)
        else:
            stime.setdefault(content,dict({e_id:t}))
    etime = {}
    for content, chunk, e_id, t in end_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in etime:
            etime[content].setdefault(e_id,t)
        else:
            etime.setdefault(content,dict({e_id:t}))
    #diffs = []
    diffs = dict()
    max_countent = 0
    for c in etime:
        summ = 0
        cnt = 0
        if c in stime:
            for e in stime[c]:
                if e in etime[c]: 
                    summ += etime[c][e]-stime[c][e]
                else:
                    summ += lifetime
                cnt += 1
        if int(c)>max_countent:
            max_countent = int(c)
        diffs.setdefault(c,summ/float(cnt))
    #print diffs
    for c in range(1,max_countent+1):
        if c in diffs:
            #print(c,diffs[c])
            continue
        else:
            diffs.setdefault(c,None)
    
    return diffs
    
def read_dl_info(start_file, end_file):
    timeout = 1
    start_times = [line.split(',') for line in open(start_file).read().split('\n') if line.strip()]
    end_times = [line.split(',') for line in open(end_file).read().split('\n') if line.strip()]
    stime = {}
    for content, chunk, e_id, t in start_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in stime:
            stime[content].setdefault(e_id,t)
        else:
            stime.setdefault(content,dict({e_id:t}))
    etime = {}
    for content, chunk, e_id, t in end_times:
        content = int(content)
        chunk = int(chunk)
        t = float(t)
        if content in etime:
            etime[content].setdefault(e_id,t)
        else:
            etime.setdefault(content,dict({e_id:t}))
    return stime, etime
    #diffs = []
#    diffs = dict()
#    max_countent = 0
#    with open(start_file+'_success', 'a+') as f:    
#        for c in etime:
#            summ = 0
#            cnt = 0
#            if c in stime:
#                for e in stime[c]:
#                    if e in etime[c]: 
#                        summ += etime[c][e]-stime[c][e]
#                        f.write(e + ' ' + str(c )+ ': ' + str(etime[c][e]-stime[c][e]) + '\n')
#                    else:
#                        summ += timeout
#                    cnt += 1
#            if int(c)>max_countent:
#                max_countent = int(c)
#            diffs.setdefault(c,summ/float(cnt))
#    f.close()
    
def read_corresponding_download_withFailed(start_file_icn,end_file_icn, start_file_noicn,end_file_noicn):
    timeout = 1
    stime_icn, etime_icn = read_dl_info(start_file_icn, end_file_icn)
    stime_noicn, etime_noicn = read_dl_info(start_file_noicn, end_file_noicn)
    
    max_countent = 0
    diffs_icn = dict()
    diffs_noicn = dict()
    for c in stime_icn:
        summ_icn = 0
        summ_noicn = 0
#        cnt_icn = 0
#        cnt_noicn = 0
        cnt = 0
        if c in etime_icn:
            for e in stime_icn[c]:
                if e in etime_icn[c] and e in etime_noicn[c]: 
                    d1 = etime_icn[c][e]-stime_icn[c][e]
                    d2 = etime_noicn[c][e]-stime_noicn[c][e]
                    if d2<timeout and d1 <timeout:
                        summ_noicn += d2
                        summ_icn += d1
                        cnt +=1
            
        if cnt >0:
            diffs_icn.setdefault(c,summ_icn/float(cnt))
            diffs_noicn.setdefault(c,summ_noicn/float(cnt))
            if int(c) > max_countent:
                max_countent = int(c)
    #print diffs
    for c in range(1,max_countent+1):
        if c not in diffs_icn:
            diffs_icn.setdefault(c,None)
            
        if c not in diffs_noicn:
            diffs_noicn.setdefault(c,None)
   
    return diffs_icn, diffs_noicn
        
#if __name__ == '__main__':
#    r = read_corresponding_times('./Out/ndn data generated', './Out/ndn data received')
#    plot(r)
    
    
    
    
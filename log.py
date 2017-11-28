# -*- coding: utf-8 -*-
import time
import numpy as np
import threading
#from matplotlib.pyplot import plot

class Log():
    def __init__(self, event_name, save_mode):
        self.event_name = event_name
        self.history = []
        self.saveTime = time.time()
        
        with open(self.event_name, 'w+') as f:
            f.write('')
            f.close()
        self.history_len = 0
        self.save_mode = save_mode
        self.dump_log()
        
    def dump_log(self):
        with open(self.event_name, 'a+') as f:
            for event in self.history:
                f.write(event + '\n')
            f.close()
        self.history = []
        self.history_len = 0
        threading.Timer(60, self.dump_log).start()
        

    def save(self, content_name, chunk_number, extra=''):
        self.history.append('%s,%i,%s%s' % (content_name, chunk_number, extra+',', time.time()))
        self.history_len += 1
        if self.save_mode == -1 or self.history_len == self.save_mode :
            with open(self.event_name, 'a+') as f:
                for event in self.history:
                    f.write(event + '\n')
                f.close()
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
            print(c,diffs[c])
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
            print(c,diffs[c])
            continue
        else:
            diffs.setdefault(c,None)
    
    return diffs
        
#if __name__ == '__main__':
#    r = read_corresponding_times('./Out/ndn data generated', './Out/ndn data received')
#    plot(r)
    
    
    
    
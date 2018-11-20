# NDSDN
Implementing NDN using SDN

The required steps for executing a sample experiment are described at the following.

0- A powerfull computer is required for executing the emulation, especially the CPU power and the maximum number of concurrent threads it supports are important. 

1- install mininet and Ryu controller and download NDSDN source files. Extract the folder and cd to the base folder.

2- Content files are in the content_files folder of the main folder. The content files are named with numbers and each one is assumed to be 10 KB. 

3- You can generate request files by executing:
   #python gen_requests.py
    It generates 50 samples of 1075 requests files from two consumers that requests 300 various content files. There is a publisher who publishes all the 300 files (you can change the default values in the file: SAMPLE_NUM, CONTENTS_NUM, CONTENT_SIZE, CONSUMERS_IDs, PUBLISHERS_IDS)

4- The target topology of the switches and hosts is determined in mn_network.py file. It can be changed arbitrary.

5- execute the following command for starting a new experiment:
   #./execute_experiment.sh protocol_name serviceHost2switch_delay switche2switch_delay sample_num
   
   Ex: ./execute_experiment.sh icn 1ms 50ms 20 
       ./execute_experiment.sh noicn 1ms 50ms 20 
   
   Given arguments are defined as:

   a- protocol_name: it can be icn or noicn. If protocol is ICN, network routing, forwarding and caching is performed according to ICN. But if protocol is noicn, no ICN related protocol applied and the requests are replied according to plain IP.

   b- serviceHost2switch_delay: The delay between each switch and its service host. It is assumed to be less than switche2switch_delay

   c- switche2switch_delay: The delay between each two switches

   d- sample_num: The number of repeated execution of the experimnet. 

6- the log files from the experiment are recorded in some files in the <Out> folder in related folders accrding to protocol_name and the delay configuration and sample number.

7- During the execution of each experiment you can see the flow tables in the switches by executing:
   -sudo ovs-ofctl -O OpenFlow14  dump-tables s1
   -sudo ovs-ofctl -O OpenFlow14  dump-flows s1

8- using draw.py, you can see the diagrams:
   #./python draw.py -i consumer_ids -e experiment_name -s sample_num
 
   Ex.: ./python draw.py -i 1,2 -e ds50ms_dsh1ms -s 20
   
   Given arguments are defined as:
   i- consumer_ids: id number of the consumers
   e- experiment_name: It is the folder name of the experiment output in ./Out according to delay configuration  
   s- sample_num: The average diagram is computed from this sample number 




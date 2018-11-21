protocol=$1
delay_sh=$2
delay_sw=$3
smpl_num=$4
exp='ds'$delay_sw'_dsh'$delay_sh

for smpl in `seq 1 $smpl_num`;
do
	if [ ! -d "./Out/"$protocol"/"$exp'/'$smpl'/' ]; then	
		mkdir -p "./Out/"$protocol"/"$exp'/'$smpl'/'

		echo '[netparam]' > myRyu.conf 
		echo '' >> myRyu.conf 
		echo 'exp='\'$exp\' >> myRyu.conf
		echo 'protocol='\'$protocol\' >> myRyu.conf  
		echo 'smpl='\'$smpl\' >> myRyu.conf 

		sudo mn -c 
		sudo ryu-manager --ofp-tcp-listen-port 9999 VICN.py  ryu.app.ofctl_rest --observe-links  --config-file myRyu.conf  > ryu_out &
		sleep 10
		sudo python  mn_network.py -d $delay_sw -e $delay_sh -p $protocol -s $smpl
    fi

done

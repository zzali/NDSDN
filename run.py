from os import system


if __name__ == '__main__':
    system("gnome-terminal --working-directory /home/mehdi/workspace/git/vicn.git/")
           # "-e \"mn --custom topology.py --topo mytopo --controller remote,ip=127.0.0.1," +
           # "port=9999 --switch ovsk,protocols=OpenFlow14 --mac --arp\"")
    system("gnome-terminal --working-directory /home/mehdi/workspace/git/vicn.git/"
           "-e 'ryu-manager --ofp-tcp-listen-port 9999 first.py --observe-links'")

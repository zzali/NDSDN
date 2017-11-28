# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 08:57:33 2016

@author: Zeinab Zali
"""
from optparse import OptionParser
import socket

if __name__ == '__main__':
    REPO_PORT = 5000
    parser = OptionParser()
#    parser.add_option("-a", "--add", dest="add",
#                      help="add a file to repo")
    parser.add_option("-p", "--path",
                      dest="path",
                      help="file complete path")
    parser.add_option("-n", "--name",
                      dest="name",
                      help="content name")
    (options, args) = parser.parse_args()
    if args[0]=='add':
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('127.0.0.1', REPO_PORT)
        sock.connect(server_address)
        file_path = options.path
        content_name = options.name
        msg = (file_path + '|' + content_name).encode()
        sock.send(msg)
        print ('after send')
        sock.close()
        
    


# -*- coding: utf-8 -*-
"""
Created on Wed May 24 22:48:04 2017

@author: root
"""
from optparse import OptionParser
import socket

BUFFER_SIZE = 50

if __name__ == '__main__':
    REPO_PORT = 5000
    parser = OptionParser()
#    parser.add_option("-a", "--add", dest="add",
#                      help="add a file to repo")
    parser.add_option("-p", "--path",
                      dest="path",
                      help="folder path of content files")
    parser.add_option("-r", "--req",
                      dest="req",
                      help="list of requests content name")
    (options, args) = parser.parse_args()

    folder_path = options.path
    contents_file = options.req
    
 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    server_address = ('127.0.0.1', REPO_PORT)
    sock.connect(server_address)
    f = open(folder_path + '/' + contents_file)
    line = f.readline().rstrip()
    while (line):
        file_path = folder_path + '/' + line
        content_name = line
        msg_str = file_path + '|' + content_name
        msg = (msg_str + ' '*(BUFFER_SIZE-len(msg_str))).encode()
        sock.send(msg)
        print ('register content ' + str(content_name))
        line = f.readline().rstrip()
    sock.close()
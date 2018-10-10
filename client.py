import socket
import json
from ThreadPool import *
from collections import OrderedDict

# TCP
# init thread pool & socket server

class Client:

    def __init__(self, _addr='127.0.0.1', _port=9999):
        self.addr = _addr
        self.port = _port

    def registration(self):
        pass

node_id = 0
node_name = 'node01'
idle_cpu = 4

info = {
    'type': 'node info',
    'info': OrderedDict({
        'node_id': node_id,
        'node_name': node_name,
        'idle_cpu': idle_cpu,
    })
}

thread_pool = ThreadPool(100, 4)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))
while True:
    task_str = s.recv(1024).decode('utf-8')
    print(task_str)


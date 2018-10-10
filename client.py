import socket
import json
from ThreadPool import *

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

thread_pool = ThreadPool(100, 4)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))
print(s.recv(1024).decode('utf-8'))
# s.send('come on'.encode('utf-8'))
while True:
    task_str = s.recv(1024).decode('utf-8')
    time.sleep(0.1)
    # task_dict = json.loads(task_str)
    print(task_str)

s.send(b'exit')
s.close()


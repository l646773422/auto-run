import socket
import json
from ThreadPool import *

# TCP
# init thread pool & socket server

node_id = 0
node_name = 'node01'

thread_pool = ThreadPool(100, 4)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))
print(s.recv(1024).decode('utf-8'))
s.send('come on'.encode('utf-8'))

task_str = s.recv(1024).decode('utf-8')
task_dict = json.loads(task_str)

print(task_dict)

s.send(b'exit')
s.close()


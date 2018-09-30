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

data = [
    ['node_id', node_id],
    ['node_name', node_name],
    ['tasks', thread_pool.working_threads()],
    ['total cpu', cpu_count()],
    ['working cpu', 0],
]

json_data = json.dumps(data).encode('utf-8')

s.send(json_data)
print(s.recv(1024).decode('utf-8'))

s.send(b'exit')
s.close()


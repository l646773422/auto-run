import socket
import json
from ThreadPool import *

# TCP
# init thread pool & socket server
thread_pool = ThreadPool(100, 4)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))
print(s.recv(1024).decode('utf-8'))

data = {
    'tasks': thread_pool.working_threads(),
    'test': 0,
}
json_data = json.dumps(data).encode('utf-8')

s.send(json_data)
print(s.recv(1024).decode('utf-8'))

s.send(b'exit')
s.close()


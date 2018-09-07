import socket
import json

# TODO TCP

task_info = json.dumps(
    [
        ['encoder', 'TAppEncoder'],
        ['-c', '1'],
        ['-c', 2],
        ['-i', 3],
        ['-o', 4],
        ['-b', 5],
        ['QP', 5],
        ['FramesToBeEncoded', 6],
        ['InputSampleBitDepth', 6],
        ['SampleBitDepth', 7],
    ]
)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('127.0.0.1', 9999))

print(s.recv(1024).decode('utf-8'))

for data in [task_info, b'hly']:
    s.send(data)
    print(s.recv(1024).decode('utf-8'))

s.send(b'exit')
s.close()

# # TODO UDP
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# for data in [b'llt', b'hly']:
#     s.sendto(data, ('127.0.0.1', 9999))
#     print(s.recv(1024).decode('utf-8'))
#
# s.close()

# encoder = json.JSONEncoder()



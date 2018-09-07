import socket
import threading
import time


# TODO tcp server
def tcplink(sock, addr):
    print('accept new connection from %s %s' % addr)
    print(addr)
    sock.send(b'welcome')
    while True:
        data = sock.recv(1024)
        time.sleep(1)
        if not data or data.decode('utf-8') == 'exit':
            break
        sock.send(('hello, %s' % data.decode('utf-8')).encode('utf-8'))
    sock.close()
    print('connection from %s:%s closed' % addr)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('127.0.0.1', 9999))
s.listen(5)
print('waiting for connection')

while True:
    sock, addr = s.accept()
    t = threading.Thread(target=tcplink, args=(sock, addr))
    t.start()


# # TODO UDP
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.bind(('127.0.0.1', 9999))
# print('bind UDP on 9999 port')
#
# while True:
#     data, addr = s.recvfrom(1024)
#     print('Received from %s:%s' % addr)
#     s.sendto(b'hello, %s!' % data, addr)


# decoder = json.JSONDecoder()
# dd = json.loads('{"a":1,"b":2,"c":3,"d":4,"e":5}')

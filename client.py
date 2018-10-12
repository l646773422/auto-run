import socket
import json
from ThreadPool import *
from func_lib import *
from collections import OrderedDict
from multiprocessing import cpu_count
import select
import hashlib

MAX_BUFFER_SIZE = 1024


class Client:

    def __init__(self, _host='127.0.0.1', _port=9999):
        self.host = _host
        self.port = _port
        self.server = None

        # client info
        self.name = 'node01'
        self.ip = get_host_ip()
        self.total_core = cpu_count()
        self.idle_core = self.total_core
        self.md5 = hashlib.md5()
        self.md5.update((self.name+self.ip).encode('utf-8'))
        self.identifier = str(self.md5.hexdigest())

    def registration(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.host, self.port))

    def to_json(self):
        return json.dumps(OrderedDict(
            type='get info',
            info=OrderedDict(
                total_core=self.total_core,
                idle_core=self.idle_core,
                name=self.name,
                ip=self.ip,
                identifier=self.identifier,
            )
        ))

    def get_msg(self, _readable):
        for _server in _readable:
            try:
                _json = _server.recv(MAX_BUFFER_SIZE)
                _data = json.loads(_json, object_pairs_hook=OrderedDict)

                if _data['type'] == 'get info':
                    client_info = self.to_json().encode('utf-8')
                    _server.send(client_info)
                elif _data['type'] == 'task':
                    # parse task

                    self.idle_core += 1
                    pass
            except ConnectionResetError:
                print('remote server error.')
                exit(1)
            except json.decoder.JSONDecodeError:
                print('wrong json string.')

    def parse_task_dict(self):
        pass

    def listen(self):
        while True:
            time.sleep(0.1)
            readable, writable, exceptional = select.select([self.server], [], [self.server])
            self.get_msg(readable)

if __name__ == '__main__':
    client = Client()
    client.registration()
    client.listen()


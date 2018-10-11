import socket
import threading
import time
import json
import queue
import select
from parallel import *
from func_lib import *
from collections import OrderedDict

MAX_TASK_SIZE = 100
MAX_BUFFER_SIZE = 1024


class Service:

    def __init__(self, _host='127.0.0.1', _port=9999):
        self.node_nums = 0
        self.nodes_info = []
        self.host = _host
        self.port = _port
        self.task_file_name = 'tasks.json'
        self.general_file_name = 'config.json'

        self.spec_dict = OrderedDict()
        self.encoder_dict = OrderedDict()
        self.tasks_list = OrderedDict()

        # config 为
        self.config = ['encoder_config', 'additional_param']
        self.task_config = 'tasks_config'
        self.fix_config = ['QPs', 'sequence_name']

        self.output_yuv = False
        self.output_stream = False

        self.task_queue = queue.Queue(MAX_TASK_SIZE)

        self.server = None

        self.server_list = []   # include server!
        self.outputs = []
        self.msg_queue = {}

        self.interval = 1
        self.reg_timer(self.polling_info, self.interval)

        self.query_json = kw_to_json(
            type='get msg'
        ).encode('utf-8')

    def start_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        self.server_list.append(self.server)
        print('server start!')

    def listen(self):
        while True:
            readable, writable, exceptional = select.select(self.server_list, self.outputs, self.server_list)
            self.get_msg(readable)
            # self.write_msg(writable)
            self.deal_except(exceptional)
            time.sleep(0.1)

    def get_msg(self, _read_able):
        for _server in _read_able:
            if _server is self.server:
                connection, client_addr = _server.accept()
                print("new connection from {}".format(client_addr))
                connection.setblocking(False)
                self.server_list.append(connection)

                self.msg_queue[connection] = queue.Queue()
            else:
                try:
                    data = _server.recv(MAX_BUFFER_SIZE)
                except ConnectionResetError:
                    print('error! client [{}] was closed'.format(_server.getpeername()[1]))
                    self.clear_server(_server)
                    break

                if not data == b'exit':
                    self.msg_queue[_server].put(data)
                    print(data)
                    if _server not in self.outputs:
                        self.outputs.append(_server)
                else:
                    print('client [{}] closed'.format(_server.getpeername()[1]))
                    if _server in self.outputs:
                        self.outputs.remove(_server)
                    self.server_list.remove(_server)
                    _server.close()
                    del self.msg_queue[_server]

    def parse_all_msg(self):
        for _server in self.msg_queue.keys():
            while not self.msg_queue[_server].empty():
                pass

    def parse_msg(self, msg):
        pass

    def write_msg(self, _write_able):
        for _server in _write_able:
            try:
                msg = self.msg_queue[_server].get_nowait()
                _server.send(msg)
            except queue.Empty:
                print('[{}] msg queue is empty'.format(_server.getpeername()[1]))
                self.outputs.remove(_server)

    def deal_except(self, exceptional):
        for _server in exceptional:
            print('error! client [{}] was closed'.format(_server.getpeername()[1]))
            self.clear_server(_server)

    def clear_server(self, _server):
        if _server in self.server_list:
            self.server_list.remove(_server)
        if _server in self.outputs:
            self.outputs.remove(_server)
        # if _server in self.excepts:
        #     self.excepts.remove(_server)
        _server.close()
        if _server in self.msg_queue.keys():
            del self.msg_queue[_server]

    def update_task_dict(self):
        self.parse_task_json(self.task_file_name)

    def parse_task_json(self, _task_file_name):
        with open(_task_file_name, 'r') as _fp:
            _json_str = json.load(_fp, object_pairs_hook=OrderedDict)
            _spec_dict = _json_str['additional_param']
            _tasks_list = _json_str['tasks_config']
            _encoder_dict = _json_str['encoder_config']
            self.spec_dict, self.encoder_dict, self.tasks_list = _spec_dict, _encoder_dict, _tasks_list

    # wrong! its for client node
    def get_general_cfg(self):
        with open(self.general_file_name, 'r') as _fp:
            _json_str = json.load(_fp)
            _general_dict = _json_str['general_config']
        return _general_dict

    def add_cfg(self, _dict: OrderedDict, _config: OrderedDict):
        for _key in _config:
            if _key not in self.fix_config:
                _dict[_key] = _config[_key]

    def assemble_tasks(self):
        """
        函数用于组装编码任务(From self.tasks_list)
        将编码器信息(encoder_dict)、特殊参数(spec_dict)和解析任务一同打包
        添加至任务队列中。
        :return: None
        """
        _encoder_dict = self.encoder_dict
        _spec_dict = self.spec_dict
        _task_list = []
        _encoder_cfg = _encoder_dict['encoder_cfg']
        _encoder_exe = _encoder_dict['exe']

        for task in self.tasks_list:
            _random_str = ''.join(random.sample(string.ascii_letters + string.digits, 4))

            for _QP in task['QPs'].split(' '):

                _task_dict = OrderedDict()

                # 先解析任务参数，然后加入专有参数 (spec_dict 里的内容)
                _seq_name = task['sequence_name']

                # seq_info 用于修饰输出文件名。
                _seq_info = (_seq_name, _random_str, _QP)

                rec_yuv = mjoin('rec', *_seq_info, '.yuv')
                dec_yuv = mjoin('dec', *_seq_info, '.yuv')
                bin_stream = mjoin('str', *_seq_info, '.bin')
                encoder_log = mjoin('[enc]', *_seq_info, '.log')
                decoder_log = mjoin('[dec]', *_seq_info, '.log')
                err_log = mjoin('[err]', *_seq_info, '.log')

                _task_dict['-c'] = mjoin(task['sequence_name'], '.cfg')
                _task_dict['-i'] = mjoin(task['sequence_name'], '.yuv')
                if self.output_yuv:
                    _task_dict['-o'] = rec_yuv
                if self.output_stream:
                    _task_dict['-b'] = bin_stream
                self.add_cfg(_task_dict, task)
                _task_dict['encoder_log'] = encoder_log
                _task_dict['decoder_log'] = decoder_log
                _task_dict['error_log'] = err_log

                _task_json = OrderedDict()
                _task_json['encoder_config'] = self.encoder_dict
                _task_json['task'] = _task_dict
                _task_json['additional_param'] = self.spec_dict
                _task_str = json.dumps(_task_json)
                self.task_queue.put(_task_str)

    def polling_info(self):
        for _server in self.server_list:
            if _server == self.server:
                continue
            try:
                # print('sending to [{}]'.format(_server.getpeername()[1]))
                _server.send(self.query_json)
            except ConnectionResetError:
                print('error! client [{}] was closed'.format(_server.getpeername()[1]))
                self.clear_server(_server)
            except ConnectionAbortedError:
                print('error! client [{}] was closed'.format(_server.getpeername()[1]))
                self.clear_server(_server)

    def reg_timer(self, _func, _interval=1):
        _timer = threading.Timer(_interval, self.reg_timer, [_func], {'_interval': _interval})
        _timer.start()
        _func()

    def publish_task(self, _sock, _addr, _node_name):
        pass

if __name__ == '__main__':

    my_sever = Service()
    my_sever.start_server()
    my_sever.update_task_dict()
    my_sever.assemble_tasks()
    my_sever.listen()

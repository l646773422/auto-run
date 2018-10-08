import socket
import threading
import time
import json
import queue
from parallel import *
from func_lib import *
from collections import OrderedDict

MAX_TASK_SIZE = 100


class Service:

    def __init__(self):
        self.node_nums = 0
        self.nodes_info = []
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

        self.sock = None
        self.start_server()
        self.set_task_dict()
        pass

    def start_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', 9999))
        self.sock.listen(5)
        print('socket start!')

    def listen(self):
        while True:
            _sock, _addr = self.sock.accept()
            t = threading.Thread(target=self.publish_task, args=(_sock, _addr))
            t.start()

    def set_task_dict(self):
        self.spec_dict, self.encoder_dict, self.tasks_list = self.parse_tasks()

    def parse_tasks(self):
        with open(self.task_file_name, 'r') as _fp:
            _json_str = json.load(_fp, object_pairs_hook=OrderedDict)
            _spec_dict = _json_str['additional_param']
            _tasks_list = _json_str['tasks_config']
            _encoder_dict = _json_str['encoder_config']
        return _spec_dict, _encoder_dict, _tasks_list

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
        函数用于组装编码任务(from self.tasks_list)
        encoder_dict 和 spec_dict 的内容不变，
        与解析出来的任务一同打包发送至计算节点。
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

    def publish_task(self, _sock, _addr):
        print('accept new connection from {}'.format(_addr))
        _sock.send(b'welcome')
        while True:
            data = _sock.recv(1024)
            time.sleep(1)
            if not data or data.decode('utf-8') == 'exit':
                break
            if data.decode('utf-8') == 'come on':
                watch = self.task_queue.get().encode()
                _sock.send(watch)
        _sock.close()
        print('connection from %s:%s closed' % _addr)

if __name__ == '__main__':

    my_sever = Service()
    my_sever.assemble_tasks()
    my_sever.listen()


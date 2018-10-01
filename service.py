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
                _seq_info = (_seq_name, _QP, _random_str)

                rec_yuv = mjoin('rec', *_seq_info, '.yuv')
                dec_yuv = mjoin('dec', *_seq_info, '.yuv')
                bin_stream = mjoin('str', *_seq_info, '.bin')
                encoder_log = mjoin('[enc]', *_seq_info, '.log')
                decoder_log = mjoin('[dec]', *_seq_info, '.log')
                err_log = mjoin('[err]', *_seq_info, '.log')

                _task_dict['-c'] = mjoin(task['sequence_name'], '.cfg')
                _task_dict['-i'] = mjoin(task['sequence_name'], '.yuv')
                if self.output_yuv:
                    _task_dict['-o'] = mjoin('rec', *_seq_info, '.yuv')
                if self.output_stream:
                    _task_dict['-b'] = mjoin('rec', *_seq_info, '.bin')
                self.add_cfg(_task_dict, task)
                _task_dict['encoder_log'] = mjoin('[enc]', *_seq_info, '.log')
                _task_dict['decoder_log'] = mjoin('[dec]', *_seq_info, '.log')
                _task_dict['error_log'] = mjoin('[err]', *_seq_info, '.log')

                task_json = OrderedDict()
                task_json['encoder_config'] = self.encoder_dict
                task_json['task'] = _task_dict
                task_json['additional_param'] = self.spec_dict
                task_str = json.dumps(task_json)

# tcp server
def tcp_link(sock, addr, task_queue):
    print('accept new connection from {}'.format(addr))
    sock.send(b'welcome')
    while True:
        data = sock.recv(1024)
        time.sleep(1)
        if not data or data.decode('utf-8') == 'exit':
            break
        # parse data

        data_dict = json.loads(data.decode('utf-8'))
        print('received data {}'.format(data_dict))
        sock.send(b'0')
    sock.close()
    print('connection from %s:%s closed' % addr)

if __name__ == '__main__':

    my_sever = Service()
    my_pool = ThreadPool(100, 3)

    my_sever.set_task_dict()
    my_sever.assemble_tasks()

    task_queue = queue.Queue(MAX_TASK_SIZE)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 9999))
    s.listen(5)
    print('waiting for connection')

    while True:
        sock, addr = s.accept()
        t = threading.Thread(target=tcp_link, args=(sock, addr, task_queue))
        t.start()


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

    class ClientInfo:

        def __init__(self):
            self.total_core = 0
            self.idle_core = 0
            self.name = 'None'
            self.active = True
            self.ip = 'None'
            self.identifier = 'None'

        def __str__(self):
            return """\
            total_core  = {},
            idle_core   = {},
            name        = {},
            active      = {},
            ip          = {},
            identifier  = {},
            """.format(self.total_core, self.idle_core, self.name, self.active, self.ip, self.identifier)

    def __init__(self, _host='127.0.0.1', _port=9999):
        self.node_nums = 0
        self.nodes_info = []
        self.host = _host
        self.port = _port
        self.task_file_name = 'demo_tasks.json'
        self.general_file_name = 'config.json'

        self.spec_dict = OrderedDict()
        self.encoder_dict = OrderedDict()
        self.tasks_list = OrderedDict()

        self.client_lock = threading.Lock()

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
        self.client_info_list = {}

        self.interval = 1

        self.query_json = kw_to_json(
            type='get info'
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
            self.write_msg(writable)
            self.deal_except(exceptional)
            time.sleep(0.1)

    def get_msg(self, _read_able):
        for _server in _read_able:
            if _server is self.server:
                connection, client_addr = _server.accept()
                print("new connection from {}".format(client_addr))
                connection.setblocking(False)
                self.server_list.append(connection)
                self.client_lock.acquire()
                self.client_info_list[connection] = self.ClientInfo()
                self.client_lock.release()

                self.msg_queue[connection] = queue.Queue()
            else:
                try:
                    _data = _server.recv(MAX_BUFFER_SIZE)
                except ConnectionResetError:
                    print('error! client [{}] was closed'.format(_server.getpeername()[1]))
                    self.clear_server(_server)
                    break

                if not _data == b'exit':
                    try:
                        _data = json.loads(_data, object_pairs_hook=OrderedDict)
                        if _data['type'] == 'get info' and 'info' in _data.keys():
                            update_from_dict(self.client_info_list[_server], _data['info'])
                            # print(self.client_info_list[_server])

                    except json.JSONDecodeError:
                        print('parsing json string error!')
                        break

                    # if _server not in self.outputs:
                    #     self.outputs.append(_server)
                else:
                    print('client [{}] closed'.format(_server.getpeername()[1]))
                    self.clear_server(_server)

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
        if _server in self.client_info_list.keys():
            self.client_info_list[_server].active = False

    def update_task_dict(self):
        _json_dict = load_json_file(self.task_file_name)
        self.spec_dict = _json_dict['additional_param']
        self.encoder_dict = _json_dict['encoder_config']
        self.tasks_list = _json_dict['tasks_config']

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

                _all_info = OrderedDict(type='task', task_description='codec')
                _all_info['encoder_config'] = self.encoder_dict
                _all_info['task'] = _task_dict
                _all_info['additional_param'] = self.spec_dict
                _task_json = json.dumps(_all_info)
                self.task_queue.put(_task_json.encode('utf-8'))

    def start_polling(self):
        reg_timer(self.polling_info, _interval= self.interval)

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

    def start_publishing(self, _output_info=False):
        _cond = self.task_queue.qsize
        reg_timer(self.publish_task, _output_info, _interval=0.5, _cond_func=_cond)

    def publish_task(self, _output_info=False):
        # 考虑使用计时器实现，在启动发布任务后，每隔一段时间搜索是否有闲置节点
        # 直到所有任务发布结束。(所以在轮询结束时加一个 <条件Timer> )

        # 遍历过程中，可能有子节点进入，此时会改变 client_info_list
        # 所以。加锁
        self.client_lock.acquire()
        for _server, _info in self.client_info_list.items():
            if _info.active is True and _info.idle_core > 0:
                try:
                    _json_data = self.task_queue.get_nowait()

                    if _output_info:
                        print(_json_data)

                    self.msg_queue[_server].put(_json_data)
                    if _server not in self.outputs:
                        self.outputs.append(_server)
                    time.sleep(1.0)
                except queue.Empty:
                    print('task queue is empty')
                    self.client_lock.release()
                    return
        self.client_lock.release()


if __name__ == '__main__':

    my_sever = Service()
    my_sever.start_server()
    my_sever.update_task_dict()
    my_sever.assemble_tasks()
    my_sever.start_polling()
    my_sever.start_publishing(_output_info=True)
    my_sever.listen()

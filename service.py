import socket
import threading
import time
import json
import queue
from parallel import *
from func_lib import *

MAX_TASK_SIZE = 100


class Service:

    def __init__(self):
        self.node_nums = 0
        self.nodes_info = []


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

    with open('tasks.json', 'r') as fp:
        json_str = json.load(fp)
        spec_dict = json_str['spec_config']
        tasks_dict = json_str['tasks_config']
        encoder_dict = json_str['encoder_config']
        general_dict = json_str['general_config']

        print(json_str)

    my_pool = ThreadPool(100, 3)

    # 感觉序列参数可以单独写成一个文件
    all_seq_data = [
        # seq-name, intra-period, FramesToBeEncode QPs
        ['BasketballPass_416x240_50', '5', '8', '5', '22 27 32 37'],
        ['BlowingBubbles_416x240_50', '5', '8', '5', '22 27 32 37'],
    ]

    seq_path = 'Sequences'  # YUV path
    cfg_path = 'Sequences'  # YUV cfg path
    work_path = '.'         #
    sample_bit_depth = '10'
    # 解析参数，拼接成指令
    for seq_data in all_seq_data:
        seq_name, intra_period, input_bit_depth, frames, QPs = seq_data
        QPs = QPs.split(' ')
        seq_cfg = path_join(cfg_path, seq_name + '.cfg')
        seq_ori_yuv = path_join(seq_path, seq_name + '.yuv')
        random_str = ''.join(random.sample(string.ascii_letters + string.digits, 4))
        for QP in QPs:
            # 加一个随机串防止重名
            encoder_cfg = 'avs3_encode_ra.cfg'
            rec_yuv = '_'.join(['rec', seq_name, QP, random_str]) + '.yuv'
            dec_yuv = '_'.join(['dec', seq_name, QP, random_str]) + '.yuv'
            bin_stream = '_'.join(['str', seq_name, QP, random_str]) + '.avs'
            encoder_log = '_'.join(['[enc]', seq_name, QP, random_str]) + '.log'
            decoder_log = '_'.join(['[dec]', seq_name, QP, random_str]) + '.log'
            err_log = '_'.join(['err', seq_name, QP, random_str]) + '.log'

            enc_base_cfg = [
                ('encoder', 'TAppEncoder'),
                ('-c', encoder_cfg),
                ('-c', seq_cfg),
                ('-i', seq_ori_yuv),
                ('-o', rec_yuv),
                ('-b', bin_stream),
                ('QP', int(QP)),
                ('FramesToBeEncoded', frames),
                ('InputSampleBitDepth', input_bit_depth),
                ('SampleBitDepth', sample_bit_depth),
            ]
            enc_other_cfg = [
                ('QPIFrame', int(QP)),
                ('QPPFrame', int(QP) + 1),
                ('QPBFrame', int(QP) + 4),
                ('stdout', encoder_log),
                # ('err_log', err_log),
                # ('xxEnable', 1)
            ]
            enc_command = ' '.join(parse_param(enc_base_cfg) + parse_param(enc_other_cfg))

            # 解码参数
            dec_cfg = [
                ('encoder', 'TAppDecoder'),
                ('-b', bin_stream),
                ('-o', dec_yuv),
                ('stdout', decoder_log),
            ]
            dec_command = ' '.join(parse_param(dec_cfg))

            my_pool.add_job(job_func, enc_command, dec_command)

    task_queue = queue.Queue(MAX_TASK_SIZE)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 9999))
    s.listen(5)
    print('waiting for connection')

    while True:
        sock, addr = s.accept()
        t = threading.Thread(target=tcp_link, args=(sock, addr, task_queue))
        t.start()


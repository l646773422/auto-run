import os
import sys
import random
import string
from ThreadPool import *


def job_func(*commands):
    for command in commands:
        os.system(command)


def path_join(*path):
    return os.path.join(*path)


def parse_param(cfg):
    command = list()
    for key, val in cfg:
        # val = other_cfg[key]
        if key.startswith('-'):
            param = key + ' ' + str(val)
        elif key.startswith('encoder'):
            param = str(val)
        elif key.startswith('stdout'):
            param = '1>>' + val
        elif key.startswith('stderr'):
            param = '2>>' + val
        else:
            param = '--' + key + '=' + str(val)
        command.append(param)
    return command

if __name__ == "__main__":

    my_pool = ThreadPool(100, 3)

    seq_path = 'Sequences'  # YUV path
    cfg_path = 'Sequences'  # YUV cfg path
    work_path = '.'         #

    sample_bit_depth = '10'

    # 感觉序列参数可以单独写成一个文件
    all_seq_data = [
        # seq-name, intra-period, FramesToBeEncode QPs
        ['BasketballPass_416x240_50', '5', '8', '5', '22 27 32 37'],
        ['BlowingBubbles_416x240_50', '5', '8', '5', '22 27 32 37'],
    ]

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

            # 感觉参数解析应该放单独一个文件
            # 编码参数
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
            pass

    my_pool.start()
    my_pool.wait_complete()

    print('finished!')

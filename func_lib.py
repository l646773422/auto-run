import os
import socket
import json
from collections import OrderedDict


def parse_info(info: list):
    data_dict = dict()
    for key, value in info:
        data_dict[key] = value
    return data_dict


def mjoin(*args, sp='_'):
    return sp.join(args[:-1]) + args[-1]


def search_key(_dict: dict, _target):
    """
    通过关键词查找配置字典的属性
    :param _dict:
    :param _target:
    :return:
    """
    for _key in _dict.keys():
        # if _key
        pass


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


def get_host_ip():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server.connect(('8.8.8.8', 80))
        ip = server.getsockname()[0]
    finally:
        server.close()

    return ip


def kw_to_json(**kwargs):
    return json.dumps(OrderedDict(
        **kwargs
    ))

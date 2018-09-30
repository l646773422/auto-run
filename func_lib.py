
def parse_info(info: list):
    data_dict = dict()
    for key, value in info:
        data_dict[key] = value
    return data_dict


def mjoin(*args, sp='_'):
    return sp.join(args[:-1]) + args[-1]

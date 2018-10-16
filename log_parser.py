import os
import re
from collections import namedtuple
from func_lib import *

# AVS2
# seq_dict = {
#     'girls_3840x2160': 'A1',
#     'parkwalk_3840x2160': 'A2',
#     'Traffic_2560x1600': 'A3',
#
#     'beach_1920x1080': 'B1',
#     'taishan_1920x1080': 'B2',
#     'Kimono1_1920x1080': 'B3',
#     'Cactus_1920x1080': 'B4',
#     'BasketballDrive_1920x1080': 'B5',
#     'BasketballDrill_832x480': 'C1',
#     'BQMall_832x480': 'C2',
#     'PartyScene_832x480': 'C3',
#     'RaceHorses_832x480': 'C4',
#     'BasketballPass_416x240': 'D1',
#     'BQSquare_416x240': 'D2',
#     'BlowingBubbles_416x240': 'D3',
#     'RaceHorses_416x240': 'D4',
#     'City_1280x720': 'E1',
#     'Crew_1280x720': 'E2',
#     'vidyo1_1280x720': 'E3',
#     'vidyo3_1280x720': 'E4',
#
#     'CampfireParty_3840x2160': 'F1',
#     'CatRobot_3840x2160': 'F2',
#     'DaylightRoad_3840x2160': 'F3',
#     'Drums_3840x2160': 'F4',
#     'RollerCoaster_4096x2160': 'F5',
#     'Tango_4096x2160': 'F6',
#     'ToddlerFountain_4096x2160': 'F7',
#     'TrafficFlow_3840x2160': 'F8',
# }

seq_dict = {
    'girls_3840x2160': 'A1',
    'ParkRunning3_3840x2160': 'A2',
    'Campfire_3840x2160': 'A3',
    'MountainBay2_3840x2160': 'A4',

    'Cactus_1920x1080': 'B1',
    'BasketballDrive_1920x1080': 'B2',
    'MarketPlace_1920x1080': 'B3',
    'RitualDance_1920x1080': 'B4',

    'City_1280x720': 'E1',
    'Crew_1280x720': 'E2',
    'vidyo1_1280x720': 'E3',
    'vidyo3_1280x720': 'E4',
}


def m_join(*elements, split=' '):
    return split.join(elements)


class LogParser:
    def __init__(self, _encoder: str):
        self.encoder = _encoder
        self.result_list = []
        self.info_tuple = namedtuple('InfoTuple', ['seq_name', 'qp', 'bits', 'Y', 'U', 'V', 'sec'])
        self.info_prototype = self.info_tuple('default', '0', '0', '0.0', '0.0', '0.0', '1')

        # 每一个都匹配一遍
        self.patterns = []
        self.info_list = []

    def parse_from_dir(self, _dir: str):
        all_logs = os.listdir(_dir)
        all_enc_logs = [x for x in all_logs if str(x).startswith('enc')]
        if len(all_enc_logs) == 0:
            return False

        for log_file in all_enc_logs:
            with open(path_join(_dir, log_file)) as fp:
                lines = fp.readlines()
                data_dict = dict()

                for line in lines:
                    line = str(line)

                    # try all patterns for each line
                    for _pattern, info_list in self.patterns:
                        match_result = _pattern.match(line)
                        if match_result is not None:
                            for _idx, _data in enumerate(match_result.groups()):
                                if info_list[_idx] == 'seq_name':
                                    data_dict[info_list[_idx]] = _data
                                else:
                                    data_dict[info_list[_idx]] = _data
                            break

                self.info_list.append(self.dict_to_info(data_dict))

    def dict_to_info(self, kwargs):
        return self.info_prototype._replace(**kwargs)

    def init_pattern(self):
        if self.encoder == 'AVS3':
            name_pattern = self.wrap_pattern(re.compile(r'.*\\([a-zA-Z]+[0-9]*_[0-9]{3,4}x[0-9]{3,4})'), 'seq_name')
            qp_pattern = self.wrap_pattern(re.compile(r'\s*QP\s*:\s*([0-9]{2})'), 'qp')
            time_pattern = self.wrap_pattern(re.compile(r'\s*Total Time:\s*([0-9]+\.[0-9]+).*'), 'sec')
            summery_pattern = self.wrap_pattern(
                re.compile(
                    r'.+a\s*([0-9]+\.[0-9]+)\s*([0-9]+\.[0-9]+)\s*([0-9]+\.[0-9]+)\s*([0-9]+\.[0-9]+)'
                ),
                'bits', 'Y', 'U', 'V'
            )
            self.patterns.append(name_pattern)
            self.patterns.append(qp_pattern)
            self.patterns.append(time_pattern)
            self.patterns.append(summery_pattern)

    @staticmethod
    def wrap_pattern(pattern, *info):
        return [pattern, info]

    @staticmethod
    def get_log_info(_log_info):
        return m_join(
            _log_info.seq_name,
            _log_info.qp,
            _log_info.bits,
            _log_info.Y, _log_info.U, _log_info.V,
            _log_info.sec, split='\t'
        )

    def sort_all_info(self):
        self.info_list = sorted(self.info_list, key=lambda x: (x.seq_name, x.qp))

    def output_all_info(self):
        pass


if __name__ == '__main__':
    # base_path = 'D:/ProjectPython/ml_way/result/log/log'
    # for path in os.listdir(base_path):
    #     if not os.path.isdir(path_join(base_path, path)):
    #         continue
    #     parse_from_dir(path_join(base_path, path))

    logger = LogParser('AVS3')
    logger.init_pattern()
    base_path = 'D:/ProjectPython/ml_way/result/log/log'
    for path in os.listdir(base_path):
        if not os.path.isdir(path_join(base_path, path)):
            continue
        logger.parse_from_dir(path_join(base_path, path))
        logger.sort_all_info()
        pass

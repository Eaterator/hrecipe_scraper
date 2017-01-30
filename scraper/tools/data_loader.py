import os
import json


class DataLoader:

    def __init__(self):
        self.files = [f for f in os.listdir(os.environ['EATERATOR_DATA_SCRAPER_PATH']) if os.path.isfile(f)]

    def iter_data_files(self):
        for _file in self.files:
            with open(_file, 'r') as f:
                data = json.loads('[' + f.read()[1:] + ']')
            yield data

import os
import json
from recipe_scraper import EATERATOR_ENV_VARIABLE, LOGGING_FILE


class DataLoader:

    def __init__(self):
        self.files = [f for f in os.listdir(os.environ[EATERATOR_ENV_VARIABLE]) if os.path.isfile(f)]

    def iter_json_data(self):
        for _file in self.files:
            with open(_file, 'r') as f:
                data = json.loads('[' + f.read()[1:] + ']')
            yield data

    @staticmethod
    def iter_log_text(line_size=5000):
        with open(LOGGING_FILE, 'r') as f:
            current_text = []
            line_count = 0
            for line in f:
                current_text.append(line)
                line_count += 1
                if line_count > line_size:
                    yield ''.join(current_text)
                    line_count = 0
                    current_text = []
        yield ''.join(current_text)

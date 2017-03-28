import os
import json
from recipe_scraper import EATERATOR_ENV_VARIABLE, LOGGING_FILE


class DataLoader:

    def __init__(self, verbose=True):
        self.files = [os.path.join(os.environ[EATERATOR_ENV_VARIABLE], f)
                      for f in os.listdir(os.environ[EATERATOR_ENV_VARIABLE])
                      if os.path.isfile(os.path.join(os.environ[EATERATOR_ENV_VARIABLE], f))]
        self.verbose = verbose

    def iter_json_data(self):
        for _file in self.files:
            if self.verbose:
                print("Loading File: {0}".format(_file))
            try:
                with open(_file, 'r', errors="ignore") as f:
                    data = json.loads('[' + f.read()[1:] + ']')
            except UnicodeDecodeError:
                with open(_file, 'r', errors="ignore") as f:
                    text = f.read()[1:]
                    try:
                        data = json.loads('[' + text + ']')
                    except UnicodeDecodeError:
                        bytes(text, 'utf-8').decode('utf-8', 'ignore')
                        data = json.loads('[' + text + ']')
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

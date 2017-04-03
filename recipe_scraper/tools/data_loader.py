import os
import json
from recipe_scraper import EATERATOR_ENV_VARIABLE, LOGGING_FILE


class DataLoader:

    def __init__(self, verbose=True):
        self.files = [os.path.join(os.environ[EATERATOR_ENV_VARIABLE], f)
                      for f in os.listdir(os.environ[EATERATOR_ENV_VARIABLE])
                      if os.path.isfile(os.path.join(os.environ[EATERATOR_ENV_VARIABLE], f)) and
                      (os.path.splitext(f)[1] == '.txt' or os.path.splitext(f)[0] == '.txt')]
        self.verbose = verbose
        if verbose:
            print("files: {0}".format(self.files))

    def iter_json_data(self):
        recipe_count = 0
        for _file in self.files:
            if self.verbose:
                print("Loading File: {0}".format(_file))
            try:
                with open(_file, 'r', errors="ignore") as f:
                    data = json.loads('[' + f.read()[1:] + ']')
            except UnicodeDecodeError:
                if self.verbose:
                    print("\tWarning unicode error with file")
                with open(_file, 'r', errors="ignore") as f:
                    text = f.read()[1:]
                    try:
                        data = json.loads('[' + text + ']')
                    except UnicodeDecodeError:
                        bytes(text, 'utf-8').decode('utf-8', 'ignore')
                        data = json.loads('[' + text + ']')
            if self.verbose:
                recipe_count += len(data) if data else 0
                message = len(data) if data else "** FAILED LOADING **"
                print("\tLoaded recipes: {0}".format(len(message)))
            yield data
        if self.verbose:
            print("\n------Total recipes: {0}".format(recipe_count))
            print("\n\n--------------Complete --------------------\n")

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

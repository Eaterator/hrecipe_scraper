import os
import re

PATTERNS = {
    'allrecipe': '',
    'recipedepository': '',
    'foodnetwork': '',
    'epicurious': '',
}


class LogInspector:

    def __init__(self):
        with open(os.path.join(os.environ['EATERATOR_DATA_SCRAPER_PATH'], 'log', 'log.txt'), 'r') as f:
            self.text = f.read()

    def find_largest_ids(self):
        """
        Function to find the last id searched for a given url pattern for each site
        :return:
        """
        largest_ids = dict()
        for site, pattern in PATTERNS.items():
            ids = re.finditer(pattern, self.text)
            largest_ids[site] = max(float(i) for i in ids)
        return largest_ids

    def calculate_stats(self):
        pass

import re

PATTERNS = {
    'allrecipes': re.compile(r'(?<=allrecipes.com/recipe/)(\d+?)(?=,)'),
    'recipedepository': re.compile(r'(?<=therecipedepository.com/recipe/)(\d+?)(?=,)'),
    'foodnetwork': re.compile(r'(?<=foodnetwork.com/recipes/)(\d+?)(?=,)'),
    'epicurious': re.compile(r'(?<=epicurious.com/recipes/food/views/)(\d+?)(?=,)'),
}


class LogInspector:

    @staticmethod
    def find_largest_ids(text):
        """
        Function to find the last id searched for a given url pattern for each site
        :return:
        """
        largest_ids = dict()
        for site, pattern in PATTERNS.items():
            for _id in re.finditer(pattern, text):
                if site in largest_ids and int(_id.group()) >= largest_ids[site]:
                    largest_ids[site] = int(_id.group()) + 1
                else:
                    largest_ids[site] = int(_id.group()) + 1
        return largest_ids

    def calculate_stats(self):
        pass

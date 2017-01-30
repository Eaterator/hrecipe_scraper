import json
from unittest import TestCase, main as run_tests
from urllib.request import urlopen

from bs4 import BeautifulSoup

from scraper.recipe_parsers import HRecipeParser

TEST_PREP_TIMES = [
    'allrecipe',
    'foodnetwork',
    'recipedepository',
]
TEST_REVIEWS_DATA = [
    'allrecipe',
    'epicurious',
    'recipedepository',
]
DEBUG_PRINT = True


class TestHRecipeParser(TestCase):

    def setUp(self):
        self.sample_sites = {
            'allrecipe': 'http://allrecipes.com/recipe/6664/basil-roasted-peppers-and-monterey-jack-cornbread/',
            'foodnetwork': 'http://www.foodnetwork.com/recipes/bobby-flay/tandoori-prawns-recipe.html',
            'epicurious': 'http://www.epicurious.com/recipes/food/views/pasta-e-fagioli-con-salsicce-pasta-and-beans-with-sausage-351989',
            'recipedepository': 'http://www.therecipedepository.com/recipe/4',
        }

    def test_parser(self):
        parser = HRecipeParser.get_parser()
        for site, url in self.sample_sites.items():
            resp = urlopen(url)
            data = parser(BeautifulSoup(resp.read(), 'lxml'))

            self.assertNotIn(data['title'], [None, ''],
                             "No title found for site {0}".format(site))
            self.assertNotEqual(data['ingredients'], [],
                                "No ingredients found for site {0}".format(site))
            self.assertNotEqual(data['instructions'], [],
                                "No instructions found for site {0}".format(site))
            if site in TEST_REVIEWS_DATA:
                self.assertTrue(data['reviews']['text'] not in [None, [], '']
                                or data['reviews']['ratings'] not in [None, [], ''],
                                "No review body/text for site: {0}".format(site))
            if site in TEST_PREP_TIMES:
                self.assertNotEqual(data['time']['cookTime'], [],
                                    "No cookTimes found for site {0}".format(site))
                self.assertNotEqual(data['time']['prepTime'], [],
                                    "No prepTimes found for site {0}".format(site))
            if DEBUG_PRINT:
                print("-----------------{0}---------------".format(site))
                print(str(json.dumps(data, indent=4)))

if __name__ == '__main__':
    run_tests()

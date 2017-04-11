import json
from unittest import TestCase, main as run_tests
from urllib import request

from bs4 import BeautifulSoup

from recipe_scraper.recipe_parsers import HRecipeParser, JsonLdParser
from recipe_scraper.tools import get_agent

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
        # see for ideas on url endpoints https://github.com/hhursev/recipe-scraper
        self.sample_sites_hrecipe = {
            # 'simplyrecipes': 'http://www.simplyrecipes.com/recipes/shrimp_scampi/',
            # 'allrecipe': 'http://allrecipes.com/recipe/6664/basil-roasted-peppers-and-monterey-jack-cornbread/',
            # 'epicurious': 'http://www.epicurious.com/recipes/food/views/pasta-e-fagioli-con-salsicce-pasta-and-beans-with-sausage-351989',
            # 'recipedepository': 'http://www.therecipedepository.com/recipe/4',
            # 'bbcfood': 'http://www.bbcgoodfood.com/recipes/mexican-chicken-tortilla-soup',  # standard item prop parser
            # 'williamssonoma': 'http://www.williams-sonoma.com/recipe/shaved-rhubarb-salad-with-almonds-and-cheese.html',  # standard item prop i think
            # 'twopeas': 'http://www.twopeasandtheirpod.com/zucchini-noodles-with-asparagus-peas-and-basil-vinaigrette/'
            # 'finedining': 'https://www.finedininglovers.com/recipes/brunch/fried-oyster-po-boy/',
            # 'thekitchn': 'http://www.thekitchn.com/recipe-roasted-lemon-oregano-shrimp-243280',
            'chow': 'http://www.chowhound.com/recipes/charred-brussels-sprouts-bacon-dates-31929',
        }

        self.sample_sites_ldjson = {
            # 'food': 'http://www.food.com/recipe/lazy-iced-tea-202502',  # uses ld-json tag look into this
            # 'foodnetwork': 'http://www.foodnetwork.com/recipes/giada-de-laurentiis/prosciutto-and-cucumber-crostini-with-arugula-mustard',
            # 'bonappetite': 'http://www.bonappetit.com/recipe/savory-fondue-babka',
            # 'jaimieoliver': 'http://www.jamieoliver.com/recipes/beetroot-recipes/apricot-root-veg-cake-with-honey-yoghurt-icing/'
            'myrecipes': 'http://www.myrecipes.com/recipe/broccoli-grape-pasta-salad'
        }

    def test_hrecipe_parser(self):
        parser = HRecipeParser.get_parser()
        for site, url in self.sample_sites_hrecipe.items():
            req = request.Request(url, data=None, headers={'User-Agent': get_agent()})
            resp = request.urlopen(req)
            data = parser(BeautifulSoup(resp.read(), 'lxml'))

            self.assertNotIn(data['title'], [None, ''],
                             "No title found for site {0}".format(site))
            self.assertNotEqual(data['ingredients'], [],
                                "No ingredients found for site {0}".format(site))
            if site not in ['williamssonoma', 'thekitchn']:
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

    def test_ldjson_parser(self):
        parser = JsonLdParser.get_parser()
        for site, url in self.sample_sites_ldjson.items():
            resp = request.urlopen(url)
            data = parser(BeautifulSoup(resp.read(), 'lxml'))

            self.assertNotEqual(data, {},
                                "No data from site {0}".format(site))
            self.assertNotIn(data['title'], [None, ''],
                             "No title found for site {0}".format(site))
            self.assertNotEqual(data['ingredients'], [],
                                "No ingredients found for site {0}".format(site))
            self.assertNotEqual(data['instructions'], [],
                                "No instructions found for site {0}".format(site))
            self.assertNotEqual(data['time']['cookTime'], [],
                                "No cookTimes found for site {0}".format(site))
            self.assertNotEqual(data['time']['prepTime'], [],
                                "No prepTimes found for site {0}".format(site))

            if DEBUG_PRINT:
                print("-----------------{0}---------------".format(site))
                print(str(json.dumps(data, indent=4)))


if __name__ == '__main__':
    run_tests()

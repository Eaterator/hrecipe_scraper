from unittest import TestCase, main as run_tests
from recipe_parsers import HRecipeParser


class TestHRecipeParser(TestCase):

    def setUp(self):
        self.sample_sites = {
            'allrecipe': 'url_here'
        }
        self.expected = EXPECTED

    def test_parser(self):
        pass


EXPECTED = {
    'allrecipe': {
        'data': 'here'
    }
}

from abc import ABCMeta, abstractmethod
from itertools import chain


class Parser:
    """
    General class to support multiple parser types/classes. Initial support for HRecipe, but secondary
    support API based scraping methods may be useful as well that can implement logic in abstract
    parser function, and return this function without instantiation explicit instantiation necessary.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse(self, soup):
        raise NotImplementedError("All scrapers need a parse method")

    @classmethod
    def get_parser(cls):
        """Returns the parse for the class to be used as a generic static function
        is the AsyncScraper class."""
        return cls().parse


class HRecipeParser(Parser):
    """
    Parser to support the open format HRecipe format. See README.md for more info. Each line in the format
    soup.select(...) represents the tag in which the data occurs on a different site.
    """

    def parse(self, soup):
        """
        Parses HTML that conforms to the HRecipe format
        :param soup: the raw html data
        :return: structures json of the parsed data in the data collection format
        """
        return {
            'title': self._find_title(soup),
            'ingredients': self._find_ingredients(soup),
            'instructions': self._find_instructions(soup),
            'time': {
                'prepTime': self._find_preparation_time(soup),
                'cookTime': self._find_cook_time(soup),
            },
            'yield': self._find_yield(soup),
            'rating': self._find_rating(soup),
        }

    @staticmethod
    def _find_title(soup):
        # TODO make more general for meta only tags if necessary
        title = []
        title.extend(chain(
            soup.select('[itemprop="name"]'),

        ))
        return title[0].text if title[0].text else title[0]['content']

    @staticmethod
    def _find_ingredients(soup):
        ingredient_tags = []
        ingredient_tags.extend(chain(
            soup.select('[itemprop="ingredients"]'),  # allrecipes
            soup.select('[itemprop="ingredient"]')  # epicurious, foodnetwork
        ))
        return [tag.text for tag in ingredient_tags]

    @staticmethod
    def _find_instructions(soup):
        instruction_tags = []
        instruction_tags.extend(chain(
            soup.select('[itemprop="recipeDirections"]'),  # epicurious, foodnetwork
            soup.select('[itemprop="recipeInstructions"]'),  # allrecipes
        ))
        return [tag.text if tag.text else tag for tag in instruction_tags]

    def _find_preparation_time(self, soup):
        preparation_tags = []
        preparation_tags.extend(chain(
            soup.select('[itemprop="prepTime"]')
        ))
        return [tag.text if tag.text else self._find_prep_times(tag) for tag in preparation_tags]

    def _find_cook_time(self, soup):
        cook_tags = []
        cook_tags.extend(chain(
            soup.select('[itemprop="cookTime"]')
        ))
        return [tag.text if tag.text else self._find_prep_times(tag) for tag in cook_tags]

    @staticmethod
    def _find_prep_times(tag):
        """If not text is in the cookTime/prepTime tags, it tries to find appropriate HTML attribute that
        locates this information"""
        #                 allrecipes, foodnetwork
        attribute_tags = ['datetime', 'content']
        for attr in attribute_tags:
            try:
                return tag[attr]
            except KeyError:
                pass
        return

    @staticmethod
    def _find_yield(soup):
        # TODO make more general for meta only tags if necessary
        _yield = []
        _yield.extend(chain(
            soup.select('[itemprop="recipeYield"]'),
        ))
        return _yield[0].text if _yield[0].text else _yield[0]['content']

    @staticmethod
    def _find_rating(soup):
        # TODO implement logic to find ratings? Not super necessary atm
        return None

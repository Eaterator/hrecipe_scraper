from abc import ABCMeta, abstractmethod


class Parser:
    """
    General class to support multiple parser times. Initial support for HRecipe, but secondary
    support API based scraping methods available.
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
    Parser to support the open format HRecipe format. See Link below for more info.
    **** PUT LINK HERE ****
    """

    def parse(self, soup):
        """
        Parses HTML that conforms to the HRecipe format
        :param soup: the raw html data
        :return: structures json of the parsed data in the data collection format
        """
        ingredients = self._find_ingredients(soup)
        instructions = self._find_instructions(soup)
        preparation_time = self._find_preparation_time(soup)
        cook_time = self._find_cook_time(soup)
        rating = self._find_rating(soup)
        return {
            'ingredients': ingredients,
            'instructions': instructions,
            'time': {
                'preparation': preparation_time,
                'cook': cook_time,
            },
            'rating': rating,
        }

    @staticmethod
    def _find_ingredients(soup):
        ingredient_tags = []
        ingredient_tags.extend(soup.select('[itemprop="ingredients"]'))\
        ingredient_tags.extend(soup.select('[itemprop="ingredient"]'))
        return [tag.text for tag in ingredient_tags]

    @staticmethod
    def _find_instructions(soup):
        # TODO review other itemprop tags across websites
        instruction_tags = []
        instruction_tags.extend(soup.select('[itemprop="recipeDirections"]'))
        instruction_tags.extend(soup.select('[itemprop="recipeInstructions"]'))
        return [tag.text if tag.text else tag for tag in instruction_tags]

    @staticmethod
    def _find_preparation_time(soup):
        prepration_tags = soup.find_all(attr={"itemprop": "prepTime"})
        # TODO logic to look through different attributes that store hrecipe time formats!
        return prepration_tags

    @staticmethod
    def _find_cook_time(soup):
        # TODO logic to look through different attributes that store hrecipe time formats!
        return soup.find_all(attr={"itemprop": "cookTime"})

    @staticmethod
    def _find_rating(soup):
        # TODO implement logic to find ratings
        return None

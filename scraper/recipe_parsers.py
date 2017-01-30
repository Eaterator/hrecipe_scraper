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
            'reviews': self._find_reviews(soup),
        }

    def _find_title(self, soup):
        # TODO make more general for meta only tags if necessary
        titles = []
        titles.extend(chain(
            soup.select('[class="recipe-name"]'),  # recipedepository
            soup.select('[itemprop="name"]'),

        ))
        return self._return_first_acceptable_value(titles)

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
        return [tag.text if tag.text else self._find_meta_tag_values(tag) for tag in preparation_tags]

    def _find_cook_time(self, soup):
        cook_tags = []
        cook_tags.extend(chain(
            soup.select('[itemprop="cookTime"]')
        ))
        return [tag.text if tag.text else self._find_meta_tag_values(tag) for tag in cook_tags]

    @staticmethod
    def _find_meta_tag_values(tag):
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

    def _find_yield(self, soup):
        yields = []
        yields.extend(chain(
            soup.select('[itemprop="recipeYield"]'),
        ))
        return self._return_first_acceptable_value(yields)

    def _find_reviews(self, soup):
        texts_tags = []
        texts_tags.extend(chain(
            soup.select('[itemprop="reviewBody"]'),  # allrecipes
            soup.select('[class="review-text"]'),  # epicurious
            soup.select('[class="gig-comment-body"]'),  # foodnetwork
        ))
        try:
            aggregate = soup.select('[itemprop="aggregateRating"]')
            ratings = {
                'average': self._return_first_acceptable_value(
                    aggregate[0].select('[itemprop="ratingValue"]')
                ),
                'count': self._return_first_acceptable_value(
                    aggregate[0].select('[itemprop="ratingCount"]'),
                    aggregate[0].select('[itemprop="reviewCount"]')
                ),
                'best': self._return_first_acceptable_value(
                    aggregate[0].select('[itemprop="bestRating"]')
                ),
                'worst': self._return_first_acceptable_value(
                    aggregate[0].select('[itemprop="worstRating"]')
                )
            }
        except IndexError:
            individual_ratings = soup.select('[itemprop="ratingValue"]')
            ratings = {
                'ratings': individual_ratings,
            }
        if not ratings:
            ratings = self._find_foodnetwork_ratings(soup)
        return {
            'text': [tag.text for tag in texts_tags],
            'ratings': ratings,
        }

    @staticmethod
    def _find_foodnetwork_ratings(soup):
        count = soup.select('[class="gig-rating-sum"]')
        average = soup.select('[class="gig-rating-stars"]')
        individual_reviews = soup.select('[class="gig-comment-rating"]')
        individual_ratings = [len(review.select('[class="gig-comment-rating-start-full"]'))
                              for review in individual_reviews]
        return {
            'average': average[0]['title'] if len(average) and hasattr(average[0], 'title') else None,
            'count': count[0].text if len(count) else None,
            'best': max(individual_ratings) if len(individual_ratings) else None,
            'worst': min(individual_ratings) if len(individual_ratings) else None,
            'ratings': individual_ratings,
        }

    def _return_first_acceptable_value(self, *tags):
        for tag_list in tags:
            for tag in tag_list:
                if tag.text:
                    return tag.text
                value = self._find_meta_tag_values(tag)
                if value:
                    return value
        return

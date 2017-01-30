import asyncio
import sys

from aiohttp import ClientSession

from scraper.recipe_parsers import HRecipeParser
from scraper.async_scraper import AsyncScraper, DOMAIN_REQUEST_DELAY

SCRAPER_CONFIGS = {
    'allrecipes': {
        'base_path': ['allrecipes.com/recipe'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'https://allrecipes.com/recipe/{0}',
        'start_id': 6663,
    },
    'foodnetwork': {
        'base_path': ['foodnetwork.com/recipes', '/recipes'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'https://www.foodnetwork.com/recipes/{0}',
        'start_id': 3,
    },
    'epicurious': {
        'base_path': ['epicurious.com/recipes/food/views', '/recipes/food/views/'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'https://www.epicurious.com/recipes/food/views/{0}',
        'start_id': 412,
    },
    'recipedepository':{
        'base_path': ['threcipedespository.com/recipe/', '/recipe'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'http://www.therecipedepository.com/recipe/{0}',
        'start_id': 4,
    }
}


def init_scrapers(loop):
    scrapers = {}
    for site, config in SCRAPER_CONFIGS.items():
        scrapers[site] = AsyncScraper(loop=loop, **config)
    return scrapers


def main(loop):
    """
    Wrapper method to launch co-routines that recursively call the next url to scrape.
    :param loop:
    :return:
    """
    scrapers = init_scrapers(loop)
    for i, key_pair in enumerate(scrapers.items()):
            asyncio.ensure_future(key_pair[1].__anext__(), loop=loop)
    return


if __name__ == '__main__':
    main_event_loop = asyncio.get_event_loop()
    main(main_event_loop)
    while True:
        pending_tasks = asyncio.Task.all_tasks(main_event_loop)
        if sum([task.done() for task in pending_tasks]) >= len(pending_tasks):
            break
        main_event_loop.run_until_complete(asyncio.gather(*pending_tasks))
    sys.exit(0)

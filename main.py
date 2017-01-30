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
    scrapers = init_scrapers(loop)
    error_count = [0] * len(scrapers)
    delay = 0
    delay_reset = 0
    batch_size = 0
    while sum(error_count) <= len(scrapers):  # endless loop to run scrapers/ parsers while they are active
        delay -= delay_reset  # keep track of delay between requests! => schedule in event loop with this delay functionality
        for i, key_pair in enumerate(scrapers.items()):
            if not error_count[i]:
                try:
                    asyncio.ensure_future(key_pair[1].__anext__(delay), loop=loop)
                except StopAsyncIteration:
                    error_count[i] = 1
        delay += DOMAIN_REQUEST_DELAY
        # only start event loop if there are 3 tasks per active sites/scraper
        print('check main loop')
        if len(asyncio.Task.all_tasks()) > (len(scrapers)-sum(error_count)) * batch_size:
            print('entered event loop')
            # interrupt after best possible case of finishing requests in 3 tasks / scraper * MIN_DELAY_BETWEEN+REQUESTS
            loop.call_later(DOMAIN_REQUEST_DELAY * batch_size, loop.stop)
            # loop runs processing the registered tasks
            loop.run_forever()
            delay_reset = DOMAIN_REQUEST_DELAY * batch_size
            import time
            time.sleep(2)
    return


if __name__ == '__main__':
    main_event_loop = asyncio.get_event_loop()
    main(main_event_loop)
    pending_tasks = asyncio.Task.all_tasks(main_event_loop)
    main_event_loop.run_until_complete(asyncio.gather(*pending_tasks))
    sys.exit(0)

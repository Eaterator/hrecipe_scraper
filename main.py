import asyncio
import sys
from aiohttp import ClientSession
from .recipe_parsers import HRecipeParser
from .async_scraper import AsyncScraper, DOMAIN_REQUEST_DELAY

SCRAPER_CONFIGS = {
    'allrecipes': {
        'base_path': ['allrecipes.com/recipe'],
        'parser': HRecipeParser.get_parser(),  # TODO needs speciality parser
        'url_id_format': 'https://allrecipes.com/recipe/{0}',
        'start_id': 6663,
    },
    'foodnetwork': {
        'base_path': ['foodnetwork.com/recipes', '/recipes'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'https://www.foodnetwork.com/recipes/{0}',
        'seed_id': 1,
    },
    'epicurious': {
        'base_path': ['epicurious.com/recipes/food/views', '/recipes/food/views/'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'https://www.epicurious/recipes/food/views/{0}',
        'seed_id': 412,
    }
}


def init_scrapers(client):
    scrapers = {}
    for site, config in SCRAPER_CONFIGS.items():
        scrapers[site] = AsyncScraper(client=client, **config)
    return scrapers


async def main(loop):
    client = ClientSession(loop=loop)
    scrapers = init_scrapers(client)
    error_count = [0] * len(scrapers)
    while sum(error_count) >= len(scrapers):  # endless loop to run scrapers/ parsers while they are active
        for i, key_pair in enumerate(scrapers.items()):
            if not error_count[i]:
                try:
                    asyncio.ensure_future(key_pair[1].__anext__(), loop=loop)
                except StopAsyncIteration:
                    error_count[i] = 1
        # only start event loop if there are 3 tasks per active sites/scraper
        if len(asyncio.Task.all_tasks()) > (len(scrapers)-sum(error_count))*3:
            # interrupt after best possible case of finishing requests in 3 tasks / scraper * MIN_DELAY_BETWEEN+REQUESTS
            loop.call_soon(DOMAIN_REQUEST_DELAY*3, loop.stop)
            # loop runs processing the registered tasks
            loop.run_forever()
    return


if __name__ == '__main__':
    main_event_loop = asyncio.get_event_loop()
    main(main_event_loop)
    pending_tasks = asyncio.Task.all_tasks(main_event_loop)
    main_event_loop.run_until_complete(asyncio.gather(*pending_tasks))
    sys.exit(0)

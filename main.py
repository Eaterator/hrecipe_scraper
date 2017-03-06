import asyncio
import sys
from recipe_scraper.recipe_parsers import HRecipeParser
from recipe_scraper.async_scraper import AsyncScraper
from recipe_scraper.tools.log_inspector import LogInspector
from recipe_scraper.tools.data_loader import DataLoader
import argparse

# default start_ids are the minimum id that returns a valid result
SCRAPER_CONFIGS = {
    'allrecipes': {
        'base_path': ['allrecipes.com/recipe'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'http://allrecipes.com/recipe/{0}',
        'start_id': 6663,
    },
    'foodnetwork': {
        'base_path': ['foodnetwork.com/recipes', '/recipes'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'http://www.foodnetwork.com/recipes/{0}',
        'start_id': 3,
    },
    'epicurious': {
        'base_path': ['epicurious.com/recipes/food/views', '/recipes/food/views/'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'http://www.epicurious.com/recipes/food/views/{0}',
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


def modify_scrapers(scrapers):
    for text in DataLoader.iter_log_text():
        max_ids = LogInspector.find_largest_ids(text)
        for site in max_ids:
            if max_ids[site]:
                setattr(scrapers[site], 'current_id', max_ids[site])


def main(loop, modify_scraper_start_id=False):
    """
    Wrapper method to launch co-routines that recursively call the next url to scrape.
    :param loop: the event loop
    :param modify_scraper_start_id: whether to modify start_id from collected values in the log
    :return:
    """
    scrapers = init_scrapers(loop)
    if modify_scraper_start_id:
        modify_scrapers(scrapers)
    for i, key_pair in enumerate(scrapers.items()):
        asyncio.ensure_future(key_pair[1].__anext__(), loop=loop)
    return


if __name__ == '__main__':
    # Parse command line args
    parser = argparse.ArgumentParser(description="Main Scraper Launcher")
    parser.add_argument('--calc-start-id', action="store_true", help="Inspect log for largest ids for start_idx")
    args = parser.parse_args()
    modify_start_id = True if args.calc_start_id else False
    # Setup wrapper for async recipe_scraper
    main_event_loop = asyncio.get_event_loop()
    main(main_event_loop, modify_scraper_start_id=modify_start_id)
    while True:
        pending_tasks = asyncio.Task.all_tasks(main_event_loop)
        if sum([task.done() for task in pending_tasks]) >= len(pending_tasks):
            break
        main_event_loop.run_until_complete(asyncio.gather(*pending_tasks))
    sys.exit(0)

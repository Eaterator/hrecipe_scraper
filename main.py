import asyncio
import sys
from recipe_scraper.recipe_parsers import HRecipeParser, JsonLdParser
from recipe_scraper.async_scraper import AsyncScraper, AsyncSraperSiteMap
from recipe_scraper.tools.log_inspector import LogInspector
from recipe_scraper.tools.data_loader import DataLoader
from recipe_scraper.tools import SITEMAP_DOWNLOADERS, SiteMapDownloader
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
        'parser': JsonLdParser.get_parser(),
        'url_id_format': 'http://www.foodnetwork.com/recipes/{0}',
        'start_id': 3,
    },
    'epicurious': {
        'base_path': ['epicurious.com/recipes/food/views', '/recipes/food/views/'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'http://www.epicurious.com/recipes/food/views/{0}',
        # 'start_id': 412,  # initial start but it looks like there is a large gap
        'start_id': 4000,
    },
    'recipedepository': {
        'base_path': ['threcipedespository.com/recipe/', '/recipe'],
        'parser': HRecipeParser.get_parser(),
        'url_id_format': 'http://www.therecipedepository.com/recipe/{0}',
        'start_id': 4,
    },
    # 'food': {
    #     'base_path': ["www.food.com/recipes"],
    #     'parser': JsonLdParser,
    #     'url_id_format': 'http://www.food.com/recipes/{0}',
    #     'start_id': None
    # },
    # 'bbcgoodfood': {
    #     'base_path': ['www.bbcgoodfood.com/recipes/']
    # }
}


def init_scrapers(loop):
    """ To start scrapers for the ID method"""
    scrapers = {}
    del SCRAPER_CONFIGS['food']
    for site, config in SCRAPER_CONFIGS.items():
        scrapers[site] = AsyncScraper(loop=loop, **config)
    return scrapers


def modify_scrapers(scrapers):
    """Calculate maximum is for the ID string formatting method"""
    for text in DataLoader.iter_log_text():
        max_ids = LogInspector.find_largest_ids(text)
        for site in max_ids:
            if max_ids[site] and max_ids[site] > getattr(scrapers[site], 'current_id'):
                setattr(scrapers[site], 'current_id', max_ids[site])
    for site in scrapers:
        scrapers[site].reset_url_queue()


# def set_scrapers_id_generator(scrapers, loop=None):
#     """
#     Sets the SiteMapDownloader class as the url generator.
#     Uses the SiteMapDownloader class' parser for the scrapers parser.
#     """
#     for site, loader in zip(scrapers, SITEMAP_DOWNLOADERS):
#         asyncio.ensure_future(scrapers[site].set_sitemap_link_loader(loader))
#     while True:
#         print("Retrieving links from log file to build visited set and building link generators")
#         tasks = asyncio.Task.all_tasks(main_event_loop)
#         loop.run_until_complete(asyncio.gather(*tasks))
#         if sum([task.done() for task in tasks]) >= len(tasks):
#             break
#         print("Finished inspecting log file for visited links")
#     print("Visited links set information: ")
#     for site, scraper in scrapers.items():
#         print('\t{0}: {1}'.format(scraper.sitemap_loader.subdirectory_output, scraper.loader_site_set_length))
#     return


def generate_scrapers_from_sitemaps_loaders(loop=None, reverse=False):
    scrapers = {}
    for sitemap in SITEMAP_DOWNLOADERS:
        sitemap.reverse = reverse
        scrapers[sitemap.subdirectory_output] = AsyncSraperSiteMap(loop=loop)
        scrapers[sitemap.subdirectory_output].set_sitemap_link_loader(sitemap)
    asyncio.ensure_future(scrapers[sitemap.subdirectory_output].load_sites_visited_from_log_file())
    while True:
        print("Retrieving links from log file to build visited set and building link generators")
        tasks = asyncio.Task.all_tasks(main_event_loop)
        loop.run_until_complete(asyncio.gather(*tasks))
        if sum([task.done() for task in tasks]) >= len(tasks):
            break
        print("Finished inspecting log file for visited links")
    print("Visited links set information: ")
    for site, scraper in scrapers.items():
        print('\t{0}: {1}'.format(scraper.sitemap_loader.subdirectory_output, scraper.loader_site_set_length))
    return scrapers


def main(loop, modify_scraper_start_id_flag=False, use_sitemaps_flag=False, reverse_flag=False, verbose=True):
    """
    Wrapper method to launch co-routines that recursively call the next url to scrape.
    :param loop: the event loop
    :param modify_scraper_start_id_flag: whether to modify start_id from collected values in the log
    :param use_sitemaps_flag: boolean whether to use the sitemaps to genearte urls
    :param: verbose: outputs information to the command line
    :return:
    """
    if modify_scraper_start_id_flag:
        scrapers = init_scrapers(loop)
        print("Using ID url parsing")
        modify_scrapers(scrapers)
        if verbose:
            print("\tMaximum IDs: ")
            for key, value in scrapers.items():
                print("\t\t{0}: {1}".format(key, getattr(value, "current_id")))
    elif use_sitemaps_flag:
        print("Using sitemap for url generation")
        scrapers = generate_scrapers_from_sitemaps_loaders(loop, reverse=reverse_flag)
    print("Beginning scraping")
    for i, key_pair in enumerate(scrapers.items()):
        asyncio.ensure_future(key_pair[1].__anext__(), loop=loop)
    return


if __name__ == '__main__':
    # Parse command line args
    parser = argparse.ArgumentParser(description="Main Scraper Launcher")
    parser.add_argument('--calc-start-id', action="store_true", help="Inspect log for largest ids for start_idx")
    parser.add_argument('--download-sitemaps', action="store_true",
                        help="Download site maps using the sitemap downloader")
    parser.add_argument('--use-sitemaps', action="store_true",
                        help="Use sitemaps directory to generate ids for scraping")
    parser.add_argument('--reverse', action="store_true",
                        help="Iterate backwards over sitemaps")
    args = parser.parse_args()
    modify_start_id = True if args.calc_start_id else False
    download_sitemaps = True if args.download_sitemaps else False
    use_sitemaps = True if args.use_sitemaps else False
    reverse = True if args.reverse else False
    if download_sitemaps:
        main_event_loop = asyncio.get_event_loop()
        for sitemap_downloader in SITEMAP_DOWNLOADERS:
            asyncio.ensure_future(sitemap_downloader.get_sitemaps(), loop=main_event_loop)
    else:
        # Setup wrapper for async recipe_scraper
        main_event_loop = asyncio.get_event_loop()
        main(
            main_event_loop,
            modify_scraper_start_id_flag=modify_start_id,
            use_sitemaps_flag=use_sitemaps,
            reverse_flag=reverse,
            verbose=True
        )
    while True:
        pending_tasks = asyncio.Task.all_tasks(main_event_loop)
        if sum([task.done() for task in pending_tasks]) >= len(pending_tasks):
            break
        main_event_loop.run_until_complete(asyncio.gather(*pending_tasks))
    if download_sitemaps:
        print("collected site maps in directory: {0}".format(SiteMapDownloader.output_directory))
    sys.exit(0)

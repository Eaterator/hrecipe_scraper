import re
import os
import xmltodict
import gzip
import aiofiles
from io import BytesIO
from aiohttp import ClientSession, TCPConnector
from abc import ABCMeta
from collections import OrderedDict
from xml.parsers.expat import ExpatError
from recipe_scraper.recipe_parsers import HRecipeParser, JsonLdParser

SITEMAP_PATTERN = re.compile(r'(?<=sitemap:).+')


class SiteMapDownloader:

    __metaclass__ = ABCMeta

    robots_url = None
    recipe_url_pattern = None
    output_directory = None
    subdirectory_output = None
    parser = None
    site_set = set()

    completed_dir = 'collected'

    def __init__(self):
        required_attributes = [
            self.robots_url,
            self.output_directory,
            self.recipe_url_pattern,
            self.subdirectory_output,
            self.parser
        ]
        if any(not i for i in required_attributes):
            raise AssertionError("robots_url and recipe_url_pattern required for a sitemap url. Also set the output"
                                 "directory using the Abstract class set_download_directory")
        try:
            os.mkdir(os.path.join(self.output_directory, self.subdirectory_output))
        except OSError:
            pass

        try:
            os.mkdir(os.path.join(self.output_directory, self.subdirectory_output, self.completed_dir))
        except OSError:
            pass
        self._reverse = False

    async def get_sitemaps(self):
        if isinstance(self.robots_url, str):
            sitemaps = await self._find_sitemaps_from_robots(self.robots_url)
        else:
            sitemaps = self.robots_url
        while sitemaps:
            sitemap = sitemaps.pop()
            conn = TCPConnector(verify_ssl=False)
            async with ClientSession(connector=conn) as client:
                async with client.get(sitemap) as response:
                    if response.status == 200:
                        try:
                            if 'gzip' in response.content_type:
                                buf = BytesIO(await response.read())
                                f = gzip.GzipFile(fileobj=buf)
                                xml = xmltodict.parse(f.read())
                            else:
                                xml = xmltodict.parse(await response.read())
                            sitemaps.extend(self._search_sitemaps(xml))
                            self.output_sitemap(xml, sitemap.split('/')[-1])
                        except Exception as e:
                            print(str(e))
                            print("Error parsing site map: {0} | content-type: {1}".format(
                                sitemap, response.content_type))

    @staticmethod
    async def _find_sitemaps_from_robots(url):
        conn = TCPConnector(verify_ssl=False)
        sitemaps = []
        async with ClientSession(connector=conn) as client:
            async with client.get(url) as response:
                if response.status == 200:
                    txt = (await response.read()).decode('utf-8').lower()
                    sitemaps = [i.strip() for i in SITEMAP_PATTERN.findall(txt)]
        return sitemaps

    @staticmethod
    def _search_sitemaps(xml, link_filter=None):
        sitemaps = list()
        if not link_filter:
            link_filter = lambda link: 'xml' in link and any(i in link for i in ['sitemap', 'site-map'])

        def _search_helper_for_sitemaps(obj):
            if isinstance(obj, OrderedDict):
                link = obj.get('loc')
                if link:
                    sitemaps.append(link)
                for item in obj.values():
                    _search_helper_for_sitemaps(item)
            elif isinstance(obj, list):
                for item in obj:
                    _search_helper_for_sitemaps(item)
            return sitemaps

        _search_helper_for_sitemaps(xml)
        return [i for i in sitemaps if link_filter(i)]

    @classmethod
    def set_output_directory(cls, dir_name):
        cls.output_directory = dir_name

    def output_sitemap(self, xml, filename):
        output_file = os.path.join(self.output_directory, self.subdirectory_output, filename)
        collected_output_file = os.path.join(self.output_directory, self.subdirectory_output,
                                             self.completed_dir, filename)
        if not os.path.isfile(output_file) and not os.path.isfile(collected_output_file):
            data = xmltodict.unparse(xml)
            with gzip.open(output_file, 'wb') as f:
                f.write(data.encode('utf-8'))

    @property
    def get_links(self):
        path = os.path.join(self.output_directory, self.subdirectory_output)
        files = sorted(os.listdir(path)) if not self._reverse else sorted(os.listdir(path), reverse=True)
        for _file in files:
            print("\t Loading Sitemap File: {0}".format(_file))
            if os.path.isfile(os.path.join(path, _file)):
                with gzip.open(os.path.join(path, _file), 'r') as f:
                    try:
                        xml = xmltodict.parse(f.read())
                        links = self._search_sitemaps(xml, link_filter=self._recipe_link_filter)
                        for link in links:
                            if link not in self.site_set:
                                yield link
                    except ExpatError:
                        pass
                os.rename(
                    os.path.join(path, _file),
                    os.path.join(path, self.completed_dir, _file)
                )
        raise StopIteration()

    def _recipe_link_filter(self, link):
        if hasattr(self, 'ignore_recipe_pattern'):
            return \
                all(i not in link for i in self.ignore_recipe_pattern) and \
                all(i in link for i in self.recipe_url_pattern)
        else:
            return all(i in link for i in self.recipe_url_pattern)

    async def create_links_set_from_log(self):
        log_file = os.path.join(
            os.environ["EATERATOR_DATA_SCRAPING_PATH"],
            'log', 'log.txt'
        )
        async with aiofiles.open(log_file, 'r') as f:
            async for line in f:
                tmp = line.strip().strip(',').split()
                for word in tmp:
                    if self._recipe_link_filter(word):
                        self.site_set.add(word)
        return

    @property
    def site_set_length(self):
        return len(self.site_set)

    @property
    def reverse(self):
        return self._reverse

    @reverse.setter
    def reverse(self, val):
        self._reverse = val


class FoodSiteMapDownloader(SiteMapDownloader):

    subdirectory_output = 'food'
    robots_url = 'http://www.food.com/robots.txt'
    ignore_recipe_pattern = ['/review']
    recipe_url_pattern = ['www.food.com/recipe/']
    parser = JsonLdParser.get_parser()


class EpicuriousSiteMapDownloader(SiteMapDownloader):

    subdirectory_output = 'epicurious'
    robots_url = 'http://www.epicurious.com/robots.txt'
    ignore_recipe_pattern = ['/review']
    recipe_url_pattern = ['www.epicurious.com/recipes/food/views']
    parser = HRecipeParser.get_parser()


class FoodnetworkSiteMapDownloader(SiteMapDownloader):

    subdirectory_output = 'foodnetwork'
    robots_url = 'http://www.foodnetwork.com/robots.txt'
    recipe_url_pattern = ['www.foodnetwork.com/recipes/']
    ignore_recipe_pattern = ['recipes/articles', 'recipes/photos', 'recipes/menus', 'recipes/packages']
    parser = JsonLdParser.get_parser()


class AllRecipesSiteMapDownloader(SiteMapDownloader):

    subdirectory_output = 'allrecipes'
    robots_url = 'http://allrecipes.com/robots.txt'
    recipe_url_pattern = ['allrecipes.com/recipe/']
    parser = HRecipeParser.get_parser()


class RecipeDepositorySiteMapDownloader(SiteMapDownloader):

    subdirectory_output = 'recipedepository'
    robots_url = 'http://www.therecipedepository.com/robots.txt'
    recipe_url_pattern = ['www.therecipedepository.com/recipe']
    parser = HRecipeParser.get_parser()


class SimplyRecipesSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'simply_recipes'
    robots_url = 'http://www.simplyrecipes.com/robots.txt'
    recipe_url_pattern = ['http://www.simplyrecipes.com/recipes/']
    parser = HRecipeParser.get_parser()


class BBCFoodSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'bbc_food'
    robots_url = 'https://www.bbcgoodfood.com/robots.txt'
    recipe_url_pattern = ['bbcgoodfood.com/recipes/']
    parser = HRecipeParser.get_parser()


class WillimasonomaSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'william_sonoma'
    robots_url = 'http://www.williams-sonoma.com/robots.txt'
    recipe_url_pattern = ['http://www.williams-sonoma.com/recipe']
    parser = HRecipeParser.get_parser()


class BonAppetiteSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'bon_appetite'
    robots_url = 'http://www.bonappetit.com/robots.txt'
    recipe_url_pattern = ['bonappetit.com/recipe/']
    parser = JsonLdParser.get_parser()


# No site map to generate links
# class JaimeOliverSiteMapDownloader(SiteMapDownloader):
#     subdirectory_output = 'jamie_oliver'
#     robots_url = 'http://'
#     recipe_url_pattern = ['jamieoliver.com/recipes/']
#     parser = JsonLdParser.get_parser()


class FineDiningSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'fine_dining'
    robots_url = 'https://www.finedininglovers.com/robots.txt'
    recipe_url_pattern = ['finedininglovers.com/recipes/']
    parser = HRecipeParser.get_parser()


class TheKitchnSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'thektichn'
    robots_url = ['http://www.thekitchn.com/sitemap.xml']
    recipe_url_pattern = ['thekitchn.com/recipe']
    parser = HRecipeParser.get_parser()


class ChowSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'chow'
    robots_url = 'http://www.chowhound.com/robots.txt'
    recipe_url_pattern = ['www.chowhound.com/recipes/']
    parser = HRecipeParser.get_parser()


class MyRecipeSiteMapDownloader(SiteMapDownloader):
    subdirectory_output = 'myrecipes'
    robots_url = ['http://www.myrecipes.com/sitemap-index.xml']
    recipe_url_pattern = ['myrecipes.com/recipe/']
    parser = JsonLdParser.get_parser()

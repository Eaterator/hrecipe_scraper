import os
from random import choice
from .sitemap_downloader import SiteMapDownloader
from .user_agent import headers

sitemap_dir = os.path.join(
    os.environ["EATERATOR_DATA_SCRAPING_PATH"],
    'sitemaps'
)
try:
    os.mkdir(sitemap_dir)
except OSError:
    pass
SiteMapDownloader.set_output_directory(sitemap_dir)
SITEMAP_DOWNLOADERS = [i() for i in SiteMapDownloader.__subclasses__()]


def get_agent():
    return choice(headers)
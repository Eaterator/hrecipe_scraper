import os
from .sitemap_downloader import SiteMapDownloader

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

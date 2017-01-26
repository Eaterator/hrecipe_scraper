import os
import logging
import sys

__version__ = '0.0.1'
__python_version__ = '3.5.2'

###############################################
#             Data Storage Settings           #
try:
    DATA_PATH = os.environ['EATORATOR_DATA_SCRAPING_PATH']
except KeyError:
    print("Please specify a data path ENV variable 'EATORATOR_DATA_SCRAPING_PATH' to use scraper")
    sys.exit(0)
DEFAULT_MAX_FILES_PER_DAY = 100
MAX_DAILY_FILES = os.environ['MAX_DAILY_FILES'] if 'MAX_DAILY_FILES' in os.environ else DEFAULT_MAX_FILES_PER_DAY
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # Size in megabytes ( 10 MB )
MAX_FILE_SIZE = os.environ['MAX_FILE_SIZE'] if 'MAX_FILE_SIZE' in os.environ else DEFAULT_MAX_FILE_SIZE


logging.basicConfig(
    filename=os.path.join(os.environ['EATORATOR_DATA_SCRAPING_PATH'], 'log', 'log.txt'),
    level=logging.DEBUG,
    formatter=logging.Formatter('%(asctime)4s - %(name)4s - %(message)s')
)
logger = logging.getLogger('scraper')
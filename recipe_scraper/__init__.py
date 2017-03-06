import os
import logging
import sys

__version__ = '0.0.1'
__python_version__ = '3.5.2'

###############################################
#             Data Storage Settings           #
EATERATOR_ENV_VARIABLE = 'EATERATOR_DATA_SCRAPING_PATH'
try:
    DATA_PATH = os.environ[EATERATOR_ENV_VARIABLE]
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
except KeyError:
    print("Please specify a data path ENV variable '{0}' to use recipe_scraper".format(EATERATOR_ENV_VARIABLE))
    sys.exit(0)
DEFAULT_MAX_FILES_PER_DAY = 100
MAX_DAILY_FILES = os.environ['MAX_DAILY_FILES'] if 'MAX_DAILY_FILES' in os.environ else DEFAULT_MAX_FILES_PER_DAY
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # Size in megabytes ( 10 MB )
MAX_FILE_SIZE = os.environ['MAX_FILE_SIZE'] if 'MAX_FILE_SIZE' in os.environ else DEFAULT_MAX_FILE_SIZE

###############################################
#              Logging Config                 #
logging_path = os.path.join(os.environ[EATERATOR_ENV_VARIABLE], 'log')
LOGGING_FILE = os.path.join(logging_path, 'log.txt')
if not os.path.exists(logging_path):
    os.makedirs(logging_path)
logging.basicConfig(
    filename=LOGGING_FILE,
    format='%(asctime)4s| %(levelname)4s| %(name)4s| %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger('recipe_scraper')

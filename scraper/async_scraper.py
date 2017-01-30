from . import MAX_FILE_SIZE, MAX_DAILY_FILES, DATA_PATH, logger, DEBUG
import os
import json
from timeit import default_timer
from asyncio import sleep as aio_sleep, ensure_future
from aiohttp import ClientSession, TCPConnector
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from bs4 import BeautifulSoup
from .recipe_parsers import HRecipeParser
from .exceptions import InvalidResponse, AsyncScraperConfigError, FileNumberException


###############################################
#             Id Generator Settings           #
MAXIMUM_SEQUENTIAL_404_ERRORS = 10
URL_BATCH_SIZE_FROM_IDS = 3

###############################################
#        File writing thread executor         #
EXECUTOR = ThreadPoolExecutor(max_workers=1)


###############################################
#             Request behaviour               #
DOMAIN_REQUEST_DELAY = 5  # time in seconds


class AsyncScraper:
    """
    Class to handle asynchronous scraping of a given queue of urls. Expects the urls to
    be from the same domain to allow a for rate limiting on a specific domain. The purpose is
    to have a single class for domain that can be used to generate asynchronous tasks to be
    run in the main event loop.
    """
    def __init__(self, parser=HRecipeParser.get_parser(), base_path=None, loop=None, start_id=None, url_id_format=None):
        """
        :param url_queue: Queue type of urls from a specific domain
        """
        self.consecutive_404_errors = 0
        self.current_id = start_id
        self.url_id_format = url_id_format
        self._url_queue = Queue()
        self.data_file_manager = DataFileManager()
        self.parser = parser
        self.followed = []  # TODO input via bisect in sorted list to make faster !?
        self.base_path = base_path
        self.loop = loop
        if not self.base_path or not start_id or not url_id_format:
            raise AsyncScraperConfigError("No base path/seed_id/url_id_format/loop specified,\
            please instantiate instance with base class.")
        self._generate_new_urls_from_id()

    def __aiter__(self):
        return self

    async def __anext__(self):
        start = default_timer()
        try:
            resp, url = await self.make_request()
            if resp:
                data = self.parse_content(resp, url)
                await self._write_content(json.dumps(data))
            else:
                if self.consecutive_404_errors > MAXIMUM_SEQUENTIAL_404_ERRORS:
                    # raise StopAsyncIteration
                    return
                else:
                    self._generate_new_urls_from_id()
        except InvalidResponse:
            pass
        await aio_sleep(DOMAIN_REQUEST_DELAY - (start - default_timer()))  # delay call for a specific time period
        ensure_future(self.__anext__(), loop=self.loop)

    async def make_request(self):
        """
        Makes an async aiohttp request to the next url in the queue, if it is not in the self.followed list
        :return:
        """
        if not self._url_queue.empty():
            url = self._url_queue.get()
            conn = TCPConnector(verify_ssl=False)
            async with ClientSession(connector=conn) as client:
                async with client.get(url) as response:
                    if response.status == 200:
                        logger.info('successful response: id: {0}, final: {1}'.format(url, response.url))
                        self.consecutive_404_errors = 0
                        return await response.read(), response.url
                    else:
                        logger.info('invalid response: {0}'.format(url))
                        self.consecutive_404_errors += 1
                        if self.consecutive_404_errors >= MAXIMUM_SEQUENTIAL_404_ERRORS:
                            logger.error("Maximum sequential 404 error encountered. Last url: {0}".format(url))
                        raise InvalidResponse()
        else:
            return None, None

    def parse_content(self, response, url):
        """
        Parses content from response into JSON format for storage, and also adds any unfollowed links to the queue
        :param response: the raw HTTP response
        :param url: final url of the request
        :return: HTTP response parsed by the given parser (ready to be written to file in JSON format)
        """
        soup = BeautifulSoup(response, 'lxml')
        data = self.parser(soup)
        data['url'] = url
        # map(self.url_queue.put, self.find_links(soup, self.base_path))
        if DEBUG:
            return json.dumps(data, indent=4)
        else:
            return json.dumps(data)

    def find_links(self, soup):
        """
        :param soup: BeautifulSoup parsed HTTP response
        :param base_path: The base path that contains recipes (i.e. domain.com/recipes)
        :return: list of valid links to new recipes
        """
        links = [link for link in soup.find_all('a')
                 if (any(path in link for path in self.base_path)) and
                 link not in self.followed]
        self.followed.extend(links)
        return links

    @property
    def url_queue(self):
        return self._url_queue

    @url_queue.setter
    def url_queue(self, url_queue):
        self._url_queue = url_queue

    @property
    def url_queue_is_empty(self):
        return self._url_queue.empty()

    @staticmethod
    def _id_generator(_id):
        while True:
            yield _id
            _id += 1

    def _generate_new_urls_from_id(self):
        for i in range(self.current_id, self.current_id + URL_BATCH_SIZE_FROM_IDS, 1):
            self.current_id += 1
            self._url_queue.put(self.url_id_format.format(i))

    async def _write_content(self, data):
        """
        Uses helper threadpool to offload blocking file I/O operations to store data
        :param data: the json data to be written to the data file
        :return:
        """
        EXECUTOR.submit(
            write_data_to_file(data, self.data_file_manager.current_data_file)
        )


class DataFileManager:

    """
    Implemented as a non-threadsafe singleton to have mutliple co-routines to share the same data management
    handler/instance.
    """
    __instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, data_folder=DATA_PATH, max_file_size=MAX_FILE_SIZE):
        self.data_folder = data_folder
        self.max_file_size = max_file_size
        self._current_data_file = None

    def _get_current_file(self):
        """
        Function finds the current datafile to begin writing to and sets private member self._current_data_file
        :return: string for the data path
        """
        current_date_str = datetime.now().date().strftime("%Y_%m_%d_{0}")
        for i in range(0, MAX_DAILY_FILES):
            file_name = os.path.join(self.data_folder, current_date_str.format(i))
            if not os.path.exists(file_name):
                self._current_data_file = file_name
                with open(file_name, 'w+') as f:
                    f.write('[')
                return
        raise FileNumberException("Too many files (>100) for the current date: {0}".format(
            datetime.now().date().strftime("%Y-%m-%d")))

    def _close_current_file(self):
        """
        Appends closes ']' to make a valid JSON entry before switching files
        :return:
        """
        with open(self._current_data_file, 'a') as f:
            f.write(']')
        return

    @property
    def current_data_file(self):
        """
        Property to return the current data file to write to.
        :return:
        """
        if not self._current_data_file or os.stat(self._current_data_file).st_size > MAX_FILE_SIZE:
            self._get_current_file()
        return self._current_data_file

    def end_current_file_operations(self):
        self._close_current_file()
        return


def write_data_to_file(data, file_name):
    """
    Simple helper function to write data to file to be executed by the threadpoolexecutor
    """
    with open(file_name, 'a') as f:
        f.write(',')  # Use a comma separator between JSON dicts in a list format
        f.write(data)
    return

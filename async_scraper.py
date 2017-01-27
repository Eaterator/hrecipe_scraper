from . import MAX_FILE_SIZE, MAX_DAILY_FILES, DATA_PATH, logger
import os
import json
from asyncio import sleep as aio_sleep
from queue import Queue
from timeit import default_timer
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from bs4 import BeautifulSoup
from .recipe_parsers import HRecipeParser
from .exceptions import InvalidResponse, AsyncScraperConfigError, FileNumberException


###############################################
#             Id Generator Settings           #
MAXIMUM_SEQUENTIAL_404_ERRORS = 10
URL_BATCH_SIZE_FROM_IDS = 1000

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
    def __init__(self, parser=HRecipeParser.get_parser(), base_path=None, client=None, seed_id=None, url_id_format=None):
        """
        :param url_queue: Queue type of urls from a specific domain
        """
        self.consecutive_404_errors = 0
        self.current_id = seed_id
        self.url_id_format = url_id_format
        self._url_queue = Queue()
        self.data_file_manager = DataFileManager()
        self.parser = parser
        self.followed = []  # TODO input via bisect in sorted list to make faster !?
        self.base_path = base_path
        self.client = client
        if not self.base_path or not seed_id or not url_id_format or not client:
            raise AsyncScraperConfigError("No base path/seed_id/url_id_format/cient specified to limit link usefulness, \
            please instantiate instance with base class.")
        self._generate_new_urls_from_id()

    def __aiter__(self):
        return self

    async def __anext__(self):
        start = default_timer()
        try:
            resp = await self.make_request()
            if resp:
                data = self.parse_content(resp)
                await self._write_content(json.dumps(data))
            else:
                if self.consecutive_404_errors > MAXIMUM_SEQUENTIAL_404_ERRORS:
                    raise StopAsyncIteration
                else:
                    self._generate_new_urls_from_id()
        except InvalidResponse:
            pass
        await aio_sleep(DOMAIN_REQUEST_DELAY - (default_timer() - start))  # delay 5s minus time taken to this point
        return

    async def make_request(self):
        """
        Makes an async aiohttp request to the next url in the queue, if it is not in the self.followed list
        :return:
        """
        if not self._url_queue.empty():
            url = self._url_queue.get()
            async with self.client.get(url) as response:
                if response.status == 200:
                    logger.info('successful response: id: {0}, final: {1}'.format(url, response.url))
                    # if response.url != url:
                    #     self.followed.append(response.url)
                    self.consecutive_404_errors = 0
                    return await response.read()
                else:
                    logger.info('invalid response: {0}'.format(url))
                    self.consecutive_404_errors += 1
                    if self.consecutive_404_errors >= MAXIMUM_SEQUENTIAL_404_ERRORS:
                        logger.error("Maximum sequential 404 error encountered. Last url: {0}".format(url))
                    raise InvalidResponse()
        else:
            return None

    def parse_content(self, response):
        """
        Parses content from response into JSON format for storage, and also adds any unfollowed links to the queue
        :param response: the raw HTTP response
        :return: HTTP response parsed by the given parser (ready to be written to file in JSON format)
        """
        soup = BeautifulSoup(response, 'lxml')
        # map(self.url_queue.put, self.find_links(soup, self.base_path))
        return json.dumps(self.parser(soup))

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

    def set_client(self, client):
        self.client = client

    @staticmethod
    def _id_generator(_id):
        while True:
            yield _id
            _id += 1

    def _generate_new_urls_from_id(self):
        for i in range(self.current_id, URL_BATCH_SIZE_FROM_IDS, 1):
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
    def __init__(self, data_folder=DATA_PATH, max_file_size=MAX_FILE_SIZE):
        self.data_folder = data_folder
        self.max_file_size = max_file_size
        self._current_data_file = None

    def _get_current_file(self):
        """
        Function finds the current datafile to begin writing to and sets private member self._current_data_file
        :return: string for the data path
        """
        current_date_str = date().strftime("%Y_%m_%d_{0}")
        for i in range(0, MAX_DAILY_FILES):
            file_name = os.path.join(self.data_folder, current_date_str.format(i))
            if not os.path.exists(file_name):
                self._current_data_file = file_name
                with open(file_name, 'w+') as f:
                    f.write('[')
                return
        raise FileNumberException("Too many files (>100) for the current date: {0}".format(date().strftime("%Y-%m-%d")))

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


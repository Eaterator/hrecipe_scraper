#Eatorator Recipe Scraper
This package utilizes the asyncio package to leverage aiohttp, delay between requests, and standard disk I/O to
allow for a single thread to run a scraper. It takes advantage of open format for hrecipes that uses well defined
ids / class names to define the location of different parts of the recipe on the page. A summary of the format can
be found here:

    http://microformats.org/wiki/hrecipe

Some sites that support the micro format can be found here (lifted from http://microformats.org/wiki/hrecipe):

    http://www.eat-vegan.rocks/
    http://funcook.com/
    http://www.therecipedepository.com
    http://sabores.sapo.pt/
    http://www.epicurious.com/
    http://www.williams-sonoma.com/
    http://foodnetwork.com/
    http://www.plantoeat.com/recipe_book
    http://www.essen-und-trinken.de
    http://itsripe.com/recipes/

#Requirments and Environment
Currently tested/developer on python version 3.5.2. See requirements.txt for additional requirements, and install like:

    pip install -r requirements.txt

Several environment variables are used, and can be set temporarily like below, or through a shell/bash script. Starred
values are required, and the others have default fall-backs.

    export VAR_NAME=value
    * EATORATOR_DATA_SCRAPING_PATH - root directory in which scraped data is stored, a valid path on the machine
    MAX_DAILY_FILES - integer, number of files stored of size MAX_FILE_SIZE (default is 100)
    MAX_FILE_SIZE - integer, controls size of data files before rotation, default is 10 MB

# Setup and Use
The scraper needs a few seed sites to start crawling, as not patterns to urls could be seen. The seed sites are used
to collect a recipe and look to links for new recipes. The base path is the sites domain/slug to the recipe posts, i.e.

    domain.com/recipes/...

this base path must be matched to crawl for recipes. Right not only these recipe paths are crawled. After tweaking these
settings in the main.py file, run from the command line like:

    (my-virtual-env) user$ python main.py

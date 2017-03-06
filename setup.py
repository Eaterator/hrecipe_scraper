from distutils.core import setup
from setuptools import find_packages

setup(
    name="recipe-scraper",
    version='0.1',
    description="Simple recipe_scraper for hrecipe formats. Runs async in one thread and writes to a text file.",
    url="https://github.com/Eaterator/hrecipe_scraper",
    author="Lucas Currah",
    license="MIT",
    keywords="hrecipe parser recipe_scraper recipe cooking",
    packages=find_packages(exclude=['tests*'])
)

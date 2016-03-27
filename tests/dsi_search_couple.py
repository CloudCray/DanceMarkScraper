from scrapers.dancesportinfo import DanceSportInfoScraper
from pprint import pprint

dsis = DanceSportInfoScraper()
search_result = dsis.search_couples("Victor Fung Anastasia Muravyova")
pprint(search_result)
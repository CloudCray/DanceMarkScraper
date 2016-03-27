from scrapers.dancesportinfo import DanceSportInfoScraper
from pprint import pprint

comp_name = "USA_Dance_National_Dancesport_Championship_27707"
event_name = "Adult_Championship_Standard_(WTVFQ)_388365"

dsis = DanceSportInfoScraper()
results = dsis.event_results(comp_name, event_name)

pprint(results)
from scrapers.dancesportinfo import DanceSportInfoScraper
from pprint import pprint

event_name = "USA_Dance_National_Dancesport_Championship_27707"

dsis = DanceSportInfoScraper()
events = dsis.event_list(event_name)

for e in events:
    print(e)
__author__ = 'Cloud'
import dsi_scrape

comp_name = "USA_Dance_National_Dancesport_Championship_27707"
event_name = "Adult_Championship_Standard_(WTVFQ)_388365"

results = dsi_scrape.event_results(comp_name, event_name)

for res in results:
    print(res)
import csv
import json
from scrapers.o2cm import O2CMScraper

o2cm = O2CMScraper()

comp_list = o2cm.comp_list()

print(comp_list[0])

comp_id = comp_list[0]["comp_id"]
events = o2cm.comp_events(comp_id)
for event in events:
    event["results"] = o2cm.event_results(comp_id, event["event_id"])
comp_list[0]["events"] = events

filename = "output_data.json"

f_out = open(filename, "w")
json.dump(comp_list[0], f_out, indent=4)
f_out.close()
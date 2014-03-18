from o2cm.scrape import init, competition_document, comp_links

init()

links = comp_links()

print(links[0])

doc = competition_document(links[0][0], links[0][1])

filename = "samples/output_data.json"
import json
f_out = open(filename, "w")
json.dump(doc, f_out, indent=4)
f_out.close()
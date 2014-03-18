import csv
from o2cm.scrape import init, competition_document, comp_links
from o2cm.flatten import flatten_comp

init()

links = comp_links()

print(links[0])

doc = competition_document(links[0][0], links[0][1])

filename = "samples/output_data.json"
import json

f_out = open(filename, "w")
json.dump(doc, f_out, indent=4)
f_out.close()


def csv_from_list_of_dicts(data, filename, header=None):
    fout = open(filename, "w", newline="\n", errors="replace")
    writer = csv.writer(fout)
    d_0 = data[0]
    d_0_list = []
    for k in d_0.keys():
        d_0_list.append(k)
    if not header is None:
        d_0_list = header
    writer.writerow(d_0_list)
    for i in data:
        i_list = []
        for j in d_0_list:
            i_list.append(i[j])
        writer.writerow(i_list)
    fout.close()

marks = flatten_comp(doc)
csv_from_list_of_dicts(marks, "samples/output_data.csv")
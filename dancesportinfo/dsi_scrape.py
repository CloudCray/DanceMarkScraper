import urllib
import urllib.request as r
import urllib.parse as p
import bs4

header_text = """Host: dancesportinfo.net
    Connection: keep-alive
    Content-Length: 18
    Accept: application/json, text/javascript, */*; q=0.01
    Origin: http://dancesportinfo.net
    X-Requested-With: XMLHttpRequest
    User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36
    Content-Type: application/json; charset=UTF-8
    Referer: http://dancesportinfo.net/
    Accept-Encoding: gzip, deflate
    Accept-Language: en-US,en;q=0.8"""

HEADERS = {x.split(":")[0].strip(): x.split(":")[1].strip() for x in header_text.split("\n")}

COOKIES = []


COMP_EVENTS_URL = "http://dancesportinfo.net/Competition/{0}/EventList"
EVENT_RESULTS_URL = "http://dancesportinfo.net/Competition/{0}/{1}/Results"


def get_page_text(url, referer=None, header=[], data=None):
    req = r.Request(url)
    for k in HEADERS.keys():
                req.add_header(k, HEADERS[k])
    for h in COOKIES:
                req.add_header(h[0], h[1])
    for h in header:
                req.add_header(h[0], h[1])
    if referer:
                req.add_header("Referer", referer)
    if data:
        resp = r.urlopen(req, data)
    else:
        resp = r.urlopen(req)
    if resp.getheader("Set-Cookie"):
            COOKIES.append(("Cookie", resp.getheader("Set-Cookie")))
    output = resp.read()
    if type(output) is bytes:
        output = output.decode("ascii", "replace")
    return output


def dict_from_event_row(row):
    cells = [x for x in row.findAll("td")]
    rec = dict()
    rec["name"] = cells[1].text.strip()
    rec["url"] = cells[1].find("a")["href"].strip().split("/")[-2]
    rec["age"] = cells[2].text.strip()
    rec["style"] = cells[3].text.strip()
    rec["date"] = cells[4].text.strip()
    return rec


def event_list(comp_name, comp_id=None):
    if not comp_id is None:
        comp_name = comp_name + "_" + str(comp_id)
    comp_name = comp_name.replace(" ", "_")
    url = COMP_EVENTS_URL.format(comp_name)
    req = r.Request(url)
    resp = r.urlopen(req).read()

    text = resp.decode("ascii", "replace")
    soup = bs4.BeautifulSoup(text)
    table = soup.find("table", {"id": 'ContentPlaceHolder2_rpComps_dgEvents_0'})
    rows = [x for x in table.findAll("tr")]
    event_dicts = [dict_from_event_row(x) for x in rows]
    return event_dicts


def dict_from_result_row(row):
    cells = [x for x in row.findAll("td")]
    rec = dict()
    rec["result"] = cells[0].find("span").text.strip()
    rec["coupleid"] = cells[2].find("a")["coupleid"].strip()
    rec["couple"] = cells[2].find("a").text.strip()
    rec["country"] = cells[2].find("span").text.strip()
    rec["score"] = cells[3].text.strip().split(" ")[0]
    rec["change"] = cells[3].text.strip().split(" ")[1].replace("(", "").replace(")","")
    return rec


def event_results(comp_name, event_name, comp_id=None, event_id=None):
    if not comp_id is None:
        comp_name = comp_name + "_" + str(comp_id)
    comp_name = comp_name.replace(" ", "_")
    if not event_id is None:
        event_name = event_name + "_" + str(event_id)
    event_name = event_name.replace(" ", "_")
    url = EVENT_RESULTS_URL.format(comp_name, event_name)
    req = r.Request(url)
    resp = r.urlopen(req).read()
    text = resp.decode("ascii", "replace")
    soup = bs4.BeautifulSoup(text)
    tables = [x for x in soup.findAll("table") if "id" in x.attrs.keys()]
    rows = []
    for t in tables:
        t_rows = t.findAll("tr")
        for tr in t_rows:
            rows.append(tr)
    event_results = [dict_from_result_row(x) for x in rows]
    return event_results



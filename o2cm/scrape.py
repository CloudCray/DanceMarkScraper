import urllib.request as r
import urllib.parse as p
import gzip
import io
import bs4
import os


HOME_URL = r"http://www.o2cm.com/home.asp"
RESULTS_URL = r"http://www.o2cm.com/Results/"
EVENT_URL_SIMPLE = "http://www.o2cm.com/Results/event3.asp"
EVENT_URL = r"http://www.o2cm.com/Results/event3.asp?event={0}"
SCORE_URL = "http://www.o2cm.com/Results/scoresheet3.asp"
HEAT_URL = r"http://www.o2cm.com/Results/scoresheet3.asp?event={0}&heatid={1}"

HEADERS = {
    "Host": "www.o2cm.com",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Origin": "http://www.o2cm.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "en-US,en;q=0.8"}

COOKIES = []


def init():
    home_resp = get_page_text(HOME_URL)

def comp_links():
    home_resp = get_page_text(HOME_URL)
    res_resp = get_page_text(RESULTS_URL, referer=HOME_URL)
    res_soup = bs4.BeautifulSoup(res_resp)
    
    res_rows = res_soup.findAll("tr", {"class": "t1n"})
    res_comps = []
    for rr in res_rows:
        if len(rr.findAll("td")) >= 3:
            lnk = rr.find("a")
            date_val = rr.findAll("td")[2].text.strip()
            res_comps.append((lnk.text, lnk.get("href"), date_val))
    return res_comps

#res_links = res_soup.findAll(name="a")
#res_comps = [(x.text, x.get("href")) for x in res_links]


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
    enc = resp.headers.get("Content-Encoding")
    output = None
    if enc:
        if enc.upper() == "GZIP":
            bi = io.BytesIO(resp.read())
            gf = gzip.GzipFile(fileobj=bi, mode="rb")
            output = gf.read()
        else:
            output = resp.read()
    else:
        output = resp.read()
    if type(output) is bytes:
        output = output.decode("ascii", "replace")
    return output

def gzip_dict(record):
    params = p.urlencode(record)
    cid = record["event"]
    byte_data = io.BytesIO()
    f = gzip.GzipFile(fileobj=byte_data, mode='wb')
    f.write(params.encode("utf-8",'replace'))
    f.close()
    gz_out = byte_data.getvalue()
    return gz_out

def comp_id_from_link(link_url):
        split_url = p.urlsplit(link_url)
        query = split_url.query
        parsed = p.parse_qs(query)
        event_id = parsed.get("event")
        if not event_id is None:
                return event_id[0]
        else:
                return None

def comp_page(comp_id):
    comp_url = EVENT_URL.format(comp_id)
    comp_page_text = get_page_text(comp_url, referer=RESULTS_URL)
    return comp_page_text

def entries_from_comp_page(comp_page):
    comp_soup = bs4.BeautifulSoup(comp_page)
    comp_entry = comp_soup.findAll("select", {"id": "selEnt"})
    entries = [(x.get("value"), x.text) for x in comp_entry[0].findAll("option")]
    return entries

def event_list_page(comp_id):
    comp_url = EVENT_URL.format(comp_id)
    event_url = EVENT_URL_SIMPLE
    data = {
    "selDiv": "",
        "selAge": "",
        "selSkl": "",
        "selSty": "",
        "selEnt": "",
        "submit": "OK",
        "event": comp_id}
    qs = p.urlencode(data).encode("utf-8",'replace')
    header = [("Content-Length", len(qs))]
    # gz_data = gzip_dict(data)
    page_text = get_page_text(event_url, referer=comp_url, header=header, data=qs)
    return page_text

def heat_page(comp_id, heat_id):
    heat_url = HEAT_URL.format(comp_id, heat_id)
    page_text = get_page_text(heat_url, referer=EVENT_URL_SIMPLE)
    return page_text

def heat_round_page(comp_id, heat_id, round_id):
    heat_url = HEAT_URL.format(comp_id, heat_id)
    score_url = SCORE_URL
    data = {
    "heatid": heat_id,
        "selCount": round_id,
        "event": comp_id}
    qs = p.urlencode(data).encode("utf-8")
    header = [("Content-Length", len(qs))]
    # gz_data = gzip_dict(data)
    page_text = get_page_text(score_url, referer=heat_url, header=header, data=qs)
    return page_text

def heat_rounds(heat_round_page_soup):
    rnds = [(x.get("value"), x.text.strip()) for x in opts]
    return list(rnds)
    
def save_to_file(path, fn, text):
    fn = os.path.join(path, fn)
    f = open(fn, "w")
    f_len = f.write(text)
    f.close()
    return fn

def competition_document(comp_text, comp_link):
    """Returns a competition python dictionary"""
    comp_id = comp_id_from_link(comp_link)
    
    comp = {}
    comp["name"] = comp_text
    comp["comp_id"] = comp_id
    comp["heats"] = []
    
    comp_event_page = event_list_page(comp_id)
    comp_event_soup = bs4.BeautifulSoup(comp_event_page)
    heat_links = comp_event_soup.findAll("a", {"target": "_blank"})

    for hl in heat_links:
        try:

            heat_name = hl.text
            heat_url = hl.get("href")

            cur_h = heat_name

            if heat_url:
                parsed_hu = p.parse_qs(heat_url)
                heat_id = parsed_hu.get("heatid")

                if heat_id:
                    heat = {}
                    heat["name"] = heat_name
                    heat["heat_id"] = heat_id[0]
                    heat["rounds"] = []

                    h_id = heat_id[0]
                    hp = heat_page(comp_id, h_id)
                    h_soup = bs4.BeautifulSoup(hp)

                    round_vals = h_soup.findAll("option")

                    if len(round_vals) == 0:
                        rounds = [("0", "Final")]
                    else:
                        rounds = [(x.get("value"), x.text) for x in round_vals]

                    for rnd in rounds:
                        try:
                            round_name = rnd[1]
                            round_id = rnd[0]

                            cur_r = round_name

                            d_round = {}
                            d_round["name"] = round_name
                            d_round["option"] = round_id
                            d_round["dances"] = []

                            rp = heat_round_page(comp_id, h_id, round_id)
                            r_soup = bs4.BeautifulSoup(rp)

                            dance_tables = r_soup.findAll("table", {"class": "t1n"})

                            for dt in dance_tables:
                                try:
                                    rows = dt.findChildren(name="tr")
                                    data_rows = []
                                    for row in rows:
                                        dr = list([str(x.text).strip() for x in row.children if x.name == "td"])
                                        if len(dr) > 0:
                                            row_color = row.get("bgcolor")
                                            if row_color is None:
                                                result = ""
                                            else:
                                                result = "R"
                                            dr.append(result.strip())
                                            data_rows.append(dr)

                                    if len(data_rows) > 0:
                                        dance = {}
                                        dance["name"] = "".join(data_rows[0])
                                        dance["data"] = data_rows

                                        cur_d = dance["name"]

                                        d_round["dances"].append(dance)

                                except Exception as ex:
                                    print("ERROR: DanceTable " + str(dt))

                            heat["rounds"].append(d_round)

                        except Exception as ex:
                            print("ERROR: Round " + str(rnd))
                            
                    comp["heats"].append(heat)

        except Exception as ex:
            print("ERROR: Heat " + str(hl))
    return comp

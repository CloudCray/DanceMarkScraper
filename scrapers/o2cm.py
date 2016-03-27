import bs4
import urllib.parse as p
import requests
import requests.cookies
import re


class O2CMScraper:
    def __init__(self):
        self.cookies = requests.cookies.RequestsCookieJar()
        self.base_url = "http://www.o2cm.com/"
        self.headers = {
            "Accept": r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "www.o2cm.com",
            "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 " + \
            "(KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36",
        }
        self.get(self.base_url + "home.asp")

    def _update_jar(self, resp):
        for c in resp.cookies:
            self.cookies.set(c.name, c.value)

    def get(self, url, params=None, headers=None):
        req_heads = self.headers.copy()
        if headers:
            req_heads.update(headers)
        req = requests.get(url, params=params, cookies=self.cookies, headers=req_heads)
        self._update_jar(req)
        return req

    def post(self, url, data=None, headers=None):
        req_heads = self.headers.copy()
        if headers:
            req_heads.update(headers)
        req = requests.post(url, data=data, cookies=self.cookies, headers=req_heads)
        self._update_jar(req)
        return req

    def comp_list(self):
        resp = self.get("http://www.o2cm.com/Results/")
        soup = bs4.BeautifulSoup(resp.text)
        trs = soup.findAll("tr", {"class": "t1n"})
        comps = []
        for tr in trs:
            if len(tr.findAll("td")) >= 3:
                link_tag = tr.find("a")
                date_value = tr.findAll("td")[2].text.strip()
                rec = {
                    "comp_name": link_tag.text,
                    "comp_id": link_tag.get("href").split("=")[1].strip(),
                    "date": date_value
                }
                comps.append(rec)
        return comps

    def comp_events(self, comp_id):
        url = "http://www.o2cm.com/Results/event3.asp"
        params = {
            "selDiv": "",
            "selAge": "",
            "selSkl": "",
            "selSty": "",
            "selEnt": "",
            "submit": "OK",
            "event": comp_id}
        resp = self.post(url, data=params)
        soup = bs4.BeautifulSoup(resp.text)
        events = []
        link_cells = soup.findAll("td", {"class": "h5b"})
        for cell in link_cells:
            link_tag = cell.find("a")
            event_name = link_tag.text.strip()
            event_id = p.parse_qs(p.urlsplit(link_tag.get("href")).query).get("heatid")[0]
            rec = {
                "event_name": event_name,
                "event_id": event_id
            }
            events.append(rec)
        return events

    def event_results(self, comp_id, event_id):
        url = "http://www.o2cm.com/Results/scoresheet3.asp"
        params = {
            "event": comp_id,
            "heatid": event_id
        }
        resp = self.get(url, params=params)
        soup = bs4.BeautifulSoup(resp.text)

        event = dict()
        event["rounds"] = []

        round_vals = soup.findAll("option")
        if len(round_vals) == 0:
            rounds = [("0", "Final")]
        else:
            rounds = [(x.get("value"), x.text) for x in round_vals]

        for rnd in rounds:
            round_name = rnd[1]
            round_id = rnd[0]

            event_round = {
                "index": round_id,
                "name": round_name,
                "results": self.event_round_results(comp_id, event_id, round_id)
            }
            event["rounds"].append(event_round)
        return event

    def event_round_results(self, comp_id, event_id, round_id):
        url = "http://www.o2cm.com/Results/scoresheet3.asp"
        params = {
            "event": comp_id,
            "heatid": event_id,
            "selCount": round_id,
        }
        resp = self.post(url, data=params)
        soup = bs4.BeautifulSoup(resp.text.replace("&nbsp;", " ").replace("&nbsp", " "))

        event_round = dict()
        event_round["comp_id"] = comp_id
        event_round["event_id"] = event_id
        event_round["round"] = round_id

        dance_tables = soup.findAll("table", {"class": "t1n"})

        event_round["dances"] = []

        event_round["results"] = []
        summary = None

        for table in dance_tables:
            parsed = parse_dance_mark_table(table)
            if parsed["table_type"] == "couples":
                event_round["judges"] = parsed["judges"]
                event_round["couples"] = parsed["couples"]
            elif parsed["table_type"] == "dance":
                dance_name = parsed["dance"]
                couples = parsed["couples"]

                dance = {
                    "name": dance_name,
                    "couples": couples,
                }
                event_round["dances"].append(dance)
            elif parsed["table_type"] == "summary":
                summary = parsed["couples"]
        if str(round_id) == "0":
            if summary:
                for couple in summary:
                    result = {
                        "number": couple["number"],
                        "result": couple["result"]
                    }
                    event_round["results"].append(result)
            elif len(event_round["dances"]) == 1:
                for couple in event_round["dances"][0]["couples"]:
                    result = couple["result"].strip()
        else:
            couple_results = {x["number"]: False for x in event_round["couples"]}
            for dance in event_round["dances"]:
                for couple in dance["couples"]:
                    result = couple["result"].strip()
                    if result != "":
                        couple_results[couple["number"]] = True
            result_list = [{"number": k, "result": couple_results[k]} for k in couple_results.keys()]
            event_round["results"] = result_list
        return event_round


def parse_dance_mark_table(table):
    output = dict()

    rows = [tr for tr in table.findAll("tr")]
    first_row = rows[0]
    text_values = [td.text.strip() for td in first_row.findAll("td")]
    total_text = "".join(text_values).lower()
    special_tables = ["summary", "couples"]

    if total_text in special_tables:
        table_type = total_text
    else:
        table_type = "dance"
    output["table_type"] = table_type

    if table_type == "dance":
        dance_name = total_text.replace("intl.", "international").replace("am.", "american")
        judge_row = rows[1]
        judge_row_values = [td.text.strip() for td in judge_row.findAll("td")]
        judge_count = judge_row_values[1:].index("")
        judges = [judge_row_values[i+1] for i in range(judge_count)]
        
        is_final = judge_row_values[-2] == "P"

        couples = []

        for row in rows[2:]:
            couple = dict()
            marks = []
            cells = [td for td in row.findAll("td")]
            cell_values = [x.text.strip() for x in cells]
            couple_number = cell_values[0]
            couple["number"] = couple_number

            for i, judge in enumerate(judges):
                value = cell_values[i + 1]
                mark = {
                    "judge": judge,
                    "value": value,
                }
                marks.append(mark)
            couple["marks"] = marks

            if is_final:
                result_text = cell_values[-2].strip()
                couple["result"] = re.search("[0-9]+", result_text).group()
                couple["rank"] = int(couple["result"])
                couple["recalls"] = 0
            else:
                couple["result"] = cell_values[-1].strip()
                recalls = sum([1 for x in marks if x["value"] == "R"])
                couple["recalls"] = recalls
                ranked_higher = sum([1 for x in couples if x["recalls"] > recalls])
                couple["rank"] = ranked_higher + 1
            couples.append(couple)

        output["dance"] = dance_name
        output["is_final"] = is_final
        output["couples"] = couples

    elif table_type == "summary":
        dance_row = rows[1]
        dance_row_values = [td.text.strip() for td in dance_row.findAll("td")]
        dance_count = dance_row_values[1:].index("")
        dances = [dance_row_values[i+1] for i in range(dance_count)]

        couples = []

        for row in rows[2:]:
            couple = dict()
            placements = []
            cells = [td for td in row.findAll("td")]
            cell_values = [x.text.strip() for x in cells]
            couple_number = cell_values[0]
            couple["number"] = couple_number
            for i, dance in enumerate(dances):
                value = re.search("[0-9]+", cell_values[i + 1]).group()
                placement = {
                    "dance": dance,
                    "index": i,
                    "value": value,
                }
                placements.append(placement)
            couple["placements"] = placements
            result_text = cell_values[-1].strip()
            couple["result"] = re.search("[0-9]+", result_text).group()
            couples.append(couple)
        output["couples"] = couples

    elif table_type == "couples":
        couples = []

        judge_row_index = 0
        for i, row in enumerate(rows):
            text_values = [td.text.strip() for td in row.findAll("td")]
            total_text = "".join(text_values).lower()
            if total_text == "judges":
                judge_row_index = i

        for row in rows[1:judge_row_index-1]:
            cells = [td for td in row.findAll("td")]
            cell_values = [x.text.strip() for x in cells]
            if cell_values:
                couple_number = cell_values[0]
                links = cells[1].findAll("a")
                leader = links[0].text.strip()
                follower = links[1].text.strip()
                location = cell_values[-1].split("-")[-1].strip()
                couple = {
                    "number": couple_number,
                    "leader": leader,
                    "follower": follower,
                    "location": location,
                }
                couples.append(couple)
        output["couples"] = couples

        judges = []
        for row in rows[judge_row_index+1:]:
            cells = [td for td in row.findAll("td")]
            cell_values = [x.text.strip() for x in cells]
            if cell_values:
                judge_number = cell_values[0]
                name = cell_values[1].split(",")[0].strip()
                location = ", ".join(cell_values[1].split(",")[:1])
                judge = {
                    "number": judge_number,
                    "name": name,
                    "location": location,
                }
                judges.append(judge)
        output["judges"] = judges
    else:
        raise ValueError("Cannot identify table type")
    return output

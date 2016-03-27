import bs4
import json
import requests
import re


class DanceSportInfoScraper:
    def __init__(self):
        self.cookies = requests.cookies.RequestsCookieJar()
        self.base_url = "http://dancesportinfo.net/"
        self.headers = {
            "Accept": r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
            "Host": "dancesportinfo.net",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 " + \
            "(KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36",
        }
        self.get(self.base_url)

    def _update_jar(self, resp):
        for c in resp.cookies:
            self.cookies.set(c.name, c.value)

    def get(self, url, params={}, headers={}):
        req_heads = self.headers.copy()
        req_heads.update(headers)
        req = requests.get(url, params=params, cookies=self.cookies, headers=req_heads)
        self._update_jar(req)
        return req

    def post(self, url, data={}, headers={}):
        req_heads = self.headers.copy()
        req_heads.update(headers)
        req = requests.post(url, data=data, cookies=self.cookies, headers=req_heads)
        self._update_jar(req)
        return req

    def search_couples(self, query):
        data = json.dumps({"query": query.lower(), "lang": ""})
        headers = {
            "Content-Length": len(data),
            "Content-Type": "application/json; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        }
        url = "http://dancesportinfo.net/Services.asmx/SearchCouples"
        resp = self.post(url, data, headers)
        if resp.status_code == 200:
            return resp.json()["d"]
        else:
            raise ValueError("Search could not be completed")

    def couple_results(self, couple_id):
        url = "http://dancesportinfo.net/Couple/{0}/Results".format(couple_id)
        couple_page = self.get(url)
        soup = bs4.BeautifulSoup(couple_page.text)
        output = {}
        output["url"] = url
        output["divisions"] = {}
        output["couple_id"] = couple_id
        output["couple_name"] = soup.find("h2").text.strip()
        for h4 in soup.findAll("h4"):
            if not "bannerheader" in h4.get("class", ""):
                division_tag = h4.findNext("span", {"id": re.compile("dgComp_Status")})
                style_tag = division_tag.findNextSibling("span")
                division = division_tag.text.strip()
                style = style_tag.text.strip()
                table = h4.findNext("table")
                results = []
                for row in table.findAll("tr"):
                    cells = row.findAll("td")
                    result = {}
                    result["date"] = cells[0].text.strip()
                    result["comp_slug"] = cells[2].find("a").get("href")
                    result["comp_id"] = cells[2].find("a").get("href").split("/")[2]
                    result["comp_name"] = cells[2].find("a").text.strip()
                    result["location"] = cells[2].text.split("\n")[1].strip()
                    result["event_slug"] = cells[3].find("a").get("href")
                    result["event_id"] = cells[3].find("a").get("href").split("/")[3]
                    result["event_name"] = cells[3].find("a").text.strip()
                    result["place"] = int(re.search("[0-9]+", cells[4].text.strip()).group())
                    result["rating"] = cells[6].text.split(" ")[0].strip()
                    result["change"] = int(re.search("[-0-9]+", cells[6].text.split(" ")[1].strip()).group())
                    results.append(result)
                if not division in output["divisions"]:
                    output["divisions"][division] = {}
                output["divisions"][division][style] = results
        return output

    def event_results(self, comp_id, event_id):
        url = "http://dancesportinfo.net/Competition/{0}/{1}/Results".format(comp_id, event_id)
        event_page = self.get(url)
        soup = bs4.BeautifulSoup(event_page.text)
        output = {}
        output["url"] = url
        output["comp_id"] = comp_id
        output["comp_name"] = soup.find("span", {"id": "ContentPlaceHolder1_CompLabel"}).text.strip()
        output["event_id"] = event_id
        event_name_span = soup.find("span", {"id": "ContentPlaceHolder2_EventLabel"}).text.strip()
        for x in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            event_name_span = event_name_span.replace(x, "|" + x)
        output["event_name"] = event_name_span.split("|")[0].strip()
        output["event_date"] = event_name_span.split("|")[1].strip()
        output["results"] = []
        for i, table in enumerate(soup.findAll("table", {"id": re.compile("ContentPlaceHolder2_rpResults_dgRound_")})):
            round_name = table.findPreviousSibling("h4").text.strip()
            for tr in table.findAll("tr"):
                cells = tr.findAll("td")
                result = {}
                result["couple_id"] = cells[2].find("a").get("encname")
                result["place"] = int(cells[2].find("a").get("pos"))
                result["rank_start"] = int(cells[2].find("a").get("rank"))
                result["rank_end"] = int(cells[2].find("a").get("nrank"))
                result["couple_name"] = cells[2].find("a").text.strip()
                result["round_reverse_index"] = i
                result["round_name"] = round_name
                output["results"].append(result)
        output["rounds"] = max([x['round_reverse_index'] for x in output["results"]]) + 1
        return output

    def search_events(self, style="", status="", results=500):
        """
            Style:
                'B' - Ballroom
                'L' - Latin
            Status:
                'N' - Juvenile
                'J' - Junior
                'Y' - Youth
                'A' - Amateur
                'S' - Senior
                'P' - Professional
        """
        url = "http://dancesportinfo.net/Services.asmx/GetCompetitionList3"
        params = {
            "Status": status,
            "Style": style,
            "countryID": "US",
            "coupleCountry": "",
            "coupleId": 0,
            "lang": "",
            "pageNo": 0,
            "pageSize": results,
            "name": "",
            "photosAvailable": False,
            "started": "",
            "town": "",
            "videosAvailable": False
        }
        data = json.dumps(params)
        headers = {
            "Content-Length": len(data),
            "Content-Type": "application/json; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        }
        resp = self.post(url, data, headers)
        if resp.status_code == 200:
            return resp.json()["d"]
        else:
            raise ValueError("Search could not be completed")

    def event_list(self, comp_id):
        url = "http://dancesportinfo.net/Competition/{0}/EventList".format(comp_id)
        resp = self.get(url)
        soup = bs4.BeautifulSoup(resp.text)
        table = soup.find("table", {"id": 'ContentPlaceHolder2_rpComps_dgEvents_0'})
        rows = [x for x in table.findAll("tr")]
        event_dicts = []
        for row in rows:
            cells = [x for x in row.findAll("td")]
            rec = dict()
            rec["name"] = cells[1].text.strip()
            rec["event_id"] = cells[1].find("a")["href"].strip().split("/")[-2]
            rec["age"] = cells[2].text.strip()
            rec["style"] = cells[3].text.strip()
            rec["date"] = cells[4].text.strip()
            event_dicts.append(rec)
        return event_dicts

def flatten_comp(comp_doc):
    heat = comp_doc["heats"][0]
    rnd = heat["rounds"][0]
    dance = rnd["dances"][0]
    
    marks = []
    all_couples = {}
    all_judges = {}

    for heat in comp_doc["heats"]:
        #heat_couples = {}

        for rnd in heat["rounds"]:
            couples = o2cm_round_couples(rnd)
            for couple in couples:
                all_couples[couple["id"]] = couple
            judges = o2cm_round_judges(rnd)
            for judge in judges:
                all_judges[judge["id"]] = judge
            rnd_type = detect_round_type(rnd["dances"], "o2cm")
            final = rnd_type[1]
            for dance in rnd["dances"]:
                dn = dance["name"]
                i = rnd["dances"].index(dance)
                if not dn in ["Couples", "Summary"]:
                    dm = dance_marks(rnd, i, "o2cm", final)
                    for mark in dm:
                        mark["comp_id"] = comp_doc["comp_id"]
                        mark["comp_name"] = comp_doc["name"]
                        mark["heat_id"] = heat["heat_id"]
                        mark["heat_name"] = heat["name"]
                        mark["round_id"] = rnd["option"]
                        mark["round_name"] = rnd["name"]
                        mark["dance_id"] = rnd["dances"].index(dance)
                        mark["dance_name"] = dance["name"]
                        mark["judge_name"] = None
                        mark["lead_name"] = None
                        mark["follow_name"] = None
                        mark["couple_location"] = None

                        judge = all_judges.get(mark["judge"])
                        couple = all_couples.get(mark["couple"])

                        if judge:
                            mark["judge_name"] = judge["name"]
                        if couple:
                            mark["lead_name"] = couple.get("lead_name")
                            mark["follow_name"] = couple.get("follow_name")
                            mark["couple_location"] = couple.get("loc")
                        mark["value"] = 0
                        if mark["mark"] == "X":
                            mark["value"] = 1
                        elif mark["mark"] == "":
                            mark["value"] = 0
                        elif mark["mark"].isnumeric():
                            mark["value"] = int(mark["mark"])

                        mark["final_result"] = final_place(heat, mark["couple"])
                        marks.append(mark)
    return marks

def detect_round_type(dances, system):
    if system == "o2cm":
        if len(dances) == 0:
            return None
        else:
            names = [dance["name"] for dance in dances]
            multidance = False
            if "Summary" in names:
                multidance = True
            elif len(dances) == 2:
                multidance = False
            else:
                multidance = True
            final = False
            if len(dances[0]["data"]) == 2:
                final = True
            elif dances[0]["data"][2][2].isnumeric():
                final = True
            return (multidance, final)


def o2cm_round_judges(rnd):
    judges = []
    judge_index = 0
    dances = rnd.get("dances")
    dance = dances[-1]
    for i in range(len(dance["data"])):
        if dance["data"][i] == ['', 'Judges', '']:
            judge_index = i
    if not judge_index == 0:
        for judge_row in dance["data"][judge_index+1:]:
            judge = {}
            judge["id"] = judge_row[0]
            rec = judge_row[1].split(",")
            judge["name"] = rec[0].strip()
            judge["loc"] = ", ".join(rec[1:]).strip()
            judges.append(judge)
    return judges

def o2cm_round_couples(rnd):
    couples = []
    judge_index = 0
    dances = rnd.get("dances")
    dance = dances[-1]
    for i in range(len(dance["data"])):
        if dance["data"][i] == ['', 'Judges', '']:
            judge_index = i
    if not judge_index == 0:
        for couple_row in dance["data"][1:judge_index-1]:
            couple = {}
            couple["id"] = couple_row[0]
            rec = couple_row[1].replace(" -", " , ").split(",")
            couple["lead_name"] = rec[0].strip()
            couple["follow_name"] = rec[1].strip()
            couple["loc"] = rec[2].strip()
            couples.append(couple)
    return couples

def dance_marks(rnd, index, system, final=True):
    marks = []
    dance = rnd["dances"][index]
    if system == "o2cm":
        judges = o2cm_round_judges(rnd)
        judge_id_row = dance["data"][1]
        for row in dance["data"][2:]:
            for judge in judges:
                j_id = judge["id"]

                just_col = judge_id_row.index(j_id)

                mark = {}
                mark["couple"] = row[0]
                mark["judge"] = j_id
                mark["mark"] = row[just_col].strip()
                if final:
                    mark["result"] = row[-3]
                else:
                    mark["result"] = row[-2]
                marks.append(mark)
    return marks

def final_place(heat, couple_id):
    for rnd in heat["rounds"]:
        dance = rnd["dances"][0]
        couple_nums = [x[0] for x in dance["data"][2:]]
        if couple_id in couple_nums:
            return couple_nums.index(couple_id) + 1

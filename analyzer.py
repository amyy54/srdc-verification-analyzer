import json
import urllib
import urllib.request
import urllib.error
import datetime
import queue
import average
from flask import abort

ENDPOINT = "https://www.speedrun.com/api/v1/"
GAME = ENDPOINT + "games?abbreviation={}&embed=moderators"
RUNS = ENDPOINT + "runs?game={}&direction=desc&orderby=date&max=200"
VERIFIED = ENDPOINT + "runs?game={}&status=verified&direction=desc&orderby=verify-date&max=200"
USERS = ENDPOINT + "users/{}"


def google_colors(analyzer_data):
    result = {}
    for pos, x in enumerate(analyzer_data, start=0):
        result[pos] = {'color': x["color"]}

    return result


def google_chart(analyzer_data):
    result = [["Examiner", "Verified"]]
    for x in analyzer_data:
        result.append([x["name"], x["runs"]])

    return result


def parse_other(other_list):
    verifier_stats = []
    for x in other_list:
        already_found = False
        for i in verifier_stats:
            if x == i["id"]:
                already_found = True
                i["runs"] += 1
                break

        if already_found:
            continue

        user_info = json.loads(urllib.request.urlopen(USERS.format(x)).read())

        if user_info["data"]["name-style"]["style"] == "solid":
            color = user_info["data"]["name-style"]["color"]["dark"]
        else:
            color = user_info["data"]["name-style"]["color-from"]["dark"]

        verifier_stats.append({
            "id": user_info["data"]["id"],
            "name": user_info["data"]["names"]["international"],
            "runs": 1,
            "length": "Not Tracked",
            "color": color
        })

    return verifier_stats


def manager(abbreviation, date=None, ending_date=None, includeLength=False):
    output_dict = {
        "game_name": "Testing",
        "game_id": "1234",
        "in_queue": 0,
        "average_daily": 0,
        "verified_daily": 0,
        "verifier_analyzed": 0,
        "verifier_stats": [],
        "other_list": []
    }

    average_verified = []

    # Find game
    games = json.loads(urllib.request.urlopen(GAME.format(abbreviation)).read())

    try:
        output_dict["game_name"] = games["data"][0]["names"]["international"]
        output_dict["game_id"] = abbreviation
    except LookupError:
        abort(404)
        return

    # Runs in queue
    output_dict["in_queue"] = len(queue.load_queue(abbreviation.split(","))[0]["runs"])

    # Verifier Information
    moderators = []
    for x in games["data"][0]["moderators"]["data"]:
        if x["name-style"]["style"] == "solid":
            color = x["name-style"]["color"]["dark"]
        else:
            color = x["name-style"]["color-from"]["dark"]
        # print(x["name-style"])
        moderators.append({
            "id": x["id"],
            "name": x["names"]["international"],
            "count": 0,
            "run_length": [],
            "mod_color": color})

    runs_analyzed_count = 0
    other_count = 0
    other_list = []

    verified_endpoint = VERIFIED.format(games["data"][0]["id"])
    if date is not None:
        starting_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    else:
        starting_date = None

    if ending_date is not None:
        ending_date = datetime.datetime.strptime(ending_date, "%Y-%m-%d")

    while True:
        date_reached = False

        try:
            verified = json.loads(urllib.request.urlopen(verified_endpoint).read())
        except urllib.error.URLError:
            abort(503)
            return

        for x in verified["data"]:
            date_of_run = datetime.datetime.strptime((x["status"]["verify-date"])[0:10], "%Y-%m-%d")
            if ending_date is not None and date_of_run > ending_date:
                continue

            if date is not None and date_of_run < starting_date:
                date_reached = True
                break

            not_other = False
            runs_analyzed_count += 1
            average_verified.append(date_of_run.day)
            for i in moderators:
                if x["status"]["examiner"] == i["id"]:
                    i["count"] += 1
                    i["run_length"].append(x["times"]["primary_t"])
                    not_other = True
            if not not_other:
                other_count += 1
                other_list.append(x["status"]["examiner"])

        if date_reached or starting_date is None:
            break

        else:
            found_endpoint = False
            for x in verified["pagination"]["links"]:
                if x["rel"] == "next":
                    verified_endpoint = x["uri"]
                    found_endpoint = True
                    break
            if not found_endpoint:
                break

    output_dict["verifier_analyzed"] = runs_analyzed_count

    output_dict["average_daily"] = average.get_average(games["data"][0]["id"], date, ending_date)

    range = max(average_verified) - min(average_verified)
    output_dict["verified_daily"] = round(runs_analyzed_count / range, 2)

    for x in moderators:
        total = 0
        for i in x["run_length"]:
            total += i
        if total != 0:
            run_average = total / len(x["run_length"])
            run_average_date = datetime.timedelta(seconds=int(run_average))
        else:
            run_average_date = None

        if runs_analyzed_count == 0:
            return None

        output_dict["verifier_stats"].append({
            "name": x["name"],
            "runs": x["count"],
            "length": str(run_average_date),
            "color": x["mod_color"]
        })

    output_dict["verifier_stats"].append({
        "name": "Other",
        "runs": other_count,
        "length": "Not Tracked",
        "color": "#FFFFFF"
    })
    output_dict["other_list"] = other_list

    return output_dict


if __name__ == "__main__":
    print(manager("smoce", date="2020-11-01", includeLength=True))

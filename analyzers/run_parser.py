import urllib
import urllib.request
import urllib.error
import json
import datetime
from isodate import parse_duration, parse_datetime
from flask import abort


REGIONS = { 
    "ypl25l47": "br", 
    "mol4z19n": "cn", 
    "e6lxy1dz": "eu", 
    "o316x197": "jp", 
    "p2g50lnk": "kr", 
    "pr184lqn": "us" 
}


def check_range(timerange, run) -> bool:
    if timerange is None:
        return True
    elif timerange[0] == "<":
        return int(timerange[1:]) > int(run["times"]["primary_t"])
    elif timerange[0] == ">":
            return int(timerange[1:]) < int(run["times"]["primary_t"])
    else:
        return True


def check_times(record, time):
    return record["time"] > time


def check_record(i : dict, records : list, is_level : bool, var_array : list, id : str) -> bool:
    record_continue = None
    for z in records:
        if z["category_id"] == i["category"]["data"]["id"] and (not is_level or z["level_id"] == i["level"]["data"]["id"]):
            if len(var_array) > 0:
                if z["variables"]["id"] == var_array[0] and z["variables"]["var"] == var_array[1]:
                    record_continue = check_times(z, i["times"]["primary_t"])
                    break
            else:
                record_continue = check_times(z, i["times"]["primary_t"])
                break

    if record_continue is None:
        if is_level:
            leaderboard_url = f"https://www.speedrun.com/api/v1/leaderboards/{id}/level/{i['level']['data']['id']}/{i['category']['data']['id']}?top=1"
        else:
            leaderboard_url = f"https://www.speedrun.com/api/v1/leaderboards/{id}/category/{i['category']['data']['id']}?top=1"

        if len(var_array) > 0:
            leaderboard_url += f"&var-{var_array[0]}={var_array[1]}"

        try:
            leaderboard = json.loads(urllib.request.urlopen(leaderboard_url).read())
        except urllib.error.URLError:
            abort(503)
            return

        if len(leaderboard["data"]["runs"]) > 0:
            records.append(
                {
                    "category_id": leaderboard["data"]["category"],
                    "level_id": "",
                    "variables": {
                        "id": "",
                        "var": ""
                    },
                    "time": leaderboard["data"]["runs"][0]["run"]["times"]["primary_t"]
                }
            )

            if is_level:
                records[len(records) - 1]["level_id"] = i['level']['data']['id']

            if len(var_array) > 0:
                records[len(records) - 1]["variables"] = {
                    "id": var_array[0],
                    "var": var_array[1]
                }

            record_continue = check_times(records[len(records) - 1], i["times"]["primary_t"])
        else:
            record_continue = True
        return record_continue


def run_parser(i : dict, category=None, user_query=None, exclusions=None, get_records=False, records : list = [], id : str = "", verifier=False, timerange=None) -> list:
    is_level = False
    title = ""
    var_array = []
    title_weblink = ""
    game = "Not Fetched"
    # Fetch Title Info
    if not isinstance(i["level"]["data"], list):
        is_level = True
        title_weblink = i["level"]["data"]["weblink"]
        title = i["level"]["data"]["name"] + ": "
    title += i["category"]["data"]["name"]

    if verifier:
        game = i['game']['data']['names']['international']

    search_title = title.replace(" ", "_").replace("%", "")
    if (category is None or search_title in category) and \
            (exclusions is None or search_title not in exclusions):
        for j in i["category"]["data"]["variables"]["data"]:
            if j["is-subcategory"] and j["id"] in i["values"]:
                var_array.append(j["id"])
                var_array.append(i["values"][j["id"]])
                title += " - " + j["values"]["values"][i["values"][j["id"]]]["label"]
        if not is_level:
            title_weblink = i["category"]["data"]["weblink"]
        
        user = ""
        user_weblink = ""
        if len(i["players"]["data"]) > 0:
            if i["players"]["data"][0]["rel"] == "user":
                user = i["players"]["data"][0]["names"]["international"]
                user_weblink = i["players"]["data"][0]["weblink"]
            else:
                try:
                    user = i["players"]["data"][0]["name"]
                except LookupError:
                    user = "User failed to load"
                    pass

        if user_query is None or user in user_query:
            if not get_records or check_record(i, records, is_level, var_array, id):
                if check_range(timerange, i):
                    # Get Time
                    run_time = parse_duration(i["times"]["primary"])
                    if title == "Damageless": # Hardcoded because I can't be bothered to try and fix it.
                        time_result = str(int(int(i["times"]["primary_t"]) / 3600)).zfill(3) + " Moons"
                    else:
                        time_result = str(run_time)
                        if time_result[-3:] == '000':
                            time_result = time_result[:-3]

                    # Platform
                    try:
                        platform = i["platform"]["data"]["name"]
                        if i['system']['emulated']:
                            platform += " (EMU)"
                    except TypeError:
                        platform = ""

                    if i['system']['region'] is not None:
                        try:
                            platform = REGIONS[i['system']['region']] + "_" + platform
                        except LookupError:
                            pass

                    # Date ago
                    try:
                        date = datetime.date.fromisoformat(i["date"])
                        dateago = date.strftime("%b %d, %Y")
                    except TypeError:
                        dateago = ""

                    verifyago = ""
                    if i["status"]["status"] == "verified":
                        status = "Verified"
                        verify_date = i["status"]["verify-date"]
                        if verify_date is not None:
                            # Support for really old runs
                            verify_date = parse_datetime(verify_date)
                            verifyago = verify_date.strftime("%b %d, %Y")
                    elif i["status"]["status"] == "rejected":
                        status = "Rejected"
                    else:
                        status = "Awaiting"

                    return {
                        "game": game,
                        "title": title,
                        "title_weblink": title_weblink,
                        "short_title": search_title,
                        "user": user,
                        "user_weblink": user_weblink,
                        "time": time_result,
                        "weblink": i["weblink"],
                        "platform": platform,
                        "date": dateago,
                        "verify-date": verifyago,
                        "status": status
                    }
    return None
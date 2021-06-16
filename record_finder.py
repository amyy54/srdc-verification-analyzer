import urllib
import urllib.request
import urllib.error
import json
import datetime
import timeago
from flask import abort


def check_times(record, time):
    return record["time"] > time


def find_records(GAMES, category=None, user_query=None, queue_order="date", exclusions=None):
    json_result = []

    records = []

    for x in GAMES:
        # Fetch Game ID
        try:
            game = json.loads(urllib.request.urlopen("https://www.speedrun.com/api/v1/games?abbreviation=" + str(x)).read())
        except urllib.error.URLError:
            abort(503)
            return

        try:
            id = game["data"][0]["id"]
        except:
            abort(404)
            return

        run_count = 0

        # Fetch game information (used for title)
        try:
            game_info = json.loads(
                urllib.request.urlopen("https://www.speedrun.com/api/v1/games/" + str(id)).read())
            game_name = game_info["data"]["names"]["international"]
        except urllib.error.URLError:
            game_name = str(x)

        queue_url = "https://www.speedrun.com/api/v1/runs?game=" + str(id) + "&status=new&direction=asc&orderby=" + queue_order + "&embed=platform,players,category.variables,level&max=200"

        json_result.append({
            "game_name": game_name,
            "runs": [],
            "run_count": 0
        })

        while True:
            # Fetch queue information
            try:
                queue = json.loads(urllib.request.urlopen(queue_url).read())
            except urllib.error.URLError:
                abort(503)
                return

            for i in queue["data"]:
                is_level = False
                title = ""
                var_array = []
                title_weblink = ""
                # Fetch Title Info
                if not isinstance(i["level"]["data"], list):
                    is_level = True
                    title_weblink = i["level"]["data"]["weblink"]
                    title = i["level"]["data"]["name"] + ": "
                title += i["category"]["data"]["name"]

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

                    if i["players"]["data"][0]["rel"] == "user":
                        user = i["players"]["data"][0]["names"]["international"]
                    else:
                        try:
                            user = i["players"]["data"][0]["name"]
                        except LookupError:
                            user = "User failed to load"
                            pass

                    if user_query is None or user in user_query:
                        # Record finding code
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

                        if record_continue:
                            run_count += 1
                            # Get Time
                            time = i["times"]["primary_t"]
                            time_result = str(datetime.timedelta(seconds=int(time)))

                            # Platform
                            platform = i["platform"]["data"]["name"]

                            # Date ago
                            date = datetime.date.fromisoformat(i["date"])
                            dateago = timeago.format(date, datetime.datetime.now())

                            json_result[len(json_result) - 1]["runs"].append({
                                "title": title,
                                "title_weblink": title_weblink,
                                "short_title": search_title,
                                "user": user,
                                "user_weblink": i["players"]["data"][0]["weblink"],
                                "time": time_result,
                                "weblink": i["weblink"],
                                "platform": platform,
                                "date": dateago
                            })

            found = False

            for y in queue["pagination"]["links"]:
                if y["rel"] == "next":
                    queue_url = y["uri"]
                    found = True
                    break

            if not found:
                break

        json_result[len(json_result) - 1]["run_count"] = run_count

    return json_result

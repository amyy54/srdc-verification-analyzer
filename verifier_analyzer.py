import json
import urllib
import urllib.request
import urllib.error
import datetime
import timeago
from flask import abort

ENDPOINT = "https://www.speedrun.com/api/v1/"
VERIFIERS = ENDPOINT + "runs?examiner={}&direction=desc&orderby=verify-date&" \
                       "embed=platform,players,category.variables,level&max=200"


def analyzer(examiner, game=None, exclusions=None):
    try:
        examiner_download = json.loads(urllib.request.urlopen(ENDPOINT + "users?lookup=" + examiner).read())
    except urllib.error.URLError:
        abort(503)
        return
    try:
        examiner = examiner_download["data"][0]["id"]
        examiner_name = examiner_download["data"][0]["names"]["international"]
    except:
        abort(404)
        return

    json_result = {
        "examiner": examiner_name,
        "runs": []
    }

    url = VERIFIERS.format(examiner)
    if game is not None:
        try:
            game_download = json.loads(urllib.request.urlopen(ENDPOINT + "games?abbreviation=" + game).read())
        except urllib.error.URLError:
            abort(503)
            return
        try:
            x = game_download["data"][0]["id"]
        except:
            abort(404)
            return
        url += "&game=" + x
    try:
        verified = json.loads(urllib.request.urlopen(url).read())
    except urllib.error.URLError:
        abort(503)
        return

    for i in verified["data"]:
        # print(i["weblink"])
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

        if exclusions is None or search_title not in exclusions:
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

                    user_weblink = ""

            # Get Time
            time = i["times"]["primary_t"]
            time_result = str(datetime.timedelta(seconds=int(time)))

            # Platform
            try:
                platform = i["platform"]["data"]["name"]
            except TypeError:
                # Multiple Mario Games
                platform = ""

            # Date ago
            date = datetime.date.fromisoformat(i["date"])
            dateago = timeago.format(date, datetime.datetime.now())
            if "hours" in dateago:
                dateago = "Today"

            verifyago = ""

            if i["status"]["status"] == "verified":
                status = "Verified"
                verify_date = i["status"]["verify-date"]
                if verify_date is not None:
                    # Support for really old runs
                    verify_date = verify_date.split("T", 1)[0]
                    verify_date = datetime.date.fromisoformat(verify_date)
                    verifyago = timeago.format(verify_date, datetime.datetime.now())
                    if "hours" in verifyago:
                        verifyago = "Today"
            else:
                status = "Rejected"

            json_result["runs"].append({
                "title": title,
                "title_weblink": title_weblink,
                "user": user,
                "user_weblink": user_weblink,
                "time": time_result,
                "weblink": i["weblink"],
                "platform": platform,
                "date": dateago,
                "verify-date": verifyago,
                "status": status
            })
    return json_result

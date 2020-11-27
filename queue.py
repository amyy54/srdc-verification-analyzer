import urllib
import urllib.request
import urllib.error
import json
import datetime


def load_queue(GAMES):
    webpage_result = ""

    for x in GAMES:
        # Fetch Game ID
        try:
            game = json.loads(urllib.request.urlopen("https://www.speedrun.com/api/v1/games?abbreviation=" + str(x)).read())
        except urllib.error.URLError:
            webpage_result += str(x) + " failed to connect. Please try again later"
            continue

        id = game["data"][0]["id"]

        # Fetch queue information
        try:
            queue = json.loads(urllib.request.urlopen("https://www.speedrun.com/api/v1/runs?game=" + str(id) + "&status=new&direction=asc&orderby=date&embed=platform,players,category.variables,level&max=200").read())
        except urllib.error.URLError:
            webpage_result += str(x) + " failed to connect. Please try again later"
            continue

        # Fetch game information (used for title)
        try:
            game_info = json.loads(urllib.request.urlopen("https://www.speedrun.com/api/v1/games/" + str(x)).read())
            game_name = game_info["data"]["names"]["international"]
        except urllib.error.URLError:
            game_name = str(x)

        webpage_result += "<h2>" + game_name + " - [" + str(len(queue["data"])) + "]</h2><br>"

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

            # Get Time
            time = i["times"]["primary_t"]
            time_result = str(datetime.timedelta(seconds=int(time)))

            # Platform
            platform = i["platform"]["data"]["name"]

            # Date ago
            # date = datetime.date.fromisoformat(i["date"])
            # dateago = timeago.format(date, datetime.datetime.now())
            dateago = i["date"]

            time_weblink = "<a href=" + i["weblink"] + ">" + time_result + "</a>"
            title_weblink = "<a href=" + title_weblink + ">" + title + "</a>"
            user_weblink = "<a href=" + i["players"]["data"][0]["weblink"] + ">" + user + "</a>"

            webpage_result += (title_weblink + " | " + user_weblink + " | " + time_weblink + " | " + platform + " | " + dateago) + "<br>"
            webpage_result += "----------------------------------<br>"

    return webpage_result

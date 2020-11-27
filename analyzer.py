import json
import urllib
import urllib.request
import urllib.error
import datetime
import matplotlib
import matplotlib.pyplot as plt

ENDPOINT = "https://www.speedrun.com/api/v1/"
GAME = ENDPOINT + "games?abbreviation={}&embed=moderators"
RUNS = ENDPOINT + "runs?game={}&direction=desc&orderby=date&max=200"
VERIFIED = ENDPOINT + "runs?game={}&status=verified&direction=desc&orderby=verify-date&max=200"
USERS = ENDPOINT + "users/{}"


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


def pie_chart(analyzer_data, filename="verifier_pie.png"):
    matplotlib.use("Agg")
    labels = []
    sizes = []
    colors = []
    for x in analyzer_data:
        if x["runs"] == 0:
            continue
        labels.append(x["name"])
        sizes.append(x["runs"])
        colors.append(x["color"])

    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
    plt.axis("equal")
    # plt.show()
    plt.savefig(filename)
    plt.close()


def manager(abbreviation, date=None, ending_date=None, includeLength=False):
    output = ""
    output_dict = {
        "game_name": "Testing",
        "in_queue": 0,
        "average_daily": 0,
        "verifier_analyzed": 0,
        "verifier_stats": [],
        "other_list": []
    }

    # Find game
    try:
        games = json.loads(urllib.request.urlopen(GAME.format(abbreviation)).read())
    except urllib.error.URLError:
        output += "Game request failed, aborting"
        return output
    try:
        output += games["data"][0]["names"]["international"] + "\n"
        output_dict["game_name"] = games["data"][0]["names"]["international"]
    except LookupError:
        output += "Game not found, aborting"
        return output

    # Get recent runs
    try:
        runs = json.loads(urllib.request.urlopen(RUNS.format(games["data"][0]["id"])).read())
    except urllib.error.URLError:
        output = "Run request failed, aborting"
        return output

    # Runs in queue
    queue = 0
    for x in runs["data"]:
        if x["status"]["status"] == "new":
            queue += 1
    output += "\nRuns in queue: {}\n".format(queue)
    output_dict["in_queue"] = queue

    # Average runs per day
    dates = []
    counter = 0
    recent_date = ""
    for x in runs["data"]:
        if len(recent_date) == 0:
            recent_date = x["date"]
            counter += 1
            continue

        if x["date"] != recent_date:
            recent_date = x["date"]
            dates.append(counter)
            counter = 0
        else:
            counter += 1
    total = 0
    for x in dates:
        total += x
    average = total / len(dates)

    output += "Average runs per day: {}\n".format(round(average, 2))
    output_dict["average_daily"] = round(average, 2)

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
            output = "Verified request failed, aborting"
            break

        for x in verified["data"]:
            date_of_run = datetime.datetime.strptime((x["status"]["verify-date"])[0:10], "%Y-%m-%d")
            if ending_date is not None and date_of_run > ending_date:
                continue

            if date is not None and date_of_run < starting_date:
                date_reached = True
                break

            not_other = False
            for i in moderators:
                if x["status"]["examiner"] == i["id"]:
                    i["count"] += 1
                    i["run_length"].append(x["times"]["primary_t"])
                    not_other = True
            if not not_other:
                other_count += 1
                other_list.append(x["status"]["examiner"])

        if date_reached:
            runs_analyzed_count = 0
            for x in moderators:
                runs_analyzed_count += x["count"]
            break
        elif starting_date is None:
            runs_analyzed_count += 200
            break

        else:
            found_endpoint = False
            runs_analyzed_count += 200
            for x in verified["pagination"]["links"]:
                if x["rel"] == "next":
                    verified_endpoint = x["uri"]
                    found_endpoint = True
                    break
            if not found_endpoint:
                break

    output += "\nVerifier Information:\n"
    output += "Runs Analyzed: {}\n\n".format(runs_analyzed_count)
    output_dict["verifier_analyzed"] = runs_analyzed_count

    for x in moderators:
        total = 0
        for i in x["run_length"]:
            total += i
        if total != 0:
            run_average = total / len(x["run_length"])
            run_average_date = datetime.timedelta(seconds=int(run_average))
        else:
            run_average_date = None
        percent = (x["count"] / runs_analyzed_count) * 100
        output += str(x["name"]) + ": {}% | {}\n".format(round(percent, 1), x["count"])
        output_dict["verifier_stats"].append({
            "name": x["name"],
            "runs": x["count"],
            "length": str(run_average_date),
            "color": x["mod_color"]
        })
        if includeLength:
            output += "\tAverage Length: {}\n".format(run_average_date)

    output_dict["verifier_stats"].append({
        "name": "Other",
        "runs": other_count,
        "length": "Not Tracked",
        "color": "#FFFFFF"
    })
    output_dict["other_list"] = other_list

    percent = (other_count / runs_analyzed_count) * 100
    output += "Other: {}%".format(round(percent, 1))

    if __name__ != "__main__":
        return output_dict
    else:
        return output


if __name__ == "__main__":
    print(manager("smoce", date="2020-11-01", includeLength=True))
    # testing()

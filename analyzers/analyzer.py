import json
import urllib
import urllib.request
import urllib.error
import datetime
from isodate import parse_datetime
import pytz
from analyzers import queue, average, sorting, combiner
from flask import abort

ENDPOINT = "https://www.speedrun.com/api/v1/"
GAME = ENDPOINT + "games?abbreviation={}&embed=moderators"
RUNS = ENDPOINT + "runs?game={}&direction=desc&orderby=date&max=200"
VERIFIED = ENDPOINT + "runs?game={}&status=verified&direction=desc&orderby=verify-date&max=200"
USERS = ENDPOINT + "users/{}"


def sort_list(analyzer_data):
    verified_list = []
    for x in analyzer_data['verifier_stats']:
        verified_list.append(x['runs'] + x['rejected_runs'])
    
    sorting.quickSort(verified_list, 0, len(verified_list) - 1)
    sorted_list = sorting.Reverse(verified_list)
    resulting_data = []
    checked_users = []
    for x in sorted_list:
        for y in analyzer_data['verifier_stats']:
            if x == (y['runs'] + y['rejected_runs']) and y['name'] not in checked_users:
                resulting_data.append(y)
                checked_users.append(y['name'])
    
    analyzer_data["verifier_stats"] = resulting_data
    return analyzer_data


def google_colors(analyzer_data):
    result = {}
    for pos, x in enumerate(analyzer_data, start=0):
        result[pos] = {'color': x["color"]}

    return result


def google_chart(analyzer_data, game_id):
    result = []
    for x in analyzer_data:
        result.append([x["name"] + " - " + str(x["runs"] + x['rejected_runs']), (x["runs"] + x['rejected_runs']), create_tooltip(x, game_id)])

    return result


def create_tooltip(analyzer_data, game_id):
    result = """<div style="padding:5px 5px 1px 5px">"""
    if analyzer_data['has_pfp']:
        result += f"""
            <img src="{analyzer_data['pfp_uri']}" style="width: 60px; height: 60px"><br><br>
        """
    if analyzer_data['name'] == "Other" or analyzer_data['name'] == "Broken User":
        result += f"""
            <strong>{analyzer_data['name']}</strong>
        """
    else:
        result += f"""
            <strong><a href="/verifier/{analyzer_data['name']}?game={analyzer_data['length'][0]['game_id']}">{analyzer_data['name']}</a></strong>
        """
    result += f"""
            <p><b>{analyzer_data['runs']}</b> Run(s) Verified</p>
    """
    if analyzer_data['rejected_runs'] != 0:
        result += f"""
            <p><b>{analyzer_data['rejected_runs']}</b> Run(s) Rejected</p>
        """
    if len(game_id.split(",")) > 1:
        result += """
        <p>Average Run Length: """
        for x in analyzer_data['length']:
            result += f"""<br>{x['game_id']}: <b>{x['length']}</b>"""
        result += "</p></div>"
    else:
        result += f"""
            <p>Average Run Length: <b>{analyzer_data['length'][0]['length']}</b></p>
            </div>
        """
    return result


def parse_other(other_list, game_id):
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
        
        try:
            user_info = json.loads(urllib.request.urlopen(USERS.format(x)).read())
        except urllib.error.HTTPError:
            verifier_stats.append({
                "id": x,
                "name": "Broken User",
                "runs": 1,
                "rejected_runs": 0,
                "length": [{
                    'game_id': game_id,
                    'length': "Not Tracked"
                }],
                "color": "#000000",
                "has_pfp": False,
                'pfp_uri': ""
            })
            continue

        if user_info["data"]["name-style"]["style"] == "solid":
            color = user_info["data"]["name-style"]["color"]["light"]
        else:
            color = user_info["data"]["name-style"]["color-from"]["light"]

        pfp_uri = user_info["data"]["assets"]["image"]["uri"]
        if pfp_uri is None:
            pfp_exists = False
        else:
            pfp_exists = True

        verifier_stats.append({
            "id": user_info["data"]["id"],
            "name": user_info["data"]["names"]["international"],
            "runs": 1,
            "rejected_runs": 0,
            "length": [{
                'game_id': game_id,
                'length': "Not Tracked"
            }],
            "color": color,
            "has_pfp": pfp_exists,
            'pfp_uri': pfp_uri
        })

    return verifier_stats


def get_analyzer_response(games, start_date, end_date, parse_var, minimal_mode, timezone, rejected, leaderboard_page=False):
    analyzer_data = []
    for x in games:
        verifier_stats = []
        temp_data = manager(x, date=start_date, ending_date=end_date, timezone=timezone, minimal=minimal_mode, include_rejects=rejected)
        if not leaderboard_page:
            for x in temp_data["verifier_stats"]:
                if x["runs"] != 0 or x['rejected_runs'] != 0:
                    verifier_stats.append(x)
            temp_data["verifier_stats"] = verifier_stats
        analyzer_data.append(temp_data)

    analyzer_data = combiner.combiner(analyzer_data)

    if parse_var and len(analyzer_data["other_list"]) > 0:
        other_data = parse_other(analyzer_data["other_list"], analyzer_data['game_id'])
        analyzer_data['verifier_stats'] = analyzer_data['verifier_stats'][:-1]
        analyzer_data['verifier_stats'] += other_data
    
    return analyzer_data


def manager(abbreviation, date=None, ending_date=None, minimal=False, timezone="UTC", include_rejects=False):
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

    try:
        tz = pytz.timezone(timezone)
    except:
        tz = pytz.UTC

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
    if not minimal:
        output_dict["in_queue"] = len(queue.load_queue(abbreviation.split(","))[0]["runs"])
    output_dict["background_image"] = games["data"][0]["assets"]["background"]["uri"]

    # Verifier Information
    moderators = []
    for x in games["data"][0]["moderators"]["data"]:
        if x["name-style"]["style"] == "solid":
            color = x["name-style"]["color"]["light"]
        else:
            color = x["name-style"]["color-from"]["light"]
        # print(x["name-style"])

        pfp_uri = x["assets"]["image"]["uri"]
        if pfp_uri is None:
            pfp_exists = False
        else:
            pfp_exists = True

        moderators.append({
            "id": x["id"],
            "name": x["names"]["international"],
            "count": 0,
            "rejected_count": 0,
            "run_length": [],
            "has_pfp": pfp_exists,
            'pfp_uri': pfp_uri,
            "mod_color": color})

    runs_analyzed_count = 0
    other_count = 0
    other_list = []

    verified_endpoint = VERIFIED.format(games["data"][0]["id"])
    reversed_order = False
    list_of_runs = []
    if date is not None:
        starting_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        starting_date = tz.localize(starting_date)
        starting_date.replace(tzinfo=tz)

    else:
        starting_date = None

    if ending_date is not None:
        end_date = datetime.datetime.strptime(ending_date, "%Y-%m-%d")
        end_date = tz.localize(end_date)
        end_date.replace(tzinfo=tz)

    while True:
        date_reached = False

        try:
            verified = json.loads(urllib.request.urlopen(verified_endpoint).read())
        except urllib.error.URLError:
            abort(503)
            return

        for x in verified["data"]:
            date_of_run = parse_datetime(x["status"]["verify-date"])

            if reversed_order:
                if ending_date is not None and date_of_run > end_date:
                    date_reached = True
                    break

                if date is not None and date_of_run < starting_date:
                    continue

                if x["id"] in list_of_runs:
                    date_reached = True
                    break
            else:
                if ending_date is not None and date_of_run > end_date:
                    continue

                if date is not None and date_of_run < starting_date:
                    date_reached = True
                    break

            not_other = False
            runs_analyzed_count += 1
            if not reversed_order:
                list_of_runs.append(x["id"])
            average_verified.append(date_of_run.timetuple().tm_yday)
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
                    if verified_endpoint[-5:] == "10000":
                        verified_endpoint = verified_endpoint.replace('direction=desc', 'direction=asc')
                        verified_endpoint = verified_endpoint[:-13]
                        reversed_order = True
                    found_endpoint = True
                    break
            if not found_endpoint:
                break

    if include_rejects:
        reversed_order = False
        verified_endpoint = VERIFIED.format(games["data"][0]["id"])
        verified_endpoint = verified_endpoint.replace("verified", "rejected")
        while True:
            date_reached = False

            try:
                verified = json.loads(urllib.request.urlopen(verified_endpoint).read())
            except urllib.error.URLError:
                abort(503)
                return

            for x in verified["data"]:
                date_of_run = datetime.datetime.strptime(x["date"], "%Y-%m-%d")
                date_of_run = date_of_run.replace(tzinfo=tz)

                if reversed_order:
                    if ending_date is not None and date_of_run > end_date:
                        date_reached = True
                        break

                    if date is not None and date_of_run < starting_date:
                        continue

                    if x["id"] in list_of_runs:
                        date_reached = True
                        break
                else:
                    if ending_date is not None and date_of_run > end_date:
                        continue

                    if date is not None and date_of_run < starting_date:
                        date_reached = True
                        break

                not_other = False
                runs_analyzed_count += 1
                if not reversed_order:
                    list_of_runs.append(x["id"])
                average_verified.append(date_of_run.timetuple().tm_yday)
                for i in moderators:
                    if x["status"]["examiner"] == i["id"]:
                        i["rejected_count"] += 1
                        not_other = True
                if not not_other:
                    pass

            if date_reached or starting_date is None:
                break

            else:
                found_endpoint = False
                for x in verified["pagination"]["links"]:
                    if x["rel"] == "next":
                        verified_endpoint = x["uri"]
                        if verified_endpoint[-5:] == "10000":
                            verified_endpoint = verified_endpoint.replace('direction=desc', 'direction=asc')
                            verified_endpoint = verified_endpoint[:-13]
                            reversed_order = True
                        found_endpoint = True
                        break
                if not found_endpoint:
                    break

    output_dict["verifier_analyzed"] = runs_analyzed_count
    if not minimal:
        output_dict["average_daily"] = average.get_average(games["data"][0]["id"], date, ending_date)

    try:
        range = max(average_verified) - min(average_verified)
    except ValueError:
        range = 0
    
    try:
        output_dict["verified_daily"] = runs_analyzed_count / range
    except ZeroDivisionError:
        output_dict["verified_daily"] = 0

    for x in moderators:
        total = 0
        for i in x["run_length"]:
            total += i
        if total != 0:
            run_average = total / len(x["run_length"])
            run_average_date = datetime.timedelta(seconds=int(run_average))
        else:
            run_average_date = None

        output_dict["verifier_stats"].append({
            "id": x["id"],
            "name": x["name"],
            "runs": x["count"],
            "rejected_runs": x["rejected_count"],
            "length": [{
                'game_id': output_dict["game_id"],
                'length': str(run_average_date)
            }],
            "has_pfp": x["has_pfp"],
            'pfp_uri': x["pfp_uri"],
            "color": x["mod_color"]
        })

    output_dict["verifier_stats"].append({
        "name": "Other",
        "runs": other_count,
        "rejected_runs": 0,
        "length": [{
                'game_id': output_dict["game_id"],
                'length': "Not Tracked"
            }],
        "color": "#000000",
        "has_pfp": False,
        'pfp_uri': None,
    })
    output_dict["other_list"] = other_list

    return output_dict

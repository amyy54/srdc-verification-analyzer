import urllib
import urllib.request
import urllib.error
import json
from flask import abort
from analyzers import run_parser


def load_queue(GAMES, category=None, user_query=None, queue_order="date", exclusions=None, get_records=False, timerange=None):
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

        # Fetch game information (used for title)
        try:
            game_info = json.loads(
                urllib.request.urlopen("https://www.speedrun.com/api/v1/games/" + str(id)).read())
            game_name = game_info["data"]["names"]["international"]
        except urllib.error.URLError:
            game_name = id

        queue_url = "https://www.speedrun.com/api/v1/runs?game=" + str(id) + "&status=new&direction=asc&orderby=" + queue_order + "&embed=platform,players,category.variables,level&max=200"

        json_result.append({
            "game_name": game_name,
            "runs": [],
            "run_count": 0,
            "game_id": x
        })

        while True:
            # Fetch queue information
            try:
                queue = json.loads(urllib.request.urlopen(queue_url).read())
            except urllib.error.URLError:
                abort(503)
                return

            for i in queue["data"]:
                parsed_run = run_parser.run_parser(i, category=category, user_query=user_query, exclusions=exclusions, get_records=get_records, records=records, id=id, timerange=timerange)
                if parsed_run is not None:
                    json_result[len(json_result) - 1]['runs'].append(parsed_run)

            found = False

            for y in queue["pagination"]["links"]:
                if y["rel"] == "next":
                    queue_url = y["uri"]
                    found = True
                    break

            if not found:
                break

        json_result[len(json_result) - 1]["run_count"] = len(json_result[len(json_result) - 1]["runs"])

    return json_result

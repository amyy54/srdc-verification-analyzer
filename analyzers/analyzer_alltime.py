import json
import urllib
import urllib.request
import urllib.error
from flask import abort

ENDPOINT = "https://www.speedrun.com/api/v1/"
GAME = ENDPOINT + "games?abbreviation={}&embed=moderators"
VERIFIED = "https://www.speedrun.com/_fedata/user/stats?userId={}"

def manager(abbreviation):
    output_dict = {
        "game_name": "Testing",
        "game_id": "1234",
        "verifier_analyzed": 0,
        "verifier_stats": [],
    }

    # Find game
    games = json.loads(urllib.request.urlopen(GAME.format(abbreviation)).read())

    try:
        output_dict["game_name"] = games["data"][0]["names"]["international"]
        output_dict["game_id"] = abbreviation
    except LookupError:
        abort(404)
        return

    # Runs in queue
    output_dict["background_image"] = games["data"][0]["assets"]["background"]["uri"]

    # Verifier Information
    moderators = []
    for x in games["data"][0]["moderators"]["data"]:
        if x["name-style"]["style"] == "solid":
            color = x["name-style"]["color"]["light"]
        else:
            color = x["name-style"]["color-from"]["light"]

        pfp_uri = x["assets"]["image"]["uri"]
        if pfp_uri is None:
            pfp_exists = False
        else:
            pfp_exists = True

        moderators.append({
            "id": x["id"],
            "name": x["names"]["international"],
            "count": 0,
            "has_pfp": pfp_exists,
            'pfp_uri': pfp_uri,
            "mod_color": color})

    runs_analyzed_count = 0

    for x in moderators:
        data = json.loads(urllib.request.urlopen(VERIFIED.format(x['id'])).read())
        for y in data['modStats']:
            if y['game']['url'] == abbreviation:
                x['count'] = y['totalRuns']
                runs_analyzed_count += y['totalRuns']
                break
        
        output_dict["verifier_stats"].append({
            "id": x["id"],
            "name": x["name"],
            "runs": x["count"],
            "rejected_runs": 0,
            "has_pfp": x["has_pfp"],
            'pfp_uri': x["pfp_uri"],
            "color": x["mod_color"]
        })

    output_dict["verifier_analyzed"] = runs_analyzed_count

    return output_dict

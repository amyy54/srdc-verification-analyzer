import json
import urllib
import urllib.request
import urllib.error
from flask import abort
from analyzers import run_parser


ENDPOINT = "https://www.speedrun.com/api/v1/"
VERIFIERS = ENDPOINT + "runs?examiner={}&direction=desc&orderby=verify-date&" \
                       "embed=platform,players,category.variables,level,game&max=200"


def analyzer(examiner, game=None, exclusions=None, status=None):
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
    if status == 'rejected':
        url += "&status=rejected"
    elif status == 'verified':
        url += "&status=verified"
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
        parsed_run = run_parser.run_parser(i, exclusions=exclusions, verifier=True)
        if parsed_run is not None:
            json_result['runs'].append(parsed_run)

    return json_result

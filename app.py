from analyzers import analyzer, queue, verifier_analyzer, analyzer_alltime
from flask import Flask, request, render_template, abort, redirect, url_for
from flask.helpers import make_response
from convert_time import convert_time
import pytz
from json import dumps
import os

app = Flask(__name__)

AUTHOR_LINK = os.environ.get("AUTHOR_LINK")
DOCS = os.environ.get("DOCS")

REGIONS = ['br_', 'cn_', 'eu_', 'jp_', 'kr_', 'us_']


@app.errorhandler(500)
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(503)
def error(e):
    response = e.get_response()

    response.data = dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
        "contact": {
            "message": "If there is reason to believe that this error is caused by the fault of the server, "
                       "please send a message indicating the request made and the error code provided.",
            "link": AUTHOR_LINK
        }
    })

    response.content_type = "application/json"

    return response


@app.route("/")
def main():
    return render_template("index.html", docs_url=DOCS if DOCS else "/docs")


@app.route("/set_timezone", methods=["POST", "GET"])
def set_timezone():
    if request.method == "POST":
        form_data = dict(request.form)
        timezone = form_data["tz_input"]
        resp = make_response(render_template('set_timezone.html', timezones=pytz.all_timezones))
        if timezone == "Clear":
            resp.set_cookie('tz', '', expires=0)
        else:
            resp.set_cookie('tz', timezone)
        return resp
    else:
        return render_template('set_timezone.html', timezones=pytz.all_timezones)


@app.route("/data/<games>")
def data(games=None):
    if games is None:
        abort(405)

    games = games.split(",")
    start_date = request.args.get("startdate")
    end_date = request.args.get("enddate")
    parse_other = request.args.get("parseother")
    short_time_ref = request.args.get("t")
    minimal_mode = request.args.get("minimal")
    include_rejected = request.args.get("rejects")

    timezone = request.cookies.get('tz')
    if timezone is None:
        timezone = "UTC"

    if short_time_ref is not None and (start_date is None and end_date is None):
        start_date_temp = convert_time(short_time_ref)
        if start_date_temp is not None:
            start_date = start_date_temp

    analyzer_data = analyzer.get_analyzer_response(games, start_date, end_date, parse_other, minimal_mode, timezone, include_rejected)

    google_chart = analyzer.google_chart(analyzer_data["verifier_stats"], analyzer_data['game_id'])

    google_colors = analyzer.google_colors(analyzer_data["verifier_stats"])
    return render_template("./data.html",
                           analyzer_info=analyzer_data,
                           chart_data=dumps(google_chart),
                           chart_colors=google_colors,
                           isMinimal=minimal_mode)


@app.route("/data/<games>/json")
def data_json(games=None):
    if games is None:
        abort(405)

    games = games.split(",")
    start_date = request.args.get("startdate")
    end_date = request.args.get("enddate")
    parse_other = request.args.get("parseother")
    short_time_ref = request.args.get("t")
    include_rejected = request.args.get("rejects")

    timezone = request.cookies.get('tz')
    if timezone is None:
        timezone = "UTC"

    if short_time_ref is not None and (start_date is None and end_date is None):
        start_date_temp = convert_time(short_time_ref)
        if start_date_temp is not None:
            start_date = start_date_temp

    analyzer_data = analyzer.get_analyzer_response(games, start_date, end_date, parse_other, False, timezone, include_rejected)

    result = {
        "code": 200,
        "data": analyzer_data,
    }

    return result


@app.route("/leaderboard/<games>")
def data_sorted(games=None):
    if games is None:
        abort(405)

    games = games.split(",")
    start_date = request.args.get("startdate")
    end_date = request.args.get("enddate")
    parse_other = request.args.get("parseother")
    short_time_ref = request.args.get("t")
    include_rejected = request.args.get("rejects")

    timezone = request.cookies.get('tz')
    if timezone is None:
        timezone = "UTC"

    if short_time_ref == "alltime":
        analyzer_data = analyzer_alltime.manager(games[0])
        include_rejected = False
    else:
        if short_time_ref is not None and (start_date is None and end_date is None):
            start_date_temp = convert_time(short_time_ref)
            if start_date_temp is not None:
                start_date = start_date_temp

        analyzer_data = analyzer.get_analyzer_response(games, start_date, end_date, parse_other, True, timezone, include_rejected, leaderboard_page=True)

    analyzer_data = analyzer.sort_list(analyzer_data)
    return render_template('./leaderboard.html', analyzer_info=analyzer_data, show_rejects=include_rejected)


@app.route("/queue/", methods=["POST", "GET"])
def queue_page():
    if request.method == 'GET':
        query = request.args.get("abbreviation")
        if query is None:
            return redirect(url_for("main"))
        else:
            return redirect(url_for('queue_page_with_directory', games=query, category=request.args.get("category"),
                                    user_query=request.args.get("user"), order_by=request.args.get("orderby")))


@app.route("/queue/<games>")
def queue_page_with_directory(games=None, category=None, user_query=None, order_by=None):
    if games is None:
        return abort(405)
    category = request.args.get("category")
    user_query = request.args.get("user")
    order_by = request.args.get("orderby")
    excluded_items = request.args.get("exclude")
    time_range = request.args.get("time")
    if category is not None:
        category = category.split(",")
    if user_query is not None:
        user_query = user_query.split(",")
    if order_by is None:
        order_by = "date"
    if excluded_items is not None:
        excluded_items = excluded_items.split(",")

    return render_template("./queue.html",
                           queue_data=queue.load_queue(games.split(","), category=category,
                                                       user_query=user_query, queue_order=order_by,
                                                       exclusions=excluded_items, timerange=time_range), 
                                                       gamereq=games,
                                                       REGIONS=REGIONS)


@app.route("/queue/<games>/records")
def records_page(games=None):
    if games is None:
        return abort(405)
    category = request.args.get("category")
    user_query = request.args.get("user")
    order_by = request.args.get("orderby")
    excluded_items = request.args.get("exclude")
    if category is not None:
        category = category.split(",")
    if user_query is not None:
        user_query = user_query.split(",")
    if order_by is None:
        order_by = "date"
    if excluded_items is not None:
        excluded_items = excluded_items.split(",")

    return render_template("./queue.html",
                           queue_data=queue.load_queue(games.split(","), category=category,
                                                       user_query=user_query, queue_order=order_by,
                                                       exclusions=excluded_items, get_records=True), 
                                                       gamereq=games,
                                                       REGIONS=REGIONS)


@app.route("/verifier/<examiner>")
def verifier_page(examiner=None):
    if examiner is None:
        return abort(405)
    game = request.args.get("game")
    status = request.args.get("status")

    excluded_items = request.args.get("exclude")
    if excluded_items is not None:
        excluded_items = excluded_items.split(",")

    return render_template("./verifier.html",
                           verifier_data=verifier_analyzer.analyzer(examiner, game=game, exclusions=excluded_items, status=status), REGIONS=REGIONS)


if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)

import analyzer
import queue
import verifier_analyzer
import record_finder
from flask import Flask, request, render_template, abort, redirect, url_for
import os
from json import dumps

app = Flask(__name__, static_folder=os.getcwd())

TWITTER = "https://twitter.com/aMinibeast"

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
                       "please send a message on twitter indicating the request made and the error code provided.",
            "link": TWITTER
        }
    })

    response.content_type = "application/json"

    return response


@app.route("/")
def main():
    return open("index.html").read()


@app.route("/data/<game>")
def data(game=None):
    if game is None:
        abort(405)

    start_date = request.args.get("startdate")
    end_date = request.args.get("enddate")
    parse_other = request.args.get("parseother")

    analyzer_data = analyzer.manager(game, date=start_date, ending_date=end_date)

    if analyzer_data is None:
        return abort(400)

    google_chart = analyzer.google_chart(analyzer_data["verifier_stats"])

    google_colors = analyzer.google_colors(analyzer_data["verifier_stats"])

    if parse_other and len(analyzer_data["other_list"]) > 0:
        other_data = analyzer.parse_other(analyzer_data["other_list"])

        other_chart = analyzer.google_chart(other_data)
        other_colors = analyzer.google_colors(other_data)

    else:
        parse_other = False
        other_chart = []
        other_colors = {}
    return render_template("./data.html",
                           game_fullname=analyzer_data["game_name"],
                           game_id=analyzer_data["game_id"],
                           in_queue=str(analyzer_data["in_queue"]),
                           average_daily=str(analyzer_data["average_daily"]),
                           average_verified=str(analyzer_data["verified_daily"]),
                           verifier_analyzed=str(analyzer_data["verifier_analyzed"]),
                           general_info=analyzer_data["verifier_stats"],
                           display_other=parse_other,
                           chart_data=dumps(google_chart),
                           chart_colors=google_colors,
                           other_google_chart=dumps(other_chart),
                           other_google_colors=other_colors)


@app.route("/queue/", methods=["POST", "GET"])
def queue_page():
    if request.method == 'GET':
        query = request.args.get("abbreviation")
        if query is None:
            return redirect("/")
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
                                                       exclusions=excluded_items))


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
                           queue_data=record_finder.find_records(games.split(","), category=category,
                                                                 user_query=user_query, queue_order=order_by,
                                                                 exclusions=excluded_items))


@app.route("/verifier/<examiner>")
def verifier_page(examiner=None):
    if examiner is None:
        return abort(405)
    game = request.args.get("game")

    excluded_items = request.args.get("exclude")
    if excluded_items is not None:
        excluded_items = excluded_items.split(",")

    return render_template("./verifier.html",
                           verifier_data=verifier_analyzer.analyzer(examiner, game=game, exclusions=excluded_items))


if __name__ == '__main__':
    app.run(host="localhost", port=5000)

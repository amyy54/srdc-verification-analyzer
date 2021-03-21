import analyzer
import queue
from flask import Flask, request, render_template, abort, redirect
import os
from json import dumps

app = Flask(__name__, static_folder=os.getcwd())


@app.errorhandler(404)
def error_404(e):
    return open("./errors/error.html").read()


@app.errorhandler(500)
def error_500(e):
    return open("./errors/server_error.html").read()


@app.errorhandler(400)
def error_400(e):
    return open("./errors/400_error.html").read()


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
                           in_queue=str(analyzer_data["in_queue"]),
                           average_daily=str(analyzer_data["average_daily"]),
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

        category = request.args.get("category")
        user_query = request.args.get("user")
        order_by = request.args.get("orderby")
        if category is not None:
            category = category.split(",")
        if user_query is not None:
            user_query = user_query.split(",")
        if order_by is None:
            order_by = "date"

        return render_template("./queue.html",
                               queue_data=queue.load_queue(query.split(","), category=category,
                                                           user_query=user_query, queue_order=order_by))
    if request.method == 'POST':
        form_data = dict(request.form)
        return render_template("./queue.html",
                               queue_data=queue.load_queue(form_data["abbreviation"].split(", ")))


@app.route("/queue/<games>")
def queue_page_with_directory(games=None):
    if games is None:
        return abort(405)
    category = request.args.get("category")
    user_query = request.args.get("user")
    order_by = request.args.get("orderby")
    if category is not None:
        category = category.split(",")
    if user_query is not None:
        user_query = user_query.split(",")
    if order_by is None:
        order_by = "date"

    return render_template("./queue.html",
                           queue_data=queue.load_queue(games.split(","), category=category,
                                                       user_query=user_query, queue_order=order_by))


if __name__ == '__main__':
    app.run(host="localhost", port=5000)

import analyzer
import queue
from flask import Flask, request, render_template, abort, Response
import os
from json import dumps

app = Flask(__name__, static_folder=os.getcwd())


@app.route("/")
def main():
    return open("index.html").read()


@app.route("/data/", methods=['POST', 'GET'])
def data():
    if request.method == 'GET':
        return abort(405)
    if request.method == 'POST':
        form_data = dict(request.form)
        if len(form_data["start_date"]) > 0:
            date = form_data["start_date"]
        else:
            date = None

        if len(form_data["end_date"]) > 0:
            end_date = form_data["end_date"]
        else:
            end_date = None

        try:
            parse_other = form_data["other_parse"] == "on"
        except KeyError:
            parse_other = False

        analyzer_data = analyzer.manager(form_data["abbreviation"], date=date, ending_date=end_date)

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
        category = request.args.get("category")
        user_query = request.args.get("user")
        order_by = request.args.get("orderby")
        if category is not None:
            category = category.split(",")
        if user_query is not None:
            user_query = user_query.split(",")
        if order_by is None:
            order_by = "date"

        if query is None:
            return abort(405)
        return render_template("./queue.html",
                               queue_data=queue.load_queue(query.split(","), category=category, user_query=user_query,
                                                           queue_order=order_by))
    if request.method == 'POST':
        form_data = dict(request.form)
        return render_template("./queue.html",
                               queue_data=queue.load_queue(form_data["abbreviation"].split(", ")))


if __name__ == '__main__':
    app.run(host="localhost", port=5000)

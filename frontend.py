import analyzer
import queue
from flask import Flask, request, render_template
import os

app = Flask(__name__, static_folder=os.getcwd())


@app.route("/")
def main():
    return open("index.html").read()


@app.route("/data/", methods=['POST', 'GET'])
def data():
    if request.method == 'GET':
        return "Only POST requests are accepted"
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
        analyzer.pie_chart(analyzer_data["verifier_stats"])

        if parse_other and len(analyzer_data["other_list"]) > 0:
            other_data = analyzer.parse_other(analyzer_data["other_list"])
            analyzer.pie_chart(other_data, filename="other_pie.png")
        else:
            parse_other = False
            other_data = []
        return render_template("./data.html",
                               game_fullname=analyzer_data["game_name"],
                               in_queue=str(analyzer_data["in_queue"]),
                               average_daily=str(analyzer_data["average_daily"]),
                               verifier_analyzed=str(analyzer_data["verifier_analyzed"]),
                               general_info=analyzer_data["verifier_stats"],
                               image_source="verifier_pie.png",
                               display_other=parse_other,
                               other_source="other_pie.png",
                               other_info=other_data)


@app.route("/queue/", methods=["POST", "GET"])
def queue_page():
    if request.method == 'GET':
        query = request.args.get("abbreviation")
        if query is None:
            return "Only POST requests or query strings are accepted"
        
        return queue.load_queue(query.split(","))
    if request.method == 'POST':
        form_data = dict(request.form)
        return queue.load_queue(form_data["abbreviation"].split(", "))


app.run(host="localhost", port=5000)

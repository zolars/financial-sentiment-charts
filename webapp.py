import sys
import json
import datetime as dt

from flask import Flask, render_template, request
from jinja2 import Markup, Environment, FileSystemLoader
from pyecharts import options as opts
from pyecharts.charts import Page

from tweet_engine import catch_pages_history
from sentiment_chart import gen_sentiment_chart
from stock_chart import gen_stock_chart

from multiprocessing import Process, Queue

app = Flask(__name__, static_folder="templates")
stock_id_set = []
query_list = []
pool = []


@app.route("/")
def index():
    return render_template("charts.html")


@app.route("/search", methods=['GET'])
def get_query():
    query = request.args.get('q')


@app.route("/scrapers", methods=['POST', 'GET'])
def changeScrapers():

    global stock_id_set, query_list

    if request.method == 'POST':
        op = request.form['op']
        stock_id = request.form['stock_id']
        query = request.form['query']

    else:
        op = request.args.get('op')
        stock_id = request.args.get('stock_id')
        query = request.args.get('query')

    if op == 'add':
        if len(stock_id_set) >= 4:
            return 'Error: The amount of scrapers is up to 4.'
        elif stock_id in stock_id_set:
            return 'Error: The stock_id is duplicated.'
        else:
            stock_id_set.append(stock_id)
            query_list.append(query)
            p = Process(target=catch_pages_history, args=(query, stock_id))
            pool.append(p)
            pool[-1].start()
            return 'success'

    elif op == 'remove':
        if stock_id not in stock_id_set:
            return 'Error: The stock_id is not existed.'
        else:
            index = stock_id_set.index(stock_id)
            del stock_id_set[index]
            del query_list[index]
            pool[index].terminate()
            del pool[index]
            return 'success'


@app.route("/charts", methods=['POST', 'GET'])
def get_charts():
    if request.method == 'POST':
        stock_id = request.form['stock_id']
        query = request.form['query']

    else:
        stock_id = request.args.get('stock_id')
        query = request.args.get('query')

    # p = Process(target=catch_pages_history, args=(query, stock_id))
    # p.start()

    sentiment_chart, startdate, enddate = gen_sentiment_chart(stock_id)
    stock_chart = gen_stock_chart(stock_id, startdate, enddate)
    sentiment_chart.overlap(stock_chart)
    return json.dumps({"chart": json.loads(sentiment_chart.dump_options())})


if __name__ == "__main__":
    app.run(debug=False)
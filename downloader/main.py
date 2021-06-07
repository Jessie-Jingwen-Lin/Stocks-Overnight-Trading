import os

import flask
from flask import Flask, request
import pickle
import io

import stockdata

app = Flask(__name__)

def download_the_tickers(tickers):
  return tickers

@app.route("/", methods=["POST"])
def download_fn():
  key = request.args.get("key")
  if key != "2MxXduKP4B":
    return "Hello World!"

  tickers_data = request.files["tickers"]
  tickers = pickle.load(tickers_data)

  from_date_data = request.files["from_date"]
  from_date = pickle.load(from_date_data)

  to_date_data = request.files["to_date"]
  to_date = pickle.load(to_date_data)

  results = stockdata.fetch_stock_data(tickers, from_date, to_date)
  

  bytes = io.BytesIO()
  pickle.dump(results, bytes)
  bytes.seek(0)

  return flask.send_file(bytes, "application/octet-stream")


if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
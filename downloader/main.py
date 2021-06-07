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
def hello_world():
  key = request.args.get("key")
  if key != "2MxXduKP4B":
    return "Hello World!"

  tickers_data = request.files["tickers"]
  tickers = pickle.load(tickers_data)
  results = download_the_tickers(tickers)

  bytes = io.BytesIO()
  pickle.dump(results, bytes)
  bytes.seek(0)

  return flask.send_file(bytes, "application/octet-stream")


if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
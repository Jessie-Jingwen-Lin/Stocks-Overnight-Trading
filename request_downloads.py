import requests
import io
import pickle
from pytz import timezone
import datetime

def request_google_download(tickers, from_date, to_date, url):
  print("Sending request for {} tickers to: {}".format(len(tickers), url))

  bytes = io.BytesIO()
  pickle.dump(tickers, bytes)
  bytes.seek(0)

  bytes_from = io.BytesIO()
  pickle.dump(from_date, bytes_from)
  bytes_from.seek(0)

  bytes_to = io.BytesIO()
  pickle.dump(to_date, bytes_to)
  bytes_to.seek(0)

  files = {'tickers': bytes, 'from_date': bytes_from, 'to_date': bytes_to}  
  r = requests.post(url, files=files, params={"key": "2MxXduKP4B"})

  print("Received response from: {}".format(url))

  # print(r)
  # print(r.content)
  bytes = io.BytesIO(r.content)
  results = pickle.load(bytes)
  return results
  # print(r.text)
  
def main():
  eastern = timezone('US/Eastern')
  loc_dt = datetime.datetime.now(eastern)
  today = loc_dt.date()
  days_ago_729 = today - datetime.timedelta(days=729)
  print(request_google_download(['AAPL', 'TSLA', 'FB', 'MSFT'], days_ago_729, today, 'https://yf-0-ecf7h7bkga-uc.a.run.app'))

if __name__ == "__main__":
  main()
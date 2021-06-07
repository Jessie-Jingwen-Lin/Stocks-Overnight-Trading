import requests
import io
import pickle

def request_download(tickers, from_date, to_date):
  url = "https://yf-0-ecf7h7bkga-uc.a.run.app"
  
  tickers = ["AAPL", "TSLA", "FB"]

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
  bytes = io.BytesIO(r.content)
  results = pickle.load(bytes)
  print(results)
  # print(r.text)
  

def main():
  request_download(['AAPL', 'TSLA', 'FB'], )
if __name__ == "__main__":
  main()
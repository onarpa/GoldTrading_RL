import requests

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
# api-key : UPNWRYXZ293J6SHT
url = 'https://www.alphavantage.co/query?function=GOLD_SILVER_SPOT&symbol=SILVER&apikey=UPNWRYXZ293J6SHT'
r = requests.get(url)
data = r.json()

print(data)
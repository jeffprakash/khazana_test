import requests

def fetch_asset_price(asset_name):
    API_URL = f"https://api.coingecko.com/api/v3/simple/price"
    response = requests.get(API_URL, params={"ids": asset_name, "vs_currencies": "usd"})
    if response.status_code == 200:
        return response.json().get(asset_name, {}).get("usd", 0)
    return None


import requests
from . import cache
from datetime import datetime

# Fetch real-time data (e.g., stock, crypto, forex)
@cache.cached(timeout=3600, key_prefix="get_asset_price")
def get_asset_price(asset_name):
    api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset_name}&vs_currencies=usd"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get(asset_name, {}).get('usd', None)
    return None

# Update price history in the database
def update_price_history(asset_id, price):
    from .models import PriceHistory, db
    today = datetime.utcnow().date()
    existing_entry = PriceHistory.query.filter_by(asset_id=asset_id, date=today).first()
    if not existing_entry:
        new_entry = PriceHistory(asset_id=asset_id, date=today, price=price)
        db.session.add(new_entry)
        db.session.commit()







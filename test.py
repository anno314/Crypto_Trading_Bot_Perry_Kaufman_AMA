# Libraries
from binance.client import Client
import pandas as pd
import numpy as np
import time
import datetime
import csv
import smtplib
import helpfunctions
import schedule

# API and Account Setup
client = helpfunctions.connect_to_binance_client()

# Check Conection and Account
account_df = client.get_account()
assets_len = len(account_df['balances'])

def task():
    print("ANDRE")


asset= "BTCUSDT"
#schedule.every(5).seconds.do(helpfunctions.try_import_daily_data(client, asset))  # Try to download latest daily price data from binance
schedule.every(10).seconds.do(task)
while True:
    df = schedule.run_pending()


    # Get the current time
    now = datetime.datetime.now()

    # Calculate the time until 8am tomorrow
    tomorrow = now + datetime.timedelta(days=1)
    target_time = datetime.datetime.combine(tomorrow, datetime.time(hour=8))

    # Sleep until 8am tomorrow
    time.sleep((target_time - now).total_seconds())
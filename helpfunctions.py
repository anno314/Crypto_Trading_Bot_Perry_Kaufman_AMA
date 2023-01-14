# Libraries
from binance.client import Client
import pandas as pd
import numpy as np
import time
import datetime
import smtplib

# API and Account Setup
def connect_to_binance_client():
    file_api = open('C:/Users/Admin/Documents/Python_Projekte/Crypto_Trading/Binance/API.txt')
    doc_api = file_api.readlines()
    api_key = doc_api[1].replace('\n','')
    api_secret = doc_api[3].replace('\n','')
    return Client(api_key, api_secret)

def print_account_balance(client):
    account_df = client.get_account()
    assets_len = len(account_df['balances'])

    print('### Account Balance ###')
    for i in range(assets_len):
        asset_name = account_df['balances'][i]['asset']
        asset_free = float(account_df['balances'][i]['free'])

        if asset_free != 0:
            print(f'asset: {asset_name}; free: {asset_free}')
    print('### Account Balance ###')

# Send Mail
def send_mail(text):
    # API setup
    file_mail = open('C:/Users/Admin/Documents/Python_Projekte/Crypto_Trading/web.de/file.txt')
    doc_mail = file_mail.readlines()
    mail_key = doc_mail[3].replace('\n', '')
    mail_user = doc_mail[1].replace('\n', '')

    # input for mail
    mail_text = text
    mail_subject = 'Crypto Trading Bot'
    mail_from = mail_user
    mail_to = mail_user

    # send mail
    mail_data = 'From:%s\nTo:%s\nSubject:%s\n\n%s' % (mail_from, mail_to, mail_subject, mail_text)
    mail_server = smtplib.SMTP('smtp.web.de', 587)
    mail_server.starttls()
    mail_server.login(mail_user, mail_key)
    mail_server.sendmail(mail_from, mail_to, mail_data)
    mail_server.quit()

# Binance Data
def get_daily_data(client, symbol, interval = '1d', lookback = '90'):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'day ago UTC'))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def try_import_daily_data(client, asset):
    try:
        df = get_daily_data(client, asset, '1d', '90')  # Import Data
    except:
        print('Something went wrong. Script continues in 1 min')
        time.sleep(61)
        df = get_daily_data(client, asset, '1d', '90')  # Import Data
    return df

# Repetitive Functions
def timestamp():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return st


def sleep_until_tomorrow(target_time):   # Target time: 12:00:00 AM -> target_time = datetime.time(12, 0, 0)
    # Get the current time
    now = datetime.datetime.now()

    # Calculate the time difference between now and the target time tomorrow
    tomorrow = now + datetime.timedelta(days=1)
    target_time = datetime.datetime.combine(tomorrow, target_time)
    time_diff = target_time - now
    seconds_diff = time_diff.total_seconds()

    # Sleep for the calculated time difference
    print("sleep...")
    time.sleep(seconds_diff)

# Technical Analysis
def AMA_chart(df, AMA_n_1, AMA_fast_1, AMA_slow_1, AMA_n_2, AMA_fast_2, AMA_slow_2, DC_open_period, DC_close_period, ATR_period):
    # Simple Moving Average Settings
    sma_interval = 30

    # Simple Moving Average
    df['SMA'] = df.Close.rolling(window=sma_interval).mean()

    # Adaptive Moving Average Setting
    n_1 = AMA_n_1
    fast_1 = AMA_fast_1
    slow_1 = AMA_slow_1

    n_2 = AMA_n_2
    fast_2 = AMA_fast_2
    slow_2 = AMA_slow_2

    # Adaptive Moving Average
    df['direction_1'] = abs(df.Close.diff(periods=n_1))
    df['abs_diff_1'] = abs(df.Close.diff(periods=1))
    df['volatility_1'] = df.abs_diff_1.rolling(window=n_1).sum()
    df['efficiency_ratio_1'] = df.direction_1 / df.volatility_1

    df['fastest_1'] = 2 / (fast_1 + 1)
    df['slowest_1'] = 2 / (slow_1 + 1)
    df['smooth_1'] = df.efficiency_ratio_1 * (df.fastest_1 - df.slowest_1) + df.slowest_1
    df['c_1'] = df.smooth_1 ** 2

    df['AMA_1'] = df.Close.rolling(window=n_1 - 1).mean()
    df['AMA_1'] = np.where(df.c_1 != np.nan, df.AMA_1.shift(1) + df.c_1 * (df.Close - df.AMA_1.shift(1)), df.AMA_1)

    df['direction_2'] = abs(df.Close.diff(periods=n_2))
    df['abs_diff_2'] = abs(df.Close.diff(periods=1))
    df['volatility_2'] = df.abs_diff_2.rolling(window=n_2).sum()
    df['efficiency_ratio_2'] = df.direction_2 / df.volatility_2

    df['fastest_2'] = 2 / (fast_2 + 1)
    df['slowest_2'] = 2 / (slow_2 + 1)
    df['smooth_2'] = df.efficiency_ratio_2 * (df.fastest_2 - df.slowest_2) + df.slowest_2
    df['c_2'] = df.smooth_2 ** 2

    df['AMA_2'] = df.Close.rolling(window=n_2 - 1).mean()
    df['AMA_2'] = np.where(df.c_2 != np.nan, df.AMA_2.shift(1) + df.c_2 * (df.Close - df.AMA_2.shift(1)), df.AMA_2)

    # Donchian Channel Setting
    open_period = DC_open_period
    close_period = DC_close_period

    # Donchian Channel (open & close)
    df['open_max'] = df.High.rolling(window=open_period).max()
    df['open_min'] = df.Low.rolling(window=open_period).min()
    df['open_mean'] = (df.open_max + df.open_min) / 2

    df['close_max'] = df.High.rolling(window=close_period).max()
    df['close_min'] = df.Low.rolling(window=close_period).min()
    df['close_mean'] = (df.close_max + df.close_min) / 2

    # MACD
    df['macd'] = df.close_mean - df.open_mean
    df['macd_signal'] = df.macd.rolling(window=close_period // 2).mean()

    # ATR Setting
    atr_period = ATR_period

    # Average True Range
    df['true_range'] = np.max(
        [abs(df.High - df.Low), abs(df.High - df.Close.shift(1)), abs(df.Low - df.Close.shift(1))], axis=0)
    df['atr'] = round(df.true_range.rolling(window=atr_period).mean(), 10)

    # Trades
    df['BUY'] = np.where((df.SMA < df.AMA_1) & (df.Close > df.AMA_1), True, False)
    df['SELL'] = np.where((df.SMA > df.AMA_1), True, False)

    return df

# Close and open a positon
def try_open_position(client, asset_dict, asset, df, test_order):
    wallet_amount = asset_dict[asset][1]
    bet_size = asset_dict[asset][2]
    lot_size = asset_dict[asset][3]

    buy_qty = ((wallet_amount * bet_size / df.atr[-1]) // lot_size) * lot_size

    if test_order == True:
        buy_order = client.create_test_order(symbol='BNBBTC', side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET,
                                             quantity=100)
        buyprice = df.iloc[-1].Close
    else:
        buy_order = client.create_order(symbol=asset, side='BUY', type='MARKET', quantity=buy_qty)
        buyprice = float(buy_order['fills'][0]['price'])

    return buy_order, buyprice

def try_close_position(client, asset_dict, asset, df, test_order):
    lot_size = asset_dict[asset][3]
    client_balances_df = pd.DataFrame(client.get_account()['balances'])
    sell_qty = float(client_balances_df[client_balances_df.asset == asset_dict[asset][0]].free)

    sell_qty = (sell_qty // lot_size) * lot_size

    if test_order == True:
        sell_order = client.create_test_order(symbol='BNBBTC', side=Client.SIDE_SELL, type=Client.ORDER_TYPE_MARKET,
                                              quantity=100)
        sellprice = df.iloc[-1].Close
    else:
        sell_order = client.create_order(symbol=asset, side='SELL', type='MARKET', quantity=sell_qty)
        sellprice = float(sell_order['fills'][0]['price'])

    return sell_order, sellprice
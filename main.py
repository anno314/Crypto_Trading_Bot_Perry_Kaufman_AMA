# Libraries
import helpfunctions
from binance.client import Client
import pandas as pd
import numpy as np
import time
import datetime
import csv
import schedule
import smtplib

# API and Account Setup
client = helpfunctions.connect_to_binance_client()

# Check Conection and Account
account_df = client.get_account()
assets_len = len(account_df['balances'])

for i in range(assets_len):
    asset_name = account_df['balances'][i]['asset']
    asset_free = float(account_df['balances'][i]['free'])

    if asset_free != 0:
        print(f'asset: {asset_name}; free: {asset_free}')

# Strategie Part

## Strategy Functions

def mail_info(text):
    mail_text = text
    mail_subject = 'Crypto Trading Bot'
    mail_from = mail_user
    mail_to = mail_user

    mail_data = 'From:%s\nTo:%s\nSubject:%s\n\n%s' % (mail_from, mail_to, mail_subject, mail_text)
    mail_server = smtplib.SMTP('smtp.web.de', 587)
    mail_server.starttls()
    mail_server.login(mail_user, mail_key)
    mail_server.sendmail(mail_from, mail_to, mail_data)
    mail_server.quit()


def get_minute_data(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'min ago UTC'))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def get_second_data(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'sec ago UTC'))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame


def get_daily_data(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'day ago UTC'))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def AMA_chart(df):
    # Simple Moving Average Settings
    sma_interval = 30

    # Simple Moving Average
    df['SMA'] = df.Close.rolling(window=sma_interval).mean()

    # Adaptive Moving Average Setting
    n_1 = 10
    fast_1 = 2
    slow_1 = 30

    n_2 = 10
    fast_2 = 10
    slow_2 = 30

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
    open_period = 23
    close_period = 11

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
    atr_period = 11

    # Average True Range
    df['true_range'] = np.max(
        [abs(df.High - df.Low), abs(df.High - df.Close.shift(1)), abs(df.Low - df.Close.shift(1))], axis=0)
    df['atr'] = round(df.true_range.rolling(window=atr_period).mean(), 10)

    # Trades
    df['BUY'] = np.where((df.SMA < df.AMA_1) & (df.Close > df.AMA_1), True, False)
    df['SELL'] = np.where((df.SMA > df.AMA_1), True, False)

    return df

def strategy_AMA(asset_dict, test_order, open_position):
    mail_info('### Trading Bot is active ###')
    for asset in list(asset_dict):
        if open_position == False:
            try:
                df = get_daily_data(asset, '1d', '90')  # Import Data
            except:
                print('Something went wrong. Script continues in 1 min')
                time.sleep(61)
                df = get_daily_data(asset, '1d', '90')  # Import Data

            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

            df = AMA_chart(df)  # Technical analysis

            print('### SCREEN MARKET ###')
            print(f'Time Stamp: ' + str(st))
            print(f'Coin Name: ' + str(asset))
            print(f'Buy Signal: ' + str(df.iloc[-1].BUY))

            if df.iloc[-1].BUY == True:

                wallet_amount = asset_dict[asset][1]
                bet_size = asset_dict[asset][2]
                lot_size = asset_dict[asset][3]

                buy_qty = ((wallet_amount * bet_size / df.atr[-1]) // lot_size) * lot_size

                ### real order vs. test order ###
                if test_order == True:
                    buy_order = client.create_test_order(symbol='BNBBTC',side=Client.SIDE_BUY,type=Client.ORDER_TYPE_MARKET,quantity=100)
                    buyprice = df.iloc[-1].Close
                else:
                    buy_order = client.create_order(symbol=asset, side='BUY', type='MARKET', quantity=buy_qty)
                    buyprice = float(buy_order['fills'][0]['price'])
                ### real order vs. test order ###

                ts = time.time()
                st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                print('### BEGIN TRADE ###')
                print(f'Time Stamp: ' + str(st))
                print(f'Coin Name: ' + str(asset))
                print(f'Trade: ' + str(asset))
                print(f'Buy Price: ' + str(buyprice))
                print('Ticket:')
                print(buy_order)

                # mail update
                mail_info(str(buy_order))

                open_position = True

                while open_position:
                    try:
                        df = get_daily_data(asset, '1d', '90')  # Import Data
                    except:
                        print('Something went wrong. Script continues in 1 min')
                        time.sleep(61)
                        df = get_daily_data(asset, '1d', '90')  # Import Data

                    df = AMA_chart(df)  # Technical analysis
                    current_close = df.iloc[-1].Close

                    if df.iloc[-1].SELL == True:
                        client_balances_df = pd.DataFrame(client.get_account()['balances'])
                        sell_qty = float(client_balances_df[client_balances_df.asset == asset_dict[asset][0]].free)

                        precision = -np.log(lot_size) / np.log(10)  # 10^(-x) = lot size
                        sell_qty = (sell_qty // lot_size) * lot_size

                        ### real order vs. test order ###
                        if test_order == True:
                            sell_order = client.create_test_order(symbol='BNBBTC',side=Client.SIDE_SELL,type=Client.ORDER_TYPE_MARKET,quantity=100)
                            sellprice = df.iloc[-1].Close
                        else:
                            sell_order = client.create_order(symbol=asset, side='SELL', type='MARKET', quantity=sell_qty)
                            sellprice = float(sell_order['fills'][0]['price'])
                        ### real order vs. test order ###

                        profit = sellprice - buyprice
                        profit_absolut = profit * sell_qty
                        profit_percent = (profit * 100) / (buyprice)
                        ts = time.time()
                        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                        print(f'Time Stamp: ' + str(st))
                        print(f'Coin Name: ' + str(asset))
                        print(f'Trade: ' + str(asset))
                        print(f'Sell Price: ' + str(sellprice))
                        print(f'Profit Amount: ' + str(profit_absolut))
                        print(f'Profit %: ' + str(profit_percent))
                        print('Ticket:')
                        print(sell_order)
                        print('### END TRADE ###')

                        res = [asset, buyprice, sell_qty, sellprice, profit_absolut, profit_percent]

                        # mail update
                        mail_info(str(sell_order))

                        # excel data
                        with open(doc_name, 'a') as f:
                            writer = csv.writer(f)
                            writer.writerow(res)

                        open_position = False
                        break
                    time.sleep(60 * 60 * 10)

        if open_position == True:
            while open_position:
                try:
                    df = get_daily_data(asset, '1d', '90')  # Import Data
                except:
                    print('Something went wrong. Script continues in 1 min')
                    time.sleep(61)
                    df = get_daily_data(asset, '1d', '90')  # Import Data

                df = AMA_chart(df)  # Technical analysis
                current_close = df.iloc[-1].Close

                if df.iloc[-1].SELL == True:
                    client_balances_df = pd.DataFrame(client.get_account()['balances'])
                    sell_qty = float(client_balances_df[client_balances_df.asset == asset_dict[asset][0]].free)

                    precision = -np.log(lot_size) / np.log(10)  # 10^(-x) = lot size
                    sell_qty = (sell_qty // lot_size) * lot_size

                    ### real order vs. test order ###
                    if test_order == True:
                        sell_order = client.create_test_order(symbol='BNBBTC', side=Client.SIDE_SELL,
                                                              type=Client.ORDER_TYPE_MARKET, quantity=100)
                        sellprice = df.iloc[-1].Close
                    else:
                        sell_order = client.create_order(symbol=asset, side='SELL', type='MARKET', quantity=sell_qty)
                        sellprice = float(sell_order['fills'][0]['price'])
                    ### real order vs. test order ###

                    profit = sellprice - buyprice
                    profit_absolut = profit * sell_qty
                    profit_percent = (profit * 100) / (buyprice)
                    ts = time.time()
                    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                    print(f'Time Stamp: ' + str(st))
                    print(f'Coin Name: ' + str(asset))
                    print(f'Trade: ' + str(asset))
                    print(f'Sell Price: ' + str(sellprice))
                    print(f'Profit Amount: ' + str(profit_absolut))
                    print(f'Profit %: ' + str(profit_percent))
                    print('Ticket:')
                    print(sell_order)
                    print('### END TRADE ###')

                    res = [asset, buyprice, sell_qty, sellprice, profit_absolut, profit_percent]

                    # mail update
                    mail_info(str(sell_order))

                    # excel data
                    with open(doc_name, 'a') as f:
                        writer = csv.writer(f)
                        writer.writerow(res)

                    open_position = False
                    break
                time.sleep(60 * 60 * 10)

    time.sleep(60 * 60 * 10)

# Run Bot
print('### Starting Trading Bot ###')

## Input for set up
test_order_input = input('Use Test Orders? (y/n): ')
open_position_input = input('Is there already an open position? (y/n): ')

def input_to_bool(input):
    if input == 'y':
        return True
    if input == 'n':
        return False

test_order_input = input_to_bool(test_order_input)
open_position_input = input_to_bool(open_position_input)

## excel setup
start_time = time.strftime("%d.%m.%Y %H:%M:%S")
doc_name = f"crypto trading adjusted moving average {start_time}".replace(" ", "_").replace(".", "").replace(":", "") + ".csv"
header = ['name', 'price(buy)', 'pieces', 'price(sell)', 'gain/loss', 'gain/loss(%)']

with open(doc_name, 'w', encoding='UTF8') as f:
    writer = csv.writer(f)
    writer.writerow(header)

## Bot
while True:
    strategy_AMA(asset_dict={'BTCUSDT': ('BTC', 100, 0.05, 0.00001)}, test_order=test_order_input, open_position=open_position_input)  # wallet amount, bet size, lot size,

# Libraries
import helpfunctions
from binance.client import Client
import pandas as pd
import numpy as np
import time
import datetime


# API and Account Setup
client = helpfunctions.connect_to_binance_client()
helpfunctions.print_account_balance(client)

# RUN BOT
def strategy_AMA(asset_dict, test_order, open_position):
    for asset in list(asset_dict):
        if open_position == False: # Check if already invested
            # Not invested yet
            df = helpfunctions.try_import_daily_data(client, asset) # Try to download latest daily price data from binance
            df = helpfunctions.AMA_chart(df, 10, 2, 30, 10, 10, 30, 23, 11, 11)  # Technical analysis

            # Info
            print('### SCREEN MARKET ###')
            print(f'Time Stamp: ' + str(helpfunctions.timestamp()))
            print(f'Coin Name: ' + str(asset))
            print(f'Buy Signal: ' + str(df.iloc[-1].BUY))

            if df.iloc[-1].BUY == True: # Check if position has to be opened
                # Open a position
                buy_order, buyprice = helpfunctions.try_open_position(client, asset_dict, asset, df, test_order)

                # Info
                print('### BEGIN TRADE ###')
                print(f'Time Stamp: ' + str(helpfunctions.timestamp()))
                print(f'Coin Name: ' + str(asset))
                print(f'Buy Price: ' + str(buyprice))
                print('Ticket:')
                print(buy_order)

                # Mail update
                helpfunctions.send_mail(str(buy_order))

                # Invested yet
                open_position = True

                while open_position:
                    df = helpfunctions.try_import_daily_data(client, asset)  # Try to download latest daily price data from binance
                    df = helpfunctions.AMA_chart(df, 10, 2, 30, 10, 10, 30, 23, 11, 11)  # Technical analysis

                    if df.iloc[-1].SELL == True: # Check if position has to be closed
                        # Close a position
                        sell_order, sellprice = helpfunctions.try_close_position(client, asset_dict, asset, df, test_order)

                        # Info
                        print(f'Time Stamp: ' + str(helpfunctions.timestamp()))
                        print(f'Coin Name: ' + str(asset))
                        print(f'Sell Price: ' + str(sellprice))
                        print(f'Profit Amount: ' + str((sellprice - buyprice) * sell_qty))
                        print(f'Profit %: ' + str(((sellprice - buyprice) * 100) / (buyprice)))
                        print('Ticket:')
                        print(sell_order)
                        print('### END TRADE ###')

                        # Mail update
                        helpfunctions.send_mail(str(sell_order))

                        # Not invested yet
                        open_position = False
                        break

                    # Sleep
                    target_time = datetime.time(8, 0, 0)
                    helpfunctions.sleep_until_tomorrow(target_time)
                    print(f'Time Stamp: ' + str(helpfunctions.timestamp()))
                    # Mail update
                    helpfunctions.send_mail('Trading Bot is active')
                    # Account update
                    helpfunctions.print_account_balance(client)
        else:
            while open_position:
                df = helpfunctions.try_import_daily_data(client, asset)  # Try to download latest daily price data from binance
                df = helpfunctions.AMA_chart(df, 10, 2, 30, 10, 10, 30, 23, 11, 11)  # Technical analysis

                if df.iloc[-1].SELL == True:  # Check if position has to be closed
                    # Close a position
                    sell_order, sellprice = helpfunctions.try_close_position(client, asset_dict, asset, df, test_order)

                    # Info
                    print(f'Time Stamp: ' + str(helpfunctions.timestamp()))
                    print(f'Coin Name: ' + str(asset))
                    print(f'Sell Price: ' + str(sellprice))
                    print(f'Profit Amount: ' + str((sellprice - buyprice) * sell_qty))
                    print(f'Profit %: ' + str(((sellprice - buyprice) * 100) / (buyprice)))
                    print('Ticket:')
                    print(sell_order)
                    print('### END TRADE ###')

                    # Mail update
                    helpfunctions.send_mail(str(sell_order))

                    # Not invested yet
                    open_position = False
                    break

                # Get the current time
                now = datetime.datetime.now()

                # Calculate the time until 8am tomorrow
                tomorrow = now + datetime.timedelta(days=1)
                target_time = datetime.datetime.combine(tomorrow, datetime.time(hour=8))

                # Sleep
                target_time = datetime.time(8, 0, 0)
                helpfunctions.sleep_until_tomorrow(target_time)
                print(f'Time Stamp: ' + str(helpfunctions.timestamp()))
                # Mail update
                helpfunctions.send_mail('Trading Bot is active')
                # Account update
                helpfunctions.print_account_balance(client)

    # Get the current time
    now = datetime.datetime.now()

    # Calculate the time until 8am tomorrow
    tomorrow = now + datetime.timedelta(days=1)
    target_time = datetime.datetime.combine(tomorrow, datetime.time(hour=8))

    # Sleep
    target_time = datetime.time(8, 0, 0)
    helpfunctions.sleep_until_tomorrow(target_time)
    print(f'Time Stamp: ' + str(helpfunctions.timestamp()))
    # Mail update
    helpfunctions.send_mail('Trading Bot is active')
    # Account update
    helpfunctions.print_account_balance(client)

# RUN BOT
while True:
    strategy_AMA({'BTCUSDT': ('BTC', 0.001)}, False, False)
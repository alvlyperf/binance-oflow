import pandas as pd
import binance
from binance.client import Client
from market_profile import MarketProfile
from binance_f import RequestClient
from binance_f.model import CandlestickInterval
from datetime import datetime
import pytz
import math
import sys

pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

'''klines('BTCUSDT','2021-01-01','2021-01-05','5m')'''


def klines(symbol, start, end, interval):
    akey = None
    pkey = None

    if interval == '1m':
        interval = Client.KLINE_INTERVAL_1MINUTE
    elif interval == '3m':
        interval = Client.KLINE_INTERVAL_3MINUTE
    elif interval == '5m':
        interval = Client.KLINE_INTERVAL_5MINUTE
    elif interval == '15m':
        interval = Client.KLINE_INTERVAL_15MINUTE
    elif interval == '30m':
        interval = Client.KLINE_INTERVAL_30MINUTE
    elif interval == '1h':
        interval = Client.KLINE_INTERVAL_1HOUR
    elif interval == '4h':
        interval = Client.KLINE_INTERVAL_4HOUR
    elif interval == '1d':
        interval = Client.KLINE_INTERVAL_1DAY

    '''local_time = pytz.timezone("Europe/Madrid")

    local_start = local_time.localize(datetime.strptime(start, "%Y-%m-%d %H:%M"), is_dst=None)
    local_end = local_time.localize(datetime.strptime(end, "%Y-%m-%d %H:%M"), is_dst=None)

    utc_start = local_start.astimezone(pytz.utc).strftime( "%Y-%m-%d %H:%M")
    utc_end = local_end.astimezone(pytz.utc).strftime( "%Y-%m-%d %H:%M")
    print(utc_start)
    print(utc_end)'''
    # sys.exit()

    client = Client(akey, pkey)
    klines = client.get_historical_klines(symbol, interval, start, end)
    df = pd.DataFrame(klines, columns=['Date',
                                       'Open',
                                       'High',
                                       'Low',
                                       'Close',
                                       'Volume',
                                       'Close time',
                                       'quote asset Volume',
                                       'number of trades',
                                       'taker buy base asset Volume',
                                       'taker buy quote asset Volume',
                                       'ignore'])

    df['Date'] = pd.to_datetime(df['Date'], unit='ms').dt.tz_localize(pytz.utc).dt.tz_convert('Europe/Madrid')
    df['Date'] = pd.to_datetime(df["Date"].dt.strftime("%Y-%m-%d %H:%M"))
    df['Open'] = df['Open'].astype(float)
    df['High'] = df['High'].astype(float)
    df['Low'] = df['Low'].astype(float)
    df['Close'] = df['Close'].astype(float)
    df['Volume'] = df['Volume'].astype(float)
    df['quote asset Volume'] = df['quote asset Volume'].astype(float)
    df['taker buy base asset Volume'] = df['taker buy base asset Volume'].astype(float)
    df['taker buy quote asset Volume'] = df['taker buy quote asset Volume'].astype(float)

    return df


def klines_futures(symbol, interval=None, limit=None, start=None, end=None):
    akey = None
    pkey = None

    if interval == '1m':
        interval = CandlestickInterval.MIN1
    elif interval == '3m':
        interval = CandlestickInterval.MIN3
    elif interval == '5m':
        interval = CandlestickInterval.MIN5
    elif interval == '15m':
        interval = CandlestickInterval.MIN15
    elif interval == '30m':
        interval = CandlestickInterval.MIN30
    elif interval == '1h':
        interval = CandlestickInterval.HOUR1
    elif interval == '4h':
        interval = CandlestickInterval.HOUR4
    elif interval == '1d':
        interval = CandlestickInterval.DAY1

    if end == 'now':
        end = datetime.now().strftime('%Y-%m-%d %H:%M')
    if start and end:
        local_time = pytz.timezone("Europe/Madrid")

        local_start = local_time.localize(datetime.strptime(start, "%Y-%m-%d %H:%M"), is_dst=None)
        local_end = local_time.localize(datetime.strptime(end, "%Y-%m-%d %H:%M"), is_dst=None)

        utc_start = local_start.astimezone(pytz.utc)
        utc_end = local_end.astimezone(pytz.utc)

        start = utc_start.timestamp() * 1000
        end = utc_end.timestamp() * 1000

    request_client = RequestClient(api_key=akey, secret_key=pkey)
    klines_futures = request_client.get_candlestick_data(symbol=symbol, interval=interval,
                                                         limit=limit, startTime=start, endTime=end)
    klines_futures = [item.__dict__ for item in klines_futures]

    df = pd.DataFrame(klines_futures)

    df = df.rename(columns={'openTime': 'Date',
                            'open': 'Open',
                            'high': 'High',
                            'low': 'Low',
                            'close': 'Close',
                            'volume': 'Volume',
                            'closeTime': 'Close time',
                            'quoteAssetVolume': 'quote asset Volume',
                            'numTrades': 'number of trades',
                            'takerBuyBaseAssetVolume': 'taker buy base asset Volume',
                            'takerBuyQuoteAssetVolume': 'taker buy quote asset Volume',
                            'ignore': 'ignore',
                            })

    df['Date'] = pd.to_datetime(df['Date'], unit='ms').dt.tz_localize(pytz.utc).dt.tz_convert('Europe/Madrid')
    df['Date'] = pd.to_datetime(df["Date"].dt.strftime("%Y-%m-%d %H:%M"))
    df['Open'] = df['Open'].astype(float)
    df['High'] = df['High'].astype(float)
    df['Low'] = df['Low'].astype(float)
    df['Close'] = df['Close'].astype(float)
    df['Volume'] = df['Volume'].astype(float)
    df['quote asset Volume'] = df['quote asset Volume'].astype(float)
    df['taker buy base asset Volume'] = df['taker buy base asset Volume'].astype(float)
    df['taker buy quote asset Volume'] = df['taker buy quote asset Volume'].astype(float)

    return df


def group_candles(df, period=5, price_interval=50, delta=False):
    imbalance = 3

    df = df
    df2 = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'taker buy base asset Volume']]
    df2 = df2.rename(columns={'taker buy base asset Volume': 'buy'})
    df2['sell'] = df2['Volume'] - df2['buy']

    candles = []
    dff_violin = []
    for i in range(0, len(df2), period):

        slice = df2[i:i + period]
        df_slice = pd.DataFrame()
        for index, row in slice.iterrows():
            auxl = math.ceil(row['Low'] / price_interval) * price_interval - (price_interval // 2)
            auxh = math.ceil(row['High'] / price_interval) * price_interval + (price_interval // 2)

            steps = range((auxl), (auxh), price_interval)
            buy_avg = row['buy'] / len(steps)
            sell_avg = row['sell'] / len(steps)
            df_aux = pd.DataFrame()

            df_aux['steps'] = steps
            df_aux['buy'] = [buy_avg] * len(steps)
            df_aux['sell'] = [sell_avg] * len(steps)
            df_slice = pd.concat([df_slice, df_aux], ignore_index=True)
        dff = df_slice.groupby(['steps'], as_index=False).sum()
        dff['datetime'] = [slice.iloc[0]['Date']] * len(dff)
        # Imbalance using diagonal price levels
        txt = []

        if delta:

            dff['text'] = [
                str(int(round(buy - sell, 0)))
                for buy, sell in zip(dff['buy'], dff['sell'])
            ]


        else:
            for i in range(len(dff[['buy']])):
                if i == 0 or i == len(dff['buy']) - 1:
                    txt.append(str(int(round(dff['sell'][i], 0))) + ' ' + str(int(round(dff['buy'][i], 0))))

                elif dff['buy'][i] > imbalance * dff['sell'][i - 1]:
                    txt.append(str(int(round(dff['sell'][i], 0))) + ' ' + '[' + str(int(round(dff['buy'][i], 0))) + ']')

                elif dff['sell'][i] > dff['buy'][i + 1] * imbalance:
                    txt.append('[' + str(int(round(dff['sell'][i], 0))) + ']' + ' ' + str(int(round(dff['buy'][i], 0))))

                else:
                    txt.append(str(int(round(dff['sell'][i], 0))) + ' ' + str(int(round(dff['buy'][i], 0))))

            dff['text'] = txt
        dff_violin.append(dff)
        candles.append(dff)

    steps = []
    datetime = []
    volumes = []
    for item in candles:
        steps += item['steps'].tolist()
        datetime += item['datetime'].tolist()
        volumes += item['text'].tolist()
    return steps, datetime, volumes, dff_violin

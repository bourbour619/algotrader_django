from numpy.lib.function_base import select
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from django.conf import settings
from datetime import datetime
import json
import re
from persiantools.jdatetime import JalaliDateTime

plt.style.use('fivethirtyeight')



def df_to_dict(df,group):
    try:
        nd = {
            'Date': [],
            'Open': [],
            'Close': [],
            'High': [],
            'Low': [],
        }
        if group == 'bourse':
            for i in range(len(df)):
                t = str(df['<DTYYYYMMDD>'].iloc[i])
                t = f'{t[:4]}/{t[4:6]}/{t[6:8]}'
                nd['Date'].append(t)
                nd['Open'].append(df['<OPEN>'].iloc[i])
                nd['Close'].append(df['<CLOSE>'].iloc[i])
                nd['High'].append(df['<HIGH>'].iloc[i])
                nd['Low'].append(df['<LOW>'].iloc[i])
        if group == 'crypto':
            for d in df:
                t = datetime.utcfromtimestamp(d[0])
                nd['Date'].append(t)
                nd['Open'].append(d[1])
                nd['Close'].append(d[2])
                nd['High'].append(d[3])
                nd['Low'].append(d[4])
        return nd
    except:
        return {}


def csv_df_validator(csv):
    name, path = csv['name'], csv['path']
    errors = {}
    if name.split('.')[-1] != 'csv' :
        errors['invalid_extension'] = True
    df = pd.read_csv(path)
    if len(df) < 100 :
        errors['row_length'] = True
    valids = ['Date', 'Close', 'Open', 'High', 'Low']
    if all(v not in df.columns for v in valids):
        errors['invalid_columns'] = True
    return errors

def to_jalali(date,point):
    if point == 'before':
        date = ''.join(date.split('/'))
        return JalaliDateTime.to_jalali(datetime(year=int(date[:4]),
                                                month=int(date[4:6]),
                                                day=int(date[6:8]))).strftime("%Y/%m/%d")
    elif point == 'after':
        if date.hour or date.minute or date.second:
            return JalaliDateTime.to_jalali(datetime(year=date.year,
                                                    month=date.month,
                                                    day=date.day,
                                                    hour=date.hour,
                                                    minute=date.minute,
                                                    second=date.second)).strftime("%Y/%m/%d - %H:%M:%S")
        else:
            return JalaliDateTime.to_jalali(datetime(year=date.year,
                                                    month=date.month,
                                                    day=date.day)).strftime("%Y/%m/%d")

def df_get_info(group, **kwargs):
    df = kwargs.get('df')
    path = kwargs.get('path')
    if path:
        df = pd.read_csv(path)
    info = {}
    if group == 'bourse':
        df = df[::-1].reset_index(drop=True)
        info = {
            'date': {
                'start': to_jalali(df['Date'].iloc[0],point='before'),
                'end': to_jalali(df['Date'].iloc[-1],point='before')
            },
            'rows': len(df)
         }
    if group == 'crypto':
        info = {
            'date': {
                'start': df['Date'].iloc[0],
                'end': df['Date'].iloc[-1]
            },
            'rows': len(df)
         }
    return info 

def check_jalali_range(**kwargs):
    start = kwargs.get('start').split('/')
    end = kwargs.get('end').split('/')
    ggStart = JalaliDateTime(year=int(start[0]), month=int(start[1]), day=int(start[2])).to_gregorian()
    ggEnd =  JalaliDateTime(year=int(end[0]), month=int(end[1]), day=int(end[2])).to_gregorian()
    if ggStart >= ggEnd:
        return False
    return True


def df_by_date(df, **kwargs):
    start = kwargs.get('start').split('/')
    end = kwargs.get('end').split('/')
    ggStart = JalaliDateTime(year=int(start[0]), month=int(start[1]), day=int(start[2])).to_gregorian()
    ggEnd =  JalaliDateTime(year=int(end[0]), month=int(end[1]), day=int(end[2])).to_gregorian()
    df['Date'] = pd.DatetimeIndex(df['Date'])
    df = df[(df['Date'] >= ggStart) & (df['Date'] <= ggEnd)]
    df['Date'] = [d.strftime("%Y/%m/%d") for d in df['Date']]
    return df


from abc import ABC, abstractmethod

class Strategy(ABC):

    @abstractmethod
    def run(self) -> dict: 
        pass

    def format(self) -> None:
        pass


class MACDCrossover(Strategy):
    table = []

    def __init__(self) -> None:
        pass

    def run(self, file) -> dict:
        try:
            self.file = file
            ticker = self.file['name']
            df = pd.read_csv(self.file['path'])
            df = df.set_index(pd.DatetimeIndex(df['Date']))
            fdf = pd.DataFrame()
            fdf['Close'] = df['Close']
            fdf['SMA30'] = fdf['Close'].rolling(window=30).mean()
            fdf['SMA100'] = fdf['Close'].rolling(window=100).mean()
            sigBuy, sigSell = [], []
            flag = -1
            for i in range(len(fdf)):
                if fdf['SMA30'][i] > fdf['SMA100'][i]:
                    if flag != -1:
                        sigBuy.append(fdf['Close'][i])
                        sigSell.append(np.nan)
                        flag = 1
                    else:
                        sigBuy.append(np.nan)
                elif fdf['SMA30'][i] < fdf['SMA100'][i]:
                    if flag != 0:
                        sigBuy.append(np.nan)
                        sigSell.append(fdf['Close'][i])
                        flag = 0
                    else:
                        sigSell.append(np.nan)
                        sigBuy.append(np.nan)
                else:
                    sigBuy.append(np.nan)
                    sigSell.append(np.nan)
            if not sigBuy and not sigSell:
                return {
                    'success': False
                }
            fdf['Buy'] = sigBuy
            fdf['Sell'] = sigSell
            fdf.to_csv(f"{settings.MEDIA_ROOT}/{ticker}_Signal.csv")
            self.format(df=fdf)
            plt.figure(figsize=(12.2, 6.1),dpi=80)
            plt.plot(fdf['Close'], label= ticker, alpha=0.5)
            plt.plot(fdf['SMA30'], label='SMA30', alpha=0.5)
            plt.plot(fdf['SMA100'], label='SMA100', alpha=0.5)
            plt.scatter(fdf.index, fdf['Buy'], label='Buy', marker='^', color='green')
            plt.scatter(fdf.index, fdf['Sell'], label='Sell', marker='v', color='red')
            plt.xlabel('Date')
            plt.ylabel('Close Price')
            plt.legend(loc='upper left')
            plt.tight_layout()
            plt.savefig(f"{settings.MEDIA_ROOT}/{ticker}_Signal.png")
            return {
                'success': True,
                'csv': settings.MEDIA_URL + f"{ticker}_Signal.csv",
                'img': settings.MEDIA_URL + f"{ticker}_Signal.png",
                'table': self.table
            }
        except:
            return {
                'success': False
            }

    def format(self,df) -> None:
        for i in range(len(df)):
            if pd.notna(df['Buy'].iloc[i]):
                self.table.append({
                    'type': 'خرید',
                    'date': to_jalali(df.index[i],point='after'),
                    'price': df['Buy'].iloc[i]
                })
            elif pd.notna(df['Sell'].iloc[i]):
                self.table.append({
                    'type': 'فروش',
                    'date': to_jalali(df.index[i],point='after'),
                    'price': df['Sell'].iloc[i]
                })

class RSI14(Strategy):
    table = []
    def __init__(self) -> None:
        pass

    def run(self,file) -> dict:
        try:
            self.file = file
            ticker = self.file['name']
            df = pd.read_csv(self.file['path'])
            df = df.set_index(pd.DatetimeIndex(df['Date']))
            fdf = pd.DataFrame()
            fdf['Close'] = df['Close']
            fdf['SMA200'] = fdf['Close'].rolling(window=200).mean()
            fdf['Price Change'] = fdf['Close'].pct_change()
            fdf['Up'] = fdf['Price Change'].apply(lambda x: x if x > 0 else 0)
            fdf['Down'] = fdf['Price Change'].apply(lambda x: abs(x) if x < 0 else 0)
            fdf['AvgUp'] = fdf['Up'].ewm(span=13).mean()
            fdf['AvgDown'] = fdf['Down'].ewm(span=13).mean()
            fdf = fdf.dropna()
            fdf['RS'] = fdf['AvgUp'] / fdf['AvgDown']
            fdf['RSI'] = fdf['RS'].apply(lambda x: 100 - (100/(x+1)))
            fdf.loc[(fdf['Close'] > fdf['SMA200']) & (fdf['RSI'] < 30), 'Buy'] = 'Yes'
            fdf.loc[(fdf['Close'] < fdf['SMA200']) | (fdf['RSI'] > 30), 'Buy'] = 'No'
            # Calc Signal Sell,Buy By RSI14
            sigBuy, sigSell = [], []
            for i in range(len(fdf)):
                if 'Yes' in fdf['Buy'].iloc[i]:
                    sigBuy.append(fdf.iloc[i + 1].name)
                    for j in range(1,11):
                        if fdf['RSI'].iloc[i + j] > 40:
                            sigSell.append(fdf.iloc[i + j + 1].name)
                            break
                        elif j == 10:
                            sigSell.append(fdf.iloc[i + j + 1].name)
            if not sigBuy and not sigSell:
                return {
                    'success': False
                }
            fdf.loc[sigSell, 'Sell'] = 'Yes'
            fdf.loc[set(fdf.index) - set(sigSell), 'Sell'] = 'No'
            fdf.to_csv(f"{settings.MEDIA_ROOT}/{ticker}_Signal.csv")
            self.format(df=fdf)
            plt.figure(figsize=(16.2, 8.1),dpi=80)
            plt.subplot(211)
            plt.plot(fdf['Close'], label= ticker, alpha=0.5)
            plt.plot(fdf['SMA200'], label= 'SMA200', alpha=0.5)
            plt.scatter(fdf.loc[sigBuy].index,fdf.loc[sigBuy]['Close'], marker='^', color='green')
            plt.scatter(fdf.loc[sigSell].index,fdf.loc[sigSell]['Close'], marker='v', color='red')
            plt.tick_params(labelbottom=False)
            plt.ylabel('Close Price')
            plt.legend(loc='upper left')
            plt.subplot(212)
            plt.plot(fdf['RSI'], label='RSI', alpha= 0.5, color='black', linewidth='2')
            plt.plot(fdf.index,np.ones(len(fdf))*30 , linestyle = '--', linewidth='2')
            plt.plot(fdf.index,np.ones(len(fdf))*70 , linestyle = '--', linewidth='2')
            plt.xticks(rotation=45)
            plt.xlabel('Date')
            plt.ylim(0,100)
            plt.legend(loc='upper left')
            plt.tight_layout()
            plt.savefig(f"{settings.MEDIA_ROOT}/{ticker}_Signal.png")
            return {
                'success': True,
                'csv': settings.MEDIA_URL + f"{ticker}_Signal.csv",
                'img': settings.MEDIA_URL + f"{ticker}_Signal.png",
                'table': self.table
            }
        except:
            return {
                'success': False
            }

    def format(self,df) -> None:
        for i in range(len(df)):
            if 'Yes' in df['Buy'].iloc[i]:
                self.table.append({
                    'type': 'خرید',
                    'date': to_jalali(df.index[i],point='after'),
                    'price': df['Close'].iloc[i]
                })
            elif 'Yes' in df['Sell'].iloc[i]:
                self.table.append({
                    'type': 'فروش',
                    'date': to_jalali(df.index[i],point='after'),
                    'price': df['Close'].iloc[i]
                })


class StrategyFactory():
    strategies = {
        'MACD Crossover': MACDCrossover,
        'RSI 14': RSI14
    }
    output = None

    def __init__(self) -> None:
        pass

    def create(self,strategy) -> Strategy:
        if self.strategies.get(strategy):
            self.output = self.strategies[strategy]()
            return self.output

    




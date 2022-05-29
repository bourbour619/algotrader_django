from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from django.core.files.storage import FileSystemStorage
import requests
from df.technical import *
from django.conf import settings
from os import error, path as opath, write
from .func import *

# Create your views here.


def index(request, *args, **kwargs):
    return render(request, 'index.html', {})

csv = {}

def bourse_backtest(request, *args, **kwargs):
    try:
        errors = {}
        if request.method == 'POST':
            fs = FileSystemStorage()
            if request.FILES.get('csv_file'):
                f = request.FILES.get('csv_file')
                global csv
                csv = {
                    'name': f.name, 
                    'path': fs.path(fs.save(f.name, f))
                }
                df = pd.read_csv(csv['path'])
                dict = df_to_dict(df,group='bourse')
                ndf = pd.DataFrame.from_dict(dict)
                ndf.to_csv(csv['path'])
                errors = csv_df_validator(csv)
                if errors:
                    return render(request, 'bourse.html', { 'errors': errors })
                else:
                    csv['error'] = 'No'
                    info = df_get_info(group='bourse',path=csv['path'])
                    csv['info'] = info
                    return render(request, 'bourse.html', { 'csv_error': csv['error'], 'csv_info': info })
            else:
                s = request.POST.get('signal_strategy')
                t = request.POST.get('ticker_input')
                tsd = request.POST.get('ticker_start_date')
                ted = request.POST.get('ticker_end_date')
                
                if s:
                    output = StrategyFactory().create(s)
                    signal = output.run(csv)
                    return render(request, 'bourse.html', {'signal': signal, 'csv_error': csv['error'], 'csv_info': csv['info'] })
                elif t:
                    if (tsd and not ted ) or (not tsd and ted):
                        errors['time_missing'] = True
                        return render(request, 'bourse.html', { 'errors': errors })
                    else:
                        ti = t[:(t.rfind('-'))]
                        tickers = get_bourse_tickers()
                        t = [t for t in tickers if t['short_name'] == ti].pop()
                        i = t['i']
                        i = i[i.rfind('=') + 1 :]
                        csvUrl = f'http://www.tsetmc.com/tsev2/data/Export-txt.aspx?t=i&a=1&b=0&i={i}'
                        l = re.sub('[#$.*?]','', t['latin'])
                        d = requests.get(csvUrl)
                        with open(opath.join(settings.MEDIA_ROOT, f'{l}.csv'), 'wb') as f:
                            f.write(d.content)
                            csv = {
                                'name': f'{l}.csv' ,
                                'path': opath.abspath(f.name)
                            }
                        df = pd.read_csv(csv['path'])
                        dict = df_to_dict(df,group='bourse')
                        ndf = pd.DataFrame.from_dict(dict)
                        if tsd and ted:
                            if not check_jalali_range(start=tsd, end=ted):
                                errors['time_invalid_range'] = True
                                return render(request, 'bourse.html', { 'errors': errors })
                            ndf = df_by_date(ndf, start=tsd, end=ted)
                        ndf.to_csv(csv['path'])
                        csv['error'] = 'No'
                        info = df_get_info(group='bourse',path=csv['path'])
                        csv['info'] = info
                        return render(request, 'bourse.html', { 'csv_error': csv['error'], 'csv_info': csv['info']})
                
                return redirect('bourse_backtest')
        return render(request, 'bourse.html', {})
    except:
        return render(request, 'bourse.html', {'server_error': True})

df = {}

def crypto_backtest(request, *args, **kwargs):
    try:
        pairs = requests.get('https://api.coinex.com/v1/market/list').json()['data']
        timeframes = ['1min','3min','5min','15min','30min','1hour','2hour','4hour','6hour','12hour','1day','3day','1week']
        constant = {
            'pairs': pairs,
            'timeframes': timeframes
        }
        if request.method == 'POST':
            s = request.POST.get('signal_strategy')
            p = request.POST.get('crypto_pair')
            t = request.POST.get('crypto_timeframe')
            if p and t:
                global df
                df = {
                    'pair': p,
                    'timeframe': t
                }
                data = requests.get(f'https://api.coinex.com/v1/market/kline?market={p}&type={t}&limit=1000').json()['data']
                if not data:
                    df['error'] = 'Yes'
                    return render(request, 'crypto.html', { 'constant': constant, 'df_error': 'Yes' })
                df['error'] = 'No'
                dict = df_to_dict(data,group='crypto')
                ddf = pd.DataFrame.from_dict(dict)
                ddf.to_csv(opath.join(settings.MEDIA_ROOT, f'{p}.csv'), index=False)
                info = df_get_info(group='crypto',df=ddf)
                df['info'] = info
                return render(request, 'crypto.html', { 'constant': constant, 'df_error': 'No' , 'df_info': info})
            elif s:
                output = StrategyFactory().create(s)
                signal = output.run({
                    'name': df['pair'],
                    'path': opath.join(settings.MEDIA_ROOT,f"{df['pair']}.csv")
                })
                return render(request, 'crypto.html', {'constant': constant, 'signal': signal, 'df_error': df['error'], 'df_info': df['info']})
            else:
                return redirect('crypto_backtest')
        return render(request, 'crypto.html', {  'constant': constant })
    except:
        return render(request, 'crypto.html', {  'constant': constant, 'server_error': True })


def ajax_bourse_tikcers(request, *args, **kwargs):
    ti = request.POST.get('tickerInput')
    if ti :
       tickers = get_bourse_tickers()
       tickers = [ f"{t['short_name']}-{t['name']}" for t in tickers]
       tickers = [ t for t in tickers if ti in t ]
       return JsonResponse(data=tickers,safe=False)

def get_bourse_tickers():
    # from bs4 import BeautifulSoup
    import requests
    import json
    from persiantools.characters import ar_to_fa

    # url = 'http://www.tsetmc.com/Loader.aspx?ParTree=111C1417'
    # html = requests.get(url).text
    # soup = BeautifulSoup(html, 'html.parser')
    # tickers = []
    # body = soup.find('table')
    # rows = body.find_all('tr')
    
    # for row in rows:
    #     if rows.index(row) != 0:
    #         cols = row.find_all('td')
    #         inscode = cols[6].a['href'].strip()
    #         inscode = inscode[inscode.rfind('=') + 1:]
    #         ticker = {
    #             'inscode': inscode,
    #             'latinTicker': cols[4].text.strip(),
    #             'latinName': cols[5].text.strip(),
    #             'ticker': cols[6].text.strip(),
    #             'name': cols[7].text.strip()
    #         }
    #         tickers.append(ticker)
    url = 'http://157.90.137.17:3000/symbol'
    r = requests.get(url)
    tickers = json.loads(r.text)
    for ticker in tickers:
        temp = {}
        for k,v in ticker.items():
            temp[k] = ar_to_fa(v)
        ticker.update(temp)
    return tickers
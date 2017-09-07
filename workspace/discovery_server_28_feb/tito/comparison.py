# compare two spreadsheets and determine the openings and closures of stores

import pandas as pd

def compare(df_new, df_old, tag):
  openings = []
  closures = []
  for i in df_new[tag].values:
    if not(i in df_old[tag].values):
      openings.append(i)
  for i in df_old[tag].values:
    if not(i in df_new[tag].values):
        closures.append(i)
  return [openings, closures]

keys_open = compare(df1, df2, 'Site Reference')[0]
keys_closed = compare(df1, df2, 'Site Reference')[1]

df_openings = df1[df1['Site Reference'].isin(keys_open)]
df_closures = df2[df2['Site Reference'].isin(keys_closed)]

df_openings.to_csv('openings.csv',sep=',')
df_closures.to_csv('closures.csv',sep=',')

{"Accept": "application/json, text/javascript, */*; q=0.01", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.8", "Connection": "keep-alive", "Content-Length": "98", "Content-Type": "application/json; charset=UTF-8", "Cookie": ".ASPXANONYMOUS=5OSC-5jy0QEkAAAAOTEzNTVmYTItZTk0ZS00NDQ3LWI3NmMtYjFkNTY4OTk1Nzg50; __utmt=1; language=en-US; __utma=97639565.1308107699.1464786718.1464786718.1464786718.1; __utmb=97639565.0.10.1464786718; __utmc=97639565; __utmz=97639565.1464786718.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utma=97639565.1308107699.1464786718.1464786718.1464786718.1; __utmb=97639565.2.10.1464786718; __utmc=97639565; __utmz=97639565.1464786718.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)", "Host": "www.colesexpress.com.au", "Origin": "https://www.colesexpress.com.au", "Referer": "https://www.colesexpress.com.au/store-locator.aspx", "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36", "X-Requested-With": "XMLHttpRequest"}

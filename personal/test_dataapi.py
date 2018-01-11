# encoding: utf-8

from DataApi import DataApi  # 这里假设项目目录名为DataApi, 且存放在工作目录下

# 请在www.quantos.org注册用户
api = DataApi(addr="tcp://data.tushare.org:8910")
# api = DataApi(addr="tcp://45.79.104.166:8910")
df, msg = api.login("13798385767", "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTIwMjA0OTQyMzUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTM3OTgzODU3NjcifQ.xdH5gvprHEsn89tPuy8L5gj7AvhIef7ZjbpDyzc5uJ4")

symbol = '002050.SZ, 000300.SH'
symbol3 = '512610.SH'
fields = 'name,open,high,low,last,volume'
fields3 = 'name'

# 获取实时行情
df1, msg1 = api.quote(symbol=symbol, fields=fields)
df2, msg2 = api.subscribe(symbol=symbol, fields=fields)
df3, msg3 = api.query(view="lb.mfInfo", fields=fields3, filter="symbol=" + symbol3)
# print(df3)
# print(df3.T)
print(df3['name'])
print('---')
print(df3.loc[0]['name'])
# print(df)
# print(msg)

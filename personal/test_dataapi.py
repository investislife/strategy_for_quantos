# encoding: utf-8

from DataApi import DataApi  # 这里假设项目目录名为DataApi, 且存放在工作目录下

# 请在www.quantos.org注册用户
# api = DataApi(addr="tcp://data.tushare.org:8910")
api = DataApi(addr="tcp://45.79.104.166:8910")
df, msg = api.login("13798385767", "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTIwMjA0OTQyMzUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTM3OTgzODU3NjcifQ.xdH5gvprHEsn89tPuy8L5gj7AvhIef7ZjbpDyzc5uJ4")

symbol = '002050.SZ, 000300.SH'
fields = 'open,high,low,last,volume'

# 获取实时行情
df, msg = api.quote(symbol=symbol, fields=fields)
print(df)
print(msg)

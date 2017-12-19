# encoding: utf-8

"""
选股函数：三根阳线

描述一只股票的价格，一般有OHLC(Open, High, Low, Close)这几个基本属性。
阳线的定义表述为两个条件：
    (1) close - open > 0，收盘价大于开盘价
    (2) (close - open) / (high - low) >= 0.7，收盘价与开盘价的差，比最高价与最低价的差，至少超过70%
这里面的0.7其实是一个参数，也可以严格到0.9或者放松到0.4，这一般会改变阳线的形状。

步骤：
    (1) 在DataView中首先取出基本数据open,high,low,close.
    (2) 通过加减和比较操作,计算出阳线.
    (3) 利用Delay函数,计算出连续三根阳线.
    (4) 过滤出符合条件的标的.
"""

from jaqs.data import RemoteDataService, DataView

data_config = {
    "remote.data.address": "tcp://data.tushare.org:8910",
    "remote.data.username": "13798385767",
    "remote.data.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTIwMjA0OTQyMzUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTM3OTgzODU3NjcifQ.xdH5gvprHEsn89tPuy8L5gj7AvhIef7ZjbpDyzc5uJ4"
}
trade_config = {
    "remote.trade.address": "tcp://gw.quantos.org:8901",
    "remote.trade.username": "13798385767",
    "remote.trade.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTIwMjA0OTQyMzUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTM3OTgzODU3NjcifQ.xdH5gvprHEsn89tPuy8L5gj7AvhIef7ZjbpDyzc5uJ4"
}

UNIVERSE = '000300.SH'
start_data = 20171211
cur_data = 20171215

dataview_props = {# Start and end date of back-test
    'start_date': start_data, 'end_date': cur_data,
    # Investment universe and performance benchmark
    'universe': UNIVERSE, 'benchmark': '000300.SH',
    # Data fields that we need
    'fields': 'open,close,high,low',
    # freq = 1 means we use daily data. Please do not change this.
    'freq': 1}

ds = RemoteDataService()
ds.init_from_config(data_config)

dv = DataView()
dv.init_from_config(dataview_props, ds)
dv.prepare_data()

# dv.add_formula('tingpai', 'trade_status != \"停牌\"', is_quarterly=False)
dv.add_formula('is_yang', '(close > open) && ((close - open) / (high -low) >= 0.4)', is_quarterly=False)
dv.add_formula('three_yang', 'is_yang && Delay(is_yang, 1) && Delay(is_yang, 2)', is_quarterly=False)

df = dv.get_snapshot(cur_data)
# df[df['three_yang'] == 1.0]
print(df[df['three_yang'] == 1.0])


from jaqs.data.dataservice import RemoteDataService
from jaqs.data.dataview import DataView
import pandas as pd
import numpy as np

phone = "13798385767"
token = "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTIwMjA0OTQyMzUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTM3OTgzODU3NjcifQ.xdH5gvprHEsn89tPuy8L5gj7AvhIef7ZjbpDyzc5uJ4"

data_config = {
  "timeout": 1800,
  "remote.data.address": "tcp://data.tushare.org:8910",
  "remote.data.username":  phone,
  "remote.data.password":  token}

# 启动DataView，并设置用户名密码
dv = DataView()
ds = RemoteDataService()
ds.init_from_config(data_config)

# -------------------------------------------------------------------------------
# 设置待分析版块及分析起止日期
# -------------------------------------------------------------------------------
# 上证50， 沪深300，中证500，中证全指
# indexList = ['000016.SH', '000300.SH', '000905.SH', '000985.CSI']
indexList = ['000016.SH', '000300.SH', '000905.SH', '000985.CSI']
retCompare = pd.DataFrame()
startdate = 20121231
enddate = 20171130

for index in indexList:
    # 设置DataView
    props = {'start_date': startdate, 'end_date': enddate, 'universe': index,
             'fields': 'close_adj',
             'freq': 1}
    dv.init_from_config(props, data_api=ds)
    dv.prepare_data()

    print(index)

    # 取出板块指数，版块成份股日收盘价及是否为成分股的信息
    closeData = dv.get_ts('close_adj')
    closeData['trade_date'] = closeData.index
    closeData['trade_date'] = closeData['trade_date'].apply(lambda x: str(x))
    closeData['trade_y'] = closeData['trade_date'].apply(lambda x: x[:4])

    benchmarkData = dv.data_benchmark
    benchmarkData['trade_date'] = benchmarkData.index
    benchmarkData['trade_date'] = benchmarkData['trade_date'].apply(lambda x: str(x))
    benchmarkData['trade_y'] = benchmarkData['trade_date'].apply(lambda x: x[:4])

    isIndexMember = dv.get_ts('index_member') == 1
    isIndexMember['trade_date'] = isIndexMember.index
    isIndexMember['trade_date'] = isIndexMember['trade_date'].apply(lambda x: str(x))
    isIndexMember['trade_y'] = isIndexMember['trade_date'].apply(lambda x: x[:4])

    # 筛选出成份股及指数年末收盘价
    closeData_Y = closeData.groupby(['trade_y']).last()
    closeData_Y = closeData_Y.drop('trade_date', 1)
    benchmark_Y = benchmarkData.groupby(['trade_y']).last()
    benchmark_Y = benchmark_Y.drop('trade_date', 1)
    isIndexMember_Y = isIndexMember.groupby(['trade_y']).last()
    isIndexMember_Y = isIndexMember_Y.drop('trade_date', 1)
    isIndexMember_Y = isIndexMember_Y.iloc[:-1, :]

    # 计算成份股及指数年收益率
    ret_Y = closeData_Y.diff() / closeData_Y.shift(1) * 100
    ret_Y_benchmark = benchmark_Y.diff() / benchmark_Y.shift(1) * 100

    ret_Y = ret_Y.iloc[1:, :]
    ret_Y_benchmark = ret_Y_benchmark.iloc[1:, :]

    ret_Y_satisfied = pd.DataFrame(ret_Y.values * isIndexMember_Y.values)

    # 计算成份股年收益率中位数
    ret_Y_satisfied = ret_Y_satisfied.replace(0.0, np.nan)
    ret_Y_satisfied['median_ret'] = ret_Y_satisfied.median(axis=1)

    outputRet = {'index_ret': ret_Y_benchmark['close'].tolist(), 'median_ret': ret_Y_satisfied['median_ret'].tolist()}
    outputRet = pd.DataFrame.from_dict(outputRet)
    outputRet.index = ret_Y_benchmark.index

    retCompare = pd.concat([retCompare, outputRet], axis=1)

retCompare.columns = ['SZ50_index', 'SZ50_median', 'HS300_index', 'HS300_median', 'ZZ500_index', 'ZZ500_median', 'Ashare_index', 'Ashare_median']
print(retCompare.T)

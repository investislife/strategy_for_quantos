# encoding: utf-8

"""
Find the best ETF

ETF: 指数增强型基金并非纯指数基金，是指基金在进行指数化投资的过程中，
为试图获得超越指数的投资回报，在被动跟踪指数的基础上，加入增强型的积极
投资手段，对投资组合进行适当调整，力求在控制风险的同时获取积极的市场收益。
因此，指数增强型基金一般有一个指数作为业绩基准。

筛选条件:
· active return，即相对于指数的主动管理收益
· active volatility，主动收益的波动性
· sharpe ratio，主动管理的夏普率
· beta，即与跟踪指数间的相关性。（越接近1越好）
当然，用户也会关心基金的绝对收益，最大回撤等指标。

"""
from __future__ import print_function, unicode_literals, division, absolute_import

from DataApi import DataApi
import numpy as np
import pandas as pd
import time

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

# Data files are stored in this folder:
dataview_store_folder = '../../output/find_the_best_etf/dataview'

# Back-test and analysis results are stored here
backtest_result_folder = '../../output/find_the_best_etf'

UNIVERSE = '000807.SH'


def get_fundlist(api, invest_type, invest_style):
    '''
    取出符合条件的股票型基金中的指数增强基金
    type，style -- 区分不同的基金
    :param api:
    :param invest_type:
    :param invest_style:
    :return:
    '''
    df, msg = api.query(
        view="lb.mfInfo",
        fields="name,invest_type,invest_style,status",
        filter="",
        data_format='pandas'
    )
    # print(df, msg)
    df = df[(df['invest_type'] == invest_type)
            # & (df['invest_style'] == invest_style)
            & (df['status'] == 101001000)
            & (df['name'].apply(lambda s:'A' not in s))
        ]

    return df


def get_index_map(api, symbols, price_date):
    '''
    取出每支基金对应的指数信息
    :param api:
    :param symbols:
    :param price_date:
    :return:
    '''
    symbol_list = symbols.split(",")
    result = {}
    for symbol in symbol_list:
        df, msg = api.query(
            view="lb.mfTrackingIndex",
            fields="",
            filter="symbol=" + symbol + "&trade_date=" + str(price_date),
            data_format='pandas'
        )
        if df is not None and len(df) > 0:
            result[symbol] = df.loc[0]['index_code']

        time.sleep(0.01)

    return result


def get_fundnav(api, symbol, start_date, end_date):
    '''
    取出基金的历史净值和指数的历史价格信息，注意需要用复权因子矫正后的净值。代码如下：
    :param api:
    :param symbol:
    :param start_date:
    :param end_date:
    :return:
    '''
    df, msg = api.query(
        view="lb.mfNav",
        fields="price_date, nav_adjusted",
        filter="start_pdate=" + str(start_date) + "&end_pdate=" + str(end_date) + "&symbol=" + symbol,
        data_format='pandas'
    )
    if df is None:
        print(df, msg)
        return

    df.index = df['price_date'].astype(np.integer)
    df.sort_index(inplace=True)
    return df


def get_index_daily(api, symbol, start, end):
    # df, msg = api.query(
    df, msg = api.daily(
        symbol=symbol,
        # view=symbol,
        fields="",
        start_date=start,
        end_date=end,
        data_format='pandas'
    )
    if df is None:
        print(df, msg)
        return

    df.index = df['trade_date']
    df.sort_index(inplace=True)
    return df


def cal_active_return(api, symbol, bench, start, end):
    '''
    计算每支基金的管理绩效，包括active return, activevolatility, sharpe ratio, beta, MaxDrawDown等
    :param api:
    :param symbol:
    :param bench:
    :param start:
    :param end:
    :return:
    '''
    # print("in func - cal_active_return: ", symbol, bench, start, end)
    df_nav = get_fundnav(api, symbol, start, end)
    df_idx = get_index_daily(api, bench, start, end)

    if df_nav is None or df_idx is None:
        return None, None, None

    strategy_value = df_nav['nav_adjusted']
    bench_value = df_idx['close']

    market_values = pd.concat([strategy_value, bench_value], axis=1).fillna(method='ffill')
    market_values.columns = ['strat', 'bench']

    df_returns = market_values.pct_change(periods=1).fillna(0.0)
    df_returns = df_returns.join((df_returns.loc[:, ['strat', 'bench']] + 1.0).cumprod(), rsuffix='_cum')

    df_returns.loc[:, 'active_cum'] = df_returns['strat_cum'] - df_returns['bench_cum'] + 1
    df_returns.loc[:, 'active'] = df_returns['active_cum'].pct_change(1).fillna(0.0)

    start = pd.to_datetime(start, format="%Y%m%d")
    end = pd.to_datetime(end, format="%Y%m%d")
    years = (end - start).days / 365.0

    active_cum = df_returns['active_cum'].values
    max_dd_start = np.argmax(np.maximum.accumulate(active_cum) - active_cum) # end of the period
    max_dd_end = np.argmax(active_cum[:max_dd_start]) # start of the period
    max_dd = (active_cum[max_dd_end] - active_cum[max_dd_start]) / active_cum[max_dd_start]

    performance_metrics = dict()
    performance_metrics['Annual Return (%)'] = \
        100 * (np.power(df_returns.loc[:, 'active_cum'].values[-1], 1. / years) - 1)
    performance_metrics['Annual Volatility (%)'] = \
        100 * (df_returns.loc[:, 'active'].std() * np.sqrt(242))
    performance_metrics['Sharpe Ratio'] = \
        (performance_metrics['Annual Return (%)'] / performance_metrics['Annual Volatility (%)'])

    risk_metrics = dict()
    risk_metrics['Beta'] = np.corrcoef(df_returns.loc[:, 'bench'], df_returns.loc[:, 'strat'])[0, 1]
    risk_metrics['Maximum Drawdown (%)'] = max_dd * 100
    risk_metrics['Maximum Drawdown start'] = df_returns.index[max_dd_start]
    risk_metrics['Maximum Drawdown end'] = df_returns.index[max_dd_end]

    # print(performance_metrics, risk_metrics, df_returns)
    return performance_metrics, risk_metrics, df_returns


if __name__ == "__main__":
    api = DataApi(addr="tcp://data.tushare.org:8910")
    df, msg = api.login(data_config["remote.data.username"], data_config["remote.data.password"])
    # print(df, msg)

    df = get_fundlist(api, u'股票型', u'增强指数型')
    symbols = ",".join(df['symbol'])

    start_data = 20161230
    curr_data = 20171227
    index_map = get_index_map(api, symbols, start_data)
    # print(index_map)

    indicators = list()
    for (symbol, index) in index_map.items():
        performance_metrics, risk_metrics, df_returns = cal_active_return(api, symbol, index, start_data, curr_data)
        if performance_metrics is None:
            continue

        indicators.append((symbol,
                           index,
                           performance_metrics['Annual Return (%)'],
                           performance_metrics['Annual Volatility (%)'],
                           performance_metrics['Sharpe Ratio'],
                           df_returns['strat_cum'].iat[-1],
                           df_returns['bench_cum'].iat[-1],
                           risk_metrics['Beta'],
                           risk_metrics['Maximum Drawdown (%)'],
                           risk_metrics['Maximum Drawdown start'],
                           risk_metrics['Maximum Drawdown end']))
        labels = ['symbol', 'index', 'AnnualReturn', 'AnnualVolatility', 'SharpeRatio',
                  'StratCumReturn', 'BenchCumReturn', 'Beta',
                  'MaximumDrawdown', 'MaximumDrawdownStart', 'MaximumDrawdownEnd']
        df = pd.DataFrame.from_records(indicators, columns=labels)
        df.describe()
        df = df.sort_values('SharpeRatio')
        df.sort_values('AnnualReturn')

        str_path = "find_the_best_etf.csv"
        df.to_csv(str_path, )

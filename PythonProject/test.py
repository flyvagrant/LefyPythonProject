
"""
from xtquant import xtdata
stocks = xtdata.get_stock_list_in_sector('沪深A股')  
#增量下载：
for s in stocks:
    if(s=='000001.SZ'):
        xtdata.download_history_data(s, '1d', '','', incrementally=True)

def init(C):
    print("初始化函数")
    #xtdata.download_history_data("000001.SZ","1d","","") # 下载000001.SZ,从20230101至今的日线数据
    xtdata.download_history_data("000001.SZ","1d","20250101","",incrementally=True) # 下载000001.SZ,从20230101至今的日线数据,增量下载

def handlebar(C):
    CURRENTTIME=C.GET_CURRENTTIME()
    print("当前时间:",CURRENTTIME)
    bartime=C.GET_BARTIME()
    return
"""
import time
from xtquant import xtdata
data2 = xtdata.get_local_data(field_list=[], stock_list=['600000.SH', '000001.SZ'],start_time='20251225093000',end_time='20251226150000',period='1m'
        ,dividend_type='none', fill_data=True, data_dir="D:\\国金QMT交易端模拟\\datadir")#
print("get_local_data:",data2)


def do_subscribe_quote(stock_list:list, period:str):
    for i in stock_list:
        xtdata.subscribe_quote(i,period = period)
    time.sleep(1) # 等待订阅完成

def f(data):
    print(data)

code_list=['600000.SH','000001.SZ']
period='1d'

do_subscribe_quote(code_list,period)

data1 = xtdata.get_market_data_ex(
        field_list=['time','close'],
        stock_list=code_list,
        period=period,
        start_time='20250101',
        end_time='20251226',
        count=-1,
        dividend_type='front',
        fill_data=True
        #,subscribe=True
    )
print("DF_market_data:",data1['000001.SZ'])

df_stk=xtdata.get_instrument_detail('300668.SZ')#获取的股本不正确
print("get_instrument_detail:",df_stk)
"""
#do_subscribe_quote(code_list,period = 'limitupperformance') # 不支持订阅：snapshotindex（股票快照），stoppricedata（涨跌停价）,limitupperformance()集合竞价
#data = xtdata.get_market_data_ex([], code_list,period="snapshotindex",start_time = "", end_time = '')

do_subscribe_quote(code_list,period = 'transactioncount1m')# 不支持订阅 transactioncount1m（资金流向数据）
data = xtdata.get_market_data_ex([], code_list,period="transactioncount1m",start_time = "", end_time = '')
print("transactioncount1m:",data)
"""
#xtdata.download_history_data("000001.SZ",period="transactioncount1d")

do_subscribe_quote(code_list,period = 'transactioncount1d')
data = xtdata.get_market_data_ex([],["000001.SZ"],period="transactioncount1d",start_time = "20251201", end_time = "20251225")
print("transactioncount1m:",data)

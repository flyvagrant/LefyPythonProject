import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
from xtquant import xtdata,xttrader
from xtquant.xttype import StockAccount
from xtquant.xttrader import XtQuantTraderCallback
from xtquant import xtconstant
import time
import copy

################################## 参数设置 ############################################################

trade_path = r"D:\国金QMT交易端模拟\userdata_mini" # 指定【实盘客户端】所在路径, 券商端指定到 userdata_mini文件夹
account = StockAccount("testS", "STOCK") # StockAccount("账号代码", "账号类型，股票为STOCK")
# account = StockAccount("2000567", "STOCK") #
use_money = 100000 # 每个标的下单用的金额，单位元，需要四舍五入时会向下取整
stock_sector = "沪深京A股" # 标的池范围，根据客户端板块选择，全市场传【沪深京A股】也可以选自选股板块，也可以自填列表
strategyName = "MA趋势交易" # 【核心设置】，策略调度的VBA指标，必须存在 **投研专业版或投研青春版** 中
period = "1d" # 指标运行周期
count = 500 # 使用K线数量，单位/根，适量减少调度数据可以加快运算速度，但是不要少于指标所用数据量
dividend_type = "front_ratio" # 复权方式，这里是等比前复权
extend_param = {} # 创建分组以减少内存占用，在内存不足的建议启用，如果运行内存充足则不需要，参考下一行写法
# extend_param = {"_group":"group1"} 


################################### 以下不需要改 ############################################################

class CallBack(XtQuantTraderCallback):
    def on_order_stock_async_response(self, response):
        print("test on_order_stock_async_response")
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        print(datetime.now(),response.seq)
    



def is_trade_time(trading_time_info):
    print("test is_trade_time")
    '''
    Args:
        trading_time_info:格式需要如下
            stock_trade_time = (["09:30:00","11:30:00"],["13:00:00","15:00:00"])
            future_trade_time = (["09:00:00","10:15:00"],["10:30:00","11:30:00"],["13:30:00","15:00:00"],["21:00:00","26:30:00"])
    return:bool
    '''
    
    _now = int((datetime.now() - timedelta(hours=4)).strftime("%H%M%S"))
    for _time_list_ in trading_time_info:
        st_str = _time_list_[0]
        _sp_st = (int(st_str.split(":")[0]) - 4) * 10000 + (int(st_str.replace(":", "")) % 10000)
        et_str = _time_list_[1]
        _sp_et = (int(et_str.split(":")[0]) - 4) * 10000 + (int(et_str.replace(":", "")) % 10000)
        
        if _sp_st <= _now < _sp_et:
            return True
    return False


def create_formula_callback(stock):
    print("test create_formula_callback")
    global buy_signal,sell_signal
    def formula_callback(formula_results):
        global _time
        time = formula_results["timelist"][-1]
        _time = time
        for key in ["买入信号","卖出信号"]:
            fild_values = formula_results["outputs"].get(key,None)
            if not fild_values:
                continue
            if key == "买入信号":
                buy_signal.setdefault(time, {})
                buy_signal[time][stock] = fild_values[-1]
            elif key == "卖出信号":
                sell_signal.setdefault(time, {})
                sell_signal[time][stock] = fild_values[-1]
            
    return formula_callback

def query_stock_holding(account):
    print("test query_stock_holding")
    """查询股票持仓

    Args:
        account (_type_): 股票账户类

    Returns:
    stock:{
        "volume":obj.volume,
        "can_use_volume":obj.can_use_volume,
        "open_price":obj.open_price,
        "market_value":obj.market_value,
        "yesterday_volume":obj.yesterday_volume,
        "avg_price":obj.avg_price
        
    """
    positions = api.query_stock_positions(account)
    Position_info = {}
    for obj in positions:
        Position_info[obj.stock_code]= {
            "volume":obj.volume,
            "can_use_volume":obj.can_use_volume,
            "open_price":obj.open_price,
            "market_value":obj.market_value,
            "yesterday_volume":obj.yesterday_volume,
            "avg_price":obj.avg_price
        }
    return Position_info

def query_stock_order_info(account) -> dict :
    print("test query_stock_order_info")
    """
    返回的结构是{stock:{order_sysID:{order_info...}}}
    """
    order = api.query_stock_orders(account)
    Order_info = {}
    for obj in order:
        stock = obj.stock_code
        Order_info.setdefault(stock, {})
        order_time = obj.order_time # 委托时间
        order_type = obj.order_type # 委托方向判断
        order_remark = obj.order_remark # 投资备注
        order_volume = obj.order_volume # 委托量
        volume_total= order_volume - obj.traded_volume # 剩余委托量
        order_status = obj.order_status #委托状态
        limit_price = obj.price # 委托价格
        order_sysID = obj.order_sysid # 委托编号
        Order_info[stock][order_sysID] = {
            "order_time":order_time, # 委托时间
            "order_volume":order_volume,# 委托量
            "volume_total":volume_total,# 剩余委托量
            "order_status":order_status,#委托状态
            "order_remark":order_remark, # 投资备注
            "order_type":order_type, # 成交方向判断
            "limit_price":limit_price
        }
    return Order_info

def inster_stock_order(account, stock_code, optype, lots, price = -1, remark = ""):
    
    print("test inster_stock_order")
    if "waiting_dict" not in globals().keys():
        global waiting_dict
        waiting_dict = {}
    
    if stock_code in waiting_dict:
        print(f"{stock_code} 未查到或存在未撤回委托 {waiting_dict[stock_code]} 暂停后续报单")
        return False

    optype = 23 if optype == "buy" else 24
    if remark == "":
        dateNow = datetime.now()
        dateNow = dateNow.hour * 3600 + dateNow.minute * 60 + dateNow.second
        remark = f"{stock_code}_{optype}_{dateNow}"
    lots = int(lots)
    price_type = xtconstant.LATEST_PRICE if not price  else xtconstant.FIX_PRICE
    api.order_stock_async(account, stock_code, optype, lots, price_type, price, order_remark=remark)
    print(f"inster_order -- stock:{stock_code},optype:{optype},lots:{lots},price:{price},order_remark:{remark}")
    waiting_dict[stock_code] = remark




def run_trade():
    print("test run_trade")
    if not is_trade_time((["09:30:00","11:30:00"],["13:00:00","15:00:00"])):
        print(f"{datetime.now()} -- 当前为非交易时间")
        return
    if len(buy_signal) == 0 or len(sell_signal) == 0 or _time == "":
        print(f"信号还没准备好,buy_signal:{buy_signal}, sell_signal:{sell_signal}, _time:{_time}")
        return
    timetag = xtdata.get_market_data_ex_ori(["time"],["000001.SH"],period = period,count=1)["000001.SH"]["time"][-1]
    if timetag not in buy_signal.keys() or timetag not in sell_signal.keys():
        print("---- wait ----")
        return
    print(f"{datetime.now()} -- 正在监控交易")
    holding_info = query_stock_holding(account)
    order_info = query_stock_order_info(account)
    _buy_signal = copy.deepcopy(buy_signal)
    _sell_signal = copy.deepcopy(sell_signal)
    
    
    for stock in order_info:
        for k,v in order_info[stock].items():
            if v["order_status"] in [56,53,54] and v["order_remark"] == waiting_dict.get(stock,"_"):
                order_remark = v["order_remark"]
                order_status = v["order_status"]
                print(f"{stock} 查到投资备注{order_remark},order_status:{order_status},从等待字典删除")
                del waiting_dict[stock]
            if v["order_status"] == 57 and v["order_remark"] == waiting_dict.get(stock,"_"): # 如果是买的废单，移除
                order_remark = v["order_remark"]
                print(f"{stock} 委托状态为废单，查到投资备注{order_remark}从等待字典删除")
                del waiting_dict[stock]
    
    
    for stock in _buy_signal.get(timetag,{}):
        _signal = _buy_signal[timetag][stock]
        if holding_info.get(stock,{}).get("volume",0) > 0:
            
            continue
        if _signal:
            tick = xtdata.get_full_tick([stock])[stock]
            ask_price = tick["askPrice"][0]
            fix_price = round(ask_price,3) if ask_price != 0 else tick["lastPrice"]
            lots = int(use_money / fix_price / 100 ) * 100 # 加四舍五入，向上取整
            inster_stock_order(account,stock, "buy", lots, fix_price)
            print(f"{datetime.now()} -- {stock} 触发买入")
            
    for stock in _sell_signal.get(timetag,{}):
        _signal = _sell_signal[timetag][stock]
        if holding_info.get(stock,{}).get("can_use_volume",0) == 0:
            print(f"{stock} 无可卖出仓位")
            continue
        if _signal:
            tick = xtdata.get_full_tick([stock])[stock]
            bid_price = tick["bidPrice"][0]
            fix_price = round(bid_price,3) if bid_price != 0 else tick["lastPrice"]
            lots = holding_info[stock]["volume"]
            inster_stock_order(account,stock, "sell", lots, fix_price)
            print(f"{datetime.now()} -- {stock} 触发卖出")
            


if __name__ == "__main__":
    print("test__main__")
    
    while 1:
        _time = xtdata.get_trading_dates("SH",count=1)[0]
        now = datetime.now()
        
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        timestamp = int(start_of_day.timestamp())*1000  # 转换为整型时间戳（秒）
        if _time < timestamp:
            print("交易日未切换,等待60秒")
            time.sleep(60)
        else:
            break
    
    callback = CallBack()
    
    api = xttrader.XtQuantTrader(trade_path,int(time.time()),callback)
    api.start()
    
    connect_result = api.connect()
    if connect_result != 0:
        raise OSError(f"交易连接失败，当前交易地址为{trade_path}, 建议检查改路径是否正确，或miniqmt是否正确开启")
    subscribe_result = api.subscribe(account)
    if subscribe_result != 0:
        raise OSError(f"账号订阅失败，当前账号{account.account_id},账号类型{account.account_type}")
    
    xtdata.subscribe_quote("000001.SH",period=period,count=1)
    
    
    
    buy_signal = {}
    sell_signal = {}
    waiting_dict = {}
    
    _time = ""
    start_time = "" # 数据开始时间，可以不填
    end_time = "" # 数据结束时间
    
    xtdata.download_sector_data()
    
    ls = xtdata.get_stock_list_in_sector(stock_sector)

    
    
    for i in ls:
        
        xtdata.subscribe_formula(
            formula_name = strategyName,
            stock_code = i,
            period = period,
            start_time = start_time,
            end_time = end_time,
            count = count,
            dividend_type = dividend_type,
            callback = create_formula_callback(i),
            extend_param = extend_param
        )
    
    while 1:
        try:
            run_trade()
            time.sleep(3)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"发生错误 -- {tb}")
            input(f"{e}按下回车键退出")
            exit()


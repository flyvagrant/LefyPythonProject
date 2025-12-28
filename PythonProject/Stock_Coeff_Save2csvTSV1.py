# -*- coding: utf-8 -*-
"""
项目名称：股票相关性分析工具
功能描述：计算多只股票的价格/收益率相关系数，并将结果追加保存到CSV
作者：XXX
创建时间：2025-12-28
版本：v1.0
依赖库：pandas, akshare, scipy, os
"""
import os
import time
import sys
from typing import Tuple, List  # 类型注解（提升代码可读性）
from xtquant import xtdata
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# ===================== 2. 配置常量（大写命名，集中管理可配置项） =====================
# 文件路径
CSV_SAVE_Result = "D:\\Work\\Stock_Coefficient\\股票相关性结果.csv"
CSV_SAVE_PATH = "D:\\Work\\Stock_Coefficient\\"
# 数据时间范围
START_DATE = "20250101"
END_DATE = "20251231"
PERIOD='1d'
# 相关系数计算阈值（筛选有效数据）
MIN_DATA_ROWS = 30  # 至少30行数据才计算相关性

# 股票代码与名称映射（便于维护）
STOCK_MAPPING = {
    "600519": "贵州茅台",
    "000858": "五粮液",
    "000568": "泸州老窖",
    "600809": "山西汾酒"
}

def calculate_correlation(df1: pd.DataFrame, df2: pd.DataFrame, stock1_code: str, stock2_code: str) -> Tuple[float, float, float]:
    """
    计算两只股票的价格相关系数、收益率相关系数及p值
    :param df1: 股票1的DataFrame
    :param df2: 股票2的DataFrame
    :param stock1_code: 股票1代码
    :param stock2_code: 股票2代码
    :return: (价格相关系数, 收益率相关系数, p值)
    """
    # 对齐日期
    df_combined = pd.merge(df1, df2, left_index=True, right_index=True, suffixes=("_"+stock1_code, "_"+stock2_code))
    # 处理缺失值（删除空行，或用ffill/bfill填充）
    df_combined = df_combined.dropna()
    # 计算价格相关系数
    price_corr = df_combined[f"close_{stock1_code}"].corr(df_combined[f"close_{stock2_code}"])
    # 计算收益率及收益率相关系数
    df_combined["return_{stock1_code}"] = df_combined[f"close_{stock1_code}"].pct_change()
    df_combined["return_{stock2_code}"] = df_combined[f"close_{stock2_code}"].pct_change()
    df_combined = df_combined.dropna()
    return_corr, p_val = stats.pearsonr(df_combined["return_{stock1_code}"], df_combined["return_{stock2_code}"])
    df_combined.to_csv(
        "D:\\Work\\Stock_Coefficient\\"+stock1_code+"_"+stock2_code+"原始数据.csv",
        index=False,
        encoding="utf-8-sig"
    )
    # 保留4位小数
    return round(price_corr, 4), round(return_corr, 4), round(p_val, 4)

def append_to_csv(result_data: dict) -> None:
    """
    将结果追加保存到CSV文件（自动处理表头）
    :param result_data: 待保存的字典（key为列名）
    """
    # 转换为DataFrame
    df_result = pd.DataFrame([result_data])
    # 判断文件是否存在，决定是否写表头
    if os.path.exists(CSV_SAVE_Result):
        df_result.to_csv(
            CSV_SAVE_PATH,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8-sig"
        )
    else:
        df_result.to_csv(
            CSV_SAVE_Result,
            mode="w",
            header=True,
            index=False,
            encoding="utf-8-sig"
        )
    print(f"✅ 已追加数据：{result_data['股票对']}")

def main(stock_pairs: List[Tuple[str, str]]) -> None:
    """
    主流程：批量计算股票对相关性并保存结果
    :param stock_pairs: 股票对列表，如[("600519", "000858"), ...]
    """
    print(f"===== 开始股票相关性分析（{START_DATE} - {END_DATE}）=====")
    for stock1_code, stock2_code in stock_pairs:
        try:
            print(f"--- 处理股票对：{stock1_code} - {stock2_code} ---")
            # 1. 获取数据
            df1 = xtdata.get_local_data(
                    field_list=['close'],
                    stock_list=[stock1_code],
                    period=PERIOD,
                    start_time=START_DATE,
                    end_time=END_DATE,
                    dividend_type='front',
                    fill_data=True, data_dir="D:\\国金QMT交易端模拟\\datadir"
                    #,subscribe=True
                )
            df2 = xtdata.get_local_data(
                    field_list=['close'],
                    stock_list=[stock2_code],
                    period=PERIOD,
                    start_time=START_DATE,
                    end_time=END_DATE,
                    dividend_type='front',
                    fill_data=True, data_dir="D:\\国金QMT交易端模拟\\datadir"
                    #,subscribe=True
                )
            df1 = df1[stock1_code]
            df2 = df2[stock2_code]
            print(f"获取数据成功：{stock1_code}（{len(df1)}行），{stock2_code}（{len(df2)}行）")
            if(len(df1) < MIN_DATA_ROWS) or (len(df2) < MIN_DATA_ROWS):
                print(f"❌ 数据行数不足，跳过{stock1_code}-{stock2_code}的相关性计算")
                continue

            # 2. 计算相关性
            price_corr, return_corr, p_val = calculate_correlation(df1, df2, stock1_code, stock2_code)
            print(f"计算结果 - 价格相关系数: {price_corr}, 收益率相关系数: {return_corr}, p值: {p_val}")
        except Exception as e:
            print(f"❌ 处理{stock1_code}-{stock2_code}失败：{str(e)}")
            continue
    print(f"===== 分析完成！结果已保存至：{os.path.abspath(CSV_SAVE_PATH)} =====")

# ===================== 5. 入口函数（防止被导入时执行） =====================
if __name__ == "__main__":
    # 定义需要分析的股票对
    target_stock_pairs = [
        ("000300.SH", "000768.SZ"),
        ("000300.SH", "000877.SZ")
    ]
    print(target_stock_pairs)
    # 执行主逻辑
    main(target_stock_pairs)

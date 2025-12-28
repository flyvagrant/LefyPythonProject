
import time
from xtquant import xtdata
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

period='1d'
stk1='000300.SH'
stk2='000877.SZ'
stock1  = xtdata.get_local_data(
        field_list=['close'],
        stock_list=[stk1],
        period=period,
        start_time='20250101',
        end_time='20251226',
        dividend_type='front',
        fill_data=True, data_dir="D:\\国金QMT交易端模拟\\datadir"
        #,subscribe=True
    )
stock1 = stock1[stk1]
stock2  = xtdata.get_local_data(
        field_list=['close'],
        stock_list=[stk2],
        period=period,
        start_time='20250101',
        end_time='20251226',
        dividend_type='front',
        fill_data=True, data_dir="D:\\国金QMT交易端模拟\\datadir"
        #,subscribe=True
    )
stock2 = stock2[stk2]
print("茅台数据:",stock1)
print("五粮液数据:",stock2)

if(len(stock2)==0 or len(stock1)==0):
    print("数据获取失败，请检查本地数据目录或下载历史数据")
    exit()

# ===================== 2. 数据预处理（对齐时间、处理缺失值） =====================
# 合并两只股票数据，按日期对齐
df_combined = pd.merge(stock1, stock2, left_index=True, right_index=True, suffixes=("_"+stk1, "_"+stk2))
# 处理缺失值（删除空行，或用ffill/bfill填充）
df_combined = df_combined.dropna()
print("合并数据1:",df_combined)

# 可选：计算收益率（价格相关性易受趋势影响，收益率相关性更能反映波动同步性）
df_combined["return_"+stk1] = df_combined["close_"+stk1].pct_change()
df_combined["return_"+stk2] = df_combined["close_"+stk2].pct_change()
df_combined = df_combined.dropna()  # 收益率会产生首行NaN，删除
print("合并数据2:",df_combined)

# ===================== 3. 计算相关系数 =====================
# 方法1：用pandas直接计算（推荐，简洁）
# 价格相关系数
price_corr = df_combined["close_"+stk1].corr(df_combined["close_"+stk2])
# 收益率相关系数（更常用）
return_corr = df_combined["return_"+stk1].corr(df_combined["return_"+stk2])

# 方法2：用scipy计算（可同时获取p值，判断相关性是否显著）
return_corr_scipy, p_value = stats.pearsonr(df_combined["return_"+stk1], df_combined["return_"+stk2])

# 输出结果
print("=== 相关性分析结果 ===")
print(f"价格相关系数：{price_corr:.4f}")
print(f"收益率相关系数（pandas）：{return_corr:.4f}")
print(f"收益率相关系数（scipy）：{return_corr_scipy:.4f}，p值：{p_value:.4f}")
# p值<0.05说明相关性在统计上显著
if p_value < 0.05:
    print("结论：两只股票收益率存在显著的线性相关")
else:
    print("结论：两只股票收益率的线性相关不显著")

# ===================== 4. 可视化（直观展示相关性） =====================
plt.rcParams["font.sans-serif"] = ["SimHei"]  # 解决中文显示
plt.figure(figsize=(12, 6))

# 子图1：价格走势对比
ax1 = plt.subplot(121)
df_combined["close_"+stk1].plot(label=stk1, ax=ax1, color="red")
df_combined["close_"+stk2].plot(label=stk2, ax=ax1, color="blue")
ax1.set_title("股价走势对比（2025）")
ax1.set_xlabel("日期")
ax1.set_ylabel("收盘价（元）")
ax1.legend()
ax1.grid(True)

# 子图2：收益率散点图（直观看相关性）
ax2 = plt.subplot(122)
plt.scatter(df_combined["return_"+stk1], df_combined["return_"+stk2], alpha=0.6)
# 添加拟合线
z = np.polyfit(df_combined["return_"+stk1], df_combined["return_"+stk2], 1)
p = np.poly1d(z)
plt.plot(df_combined["return_"+stk1], p(df_combined["return_"+stk1]), "r--", linewidth=2)
# 添加相关系数标注
plt.text(0.02, 0.05, f"相关系数：{return_corr:.4f}", fontsize=12)
ax2.set_title("收益率散点图")
ax2.set_xlabel(stk1+"日收益率")
ax2.set_ylabel(stk2+"日收益率")
ax2.grid(True)

plt.tight_layout()
plt.show()
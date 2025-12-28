# copilot-instructions.md — 为 AI 助手准备的项目指南

目的：帮助自动化编码智能体（Copilot/assistant）快速在此仓库中产出可用、低风险的修改。

要点速览
- 仓库类型：小型策略脚本仓库，核心依赖 `xtquant`、`xtdata`、`pandas`、`numpy`。
- 主要入口：`xtqmt_xsz_ts.py`（包含 `init(C)`, `after_init(C)`, `handlebar(C)` 等策略钩子）。
- 运行命令：`python xtqmt_xsz_ts.py`（脚本内 `param` 字典可调整回测/运行参数）。

关键约定（必须遵守）
- `C`（context）是主要运行时接口：优先使用 `C.get_*` 提供的数据/合约查询方法，不要替换为自建全局数据源。
- 全局状态使用 `g`（单例空类），常见字段如 `g.factor_df`, `g.close_df`, `g.holdings`。不要随意改名或改为局部变量。
- 数据结构约定：多数时间序列以时间为 index、证券代码为 columns 的 `pandas.DataFrame`。很多计算依赖 `.shift(1)` 避免未来函数泄露 —— 保持这一惯例。

常见模式与示例
- 防止未来函数：见 `xtqmt_xsz_ts.py` 中 `g.factor_df = factor_sorted.shift(1)` 与 `g.close_df = close_df.shift(1)`。
- 排序筛选：`rank_filter(df, N)` 返回布尔 DataFrame，随后作为买入/持仓掩码使用。
- 接口差异：仓内代码存在 `get_instrumentdetail` 与 `get_instrument_detail` 两种写法；在运行环境中先确认 `C`/`xtdata` 的实际 API 名称后再修改调用。

运行与调试
- 本地运行：在仓库根目录运行 `python xtqmt_xsz_ts.py`。
- 参数调整：脚本内部使用 `param` 字典传参给 `run_strategy_file`；可直接在脚本中修改 `start_time`/`end_time`/`period` 等。
- 依赖安装：确保 `xtquant`、`xtdata`（若有）、`pandas`、`numpy` 可用。CI 环境建议 mock `xtdata` 接口以便单元测试。
- 简单检测：`test.py` 用途极简，可作为环境检查示例。

修改与 PR 指南（建议）
- 不要修改 `g` 的字段名或数据布局，除非所有调用点一起更新并经过本地回测验证。
- 变更外部 API 调用前，先在交互 REPL 中验证 `C`/`xtdata` 的真实方法名。
- 如果添加测试，优先用适配器/Mock 封装 `xtdata`/`xtquant` 调用，避免在 CI 中依赖真实数据源。

如果有不完整或运行失败的地方，请指出文件与行号（或提供可复现步骤），我会据此迭代本指南。

主要示例文件：
- xtqmt_xsz_ts.py
- test.py

—— 结束 ——

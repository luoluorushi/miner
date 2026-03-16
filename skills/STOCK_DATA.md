# Stock Data 子技能

**版本**: 2.3.0

**作用**：提供股票市场数据查询能力，包括实时行情、K线/分时数据、财务报表、资金流向、新闻公告、研究报告和公司简况

**数据源**：腾讯自选股行情数据接口

**支持市场**：A股（沪深/科创/北交所）、港股、美股

---

## 二进制工具

位于 `gold-miner/bin/` 目录：
- `stock-data-darwin-aarch64`（macOS Apple Silicon）
- `stock-data-linux-x86_64`（Linux）
- `stock-data-windows-x86_64.exe`（Windows）

**Windows 调用示例**：
```bash
d:/code/androws/gold-miner/bin/stock-data-windows-x86_64.exe <command> <args>
```

---

## 核心命令

### 1. 股票搜索
```bash
stock-data search 腾讯控股        # 搜索股票
stock-data search 华夏 fund       # 搜索基金
stock-data search 科技 sector     # 搜索板块
```

### 2. 实时行情
```bash
stock-data quote sh600000                    # 单只股票
stock-data quote sh600000,sz000001,hk00700   # 多只股票
```

### 3. K线数据
```bash
stock-data kline sh600000 day 20     # 日K线
stock-data kline hk00700 week 10     # 周K线
stock-data kline sz000001 day 60 qfq # 前复权
```

**周期选项**：`day`, `week`, `month`, `season`, `year`, `m1`, `m5`, `m15`, `m30`, `m60`, `m120`

**复权类型**：空(不复权), `qfq`(前复权), `hfq`(后复权)

### 4. 财务数据

**A股**：
```bash
stock-data finance sh600000 summary  # 财报摘要
stock-data finance sh600000 lrb      # 利润表
stock-data finance sh600000 zcfz     # 资产负债表
stock-data finance sh600000 xjll     # 现金流量表
```

**港股**：
```bash
stock-data finance hk00700 zhsy 4    # 综合损益表
stock-data finance hk00700 zcfz 2    # 资产负债表
stock-data finance hk00700 xjll 8    # 现金流量表
```

**美股**：
```bash
stock-data finance BABA.N income 4    # 利润表
stock-data finance BABA.N balance 2   # 资产负债表
stock-data finance BABA.N cashflow 8  # 现金流量表
```

### 5. 公司简况
```bash
stock-data profile sh600000
stock-data profile hk00700
stock-data profile usAAPL
```

### 6. 资金分析
```bash
# 港股资金
stock-data hkfund hk00700

# A股主力资金
stock-data asfund sh600000
stock-data asfund sh600000 historyFundFlow 30

# A股公开交易数据
stock-data aspublic sh600000
stock-data aspublic sh600000 rzrq      # 融资融券
stock-data aspublic sh600000 lhb,dzjy  # 龙虎榜+大宗交易
```

### 7. 新闻资讯
```bash
stock-data news sh600000      # 综合资讯
stock-data notice sh600000    # 公告列表（A股）
stock-data rating sh600000    # 机构评级（A股）
stock-data report sh600000    # 研报列表
```

### 8. 筹码分布
```bash
stock-data chip sh600000                # 最新筹码
stock-data chip sh600000 2026-03-06     # 指定日期
stock-data chip sh600000 --price 10.50  # 指定价格获利比例
```

---

## 股票代码格式

| 市场 | 格式 | 示例 |
|------|------|------|
| 沪市 | sh + 6位数字 | `sh600000` |
| 深市 | sz + 6位数字 | `sz000001` |
| 科创板 | sh + 6位数字 | `sh688981` |
| 港股 | hk + 5位数字 | `hk00700` |
| 美股 | us + 代码 | `usAAPL` |

---

## 已知限制

- 港股/美股财务API返回可能为空，需要手动补充数据
- 部分命令仅支持A股（如 `notice`, `rating`）

# 股票评估 Prompt 模板

## 触发条件
当用户请求评估某只股票时，使用此流程。

## 输入
- 股票代码或名称

## 评估流程

### Step 1: 基础信息获取（脚本）
```bash
# 搜索股票代码（如果只有名称）
stock-data search {公司名称}

# 获取公司简介
stock-data profile {股票代码}

# 获取财务数据
stock-data finance {股票代码} summary

# 获取实时行情
stock-data quote {股票代码}

# 获取研报评级
stock-data rating {股票代码}

# 获取新闻
stock-data news {股票代码}
```

### Step 2: AI含量评估（LLM搜索）
搜索关键词：
- "{公司名称} AI业务 收入占比"
- "{公司名称} 英伟达 供应商"
- "{公司名称} AI服务器 订单"
- "{公司名称} 2025年报 AI业务"

评估要点：
1. AI相关业务收入占比
2. 主要AI客户（英伟达、微软、谷歌、Meta、字节等）
3. AI产品/服务的具体内容
4. AI业务的增长趋势

### Step 3: 护城河评估（LLM搜索）
搜索关键词：
- "{公司名称} 市占率 行业排名"
- "{公司名称} 核心技术 专利"
- "{公司名称} 竞争优势"
- "{公司名称} vs {主要竞争对手}"

评估要点：
1. 全球/国内市占率
2. 技术壁垒（专利、良率、工艺）
3. 规模优势（产能、成本）
4. 客户粘性（认证周期、切换成本）

### Step 4: 需求增长评估（LLM搜索）
搜索关键词：
- "{所在行业} 市场规模 增速 2026"
- "{公司名称} 订单 产能利用率"
- "{公司名称} 扩产 投资"
- "{下游行业} 资本开支 2026"

评估要点：
1. 行业市场规模和CAGR
2. 公司订单/营收增速
3. 产能利用率和扩产计划
4. 下游需求驱动因素

### Step 5: 财务质量评估（脚本计算）
从财务数据自动计算：
- ROE
- 毛利率
- 净利率
- 经营现金流/净利润
- 资产负债率

### Step 6: 估值评估（脚本+LLM）
脚本获取：
- 当前PE/PB/PS
- 历史估值区间

LLM分析：
- 与同行业对比
- PEG计算（需要预测增速）
- 估值合理性判断

### Step 7: 市值/AI利润比计算（脚本）
```python
# 计算公式
market_cap = quote_data.market_cap  # 市值
profit = finance_data.profit_ttm    # 总利润
ai_revenue_pct = <从搜索结果获取>    # AI收入占比

ai_profit = profit * ai_revenue_pct / 100
mcap_ai_profit_ratio = market_cap / ai_profit

# 评分
if mcap_ai_profit_ratio < 30:
    score = 5  # 明显低估
elif mcap_ai_profit_ratio < 50:
    score = 4  # 合理定价
elif mcap_ai_profit_ratio < 80:
    score = 3  # 增速匹配
elif mcap_ai_profit_ratio < 150:
    score = 2  # 偏高
else:
    score = 1  # 严重高估
```

### Step 8: 催化剂/风险评估（LLM搜索）
搜索关键词：
- "{公司名称} 最新消息 利好"
- "{公司名称} 新产品 新客户"
- "{公司名称} 风险 减持 解禁"
- "{公司名称} 研报 投资评级"

评估要点：
1. 近期催化剂事件
2. 潜在风险因素
3. 券商评级和目标价

### Step 9: 更新数据库（脚本）
```bash
# 更新各维度评分
python db.py update {code} -d ai_exposure -s {score} -e "{evidence}"
python db.py update {code} -d moat -s {score} -e "{evidence}"
python db.py update {code} -d demand_growth -s {score} -e "{evidence}"
python db.py update {code} -d financial_quality -s {score} -e "{evidence}"
python db.py update {code} -d valuation -s {score} -e "{evidence}"
python db.py update {code} -d mcap_ai_profit_ratio -s {score} -e "{evidence}"
python db.py update {code} -d catalyst_risk -s {score} -e "{evidence}"
```

---

## 输出格式

### 展示给用户的评估报告

```markdown
# {股票名称} ({股票代码}) 评估报告

## 基本信息
- 所属板块: {sector}
- 主营业务: {main_business}
- 市值: {market_cap}亿

## 七维度评分

| 维度 | 评分 | 关键依据 |
|-----|------|---------|
| AI含量 | ⭐×{score} | {evidence} |
| 护城河 | ⭐×{score} | {evidence} |
| 需求增长 | ⭐×{score} | {evidence} |
| 财务质量 | ⭐×{score} | {evidence} |
| 市值/AI利润比 | ⭐×{score} | {ratio}x - {analysis} |
| 估值 | ⭐×{score} | {evidence} |
| 催化剂/风险 | ⭐×{score} | {evidence} |

## AI总评
- **评分**: {total_score} / 5.0
- **评级**: {rating}
- **投资逻辑**: {investment_thesis}

## 风险提示
1. {risk_1}
2. {risk_2}
3. {risk_3}

---
请给出您的评级(1-5星)和备注:
```

### 写入数据库的JSON格式

```json
{
  "stock_code": "xxx",
  "stock_name": "xxx",
  "sector": "xxx",
  "evaluation_date": "2026-03-13",
  
  "dimensions": {
    "ai_exposure": {
      "score": 4,
      "ai_revenue_pct": 30,
      "key_customers": ["英伟达", "微软"],
      "evidence": "...",
      "confidence": "high"
    },
    "moat": {
      "score": 4,
      "moat_type": ["技术壁垒", "规模效应"],
      "market_share": "全球第X",
      "evidence": "..."
    },
    "demand_growth": {
      "score": 4,
      "industry_cagr": "30%",
      "company_growth": "40%",
      "evidence": "..."
    },
    "financial_quality": {
      "score": 4,
      "roe": 18.5,
      "gross_margin": 28.3,
      "net_margin": 12.1
    },
    "valuation": {
      "score": 3,
      "pe_ttm": 35,
      "peg": 0.9,
      "vs_industry": "略高于行业平均"
    },
    "mcap_ai_profit_ratio": {
      "score": 3,
      "market_cap_billion": 500,
      "total_profit_billion": 10,
      "ai_revenue_pct": 30,
      "ai_profit_billion": 3,
      "ratio": 166.7,
      "analysis": "市值/AI利润比偏高"
    },
    "catalyst_risk": {
      "score": 3,
      "catalysts": ["...", "..."],
      "risks": ["...", "..."]
    }
  },
  
  "ai_total_score": 3.65,
  "ai_rating": "⭐⭐⭐",
  "ai_summary": "一句话总结",
  "ai_investment_thesis": "详细投资逻辑..."
}
```

---

## 注意事项

1. **数据时效性**：优先使用最新数据，注明数据日期
2. **信息可信度**：区分官方披露、券商研报、媒体报道
3. **保守原则**：无法确认时给予较低评分
4. **对比思维**：将公司与同行对比评估
5. **程序化更新**：评估完成后必须调用 `db.py` 更新数据库

# Gold Miner 技能部署到 OpenClaw 指南

本文档说明如何将 Gold Miner（挖金矿）技能部署到 OpenClaw，通过企业微信聊天使用。

---

## 一、部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    企业微信智能机器人                      │
│                          ↓                              │
│                     OpenClaw 网关                        │
│                          ↓                              │
│            ┌─────────────────────────────┐              │
│            │    Gold Miner Skill         │              │
│            │  ├── SKILL.md (技能描述)     │              │
│            │  ├── bin/ (数据查询工具)     │              │
│            │  ├── scripts/db.py (数据库)  │              │
│            │  └── database/ (评级数据)    │              │
│            └─────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## 二、准备工作

### 2.1 OpenClaw 环境要求

- Node.js >= 22
- OpenClaw 已安装并初始化
- 企业微信智能机器人已创建（长连接方式）
- Python 3.8+ （用于运行 db.py 脚本）

### 2.2 获取技能文件

将 `gold-miner` 整个目录复制到 OpenClaw 服务器：

```bash
# 方式1：直接复制
scp -r gold-miner/ user@your-server:~/

# 方式2：通过 Git（如果已纳入版本管理）
git clone <your-repo> && cd <repo>/gold-miner
```

---

## 三、部署步骤

### 步骤 1：创建技能目录

OpenClaw 会从以下位置加载技能（优先级从高到低）：
1. **Workspace skills**: `<workspace>/.codebuddy/skills/` 或 `<workspace>/skills/`
2. **User skills**: `~/.openclaw/skills/`
3. **Bundled skills**: 系统内置

**推荐放到用户技能目录**：

```bash
# Linux/macOS
mkdir -p ~/.openclaw/skills/gold-miner
cp -r gold-miner/* ~/.openclaw/skills/gold-miner/

# Windows PowerShell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.openclaw\skills\gold-miner" -Force
Copy-Item -Path "gold-miner\*" -Destination "$env:USERPROFILE\.openclaw\skills\gold-miner\" -Recurse
```

### 步骤 2：创建 SKILL.md 文件

OpenClaw 通过 `SKILL.md` 文件识别技能。将现有 `skill.md` 重命名并调整格式：

**文件位置**: `~/.openclaw/skills/gold-miner/SKILL.md`

```markdown
---
name: gold-miner
description: AI受益股"金矿股"挖掘与评估系统，用于分析股票的AI受益程度、七维度评分、排行榜查询
triggers:
  - 评估股票
  - 分析股票
  - 金矿股
  - AI受益股
  - 股票排行
  - 挖金矿
requirements:
  - python>=3.8
---

# Gold Miner Skill (挖金矿)

## 描述
AI受益股"金矿股"挖掘与评估系统。已完成313只AI受益股的七维度评估，支持排行榜查询、板块筛选、个股深度分析。

## 核心能力

### 1. 查看排行榜
```bash
python ~/.openclaw/skills/gold-miner/scripts/db.py list --top 20 --sort ai
```

### 2. 按板块筛选
```bash
python ~/.openclaw/skills/gold-miner/scripts/db.py list --sector 光通信
```

可选板块: 光通信, AI芯片, 半导体设备, 存储, 散热, 服务器, PCB, 云计算

### 3. 查看个股详情
```bash
python ~/.openclaw/skills/gold-miner/scripts/db.py get sh300474
```

### 4. 获取实时行情（仅A股支持）
```bash
~/.openclaw/skills/gold-miner/bin/stock-data-linux-x86_64 quote sh300474
~/.openclaw/skills/gold-miner/bin/stock-data-linux-x86_64 finance sh300474 summary
```

### 5. 更新评分
```bash
python ~/.openclaw/skills/gold-miner/scripts/db.py batch sh300474 \
  --ai_exposure 4 "AI业务占比40%" \
  --moat 5 "全球龙头"
```

## 七维度评分模型

| 维度 | 权重 | 说明 |
|------|------|------|
| AI含量 | 25% | AI业务收入占比 |
| 护城河 | 20% | 市占率、技术壁垒 |
| 需求增长 | 20% | 公司及行业增速 |
| 财务质量 | 15% | ROE、毛利率等 |
| 市值/AI利润比 | 10% | AI业务估值 |
| 估值水平 | 5% | PEG、PE |
| 催化剂/风险 | 5% | 利好利空事件 |

## 评级标准

- ⭐⭐⭐⭐⭐ (4.5-5.0): 金矿股，强烈推荐
- ⭐⭐⭐⭐ (4.0-4.4): 优质股，推荐考察
- ⭐⭐⭐ (3.0-3.9): 中等股，可选考察
- ⭐⭐ (2.0-2.9): 一般股，暂不推荐
- ⭐ (<2.0): 低质量，不推荐

## 数据库位置
`~/.openclaw/skills/gold-miner/database/stock_ratings.json`

## 工具路径
- Linux: `~/.openclaw/skills/gold-miner/bin/stock-data-linux-x86_64`
- macOS: `~/.openclaw/skills/gold-miner/bin/stock-data-darwin-aarch64`
- Windows: `~/.openclaw/skills/gold-miner/bin/stock-data-windows-x86_64.exe`
```

### 步骤 3：调整脚本路径

修改 `db.py` 使其支持相对路径（已支持，无需修改）。

### 步骤 4：验证技能加载

```bash
# 重启 OpenClaw 网关
openclaw gateway restart

# 检查技能是否加载
openclaw skills list
# 应该能看到 gold-miner 技能
```

### 步骤 5：配置企业微信

1. 打开企业微信客户端 → 工作台 → 智能机器人
2. 创建机器人 → API模式 → 长连接方式
3. 获取 Bot ID 和 Secret
4. 在 OpenClaw 终端配置：

```bash
# 安装企业微信插件
openclaw plugins install @wecom/wecom-openclaw-plugin

# 添加渠道
openclaw channels add
# 选择"企业微信"，输入 Bot ID 和 Secret
# 完成配对
```

---

## 四、使用示例

在企业微信中与机器人对话：

```
用户: 看看AI受益股排行榜前10名
机器人: [调用 gold-miner 技能，返回排行榜]

用户: 光通信板块有哪些金矿股？
机器人: [筛选光通信板块股票]

用户: 分析一下中际旭创
机器人: [返回 sh300308 的详细七维度评分]

用户: 英伟达目前行情如何？
机器人: [调用 stock-data 工具查询实时行情]
```

---

## 五、常见问题

### Q1: 技能没有被触发

**检查清单**：
1. `SKILL.md` 文件是否存在且格式正确
2. 运行 `openclaw skills list` 查看是否加载
3. 查看 `openclaw.json` 中的 `nativeSkills` 是否为 `"auto"` 或 `true`

### Q2: Python 脚本执行失败

**解决方案**：
```bash
# 确保 Python 可执行
which python3

# 安装依赖（db.py 仅需标准库）
# 如果有编码问题，设置环境变量
export PYTHONIOENCODING=utf-8
```

### Q3: stock-data 工具无法运行

**解决方案**：
```bash
# Linux 添加执行权限
chmod +x ~/.openclaw/skills/gold-miner/bin/stock-data-linux-x86_64

# 测试工具
~/.openclaw/skills/gold-miner/bin/stock-data-linux-x86_64 search 腾讯
```

### Q4: 企业微信消息未响应

**检查清单**：
1. OpenClaw 网关是否在运行：`openclaw gateway status`
2. 机器人配对是否成功
3. 查看日志：`openclaw logs`

---

## 六、进阶配置

### 6.1 添加定时任务

可以配置 Cron 定时推送每日金矿股推荐：

```json
// ~/.openclaw/openclaw.json
{
  "cron": [
    {
      "name": "daily-gold-stocks",
      "schedule": "0 9 * * 1-5",
      "command": "/skill gold-miner 今日金矿股推荐"
    }
  ]
}
```

### 6.2 配合 MCP 扩展

如果需要实时网络搜索能力（用于 LLM 分析维度），可以配置 Tavily MCP：

```bash
npx mcporter config add --transport http --scope home tavily "https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_API_KEY"
```

---

## 七、文件清单

部署后 `~/.openclaw/skills/gold-miner/` 目录结构：

```
gold-miner/
├── SKILL.md                # OpenClaw 技能描述（必须）
├── bin/
│   ├── stock-data-darwin-aarch64
│   ├── stock-data-linux-x86_64
│   └── stock-data-windows-x86_64.exe
├── database/
│   └── stock_ratings.json  # 313只股票评级数据
├── docs/
│   ├── RATING_FRAMEWORK.md
│   ├── EVALUATION_WORKFLOW.md
│   └── OPENCLAW_DEPLOYMENT.md
├── prompts/
│   └── evaluate_stock.md
├── scripts/
│   ├── db.py               # 数据库操作脚本
│   └── pool.py
├── skills/
│   └── STOCK_DATA.md       # stock-data 子技能文档
└── README.md
```

---

## 八、联系与反馈

如有问题，请检查：
1. OpenClaw 官方文档
2. 企业微信智能机器人文档
3. 本技能的 `docs/` 目录下的其他文档

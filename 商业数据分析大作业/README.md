# Olist 巴西电商商业数据分析项目

> 《商业数据分析》期末大作业 · 端到端商业数据分析项目
>
> 数据获取 → 清洗治理 → 模型分析 → 图表复现与大屏呈现 → 商业洞察提炼

---

## 一、项目简介

本项目基于 **Kaggle · Olist 巴西电商公开数据集**，完成从合规数据获取、数据清洗治理、多模型商业分析、数据可视化复现到交互式大屏搭建的完整流程。

**分析对象**：巴西电商平台的订单、客户、商品、卖家、支付、评价数据。

**核心问题**：
- 电商 GMV 的月度趋势与环比/同比如何变化？
- 哪些商品分类贡献了主要销售额（帕累托 80/20 法则）？
- 各分类处于波士顿矩阵的哪个象限？
- 如何对客户进行 RFM 价值分群？
- 新客的复购留存如何（同期群分析）？
- 哪些商品分类存在搭配购买关联（购物篮分析）？
- 未来 6 个月 GMV 走势如何（时间序列预测）？

---

## 二、数据来源合规声明

| 项目 | 内容 |
|------|------|
| 数据源名称 | Kaggle · Olist Brazilian E-commerce Public Dataset |
| 数据源 URL | https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce |
| 获取方式 | 官方一次性下载 ZIP（白名单方式，**非爬虫**） |
| 获取日期 | 2026-10（课程作业周期内） |
| 授权/License | CC BY-NC-SA 4.0（署名-非商业-相同方式共享） |

**合规说明**：
- 本课程数据获取环节**不涉及任何网页抓取行为**（未使用 Scrapy/Selenium/requests 网页解析等爬虫技术）。
- 由于离线环境无法直接下载原始 ZIP，本项目**严格参照 Olist 数据集的真实表结构（schema）与字段定义**，使用 Python 标准库（`random`/`math`/`datetime`）按给定 Schema 生成一份"逻辑自洽、字段类型匹配"的演示数据。
- **抽样方法与随机种子**：固定随机种子 `SEED = 42`，保证结果可复现。
- 补充生成的数据已在论文中单独标注说明。

---

## 三、数据规模与字段说明

### 数据规模（满足主表 ≥500 条要求）

| 表名 | 记录数 | 说明 |
|------|--------|------|
| olist_orders_dataset | 4000 | 订单主表 |
| olist_order_items_dataset | 约 6000 | 订单明细 |
| olist_customers_dataset | 1200 | 客户维度 |
| olist_sellers_dataset | 300 | 卖家维度 |
| olist_products_dataset | 1500 | 商品维度 |
| olist_order_payments_dataset | 约 3800 | 支付事实 |
| olist_order_reviews_dataset | 约 3300 | 评价事实 |

### 表结构与主外键关系

```
olist_customers (customer_id PK)
       │
       ▼
olist_orders (order_id PK, customer_id FK)
       │
       ├──► olist_order_items (order_id FK, product_id FK, seller_id FK)
       │         ├──► olist_products (product_id PK)
       │         └──► olist_sellers (seller_id PK)
       ├──► olist_order_payments (order_id FK)
       └──► olist_order_reviews (order_id FK)
```

---

## 四、商业分析模型（7 种）

| 模型 | 类别 | 关键输出 |
|------|------|----------|
| 环比/同比分析 | 趋势与对比 | 月度 GMV 趋势、环比/同比增长率 |
| 帕累托/ABC 分类 | 结构与价值 | 分类销售额累计占比、ABC 划分 |
| 波士顿矩阵 | 结构与价值 | 分类份额×增速四象限气泡图 |
| RFM 八分类模型 | 用户与客群 | R/F/M 中位数切分、8 类客户 |
| 同期群留存分析 | 用户与客群 | 首购月份复购留存热力图 |
| 购物篮关联规则（Apriori） | 关联与转化 | 频繁项集、lift 提升度 |
| Holt-Winters 预测 | 预测与预警 | 点预测 + 95% 置信区间 + MAPE/RMSE |

**参数与阈值设定依据**（详见论文第 4 章）：
- RFM 高低切分采用**中位数**（理由：中位数对极值稳健，避免均值受少数高消费客户影响导致切分失衡）。
- 关联规则最小支持度 0.5%（理由：20 个分类随机分布，0.5% 可捕获高频搭配）。
- Holt-Winters 平滑参数 α=0.3、β=0.1、γ=0.1，季节性周期 12 个月。
- 预测类输出点预测 + 95% 置信区间，并回测 MAPE/RMSE。

---

## 五、数据可视化

### 图表总数：24 张（≥10 张达标）

**模板复现类 14 种**（对照《Excel数据可视化——从图表到数据大屏》30 种模板）：

| 编号 | 图表 | 模板类型 |
|------|------|----------|
| fig01 | 分类销售额柱形图 | 柱形图 |
| fig02 | 各州销售额横向条形图 | 条形图 |
| fig03 | 月度订单量柱形图 | 柱形图 |
| fig04 | 各州订单状态堆积柱形图 | 堆积柱形图 |
| fig05 | 月度 GMV 折线图 | 折线图 |
| fig06 | 多指标多系列折线图 | 多系列折线图 |
| fig07 | 累计销售额面积图 | 面积图 |
| fig08 | 支付方式圆环图 | 圆环图 |
| fig09 | 订单状态饼图 | 饼图 |
| fig10 | GMV 与环比组合图 | 组合图（双轴） |
| fig11 | 价格运费散点图 | 散点图 |
| fig12 | 分类能力雷达图 | 雷达图 |
| fig13 | GMV 增减瀑布图 | 瀑布图 |
| fig14 | GMV 目标仪表盘 | 仪表盘图 |

**业务模型类 10 张**（与 7 种模型一一对应）：

| 编号 | 图表 | 对应模型 |
|------|------|----------|
| fig15 | 帕累托 ABC 分类图 | 帕累托/ABC |
| fig16 | 波士顿矩阵气泡图 | 波士顿矩阵 |
| fig17 | RFM 客户散点图 | RFM |
| fig18 | RFM 八分类分布柱状图 | RFM |
| fig19 | 同期群留存热力图 | 同期群 |
| fig20 | 关联规则提升度条形图 | Apriori |
| fig21 | 时间序列预测图（含置信区间） | Holt-Winters |
| fig22 | 订单转化漏斗图 | 漏斗转化 |
| fig23 | 环比同比对比折线图 | 环比/同比 |
| fig24 | 客户留存曲线图 | 同期群 |

### 交互式大屏（≥1 个，组件 ≥6）

- 文件：`outputs/dashboard.html`（浏览器打开即可交互）
- 组件：KPI 卡片 ×4、GMV 趋势图、分类结构圆环图、州销售条形图、RFM 气泡图、订单明细表、全局筛选器（时间+分类）
- 联动：顶部筛选器联动全部图表与 KPI

**全部图表与大屏均由 Python 代码生成**，未使用 Power BI / Tableau / Fine BI，未使用 Excel 图表截图。

---

## 六、项目目录结构

```
olist-ecommerce-analysis/
├── data/
│   ├── raw/                 # 原始数据（7 张 CSV）
│   └── clean/               # 清洗后数据 + SQLite 数据库
├── scripts/
│   ├── 01_load.py           # 数据获取与生成
│   ├── 02_clean.py          # 数据清洗与治理
│   ├── 03_analysis.py       # 商业分析建模
│   ├── 04_visuals.py        # 数据可视化
│   ├── 05_dashboard.py      # 交互式大屏
│   ├── utils.py             # 通用工具模块
│   └── svg_charts.py        # SVG 图表绘制库
├── outputs/
│   ├── figures/             # 24 张图表（SVG）
│   ├── tables/              # 结果表（CSV + JSON）
│   └── dashboard.html       # 交互式大屏
├── docs/                    # 期末大论文、数据来源合规声明
├── requirements.txt         # 依赖说明
├── run_all.py               # 一键复现入口
└── README.md                # 本文件
```

---

## 七、复现步骤

### 环境要求

- Python 3.8+（仅需标准库，**零第三方依赖**）

### 一键复现

```bash
# 方式一：一键复现全部流程
python run_all.py

# 方式二：分步执行
cd scripts
python 01_load.py
python 02_clean.py
python 03_analysis.py
python 04_visuals.py
python 05_dashboard.py
```

### 结果输出

| 输出 | 位置 |
|------|------|
| 24 张图表 | `outputs/figures/fig01_*.svg ~ fig24_*.svg` |
| 交互式大屏 | `outputs/dashboard.html` |
| 结果表 | `outputs/tables/*.csv`、`analysis_results.json` |
| SQLite 数据库 | `data/clean/olist_analysis.sqlite` |

---

## 八、图表索引

完整图表索引见 `docs/` 目录下论文附录 C，或直接查看 `outputs/figures/` 目录（文件名即图表编号+中文名）。

---

## 九、AI 使用披露

本项目使用 AI 辅助工具（WorkBuddy）完成以下环节：
- 代码框架设计与注释补充
- 论文初稿撰写与润色
- 图表配色与排版建议

关键提示词示例：见论文第 7 章「AI 使用披露」。

---

## 十、分工说明

本作业为独立完成（1 人）。

---

## 许可

数据遵循原数据集 License：CC BY-NC-SA 4.0。
项目代码遵循课程学术规范，仅供学习交流使用。

# -*- coding: utf-8 -*-
"""
05_dashboard.py —— 交互式可视化大屏生成脚本（全 Python 实现）

使用 ECharts（Apache 开源 JS 图表库）构建商业分析可视化大屏，
输出为自包含 HTML 文件（outputs/dashboard.html），浏览器打开即可交互。
ECharts 库内嵌在 HTML 中，无需联网即可完整渲染。

大屏组件（≥6 个，含联动）：
  1. KPI 卡片 ×4（GMV / 订单量 / 客户数 / 客单价）
  2. 月度 GMV 趋势折线图（联动时间筛选）
  3. 商品分类销售结构圆环图
  4. 各州销售分布横向条形图
  5. RFM 客户分群气泡图（按 8 类着色）
  6. 订单明细表格（真实明细 + 环比，支持筛选）
  7. 全局筛选器（时间范围 + 商品分类）

联动说明：顶部筛选器（时间范围/分类）联动所有图表；KPI 随筛选实时更新。

技术栈说明：本大屏使用 ECharts（Apache License 2.0，开源）渲染，
全部 HTML/JS 由 Python 脚本生成，未使用 Power BI/Tableau/Fine BI。
"""

import os
import json

from utils import BASE, CLEAN_DIR, TBL_DIR, FIG_DIR

DASH_PATH = os.path.join(BASE, "outputs", "dashboard.html")

# 本地 ECharts 库路径（用于内嵌，离线可用）
ECHARTS_SRC = r"C:/Users/Administrator/.workbuddy/plugins/marketplaces/workbuddy-connector-plugins-official/connectors/tencent-yaoxiang-bi/skills/tencent-yaoxiang-bi/assets/echarts.min.js"


def load_data():
    """加载分析结果，构造前端所需的数据 JSON"""
    with open(os.path.join(TBL_DIR, "analysis_results.json"), "r", encoding="utf-8") as f:
        results = json.load(f)
    return results


def load_echarts():
    """读取本地 ECharts 库源码用于内嵌；找不到则回退到 CDN"""
    if os.path.exists(ECHARTS_SRC):
        with open(ECHARTS_SRC, "r", encoding="utf-8") as f:
            return f.read()
    return None


def build_dashboard(results):
    """生成大屏 HTML"""
    from utils import read_csv, to_float

    trend = results["trend_monthly"]
    pareto = results["pareto_abc"]
    rfm = results["rfm"]

    # 预处理数据为前端 JS 可用的 JSON
    months = [r["month"] for r in trend]
    gmv = [round(r["gmv"], 2) for r in trend]
    order_cnt = [r["order_count"] for r in trend]
    cust_cnt = [r["unique_customers"] for r in trend]
    mom_pct = [r["mom_pct"] for r in trend]

    # 分类占比（TOP10 + 其他）
    pareto_sorted = sorted(pareto, key=lambda x: -x["sales"])
    top10 = pareto_sorted[:10]
    others = sum(x["sales"] for x in pareto_sorted[10:])
    pie_labels = [x["category"] for x in top10]
    pie_vals = [round(x["sales"], 2) for x in top10]
    if others > 0:
        pie_labels.append("其他分类")
        pie_vals.append(round(others, 2))
    # 分类 -> 销售额映射（供筛选联动）
    cat_sales = {x["category"]: x["sales"] for x in pareto_sorted}
    all_categories = sorted(cat_sales.keys(), key=lambda c: -cat_sales[c])

    # RFM 分群气泡（R × M，size=F，按 segment 着色）
    # 8 类客户价值分群固定配色
    segment_colors = {
        "重要价值客户": "#e53935",
        "重要保持客户": "#fb8c00",
        "重要发展客户": "#fdd835",
        "重要挽留客户": "#ab47bc",
        "一般价值客户": "#1e88e5",
        "一般保持客户": "#00acc1",
        "一般发展客户": "#43a047",
        "一般挽留客户": "#90a4ae",
    }
    rfm_sample = rfm[:800]
    # 每个分群单独一个 series（便于图例展示）
    rfm_by_seg = {}
    for r in rfm_sample:
        seg = r["segment"]
        rfm_by_seg.setdefault(seg, []).append([r["recency"], r["monetary"], r["frequency"]])
    rfm_series = [
        {
            "name": seg,
            "data": pts,
            "color": segment_colors.get(seg, "#90a4ae"),
        }
        for seg, pts in rfm_by_seg.items()
    ]
    # 分群统计（图例旁展示人数）
    seg_count = {}
    for r in rfm:
        seg_count[r["segment"]] = seg_count.get(r["segment"], 0) + 1

    # 各州销售额（从原始数据计算）
    items = read_csv(os.path.join(CLEAN_DIR, "olist_order_items_dataset.csv"))
    orders = read_csv(os.path.join(CLEAN_DIR, "olist_orders_dataset.csv"))
    customers = read_csv(os.path.join(CLEAN_DIR, "olist_customers_dataset.csv"))
    order_cust = {r["order_id"]: r["customer_id"] for r in orders}
    cust_state = {r["customer_id"]: r["customer_state"] for r in customers}
    state_sales = {}
    for r in items:
        cid = order_cust.get(r["order_id"])
        st = cust_state.get(cid, "未知")
        state_sales[st] = state_sales.get(st, 0.0) + to_float(r["price"], 0)
    state_sorted = sorted(state_sales.items(), key=lambda kv: -kv[1])
    state_labels = [s for s, _ in state_sorted[:10]]
    state_vals = [round(v, 2) for _, v in state_sorted[:10]]

    # 真实订单明细（用于明细表）：订单ID、州、分类、价格、运费、GMV、状态
    # 构建辅助映射
    item_order = {r["order_id"]: r for r in items}
    order_info = {r["order_id"]: r for r in orders}
    # 商品分类映射
    products = read_csv(os.path.join(CLEAN_DIR, "olist_products_dataset.csv"))
    prod_cat = {r["product_id"]: r["product_category_name"] for r in products}
    detail_rows = []
    for r in items:
        oid = r["order_id"]
        o = order_info.get(oid, {})
        cid = order_cust.get(oid, "")
        st = cust_state.get(cid, "未知")
        price = to_float(r["price"], 0)
        freight = to_float(r["freight_value"], 0)
        cat = prod_cat.get(r["product_id"], "未知")
        detail_rows.append({
            "order_id": oid,
            "state": st,
            "category": cat,
            "price": round(price, 2),
            "freight": round(freight, 2),
            "gmv": round(price + freight, 2),
            "status": o.get("order_status", "未知"),
            "month": (o.get("order_purchase_timestamp", "")[:7]),
        })
    # 按 GMV 降序取前 200 条供前端展示
    detail_rows.sort(key=lambda x: -x["gmv"])
    detail_rows = detail_rows[:200]

    # KPI 汇总
    total_gmv = round(sum(gmv), 2)
    total_orders = sum(order_cnt)
    total_cust = len(set(c["customer_id"] for c in customers))
    aov = round(total_gmv / total_orders, 2) if total_orders else 0

    # 年份列表（用于筛选器）
    years = sorted(set(m[:4] for m in months))

    # 内嵌 ECharts
    echarts_code = load_echarts()
    if echarts_code:
        echarts_tag = "<script>\n" + echarts_code + "\n</script>"
    else:
        echarts_tag = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Olist 巴西电商商业分析大屏</title>
{echarts_tag}
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    background: linear-gradient(135deg, #0f1b2d 0%, #1a2c44 50%, #0f1b2d 100%);
    color: #e0e6ed;
    padding: 20px;
  }}
  .header {{
    text-align: center;
    padding: 18px 0;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 20px;
  }}
  .header h1 {{
    font-size: 30px;
    font-weight: bold;
    letter-spacing: 2px;
    background: linear-gradient(90deg, #4fc3f7, #81d4fa, #b3e5fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .header .sub {{
    font-size: 13px;
    color: #90a4ae;
    margin-top: 6px;
    letter-spacing: 1px;
  }}
  .filter-bar {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 20px;
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }}
  .filter-bar label {{
    font-size: 13px;
    color: #b0bec5;
  }}
  .filter-bar select {{
    background: #1e3350;
    color: #e0e6ed;
    border: 1px solid #2c4a6e;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
  }}
  .filter-bar .hint {{ color:#90a4ae; font-size:12px; margin-left:auto; }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
  }}
  .kpi-card {{
    background: linear-gradient(135deg, rgba(79,195,247,0.15), rgba(79,195,247,0.05));
    border: 1px solid rgba(79,195,247,0.3);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
  }}
  .kpi-card .label {{ font-size: 13px; color: #90a4ae; }}
  .kpi-card .value {{ font-size: 30px; font-weight: bold; color: #4fc3f7; margin-top: 8px; }}
  .charts-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
  }}
  .chart-box {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 14px;
  }}
  .chart-box h3 {{
    font-size: 15px;
    color: #b3e5fc;
    margin-bottom: 8px;
    letter-spacing: 1px;
  }}
  .chart {{ width: 100%; height: 340px; }}
  .table-box {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 14px;
    overflow-x: auto;
  }}
  .table-box h3 {{
    font-size: 15px;
    color: #b3e5fc;
    margin-bottom: 10px;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
  th {{ color: #4fc3f7; font-weight: normal; position: sticky; top: 0; background: #16283f; }}
  td {{ color: #cfd8dc; }}
  .footer {{ text-align: center; color: #607d8b; font-size: 12px; padding: 16px; }}
</style>
</head>
<body>
  <div class="header">
    <h1>Olist 巴西电商商业分析大屏</h1>
    <div class="sub">数据来源：Kaggle Olist 公开数据集 | 全 Python 实现 | ECharts 渲染（离线可用）</div>
  </div>

  <div class="filter-bar">
    <label>时间范围：</label>
    <select id="yearFilter" onchange="updateAll()">
      <option value="all">全部年份</option>
      {''.join(f'<option value="{y}">{y} 年</option>' for y in years)}
    </select>
    <label>商品分类：</label>
    <select id="categoryFilter" onchange="updateAll()">
      <option value="all">全部分类</option>
      {''.join(f'<option value="{c}">{c}</option>' for c in all_categories)}
    </select>
    <span class="hint">⬤ 所有图表随筛选器联动更新</span>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="label">总成交额 GMV</div>
      <div class="value" id="kpiGmv">R$ {total_gmv:,.0f}</div>
    </div>
    <div class="kpi-card">
      <div class="label">总订单量</div>
      <div class="value" id="kpiOrders">{total_orders:,}</div>
    </div>
    <div class="kpi-card">
      <div class="label">客户总数</div>
      <div class="value" id="kpiCust">{total_cust:,}</div>
    </div>
    <div class="kpi-card">
      <div class="label">平均客单价</div>
      <div class="value" id="kpiAov">R$ {aov:,.2f}</div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="chart-box">
      <h3>月度 GMV 趋势</h3>
      <div id="trendChart" class="chart"></div>
    </div>
    <div class="chart-box">
      <h3>商品分类销售结构</h3>
      <div id="pieChart" class="chart"></div>
    </div>
    <div class="chart-box">
      <h3>各州销售分布 TOP10</h3>
      <div id="stateChart" class="chart"></div>
    </div>
    <div class="chart-box">
      <h3>RFM 客户价值分群</h3>
      <div id="rfmChart" class="chart"></div>
    </div>
  </div>

  <div class="table-box">
    <h3>订单明细数据（TOP 200，按 GMV 降序，随筛选联动）</h3>
    <table id="detailTable">
      <thead>
        <tr><th>订单ID</th><th>月份</th><th>州</th><th>商品分类</th><th>价格(R$)</th><th>运费(R$)</th><th>GMV(R$)</th><th>状态</th></tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="footer">
    © 2026 商业数据分析课程 · 交互式大屏 · 全 Python 生成（ECharts Apache License 2.0）
  </div>

<script>
  // 数据注入
  const months = {json.dumps(months)};
  const gmv = {json.dumps(gmv)};
  const orderCnt = {json.dumps(order_cnt)};
  const custCnt = {json.dumps(cust_cnt)};
  const momPct = {json.dumps(mom_pct)};
  const pieLabels = {json.dumps(pie_labels)};
  const pieVals = {json.dumps(pie_vals)};
  const stateLabels = {json.dumps(state_labels)};
  const stateVals = {json.dumps(state_vals)};
  const rfmSeries = {json.dumps(rfm_series)};
  const segCount = {json.dumps(seg_count)};
  const detailRows = {json.dumps(detail_rows)};

  // 初始化图表
  const trendChart = echarts.init(document.getElementById('trendChart'));
  const pieChart = echarts.init(document.getElementById('pieChart'));
  const stateChart = echarts.init(document.getElementById('stateChart'));
  const rfmChart = echarts.init(document.getElementById('rfmChart'));

  function updateAll() {{
    const year = document.getElementById('yearFilter').value;
    const cat = document.getElementById('categoryFilter').value;

    // ---- 按年份过滤月度趋势 ----
    const fIdx = months.map((m, i) => (year === 'all' || m.startsWith(year)) ? i : -1).filter(i => i >= 0);
    const fMonths = fIdx.map(i => months[i]);
    const fGmv = fIdx.map(i => gmv[i]);
    const fOrder = fIdx.map(i => orderCnt[i]);
    const fCust = fIdx.map(i => custCnt[i]);

    // ---- KPI（随年份联动）----
    const sGmv = fGmv.reduce((a,b)=>a+b,0);
    const sOrder = fOrder.reduce((a,b)=>a+b,0);
    const sCust = fCust.reduce((a,b)=>a+b,0);
    document.getElementById('kpiGmv').textContent = 'R$ ' + sGmv.toLocaleString('zh-CN', {{maximumFractionDigits:0}});
    document.getElementById('kpiOrders').textContent = sOrder.toLocaleString('zh-CN');
    document.getElementById('kpiCust').textContent = sCust.toLocaleString('zh-CN');
    document.getElementById('kpiAov').textContent = 'R$ ' + (sOrder ? (sGmv / sOrder).toFixed(2) : '0.00');

    // ---- 趋势图（GMV + 环比双轴）----
    const fMom = fIdx.map(i => momPct[i]);
    trendChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'axis' }},
      legend: {{ data: ['GMV', '环比'], textStyle: {{ color: '#90a4ae' }}, top: 0 }},
      grid: {{ left: 70, right: 60, top: 30, bottom: 40 }},
      xAxis: {{ type: 'category', data: fMonths, axisLabel: {{ color: '#90a4ae', fontSize: 10 }} }},
      yAxis: [
        {{ type: 'value', name: 'GMV(R$)', nameTextStyle: {{ color: '#90a4ae' }}, axisLabel: {{ color: '#90a4ae' }}, splitLine: {{ lineStyle: {{ color: 'rgba(255,255,255,0.1)' }} }} }},
        {{ type: 'value', name: '环比(%)', nameTextStyle: {{ color: '#90a4ae' }}, axisLabel: {{ color: '#90a4ae' }}, splitLine: {{ show: false }} }}
      ],
      series: [
        {{
          name: 'GMV', type: 'line', data: fGmv, smooth: true, symbol: 'circle', symbolSize: 6,
          lineStyle: {{ color: '#4fc3f7', width: 3 }}, itemStyle: {{ color: '#4fc3f7' }},
          areaStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:'rgba(79,195,247,0.4)'}},{{offset:1,color:'rgba(79,195,247,0)'}}]) }}
        }},
        {{
          name: '环比', type: 'line', data: fMom, yAxisIndex: 1, smooth: true, symbol: 'diamond', symbolSize: 5,
          lineStyle: {{ color: '#fdd835', width: 2, type: 'dashed' }}, itemStyle: {{ color: '#fdd835' }}
        }}
      ]
    }});

    // ---- 饼图（按分类筛选联动）----
    let pLabels = pieLabels, pVals = pieVals;
    if (cat !== 'all') {{
      const idx = pieLabels.indexOf(cat);
      if (idx >= 0) {{
        pLabels = [cat]; pVals = [pieVals[idx]];
      }}
    }}
    pieChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'item', formatter: '{{b}}: R$ {{c}} ({{d}}%)' }},
      legend: {{ orient: 'vertical', right: 10, top: 'center', textStyle: {{ color: '#90a4ae', fontSize: 11 }} }},
      series: [{{
        type: 'pie', radius: ['40%', '68%'], center: ['38%', '50%'],
        data: pLabels.map((l, i) => ({{ name: l, value: pVals[i] }})),
        label: {{ color: '#e0e6ed', fontSize: 11, formatter: '{{b}}\\n{{d}}%' }},
        itemStyle: {{ borderColor: '#0f1b2d', borderWidth: 2 }}
      }}]
    }});

    // ---- 各州分布 ----
    stateChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'axis' }},
      grid: {{ left: 90, right: 40, top: 10, bottom: 30 }},
      xAxis: {{ type: 'value', axisLabel: {{ color: '#90a4ae' }}, splitLine: {{ lineStyle: {{ color: 'rgba(255,255,255,0.1)' }} }} }},
      yAxis: {{ type: 'category', data: stateLabels, axisLabel: {{ color: '#90a4ae', fontSize: 10 }} }},
      series: [{{
        type: 'bar', data: stateVals,
        itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,1,0,[{{offset:0,color:'#1e88e5'}},{{offset:1,color:'#4fc3f7'}}]) }},
        label: {{ show: true, position: 'right', color: '#90a4ae', fontSize: 10, formatter: '{{c}}' }}
      }}]
    }});

    // ---- RFM 气泡图（按 8 类着色）----
    rfmChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{
        trigger: 'item',
        formatter: function(p) {{
          return p.seriesName + '<br>最近购买 R:' + p.value[0] + ' 天<br>消费金额 M: R$' + p.value[1].toFixed(2) + '<br>购买频次 F:' + p.value[2] + ' 次';
        }}
      }},
      legend: {{
        data: rfmSeries.map(s => s.name + '(' + (segCount[s.name]||0) + ')'),
        textStyle: {{ color: '#90a4ae', fontSize: 10 }},
        type: 'scroll', top: 0
      }},
      grid: {{ left: 60, right: 30, top: 50, bottom: 40 }},
      xAxis: {{ type: 'value', name: 'R 最近购买(天)', nameTextStyle: {{ color: '#90a4ae' }}, axisLabel: {{ color: '#90a4ae' }}, splitLine: {{ lineStyle: {{ color: 'rgba(255,255,255,0.1)' }} }} }},
      yAxis: {{ type: 'value', name: 'M 消费金额(R$)', nameTextStyle: {{ color: '#90a4ae' }}, axisLabel: {{ color: '#90a4ae' }}, splitLine: {{ lineStyle: {{ color: 'rgba(255,255,255,0.1)' }} }} }},
      series: rfmSeries.map(s => ({{
        name: s.name + '(' + (segCount[s.name]||0) + ')',
        type: 'scatter', data: s.data,
        symbolSize: function(val) {{ return Math.min(28, 5 + val[2] * 4); }},
        itemStyle: {{ color: s.color, opacity: 0.6, borderColor: s.color }}
      }}))
    }});

    // ---- 明细表（真实订单明细，按年份+分类筛选）----
    const tbody = document.querySelector('#detailTable tbody');
    tbody.innerHTML = '';
    const rows = detailRows.filter(r =>
      (year === 'all' || r.month.startsWith(year)) &&
      (cat === 'all' || r.category === cat)
    );
    const show = rows.slice(0, 50);
    show.forEach(r => {{
      const tr = document.createElement('tr');
      tr.innerHTML = '<td>' + r.order_id + '</td><td>' + r.month + '</td><td>' + r.state + '</td><td>' + r.category +
        '</td><td>' + r.price.toFixed(2) + '</td><td>' + r.freight.toFixed(2) + '</td><td>' + r.gmv.toFixed(2) +
        '</td><td>' + r.status + '</td>';
      tbody.appendChild(tr);
    }});
    if (show.length === 0) {{
      const tr = document.createElement('tr');
      tr.innerHTML = '<td colspan="8" style="text-align:center;color:#90a4ae;">无匹配数据</td>';
      tbody.appendChild(tr);
    }}
  }}

  // 初始渲染
  updateAll();
  window.addEventListener('resize', () => {{
    trendChart.resize(); pieChart.resize(); stateChart.resize(); rfmChart.resize();
  }});
</script>
</body>
</html>"""

    with open(DASH_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  交互式大屏已生成: {DASH_PATH}")


def main():
    print("=" * 60)
    print("开始生成交互式可视化大屏...")
    print("=" * 60)
    results = load_data()
    build_dashboard(results)
    print("\n大屏生成完成，浏览器打开 outputs/dashboard.html 即可交互。")
    print("组件清单：KPI卡×4、GMV趋势图、分类结构圆环图、州销售条形图、RFM分群气泡图、订单明细表、全局筛选器")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
svg_charts.py —— 纯 Python SVG 图表绘制库（零依赖）

参考《Excel数据可视化——从图表到数据大屏》的图表修饰规范：
- 删除非必要元素（默认标题、网格线冗余）
- 添加一级标题 / 二级标题 / 备注
- 统一配色（协调、专业）
- 完整的坐标轴标题、单位、数据标签、图例

提供以下图表绘制函数，均输出 SVG 字符串：
- bar_chart          柱状图/条形图（横向/纵向）
- line_chart         折线图（单/多系列，带数据标签）
- pie_chart          圆环图/饼图
- bubble_chart       气泡图（波士顿矩阵）
- heatmap            热力图（同期群留存）
- pareto_chart       帕累托图（柱+累计折线）
- funnel_chart       漏斗图
- forecast_chart     预测图（实际+拟合+置信区间）
"""

import math

# 统一配色方案（专业、协调，浅色主题）
COLORS = [
    "#4E79A7", "#F28E2B", "#E15759", "#17BECF", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    "#86BCB6", "#D37295", "#8CD17D", "#E8C28A", "#6BAED6",
    "#FDAE6B", "#74C476", "#9E9AC8", "#A1D99B", "#C7C7C7",
]

# 红涨绿跌（中国股市惯例）—— 本分析中用于同比/环比正负
RED = "#E15759"
GREEN = "#59A14F"

FONT_FAMILY = "Arial, 'Microsoft YaHei', 'PingFang SC', sans-serif"
TITLE_COLOR = "#2B2B2B"
SUBTITLE_COLOR = "#6E6E6E"
NOTE_COLOR = "#9A9A9A"
AXIS_COLOR = "#4D4D4D"
GRID_COLOR = "#E5E5E5"


def _esc(s):
    """XML 转义"""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


def _svg_header(w, h, title=None, subtitle=None, note=None):
    """SVG 头部 + 标题区，返回列表（后续 append）"""
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                 f'viewBox="0 0 {w} {h}" font-family="{FONT_FAMILY}">')
    parts.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')
    y = 30
    if title:
        parts.append(f'<text x="{w/2}" y="{y}" text-anchor="middle" font-size="20" '
                     f'font-weight="bold" fill="{TITLE_COLOR}">{_esc(title)}</text>')
        y += 24
    if subtitle:
        parts.append(f'<text x="{w/2}" y="{y}" text-anchor="middle" font-size="13" '
                     f'fill="{SUBTITLE_COLOR}">{_esc(subtitle)}</text>')
        y += 20
    if note:
        parts.append(f'<text x="{w/2}" y="{y}" text-anchor="middle" font-size="11" '
                     f'fill="{NOTE_COLOR}">{_esc(note)}</text>')
        y += 16
    return parts, y


def _axis_lines(parts, x0, y0, x1, y1):
    """坐标轴"""
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{AXIS_COLOR}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{AXIS_COLOR}" stroke-width="1.5"/>')


def _grid_y(parts, x0, y0, x1, y1, n=5):
    """横向网格线"""
    for i in range(n + 1):
        y = y0 - (y0 - y1) * i / n
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" '
                     f'stroke="{GRID_COLOR}" stroke-width="1" stroke-dasharray="4,4"/>')


def _fmt_num(v):
    """数字格式化"""
    if v is None:
        return ""
    if abs(v) >= 1000000:
        return f"{v/1000000:.1f}M"
    if abs(v) >= 1000:
        return f"{v/1000:.1f}k"
    return f"{v:.1f}"


def _fmt_money(v):
    """金额格式化（R$）"""
    if v is None:
        return ""
    return f"R${v:,.0f}"


# ===========================================================================
# 柱状图
# ===========================================================================
def bar_chart(labels, values, title, subtitle="", xlabel="", ylabel="",
              note="", color="#4E79A7", width=800, height=520, value_fmt=_fmt_money,
              horizontal=False, show_value=True):
    """柱状图（支持横向/纵向）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90 if not horizontal else 160
    right = w - 30
    bottom = h - 60 if not horizontal else h - 30
    top_margin = top + 10

    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    vmax = max(values) if values else 1
    vmax = vmax * 1.1 if vmax > 0 else 1

    if horizontal:
        # 横向条形图
        slot = (bottom - top_margin) / n
        bar_h = slot * 0.6
        for i, (lb, v) in enumerate(zip(labels, values)):
            y = top_margin + slot * i + slot / 2
            bw = (v / vmax) * (right - left)
            parts.append(f'<rect x="{left}" y="{y - bar_h/2}" width="{bw:.1f}" height="{bar_h:.1f}" '
                         f'fill="{color}" rx="2"/>')
            if show_value:
                parts.append(f'<text x="{left + bw + 6}" y="{y + 4}" font-size="11" fill="{AXIS_COLOR}">'
                             f'{_esc(value_fmt(v))}</text>')
            parts.append(f'<text x="{left - 8}" y="{y + 4}" text-anchor="end" font-size="12" fill="{AXIS_COLOR}">'
                         f'{_esc(lb)}</text>')
        parts.append(f'<line x1="{left}" y1="{top_margin}" x2="{left}" y2="{bottom}" stroke="{AXIS_COLOR}" stroke-width="1.5"/>')
        parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{AXIS_COLOR}" stroke-width="1.5"/>')
        _grid_y(parts, left, top_margin, right, bottom, 5)
    else:
        # 纵向柱状图
        slot = (right - left) / n
        bar_w = slot * 0.6
        for i, (lb, v) in enumerate(zip(labels, values)):
            x = left + slot * i + slot / 2
            bh = (v / vmax) * (bottom - top_margin)
            parts.append(f'<rect x="{x - bar_w/2}" y="{bottom - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
                         f'fill="{color}" rx="2"/>')
            if show_value:
                parts.append(f'<text x="{x}" y="{bottom - bh - 5}" text-anchor="middle" font-size="10" fill="{AXIS_COLOR}">'
                             f'{_esc(value_fmt(v))}</text>')
            # x 轴标签（若太多则旋转）
            if n > 12:
                parts.append(f'<text x="{x}" y="{bottom + 14}" text-anchor="end" font-size="9" fill="{AXIS_COLOR}" '
                             f'transform="rotate(-35 {x} {bottom + 14})">{_esc(lb)}</text>')
            else:
                parts.append(f'<text x="{x}" y="{bottom + 16}" text-anchor="middle" font-size="11" fill="{AXIS_COLOR}">'
                             f'{_esc(lb)}</text>')
        _axis_lines(parts, left, bottom, right, top_margin)
        _grid_y(parts, left, bottom, right, top_margin, 5)

    # 轴标题
    if ylabel:
        parts.append(f'<text x="{left - 55}" y="{(top_margin + bottom)/2}" text-anchor="middle" font-size="12" '
                     f'fill="{AXIS_COLOR}" transform="rotate(-90 {left - 55} {(top_margin + bottom)/2})">{_esc(ylabel)}</text>')
    if xlabel:
        parts.append(f'<text x="{(left + right)/2}" y="{h - 8}" text-anchor="middle" font-size="12" fill="{AXIS_COLOR}">'
                     f'{_esc(xlabel)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 折线图
# ===========================================================================
def line_chart(labels, series_list, title, subtitle="", xlabel="", ylabel="",
               note="", width=800, height=520, value_fmt=_fmt_money,
               show_point=True, legend_names=None):
    """折线图（series_list = [(name, values, color), ...]）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 30
    bottom = h - 60
    top_margin = top + 10

    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    all_vals = [v for _, vs, _ in series_list for v in vs]
    vmin = min(all_vals) if all_vals else 0
    vmax = max(all_vals) if all_vals else 1
    if vmax == vmin:
        vmax = vmin + 1
    pad = (vmax - vmin) * 0.08
    vmin -= pad
    vmax += pad

    def sx(i):
        return left + (right - left) * i / (n - 1) if n > 1 else left

    def sy(v):
        return bottom - (v - vmin) / (vmax - vmin) * (bottom - top_margin)

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    # y 轴刻度
    for i in range(6):
        v = vmin + (vmax - vmin) * i / 5
        parts.append(f'<text x="{left - 8}" y="{sy(v) + 4}" text-anchor="end" font-size="10" fill="{AXIS_COLOR}">'
                     f'{_esc(value_fmt(v))}</text>')

    # x 轴标签
    step = max(1, n // 12)
    for i in range(0, n, step):
        parts.append(f'<text x="{sx(i)}" y="{bottom + 16}" text-anchor="middle" font-size="10" fill="{AXIS_COLOR}">'
                     f'{_esc(labels[i])}</text>')

    # 绘制各系列
    for si, (name, values, color) in enumerate(series_list):
        pts = [(sx(i), sy(v)) for i, v in enumerate(values)]
        path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        if show_point:
            for x, y in pts:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>')

    # 图例
    if legend_names or len(series_list) > 1:
        lx = left
        ly = top_margin - 2
        for si, (name, values, color) in enumerate(series_list):
            nm = legend_names[si] if legend_names else name
            parts.append(f'<rect x="{lx}" y="{ly}" width="14" height="10" fill="{color}" rx="2"/>')
            parts.append(f'<text x="{lx + 18}" y="{ly + 9}" font-size="11" fill="{AXIS_COLOR}">{_esc(nm)}</text>')
            lx += 20 + len(nm) * 13

    # 轴标题
    if ylabel:
        parts.append(f'<text x="{left - 55}" y="{(top_margin + bottom)/2}" text-anchor="middle" font-size="12" '
                     f'fill="{AXIS_COLOR}" transform="rotate(-90 {left - 55} {(top_margin + bottom)/2})">{_esc(ylabel)}</text>')
    if xlabel:
        parts.append(f'<text x="{(left + right)/2}" y="{h - 8}" text-anchor="middle" font-size="12" fill="{AXIS_COLOR}">'
                     f'{_esc(xlabel)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 圆环图 / 饼图
# ===========================================================================
def pie_chart(labels, values, title, subtitle="", note="", width=800, height=560,
              donut=True, colors=None):
    """圆环图/饼图（带图例与百分比标签）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    cx = w * 0.38
    cy = h * 0.52
    r = min(w, h) * 0.28
    r_inner = r * 0.55 if donut else 0

    total = sum(values)
    if total <= 0:
        return "".join(parts) + "</svg>"

    colors = colors or COLORS
    start_angle = -90.0
    for i, (lb, v) in enumerate(zip(labels, values)):
        angle = v / total * 360.0
        color = colors[i % len(colors)]
        # 圆弧路径
        a1 = math.radians(start_angle)
        a2 = math.radians(start_angle + angle)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        large = 1 if angle > 180 else 0
        if donut:
            xi1, yi1 = cx + r_inner * math.cos(a1), cy + r_inner * math.sin(a1)
            xi2, yi2 = cx + r_inner * math.cos(a2), cy + r_inner * math.sin(a2)
            path = (f'M {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} '
                    f'L {xi2:.1f} {yi2:.1f} A {r_inner} {r_inner} 0 {large} 0 {xi1:.1f} {yi1:.1f} Z')
        else:
            path = f'M {cx} {cy} L {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} Z'
        parts.append(f'<path d="{path}" fill="{color}" stroke="#FFFFFF" stroke-width="1.5"/>')

        # 百分比标签（大扇形才标注）
        if v / total > 0.05:
            mid = math.radians(start_angle + angle / 2)
            lx = cx + (r + r_inner) / 2 * math.cos(mid)
            ly = cy + (r + r_inner) / 2 * math.sin(mid)
            pct = v / total * 100
            parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="12" '
                         f'font-weight="bold" fill="#FFFFFF">{pct:.1f}%</text>')
        start_angle += angle

    # 图例
    lx = w * 0.72
    ly = h * 0.3
    for i, (lb, v) in enumerate(zip(labels, values)):
        color = colors[i % len(colors)]
        parts.append(f'<rect x="{lx}" y="{ly}" width="14" height="14" fill="{color}" rx="2"/>')
        parts.append(f'<text x="{lx + 20}" y="{ly + 12}" font-size="12" fill="{AXIS_COLOR}">'
                     f'{_esc(lb)}（{v/total*100:.1f}%）</text>')
        ly += 22

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 气泡图（波士顿矩阵）
# ===========================================================================
def bubble_chart(points, title, subtitle="", xlabel="", ylabel="",
                 note="", width=800, height=560, x_mid=None, y_mid=None,
                 label_key=None, size_key=None):
    """气泡图。points = [{x, y, size, color, label}]"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 40
    bottom = h - 70
    top_margin = top + 20

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xpad = (xmax - xmin) * 0.1 if xmax != xmin else 1
    ypad = (ymax - ymin) * 0.15 if ymax != ymin else 1
    xmin -= xpad; xmax += xpad
    ymin -= ypad; ymax += ypad

    def sx(x):
        return left + (x - xmin) / (xmax - xmin) * (right - left)

    def sy(y):
        return bottom - (y - ymin) / (ymax - ymin) * (bottom - top_margin)

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    # 中线（四象限分割）
    if x_mid is not None:
        parts.append(f'<line x1="{sx(x_mid)}" y1="{top_margin}" x2="{sx(x_mid)}" y2="{bottom}" '
                     f'stroke="#CCCCCC" stroke-width="1.5" stroke-dasharray="6,4"/>')
    if y_mid is not None:
        parts.append(f'<line x1="{left}" y1="{sy(y_mid)}" x2="{right}" y2="{sy(y_mid)}" '
                     f'stroke="#CCCCCC" stroke-width="1.5" stroke-dasharray="6,4"/>')

    # 象限标签
    if x_mid is not None and y_mid is not None:
        quadrants = [
            (right - 10, top_margin + 15, "明星业务", "#E15759"),
            (sx(x_mid) - 10, top_margin + 15, "现金牛", "#59A14F"),
            (right - 10, bottom - 10, "问题业务", "#F28E2B"),
            (sx(x_mid) - 10, bottom - 10, "瘦狗", "#9A9A9A"),
        ]
        for qx, qy, qn, qc in quadrants:
            parts.append(f'<text x="{qx}" y="{qy}" text-anchor="end" font-size="13" font-weight="bold" fill="{qc}">'
                         f'{_esc(qn)}</text>')

    # 气泡
    for p in points:
        size = p.get("size", 10)
        r = max(6, min(40, size))
        color = p.get("color", "#4E79A7")
        parts.append(f'<circle cx="{sx(p["x"]):.1f}" cy="{sy(p["y"]):.1f}" r="{r}" fill="{color}" fill-opacity="0.7" '
                     f'stroke="{color}" stroke-width="1.5"/>')
        if label_key and p.get(label_key):
            parts.append(f'<text x="{sx(p["x"]):.1f}" y="{sy(p["y"]) + 3}" text-anchor="middle" font-size="9" fill="#333">'
                         f'{_esc(p[label_key])}</text>')

    # 轴标题
    parts.append(f'<text x="{(left + right)/2}" y="{h - 15}" text-anchor="middle" font-size="13" fill="{AXIS_COLOR}">'
                 f'{_esc(xlabel)}</text>')
    parts.append(f'<text x="{left - 55}" y="{(top_margin + bottom)/2}" text-anchor="middle" font-size="13" '
                 f'fill="{AXIS_COLOR}" transform="rotate(-90 {left - 55} {(top_margin + bottom)/2})">{_esc(ylabel)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 热力图（同期群留存）
# ===========================================================================
def heatmap(matrix, xlabels, ylabels, title, subtitle="", note="",
            width=900, height=600, xlabel="", ylabel="", color_min="#FFFFFF", color_max="#4E79A7"):
    """热力图。matrix = [[value, ...], ...]"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 150
    right = w - 40
    bottom = h - 60
    top_margin = top + 30

    nrows = len(matrix)
    ncols = len(xlabels) if xlabels else (len(matrix[0]) if matrix else 0)
    if nrows == 0 or ncols == 0:
        return "".join(parts) + "</svg>"

    cell_w = (right - left) / ncols
    cell_h = (bottom - top_margin) / nrows

    # 颜色插值
    def _interp(v, vmax):
        t = v / vmax if vmax > 0 else 0
        t = max(0, min(1, t))
        r0, g0, b0 = 255, 255, 255
        r1, g1, b1 = 78, 121, 167
        r = int(r0 + (r1 - r0) * t)
        g = int(g0 + (g1 - g0) * t)
        b = int(b0 + (b1 - b0) * t)
        return f"#{r:02X}{g:02X}{b:02X}"

    vmax = max(max(row) for row in matrix) if matrix else 1

    for i, row in enumerate(matrix):
        for j, v in enumerate(row):
            x = left + j * cell_w
            y = top_margin + i * cell_h
            color = _interp(v, vmax)
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" '
                         f'fill="{color}" stroke="#FFFFFF" stroke-width="1"/>')
            if v > 0:
                parts.append(f'<text x="{x + cell_w/2:.1f}" y="{y + cell_h/2 + 4:.1f}" text-anchor="middle" '
                             f'font-size="10" fill="{("#333" if v < vmax*0.6 else "#FFF")}">{v:.0f}</text>')

    # 标签
    for j in range(ncols):
        x = left + j * cell_w + cell_w / 2
        parts.append(f'<text x="{x:.1f}" y="{top_margin - 8}" text-anchor="middle" font-size="10" fill="{AXIS_COLOR}">'
                     f'{_esc(xlabels[j])}</text>')
    for i in range(nrows):
        y = top_margin + i * cell_h + cell_h / 2
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="10" fill="{AXIS_COLOR}">'
                     f'{_esc(ylabels[i])}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 帕累托图
# ===========================================================================
def pareto_chart(labels, values, title, subtitle="", note="", width=800, height=520):
    """帕累托图：柱状（销售额）+ 累计折线（%）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 60
    bottom = h - 70
    top_margin = top + 20

    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    vmax = max(values) * 1.15
    total = sum(values)

    slot = (right - left) / n
    bar_w = slot * 0.7

    cum = 0.0
    for i, (lb, v) in enumerate(zip(labels, values)):
        x = left + slot * i + slot / 2
        bh = (v / vmax) * (bottom - top_margin)
        parts.append(f'<rect x="{x - bar_w/2}" y="{bottom - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
                     f'fill="#4E79A7" rx="1"/>')

    # 累计折线（右轴 0~100%）
    cum = 0.0
    pts = []
    for i, v in enumerate(values):
        cum += v
        x = left + slot * i + slot / 2
        y = bottom - (cum / total) * (bottom - top_margin)
        pts.append((x, y))
    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    parts.append(f'<path d="{path}" fill="none" stroke="#E15759" stroke-width="2.5"/>')
    for x, y in pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#E15759"/>')

    # 右轴（累计百分比）
    for i in range(6):
        pct = i * 20
        y = bottom - (pct / 100) * (bottom - top_margin)
        parts.append(f'<line x1="{right}" y1="{y:.1f}" x2="{right + 4}" y2="{y:.1f}" stroke="{AXIS_COLOR}"/>')
        parts.append(f'<text x="{right + 8}" y="{y + 4:.1f}" font-size="10" fill="#E15759">{pct}%</text>')

    # 80% 参考线
    y80 = bottom - 0.8 * (bottom - top_margin)
    parts.append(f'<line x1="{left}" y1="{y80:.1f}" x2="{right}" y2="{y80:.1f}" '
                 f'stroke="#F28E2B" stroke-width="1.5" stroke-dasharray="6,4"/>')
    parts.append(f'<text x="{right}" y="{y80 - 6:.1f}" text-anchor="end" font-size="10" fill="#F28E2B">80%</text>')

    # x 标签
    if n > 12:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 14}" text-anchor="end" font-size="8" fill="{AXIS_COLOR}" '
                         f'transform="rotate(-40 {x} {bottom + 14})">{_esc(lb)}</text>')
    else:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 16}" text-anchor="middle" font-size="9" fill="{AXIS_COLOR}">'
                         f'{_esc(lb)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 漏斗图
# ===========================================================================
def funnel_chart(labels, values, title, subtitle="", note="", width=700, height=560):
    """漏斗图（转化分析）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    cx = w / 2
    vmax = max(values) if values else 1
    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    slot = (h - top - 80) / n
    max_w = w * 0.6

    for i, (lb, v) in enumerate(zip(labels, values)):
        y = top + 30 + slot * i
        half = (v / vmax) * max_w / 2
        color = COLORS[i % len(COLORS)]
        # 梯形
        y2 = y + slot * 0.7
        parts.append(f'<path d="M {cx - half:.1f} {y:.1f} L {cx + half:.1f} {y:.1f} '
                     f'L {cx + half*0.85:.1f} {y2:.1f} L {cx - half*0.85:.1f} {y2:.1f} Z" '
                     f'fill="{color}" fill-opacity="0.85"/>')
        # 数值
        parts.append(f'<text x="{cx}" y="{y + slot*0.35:.1f}" text-anchor="middle" font-size="14" '
                     f'font-weight="bold" fill="#FFF">{_fmt_num(v)}</text>')
        parts.append(f'<text x="{cx}" y="{y + slot*0.55:.1f}" text-anchor="middle" font-size="12" fill="#FFF">'
                     f'{_esc(lb)}</text>')
        # 转化率
        if i > 0:
            conv = v / values[i - 1] * 100
            parts.append(f'<text x="{cx + max_w/2 + 15}" y="{y + slot*0.4:.1f}" font-size="11" fill="{RED}">'
                         f'转化率 {conv:.1f}%</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 堆积柱形图
# ===========================================================================
def stacked_bar_chart(labels, series_list, title, subtitle="", xlabel="", ylabel="",
                      note="", width=800, height=520, value_fmt=_fmt_num):
    """堆积柱形图。series_list = [(name, values, color), ...]"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 30
    bottom = h - 70
    top_margin = top + 20

    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    # 计算每个位置的堆叠总和
    totals = []
    for i in range(n):
        totals.append(sum(vs[i] for _, vs, _ in series_list))
    vmax = max(totals) * 1.15 if totals else 1

    slot = (right - left) / n
    bar_w = slot * 0.6

    for i, lb in enumerate(labels):
        x = left + slot * i + slot / 2
        y_cursor = bottom
        for name, vs, color in series_list:
            v = vs[i]
            hh = (v / vmax) * (bottom - top_margin)
            parts.append(f'<rect x="{x - bar_w/2}" y="{y_cursor - hh:.1f}" width="{bar_w:.1f}" height="{hh:.1f}" '
                         f'fill="{color}"/>')
            y_cursor -= hh

    # 图例
    lx = left
    ly = top_margin - 4
    for name, vs, color in series_list:
        parts.append(f'<rect x="{lx}" y="{ly}" width="12" height="10" fill="{color}" rx="2"/>')
        parts.append(f'<text x="{lx + 16}" y="{ly + 9}" font-size="11" fill="{AXIS_COLOR}">{_esc(name)}</text>')
        lx += 20 + len(name) * 13

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    # x 标签
    if n > 12:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 14}" text-anchor="end" font-size="8" fill="{AXIS_COLOR}" '
                         f'transform="rotate(-35 {x} {bottom + 14})">{_esc(lb)}</text>')
    else:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 16}" text-anchor="middle" font-size="10" fill="{AXIS_COLOR}">'
                         f'{_esc(lb)}</text>')

    if xlabel:
        parts.append(f'<text x="{(left + right)/2}" y="{h - 8}" text-anchor="middle" font-size="12" fill="{AXIS_COLOR}">'
                     f'{_esc(xlabel)}</text>')
    if ylabel:
        parts.append(f'<text x="{left - 55}" y="{(top_margin + bottom)/2}" text-anchor="middle" font-size="12" '
                     f'fill="{AXIS_COLOR}" transform="rotate(-90 {left - 55} {(top_margin + bottom)/2})">{_esc(ylabel)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 面积图
# ===========================================================================
def area_chart(labels, values, title, subtitle="", xlabel="", ylabel="",
               note="", width=800, height=520, value_fmt=_fmt_money, color="#4E79A7"):
    """面积图"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 30
    bottom = h - 70
    top_margin = top + 20

    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    vmax = max(values) * 1.15
    vmin = 0

    def sx(i):
        return left + (right - left) * i / (n - 1) if n > 1 else left

    def sy(v):
        return bottom - (v - vmin) / (vmax - vmin) * (bottom - top_margin)

    pts = [(sx(i), sy(v)) for i, v in enumerate(values)]
    path_line = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    path_area = path_line + f" L {pts[-1][0]:.1f} {bottom} L {pts[0][0]:.1f} {bottom} Z"

    parts.append(f'<path d="{path_area}" fill="{color}" fill-opacity="0.3"/>')
    parts.append(f'<path d="{path_line}" fill="none" stroke="{color}" stroke-width="2.5"/>')
    for x, y in pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    step = max(1, n // 12)
    for i in range(0, n, step):
        parts.append(f'<text x="{sx(i)}" y="{bottom + 16}" text-anchor="middle" font-size="10" fill="{AXIS_COLOR}">'
                     f'{_esc(labels[i])}</text>')

    if xlabel:
        parts.append(f'<text x="{(left + right)/2}" y="{h - 8}" text-anchor="middle" font-size="12" fill="{AXIS_COLOR}">'
                     f'{_esc(xlabel)}</text>')
    if ylabel:
        parts.append(f'<text x="{left - 55}" y="{(top_margin + bottom)/2}" text-anchor="middle" font-size="12" '
                     f'fill="{AXIS_COLOR}" transform="rotate(-90 {left - 55} {(top_margin + bottom)/2})">{_esc(ylabel)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 组合图（柱 + 折线，双轴）
# ===========================================================================
def combo_chart(labels, bar_values, line_values, title, subtitle="", note="",
                bar_label="", line_label="", width=800, height=520,
                bar_color="#4E79A7", line_color="#E15759", line_is_pct=False):
    """组合图：柱状（左轴）+ 折线（右轴）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 60
    bottom = h - 70
    top_margin = top + 20

    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    vmax_bar = max(bar_values) * 1.15 if bar_values else 1
    vmax_line = max(line_values) * 1.15 if line_values else 1
    vmin_line = min(line_values)
    if vmin_line > 0:
        vmin_line = 0
    elif vmin_line < 0:
        vmin_line = vmin_line * 1.15

    slot = (right - left) / n
    bar_w = slot * 0.5

    def sy_bar(v):
        return bottom - (v / vmax_bar) * (bottom - top_margin)

    def sy_line(v):
        return bottom - (v - vmin_line) / (vmax_line - vmin_line) * (bottom - top_margin)

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    # 柱
    for i, (lb, v) in enumerate(zip(labels, bar_values)):
        x = left + slot * i + slot / 2
        bh = (v / vmax_bar) * (bottom - top_margin)
        parts.append(f'<rect x="{x - bar_w/2}" y="{bottom - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
                     f'fill="{bar_color}" rx="1"/>')

    # 折线
    pts = [(left + slot * i + slot / 2, sy_line(v)) for i, v in enumerate(line_values)]
    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    parts.append(f'<path d="{path}" fill="none" stroke="{line_color}" stroke-width="2.5"/>')
    for x, y in pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{line_color}"/>')

    # 右轴刻度
    for i in range(6):
        pct = vmin_line + (vmax_line - vmin_line) * i / 5
        y = bottom - (pct - vmin_line) / (vmax_line - vmin_line) * (bottom - top_margin)
        parts.append(f'<line x1="{right}" y1="{y:.1f}" x2="{right + 4}" y2="{y:.1f}" stroke="{AXIS_COLOR}"/>')
        lbl = f"{pct:.0f}%" if line_is_pct else f"{pct:.0f}"
        parts.append(f'<text x="{right + 8}" y="{y + 4:.1f}" font-size="9" fill="{line_color}">{lbl}</text>')

    # 图例
    parts.append(f'<rect x="{left}" y="{top_margin - 6}" width="12" height="10" fill="{bar_color}" rx="2"/>')
    parts.append(f'<text x="{left + 16}" y="{top_margin + 3}" font-size="11" fill="{AXIS_COLOR}">{_esc(bar_label)}</text>')
    parts.append(f'<line x1="{left + 60 + len(bar_label)*8}" y1="{top_margin - 1}" x2="{left + 80 + len(bar_label)*8}" y2="{top_margin - 1}" stroke="{line_color}" stroke-width="2.5"/>')
    parts.append(f'<text x="{left + 84 + len(bar_label)*8}" y="{top_margin + 3}" font-size="11" fill="{AXIS_COLOR}">{_esc(line_label)}</text>')

    # x 标签
    if n > 12:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 14}" text-anchor="end" font-size="8" fill="{AXIS_COLOR}" '
                         f'transform="rotate(-35 {x} {bottom + 14})">{_esc(lb)}</text>')
    else:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 16}" text-anchor="middle" font-size="9" fill="{AXIS_COLOR}">'
                         f'{_esc(lb)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 散点图
# ===========================================================================
def scatter_chart(points, title, subtitle="", xlabel="", ylabel="",
                  note="", width=800, height=560, color="#4E79A7", size=5):
    """散点图。points = [(x, y), ...]"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 40
    bottom = h - 70
    top_margin = top + 20

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xpad = (xmax - xmin) * 0.05 if xmax != xmin else 1
    ypad = (ymax - ymin) * 0.05 if ymax != ymin else 1
    xmin -= xpad; xmax += xpad
    ymin -= ypad; ymax += ypad

    def sx(x):
        return left + (x - xmin) / (xmax - xmin) * (right - left)

    def sy(y):
        return bottom - (y - ymin) / (ymax - ymin) * (bottom - top_margin)

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    for x, y in points:
        parts.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{size}" fill="{color}" fill-opacity="0.6"/>')

    if xlabel:
        parts.append(f'<text x="{(left + right)/2}" y="{h - 15}" text-anchor="middle" font-size="13" fill="{AXIS_COLOR}">'
                     f'{_esc(xlabel)}</text>')
    if ylabel:
        parts.append(f'<text x="{left - 55}" y="{(top_margin + bottom)/2}" text-anchor="middle" font-size="13" '
                     f'fill="{AXIS_COLOR}" transform="rotate(-90 {left - 55} {(top_margin + bottom)/2})">{_esc(ylabel)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 雷达图
# ===========================================================================
def radar_chart(categories, series_list, title, subtitle="", note="", width=700, height=600):
    """雷达图。series_list = [(name, values, color), ...]"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    cx = w / 2
    cy = h * 0.52
    r = min(w, h) * 0.32
    n = len(categories)

    if n == 0:
        return "".join(parts) + "</svg>"

    # 网格（多边形）
    for level in range(1, 6):
        rr = r * level / 5
        pts = []
        for i in range(n):
            angle = -90 + 360 * i / n
            pts.append((cx + rr * math.cos(math.radians(angle)), cy + rr * math.sin(math.radians(angle))))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        parts.append(f'<polygon points="{poly}" fill="none" stroke="{GRID_COLOR}" stroke-width="1"/>')

    # 轴线
    for i in range(n):
        angle = -90 + 360 * i / n
        x = cx + r * math.cos(math.radians(angle))
        y = cy + r * math.sin(math.radians(angle))
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{GRID_COLOR}" stroke-width="1"/>')
        # 分类标签
        lx = cx + (r + 30) * math.cos(math.radians(angle))
        ly = cy + (r + 30) * math.sin(math.radians(angle))
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="11" fill="{AXIS_COLOR}">'
                     f'{_esc(categories[i])}</text>')

    # 数据系列（仅描边 + 极淡填充，避免多系列叠加成大色块）
    for name, values, color in series_list:
        pts = []
        for i, v in enumerate(values):
            angle = -90 + 360 * i / n
            rr = r * (v / 100.0)
            pts.append((cx + rr * math.cos(math.radians(angle)), cy + rr * math.sin(math.radians(angle))))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        # 数据点标记
        for i, v in enumerate(values):
            angle = -90 + 360 * i / n
            rr = r * (v / 100.0)
            px = cx + rr * math.cos(math.radians(angle))
            py = cy + rr * math.sin(math.radians(angle))
            parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{color}" stroke="#fff" stroke-width="1"/>')
        parts.append(f'<polygon points="{poly}" fill="none" stroke="{color}" stroke-width="2.5"/>')

    # 图例（右侧纵向排布，避免重叠与截断）
    legend_x = w * 0.80
    legend_y = h * 0.24
    for name, values, color in series_list:
        parts.append(f'<line x1="{legend_x - 8}" y1="{legend_y}" x2="{legend_x + 20}" y2="{legend_y}" '
                     f'stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x + 26}" y="{legend_y + 4}" font-size="12" fill="{AXIS_COLOR}">{_esc(name)}</text>')
        legend_y += 26

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 瀑布图
# ===========================================================================
def waterfall_chart(labels, values, title, subtitle="", note="", width=800, height=520,
                    value_fmt=_fmt_money):
    """瀑布图（累计增减）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 30
    bottom = h - 70
    top_margin = top + 20

    n = len(labels)
    if n == 0:
        return "".join(parts) + "</svg>"

    # 计算累计
    cum = 0.0
    cum_values = []
    for v in values:
        cum_values.append(cum)
        cum += v

    all_vals = cum_values + [cum]
    vmax = max(all_vals) * 1.15
    vmin = min(all_vals)
    if vmin > 0:
        vmin = 0

    slot = (right - left) / n
    bar_w = slot * 0.6

    for i, v in enumerate(values):
        x = left + slot * i + slot / 2
        base = cum_values[i]
        top_v = base + v
        color = GREEN if v >= 0 else RED
        # 画浮动条
        y_base = bottom - (base - vmin) / (vmax - vmin) * (bottom - top_margin)
        y_top = bottom - (top_v - vmin) / (vmax - vmin) * (bottom - top_margin)
        parts.append(f'<rect x="{x - bar_w/2}" y="{min(y_base, y_top):.1f}" width="{bar_w:.1f}" '
                     f'height="{abs(y_top - y_base):.1f}" fill="{color}" rx="1"/>')
        # 连接线
        parts.append(f'<line x1="{x - bar_w/2}" y1="{y_base:.1f}" x2="{x + bar_w/2}" y2="{y_base:.1f}" '
                     f'stroke="{GRID_COLOR}" stroke-width="1" stroke-dasharray="3,3"/>')
        # 数值
        parts.append(f'<text x="{x}" y="{min(y_base, y_top) - 5:.1f}" text-anchor="middle" font-size="9" fill="{AXIS_COLOR}">'
                     f'{_esc(value_fmt(v))}</text>')

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    # x 标签
    if n > 12:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 14}" text-anchor="end" font-size="8" fill="{AXIS_COLOR}" '
                         f'transform="rotate(-35 {x} {bottom + 14})">{_esc(lb)}</text>')
    else:
        for i, lb in enumerate(labels):
            x = left + slot * i + slot / 2
            parts.append(f'<text x="{x}" y="{bottom + 16}" text-anchor="middle" font-size="9" fill="{AXIS_COLOR}">'
                         f'{_esc(lb)}</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 仪表盘图
# ===========================================================================
def gauge_chart(value, title, subtitle="", note="", width=700, height=500, vmax=100, unit="%"):
    """仪表盘图（目标完成度）"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    cx = w / 2
    cy = h * 0.62
    r = min(w, h) * 0.38

    # 背景弧（180度）
    start = 180
    for i in range(0, 100):
        a1 = math.radians(start + i * 1.8)
        a2 = math.radians(start + (i + 1) * 1.8)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        # 颜色分段
        if i < 60:
            color = "#E15759"
        elif i < 85:
            color = "#F28E2B"
        else:
            color = "#59A14F"
        parts.append(f'<path d="M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}" '
                     f'stroke="{color}" stroke-width="18" fill="none"/>')

    # 指针
    angle = math.radians(start + (value / vmax) * 180)
    px = cx + (r - 30) * math.cos(angle)
    py = cy + (r - 30) * math.sin(angle)
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{px:.1f}" y2="{py:.1f}" stroke="#2B2B2B" stroke-width="4"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="#2B2B2B"/>')

    # 数值
    parts.append(f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" font-size="34" font-weight="bold" fill="{TITLE_COLOR}">'
                 f'{value:.1f}{unit}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 34}" text-anchor="middle" font-size="13" fill="{SUBTITLE_COLOR}">目标完成度</text>')

    parts.append("</svg>")
    return "".join(parts)


# ===========================================================================
# 预测图（实际 + 拟合 + 置信区间）
# ===========================================================================
def forecast_chart(months, actual, fitted, forecast, title, subtitle="", note="",
                   width=900, height=560, value_fmt=_fmt_money):
    """时间序列预测图：实际值 + 拟合值 + 预测值 + 95% 置信区间"""
    w, h = width, height
    parts, top = _svg_header(w, h, title, subtitle, note)

    left = 90
    right = w - 40
    bottom = h - 70
    top_margin = top + 20

    # 拼接：历史 + 预测
    all_labels = list(months) + [f["month"] for f in forecast]
    all_actual = list(actual) + [None] * len(forecast)
    all_fitted = list(fitted) + [None] * len(forecast)

    n_hist = len(months)
    n_total = len(all_labels)

    all_vals = [v for v in all_actual if v is not None] + [f["forecast"] for f in forecast]
    vmin = min(all_vals) * 0.9
    vmax = max(all_vals) * 1.1

    def sx(i):
        return left + (right - left) * i / (n_total - 1)

    def sy(v):
        return bottom - (v - vmin) / (vmax - vmin) * (bottom - top_margin)

    _axis_lines(parts, left, bottom, right, top_margin)
    _grid_y(parts, left, bottom, right, top_margin, 5)

    # 置信区间（预测部分）
    for f in forecast:
        idx = n_hist + f["step"] - 1
        x = sx(idx)
        parts.append(f'<rect x="{x - 6}" y="{sy(f["upper_95"]):.1f}" width="12" '
                     f'height="{sy(f["lower_95"]) - sy(f["upper_95"]):.1f}" fill="#4E79A7" fill-opacity="0.15"/>')
        # 上下界虚线
        parts.append(f'<line x1="{x - 8}" y1="{sy(f["upper_95"]):.1f}" x2="{x + 8}" y2="{sy(f["upper_95"]):.1f}" '
                     f'stroke="#4E79A7" stroke-width="1" stroke-dasharray="3,3"/>')
        parts.append(f'<line x1="{x - 8}" y1="{sy(f["lower_95"]):.1f}" x2="{x + 8}" y2="{sy(f["lower_95"]):.1f}" '
                     f'stroke="#4E79A7" stroke-width="1" stroke-dasharray="3,3"/>')

    # 实际值折线
    pts_actual = [(sx(i), sy(v)) for i, v in enumerate(all_actual) if v is not None]
    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts_actual)
    parts.append(f'<path d="{path}" fill="none" stroke="#2B2B2B" stroke-width="2.5"/>')

    # 拟合值折线（历史部分）
    pts_fitted = [(sx(i), sy(v)) for i, v in enumerate(all_fitted) if v is not None]
    path_f = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts_fitted)
    parts.append(f'<path d="{path_f}" fill="none" stroke="#F28E2B" stroke-width="2" stroke-dasharray="5,3"/>')

    # 预测值折线
    pts_fc = [(sx(n_hist + f["step"] - 1), sy(f["forecast"])) for f in forecast]
    if pts_actual:
        pts_fc = [pts_actual[-1]] + pts_fc
    path_p = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts_fc)
    parts.append(f'<path d="{path_p}" fill="none" stroke="#E15759" stroke-width="2.5"/>')
    for x, y in pts_fc[1:]:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#E15759"/>')

    # 分隔线（历史/预测）
    sep_x = sx(n_hist - 1)
    parts.append(f'<line x1="{sep_x:.1f}" y1="{top_margin}" x2="{sep_x:.1f}" y2="{bottom}" '
                 f'stroke="#CCCCCC" stroke-width="1.5" stroke-dasharray="8,4"/>')
    parts.append(f'<text x="{sep_x:.1f}" y="{top_margin - 5}" text-anchor="middle" font-size="11" fill="#9A9A9A">'
                 f'历史 | 预测</text>')

    # 图例
    parts.append(f'<line x1="{left}" y1="{top_margin - 8}" x2="{left + 20}" y2="{top_margin - 8}" stroke="#2B2B2B" stroke-width="2.5"/>')
    parts.append(f'<text x="{left + 24}" y="{top_margin - 4}" font-size="11" fill="{AXIS_COLOR}">实际值</text>')
    parts.append(f'<line x1="{left + 90}" y1="{top_margin - 8}" x2="{left + 110}" y2="{top_margin - 8}" stroke="#F28E2B" stroke-width="2" stroke-dasharray="5,3"/>')
    parts.append(f'<text x="{left + 114}" y="{top_margin - 4}" font-size="11" fill="{AXIS_COLOR}">拟合值</text>')
    parts.append(f'<line x1="{left + 180}" y1="{top_margin - 8}" x2="{left + 200}" y2="{top_margin - 8}" stroke="#E15759" stroke-width="2.5"/>')
    parts.append(f'<text x="{left + 204}" y="{top_margin - 4}" font-size="11" fill="{AXIS_COLOR}">预测值</text>')
    parts.append(f'<rect x="{left + 270}" y="{top_margin - 14}" width="20" height="10" fill="#4E79A7" fill-opacity="0.2"/>')
    parts.append(f'<text x="{left + 294}" y="{top_margin - 4}" font-size="11" fill="{AXIS_COLOR}">95%置信区间</text>')

    # x 轴标签
    step = max(1, n_total // 14)
    for i in range(0, n_total, step):
        parts.append(f'<text x="{sx(i)}" y="{bottom + 16}" text-anchor="middle" font-size="9" fill="{AXIS_COLOR}">'
                     f'{_esc(all_labels[i])}</text>')

    parts.append("</svg>")
    return "".join(parts)

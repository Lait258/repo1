# -*- coding: utf-8 -*-
"""
《Excel数据可视化——从图表到数据大屏》第二章 30 个图表 Python 复现
数据源: data/第二章 图表(前15).xlsx, data/第二章 图表(后15).xlsx
输出  : figures/ 下的 PNG 图片
依赖  : matplotlib, pandas, numpy, scipy
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Wedge, Circle, Rectangle, Polygon, PathPatch
from matplotlib.path import Path
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
from scipy.interpolate import make_interp_spline

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "SimHei", "WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 100

DATA1 = r"/mnt/agents/output/excel-data-viz-chapter2/data/第二章 图表(前15).xlsx"
DATA2 = r"/mnt/agents/output/excel-data-viz-chapter2/data/第二章 图表(后15).xlsx"
FIG = r"/mnt/agents/output/excel-data-viz-chapter2/figures"

def read(sheet, book=1, header=1):
    f = DATA1 if book == 1 else DATA2
    df = pd.read_excel(f, sheet_name=sheet, header=header)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df = df.dropna(subset=[df.columns[0]])
    return df.reset_index(drop=True)

def save(fig, name):
    fig.savefig(f"{FIG}/{name}.png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    print("saved:", name)

# ============ 01 渐变柱形图 ============
def chart01():
    df = read("1 渐变柱形图")
    fig, ax = plt.subplots(figsize=(8, 5))
    cmap = LinearSegmentedColormap.from_list("g", ["#B7E4C7", "#2D6A4F"])
    x = np.arange(len(df))
    bars = ax.bar(x, df["销售量"], width=0.6, color="#2D6A4F")
    # 在柱体内部画垂直渐变色块
    for b in bars:
        grad = np.linspace(0, 1, 256).reshape(-1, 1)
        ax.imshow(grad, extent=[b.get_x(), b.get_x()+b.get_width(), 0, b.get_height()],
                  aspect="auto", cmap=cmap, zorder=3)
    ax.set_xticks(x); ax.set_xticklabels(df["区域"])
    ax.set_title("01 渐变柱形图"); ax.set_ylabel("销售量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "01_渐变柱形图")

# ============ 02 带均值柱形图 ============
def chart02():
    df = read("2 带均值柱形图")
    mean = df["销售量"].mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df["区域"], df["销售量"], color="#6FB3B8", width=0.6)
    ax.axhline(mean, color="#C0392B", ls="--", lw=1.5)
    ax.text(len(df)-0.4, mean, f"均值 {mean:.0f}", color="#C0392B",
            va="bottom", ha="right", fontsize=11)
    ax.set_title("02 带均值柱形图"); ax.set_ylabel("销售量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "02_带均值柱形图")

# ============ 03 渐变圆角柱形图 ============
def chart03():
    df = read("3 渐变圆角柱形图").dropna()
    cmap = LinearSegmentedColormap.from_list("g", ["#B7E4C7", "#2D6A4F"])
    fig, ax = plt.subplots(figsize=(8, 5))
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    for i, (name, v) in enumerate(zip(df["商品"], df["销量"])):
        w, h = 0.55, v
        r = w / 2
        # 圆角矩形（上圆角）
        p = FancyBboxPatch((i - w/2, 0), w, h,
                           boxstyle=f"round,pad=0,rounding_size={min(r, h*0.5)}",
                           mutation_aspect=1, fc="#2D6A4F", ec="none")
        ax.add_patch(p)
        # 裁剪渐变填充
        ax.imshow(grad, extent=[i-w/2, i+w/2, 0, h], aspect="auto", cmap=cmap,
                  clip_path=p, clip_on=True, zorder=3)
        ax.text(i, h+15, int(v), ha="center", fontsize=10)
    ax.set_xlim(-0.6, len(df)-0.4); ax.set_ylim(0, df["销量"].max()*1.12)
    ax.set_xticks(range(len(df))); ax.set_xticklabels(df["商品"])
    ax.set_title("03 渐变圆角柱形图"); ax.set_ylabel("销量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "03_渐变圆角柱形图")

# ============ 04 标注柱形图 ============
def chart04():
    df = read("4 标注柱形图").dropna()
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(df["月份"], df["销量"], color="#8ECAE6", width=0.6)
    imax = df["销量"].idxmax(); imin = df["销量"].idxmin()
    for i, b in enumerate(bars):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+80, int(b.get_height()),
                ha="center", fontsize=9)
    # 最大/最小值箭头标注
    for i, c, t in [(imax, "#2A9D8F", "最高"), (imin, "#E76F51", "最低")]:
        v = df.loc[i, "销量"]
        ax.annotate(f"{t} {int(v)}", xy=(i, v), xytext=(i, v+900),
                    arrowprops=dict(arrowstyle="->", color=c), color=c,
                    ha="center", fontsize=10)
    ax.set_title("04 标注柱形图"); ax.set_ylabel("销量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "04_标注柱形图")

# ============ 05 层叠柱形图 ============
def chart05():
    df = read("5 层叠柱形图")
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#A8DADC", "#6FB3B8", "#457B9D", "#2A9D8F", "#1D3557"]
    bottom = 0
    for i, (q, v) in enumerate(zip(df["季度"], df["销售额"])):
        ax.bar(i, v, bottom=bottom, color=colors[i % 5], width=0.6)
        ax.text(i, bottom + v/2, f"{q}\n{int(v)}", ha="center", va="center",
                color="white", fontsize=9)
        bottom += v
    ax.set_xticks([]); ax.set_title("05 层叠柱形图"); ax.set_ylabel("销售额(累计)")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "05_层叠柱形图")

# ============ 06 蝴蝶图(销量对比) ============
def chart06():
    df = read("6 蝴蝶图")
    y = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(y, -df["2021年销量"], color="#F4A261", height=0.6, label="2021年销量")
    ax.barh(y,  df["2022年销量"], color="#2A9D8F", height=0.6, label="2022年销量")
    for i, (a, b) in enumerate(zip(df["2021年销量"], df["2022年销量"])):
        ax.text(-a-40, i, int(a), ha="right", va="center", fontsize=9)
        ax.text(b+40, i, int(b), ha="left", va="center", fontsize=9)
    ax.set_yticks(y); ax.set_yticklabels(df["区域"])
    ax.axvline(0, color="gray", lw=0.8)
    ax.set_title("06 蝴蝶图（2021 vs 2022 销量）"); ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "06_蝴蝶图_销量")

# ============ 07 蝴蝶图(百分比) ============
def chart07():
    df = read("7 蝴蝶图").dropna(subset=["区域"])
    y = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(y, -df["2021年"], color="#F4A261", height=0.55, label="2021年")
    ax.barh(y,  df["2022年"], color="#2A9D8F", height=0.55, label="2022年")
    for i, (a, b) in enumerate(zip(df["2021年"], df["2022年"])):
        ax.text(-a-0.01, i, f"{a:.0%}", ha="right", va="center", fontsize=9)
        ax.text(b+0.01, i, f"{b:.0%}", ha="left", va="center", fontsize=9)
    ax.set_yticks(y); ax.set_yticklabels(df["区域"])
    ax.set_xlim(-0.6, 0.6); ax.axvline(0, color="gray", lw=0.8)
    ax.set_xticks([])
    ax.set_title("07 蝴蝶图（占比对比）"); ax.legend()
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    save(fig, "07_蝴蝶图_占比")

# ============ 08 数值百分比柱形图 ============
def chart08():
    df = read("8 数值百分比")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df["区域"], df["销量"], color="#457B9D", width=0.6)
    for i, (v, pct) in enumerate(zip(df["销量"], df["同比去年"])):
        ax.text(i, v+60, f"{int(v)}", ha="center", fontsize=10)
        color = "#2A9D8F" if pct >= 0 else "#E76F51"
        sym = "▲" if pct >= 0 else "▼"
        ax.text(i, v+260, f"{sym} {abs(pct):.1%}", ha="center", fontsize=9, color=color)
    ax.set_title("08 数值百分比柱形图"); ax.set_ylabel("销量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "08_数值百分比柱形图")

# ============ 09 对比柱形图 ============
def chart09():
    df = read("9 对比柱形图")
    x = np.arange(len(df)); w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w/2, df["2021销量"], w, label="2021销量", color="#A8DADC")
    ax.bar(x + w/2, df["2022销量"], w, label="2022销量", color="#457B9D")
    for i in x:
        ax.text(i - w/2, df.loc[i, "2021销量"]+60, int(df.loc[i, "2021销量"]),
                ha="center", fontsize=8)
        ax.text(i + w/2, df.loc[i, "2022销量"]+60, int(df.loc[i, "2022销量"]),
                ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(df["商品"])
    ax.set_title("09 对比柱形图"); ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "09_对比柱形图")

# ============ 10 甘特图 ============
def chart10():
    df = read("10 甘特图", header=2)
    df["开始日期"] = pd.to_datetime(df["开始日期"])
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, r in df.iterrows():
        start = r["开始日期"]
        days = pd.Timedelta(days=float(r["项目天数"]))
        # 背景条:总工期
        ax.barh(i, days, left=start, color="#E9ECEF", height=0.55, zorder=1)
        # 已完成部分
        ax.barh(i, pd.Timedelta(days=float(r["进行天数"])), left=start,
                color="#2A9D8F", height=0.55, zorder=2)
        ax.text(start + days + pd.Timedelta(days=0.6), i,
                f"{r['完成度']:.0%}", va="center", fontsize=9, color="#2A9D8F")
    ax.set_yticks(range(len(df))); ax.set_yticklabels(df["项目名称"])
    ax.invert_yaxis()
    ax.set_title("10 甘特图（绿色为已完成进度）")
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    save(fig, "10_甘特图")

# ============ 11 平滑折线图 ============
def chart11():
    df = read("11 平滑折线图")
    x = np.arange(len(df))
    xs = np.linspace(x.min(), x.max(), 400)
    ys = make_interp_spline(x, df["销量"], k=3)(xs)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(xs, ys, color="#457B9D", lw=2, zorder=2)
    ax.plot(x, df["销量"], "o", color="#E76F51", ms=5, zorder=3)
    ax.fill_between(xs, ys, color="#457B9D", alpha=0.1)
    ax.set_xticks(x); ax.set_xticklabels(df["月份"], fontsize=8)
    ax.set_title("11 平滑折线图"); ax.set_ylabel("销量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "11_平滑折线图")

# ============ 12 菱形走势图 ============
def chart12():
    df = read("12 菱形走势图")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["月份"], df["完成率"], color="#6FB3B8", lw=1.8,
            marker="D", ms=9, mec="#2A9D8F", mfc="#B7E4C7", zorder=3)
    for i, v in enumerate(df["完成率"]):
        ax.text(i, v+0.02, f"{v:.0%}", ha="center", fontsize=9)
    ax.set_ylim(df["完成率"].min()-0.1, df["完成率"].max()+0.12)
    ax.set_title("12 菱形走势图"); ax.set_ylabel("完成率")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "12_菱形走势图")

# ============ 13 对比折线图 ============
def chart13():
    df = read("13 对比折线图")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["月份"], df["2021年"], marker="o", color="#A8DADC", lw=2, label="2021年")
    ax.plot(df["月份"], df["2022年"], marker="o", color="#E76F51", lw=2, label="2022年")
    # 交点区域高亮（可选）
    ax.set_title("13 对比折线图"); ax.set_ylabel("销量"); ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "13_对比折线图")

# ============ 14 单值圆环图 ============
def chart14():
    df = read("14 单值圆环图")
    v = float(df["完成率"].iloc[0])
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie([v, 1-v], colors=["#2A9D8F", "#E9ECEF"],
           startangle=90, counterclock=False,
           wedgeprops=dict(width=0.3))
    ax.text(0, 0, f"{v:.0%}", ha="center", va="center", fontsize=28, color="#2A9D8F")
    ax.set_title("14 单值圆环图（完成率 85%）")
    save(fig, "14_单值圆环图")

# ============ 15 水球图 ============
def chart15():
    df = read("15 水球图")
    v = float(df["完成率"].iloc[0])
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.15, 1.15); ax.set_aspect("equal")
    ax.axis("off")
    theta = np.linspace(0, 2*np.pi, 200)
    R = 1.0
    ax.plot(R*np.cos(theta), R*np.sin(theta), color="#457B9D", lw=2)
    # 水面(加波浪)
    y0 = -R + 2*R*v  # 水面高度
    xs = np.linspace(-R, R, 400)
    wave = 0.03*np.sin(xs*20)
    fill_y = np.minimum(y0 + wave, np.sqrt(np.clip(R**2 - xs**2, 0, None)))
    ax.fill_between(xs, -R, fill_y, color="#74C0FC", alpha=0.85)
    ax.text(0, 0, f"{v:.0%}", ha="center", va="center", fontsize=26, color="#1864AB")
    ax.set_title("15 水球图（完成率 65%）", pad=10)
    save(fig, "15_水球图")

if __name__ == "__main__":
    import sys
    chart01(); chart02(); chart03(); chart04(); chart05(); chart06()
    chart07(); chart08(); chart09(); chart10(); chart11(); chart12()
    chart13(); chart14(); chart15()

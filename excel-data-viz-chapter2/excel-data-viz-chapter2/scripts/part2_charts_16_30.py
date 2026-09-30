# -*- coding: utf-8 -*-
"""第二章图表复现: 16-30 (接 part1)"""
from part1_charts_01_15 import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Wedge, Circle, Rectangle
from matplotlib.colors import LinearSegmentedColormap

# ============ 16 波浪水球图 ============
def chart16():
    df = pd.read_excel(DATA2, sheet_name="16 波浪水球图 ", header=None)
    v = float(df.iloc[3, 2])  # 完成率
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.2, 1.2); ax.set_aspect("equal"); ax.axis("off")
    theta = np.linspace(0, 2*np.pi, 300)
    R = 1.0
    # 外圈(波浪边框): 半径按角度轻微起伏
    ax.plot(R*np.cos(theta), R*np.sin(theta), color="#4D96FF", lw=1.5, alpha=0.9)
    y0 = -R + 2*R*v
    xs = np.linspace(-R, R, 600)
    top = np.sqrt(np.clip(R**2 - xs**2, 0, None))
    wave = 0.04*np.sin(xs*14) + 0.015*np.sin(xs*30)
    ax.fill_between(xs, -top, np.minimum(y0 + wave, top), color="#6BCB77", alpha=0.85)
    ax.text(0, 0.12, f"{v:.0%}", ha="center", va="center", fontsize=26, color="#1B5E20")
    ax.text(0, -0.22, "完成率", ha="center", fontsize=12, color="#1B5E20")
    ax.set_title("16 波浪水球图", pad=10)
    save(fig, "16_波浪水球图")

# ============ 17 玉玦图 ============
def chart17():
    df = read("17 玉玦图", book=2)
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection="polar"))
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    colors = ["#2A9D8F", "#6FB3B8", "#A8DADC", "#E9ECEF"]
    bottom = 0
    for i, r in df.iterrows():
        theta = r["占比"] * 2*np.pi
        ax.barh(1, theta, left=bottom, height=0.5, color=colors[i % 4],
                edgecolor="white", lw=2)
        mid = bottom + theta/2
        ax.text(mid, 1.05, f'{r["年龄"]} {r["占比"]:.1%}', ha="center", va="center",
                fontsize=10, rotation=0)
        bottom += theta
    ax.set_ylim(0, 1.6); ax.set_yticks([]); ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title("17 玉玦图（员工年龄分布）", pad=20)
    save(fig, "17_玉玦图")

# ============ 18 跑道图 ============
def chart18():
    df = read("18 跑道图", book=2)
    total = df["人数"].max() * 1.25
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(df)))
    for i, (d, n) in enumerate(zip(df["部门"], df["人数"])):
        p = FancyBboxPatch((0, i*0.9), total, 0.6,
                           boxstyle="round,pad=0,rounding_size=0.3",
                           fc="#F1F3F5", ec="none")
        ax.add_patch(p)
        p2 = FancyBboxPatch((0, i*0.9), n, 0.6,
                            boxstyle="round,pad=0,rounding_size=0.3",
                            fc=colors[i], ec="none")
        ax.add_patch(p2)
        ax.text(total + 10, i*0.9 + 0.3, f"{int(n)} 人", va="center", fontsize=10)
    ax.set_xlim(0, total*1.15); ax.set_ylim(-0.2, len(df)*0.9)
    ax.set_yticks([i*0.9+0.3 for i in range(len(df))]); ax.set_yticklabels(df["部门"])
    ax.set_xticks([]); ax.set_title("18 跑道图（各部门人数）")
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    save(fig, "18_跑道图")

# ============ 19 南丁格尔圆饼图 ============
def chart19():
    df = read("19 南丁格尔圆饼图", book=2)
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(projection="polar"))
    vals = df["人数占比"].values
    n = len(vals)
    theta = 2*np.pi/n
    colors = plt.cm.Set2(np.linspace(0, 1, n))
    for i, v in enumerate(vals):
        ax.bar(i*theta, v, width=theta*0.95, color=colors[i],
               edgecolor="white", lw=1.5)
        ang = i*theta + theta/2
        ax.text(ang, v+0.02, f'{df["部门"].iloc[i]}\n{v:.1%}',
                ha="center", va="center", fontsize=9)
    ax.set_ylim(0, vals.max()*1.25)
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title("19 南丁格尔圆饼图（玫瑰图）", pad=20)
    save(fig, "19_南丁格尔圆饼图")

# ============ 20 南丁格尔圆环图 ============
def chart20():
    df = read("20 南丁格尔圆环图", book=2)
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(projection="polar"))
    vals = df["人数占比"].values
    n = len(vals)
    theta = 2*np.pi/n
    inner = vals.max()*0.45
    colors = ["#F4A261", "#6FB3B8", "#2A9D8F", "#457B9D"]
    for i, v in enumerate(vals):
        ax.bar(i*theta, v-inner, bottom=inner, width=theta*0.95,
               color=colors[i % 4], edgecolor="white", lw=1.5)
        ang = i*theta + theta/2
        ax.text(ang, v+0.03, f'{df["年龄"].iloc[i]}\n{v:.1%}',
                ha="center", va="center", fontsize=10)
    ax.set_ylim(0, vals.max()*1.25)
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title("20 南丁格尔圆环图", pad=20)
    save(fig, "20_南丁格尔圆环图")

# ============ 22 仪表盘图 ============
def chart22():
    df = pd.read_excel(DATA2, sheet_name="22 仪表盘图", header=None)
    value = float(df.iloc[2, 7])  # 指针数值 76
    vmin, vmax = 50, 150
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-1.3, 1.3); ax.set_ylim(-0.3, 1.3)
    a0, a1 = 180, 0  # 从180°到0°
    # 三段色带
    bands = [(vmin, 90, "#B7E4C7"), (90, 120, "#FFE08A"), (120, vmax, "#F4A261")]
    for lo, hi, c in bands:
        t0 = 180 - (lo-vmin)/(vmax-vmin)*180
        t1 = 180 - (hi-vmin)/(vmax-vmin)*180
        ax.add_patch(Wedge((0, 0), 1.0, t1, t0, width=0.18, fc=c, ec="white"))
    # 刻度
    for t in range(vmin, vmax+1, 10):
        ang = np.deg2rad(180 - (t-vmin)/(vmax-vmin)*180)
        ax.plot([0.82*np.cos(ang), 0.72*np.cos(ang)],
                [0.82*np.sin(ang), 0.72*np.sin(ang)], color="gray", lw=1)
        ax.text(0.62*np.cos(ang), 0.62*np.sin(ang), str(t),
                ha="center", va="center", fontsize=8)
    # 指针
    pa = np.deg2rad(180 - (value-vmin)/(vmax-vmin)*180)
    ax.plot([0, 0.68*np.cos(pa)], [0, 0.68*np.sin(pa)], color="#C0392B", lw=3)
    ax.add_patch(Circle((0, 0), 0.04, fc="#C0392B"))
    ax.text(0, -0.22, f"{value:.0f}", ha="center", fontsize=22, color="#C0392B")
    ax.set_title("22 仪表盘图", pad=12)
    save(fig, "22_仪表盘图")

# ============ 23 柱形折线图 ============
def chart23():
    df = read("23 柱形折线图", book=2)
    x = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x, df["销售量"], color="#A8DADC", width=0.55, label="销售量")
    ax2 = ax.twinx()
    ax2.plot(x, df["销售量"], color="#E76F51", marker="o", lw=2, label="趋势线")
    ax.set_xticks(x); ax.set_xticklabels(df["年份"])
    ax.set_title("23 柱形折线图")
    ax.spines[["top"]].set_visible(False)
    save(fig, "23_柱形折线图")

# ============ 24 目标柱形图 ============
def chart24():
    df = read("24 目标柱形图", book=2)
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(df))
    ax.bar(x, df["实际销量"], color="#6FB3B8", width=0.55, label="实际销量")
    for i, t in enumerate(df["目标销量"]):
        ax.plot([i-0.28, i+0.28], [t, t], color="#C0392B", lw=2)
        ax.text(i+0.3, t, f"目标 {t}", va="center", fontsize=8, color="#C0392B")
    for i, (a, t) in enumerate(zip(df["实际销量"], df["目标销量"])):
        c = "#2A9D8F" if a >= t else "#E76F51"
        ax.text(i, a+18, int(a), ha="center", fontsize=9, color=c)
    ax.set_xticks(x); ax.set_xticklabels(df["商品"])
    ax.set_title("24 目标柱形图"); ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "24_目标柱形图")

# ============ 25 子弹图 ============
def chart25():
    df = read("25 子弹图", book=2, header=2)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(df))
    for i, r in df.iterrows():
        # 背景性能区间: 0-及格-良好-优秀
        g, ok, good, exc = 0, r["及格"], r["及格"]+r["良好"], r["及格"]+r["良好"]+r["优秀"]
        ax.barh(i, ok, color="#E9ECEF", height=0.5)
        ax.barh(i, r["良好"], left=ok, color="#CED4DA", height=0.5)
        ax.barh(i, r["优秀"], left=good, color="#ADB5BD", height=0.5)
        # 实际值
        ax.barh(i, r["实际"], color="#2A9D8F", height=0.2)
        # 目标标记
        ax.plot([r["目标"], r["目标"]], [i-0.28, i+0.28], color="#C0392B", lw=2)
        ax.text(r["实际"]+15, i, int(r["实际"]), va="center", fontsize=9)
    ax.set_yticks(x); ax.set_yticklabels(df["商品"])
    ax.set_title("25 子弹图（▏红线为目标值）")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "25_子弹图")

# ============ 26 柱形圆 ============
def chart26():
    df = read("26 柱形圆", book=2)
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(df)); base = df["占位"].iloc[0]
    ax.bar(x, [base]*len(df), color="#F1F3F5", width=0.6)
    for i, v in enumerate(df["销量"]):
        ax.bar(i, v, color="#6FB3B8", width=0.6)
        # 柱顶半圆
        w = 0.6; r = w/2
        theta = np.linspace(0, np.pi, 50)
        ax.fill(v*np.cos(theta)*r/w*0 + i + r*np.cos(theta),
                v + r*np.sin(theta), color="#6FB3B8")
        ax.text(i, base+60, int(v), ha="center", fontsize=10)
    ax.set_xticks(x); ax.set_xticklabels(df["区域"])
    ax.set_ylim(0, base*1.15)
    ax.set_title("26 柱形圆"); ax.set_ylabel("销量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "26_柱形圆")

# ============ 27 簇状柱形折线图 ============
def chart27():
    df = read("27 簇状柱形折线图", book=2)
    x = np.arange(len(df)); w = 0.36
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - w/2, df["2021销量"], w, label="2021销量", color="#A8DADC")
    ax.bar(x + w/2, df["2022销量"], w, label="2022销量", color="#457B9D")
    ax2 = ax.twinx()
    growth = (df["2022销量"] - df["2021销量"]) / df["2021销量"] * 100
    ax2.plot(x, growth, color="#E76F51", marker="o", lw=2, label="同比增长率(%)")
    for i, g in enumerate(growth):
        ax2.annotate(f"{g:.1f}%", (i, g), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=8, color="#E76F51")
    ax.set_xticks(x); ax.set_xticklabels(df["区域"])
    ax.set_title("27 簇状柱形折线图")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1+h2, l1+l2, loc="upper left", fontsize=8)
    ax.spines[["top"]].set_visible(False)
    save(fig, "27_簇状柱形折线图")

# ============ 28 复合柱形图 ============
def chart28():
    df = read("28 复合柱形图", book=2)
    mean = df["月度销量"].mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#457B9D" if v >= mean else "#A8DADC" for v in df["月度销量"]]
    ax.bar(df["月份"], df["月度销量"], color=colors, width=0.6)
    for i, v in enumerate(df["月度销量"]):
        ax.text(i, v+40, int(v), ha="center", fontsize=8)
    ax.axhline(mean, color="#C0392B", ls="--", lw=1.2)
    ax.text(len(df)-0.5, mean, f"均值 {mean:.0f}", color="#C0392B", va="bottom", ha="right")
    ax.set_title("28 复合柱形图（高于/低于均值分色）"); ax.set_ylabel("月度销量")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "28_复合柱形图")

# ============ 29 滑珠图 ============
def chart29():
    df = read("29 滑珠图", book=2)
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, r in df.iterrows():
        ax.plot([0, 1], [i, i], color="#DEE2E6", lw=6, solid_capstyle="round", zorder=1)
        ax.plot([0, r["完成率"]], [i, i], color="#2A9D8F", lw=6,
                solid_capstyle="round", zorder=2)
        ax.plot(r["完成率"], i, "o", ms=14, color="#1B5E20", zorder=3)
        ax.plot(r["完成率"], i, "o", ms=6, color="white", zorder=4)
        ax.text(r["完成率"], i+0.22, f'{r["完成率"]:.0%}', ha="center", fontsize=9)
    ax.set_yticks(range(len(df))); ax.set_yticklabels(df["区域"])
    ax.set_xlim(-0.05, 1.1); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0%}")
    ax.set_ylim(-0.5, len(df)-0.3)
    ax.set_title("29 滑珠图（完成率）")
    ax.spines[["top", "right", "left"]].set_visible(False)
    save(fig, "29_滑珠图")

# ============ 30 对比滑珠图 ============
def chart30():
    df = read("30 对比滑珠图", book=2, header=2)
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, r in df.iterrows():
        ax.plot([0, 1], [i, i], color="#DEE2E6", lw=6, solid_capstyle="round", zorder=1)
        ax.plot(r["2021完成率"], i, "o", ms=13, color="#F4A261", zorder=3, label="2021" if i==0 else None)
        ax.plot(r["2022完成率"], i, "o", ms=13, color="#2A9D8F", zorder=4, label="2022" if i==0 else None)
        ax.plot(r["2021完成率"], i, "o", ms=5, color="white", zorder=5)
        ax.plot(r["2022完成率"], i, "o", ms=5, color="white", zorder=6)
        ax.annotate("", xy=(r["2022完成率"], i), xytext=(r["2021完成率"], i),
                    arrowprops=dict(arrowstyle="-|>", color="#868E96", lw=1.2), zorder=2)
    ax.set_yticks(range(len(df))); ax.set_yticklabels(df["区域"])
    ax.set_xlim(-0.05, 1.1); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0%}")
    ax.set_title("30 对比滑珠图（2021 vs 2022）"); ax.legend()
    ax.spines[["top", "right", "left"]].set_visible(False)
    save(fig, "30_对比滑珠图")

if __name__ == "__main__":
    chart16(); chart17(); chart18(); chart19(); chart20()
    chart22(); chart23(); chart24(); chart25(); chart26()
    chart27(); chart28(); chart29(); chart30()

# -*- coding: utf-8 -*-
"""
utils.py —— 纯 Python 标准库实现的通用数据工具模块

提供轻量级的 CSV 读写、分组聚合、统计计算等能力，
替代 pandas/numpy 的核心用法，保证任何环境零依赖可复现。

设计原则：
- 仅使用 Python 标准库（csv / json / math / statistics / datetime）
- 数据在内存中以"列表字典"（list of dict）形式流转，字段名对齐 Olist schema
"""

import csv
import json
import math
import os
import statistics
import datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "raw")
CLEAN_DIR = os.path.join(BASE, "data", "clean")
FIG_DIR = os.path.join(BASE, "outputs", "figures")
TBL_DIR = os.path.join(BASE, "outputs", "tables")
DOC_DIR = os.path.join(BASE, "docs")
os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TBL_DIR, exist_ok=True)
os.makedirs(DOC_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# CSV 读写
# ---------------------------------------------------------------------------
def read_csv(path):
    """读取 CSV，返回 list[dict]，所有值保持字符串（后续按需转型）"""
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def write_csv(rows, fieldnames, path):
    """写入 CSV（utf-8-sig，Excel 可直接打开）"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_float(x, default=None):
    """安全转 float"""
    try:
        if x is None or x == "":
            return default
        return float(x)
    except (ValueError, TypeError):
        return default


def to_int(x, default=None):
    """安全转 int"""
    try:
        if x is None or x == "":
            return default
        return int(float(x))
    except (ValueError, TypeError):
        return default


def row_key(r, key):
    """提取行的主键值（支持单字段或复合主键元组）"""
    if isinstance(key, tuple):
        return tuple(r.get(k) for k in key)
    return r.get(key)


def to_date(x, fmt="%Y-%m-%d %H:%M:%S"):
    """安全转 datetime"""
    try:
        if x is None or x == "":
            return None
        return dt.datetime.strptime(x, fmt)
    except (ValueError, TypeError):
        return None


def to_date_d(x):
    """安全转 date（兼容 %Y-%m-%d）"""
    try:
        if x is None or x == "":
            return None
        return dt.datetime.strptime(x, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 分组聚合
# ---------------------------------------------------------------------------
def groupby(rows, key_fn):
    """按 key_fn 分组，返回 dict[key] -> list[rows]"""
    groups = {}
    for r in rows:
        k = key_fn(r)
        groups.setdefault(k, []).append(r)
    return groups


def aggregate(rows, key_fn, agg_fn):
    """分组聚合：返回 dict[key] -> agg_fn(该组行列表) 的结果"""
    groups = groupby(rows, key_fn)
    return {k: agg_fn(v) for k, v in groups.items()}


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------
def mean(values):
    values = [v for v in values if v is not None]
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values):
    values = sorted([v for v in values if v is not None])
    if not values:
        return 0.0
    n = len(values)
    if n % 2 == 1:
        return values[n // 2]
    return (values[n // 2 - 1] + values[n // 2]) / 2.0


def quantile(values, q):
    """分位数（q 为 0~1）"""
    values = sorted([v for v in values if v is not None])
    if not values:
        return 0.0
    idx = (len(values) - 1) * q
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return values[lo]
    frac = idx - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def pstdev(values):
    """总体标准差"""
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


# ---------------------------------------------------------------------------
# 日期工具
# ---------------------------------------------------------------------------
def month_key(d):
    """返回 YYYY-MM 字符串"""
    return d.strftime("%Y-%m")


def days_between(d1, d2):
    """两个日期的天数差"""
    if d1 is None or d2 is None:
        return None
    return (d2 - d1).days


# ---------------------------------------------------------------------------
# 结果表输出
# ---------------------------------------------------------------------------
def save_result_table(rows, fieldnames, name):
    """保存结果表为 CSV（outputs/tables/）"""
    path = os.path.join(TBL_DIR, name)
    write_csv(rows, fieldnames, path)
    print(f"  结果表已保存: tables/{name}")
    return path

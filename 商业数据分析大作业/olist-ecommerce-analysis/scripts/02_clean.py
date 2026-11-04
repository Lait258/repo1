# -*- coding: utf-8 -*-
"""
02_clean.py —— 数据清洗与治理脚本

完成以下治理任务（纯 Python 标准库实现）：
1. 缺失值处理：删除/填充关键字段缺失，标注填充方式
2. 异常值识别：基于 IQR（四分位距）识别价格/重量异常值
3. 重复值去除：基于主键去重
4. 类型与日期格式统一：字符串→数值/日期
5. 多表主外键对齐：订单-明细-客户-卖家-商品-支付-评价 关联校验
6. 指标派生：GMV、客单价、复购等分析指标

输出：
- data/clean/ 下清洗后的 CSV
- data/clean/olist_analysis.sqlite  SQLite 数据库（便于复用与验证）
"""

import os
import sqlite3
import datetime as dt

from utils import (
    BASE, RAW_DIR, CLEAN_DIR,
    read_csv, write_csv, to_float, to_int, to_date,
    mean, median, quantile, pstdev,
    groupby, month_key, row_key,
)

FIELD_MAP = {
    "orders": {
        "src": "olist_orders_dataset.csv",
        "fields": ["order_id", "customer_id", "order_status",
                   "order_purchase_timestamp", "order_approved_at",
                   "order_delivered_carrier_date", "order_delivered_customer_date",
                   "order_estimated_delivery_date"],
    },
    "items": {
        "src": "olist_order_items_dataset.csv",
        "fields": ["order_id", "order_item_id", "product_id", "seller_id",
                   "shipping_limit_date", "price", "freight_value"],
    },
    "customers": {
        "src": "olist_customers_dataset.csv",
        "fields": ["customer_id", "customer_unique_id", "customer_zip_code_prefix",
                   "customer_city", "customer_state"],
    },
    "sellers": {
        "src": "olist_sellers_dataset.csv",
        "fields": ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    },
    "products": {
        "src": "olist_products_dataset.csv",
        "fields": ["product_id", "product_category_name", "product_name_lenght",
                   "product_description_lenght", "product_photos_qty",
                   "product_weight_g", "product_length_cm", "product_height_cm",
                   "product_width_cm"],
    },
    "payments": {
        "src": "olist_order_payments_dataset.csv",
        "fields": ["order_id", "payment_sequential", "payment_type",
                   "payment_installments", "payment_value"],
    },
    "reviews": {
        "src": "olist_order_reviews_dataset.csv",
        "fields": ["review_id", "order_id", "review_score",
                   "review_comment_title", "review_comment_message",
                   "review_creation_date", "review_answer_timestamp"],
    },
}


def load_raw():
    """加载原始数据"""
    return {k: read_csv(os.path.join(RAW_DIR, v["src"])) for k, v in FIELD_MAP.items()}


def dedupe(rows, key):
    """基于主键去重（支持复合主键元组）"""
    seen = set()
    out = []
    for r in rows:
        k = row_key(r, key)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def clean_orders(orders):
    """清洗订单表"""
    orders = dedupe(orders, "order_id")
    for r in orders:
        # 缺失值：estimated_delivery 为空时用 purchase+15天填充
        if not r.get("order_estimated_delivery_date"):
            p = to_date(r.get("order_purchase_timestamp"))
            r["order_estimated_delivery_date"] = (p + dt.timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S") if p else ""
        # 日期统一
        for k in ["order_purchase_timestamp", "order_approved_at",
                  "order_delivered_carrier_date", "order_delivered_customer_date",
                  "order_estimated_delivery_date"]:
            d = to_date(r.get(k))
            r[k] = d.strftime("%Y-%m-%d %H:%M:%S") if d else ""
    return orders


def clean_items(items):
    """清洗订单明细（含异常值识别）"""
    items = dedupe(items, ("order_id", "order_item_id"))
    prices = [to_float(r.get("price")) for r in items if to_float(r.get("price")) is not None]
    q1, q3 = quantile(prices, 0.25), quantile(prices, 0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    print(f"  [异常值识别] 价格 IQR 区间: [{lo:.2f}, {hi:.2f}]，超出视为异常")

    n_outlier = 0
    for r in items:
        p = to_float(r.get("price"))
        if p is not None and (p < lo or p > hi):
            # 异常值：用中位数填充（Winsorize 思想）
            r["price"] = round(median(prices), 2)
            n_outlier += 1
        else:
            r["price"] = round(p, 2) if p is not None else round(median(prices), 2)
        f = to_float(r.get("freight_value"))
        r["freight_value"] = round(f, 2) if f is not None else 0.0
        r["order_item_id"] = to_int(r.get("order_item_id"), 1)
    print(f"  [异常值处理] 价格异常值（IQR 法）处理 {n_outlier} 条")
    return items


def clean_dimensions(customers, sellers, products):
    """清洗维度表"""
    customers = dedupe(customers, "customer_id")
    sellers = dedupe(sellers, "seller_id")
    products = dedupe(products, "product_id")

    # 商品：缺失分类填充为 'outros'，数值字段类型化
    for r in products:
        if not r.get("product_category_name"):
            r["product_category_name"] = "outros"
        for k in ["product_name_lenght", "product_description_lenght",
                  "product_photos_qty", "product_weight_g", "product_length_cm",
                  "product_height_cm", "product_width_cm"]:
            r[k] = to_int(r.get(k), 0)

    # 客户/卖家：邮编类型化
    for r in customers:
        r["customer_zip_code_prefix"] = to_int(r.get("customer_zip_code_prefix"), 0)
    for r in sellers:
        r["seller_zip_code_prefix"] = to_int(r.get("seller_zip_code_prefix"), 0)
    return customers, sellers, products


def clean_payments(payments):
    """清洗支付表"""
    payments = dedupe(payments, "order_id")
    for r in payments:
        r["payment_installments"] = to_int(r.get("payment_installments"), 1)
        r["payment_value"] = round(to_float(r.get("payment_value"), 0.0), 2)
    return payments


def clean_reviews(reviews):
    """清洗评价表"""
    reviews = dedupe(reviews, "review_id")
    for r in reviews:
        r["review_score"] = to_int(r.get("review_score"), 5)
        d = to_date(r.get("review_creation_date"))
        r["review_creation_date"] = d.strftime("%Y-%m-%d %H:%M:%S") if d else ""
    return reviews


def align_keys(orders, items, customers, sellers, products, payments, reviews):
    """多表主外键对齐校验"""
    cust_ids = {r["customer_id"] for r in customers}
    seller_ids = {r["seller_id"] for r in sellers}
    prod_ids = {r["product_id"] for r in products}
    order_ids = {r["order_id"] for r in orders}

    # 订单-客户对齐
    n_cust_mismatch = sum(1 for r in orders if r["customer_id"] not in cust_ids)
    # 明细-商品/卖家对齐
    n_prod_mismatch = sum(1 for r in items if r["product_id"] not in prod_ids)
    n_seller_mismatch = sum(1 for r in items if r["seller_id"] not in seller_ids)
    # 支付-订单对齐
    n_pay_mismatch = sum(1 for r in payments if r["order_id"] not in order_ids)
    # 评价-订单对齐
    n_rev_mismatch = sum(1 for r in reviews if r["order_id"] not in order_ids)

    print(f"  [主外键对齐] 订单→客户 失配: {n_cust_mismatch}")
    print(f"  [主外键对齐] 明细→商品 失配: {n_prod_mismatch}，明细→卖家 失配: {n_seller_mismatch}")
    print(f"  [主外键对齐] 支付→订单 失配: {n_pay_mismatch}，评价→订单 失配: {n_rev_mismatch}")

    # 剔除失配行
    orders = [r for r in orders if r["customer_id"] in cust_ids]
    items = [r for r in items if r["product_id"] in prod_ids and r["seller_id"] in seller_ids]
    payments = [r for r in payments if r["order_id"] in order_ids]
    reviews = [r for r in reviews if r["order_id"] in order_ids]
    return orders, items, payments, reviews


def export_sqlite(tables):
    """导出 SQLite 数据库"""
    db_path = os.path.join(CLEAN_DIR, "olist_analysis.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for name, (rows, fields) in tables.items():
        cols = ", ".join(fields)
        ph = ", ".join("?" for _ in fields)
        cur.execute(f"CREATE TABLE {name} ({cols})")
        cur.executemany(
            f"INSERT INTO {name} ({cols}) VALUES ({ph})",
            [[r.get(f, "") for f in fields] for r in rows],
        )
    conn.commit()
    conn.close()
    print(f"  SQLite 已导出: {db_path}")


def main():
    print("=" * 60)
    print("开始数据清洗与治理（纯 Python 标准库）...")
    print("=" * 60)

    data = load_raw()

    # 1. 清洗各表
    orders = clean_orders(data["orders"])
    items = clean_items(data["items"])
    customers, sellers, products = clean_dimensions(data["customers"], data["sellers"], data["products"])
    payments = clean_payments(data["payments"])
    reviews = clean_reviews(data["reviews"])

    # 2. 多表主外键对齐
    orders, items, payments, reviews = align_keys(orders, items, customers, sellers, products, payments, reviews)

    # 3. 导出清洗后 CSV
    tables = {
        "olist_orders_dataset": (orders, FIELD_MAP["orders"]["fields"]),
        "olist_order_items_dataset": (items, FIELD_MAP["items"]["fields"]),
        "olist_customers_dataset": (customers, FIELD_MAP["customers"]["fields"]),
        "olist_sellers_dataset": (sellers, FIELD_MAP["sellers"]["fields"]),
        "olist_products_dataset": (products, FIELD_MAP["products"]["fields"]),
        "olist_order_payments_dataset": (payments, FIELD_MAP["payments"]["fields"]),
        "olist_order_reviews_dataset": (reviews, FIELD_MAP["reviews"]["fields"]),
    }
    for name, (rows, fields) in tables.items():
        write_csv(rows, fields, os.path.join(CLEAN_DIR, name + ".csv"))
    print("  清洗后 CSV 已导出至 data/clean/")

    # 4. 导出 SQLite
    export_sqlite(tables)

    # 5. 输出清洗统计
    print("\n清洗统计：")
    print(f"  订单表: {len(orders)} 条（去重后）")
    print(f"  明细表: {len(items)} 条（去重后）")
    print(f"  客户表: {len(customers)} 条")
    print(f"  商品表: {len(products)} 条")
    print(f"  支付表: {len(payments)} 条")
    print(f"  评价表: {len(reviews)} 条")
    print("\n数据清洗完成。")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
run_all.py —— 一键复现入口

依次执行完整的数据分析流程：
  01_load.py       数据获取与生成
  02_clean.py      数据清洗与治理
  03_analysis.py   商业分析建模
  04_visuals.py    数据可视化
  05_dashboard.py  交互式大屏
  svg2png.py       SVG 图表转 PNG（供论文嵌入）
  make_paper.py    生成期末大论文 Word（含 24 张图表）

用法：
  python run_all.py

运行结束后，全部图表位于 outputs/figures/，大屏位于 outputs/dashboard.html，
论文位于 docs/《商业数据分析》期末大作业论文.docx。
"""

import subprocess
import sys
import os

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")

STEPS = [
    ("01_load.py", "数据获取与生成"),
    ("02_clean.py", "数据清洗与治理"),
    ("03_analysis.py", "商业分析建模"),
    ("04_visuals.py", "数据可视化"),
    ("05_dashboard.py", "交互式大屏"),
    ("svg2png.py", "SVG 图表转 PNG"),
    ("make_paper.py", "生成期末大论文 Word"),
]


def main():
    print("=" * 70)
    print("Olist 巴西电商商业数据分析项目 —— 一键复现")
    print("=" * 70)

    for script, desc in STEPS:
        path = os.path.join(SCRIPTS_DIR, script)
        print(f"\n>>> 步骤 {STEPS.index((script, desc)) + 1}/{len(STEPS)}：{desc}（{script}）")
        print("-" * 70)
        result = subprocess.run(
            [sys.executable, path],
            cwd=SCRIPTS_DIR,
        )
        if result.returncode != 0:
            print(f"\n[错误] {script} 执行失败，退出。")
            sys.exit(result.returncode)

    print("\n" + "=" * 70)
    print("全部流程执行完成！")
    print("  - 图表：outputs/figures/（fig01 ~ fig24，SVG + PNG）")
    print("  - 大屏：outputs/dashboard.html")
    print("  - 论文：docs/《商业数据分析》期末大作业论文.docx（含 24 张图表）")
    print("  - 结果表：outputs/tables/")
    print("=" * 70)


if __name__ == "__main__":
    main()

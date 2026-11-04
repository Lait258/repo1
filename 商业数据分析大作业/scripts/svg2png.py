# -*- coding: utf-8 -*-
"""svg2png.py —— 用无头浏览器把 SVG 批量转 PNG（供论文嵌入）

依赖：本机需装有 Edge 或 Chrome 浏览器（用于无头截图转换 SVG→PNG）。
若找不到浏览器，将跳过 PNG 转换（此时论文仍可生成，但正文图表不嵌入）。
说明：核心的 01~05 脚本（数据/图表 SVG/大屏）均为纯 Python 标准库，不依赖浏览器。
"""
import os, subprocess, glob, sys, re

# 常见浏览器路径（按优先级探测）
BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "figures")
PNG_DIR = os.path.join(FIG_DIR, "png")


def find_browser():
    """探测可用的浏览器可执行文件"""
    for p in BROWSER_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def read_svg_size(svg_path):
    """从 SVG 读取实际宽高（像素），用于设置无头浏览器窗口尺寸，避免裁切/滚动条。"""
    with open(svg_path, "r", encoding="utf-8") as f:
        head = f.read(2000)
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', head)
    if m:
        return int(float(m.group(1))), int(float(m.group(2)))
    m = re.search(r'<svg[^>]*\bheight="([\d.]+)"[^>]*\bwidth="([\d.]+)"', head)
    if m:
        return int(float(m.group(2))), int(float(m.group(1)))
    return 800, 520


def convert_all():
    browser = find_browser()
    if not browser:
        print("[提示] 未找到 Edge/Chrome 浏览器，跳过 SVG→PNG 转换（论文正文图表将不嵌入）。")
        print("[提示] 核心图表 SVG 与大屏 HTML 已正常生成，不影响主要成果。")
        return False

    os.makedirs(PNG_DIR, exist_ok=True)
    svgs = sorted(glob.glob(os.path.join(FIG_DIR, "*.svg")))
    print(f"待转换 SVG 数量: {len(svgs)}（使用浏览器: {os.path.basename(browser)}）")
    ok, fail = 0, []
    for s in svgs:
        name = os.path.basename(s).replace(".svg", ".png")
        out = os.path.join(PNG_DIR, name)
        if os.path.exists(out) and os.path.getsize(out) > 0:
            ok += 1
            continue
        # 动态读取 SVG 真实尺寸，避免窗口尺寸不匹配导致的裁切/色块
        w, h = read_svg_size(s)
        url = "file:///" + s.replace("\\", "/")
        try:
            subprocess.run(
                [browser, "--headless", "--disable-gpu", f"--screenshot={out}",
                 f"--window-size={w},{h}", "--hide-scrollbars", url],
                capture_output=True, timeout=60,
            )
        except Exception:
            fail.append(name)
            continue
        if os.path.exists(out) and os.path.getsize(out) > 0:
            ok += 1
        else:
            fail.append(name)
    print(f"成功 {ok} 张, 失败 {len(fail)} 张")
    if fail:
        print("失败:", fail)
    return ok > 0


if __name__ == "__main__":
    convert_all()

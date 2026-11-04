# -*- coding: utf-8 -*-
"""
make_paper.py —— 基于模板生成期末大论文 Word 文档

流程：
1. 读取模板 docx（保留校徽图、封面信息表、评分表、章节结构）
2. 填充封面信息（题目、学院、专业班级、学号、姓名、完成日期）
3. 删除红色提示文字，填充论文正文内容
4. 输出到 docs/ 目录

采用纯 Python 标准库（zipfile + xml）操作 docx 的 XML，
保证任何环境零依赖可复现。
"""

import os
import re
import shutil
import zipfile
import copy
import xml.etree.ElementTree as ET

from paper_content import (
    PAPER_TITLE, COVER, AUTHOR, AUTHOR_UNIT,
    ABSTRACT, KEYWORDS, SECTIONS, REFERENCES,
    APPENDIX_CODE, APPENDIX_REPO, APPENDIX_FIGURES,
)

# 路径
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = r"F:\Users\user\Desktop\作业\商业数据分析\5、《商业数据分析》 - 期末大作业模板.docx"
OUTPUT = os.path.join(BASE, "docs", "《商业数据分析》期末大作业论文.docx")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# 图表 PNG 目录
PNG_DIR = os.path.join(BASE, "outputs", "figures", "png")

# ===========================================================================
# 图表嵌入方案：{二级标题 heading: [(图片文件名, 图题), ...]}
# 图题编号按 SECTIONS 遍历顺序（正文出现顺序）依次递增，
# 下面每个图题编号在运行时由 build_document 自动重排为连续序号。
# ===========================================================================
FIGURES = {
    # 5.1 数据探索性分析
    "数据探索性分析": [
        ("fig01_多指标趋势图.png", "GMV、订单量、客户数多指标趋势图"),
        ("fig02_订单状态饼图.png", "订单状态占比饼图"),
        ("fig03_支付方式圆环图.png", "支付方式占比圆环图"),
    ],
    # 5.2 可视化模板复现
    "可视化模板复现": [
        ("fig04_分类销售额柱形图.png", "商品分类销售额 TOP10 柱形图"),
        ("fig05_各州销售额横向条形图.png", "各州销售额横向条形图"),
        ("fig06_月度订单量柱形图.png", "月度订单量柱形图"),
        ("fig07_各州订单状态堆积柱形图.png", "各州订单状态堆积柱形图"),
        ("fig08_月度GMV折线图.png", "月度 GMV 折线图"),
        ("fig09_累计销售额面积图.png", "累计销售额面积图"),
        ("fig10_GMV与环比组合图.png", "GMV 与环比组合图"),
        ("fig11_价格运费散点图.png", "价格与运费散点图"),
        ("fig12_分类能力雷达图.png", "商品分类能力雷达图"),
        ("fig13_GMV瀑布图.png", "GMV 瀑布图"),
        ("fig14_GMV目标仪表盘.png", "GMV 目标完成度仪表盘"),
    ],
    # 5.3 业务模型图
    "业务模型图": [
        ("fig15_帕累托ABC分类图.png", "商品分类帕累托 ABC 分类图"),
        ("fig16_波士顿矩阵气泡图.png", "波士顿矩阵气泡图"),
        ("fig17_RFM客户散点图.png", "RFM 客户价值散点图"),
        ("fig18_RFM八分类分布柱状图.png", "RFM 八分类分布柱状图"),
        ("fig19_同期群留存热力图.png", "同期群留存率热力图"),
        ("fig20_关联规则提升度条形图.png", "关联规则提升度条形图"),
        ("fig21_时间序列预测图.png", "时间序列预测图（含置信区间）"),
        ("fig22_订单转化漏斗图.png", "订单转化漏斗图"),
        ("fig23_环比同比对比折线图.png", "环比同比对比折线图"),
        ("fig24_客户留存曲线图.png", "客户留存曲线图"),
    ],
}

# WordprocessingML 命名空间
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_NS = {"w": W}
ET.register_namespace("w", W)


def qn(tag):
    """生成带命名空间的标签"""
    return f"{{{W}}}{tag}"


# ===========================================================================
# 工具函数：构建段落/文本
# ===========================================================================
def make_run(text, font_ea="宋体", font_ascii="Times New Roman", size=None,
             bold=False, color=None, underline=False):
    """构建一个 run（文本片段）元素"""
    r = ET.Element(qn("r"))
    rPr = ET.SubElement(r, qn("rPr"))
    rFonts = ET.SubElement(rPr, qn("rFonts"))
    rFonts.set(qn("ascii"), font_ascii)
    rFonts.set(qn("hAnsi"), font_ascii)
    rFonts.set(qn("eastAsia"), font_ea)
    rFonts.set(qn("hint"), "eastAsia")
    if size:
        sz = ET.SubElement(rPr, qn("sz"))
        sz.set(qn("val"), str(size * 2))  # 半磅
        szCs = ET.SubElement(rPr, qn("szCs"))
        szCs.set(qn("val"), str(size * 2))
    if bold:
        ET.SubElement(rPr, qn("b"))
    if color:
        c = ET.SubElement(rPr, qn("color"))
        c.set(qn("val"), color)
    if underline:
        u = ET.SubElement(rPr, qn("u"))
        u.set(qn("val"), "single")
    t = ET.SubElement(r, qn("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


def make_para(runs=None, jc=None, indent_first=None, line=None, line_rule="auto"):
    """构建段落元素"""
    p = ET.Element(qn("p"))
    pPr = ET.SubElement(p, qn("pPr"))
    if jc:
        j = ET.SubElement(pPr, qn("jc"))
        j.set(qn("val"), jc)
    if indent_first:
        ind = ET.SubElement(pPr, qn("ind"))
        ind.set(qn("firstLine"), str(indent_first))
    if line:
        sp = ET.SubElement(pPr, qn("spacing"))
        sp.set(qn("line"), str(line))
        sp.set(qn("lineRule"), line_rule)
    if runs:
        for r in runs:
            p.append(r)
    return p


def make_heading_para(text, level=2):
    """构建章节标题段落（黑体加粗）"""
    if level == 1:
        # 一级标题：四号黑体
        size = 14
    elif level == 2:
        # 二级标题：小四黑体
        size = 12
    else:
        size = 12
    return make_para(
        [make_run(text, font_ea="黑体", font_ascii="Times New Roman", size=size, bold=True)],
        line=360, line_rule="auto",
    )


def make_body_para(text, indent_first=480, line=360):
    """构建正文段落（小四宋体，1.5倍行距，首行缩进2字符）"""
    return make_para(
        [make_run(text, font_ea="宋体", font_ascii="Times New Roman", size=12)],
        indent_first=indent_first, line=line, line_rule="auto",
    )


# ===========================================================================
# 图片嵌入：把 PNG 加入 docx，构建 drawing 段落
# ===========================================================================
# 命名空间（图片相关）
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
ET.register_namespace("a", A_NS)
ET.register_namespace("pic", PIC_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("wp", WP_NS)

# 图片信息收集（name -> (rId, emu 宽高)）
IMAGE_RELS = []


def make_image_para(png_name, caption, emu_w=5715000, emu_h=3715000):
    """
    构建含图片 + 图题的段落列表
    png_name: PNG 文件名（在 outputs/figures/png/ 下）
    caption: 图题文字（如 "图1 ..."）
    emu_w/emu_h: 图片显示尺寸（EMU，默认约 15cm × 9.75cm，即 800:520 比例）
    """
    # 若 PNG 不存在（未运行 svg2png.py 或浏览器缺失），仅输出图题文字，跳过图片
    png_path = os.path.join(PNG_DIR, png_name)
    if not os.path.exists(png_path):
        return [make_para(
            [make_run(caption, font_ea="宋体", font_ascii="Times New Roman", size=10.5, bold=True)],
            jc="center", line=360,
        )]

    # 分配 rId
    r_id = f"rIdImg{len(IMAGE_RELS) + 100}"
    IMAGE_RELS.append((r_id, png_name))

    paras = []

    # 图片段落（居中，无缩进）
    p_img = ET.Element(qn("p"))
    pPr = ET.SubElement(p_img, qn("pPr"))
    jc = ET.SubElement(pPr, qn("jc"))
    jc.set(qn("val"), "center")
    spacing = ET.SubElement(pPr, qn("spacing"))
    spacing.set(qn("before"), "120")
    spacing.set(qn("after"), "60")
    run = ET.SubElement(p_img, qn("r"))
    drawing = ET.SubElement(run, qn("drawing"))
    inline = ET.SubElement(drawing, f"{{{WP_NS}}}inline")
    inline.set("distT", "0"); inline.set("distB", "0")
    inline.set("distL", "0"); inline.set("distR", "0")
    # extent
    extent = ET.SubElement(inline, f"{{{WP_NS}}}extent")
    extent.set("cx", str(emu_w)); extent.set("cy", str(emu_h))
    # effectExtent
    eff = ET.SubElement(inline, f"{{{WP_NS}}}effectExtent")
    eff.set("l", "0"); eff.set("t", "0"); eff.set("r", "0"); eff.set("b", "0")
    # docPr
    docPr = ET.SubElement(inline, f"{{{WP_NS}}}docPr")
    docPr.set("id", str(len(IMAGE_RELS) + 50))
    docPr.set("name", png_name)
    # cNvGraphicFramePr
    cNv = ET.SubElement(inline, f"{{{WP_NS}}}cNvGraphicFramePr")
    ET.SubElement(cNv, f"{{{A_NS}}}graphicFrameLocks").set("noChangeAspect", "1")
    # graphic
    graphic = ET.SubElement(inline, f"{{{A_NS}}}graphic")
    graphicData = ET.SubElement(graphic, f"{{{A_NS}}}graphicData")
    graphicData.set("uri", PIC_NS)
    pic = ET.SubElement(graphicData, f"{{{PIC_NS}}}pic")
    nvPicPr = ET.SubElement(pic, f"{{{PIC_NS}}}nvPicPr")
    cNvPr = ET.SubElement(nvPicPr, f"{{{PIC_NS}}}cNvPr")
    cNvPr.set("id", str(len(IMAGE_RELS) + 50)); cNvPr.set("name", png_name)
    cNvPicPr = ET.SubElement(nvPicPr, f"{{{PIC_NS}}}cNvPicPr")
    ET.SubElement(cNvPicPr, f"{{{A_NS}}}picLocks").set("noChangeAspect", "1")
    blipFill = ET.SubElement(pic, f"{{{PIC_NS}}}blipFill")
    blip = ET.SubElement(blipFill, f"{{{A_NS}}}blip")
    blip.set(f"{{{R_NS}}}embed", r_id)
    stretch = ET.SubElement(blipFill, f"{{{A_NS}}}stretch")
    ET.SubElement(stretch, f"{{{A_NS}}}fillRect")
    spPr = ET.SubElement(pic, f"{{{PIC_NS}}}spPr")
    xfrm = ET.SubElement(spPr, f"{{{A_NS}}}xfrm")
    off = ET.SubElement(xfrm, f"{{{A_NS}}}off"); off.set("x", "0"); off.set("y", "0")
    ext = ET.SubElement(xfrm, f"{{{A_NS}}}ext"); ext.set("cx", str(emu_w)); ext.set("cy", str(emu_h))
    prstGeom = ET.SubElement(spPr, f"{{{A_NS}}}prstGeom")
    prstGeom.set("prst", "rect")
    ET.SubElement(prstGeom, f"{{{A_NS}}}avLst")
    paras.append(p_img)

    # 图题段落（居中，五号宋体加粗）
    paras.append(make_para(
        [make_run(caption, font_ea="宋体", font_ascii="Times New Roman", size=10.5, bold=True)],
        jc="center", line=360,
    ))
    return paras


# ===========================================================================
# 主流程
# ===========================================================================
def build_document():
    global IMAGE_RELS
    IMAGE_RELS = []  # 重置图片关系列表

    # 1. 读取模板所有内容
    zin = zipfile.ZipFile(TEMPLATE)
    names = zin.namelist()

    # 读取 document.xml
    doc_xml = zin.read("word/document.xml").decode("utf-8")
    root = ET.fromstring(doc_xml)
    body = root.find(qn("body"))

    # 收集需要保留的内容（封面图、表格）和需要替换的段落
    paragraphs = body.findall(qn("p"))
    tables = body.findall(qn("tbl"))
    sectPr = body.find(qn("sectPr"))

    # 2. 处理：识别各段落角色
    # 段落索引到文本
    def para_text(p):
        return "".join(t.text or "" for t in p.findall(f".//{qn('t')}"))

    texts = [para_text(p) for p in paragraphs]

    # 3. 构建新的 body 内容：保留封面（段落0~9 + 评分表），替换正文
    # 封面段落：0(图) 1(空) 2(标题商业数据分析) 3-8(填空) 9(数据科学学院)
    # 表格：评分表
    # 正文：段落 10 之后（红色提示 + 章节结构）

    # 先填充封面信息（题目等）
    cover_map = {
        "题　　目：": COVER["title"],
        "学　　院：": COVER["college"],
        "专业班级：": COVER["class"],
        "学　　号：": COVER["student_id"],
        "姓　　名：": COVER["name"],
        "完成日期：": COVER["date"],
    }

    for p in paragraphs:
        t = para_text(p)
        for key, val in cover_map.items():
            if key in t and val:
                # 在该段落末尾追加内容（替换下划线后的空格）
                # 找到下划线 run 后插入新 run
                runs = p.findall(qn("r"))
                # 在段落中追加一个带下划线的 run 填入值
                new_run = make_run(" " + val, font_ea="楷体_GB2312", font_ascii="楷体_GB2312",
                                   size=14, underline=True)
                p.append(new_run)
                break

    # 4. 删除红色提示段落（正文部分），保留章节标题结构
    # 红色提示段落的文本特征
    red_markers = ["论文题目（三黑居中", "作者（五号宋体）", "（嘉兴大学", "摘要（四号黑体）",
                   "关键词（四号黑体）", "注意：全文红色字体均可删除"]

    # 找到正文起始位置（"论文题目"提示段）
    body_start = None
    for i, t in enumerate(texts):
        if "论文题目（三黑居中" in t:
            body_start = i
            break

    # 构建正文新段落列表（替换 body_start 及之后的所有段落）
    new_body_paras = []

    # ========== 论文题目（三黑居中）==========
    new_body_paras.append(make_para(
        [make_run(PAPER_TITLE, font_ea="黑体", font_ascii="Times New Roman", size=16, bold=True)],
        jc="center", line=360,
    ))
    # 作者（五号宋体）
    new_body_paras.append(make_para(
        [make_run(AUTHOR, font_ea="宋体", font_ascii="Times New Roman", size=10.5)],
        jc="center", line=360,
    ))
    # 单位（五号宋体）
    new_body_paras.append(make_para(
        [make_run(f"（{AUTHOR_UNIT}）", font_ea="宋体", font_ascii="Times New Roman", size=10.5)],
        jc="center", line=360,
    ))
    new_body_paras.append(make_para(line=360))  # 空行

    # ========== 摘要 ==========
    new_body_paras.append(make_para(
        [make_run("摘要", font_ea="黑体", font_ascii="Times New Roman", size=14, bold=True)],
        indent_first=480, line=360,
    ))
    new_body_paras.append(make_body_para(ABSTRACT, indent_first=480, line=360))

    # ========== 关键词 ==========
    new_body_paras.append(make_para(
        [make_run("关键词", font_ea="黑体", font_ascii="Times New Roman", size=14, bold=True)],
        indent_first=480, line=360,
    ))
    new_body_paras.append(make_body_para(KEYWORDS, indent_first=480, line=360))
    new_body_paras.append(make_para(line=360))  # 空行

    # ========== 正文各章节 ==========
    chapter_num = 0
    fig_num = 0  # 图表连续编号
    for chapter_title, subsections in SECTIONS.items():
        chapter_num += 1
        # 一级章节标题（四号黑体，居中或左对齐）
        new_body_paras.append(make_para(
            [make_run(f"{chapter_num}  {chapter_title}", font_ea="黑体", font_ascii="Times New Roman",
                      size=14, bold=True)],
            jc="center", line=360,
        ))
        for sub in subsections:
            # 二级标题
            new_body_paras.append(make_heading_para(sub["heading"], level=2))
            # 正文段落
            for para in sub["paragraphs"]:
                new_body_paras.append(make_body_para(para, indent_first=480, line=360))
            # 该小节后插入图表（若有），图题编号自动连续
            if sub["heading"] in FIGURES:
                for png_name, caption in FIGURES[sub["heading"]]:
                    fig_num += 1
                    full_caption = f"图{fig_num}  {caption}"
                    new_body_paras.extend(make_image_para(png_name, full_caption))

    # ========== 参考文献 ==========
    new_body_paras.append(make_para(
        [make_run("参考文献", font_ea="黑体", font_ascii="Times New Roman", size=14, bold=True)],
        jc="center", line=360,
    ))
    for ref in REFERENCES:
        new_body_paras.append(make_body_para(ref, indent_first=0, line=360))

    # ========== 附录 ==========
    new_body_paras.append(make_para(
        [make_run("附录", font_ea="黑体", font_ascii="Times New Roman", size=14, bold=True)],
        jc="center", line=360,
    ))
    new_body_paras.append(make_heading_para("A  核心代码片段", level=2))
    for line_text in APPENDIX_CODE.split("\n"):
        new_body_paras.append(make_para(
            [make_run(line_text, font_ea="宋体", font_ascii="Consolas", size=10.5)],
            line=300,
        ))
    new_body_paras.append(make_heading_para("B  Gitee/GitHub 仓库链接与目录结构", level=2))
    for line_text in APPENDIX_REPO.split("\n"):
        new_body_paras.append(make_para(
            [make_run(line_text, font_ea="宋体", font_ascii="Consolas", size=10.5)],
            line=300,
        ))
    new_body_paras.append(make_heading_para("C  图表索引", level=2))
    for line_text in APPENDIX_FIGURES.split("\n"):
        new_body_paras.append(make_para(
            [make_run(line_text, font_ea="宋体", font_ascii="Times New Roman", size=10.5)],
            line=300,
        ))

    # 5. 重新组装 body：封面段落（0~body_start-1）+ 表格 + 新正文 + sectPr
    # 清理 body 现有内容
    for child in list(body):
        body.remove(child)

    # 添加封面段落（保留图、标题、填空等，正文起始之前的部分）
    for p in paragraphs[:body_start]:
        body.append(p)

    # 添加评分表（如果存在）
    for tbl in tables:
        body.append(copy.deepcopy(tbl))

    # 添加新正文段落
    for p in new_body_paras:
        body.append(p)

    # 添加 sectPr
    if sectPr is not None:
        body.append(copy.deepcopy(sectPr))

    # 6. 写回 document.xml
    new_doc_xml = ET.tostring(root, encoding="unicode")

    # 6.1 处理图片：更新 document.xml.rels，加入图片关系
    rels_name = "word/_rels/document.xml.rels"
    rels_xml = zin.read(rels_name).decode("utf-8")
    rels_root = ET.fromstring(rels_xml)
    # 找现有最大 rId 编号
    existing_ids = [r.get("Id") for r in rels_root if r.get("Id")]
    max_num = 0
    for rid in existing_ids:
        m = re.match(r"rId(\d+)", rid or "")
        if m:
            max_num = max(max_num, int(m.group(1)))
    # 追加图片关系
    img_rid_map = {}  # 原 rId -> 实际 rId
    for i, (orig_rid, png_name) in enumerate(IMAGE_RELS):
        new_num = max_num + i + 1
        actual_rid = f"rId{new_num}"
        img_rid_map[orig_rid] = actual_rid
        rel = ET.SubElement(rels_root, f"{{{R_NS}}}Relationship")
        rel.set("Id", actual_rid)
        rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
        rel.set("Target", f"media/{png_name}")
    new_rels_xml = ET.tostring(rels_root, encoding="unicode")

    # 替换 document.xml 中的占位 rId（rIdImgXXX -> 实际 rId）
    for orig_rid, actual_rid in img_rid_map.items():
        new_doc_xml = new_doc_xml.replace(f'"{orig_rid}"', f'"{actual_rid}"')

    # 7. 重新打包 docx
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in names:
            if name == "word/document.xml":
                zout.writestr(name, new_doc_xml)
            elif name == rels_name:
                zout.writestr(name, new_rels_xml)
            else:
                zout.writestr(name, zin.read(name))
        # 写入图片文件
        for orig_rid, png_name in IMAGE_RELS:
            png_path = os.path.join(PNG_DIR, png_name)
            zout.writestr(f"word/media/{png_name}", open(png_path, "rb").read())

    zin.close()
    print(f"论文已生成：{OUTPUT}（含 {len(IMAGE_RELS)} 张图表）")


if __name__ == "__main__":
    build_document()

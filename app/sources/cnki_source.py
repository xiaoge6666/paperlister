# -*- coding: utf-8 -*-
"""知网题录解析：粘贴详情页/列表页文本 → Paper。

用法（半自动）：用户在自己浏览器（保持 IP 登录）打开知网详情页，
Ctrl+A 全选复制 → 粘贴到软件文本框 → parse_detail_text()。
"""
import re

from ..models import Paper


FIELD_KEYS = [
    "作者", "导师", "学科专业", "专业", "学位授予单位", "培养单位", "学位年度", "年度",
    "DOI", "doi", "摘要", "关键词", "关键字", "分类号", "来源", "刊名", "发表时间",
    "出版时间", "中图分类号", "网络首发", "文献来源", "更新时间", "入库时间", "专辑",
    "专题", "主办单位", "出版地", "编辑", "引用格式", "下载", "阅读", "分享",
]


def _clean(t):
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _find(text, keys, window=200):
    """找关键词后取值，截断到下一个字段词为止。"""
    for k in keys:
        i = text.find(k)
        if i < 0:
            continue
        tail = text[i + len(k):i + len(k) + window]
        best = len(tail)
        for fk in FIELD_KEYS:
            j = tail.find(fk)
            if 0 <= j < best:
                best = j
        tail = tail[:best]
        tail = tail.strip(" ：:：,，。;；\"'“”‘’\n\r\t")
        tail = _clean(tail)
        if tail:
            return tail
    return ""


def _find_year(text):
    m = re.search(r"(19|20)\d{2}\s*[年.]", text)
    if m:
        return m.group(0).strip("年.").strip()
    m2 = re.search(r"(19|20)\d{2}", text)
    return m2.group(0) if m2 else ""


def parse_detail_text(text):
    """解析知网详情页全文文本 → Paper（学位论文/期刊文章通用）。"""
    text = re.sub(r"\r\n?", "\n", text)
    title = ""
    m = re.search(r"<title>(.*?)</title>", text, re.S)
    if m:
        title = _clean(re.sub(r"<[^>]+>", "", m.group(1)))
        title = re.sub(r"[-_—|].*?知网.*$", "", title).strip()
        title = re.sub(r"[-_—|].*$", "", title).strip()
    if not title or len(title) < 4:
        # 详情页通常标题在开头大字
        for line in text.split("\n"):
            line = line.strip()
            if 6 <= len(line) <= 120 and not re.search(r"(作者|导师|单位|摘要|关键词|下载|阅读|分享|中图|分类|DOI|文献|网络|时间|机构|来源)", line):
                title = line
                break

    author = _find(text, ["作者：", "作者:", "作者 "])
    thesis_type = ""
    if re.search(r"博士", text) and re.search(r"学位论文", text):
        thesis_type = "博士"
    elif re.search(r"硕士", text) and re.search(r"学位论文", text):
        thesis_type = "硕士"
    is_thesis = thesis_type != "" or ("导师" in text and "学位论文" in text)

    if is_thesis:
        advisor = _find(text, ["导师：", "导师:", "导师 "])
        dept = _find(text, ["学科专业：", "学科专业:", "专业：", "专业:"])
        unit = _find(text, ["学位授予单位：", "学位授予单位:", "培养单位："])
        unit = re.sub(r"(博士|硕士)学位?论文.*$", "", unit).strip()
        pub = unit or dept
        tags = ["知网", "学位论文"]
        if dept:
            tags.append(dept[:12])
    else:
        advisor = ""
        pub = _find(text, ["来源：", "来源:", "刊名：", "刊名:", "期刊："])
        tags = ["知网", "期刊文章"]

    year = _find_year(text)
    doi = _find(text, ["DOI：", "DOI:", "doi："])
    if not doi:
        m = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", text)
        doi = m.group(0) if m else ""
    abstract = ""
    i = text.find("摘要")
    if i >= 0:
        abstract = _clean(text[i + 2:i + 1000])
        abstract = re.split(r"(关键词|【关键词】|关键字|【关键字】)", abstract)[0].strip()
    kw = ""
    m = re.search(r"(关键词|【关键词】)\s*[:：]?\s*(.{5,120})", text)
    if m:
        kw = _clean(m.group(2))
        for sep in ("；", ";", " "):
            if sep in kw:
                kw = kw.split(sep)[0]
                break
    if kw:
        tags.append(kw[:20])

    creators = []
    if author:
        for a in re.split(r"[、,，;；]", author):
            a = a.strip()
            if a and len(a) <= 12:
                creators.append({"creatorType": "author", "lastName": a})
    if advisor:
        for a in re.split(r"[、,，;；]", advisor):
            a = a.strip()
            if a and len(a) <= 12:
                creators.append({"creatorType": "contributor", "lastName": a})

    return Paper(
        title=title[:300],
        creators=creators[:12],
        date=year,
        publication=pub[:120],
        doi=doi[:80],
        abstract=abstract[:3000],
        source="CNKI",
        thesis_type=thesis_type,
        tags=tags,
    )

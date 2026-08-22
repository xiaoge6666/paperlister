# -*- coding: utf-8 -*-
"""Google Scholar 抓取：cookie 反爬破解法（google.com 拿 NID → scholar 查询）。"""
import re
import time
import html as htmllib

from ..net import UA
from ..models import Paper

import requests


def _session(settings):
    px = settings.proxy_dict
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    try:
        s.get("https://www.google.com/", proxies=px, timeout=40)
    except Exception:
        pass  # 拿不到 NID 也试一把
    return s


def _parse_gsr(text):
    """解析 Scholar 结果页 -> list[dict]"""
    out = []
    for b in text.split('<div class="gs_r gs_or gs_scl"')[1:]:
        m = re.search(r'<h3 class="gs_rt".*?>(?:<span class="gs_ctg2">\[(\w+)\]</span>)?\s*<a[^>]*>(.*?)</a>', b, re.S)
        title = ""
        if m:
            title = htmllib.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        m2 = re.search(r'<div class="gs_a">(.*?)</div>', b, re.S)
        src = ""
        if m2:
            src = htmllib.unescape(re.sub(r"<[^>]+>", "", m2.group(1))).strip().replace("\n", " ")
        m3 = re.search(r"Cited by (\d+)", b)
        cited = int(m3.group(1)) if m3 else 0
        m4 = re.search(r'<a[^>]*href="(http[^"]+)"[^>]*>\s*\[PDF\]', b)
        pdf = m4.group(1) if m4 else ""
        if title:
            out.append({"title": title, "src": src, "cited": cited, "pdf": pdf})
    return out


def _src_parse(src):
    """gs_a 行: 作者 - 期刊, 年份 - 其他。返回 (authors, journal, year)"""
    src = src.replace("\xa0", " ")
    parts = [p.strip() for p in re.split(r"\s*-\s*", src)]
    authors = parts[0] if parts else ""
    journal = ""
    year = ""
    if len(parts) > 1:
        seg = parts[1]
        m = re.search(r"(\d{4})", seg)
        if m:
            year = m.group(1)
        j = re.sub(r",\s*\d{4}.*$", "", seg).strip()
        # 期刊段若不含常见刊名特征（如全是人名），留空让 Crossref 补全
        if j and not re.match(r"^[A-Z][a-z]+(,|\s+and|\s+et al)", j):
            journal = j
    elif len(parts) == 1:
        m = re.search(r"(\d{4})", src)
        if m:
            year = m.group(1)
    return authors, journal, year


def search(settings, queries, n=10, progress=None):
    """queries: list[str]（1-2 个查询词）"""
    if isinstance(queries, str):
        queries = [queries]
    px = settings.proxy_dict
    s = _session(settings)
    papers = []
    seen = set()
    for q in queries:
        if progress:
            progress(f"Scholar 抓取: {q}")
        try:
            r = s.get("https://scholar.google.com/scholar",
                      params={"hl": "en", "q": q}, proxies=px, timeout=50)
            if r.status_code != 200 or "gs_ri" not in r.text:
                if progress:
                    progress(f"  ⚠ Scholar 返回异常 (HTTP {r.status_code})，跳过该查询")
                time.sleep(3)
                continue
            for d in _parse_gsr(r.text)[:n]:
                key = d["title"].lower()
                if key in seen:
                    continue
                seen.add(key)
                authors, journal, year = _src_parse(d["src"])
                creators = []
                for a in re.split(r",|\s+and\s+", authors):
                    a = a.strip()
                    if not a or a == "…":
                        continue
                    if "…" in a or a.endswith(".") and len(a) < 4:
                        continue
                    parts = a.rsplit(" ", 1)
                    creators.append({
                        "creatorType": "author",
                        "firstName": parts[0] if len(parts) > 1 else "",
                        "lastName": parts[-1],
                    })
                p = Paper(
                    title=d["title"],
                    creators=creators[:12],
                    date=year,
                    publication=journal,
                    cited=d["cited"],
                    source="Scholar",
                    tags=["Scholar"],
                    url=d["pdf"] or "",
                )
                if d["pdf"]:
                    p.note = f"OA PDF: {d['pdf']}"
                papers.append(p)
        except Exception as e:
            if progress:
                progress(f"  ⚠ Scholar 查询失败: {e}")
        time.sleep(3)
    return papers

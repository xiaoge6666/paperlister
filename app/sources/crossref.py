# -*- coding: utf-8 -*-
"""Crossref：按 DOI 或标题补全题录（免费开放接口）。"""
import time

from ..net import get
from ..models import Paper

BASE = "https://api.crossref.org/works"


def _norm(item):
    """Crossref JSON -> dict 片段。"""
    title = (item.get("title") or [""])[0]
    creators = []
    for a in (item.get("author") or [])[:12]:
        fn = a.get("given", "")
        ln = a.get("family", "")
        if not ln:
            continue
        creators.append({"creatorType": "author", "firstName": fn, "lastName": ln})
    pub = ""
    for k in ("container-title", "short-container-title"):
        v = item.get(k)
        if v:
            pub = v[0] if isinstance(v, list) else v
            if pub:
                break
    date = ""
    for key in ("published-print", "published", "issued"):
        dp = item.get(key, {}).get("date-parts", [[None]])
        if dp and dp[0] and dp[0][0]:
            date = str(dp[0][0])
            break
    vol = item.get("volume", "")
    iss = item.get("issue", "")
    pages = item.get("page", "")
    abstract = re_abstract(item.get("abstract", ""))
    return {
        "title": title,
        "creators": creators,
        "date": date,
        "publication": pub,
        "volume": vol,
        "issue": iss,
        "pages": pages,
        "doi": item.get("DOI", ""),
        "url": item.get("URL", ""),
        "abstract": abstract,
    }


def re_abstract(s):
    import re
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()[:3000]


def lookup_doi(settings, doi):
    """按 DOI 查完整题录 -> Paper | None"""
    try:
        r = get(f"{BASE}/{doi}", proxies=settings.proxy_dict, timeout=45)
        if r.status_code != 200:
            return None
        item = r.json()["message"]
        d = _norm(item)
        if not d["title"]:
            return None
        p = Paper(**d, source="Crossref", tags=["Crossref"])
        return p
    except Exception:
        return None


def search_title(settings, title, n=3):
    """按标题模糊查 DOI（Scholar 无 DOI 时补全）。"""
    try:
        r = get(BASE, params={"query.bibliographic": title, "rows": n},
                proxies=settings.proxy_dict, timeout=45)
        if r.status_code != 200:
            return []
        items = r.json().get("message", {}).get("items", [])
        return [_norm(it) for it in items if it.get("title")]
    except Exception:
        return []

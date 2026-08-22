# -*- coding: utf-8 -*-
"""NCBI/PubMed 检索：esearch + esummary + efetch(摘要) + elink(PMC 标注)。"""
import time
import re
from ..net import get
from ..models import Paper

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def _api_key(settings):
    return settings["ncbi_key"] or None


def _call(settings, endpoint, params):
    px = settings.proxy_dict
    p = dict(params)
    k = _api_key(settings)
    if k:
        p["api_key"] = k
    return get(BASE + endpoint, params=p, proxies=px, timeout=60)


def esearch(settings, term, n=20):
    r = _call(settings, "esearch.fcgi", {"db": "pubmed", "term": term, "retmax": n, "retmode": "json"})
    return r.json()["esearchresult"].get("idlist", [])


def esummary(settings, pmids):
    out = {}
    for i in range(0, len(pmids), 50):
        chunk = pmids[i:i + 50]
        r = _call(settings, "esummary.fcgi", {"db": "pubmed", "id": ",".join(chunk), "retmode": "json"})
        res = r.json().get("result", {})
        for k, v in res.items():
            if k != "uids":
                out[k] = v
        time.sleep(0.4)
    return out


def efetch_abstracts(settings, pmids):
    """批量取摘要 XML -> {pmid: abstract}"""
    out = {}
    for i in range(0, len(pmids), 20):
        chunk = pmids[i:i + 20]
        r = _call(settings, "efetch.fcgi",
                  {"db": "pubmed", "id": ",".join(chunk), "retmode": "xml"})
        for pmid in chunk:
            seg = re.search(rf"<PubmedArticle>.*?<PMID[^>]*>{pmid}</PMID>.*?</PubmedArticle>",
                            r.text, re.S)
            if not seg:
                continue
            abs_parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", seg.group(0), re.S)
            clean = []
            for a in abs_parts:
                a = re.sub(r"<[^>]+>", "", a)
                a = a.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                clean.append(a.strip())
            out[pmid] = " ".join(clean)[:3000]
        time.sleep(0.4)
    return out


def elink_pmc(settings, pmid):
    r = _call(settings, "elink.fcgi", {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"})
    try:
        for ls in r.json().get("linksets", []):
            for ln in ls.get("linksetdbs", []):
                if ln["dbto"] == "pmc":
                    return ln["links"][0]
    except Exception:
        pass
    return None


def search(settings, term, n=15, progress=None):
    """完整检索：返回 Paper 列表。"""
    if progress:
        progress(f"NCBI 检索: {term}")
    pmids = esearch(settings, term, n)
    if not pmids:
        return []
    if progress:
        progress(f"命中 {len(pmids)} 条，拉取详情…")
    sums = esummary(settings, pmids[:n])
    abs_map = efetch_abstracts(settings, pmids[:n])

    papers = []
    for pid in pmids[:n]:
        s = sums.get(pid)
        if not s:
            continue
        creators = []
        for a in (s.get("authors") or []):
            name = (a.get("name") or "").strip()
            if not name:
                continue
            parts = name.rsplit(" ", 1)
            creators.append({
                "creatorType": "author",
                "firstName": parts[0] if len(parts) > 1 else "",
                "lastName": parts[-1],
            })
        doi = ""
        for aid in (s.get("articleids") or []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
        pmc = elink_pmc(settings, pid)
        p = Paper(
            title=(s.get("title") or "").strip(),
            creators=creators,
            date=(s.get("pubdate") or ""),
            publication=(s.get("fulljournalname") or s.get("source") or ""),
            volume=(s.get("volume") or ""),
            issue=(s.get("issue") or ""),
            pages=(s.get("pages") or ""),
            doi=doi,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
            abstract=abs_map.get(pid, ""),
            cited=int(s.get("citedbycount") or 0),
            source="NCBI",
            pmid=pid,
            tags=["NCBI", "PubMed"],
        )
        if pmc:
            p.tags.append(f"PMC{pmc}")
            p.note = f"PMC 可下: PMC{pmc}"
        papers.append(p)
    return papers

# -*- coding: utf-8 -*-
"""冒烟测试：验证核心模块（不依赖 GUI）。"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import Settings
from app.sources import ncbi_source, scholar_source, cnki_source, crossref

s = Settings()

print("=" * 20, "1. NCBI 检索", "=" * 20)
papers = ncbi_source.search(s, '"PP2A"[Title] AND (fung*[Title/Abstract] OR yeast*)', n=5)
for p in papers:
    print(f"  PMID {p.pmid} | {p.year} | {p.publication[:30]} | cited={p.cited} | tags={p.tags}")
    print(f"    {p.title[:80]}")

print("=" * 20, "2. Crossref DOI 补全", "=" * 20)
p = crossref.lookup_doi(s, "10.1038/nature14019")
if p:
    print(f"  {p.title[:60]} | {p.publication} {p.volume}({p.issue}):{p.pages} | {p.year}")
else:
    print("  lookup 失败")

print("=" * 20, "3. Scholar 抓取", "=" * 20)
sp = scholar_source.search(s, ["Rho GTPase Fusarium"], n=5)
for p in sp:
    print(f"  cited={p.cited} | {p.publication[:25]} | {p.year}")
    print(f"    {p.title[:70]}")

print("=" * 20, "4. 知网文本解析", "=" * 20)
demo = """白念珠菌TORC1/PP2A通过ATG磷酸化调控自噬影响生物膜形成和耐药性的研究
作者：沈佳娣  导师：魏昕  学科专业：口腔医学
学位授予单位：南京医科大学  博士学位论文
年度：2024
摘要：白念珠菌是临床念珠菌感染主因，生物膜增强耐药性。研究TORC1/PP2A通过ATG蛋白磷酸化调控自噬的机制及其对生物膜形成和耐药性的影响。
关键词：白念珠菌；TORC1；PP2A；自噬；生物膜
DOI：10.xxxx/d.cnki.gnjmu.2024.000001"""
cp = cnki_source.parse_detail_text(demo)
print(f"  标题: {cp.title}")
print(f"  作者: {[c['lastName'] for c in cp.creators]}")
print(f"  类型: {cp.thesis_type} | 学校: {cp.publication} | 年份: {cp.year} | DOI: {cp.doi}")
print(f"  tags: {cp.tags}")

print("\nSMOKE OK")

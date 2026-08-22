# -*- coding: utf-8 -*-
"""诊断：各环节耗时。"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import Settings
from app.sources import ncbi_source, scholar_source

s = Settings()
t0 = time.time()
print("== NCBI ==")
papers = ncbi_source.search(s, '"Rho GTPase"[Title/Abstract] AND Fusarium', n=5)
print(f"NCBI {len(papers)} 条, 耗时 {time.time()-t0:.1f}s")

t0 = time.time()
print("== Scholar (单查询) ==")
sp = scholar_source.search(s, ["Rho GTPase Fusarium"], n=5)
print(f"Scholar {len(sp)} 条, 耗时 {time.time()-t0:.1f}s")

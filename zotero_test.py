# -*- coding: utf-8 -*-
"""Zotero 直连只读测试。"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import Settings
from app import zotero

s = Settings()
t0 = time.time()
ok, msg = zotero.check_auth(s)
print(f"check_auth: {ok} {msg} ({time.time()-t0:.1f}s)")
if ok:
    colls = zotero.list_collections(s)
    print(f"collections: {len(colls)} 个 | 前 5: {[c['name'] for c in colls[:5]]}")
    print(f"耗时 {time.time()-t0:.1f}s")

# -*- coding: utf-8 -*-
"""Zotero API：合集查询/新建 + 批量入库（父条目 + 笔记，无附件）。"""
from .net import get, post

BASE = "https://api.zotero.org/users/{uid}/"


def _headers(settings):
    return {
        "Zotero-API-Key": settings["zotero_key"],
        "Zotero-API-Version": "3",
        "Content-Type": "application/json",
    }


def _base(settings):
    return BASE.format(uid=settings["zotero_uid"])


def check_auth(settings):
    """验证 key 可用，返回 (ok, msg)。Zotero API 直连（不走代理）。"""
    try:
        r = get(_base(settings) + "collections", params={"limit": 1},
                proxies=None, timeout=30, headers=_headers(settings))
        if r.status_code == 200:
            return True, "连接正常"
        if r.status_code == 403:
            return False, "API Key 无效 (403)"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, f"网络错误: {e}"


def list_collections(settings):
    """-> list[{key, name}]"""
    r = get(_base(settings) + "collections", params={"limit": 100},
            proxies=None, timeout=30, headers=_headers(settings))
    if r.status_code != 200:
        raise RuntimeError(f"Zotero 合集查询失败 HTTP {r.status_code}")
    return [{"key": c["key"], "name": c["data"]["name"]} for c in r.json()]


def create_collection(settings, name, parent_key=None):
    body = {"name": name}
    if parent_key:
        body["parentCollection"] = parent_key
    r = post(_base(settings) + "collections", json=body,
             proxies=None, timeout=30, headers=_headers(settings))
    if r.status_code != 201:
        raise RuntimeError(f"合集创建失败 HTTP {r.status_code}: {r.text[:300]}")
    return r.json()["key"]


def add_items(settings, papers, collection_key):
    """批量入库：父条目 + child note。返回 (成功数, 失败明细)。"""
    items = []
    for p in papers:
        items.append(p.to_zotero_item([collection_key]))
    r = post(_base(settings) + "items", json=items,
             proxies=None, timeout=120, headers=_headers(settings))
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Zotero 入库失败 HTTP {r.status_code}: {r.text[:500]}")
    res = r.json()
    ok = res.get("successful", {})
    failed = res.get("failed", {})
    keys = {}
    for idx_str, v in ok.items():
        try:
            keys[int(idx_str)] = v["key"]
        except Exception:
            pass

    # 建笔记（有内容才建）
    notes = []
    for idx, p in enumerate(papers):
        if idx in keys and (p.note or "").strip():
            notes.append({
                "itemType": "note",
                "parentItem": keys[idx],
                "note": p.note.strip(),
            })
    n_notes = 0
    if notes:
        r2 = post(_base(settings) + "items", json=notes,
                  proxies=None, timeout=120, headers=_headers(settings))
        if r2.status_code in (200, 201):
            n_notes = len(r2.json().get("successful", {}))
    fail_list = []
    for idx_str, v in failed.items():
        fail_list.append(f"#{idx_str} {v.get('message', '?')}")
    return len(keys), n_notes, fail_list

# -*- coding: utf-8 -*-
"""AI 模块测试：mock 网络调用。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import Settings
from app import ai
from app.models import Paper

s = Settings()
s["ai_key"] = ""  # 未配置
p = Paper(title="Test", publication="Nature", date="2025", abstract="some abstract")

# 1. 未配置 → None
assert ai.tag_and_note(s, p) is None, "未配置 key 应返回 None"
ok, msg = ai.test_connection(s)
assert not ok and "未配置" in msg, f"未配置应报未配置: {msg}"
print("1. 未配置禁用 ✅")

# 2. 正常 JSON
s["ai_key"] = "sk-test"
calls = {"n": 0}


def fake_call(settings, messages, timeout=90):
    calls["n"] += 1
    return '{"tags": ["白念珠菌", "自噬", "TORC1"], "note": "<p><b>Test</b></p><p>· 核心</p>"}'


ai._call_llm = fake_call
tags, note = ai.tag_and_note(s, p)
assert tags == ["白念珠菌", "自噬", "TORC1"], tags
assert "<p>" in note
print(f"2. 正常 JSON 解析 ✅ ({calls['n']} 次调用)")

# 3. code fence 容错
ai._call_llm = lambda *a, **k: '```json\n{"tags": ["A"], "note": "<p>n</p>"}\n```'
tags, note = ai.tag_and_note(s, p)
assert tags == ["A"] and "<p>n</p>" in note
print("3. code fence 容错 ✅")

# 4. 无效输出 → 异常
ai._call_llm = lambda *a, **k: "抱歉我不能"
try:
    ai.tag_and_note(s, p)
    raise SystemExit("应该抛异常")
except ValueError:
    print("4. 无效输出抛错 ✅")

# 5. 合并标签逻辑（保留来源标签）
p2 = Paper(title="x", publication="mBio", date="2024", abstract="", source="NCBI", tags=["NCBI", "PubMed"])
base = [t for t in p2.tags if t in ("NCBI", "PubMed", "Scholar", "知网")]
merged = base + [t for t in ["镰刀菌", "毒力", "NCBI"] if t not in base]
assert merged == ["NCBI", "PubMed", "镰刀菌", "毒力"], merged
print("5. 标签合并去重 ✅")

print("\nAI MODULE ALL OK")

# -*- coding: utf-8 -*-
"""AI 服务（可选）：调用 OpenAI 兼容接口为文献生成语义标签 + 中文笔记。

key 未配置时所有函数返回 None，界面自动禁用相关按钮。
"""
import json
import re

from .net import post

PROMPT = """你是科研文献助手。根据下面文献信息，输出 JSON（不要其它文字）：
{{"tags": ["标签1", "标签2", ...], "note": "<p>...</p>"}}

要求：
- tags：3-6 个中文语义标签，覆盖 研究方向/物种/机制/方法，具体不空泛（如"白念珠菌""自噬""TORC1""敲除验证"），不含"文献""研究"这类通用词
- note：一段中文阅读笔记 HTML，格式：
  <p><b>{{标题}}</b>（{{期刊/学校}} {{年份}}）</p>
  <p>· 核心内容：2-3 句，讲清做了什么、发现什么</p>
  <p>· 可借鉴：1 句，对本实验室研究有什么方法/思路参考</p>

文献信息：
标题：{title}
来源：{publication} {date}
作者：{authors}
摘要：{abstract}"""


def _model_ready(settings):
    return bool((settings["ai_key"] or "").strip())


def _call_llm(settings, messages, timeout=90):
    url = (settings["ai_base"] or "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/") + "/chat/completions"
    body = {
        "model": settings["ai_model"] or "qwen3.7-flash",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 800,
    }
    h = {"Authorization": f"Bearer {settings['ai_key']}"}
    r = post(url, json=body, proxies=None, timeout=timeout, headers=h)
    if r.status_code != 200:
        raise RuntimeError(f"AI 服务 HTTP {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"]


def _parse_json(text):
    """容错解析：剥离 markdown code fence 后取第一个 JSON 对象。"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("AI 返回无 JSON")
    return json.loads(m.group(0))


def tag_and_note(settings, paper, timeout=90):
    """单篇：返回 (tags, note_html)。失败抛异常。"""
    if not _model_ready(settings):
        return None
    abstract = paper.abstract or "（无摘要）"
    abstract = abstract[:1200]
    authors = paper.author_str or "未知"
    prompt = PROMPT.format(
        title=paper.title, publication=paper.publication or "未知来源",
        date=paper.year or paper.date or "未知年份", authors=authors, abstract=abstract)
    out = _call_llm(settings, [{"role": "user", "content": prompt}], timeout=timeout)
    data = _parse_json(out)
    tags = [str(t).strip() for t in data.get("tags", []) if str(t).strip()]
    note = str(data.get("note", "")).strip()
    if not tags or not note:
        raise ValueError("AI 返回字段不完整")
    return tags, note


def test_connection(settings, timeout=30):
    """发送最小请求验证 key。返回 (ok, msg)。"""
    if not _model_ready(settings):
        return False, "未配置 API Key"
    try:
        out = _call_llm(settings, [{"role": "user", "content": "回复 OK 两个字"}], timeout=timeout)
        return True, f"AI 服务正常（回复：{out.strip()[:30]}）"
    except Exception as e:
        return False, str(e)

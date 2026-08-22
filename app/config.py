# -*- coding: utf-8 -*-
"""配置管理：JSON 存程序目录（便携）。打包后存 exe 同级目录。"""
import json
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent   # PyInstaller onefile：exe 所在目录
else:
    APP_DIR = Path(__file__).resolve().parent.parent  # 开发模式：项目根
CONFIG_PATH = APP_DIR / "config.json"

DEFAULTS = {
    "zotero_key": "",        # 个人凭据，默认留空：分发软件时勿带个人 key
    "zotero_uid": "",
    "ncbi_key": "",
    "proxy": "http://127.0.0.1:7897",   # 通用本地代理地址，非隐私
    "use_proxy": True,
    "scholar_queries": 2,       # Scholar 一次跑几个查询词
    "default_tags": "文献题录",
    # AI 服务（可选）：OpenAI 兼容接口，key 留空则禁用 AI 标签/笔记
    "ai_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "ai_model": "qwen3.7-flash",
    "ai_key": "",
}


class Settings:
    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            if self.path.exists():
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
        except Exception:
            pass

    def save(self):
        try:
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            raise RuntimeError(f"配置保存失败: {e}")

    def __getitem__(self, k):
        return self.data.get(k, DEFAULTS.get(k))

    def __setitem__(self, k, v):
        self.data[k] = v

    @property
    def proxy_dict(self):
        p = self["proxy"]
        return {"http": p, "https": p} if p and self["use_proxy"] else None

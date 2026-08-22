# -*- coding: utf-8 -*-
"""网络工具：代理→直连 自动兜底。"""
import time
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def get(url, params=None, proxies=None, timeout=45, headers=None, tries=3):
    """GET 请求，按 [proxies, None(直连)] 顺序兜底重试。"""
    last = None
    variants = [proxies, None] if proxies else [None]
    for px in variants:
        for _ in range(tries):
            try:
                h = {"User-Agent": UA}
                if headers:
                    h.update(headers)
                r = requests.get(url, params=params, proxies=px, timeout=timeout, headers=h)
                return r
            except Exception as e:
                last = e
                time.sleep(1.2)
    raise last


def post(url, json=None, proxies=None, timeout=90, headers=None, data=None):
    last = None
    variants = [proxies, None] if proxies else [None]
    for px in variants:
        for _ in range(tries := 2):
            try:
                h = {"User-Agent": UA}
                if headers:
                    h.update(headers)
                r = requests.post(url, json=json, data=data, proxies=px, timeout=timeout, headers=h)
                return r
            except Exception as e:
                last = e
                time.sleep(1.2)
    raise last

# -*- coding: utf-8 -*-
"""数据模型。"""
from dataclasses import dataclass, field


@dataclass
class Paper:
    title: str = ""
    creators: list = field(default_factory=list)   # [{creatorType, firstName, lastName}]
    date: str = ""                                 # 年份或完整日期
    publication: str = ""                          # 期刊名 / 学校名
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    cited: int = 0
    source: str = ""                               # NCBI / Scholar / CNKI
    pmid: str = ""
    thesis_type: str = ""                          # 博士 / 硕士（学位论文）
    tags: list = field(default_factory=list)
    note: str = ""                                 # 入库笔记（可编辑）

    @property
    def year(self):
        m = self.date.strip()
        return m[:4] if m[:4].isdigit() else ""

    @property
    def author_str(self):
        names = []
        for c in self.creators:
            nm = (c.get("firstName", "") + " " + c.get("lastName", "")).strip()
            if nm:
                names.append(nm)
        if len(names) > 3:
            return "、".join(names[:3]) + " 等"
        return "、".join(names)

    def to_zotero_item(self, collections):
        """转 Zotero 父条目 JSON。"""
        if self.thesis_type:
            it = {
                "itemType": "thesis",
                "title": self.title,
                "creators": self.creators or [{"creatorType": "author", "lastName": "未知"}],
                "date": self.year or self.date,
                "thesisType": self.thesis_type,
                "university": self.publication,
            }
        else:
            it = {
                "itemType": "journalArticle",
                "title": self.title,
                "creators": self.creators or [{"creatorType": "author", "lastName": "未知"}],
                "date": self.date or self.year,
                "publicationTitle": self.publication,
            }
            for k in ("volume", "issue", "pages"):
                v = getattr(self, k)
                if v:
                    it[k] = v
        if self.doi:
            it["DOI"] = self.doi
        if self.url:
            it["url"] = self.url
        if self.abstract:
            it["abstractNote"] = self.abstract
        if self.tags:
            it["tags"] = [{"tag": t} for t in self.tags]
        if collections:
            it["collections"] = collections
        return it

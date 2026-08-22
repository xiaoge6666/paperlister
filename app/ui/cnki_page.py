# -*- coding: utf-8 -*-
"""知网页：粘贴详情页文本 → 解析题录。"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QPlainTextEdit, QMessageBox)
from PySide6.QtCore import Qt, Signal

from .papertable import PaperTable
from ..sources import cnki_source


class CnkiPage(QWidget):
    add_to_queue = Signal(object)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        tip = QLabel(
            "使用说明：在浏览器（保持知网 IP 登录）打开文献详情页 → Ctrl+A 全选 → Ctrl+C 复制 → "
            "粘贴到下面 → 点「解析」→ 勾选后加入入库队列。\n"
            "支持学位论文与期刊文章；一次粘贴一篇详情页内容。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#666;")
        lay.addWidget(tip)

        self.text = QPlainTextEdit()
        self.text.setPlaceholderText("在此粘贴知网详情页全文文本…")
        lay.addWidget(self.text, 1)

        row = QHBoxLayout()
        self.btn_parse = QPushButton("🔍 解析")
        self.lbl_count = QLabel("")
        self.btn_add = QPushButton("→ 加入入库队列（勾选）")
        row.addWidget(self.btn_parse)
        row.addWidget(self.lbl_count)
        row.addStretch(1)
        row.addWidget(self.btn_add)
        lay.addLayout(row)

        self.table = PaperTable()
        self.table.setMaximumHeight(260)
        lay.addWidget(self.table)

        self.btn_parse.clicked.connect(self.do_parse)
        self.btn_add.clicked.connect(self.send_to_queue)

    def do_parse(self):
        txt = self.text.toPlainText().strip()
        if not txt:
            QMessageBox.information(self, "提示", "请先粘贴知网详情页文本")
            return
        p = cnki_source.parse_detail_text(txt)
        if not p.title:
            QMessageBox.warning(self, "解析失败", "没识别到标题，请确认复制的是详情页全文")
            return
        self.table.set_papers([p])
        self.lbl_count.setText(f"解析 1 条：{p.title[:40]}…（{p.publication or '未知来源'} {p.year}）")

    def send_to_queue(self):
        papers = self.table.checked_papers()
        if not papers:
            QMessageBox.information(self, "提示", "没有勾选的条目")
            return
        self.add_to_queue.emit(papers)
        self.lbl_count.setText("已加入入库队列")

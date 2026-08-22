# -*- coding: utf-8 -*-
"""共享表格工具：Paper 列表表格 + 勾选。"""
from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QCheckBox,
                               QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt


class PaperTable(QTableWidget):
    HEADERS = ["☑", "标题", "作者", "年份", "期刊/学校", "被引", "来源", "标签", "备注/笔记"]

    def __init__(self, parent=None):
        super().__init__(0, len(self.HEADERS), parent)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.verticalHeader().setVisible(False)
        h = self.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(8, QHeaderView.Stretch)
        self._papers = []

    def set_papers(self, papers):
        self._papers = list(papers)
        self.setRowCount(len(self._papers))
        for row, p in enumerate(self._papers):
            cb = QCheckBox()
            cb.setChecked(True)
            self.setCellWidget(row, 0, cb)
            vals = [p.title, p.author_str, p.year, p.publication,
                    str(p.cited), p.source, ", ".join(p.tags) if p.tags else "", p.note]
            for col, val in enumerate(vals, start=1):
                item = QTableWidgetItem(val)
                item.setToolTip(val)
                if col == 1:
                    item.setToolTip(f"{p.title}\n{p.abstract[:300]}")
                self.setItem(row, col, item)

    def checked_papers(self):
        out = []
        for row, p in enumerate(self._papers):
            w = self.cellWidget(row, 0)
            if w and w.isChecked():
                it = self.item(row, 8)
                if it:
                    p.note = it.text()
                out.append(p)
        return out

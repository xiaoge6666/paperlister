# -*- coding: utf-8 -*-
"""检索页：NCBI + Google Scholar 混合检索。"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QSpinBox, QPushButton, QCheckBox, QPlainTextEdit,
                               QMessageBox, QSplitter)
from PySide6.QtCore import Qt, Signal

from .worker import Worker
from .papertable import PaperTable
from ..sources import ncbi_source, scholar_source, crossref


class SearchPage(QWidget):
    add_to_queue = Signal(object)   # list[Paper]

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._worker = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("检索词（PubMed 语法）："))
        self.term = QLineEdit()
        self.term.setPlaceholderText('例: "PP2A"[Title] AND (fung*[Title/Abstract] OR yeast*) 或 Rho GTPase Fusarium')
        row1.addWidget(self.term, 1)
        row1.addWidget(QLabel("每源条数"))
        self.num = QSpinBox()
        self.num.setRange(3, 30)
        self.num.setValue(10)
        row1.addWidget(self.num)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        self.cb_ncbi = QCheckBox("NCBI/PubMed")
        self.cb_ncbi.setChecked(True)
        self.cb_scholar = QCheckBox("Google Scholar")
        self.cb_scholar.setChecked(True)
        self.cb_doi = QCheckBox("Scholar 结果自动 Crossref 补全 DOI")
        self.cb_doi.setChecked(True)
        self.btn_search = QPushButton("🔍 开始检索")
        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        row2.addWidget(self.cb_ncbi)
        row2.addWidget(self.cb_scholar)
        row2.addWidget(self.cb_doi)
        row2.addStretch(1)
        row2.addWidget(self.btn_search)
        row2.addWidget(self.btn_stop)
        lay.addLayout(row2)

        split = QSplitter(Qt.Vertical)
        self.table = PaperTable()
        split.addWidget(self.table)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        split.addWidget(self.log)
        lay.addWidget(split, 1)

        row3 = QHBoxLayout()
        self.lbl_count = QLabel("")
        self.btn_add = QPushButton("→ 加入入库队列（勾选）")
        row3.addWidget(self.lbl_count)
        row3.addStretch(1)
        row3.addWidget(self.btn_add)
        lay.addLayout(row3)

        self.btn_search.clicked.connect(self.do_search)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_add.clicked.connect(self.send_to_queue)

    def log_line(self, s):
        self.log.appendPlainText(s)

    def do_search(self):
        term = self.term.text().strip()
        if not term:
            QMessageBox.warning(self, "提示", "请输入检索词")
            return
        self.table.set_papers([])
        self.lbl_count.setText("")
        n = self.num.value()
        use_ncbi = self.cb_ncbi.isChecked()
        use_scholar = self.cb_scholar.isChecked()
        if not (use_ncbi or use_scholar):
            QMessageBox.warning(self, "提示", "至少选一个来源")
            return

        def run(progress):
            papers = []
            if use_ncbi:
                papers += ncbi_source.search(self.settings, term, n=n, progress=progress)
            if use_scholar:
                q = term.replace('"', "").replace("[Title]", "").replace("[Title/Abstract]", "")
                q = q.split(" AND ")[0].strip()
                sp = scholar_source.search(self.settings, [q], n=n, progress=progress)
                if self.cb_doi.isChecked():
                    progress("Crossref 补全 Scholar DOI…")
                    for p in sp:
                        if not p.doi:
                            cands = crossref.search_title(self.settings, p.title, n=1)
                            if cands and cands[0]["doi"]:
                                d = cands[0]
                                p.doi = d["doi"]
                                if not p.publication and d["publication"]:
                                    p.publication = d["publication"]
                                if not p.year and d["date"]:
                                    p.date = d["date"]
                                p.url = d.get("url", p.url)
                papers += sp
            return papers

        self.btn_search.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._worker = Worker(run)
        self._worker.progress.connect(self.log_line)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.finished_err.connect(self._on_err)
        self._worker.start()

    def _on_done(self, papers):
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.table.set_papers(papers)
        self.lbl_count.setText(f"共 {len(papers)} 条（NCBI {sum(1 for p in papers if p.source=='NCBI')} / Scholar {sum(1 for p in papers if p.source=='Scholar')}）")

    def _on_err(self, msg):
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(False)
        QMessageBox.critical(self, "检索失败", msg)

    def stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self.log_line("已请求停止（当前请求完成后结束）")

    def send_to_queue(self):
        papers = self.table.checked_papers()
        if not papers:
            QMessageBox.information(self, "提示", "没有勾选的条目")
            return
        self.add_to_queue.emit(papers)
        self.log_line(f"已将 {len(papers)} 条加入入库队列")

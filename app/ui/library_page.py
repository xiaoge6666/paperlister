# -*- coding: utf-8 -*-
"""入库页：待入库队列 + Zotero 合集 + 一键入库。"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QPushButton, QPlainTextEdit, QMessageBox,
                               QSplitter)
from PySide6.QtCore import Qt, Signal

from .worker import Worker
from .papertable import PaperTable
from .. import zotero, ai


def default_note(p):
    """无笔记时生成基础模板。"""
    head = f"<p><b>{p.title}</b>（{p.publication or '未知来源'} {p.year or p.date}）</p>"
    if p.abstract:
        return head + "<p>· " + p.abstract[:220] + "…</p>"
    return head + "<p>· （待补充阅读笔记）</p>"


class LibraryPage(QWidget):
    count_changed = Signal(int)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.collections = []
        self._worker = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Zotero 合集："))
        self.cmb_coll = QComboBox()
        self.cmb_coll.setMinimumWidth(260)
        self.cmb_coll.setEditable(True)
        top.addWidget(self.cmb_coll)
        self.btn_refresh = QPushButton("刷新合集")
        self.btn_test = QPushButton("连接测试")
        top.addWidget(self.btn_refresh)
        top.addWidget(self.btn_test)
        top.addStretch(1)
        lay.addLayout(top)

        split = QSplitter(Qt.Vertical)
        self.table = PaperTable()
        split.addWidget(self.table)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(140)
        split.addWidget(self.log)
        lay.addWidget(split, 1)

        row = QHBoxLayout()
        self.lbl_count = QLabel("待入库 0 条")
        self.btn_ai = QPushButton("✨ AI 打标签+笔记（勾选）")
        self.btn_del = QPushButton("删除选中行")
        self.btn_clear = QPushButton("清空")
        self.btn_import = QPushButton("📥 一键入库（勾选）")
        self.btn_import.setStyleSheet("font-weight:bold;")
        row.addWidget(self.lbl_count)
        row.addStretch(1)
        row.addWidget(self.btn_ai)
        row.addWidget(self.btn_del)
        row.addWidget(self.btn_clear)
        row.addWidget(self.btn_import)
        lay.addLayout(row)

        self.btn_refresh.clicked.connect(self.refresh_collections)
        self.btn_test.clicked.connect(self.test_conn)
        self.btn_ai.clicked.connect(self.do_ai)
        self.btn_del.clicked.connect(self.del_selected)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_import.clicked.connect(self.do_import)

    def log_line(self, s):
        self.log.appendPlainText(s)

    # ---- 队列管理 ----
    def add_papers(self, papers):
        cur = self.table._papers
        seen = {p.title.lower() for p in cur}
        for p in papers:
            if p.title.lower() in seen:
                continue
            if not p.note:
                p.note = default_note(p)
            cur.append(p)
        self.table.set_papers(cur)
        self._update_count()

    def _update_count(self):
        self.lbl_count.setText(f"待入库 {len(self.table._papers)} 条")
        self.count_changed.emit(len(self.table._papers))

    def del_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)
            del self.table._papers[r]
        self._update_count()

    def clear_all(self):
        self.table.set_papers([])
        self._update_count()

    # ---- Zotero ----
    def refresh_collections(self):
        def run(progress):
            return zotero.list_collections(self.settings)
        self.btn_refresh.setEnabled(False)
        self._worker = Worker(run)
        self._worker.finished_ok.connect(self._on_colls)
        self._worker.finished_err.connect(lambda m: (self.btn_refresh.setEnabled(True),
                                                     QMessageBox.critical(self, "错误", m)))
        self._worker.start()

    def _on_colls(self, colls):
        self.btn_refresh.setEnabled(True)
        self.collections = colls
        cur = self.cmb_coll.currentText()
        self.cmb_coll.clear()
        for c in colls:
            self.cmb_coll.addItem(c["name"], c["key"])
        if cur:
            idx = self.cmb_coll.findText(cur)
            if idx >= 0:
                self.cmb_coll.setCurrentIndex(idx)
        self.log_line(f"已加载 {len(colls)} 个合集（下拉框可直接输入新建合集名）")

    def test_conn(self):
        def run(progress):
            return zotero.check_auth(self.settings)
        self._worker = Worker(run)
        self._worker.finished_ok.connect(
            lambda r: self.log_line(f"Zotero 连接：{'✅ ' + r[1] if r[0] else '❌ ' + r[1]}"))
        self._worker.finished_err.connect(lambda m: self.log_line(f"Zotero 连接：❌ {m}"))
        self._worker.start()

    def do_ai(self):
        """AI 批量打标签+笔记（勾选条目）。"""
        papers = self.table.checked_papers()
        if not papers:
            QMessageBox.information(self, "提示", "没有勾选的条目")
            return
        if not ai._model_ready(self.settings):
            QMessageBox.warning(self, "未配置 AI", "请先在「④ 设置」页填写 AI API Key（百炼或 DeepSeek），并保存")
            return
        self.btn_ai.setEnabled(False)
        self.log_line(f"✨ AI 处理 {len(papers)} 篇…（模型 {self.settings['ai_model']}）")

        def run(progress):
            ok_n, fail_n, fails = 0, 0, []
            for i, p in enumerate(papers, 1):
                progress(f"[{i}/{len(papers)}] {p.title[:40]}…")
                try:
                    tags, note = ai.tag_and_note(self.settings, p)
                    if tags:
                        # 保留来源标签，合并语义标签
                        base = [t for t in p.tags if t in ("NCBI", "PubMed", "Scholar", "知网")]
                        p.tags = base + [t for t in tags if t not in base]
                    if note:
                        p.note = note
                    ok_n += 1
                except Exception as e:
                    fail_n += 1
                    fails.append(f"{p.title[:40]}…：{e}")
            return ok_n, fail_n, fails

        self._worker = Worker(run)
        self._worker.progress.connect(self.log_line)
        self._worker.finished_ok.connect(self._on_ai_done)
        self._worker.finished_err.connect(self._on_ai_err)
        self._worker.start()

    def _on_ai_done(self, res):
        self.btn_ai.setEnabled(True)
        ok_n, fail_n, fails = res
        self.log_line(f"✅ AI 处理完成：成功 {ok_n} / 失败 {fail_n}")
        for f in fails:
            self.log_line(f"  ⚠ {f}")
        # 刷新表格显示新标签/笔记
        self.table.set_papers(self.table._papers)
        if fail_n:
            QMessageBox.warning(self, "部分失败", "\n".join(fails[:8]))

    def _on_ai_err(self, msg):
        self.btn_ai.setEnabled(True)
        QMessageBox.critical(self, "AI 处理失败", msg)

    def do_import(self):
        papers = self.table.checked_papers()
        if not papers:
            QMessageBox.information(self, "提示", "没有勾选的条目")
            return
        coll_name = self.cmb_coll.currentText().strip()
        if not coll_name:
            QMessageBox.warning(self, "提示", "请选择或输入 Zotero 合集名")
            return
        coll_key = None
        for c in self.collections:
            if c["name"] == coll_name:
                coll_key = c["key"]
                break
        # 笔记以表格当前文本为准
        for row, p in enumerate(self.table._papers):
            item = self.table.item(row, 7)
            if item:
                p.note = item.text()

        def run(progress):
            if not coll_key:
                progress(f"新建合集「{coll_name}」…")
                coll_key_new = zotero.create_collection(self.settings, coll_name)
                progress(f"合集已建: {coll_key_new}")
            else:
                coll_key_new = coll_key
            ok, notes, fails = zotero.add_items(self.settings, papers, coll_key_new)
            return ok, notes, fails, coll_key_new

        self.btn_import.setEnabled(False)
        self._worker = Worker(run)
        self._worker.progress.connect(self.log_line)
        self._worker.finished_ok.connect(self._on_imported)
        self._worker.finished_err.connect(self._on_import_err)
        self._worker.start()

    def _on_imported(self, res):
        self.btn_import.setEnabled(True)
        ok, notes, fails, coll_key = res
        self.log_line(f"✅ 入库完成：父条目 {ok} 条 / 笔记 {notes} 条 / 失败 {len(fails)}")
        for f in fails:
            self.log_line(f"  ⚠ {f}")
        if fails:
            QMessageBox.warning(self, "部分失败", "\n".join(fails[:8]))
        else:
            QMessageBox.information(self, "完成", f"已入库 {ok} 条到合集（含 {notes} 条笔记）")
        self.refresh_collections()

    def _on_import_err(self, msg):
        self.btn_import.setEnabled(True)
        QMessageBox.critical(self, "入库失败", msg)

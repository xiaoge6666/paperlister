# -*- coding: utf-8 -*-
"""端到端测试 v2：真实检索 → 队列 → Zotero 只读。QEventLoop 等待。
凭据从环境变量 PL_ZOTERO_KEY / PL_ZOTERO_UID / PL_NCBI_KEY 注入；未设置则跳过。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QEventLoop

# 防模态框卡死
_QMB = QMessageBox


def _noop_box(*a, **k):
    print(f"[e2e][box] {a[1] if len(a) > 1 else ''}", flush=True)
    return _QMB.Ok


QMessageBox.warning = staticmethod(_noop_box)
QMessageBox.critical = staticmethod(_noop_box)
QMessageBox.information = staticmethod(_noop_box)

from app.config import Settings
from app.ui.main_window import MainWindow

# 注入本地真实凭据（从环境变量读取；测试脚本不随 zip 分发）
_settings = Settings()
pl_key = os.environ.get("PL_ZOTERO_KEY")
pl_uid = os.environ.get("PL_ZOTERO_UID")
pl_ncbi = os.environ.get("PL_NCBI_KEY")
if not (pl_key and pl_uid and pl_ncbi):
    print("[e2e] 跳过：未设置 PL_ZOTERO_KEY/PL_ZOTERO_UID/PL_NCBI_KEY 环境变量", flush=True)
    sys.exit(0)
_settings["zotero_key"] = pl_key
_settings["zotero_uid"] = pl_uid
_settings["ncbi_key"] = pl_ncbi
_settings.save()

app = QApplication(sys.argv)
win = MainWindow(_settings)
win.show()

# --- 1. 真实检索 ---
win.search_page.term.setText('"Rho GTPase"[Title/Abstract] AND Fusarium')
win.search_page.num.setValue(5)
win.search_page.cb_scholar.setChecked(True)
win.search_page.cb_doi.setChecked(True)
win.search_page.do_search()

loop = QEventLoop()
win.search_page._worker.finished_ok.connect(loop.quit)
win.search_page._worker.finished_err.connect(loop.quit)
QTimer.singleShot(180000, loop.quit)  # 3 分钟兜底
loop.exec()

n = win.search_page.table.rowCount()
print(f"[e2e] 检索完成: {n} 条", flush=True)
assert n > 0, "检索 0 条"
if win.search_page._worker.finished_err and n == 0:
    sys.exit(1)

# --- 2. 加入队列 ---
win.search_page.send_to_queue()
qn = len(win.library_page.table._papers)
print(f"[e2e] 队列: {qn} 条", flush=True)
assert qn > 0, "队列为空"

# --- 3. Zotero 只读 ---
win.library_page.refresh_collections()
loop2 = QEventLoop()
win.library_page._worker.finished_ok.connect(loop2.quit)
win.library_page._worker.finished_err.connect(loop2.quit)
QTimer.singleShot(60000, loop2.quit)
loop2.exec()
cn = win.library_page.cmb_coll.count()
print(f"[e2e] Zotero 合集: {cn} 个", flush=True)
assert cn > 0, "Zotero 连接失败"

print("[e2e] ALL OK", flush=True)

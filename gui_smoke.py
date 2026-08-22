# -*- coding: utf-8 -*-
"""GUI 自检：构造主窗口 → 模拟加入队列 → 1.5s 后退出。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# 防模态框卡死
_QMB = QMessageBox
QMessageBox.warning = staticmethod(lambda *a, **k: _QMB.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: _QMB.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: _QMB.Ok)

from app.config import Settings
from app.ui.main_window import MainWindow
from app.models import Paper

app = QApplication(sys.argv)
win = MainWindow(Settings())
win.show()

# 模拟：加入 2 条到入库队列
p1 = Paper(title="Test Paper One", publication="Nature", date="2025",
           creators=[{"creatorType": "author", "lastName": "Zhang"}],
           note="<p><b>Test</b></p>")
p2 = Paper(title="Test Paper Two", publication="mBio", date="2024",
           creators=[{"creatorType": "author", "lastName": "Li"}])
win.library_page.add_papers([p1, p2])
assert len(win.library_page.table._papers) == 2, "queue add failed"
# 去重测试
win.library_page.add_papers([p2])
assert len(win.library_page.table._papers) == 2, "dedup failed"
# 勾选 + 默认笔记测试
win.library_page.add_papers([p1])
checked = win.library_page.table.checked_papers()
assert len(checked) == 2, f"checked failed: {len(checked)}"
print("GUI SMOKE OK: queue=2, dedup ok, checked ok, tabs=", win.tabs.count())
QTimer.singleShot(800, app.quit)
sys.exit(app.exec())

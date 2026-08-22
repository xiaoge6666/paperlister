# -*- coding: utf-8 -*-
"""主窗口。"""
from PySide6.QtWidgets import QMainWindow, QTabWidget, QLabel
from PySide6.QtCore import Qt

from .search_page import SearchPage
from .cnki_page import CnkiPage
from .library_page import LibraryPage
from .settings_page import SettingsPage
from .. import __version__


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle(f"PaperLister 文献题录管家 v{__version__}")
        self.resize(1080, 720)

        self.tabs = QTabWidget()
        self.search_page = SearchPage(settings)
        self.cnki_page = CnkiPage(settings)
        self.library_page = LibraryPage(settings)
        self.settings_page = SettingsPage(settings)

        self.tabs.addTab(self.search_page, "① 检索 (NCBI/Scholar)")
        self.tabs.addTab(self.cnki_page, "② 知网 (粘贴解析)")
        self.tabs.addTab(self.library_page, "③ 入库 Zotero")
        self.tabs.addTab(self.settings_page, "④ 设置")

        self.search_page.add_to_queue.connect(self.library_page.add_papers)
        self.cnki_page.add_to_queue.connect(self.library_page.add_papers)
        self.library_page.count_changed.connect(
            lambda n: self.statusBar().showMessage(f"入库队列 {n} 条", 4000))

        self.setCentralWidget(self.tabs)
        self.statusBar().showMessage("就绪 — 网络路由：NCBI/Scholar 走代理，知网走浏览器直连")
        self._first_run_check()

    def _first_run_check(self):
        """首次运行：Zotero 凭据未填时引导到设置页。"""
        if self.settings["zotero_key"] and self.settings["zotero_uid"]:
            return
        self.tabs.setCurrentWidget(self.settings_page)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "首次使用",
            "请先在「设置」页填写你自己的 Zotero API Key 和 User ID（必填），\n"
            "以及 NCBI API Key（可选，建议填）。填完点「保存设置」即可开始使用。")

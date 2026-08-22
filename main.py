# -*- coding: utf-8 -*-
"""PaperLister 文献题录管家 — 入口。"""
import sys
from pathlib import Path

# 保证打包后也能找到 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication
from app.config import Settings
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PaperLister")
    settings = Settings()
    win = MainWindow(settings)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""通用后台任务 Worker（QThread）。"""
from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """跑一个可调用对象，带进度信号。fn(progress_cb, ...) -> result"""
    progress = Signal(str)
    finished_ok = Signal(object)
    finished_err = Signal(str)

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self.fn = fn
        self.args = args

    def run(self):
        try:
            result = self.fn(self.progress.emit, *self.args)
            self.finished_ok.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished_err.emit(str(e))

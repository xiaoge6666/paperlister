# -*- coding: utf-8 -*-
"""设置页：个人凭据 + 网络 + 测试连接。"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                               QCheckBox, QSpinBox, QPushButton, QLabel,
                               QMessageBox, QGroupBox, QHBoxLayout)
from PySide6.QtCore import Qt

from .worker import Worker
from .. import zotero


class SettingsPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._worker = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)

        g1 = QGroupBox("Zotero（必填：自己的 API Key 与 User ID）")
        f1 = QFormLayout(g1)
        self.ed_key = QLineEdit(self.settings["zotero_key"])
        self.ed_key.setPlaceholderText("粘贴自己的 Zotero API Key（zotero.org/settings/keys）")
        self.ed_uid = QLineEdit(self.settings["zotero_uid"])
        self.ed_uid.setPlaceholderText("Zotero 账号 User ID（zotero.org/settings 页面可见）")
        f1.addRow("API Key：", self.ed_key)
        f1.addRow("User ID：", self.ed_uid)
        h1 = QHBoxLayout()
        self.lbl_zot = QLabel(self._status_label("zotero"))
        self.btn_test = QPushButton("🔌 测试 Zotero 连接")
        h1.addWidget(self.lbl_zot)
        h1.addStretch(1)
        h1.addWidget(self.btn_test)
        f1.addRow("", h1)
        lay.addWidget(g1)

        g2 = QGroupBox("网络")
        f2 = QFormLayout(g2)
        self.ed_proxy = QLineEdit(self.settings["proxy"])
        self.ed_proxy.setPlaceholderText("http://127.0.0.1:7897")
        self.cb_proxy = QCheckBox("使用代理（NCBI/Scholar 走代理；Zotero 始终直连）")
        self.cb_proxy.setChecked(bool(self.settings["use_proxy"]))
        f2.addRow("代理地址：", self.ed_proxy)
        f2.addRow("", self.cb_proxy)
        lay.addWidget(g2)

        g3 = QGroupBox("NCBI（可选，留空也能用但限速 3 次/秒）")
        f3 = QFormLayout(g3)
        self.ed_ncbi = QLineEdit(self.settings["ncbi_key"])
        self.ed_ncbi.setPlaceholderText("NCBI E-utilities API Key（ncbi.nlm.nih.gov/account/settings）")
        f3.addRow("API Key：", self.ed_ncbi)
        lay.addWidget(g3)

        g4 = QGroupBox("Scholar")
        f4 = QFormLayout(g4)
        self.sp_queries = QSpinBox()
        self.sp_queries.setRange(1, 4)
        self.sp_queries.setValue(int(self.settings["scholar_queries"]))
        f4.addRow("每次查询词数量：", self.sp_queries)
        lay.addWidget(g4)

        g5 = QGroupBox("AI 服务（可选：语义标签 + 中文笔记，不填则用规则标签）")
        f5 = QFormLayout(g5)
        self.ed_ai_base = QLineEdit(self.settings["ai_base"])
        self.ed_ai_base.setPlaceholderText("OpenAI 兼容端点，默认阿里云百炼")
        self.ed_ai_key = QLineEdit(self.settings["ai_key"])
        self.ed_ai_key.setEchoMode(QLineEdit.Password)
        self.ed_ai_key.setPlaceholderText("百炼 API Key（dashscope.console.aliyun.com），或 DeepSeek 官方 key")
        self.ed_ai_model = QLineEdit(self.settings["ai_model"])
        self.ed_ai_model.setPlaceholderText("qwen3.7-flash（便宜） / deepseek-chat / 其它 OpenAI 兼容模型")
        f5.addRow("API 地址：", self.ed_ai_base)
        f5.addRow("API Key：", self.ed_ai_key)
        f5.addRow("模型：", self.ed_ai_model)
        h5 = QHBoxLayout()
        self.lbl_ai = QLabel("○ 未配置（AI 功能禁用）" if not self.settings["ai_key"] else "✅ 已配置")
        self.btn_ai_test = QPushButton("🔌 测试 AI 服务")
        h5.addWidget(self.lbl_ai)
        h5.addStretch(1)
        h5.addWidget(self.btn_ai_test)
        f5.addRow("", h5)
        lay.addWidget(g5)

        self.btn_save = QPushButton("💾 保存设置")
        lay.addWidget(self.btn_save)
        note = QLabel("配置保存在程序目录 config.json（便携，换电脑/发人需重新填写自己的凭据）。"
                      "API Key 为明文，请勿把 config.json 或本程序随意传播。")
        note.setWordWrap(True)
        note.setStyleSheet("color:#999;")
        lay.addWidget(note)
        lay.addStretch(1)

        self.btn_save.clicked.connect(self.save)
        self.btn_test.clicked.connect(self.test_zotero)
        self.btn_ai_test.clicked.connect(self.test_ai)

    def _status_label(self, which):
        ok = bool((self.settings["zotero_key"] if which == "zotero" else self.settings["ncbi_key"]).strip())
        return ("✅ 已填写" if ok else "❌ 未填写") if which == "zotero" else \
               ("✅ 已填写" if ok else "○ 未填（可选）")

    def refresh_status(self):
        self.lbl_zot.setText(self._status_label("zotero"))

    def save(self):
        self.settings["zotero_key"] = self.ed_key.text().strip()
        self.settings["zotero_uid"] = self.ed_uid.text().strip()
        self.settings["proxy"] = self.ed_proxy.text().strip()
        self.settings["use_proxy"] = self.cb_proxy.isChecked()
        self.settings["ncbi_key"] = self.ed_ncbi.text().strip()
        self.settings["scholar_queries"] = self.sp_queries.value()
        self.settings["ai_base"] = self.ed_ai_base.text().strip()
        self.settings["ai_key"] = self.ed_ai_key.text().strip()
        self.settings["ai_model"] = self.ed_ai_model.text().strip()
        try:
            self.settings.save()
            self.refresh_status()
            QMessageBox.information(self, "完成", "设置已保存")
        except Exception as e:
            QMessageBox.critical(self, "失败", str(e))

    def test_zotero(self):
        # 用界面当前值测试（未保存也测）
        from ..config import Settings
        tmp = Settings()
        tmp["zotero_key"] = self.ed_key.text().strip()
        tmp["zotero_uid"] = self.ed_uid.text().strip()
        if not tmp["zotero_key"] or not tmp["zotero_uid"]:
            QMessageBox.warning(self, "提示", "请先填写 Zotero API Key 和 User ID")
            return
        self.btn_test.setEnabled(False)
        self.lbl_zot.setText("⏳ 测试中…")
        self._worker = Worker(zotero.check_auth, tmp)
        self._worker.finished_ok.connect(self._on_test)
        self._worker.finished_err.connect(self._on_test_err)
        self._worker.start()

    def _on_test(self, res):
        self.btn_test.setEnabled(True)
        ok, msg = res
        self.lbl_zot.setText("✅ 连接正常" if ok else f"❌ {msg}")
        if not ok:
            QMessageBox.warning(self, "连接失败", msg)

    def _on_test_err(self, msg):
        self.btn_test.setEnabled(True)
        self.lbl_zot.setText(f"❌ {msg}")
        QMessageBox.critical(self, "连接失败", str(msg))

    def test_ai(self):
        from ..config import Settings
        from .. import ai
        tmp = Settings()
        tmp["ai_base"] = self.ed_ai_base.text().strip()
        tmp["ai_key"] = self.ed_ai_key.text().strip()
        tmp["ai_model"] = self.ed_ai_model.text().strip()
        if not tmp["ai_key"]:
            QMessageBox.warning(self, "提示", "请先填写 AI API Key")
            return
        self.btn_ai_test.setEnabled(False)
        self.lbl_ai.setText("⏳ 测试中…")
        self._worker = Worker(ai.test_connection, tmp)
        self._worker.finished_ok.connect(self._on_ai_test)
        self._worker.finished_err.connect(
            lambda m: (self.btn_ai_test.setEnabled(True), self.lbl_ai.setText(f"❌ {m}")))
        self._worker.start()

    def _on_ai_test(self, res):
        self.btn_ai_test.setEnabled(True)
        ok, msg = res
        self.lbl_ai.setText("✅ " + msg if ok else "❌ " + msg)
        if not ok:
            QMessageBox.warning(self, "AI 服务", msg)

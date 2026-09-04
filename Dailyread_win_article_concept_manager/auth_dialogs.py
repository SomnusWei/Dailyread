# -*- coding: utf-8 -*-
"""登录 / 注册对话框"""
import json
import os

from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QHBoxLayout, QStackedWidget, QWidget, QMessageBox, QCheckBox
)

from api_client import api_client


# ---------- 后台调用线程 ----------
class _AuthWorker(QThread):
    """异步调用 API，避免阻塞 UI"""
    done = pyqtSignal(dict)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            r = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            r = {'code': -1, 'message': str(e), 'data': None}
        self.done.emit(r)


# ---------- 登录对话框 ----------
class LoginDialog(QDialog):
    """登录对话框（未登录时弹出）"""

    # 与主程序一致的 QSettings 组织/应用名（Windows 注册表本地存储）
    _ORG = "DailyRead"
    _APP = "ArticleConceptManager"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录 - DailyRead")
        self.setModal(True)
        self.setMinimumWidth(380)
        self._worker = None
        self._setup_ui()
        self._load_saved_credentials()

    @staticmethod
    def _settings():
        return QSettings(LoginDialog._ORG, LoginDialog._APP)

    def _load_saved_credentials(self):
        """回填上次勾选"记住账号密码"保存的用户名/密码"""
        s = self._settings()
        user = s.value("login_username", "")
        pwd = s.value("login_password", "")
        if user:
            self.username_edit.setText(user)
        if user and pwd:
            self.password_edit.setText(pwd)
            self.remember_check.setChecked(True)

    def _save_credentials(self):
        """登录成功后按勾选状态保存或清除本地账号密码"""
        s = self._settings()
        if self.remember_check.isChecked():
            s.setValue("login_username", self.username_edit.text().strip())
            s.setValue("login_password", self.password_edit.text())
        else:
            s.remove("login_username")
            s.remove("login_password")
        s.sync()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("每日阅读 · 账号登录")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 12px 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("3-32 位")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("至少 6 位")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("用户名:", self.username_edit)
        form.addRow("密码:", self.password_edit)
        layout.addLayout(form)

        self.remember_check = QCheckBox("记住密码（仅本地存储）")
        layout.addWidget(self.remember_check)

        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        # 切换到注册
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(QLabel("还没有账号？"))
        register_link = QPushButton("去注册")
        register_link.setFlat(True)
        register_link.setStyleSheet("color: #1976D2; text-decoration: underline; border: none;")
        register_link.clicked.connect(self._switch_to_register)
        switch_layout.addWidget(register_link)
        switch_layout.addStretch()
        layout.addLayout(switch_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #d32f2f;")
        layout.addWidget(self.status_label)

        # 回车登录
        self.password_edit.returnPressed.connect(self._on_login)

    def _switch_to_register(self):
        self.done(-2)  # 自定义退出码：切换到注册

    def _on_login(self):
        u = self.username_edit.text().strip()
        p = self.password_edit.text()
        if len(u) < 3 or len(p) < 6:
            self.status_label.setText("用户名至少 3 位，密码至少 6 位")
            return
        self.status_label.setText("登录中...")
        self.login_btn.setEnabled(False)
        self._worker = _AuthWorker(api_client.login, u, p)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _on_done(self, result):
        self.login_btn.setEnabled(True)
        if result.get('code') == 0:
            self._save_credentials()
            self.done(1)  # 登录成功
        else:
            self.status_label.setText(result.get('message', '登录失败'))


# ---------- 注册对话框 ----------
class RegisterDialog(QDialog):
    """注册对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("注册 - DailyRead")
        self.setModal(True)
        self.setMinimumWidth(380)
        self._check_worker = None
        self._reg_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("每日阅读 · 注册新账号")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 12px 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("3-32 位")
        self.nickname_edit = QLineEdit()
        self.nickname_edit.setPlaceholderText("可选")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("至少 6 位")
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("用户名:", self.username_edit)
        form.addRow("昵称:", self.nickname_edit)
        form.addRow("密码:", self.password_edit)
        form.addRow("确认密码:", self.confirm_edit)
        layout.addLayout(form)

        self.username_status = QLabel("")
        self.username_status.setStyleSheet("color: #888;")
        layout.addWidget(self.username_status)
        self.username_edit.editingFinished.connect(self._check_username)

        self.register_btn = QPushButton("注册")
        self.register_btn.clicked.connect(self._on_register)
        layout.addWidget(self.register_btn)

        switch_layout = QHBoxLayout()
        switch_layout.addWidget(QLabel("已有账号？"))
        login_link = QPushButton("去登录")
        login_link.setFlat(True)
        login_link.setStyleSheet("color: #1976D2; text-decoration: underline; border: none;")
        login_link.clicked.connect(self._switch_to_login)
        switch_layout.addWidget(login_link)
        switch_layout.addStretch()
        layout.addLayout(switch_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #d32f2f;")
        layout.addWidget(self.status_label)

    def _check_username(self):
        u = self.username_edit.text().strip()
        if len(u) < 3:
            self.username_status.setText("")
            return
        self.username_status.setText("校验中...")
        self.username_status.setStyleSheet("color: #888;")
        self._check_worker = _AuthWorker(api_client.check_username, u)
        self._check_worker.done.connect(self._on_check_done)
        self._check_worker.start()

    def _on_check_done(self, result):
        if result.get('code') == 0:
            if result['data'].get('available'):
                self.username_status.setText("✓ 用户名可用")
                self.username_status.setStyleSheet("color: #2e7d32;")
            else:
                self.username_status.setText("✗ 用户名已存在")
                self.username_status.setStyleSheet("color: #d32f2f;")
        else:
            self.username_status.setText("")

    def _switch_to_login(self):
        self.done(-2)

    def _on_register(self):
        u = self.username_edit.text().strip()
        n = self.nickname_edit.text().strip()
        p = self.password_edit.text()
        c = self.confirm_edit.text()
        if len(u) < 3:
            self.status_label.setText("用户名至少 3 位")
            return
        if len(p) < 6:
            self.status_label.setText("密码至少 6 位")
            return
        if p != c:
            self.status_label.setText("两次密码不一致")
            return
        self.status_label.setText("注册中...")
        self.register_btn.setEnabled(False)
        self._reg_worker = _AuthWorker(api_client.register, u, p, n)
        self._reg_worker.done.connect(self._on_done)
        self._reg_worker.start()

    def _on_done(self, result):
        self.register_btn.setEnabled(True)
        if result.get('code') == 0:
            QMessageBox.information(self, "注册成功", "账号已创建并自动登录")
            self.done(1)
        else:
            self.status_label.setText(result.get('message', '注册失败'))


def show_login_or_register(parent=None):
    """循环显示登录/注册对话框，直到登录成功或用户退出。
    返回 True 表示已登录，False 表示用户取消。
    """
    current = 'login'
    while True:
        if current == 'login':
            dlg = LoginDialog(parent)
        else:
            dlg = RegisterDialog(parent)
        code = dlg.exec()
        if code == 1:
            return True
        elif code == -2:
            current = 'register' if current == 'login' else 'login'
        else:
            return False

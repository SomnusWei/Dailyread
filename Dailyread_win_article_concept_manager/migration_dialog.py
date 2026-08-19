# -*- coding: utf-8 -*-
"""数据迁移对话框：导入旧 JSON 备份到服务端"""
import json
import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox
)

from api_client import api_client


class _MigrateWorker(QThread):
    progress = pyqtSignal(int, int)  # current, total
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, articles, checkins):
        super().__init__()
        self.articles = articles
        self.checkins = checkins

    def run(self):
        try:
            total = len(self.articles)
            batch_size = 20
            added = updated = skipped = 0
            for i in range(0, total, batch_size):
                batch = self.articles[i:i + batch_size]
                try:
                    r = api_client.migrate_import(batch, self.checkins if i == 0 else None)
                    if r.get('code') == 0:
                        stats = (r.get('data') or {}).get('articles', {})
                        added += stats.get('added', 0)
                        updated += stats.get('updated', 0)
                        skipped += stats.get('skipped', 0)
                    else:
                        self.error.emit(f"第 {i // batch_size + 1} 批导入失败: {r.get('message', '未知错误')}")
                        return
                except Exception as e:
                    self.error.emit(f"第 {i // batch_size + 1} 批请求异常: {str(e)}")
                    return
                self.progress.emit(min(i + batch_size, total), total)
            self.done.emit({'added': added, 'updated': updated, 'skipped': skipped})
        except Exception as e:
            self.error.emit(f"导入异常: {str(e)}")


class MigrationDialog(QDialog):
    """导入旧 JSON 备份对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据迁移 - 导入旧备份")
        self.setMinimumSize(500, 400)
        self._articles = []
        self._checkins = []
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        desc = QLabel(
            "将旧的 JSON 备份文件导入到服务端。\n\n"
            "支持格式：\n"
            "  • daily_read_backup_windows.json（Win 端备份）\n"
            "  • app_data.json（Win 端本地数据）\n"
            "  • daily_read_backup.json（鸿蒙端备份）\n\n"
            "导入后服务端按 (用户名, 文章ID) 去重，已存在则更新。"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton("选择 JSON 文件")
        self.select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(self.select_btn)
        self.import_btn = QPushButton("开始导入")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self.import_btn)
        layout.addLayout(btn_layout)

        self.preview_label = QLabel("未选择文件")
        layout.addWidget(self.preview_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "标题", "打卡天数", "完成率"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #1976D2;")
        layout.addWidget(self.status_label)

    def _on_select(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "JSON 文件 (*.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"文件解析失败: {e}")
            return

        # 兼容多种格式
        articles = data.get('articles', [])
        if not articles and isinstance(data, list):
            articles = data
        if not articles:
            QMessageBox.warning(self, "错误", "文件中未找到 articles 数组")
            return

        # 回填 clientId（与 DataModel._backfill_client_ids 一致：migrate-{id}）
        for a in articles:
            if not a.get('clientId'):
                a['clientId'] = f"migrate-{a.get('id', 0)}"

        self._articles = articles
        self._checkins = data.get('checkins', []) or data.get('checkInRecords', [])
        # 打卡记录的 articleId 也需转为 migrate-{id} 格式以匹配文章 clientId
        for c in self._checkins:
            if not c.get('clientId'):
                c['clientId'] = f"migrate-{c.get('articleId', c.get('clientId', 0))}"

        self.preview_label.setText(f"已加载: {os.path.basename(path)}\n"
                                   f"文章 {len(self._articles)} 篇，打卡记录 {len(self._checkins)} 条")

        self.table.setRowCount(min(len(articles), 20))
        for i, a in enumerate(articles[:20]):
            self.table.setItem(i, 0, QTableWidgetItem(str(a.get('id', a.get('clientId', '')))))
            self.table.setItem(i, 1, QTableWidgetItem(a.get('title', '')[:30]))
            self.table.setItem(i, 2, QTableWidgetItem(str(a.get('checkInDays', 0))))
            self.table.setItem(i, 3, QTableWidgetItem(f"{a.get('completionRate', 0)}%"))

        self.import_btn.setEnabled(True)
        self.status_label.setText("")

    def _on_import(self):
        if not self._articles:
            return
        self.import_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self._articles))
        self.progress.setValue(0)
        self.status_label.setText("导入中...")

        self._worker = _MigrateWorker(self._articles, self._checkins)
        self._worker.progress.connect(self._on_progress)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_error(self, msg: str):
        """处理迁移错误"""
        self.progress.setVisible(False)
        self.import_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.status_label.setText(f"导入失败: {msg}")
        QMessageBox.critical(self, "错误", f"导入失败：{msg}")

    def _on_progress(self, current, total):
        self.progress.setValue(current)

    def _on_done(self, stats):
        self.progress.setVisible(False)
        self.import_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.status_label.setText(
            f"导入完成：新增 {stats.get('added', 0)} 篇，更新 {stats.get('updated', 0)} 篇，"
            f"跳过 {stats.get('skipped', 0)} 篇"
        )
        QMessageBox.information(self, "完成", self.status_label.text())

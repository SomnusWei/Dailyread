# -*- coding: utf-8 -*-
"""
每日阅读 · 文章与概念管理器
使用 PyQt6 构建的 Windows 桌面应用
"""

import base64
import io
import json
import os
import re
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QSize, QByteArray, QBuffer
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QImage
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
    QCheckBox, QDialogButtonBox, QTabWidget, QMainWindow,
    QStatusBar, QGroupBox, QProgressBar
)


# ==================== 数据模型 ====================

class DataModel:
    """数据模型：管理文章"""

    APP_DATA_FILE = "app_data.json"
    BACKUP_FILE = "daily_read_backup_windows.json"
    WEBDAV_CONFIG_FILE = "webdav_config.json"

    def __init__(self):
        self.articles: list = []
        # 保留兼容性字段（旧版本备份可能包含）
        self.concepts: list = []
        self.clinical_notes: list = []
        self.next_article_id = 1
        self.next_concept_id = 1
        self.next_clinical_note_id = 1
        self.version = 7
        self.load()

    def load(self):
        """从文件加载数据"""
        if os.path.exists(self.APP_DATA_FILE):
            try:
                with open(self.APP_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.articles = data.get('articles', [])
                    # 保留兼容性字段但不使用
                    self.concepts = data.get('concepts', [])
                    self.clinical_notes = data.get('clinical_notes', [])
                    self.next_article_id = data.get('next_article_id', 1)
                    self.next_concept_id = data.get('next_concept_id', 1)
                    self.next_clinical_note_id = data.get('next_clinical_note_id', 1)
                    self.version = data.get('version', 7)
            except Exception as e:
                print(f"加载数据失败: {e}")
                self.articles = []
                self.concepts = []
                self.clinical_notes = []
        else:
            self.load_backup_sample()

    def load_backup_sample(self):
        """加载备份样例"""
        if os.path.exists(self.BACKUP_FILE):
            try:
                with open(self.BACKUP_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.articles = data.get('articles', [])
                    # 保留兼容性字段但不使用
                    self.concepts = data.get('concepts', [])
                    self.clinical_notes = data.get('clinical_notes', data.get('clinicalNotes', []))
                    # 记录日志
                    if self.concepts:
                        print(f"检测到旧备份文件包含 {len(self.concepts)} 条概念数据，已跳过使用")
                    if self.clinical_notes:
                        print(f"检测到旧备份文件包含 {len(self.clinical_notes)} 条临床笔记数据，已跳过使用")
            except Exception as e:
                print(f"加载备份样例失败: {e}")

    def save(self):
        """保存数据到文件（紧凑JSON，写盘更快）"""
        data = {
            'version': self.version,
            'articles': self.articles,
            'concepts': [],  # 不保存概念数据
            'clinical_notes': [],  # 不保存临床笔记数据
            'next_article_id': self.next_article_id,
            'next_concept_id': 1,
            'next_clinical_note_id': 1
        }
        with open(self.APP_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def count_chinese_chars(self, text: str) -> int:
        """统计汉字数量（re 底层为 C，快于 Python 循环）"""
        if not text:
            return 0
        return len(re.findall(r'[\u4e00-\u9fff]', text))

    def add_article(self, article_data: dict, save_now: bool = True) -> int:
        """添加文章"""
        article_data['id'] = self.next_article_id
        article_data['chineseChars'] = self.count_chinese_chars(article_data.get('content', ''))
        article_data.setdefault('imagewebp', '')
        _now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        article_data['createTime'] = _now
        article_data['lastModified'] = _now
        self.articles.append(article_data)
        self.next_article_id += 1
        if save_now:
            self.save()
        return article_data['id']

    def update_article(self, article_id: int, article_data: dict):
        """更新文章"""
        for i, article in enumerate(self.articles):
            if article['id'] == article_id:
                article_data['id'] = article_id
                article_data['chineseChars'] = self.count_chinese_chars(article_data.get('content', ''))
                article_data['createTime'] = article.get('createTime', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
                article_data['lastModified'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                article_data.setdefault('imagewebp', article.get('imagewebp', ''))
                self.articles[i] = article_data
                self.save()
                return True
        return False

    def delete_articles(self, article_ids: list):
        """删除文章"""
        self.articles = [a for a in self.articles if a['id'] not in article_ids]
        self.save()

    def export_backup(self, filepath: str):
        """导出备份"""
        data = {
            'version': self.version,
            'exportTime': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'dataType': 'daily_read_backup',
            'articles': self.articles,
            'concepts': [],  # 不导出概念数据
            'clinicalNotes': []  # 不导出临床笔记数据
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_backup(self, filepath: str):
        """导入备份"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.articles = data.get('articles', [])
            # 保留兼容性字段但不使用
            concepts = data.get('concepts', [])
            clinical_notes = data.get('clinical_notes', data.get('clinicalNotes', data.get('notes', [])))
            if concepts:
                print(f"检测到旧备份文件包含 {len(concepts)} 条概念数据，已跳过导入")
            if clinical_notes:
                print(f"检测到旧备份文件包含 {len(clinical_notes)} 条临床笔记数据，已跳过导入")
            if self.articles:
                self.next_article_id = max(a['id'] for a in self.articles) + 1
            self.save()

    def export_articles_json(self, filepath: str):
        """导出文章为 JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)

    def import_articles_json(self, filepath: str, replace: bool = False):
        """导入文章 JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            if replace:
                self.articles = articles
            else:
                existing_ids = {a['id'] for a in self.articles}
                for article in articles:
                    if article['id'] not in existing_ids:
                        self.articles.append(article)
            if self.articles:
                self.next_article_id = max(a['id'] for a in self.articles) + 1
            self.save()


class WebDAVConfig:
    """WebDAV 配置"""

    def __init__(self):
        self.server_url = ""
        self.username = ""
        self.password = ""
        self.remote_filename = "daily_read_backup_windows.json"
        self.load()

    def load(self):
        """从文件加载配置"""
        if os.path.exists(DataModel.WEBDAV_CONFIG_FILE):
            try:
                with open(DataModel.WEBDAV_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.server_url = data.get('server_url', '')
                    self.username = data.get('username', '')
                    self.password = data.get('password', '')
                    self.remote_filename = data.get('remote_filename', 'daily_read_backup_windows.json')
            except Exception as e:
                print(f"加载 WebDAV 配置失败: {e}")

    def save(self):
        """保存配置到文件"""
        data = {
            'server_url': self.server_url,
            'username': self.username,
            'password': self.password,
            'remote_filename': self.remote_filename
        }
        with open(DataModel.WEBDAV_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return bool(self.server_url and self.username and self.password)


class WebDAVClient:
    """WebDAV 客户端"""

    @staticmethod
    def upload(config: WebDAVConfig, local_file: str, progress_callback=None) -> bool:
        """上传文件到 WebDAV"""
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            remote_url = config.server_url.rstrip('/') + '/DailyRead/'
            requests.request('MKCOL', remote_url, auth=HTTPBasicAuth(config.username, config.password), timeout=30)

            remote_path = remote_url + config.remote_filename
            file_size = os.path.getsize(local_file)

            with open(local_file, 'rb') as f:
                content = f.read()

            if progress_callback:
                progress_callback(0, file_size, "开始上传...")

            response = requests.put(remote_path, data=content, auth=HTTPBasicAuth(config.username, config.password), timeout=60)

            if progress_callback:
                progress_callback(file_size, file_size, "上传完成")

            return response.status_code in (200, 201, 204)
        except Exception as e:
            print(f"WebDAV 上传失败: {e}")
            if progress_callback:
                progress_callback(0, 0, f"上传失败: {str(e)}")
            return False

    @staticmethod
    def download(config: WebDAVConfig, local_file: str, progress_callback=None) -> bool:
        """从 WebDAV 下载文件"""
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            remote_url = config.server_url.rstrip('/') + '/DailyRead/' + config.remote_filename

            if progress_callback:
                progress_callback(0, 0, "正在连接...")

            response = requests.get(remote_url, auth=HTTPBasicAuth(config.username, config.password), timeout=60, stream=True)

            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                if progress_callback:
                    progress_callback(0, total_size, "开始下载...")

                with open(local_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                progress_callback(downloaded, total_size, f"下载中... {int(downloaded/total_size*100)}%")

                if progress_callback:
                    progress_callback(total_size, total_size, "下载完成")

                return True
            return False
        except Exception as e:
            print(f"WebDAV 下载失败: {e}")
            if progress_callback:
                progress_callback(0, 0, f"下载失败: {str(e)}")
            return False


# ==================== 工具函数 ====================

def center_window(window: QWidget):
    """将窗口居中显示"""
    if window.window():
        geo = window.frameGeometry()
        screens = QApplication.instance().screens()
        if screens:
            center = screens[0].availableGeometry().center()
            geo.moveCenter(center)
            window.move(geo.topLeft())


# ==================== 图片处理工具 ====================

def compress_image_to_webp_base64(filepath: str, max_size_kb: int = 25) -> str:
    """
    将图片文件转换为 WebP 格式并压缩到指定大小以下，返回纯 base64 字符串（无前缀）
    保持原始宽高比，不修改尺寸，仅通过质量压缩控制文件大小
    参数：
        filepath: 图片文件路径
        max_size_kb: 最大文件大小，单位 KB，默认 25KB
    """
    try:
        image = QImage(filepath)
        if image.isNull():
            return ''

        max_bytes = max_size_kb * 1024

        # 循环降低质量直到满足大小要求（保持原始尺寸和宽高比）
        for quality in range(80, 5, -10):
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.OpenModeFlag.WriteOnly)
            image.save(buffer, "WEBP", quality)
            buffer.close()
            if byte_array.size() <= max_bytes:
                return byte_array.toBase64().data().decode('ascii')

        # 如果仍然过大，使用最低质量
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        image.save(buffer, "WEBP", 5)
        buffer.close()
        return byte_array.toBase64().data().decode('ascii')

    except Exception as e:
        print(f"图片压缩失败: {e}")
        return ''


def webp_base64_to_pixmap(b64_str: str, max_width: int = 300, max_height: int = 200) -> QPixmap:
    """将 WebP base64 字符串转换为 QPixmap（用于预览）"""
    if not b64_str:
        return QPixmap()
    try:
        raw_bytes = base64.b64decode(b64_str)
        byte_array = QByteArray(raw_bytes)
        pixmap = QPixmap()
        pixmap.loadFromData(byte_array, "WEBP")
        if not pixmap.isNull():
            # 同时限制宽高，保持比例
            pixmap = pixmap.scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return pixmap
    except Exception as e:
        print(f"图片解码失败: {e}")
        return QPixmap()


def get_base64_size_kb(b64_str: str) -> float:
    """计算 base64 字符串对应原始数据的大小（KB）"""
    if not b64_str:
        return 0.0
    return len(b64_str) * 3 / 4 / 1024


# ==================== 文章编辑对话框 ====================

class ArticleEditDialog(QDialog):
    """文章编辑对话框"""

    def __init__(self, article: dict = None, parent=None):
        super().__init__(parent)
        self.article = article or {}
        self.is_edit = bool(article and article.get('id'))
        self.imagewebp_data = ''
        self.setWindowTitle("编辑文章" if self.is_edit else "添加文章")
        
        # 强制设置窗口大小（覆盖任何保存的设置）
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        settings.clear()  # 清除所有旧设置
        
        self.setFixedWidth(900)
        self.setFixedHeight(550)
        self.setStyleSheet("QDialog { margin-top: 0px; }")
        self.setup_ui()
        if self.article and self.article.get('imagewebp'):
            self.imagewebp_data = self.article.get('imagewebp', '')
            self.update_image_preview()

    def restore_geometry(self):
        """恢复窗口几何信息"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        # 清除旧的几何信息，使用新的默认布局
        settings.remove("article_dialog_geometry")
        center_window(self)

    def closeEvent(self, event):
        """关闭时保存窗口几何信息"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        settings.setValue("article_dialog_geometry", self.saveGeometry())
        event.accept()

    def setup_ui(self):
        # 主布局：垂直排列
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 5, 10, 10)

        # 标题行
        title_layout = QHBoxLayout()
        title_label = QLabel("文章标题")
        self.titleEdit = QLineEdit()
        self.titleEdit.setPlaceholderText("请输入文章标题")
        if self.article:
            self.titleEdit.setText(self.article.get('title', ''))
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.titleEdit)
        main_layout.addLayout(title_layout)

        # 内容区域：左右布局（不使用 splitter）
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # ========== 左侧面板（25%宽度，约 225px）==========
        left_widget = QWidget()
        left_widget.setFixedWidth(225)  # 25% of 900px = 225px
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 图片设置标签
        image_label = QLabel("图片设置")
        image_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(image_label)

        # 图片预览区
        self.imagePreviewLabel = QLabel()
        self.imagePreviewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagePreviewLabel.setFixedHeight(200)
        self.imagePreviewLabel.setStyleSheet("QLabel { border: 1px dashed #999; padding: 8px; }")
        self.imagePreviewLabel.setText("（暂无图片）")
        left_layout.addWidget(self.imagePreviewLabel)

        # 图片操作按钮
        image_btn_layout = QHBoxLayout()
        self.selectImageBtn = QPushButton("选择图片...")
        self.selectImageBtn.clicked.connect(self.on_select_image)
        image_btn_layout.addWidget(self.selectImageBtn)

        self.removeImageBtn = QPushButton("移除图片")
        self.removeImageBtn.clicked.connect(self.on_remove_image)
        image_btn_layout.addWidget(self.removeImageBtn)

        self.imageSizeLabel = QLabel("")
        image_btn_layout.addWidget(self.imageSizeLabel)
        image_btn_layout.addStretch()
        left_layout.addLayout(image_btn_layout)

        # 选项设置
        options_group = QGroupBox("选项设置")
        options_layout = QFormLayout(options_group)
        options_layout.setSpacing(5)

        # 状态复选框
        status_layout = QHBoxLayout()
        self.isReadingCheck = QCheckBox("正在阅读")
        self.isReadingCheck.setChecked(True)
        status_layout.addWidget(self.isReadingCheck)
        options_layout.addRow("状态:", status_layout)

        # 必读设置
        required_layout = QHBoxLayout()
        self.isRequiredCheck = QCheckBox("必读")
        self.useIndependentCheckRateCheck = QCheckBox("独立目标")
        required_layout.addWidget(self.isRequiredCheck)
        required_layout.addWidget(self.useIndependentCheckRateCheck)
        options_layout.addRow("必读:", required_layout)

        # 数值设置
        self.independentCheckRateSpin = QSpinBox()
        self.independentCheckRateSpin.setRange(0, 100)
        self.independentCheckRateSpin.setFixedWidth(50)
        if self.article:
            self.independentCheckRateSpin.setValue(self.article.get('independentCheckRate', 0))
        options_layout.addRow("独立目标:", self.independentCheckRateSpin)

        self.checkInDaysSpin = QSpinBox()
        self.checkInDaysSpin.setRange(0, 9999)
        self.checkInDaysSpin.setFixedWidth(50)
        if self.article:
            self.checkInDaysSpin.setValue(self.article.get('checkInDays', 0))
        options_layout.addRow("打卡天数:", self.checkInDaysSpin)

        self.completionRateSpin = QSpinBox()
        self.completionRateSpin.setRange(0, 100)
        self.completionRateSpin.setFixedWidth(50)
        if self.article:
            self.completionRateSpin.setValue(self.article.get('completionRate', 0))
        options_layout.addRow("完成率:", self.completionRateSpin)

        # 设置初始值
        if self.article:
            self.isReadingCheck.setChecked(self.article.get('isReading', False))
            self.isRequiredCheck.setChecked(self.article.get('isRequired', False))
            self.useIndependentCheckRateCheck.setChecked(self.article.get('useIndependentCheckRate', False))
        else:
            from PyQt6.QtCore import QSettings
            settings = QSettings("DailyRead", "ArticleConceptManager")
            self.isReadingCheck.setChecked(settings.value("article_default_isReading", True, type=bool))
            self.isRequiredCheck.setChecked(settings.value("article_default_isRequired", False, type=bool))
            self.useIndependentCheckRateCheck.setChecked(
                settings.value("article_default_useIndependentCheckRate", False, type=bool)
            )

        left_layout.addWidget(options_group)
        left_layout.addStretch()  # 让内容靠上

        content_layout.addWidget(left_widget)

        # ========== 右侧面板（自动填充剩余空间）==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 文章内容标签
        content_label = QLabel("文章内容")
        right_layout.addWidget(content_label)

        # 文章内容编辑区
        self.contentEdit = QTextEdit()
        self.contentEdit.setPlaceholderText("请输入文章内容")
        # 设置较大的字号便于编辑
        font = self.contentEdit.font()
        font.setPointSize(14)
        self.contentEdit.setFont(font)
        if self.article:
            self.contentEdit.setPlainText(self.article.get('content', ''))
        right_layout.addWidget(self.contentEdit)

        content_layout.addWidget(right_widget, 1)  # stretch=1，自动填充

        main_layout.addLayout(content_layout)

        # 按钮
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.on_ok)
        buttonBox.rejected.connect(self.reject)
        main_layout.addWidget(buttonBox)

    def on_select_image(self):
        """选择图片并压缩为WebP"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;所有文件 (*.*)"
        )
        if not filepath:
            return
        b64 = compress_image_to_webp_base64(filepath, max_size_kb=25)
        if not b64:
            QMessageBox.warning(self, "提示", "图片处理失败，请选择其他图片")
            return
        self.imagewebp_data = b64
        self.update_image_preview()

    def on_remove_image(self):
        """移除图片"""
        self.imagewebp_data = ''
        self.update_image_preview()

    def update_image_preview(self):
        """更新图片预览显示"""
        if self.imagewebp_data:
            pixmap = webp_base64_to_pixmap(self.imagewebp_data, max_width=350, max_height=180)
            if not pixmap.isNull():
                self.imagePreviewLabel.setPixmap(pixmap)
                size_kb = get_base64_size_kb(self.imagewebp_data)
                self.imageSizeLabel.setText(f"约 {size_kb:.1f} KB")
            else:
                self.imagePreviewLabel.setText("（图片预览失败）")
                self.imageSizeLabel.setText("")
        else:
            self.imagePreviewLabel.clear()
            self.imagePreviewLabel.setText("（暂无图片）")
            self.imageSizeLabel.setText("")

    def on_ok(self):
        """点击OK按钮时的验证"""
        title = self.titleEdit.text().strip()
        content = self.contentEdit.toPlainText().strip()

        # 如果标题和内容都为空，不允许保存
        if not title and not content:
            QMessageBox.warning(self, "提示", "标题和内容不能同时为空")
            return

        self.accept()

    def get_data(self) -> list:
        """获取编辑后的数据，可能返回单条或多条"""
        title = self.titleEdit.text().strip()
        content = self.contentEdit.toPlainText().strip()

        # 如果标题为空但内容包含分隔符，使用快速粘贴逻辑
        if not title and content and ('|' in content or '.' in content):
            result = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if '|' in line:
                    parts = line.split('|', 1)
                else:
                    parts = line.split('.', 1)
                if len(parts) >= 1:
                    item_title = parts[0].strip()
                    item_content = parts[1].strip() if len(parts) > 1 else ""
                    if item_title:
                        result.append({
                            'title': item_title,
                            'content': item_content,
                            'contentHtml': '',
                            'isReading': self.isReadingCheck.isChecked(),
                            'isRequired': self.isRequiredCheck.isChecked(),
                            'useIndependentCheckRate': self.useIndependentCheckRateCheck.isChecked(),
                            'independentCheckRate': self.independentCheckRateSpin.value(),
                            'checkInDays': self.checkInDaysSpin.value(),
                            'completionRate': self.completionRateSpin.value(),
                            'imagewebp': ''
                        })
            return result if result else [{'title': title, 'content': content, 'imagewebp': ''}]

        # 正常返回单条数据
        return [{
            'title': title,
            'content': content,
            'contentHtml': self.article.get('contentHtml', ''),
            'isReading': self.isReadingCheck.isChecked(),
            'isRequired': self.isRequiredCheck.isChecked(),
            'useIndependentCheckRate': self.useIndependentCheckRateCheck.isChecked(),
            'independentCheckRate': self.independentCheckRateSpin.value(),
            'checkInDays': self.checkInDaysSpin.value(),
            'completionRate': self.completionRateSpin.value(),
            'imagewebp': self.imagewebp_data
        }]


# ==================== 快速粘贴对话框 ====================

class QuickPasteDialog(QDialog):
    """快速粘贴对话框"""

    def __init__(self, paste_type: str = "article", parent=None):
        super().__init__(parent)
        self.paste_type = paste_type
        self.parsed_data = []
        self.setWindowTitle("快速粘贴添加")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        center_window(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        if self.paste_type == "article":
            desc = "每行格式：标题,内容 或 标题|内容\n示例：\n我的文章,这是文章内容\n第二篇|这也是内容"
        else:
            desc = "每行格式：标题|分类|学科|章节|内容\n字段可以留空\n示例：\n数学概念|数学|代数||内容\n物理|物理力学||第二章|内容"

        desc_label = QLabel(desc)
        layout.addWidget(desc_label)

        self.inputEdit = QPlainTextEdit()
        self.inputEdit.setPlaceholderText("请粘贴内容，每行一条记录")
        layout.addWidget(self.inputEdit)

        preview_btn = QPushButton("预览")
        preview_btn.clicked.connect(self.do_preview)
        layout.addWidget(preview_btn)

        preview_label = QLabel("预览")
        layout.addWidget(preview_label)

        self.previewEdit = QPlainTextEdit()
        self.previewEdit.setReadOnly(True)
        self.previewEdit.setMaximumHeight(150)
        layout.addWidget(self.previewEdit)

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

    def do_preview(self):
        """预览解析结果"""
        lines = self.inputEdit.toPlainText().strip().split('\n')
        self.parsed_data = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if self.paste_type == "article":
                if '|' in line:
                    parts = line.split('|', 1)
                else:
                    parts = line.split(',', 1)
                if len(parts) >= 1:
                    title = parts[0].strip()
                    content = parts[1].strip() if len(parts) > 1 else ""
                    self.parsed_data.append({'title': title, 'content': content, 'isReading': True})
            else:
                parts = line.split('|')
                while len(parts) < 5:
                    parts.append('')
                self.parsed_data.append({
                    'title': parts[0].strip(),
                    'category': parts[1].strip(),
                    'subject': parts[2].strip(),
                    'chapter': parts[3].strip(),
                    'content': parts[4].strip(),
                    'isReading': True
                })

        preview_text = f"共解析 {len(self.parsed_data)} 条记录：\n\n"
        for i, item in enumerate(self.parsed_data[:10], 1):
            if self.paste_type == "article":
                preview_text += f"{i}. 标题: {item['title'][:30]}... 内容: {item['content'][:20]}...\n"
            else:
                preview_text += f"{i}. {item['title'][:20]} | {item['category']} | {item['subject']} | {item['chapter']}\n"

        if len(self.parsed_data) > 10:
            preview_text += f"\n... 还有 {len(self.parsed_data) - 10} 条记录"

        self.previewEdit.setPlainText(preview_text)

    def get_parsed_data(self) -> list:
        """获取解析后的数据"""
        if not self.parsed_data:
            self.do_preview()
        return self.parsed_data


# ==================== 导入选项对话框 ====================

class ImportOptionDialog(QDialog):
    """导入选项对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.replace = False
        self.setWindowTitle("导入选项")
        self.setMinimumWidth(300)
        self.setup_ui()
        center_window(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("请选择导入方式："))

        append_btn = QPushButton("追加（保留现有数据）")
        append_btn.clicked.connect(lambda: self.select(False))
        layout.addWidget(append_btn)

        replace_btn = QPushButton("替换（覆盖现有数据）")
        replace_btn.clicked.connect(lambda: self.select(True))
        layout.addWidget(replace_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def select(self, replace: bool):
        self.replace = replace
        self.accept()


# ==================== WebDAV 配置对话框 ====================

class WebDAVConfigDialog(QDialog):
    """WebDAV 配置对话框"""

    def __init__(self, config: WebDAVConfig = None, parent=None):
        super().__init__(parent)
        self.config = config or WebDAVConfig()
        self.setWindowTitle("配置 WebDAV")
        self.setMinimumWidth(450)
        self.setup_ui()
        center_window(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("服务器设置"))

        self.serverUrlEdit = QLineEdit()
        self.serverUrlEdit.setPlaceholderText("https://dav.jianguoyun.com/dav/")
        self.serverUrlEdit.setText(self.config.server_url)
        layout.addWidget(self.serverUrlEdit)

        self.usernameEdit = QLineEdit()
        self.usernameEdit.setPlaceholderText("用户名")
        self.usernameEdit.setText(self.config.username)
        layout.addWidget(self.usernameEdit)

        self.passwordEdit = QLineEdit()
        self.passwordEdit.setPlaceholderText("密码或应用授权令牌")
        self.passwordEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.passwordEdit.setText(self.config.password)
        layout.addWidget(self.passwordEdit)

        layout.addWidget(QLabel("远程文件名"))
        self.filenameEdit = QLineEdit()
        self.filenameEdit.setPlaceholderText("daily_read_backup_windows.json")
        self.filenameEdit.setText(self.config.remote_filename)
        layout.addWidget(self.filenameEdit)

        help_label = QLabel("提示：坚果云服务器地址：https://dav.jianguoyun.com/dav/\n建议使用「应用授权」令牌作为密码。")
        help_label.setStyleSheet("color: gray;")
        layout.addWidget(help_label)

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

    def get_config(self) -> WebDAVConfig:
        """获取配置"""
        self.config.server_url = self.serverUrlEdit.text()
        self.config.username = self.usernameEdit.text()
        self.config.password = self.passwordEdit.text()
        self.config.remote_filename = self.filenameEdit.text() or "daily_read_backup_windows.json"
        return self.config


# ==================== 文章管理页面 ====================

class ArticlePage(QWidget):
    """文章管理页面"""

    def __init__(self, data_model: DataModel, parent=None):
        super().__init__(parent)
        self.data_model = data_model
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        add_btn = QPushButton("添加")
        add_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 5px 15px;")
        add_btn.clicked.connect(self.add_article)
        toolbar_layout.addWidget(add_btn)

        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_article)
        toolbar_layout.addWidget(edit_btn)

        delete_btn = QPushButton("批量删除")
        delete_btn.clicked.connect(self.delete_articles)
        toolbar_layout.addWidget(delete_btn)

        quick_paste_btn = QPushButton("快速粘贴")
        quick_paste_btn.clicked.connect(self.quick_paste)
        toolbar_layout.addWidget(quick_paste_btn)

        import_btn = QPushButton("导入 JSON")
        import_btn.clicked.connect(self.import_json)
        toolbar_layout.addWidget(import_btn)

        export_btn = QPushButton("导出 JSON")
        export_btn.clicked.connect(self.export_json)
        toolbar_layout.addWidget(export_btn)

        toolbar_layout.addStretch()

        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("搜索标题...")
        self.searchEdit.setFixedWidth(200)
        self.searchEdit.textChanged.connect(self.on_search)
        toolbar_layout.addWidget(self.searchEdit)

        layout.addLayout(toolbar_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "标题", "汉字数", "在读", "独立打卡率", "独立目标完成率",
            "必读", "累计打卡天数", "完成率", "图片", "内容"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f5f5f5;
                background-color: #ffffff;
                color: #000000;
            }
            QTableWidget::item {
                color: #000000;
            }
            QTableWidget::item:selected {
                background-color: #3399ff;
                color: white;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(2, 10):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)

        self.table.cellDoubleClicked.connect(self.on_double_click)
        self.table.cellClicked.connect(self.on_row_click)

        # 右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)

        # 快捷键
        from PyQt6.QtGui import QShortcut, QKeySequence
        from PyQt6.QtCore import QSettings

        settings = QSettings("DailyRead", "ArticleConceptManager")
        add_key = settings.value("shortcut_add_article", "Ctrl+N")
        search_key = settings.value("shortcut_search_article", "Ctrl+F")

        self.add_shortcut = QShortcut(QKeySequence(add_key), self)
        self.add_shortcut.activated.connect(self.add_article)

        self.search_shortcut = QShortcut(QKeySequence(search_key), self)
        self.search_shortcut.activated.connect(self.focus_search)

    def focus_search(self):
        """聚焦搜索框"""
        self.searchEdit.setFocus()

    def refresh_table(self, articles: list = None):
        """刷新表格（优化：禁用重绘 + 单次循环填充，避免每行触发重排）"""
        if articles is None:
            articles = self.data_model.articles

        # 先禁用重绘，避免每次setItem触发布局重算
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(articles))

        _align = Qt.AlignmentFlag.AlignCenter
        _QTableWidgetItem = QTableWidgetItem

        for row, article in enumerate(articles):
            # ID列
            item0 = _QTableWidgetItem(str(article.get('id', '')))
            item0.setTextAlignment(_align)
            self.table.setItem(row, 0, item0)
            # 标题
            item1 = _QTableWidgetItem(article.get('title', ''))
            item1.setTextAlignment(_align)
            self.table.setItem(row, 1, item1)
            # 汉字数
            item2 = _QTableWidgetItem(str(article.get('chineseChars', 0)))
            item2.setTextAlignment(_align)
            self.table.setItem(row, 2, item2)
            # 正在阅读
            item3 = _QTableWidgetItem("是" if article.get('isReading') else "否")
            item3.setTextAlignment(_align)
            self.table.setItem(row, 3, item3)
            # 独立完成率
            item4 = _QTableWidgetItem(str(article.get('independentCheckRate', 0)) + "%")
            item4.setTextAlignment(_align)
            self.table.setItem(row, 4, item4)
            # 使用独立
            item5 = _QTableWidgetItem("是" if article.get('useIndependentCheckRate') else "否")
            item5.setTextAlignment(_align)
            self.table.setItem(row, 5, item5)
            # 必读
            item6 = _QTableWidgetItem("是" if article.get('isRequired') else "否")
            item6.setTextAlignment(_align)
            self.table.setItem(row, 6, item6)
            # 累计打卡
            item7 = _QTableWidgetItem(str(article.get('checkInDays', 0)))
            item7.setTextAlignment(_align)
            self.table.setItem(row, 7, item7)
            # 完成率
            item8 = _QTableWidgetItem(str(article.get('completionRate', 0)) + "%")
            item8.setTextAlignment(_align)
            self.table.setItem(row, 8, item8)
            # 图片
            has_image = bool(article.get('imagewebp', ''))
            if has_image:
                size_kb = get_base64_size_kb(article.get('imagewebp', ''))
                item9 = _QTableWidgetItem(f"✓ 有图({size_kb:.0f}KB)")
            else:
                item9 = _QTableWidgetItem("—")
            item9.setTextAlignment(_align)
            self.table.setItem(row, 9, item9)
            # 内容
            content = article.get('content', '')
            display_content = content[:50] + "..." if len(content) > 50 else content
            item10 = _QTableWidgetItem(display_content)
            item10.setTextAlignment(_align)
            self.table.setItem(row, 10, item10)

        # 恢复重绘，只触发一次完整刷新
        self.table.setUpdatesEnabled(True)

    def on_search(self, text: str):
        """搜索过滤"""
        if not text:
            self.refresh_table()
            return
        filtered = [a for a in self.data_model.articles if text.lower() in a.get('title', '').lower()]
        self.refresh_table(filtered)

    def on_row_click(self, row: int, col: int):
        """单击选中行 - 已由SelectionMode自动处理"""
        pass

    def on_double_click(self, row: int, col: int):
        """双击编辑"""
        article_id = int(self.table.item(row, 0).text())
        article = next((a for a in self.data_model.articles if a['id'] == article_id), None)
        if article:
            self.do_edit_article(article)

    def show_context_menu(self, pos):
        """显示右键菜单"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        menu = QMenu()
        delete_action = menu.addAction("删除选中")
        action = menu.exec(self.table.mapToGlobal(pos))

        if action == delete_action:
            self.delete_articles()

    def add_article(self):
        """添加文章"""
        dialog = ArticleEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data_list = dialog.get_data()
            # 先批量写入内存，最后只写一次磁盘
            if len(data_list) == 1:
                self.data_model.add_article(data_list[0])
            else:
                for data in data_list:
                    self.data_model.add_article(data, save_now=False)
                self.data_model.save()
            self.refresh_table()
            self.window().statusBar().showMessage(f"已添加 {len(data_list)} 篇文章", 3000)

    def edit_article(self):
        """编辑选中文章"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要编辑的文章")
            return
        row = selected_rows[0].row()
        article_id = int(self.table.item(row, 0).text())
        article = next((a for a in self.data_model.articles if a['id'] == article_id), None)
        if article:
            self.do_edit_article(article)

    def do_edit_article(self, article: dict):
        """执行编辑"""
        dialog = ArticleEditDialog(article, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data and isinstance(data, list):
                data = data[0]
            self.data_model.update_article(article['id'], data)
            self.refresh_table()
            self.window().statusBar().showMessage("文章更新成功", 3000)

    def delete_articles(self):
        """批量删除"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的文章")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 篇文章吗？")
        if reply == QMessageBox.StandardButton.Yes:
            ids = [int(self.table.item(row.row(), 0).text()) for row in selected_rows]
            self.data_model.delete_articles(ids)
            self.refresh_table()
            QMessageBox.information(self, "成功", f"已删除 {len(ids)} 篇文章")

    def quick_paste(self):
        """快速粘贴"""
        dialog = QuickPasteDialog("article", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data_list = dialog.get_parsed_data()
            # 批量写入内存，最后只写一次磁盘
            for data in data_list:
                self.data_model.add_article(data, save_now=False)
            if data_list:
                self.data_model.save()
            self.refresh_table()
            QMessageBox.information(self, "成功", f"已添加 {len(data_list)} 篇文章")

    def import_json(self):
        """导入 JSON"""
        filepath, _ = QFileDialog.getOpenFileName(self, "选择 JSON 文件", "", "JSON Files (*.json)")
        if not filepath:
            return
        option_dialog = ImportOptionDialog(self)
        if option_dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.data_model.import_articles_json(filepath, option_dialog.replace)
                self.refresh_table()
                article_count = len(self.data_model.articles)
                QMessageBox.information(self, "成功", f"文章导入成功\n\n当前文章总数：{article_count} 篇")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败：{str(e)}")

    def export_json(self):
        """导出 JSON"""
        filepath, _ = QFileDialog.getSaveFileName(self, "保存 JSON 文件", "articles.json", "JSON Files (*.json)")
        if not filepath:
            return
        try:
            article_count = len(self.data_model.articles)
            self.data_model.export_articles_json(filepath)
            QMessageBox.information(self, "成功", f"文章导出成功\n\n导出文章数量：{article_count} 篇")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")


# ==================== 备份与恢复页面 ====================

class BackupPage(QWidget):
    """备份与恢复页面"""

    def __init__(self, data_model: DataModel, parent=None):
        super().__init__(parent)
        self.data_model = data_model
        self.webdav_config = WebDAVConfig()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 本地备份
        local_group = QGroupBox("本地备份")
        local_layout = QVBoxLayout(local_group)

        export_btn = QPushButton("导出备份")
        export_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 5px 15px;")
        export_btn.clicked.connect(self.export_backup)
        local_layout.addWidget(export_btn)

        import_btn = QPushButton("导入备份")
        import_btn.clicked.connect(self.import_backup)
        local_layout.addWidget(import_btn)

        layout.addWidget(local_group)

        # WebDAV 同步
        webdav_group = QGroupBox("WebDAV 同步")
        webdav_layout = QVBoxLayout(webdav_group)

        upload_btn = QPushButton("WebDAV 上传")
        upload_btn.clicked.connect(self.webdav_upload)
        webdav_layout.addWidget(upload_btn)

        download_btn = QPushButton("WebDAV 下载")
        download_btn.clicked.connect(self.webdav_download)
        webdav_layout.addWidget(download_btn)

        config_btn = QPushButton("配置 WebDAV")
        config_btn.clicked.connect(self.config_webdav)
        webdav_layout.addWidget(config_btn)

        layout.addWidget(webdav_group)

        # 底栏进度条
        progress_group = QGroupBox("传输进度")
        progress_layout = QVBoxLayout(progress_group)
        self.progressStatusLabel = QLabel("就绪")
        progress_layout.addWidget(self.progressStatusLabel)
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        progress_layout.addWidget(self.progressBar)
        layout.addWidget(progress_group)

        layout.addStretch()

    def export_backup(self):
        """导出备份"""
        filepath, _ = QFileDialog.getSaveFileName(self, "保存备份文件", self.data_model.BACKUP_FILE, "JSON Files (*.json)")
        if not filepath:
            return
        try:
            self.data_model.export_backup(filepath)
            article_count = len(self.data_model.articles)
            QMessageBox.information(
                self, "成功",
                f"备份已保存到：{filepath}\n\n包含文章：{article_count} 篇"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")

    def import_backup(self):
        """导入备份"""
        filepath, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "JSON Files (*.json)")
        if not filepath:
            return
        reply = QMessageBox.question(self, "确认导入", "导入备份会覆盖当前所有数据，确定要继续吗？\n建议先导出一份当前数据作为备份。")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.data_model.import_backup(filepath)
                article_count = len(self.data_model.articles)
                QMessageBox.information(
                    self, "成功",
                    f"备份导入成功\n\n文章数量：{article_count} 篇"
                )
                self.refresh_all_tables()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败：{str(e)}")

    def config_webdav(self):
        """配置 WebDAV"""
        dialog = WebDAVConfigDialog(self.webdav_config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.webdav_config = dialog.get_config()
            self.webdav_config.save()
            QMessageBox.information(self, "成功", "WebDAV 配置已保存")

    def webdav_upload(self):
        """WebDAV 上传"""
        if not self.webdav_config.is_valid():
            QMessageBox.warning(self, "提示", "请先配置 WebDAV")
            self.config_webdav()
            return

        temp_file = "temp_backup.json"
        try:
            self.data_model.export_backup(temp_file)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出备份失败：{str(e)}")
            return

        self.progressBar.setValue(0)
        self.progressStatusLabel.setText("准备上传...")

        def progress_callback(current, total, status):
            if total > 0:
                percent = int(current / total * 100)
                self.progressBar.setValue(percent)
            self.progressStatusLabel.setText(status)

        success = False
        try:
            success = WebDAVClient.upload(self.webdav_config, temp_file, progress_callback)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        if success:
            article_count = len(self.data_model.articles)
            self.progressBar.setValue(100)
            self.progressStatusLabel.setText("上传完成")
            QMessageBox.information(
                self, "成功",
                f"上传成功\n\n上传文章：{article_count} 篇"
            )
        else:
            self.progressBar.setValue(0)
            self.progressStatusLabel.setText("上传失败")
            QMessageBox.critical(self, "错误", "上传失败，请检查网络连接和配置")

    def webdav_download(self):
        """WebDAV 下载"""
        if not self.webdav_config.is_valid():
            QMessageBox.warning(self, "提示", "请先配置 WebDAV")
            self.config_webdav()
            return

        reply = QMessageBox.question(self, "确认下载", "下载会覆盖当前所有数据，确定要继续吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return

        temp_file = "temp_download.json"

        self.progressBar.setValue(0)
        self.progressStatusLabel.setText("准备下载...")

        def progress_callback(current, total, status):
            if total > 0:
                percent = int(current / total * 100)
                self.progressBar.setValue(percent)
            self.progressStatusLabel.setText(status)

        success = False
        try:
            success = WebDAVClient.download(self.webdav_config, temp_file, progress_callback)
        except Exception as e:
            self.progressBar.setValue(0)
            self.progressStatusLabel.setText(f"下载失败: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            QMessageBox.critical(self, "错误", f"下载失败：{str(e)}")
            return

        if success:
            try:
                self.data_model.import_backup(temp_file)
                article_count = len(self.data_model.articles)
                self.progressBar.setValue(100)
                self.progressStatusLabel.setText("下载完成")
                QMessageBox.information(
                    self, "成功",
                    f"下载并恢复成功\n\n文章数量：{article_count} 篇"
                )
                self.refresh_all_tables()
            except Exception as e:
                self.progressBar.setValue(0)
                self.progressStatusLabel.setText("恢复失败")
                QMessageBox.critical(self, "错误", f"恢复失败：{str(e)}")
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        else:
            self.progressBar.setValue(0)
            self.progressStatusLabel.setText("下载失败")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            QMessageBox.critical(self, "错误", "下载失败，请检查网络连接和远程文件是否存在")

    def refresh_all_tables(self):
        """刷新所有表格"""
        main_window = self.window()
        if hasattr(main_window, 'refresh_all'):
            main_window.refresh_all()


# ==================== 快捷键输入控件 ====================

class ShortcutEdit(QLineEdit):
    """快捷键输入控件，支持自动识别按键组合"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("按下快捷键组合...")
        self.modifiers = []
        self.key = None

    def keyPressEvent(self, event):
        """捕获按键事件"""
        key = event.key()

        # 忽略修饰键单独按下
        if key in [Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta]:
            return

        # 收集修饰键
        modifiers = []
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("Ctrl")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("Shift")
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("Alt")
        if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
            modifiers.append("Meta")

        # 获取按键名称
        key_name = self.get_key_name(key)

        # 组合快捷键字符串
        if modifiers:
            shortcut = "+".join(modifiers) + "+" + key_name
        else:
            shortcut = key_name

        self.setText(shortcut)

    def get_key_name(self, key):
        """获取按键名称"""
        key_map = {
            Qt.Key.Key_Escape: "Esc",
            Qt.Key.Key_Tab: "Tab",
            Qt.Key.Key_Backspace: "Backspace",
            Qt.Key.Key_Return: "Enter",
            Qt.Key.Key_Enter: "Enter",
            Qt.Key.Key_Space: "Space",
            Qt.Key.Key_Delete: "Del",
            Qt.Key.Key_Insert: "Ins",
            Qt.Key.Key_Home: "Home",
            Qt.Key.Key_End: "End",
            Qt.Key.Key_PageUp: "PageUp",
            Qt.Key.Key_PageDown: "PageDown",
            Qt.Key.Key_Left: "Left",
            Qt.Key.Key_Right: "Right",
            Qt.Key.Key_Up: "Up",
            Qt.Key.Key_Down: "Down",
        }

        if key in key_map:
            return key_map[key]
        elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            return f"F{key - Qt.Key.Key_F1 + 1}"
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return chr(key)
        elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(key)
        else:
            return ""


# ==================== 设置页面 ====================

class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shortcuts = {
            'add_article': 'Ctrl+N',
            'search_article': 'Ctrl+F',
            'add_concept': 'Ctrl+N',
            'search_concept': 'Ctrl+F',
            'add_clinical_note': 'Ctrl+N',
            'search_clinical_note': 'Ctrl+F'
        }
        # 文章默认设置
        self.article_defaults = {
            'isReading': True,
            'isRequired': False,
            'useIndependentCheckRate': False
        }
        self.load_shortcuts()
        self.load_article_defaults()
        self.setup_ui()

    def load_shortcuts(self):
        """加载保存的快捷键配置"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        for key in self.shortcuts:
            saved = settings.value(f"shortcut_{key}")
            if saved:
                self.shortcuts[key] = saved

    def save_shortcuts(self):
        """保存快捷键配置"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        for key, value in self.shortcuts.items():
            settings.setValue(f"shortcut_{key}", value)

    def load_article_defaults(self):
        """加载文章默认设置"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        self.article_defaults['isReading'] = settings.value("article_default_isReading", True, type=bool)
        self.article_defaults['isRequired'] = settings.value("article_default_isRequired", False, type=bool)
        self.article_defaults['useIndependentCheckRate'] = settings.value(
            "article_default_useIndependentCheckRate", False, type=bool
        )

    def save_article_defaults(self):
        """保存文章默认设置"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        settings.setValue("article_default_isReading", self.article_defaults['isReading'])
        settings.setValue("article_default_isRequired", self.article_defaults['isRequired'])
        settings.setValue("article_default_useIndependentCheckRate", self.article_defaults['useIndependentCheckRate'])

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 快捷键设置
        shortcut_group = QGroupBox("快捷键设置")
        shortcut_layout = QFormLayout(shortcut_group)

        # 提示
        shortcut_layout.addRow(QLabel("点击输入框后，直接按下想要设置的快捷键组合即可"))

        # 文章管理快捷键
        article_group = QGroupBox("文章管理")
        article_layout = QFormLayout(article_group)

        self.add_article_edit = ShortcutEdit()
        self.add_article_edit.setText(self.shortcuts['add_article'])
        self.search_article_edit = ShortcutEdit()
        self.search_article_edit.setText(self.shortcuts['search_article'])

        article_layout.addRow("添加文章", self.add_article_edit)
        article_layout.addRow("搜索文章", self.search_article_edit)
        shortcut_layout.addRow(article_group)

        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.on_save_settings)
        button_layout.addWidget(save_btn)

        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self.on_reset_settings)
        button_layout.addWidget(reset_btn)

        shortcut_layout.addRow(button_layout)
        layout.addWidget(shortcut_group)

        # 文章默认设置
        article_defaults_group = QGroupBox("文章默认设置")
        article_defaults_layout = QHBoxLayout(article_defaults_group)

        self.default_isReading_check = QCheckBox("正在阅读")
        self.default_isReading_check.setChecked(self.article_defaults['isReading'])
        article_defaults_layout.addWidget(self.default_isReading_check)

        self.default_isRequired_check = QCheckBox("必读")
        self.default_isRequired_check.setChecked(self.article_defaults['isRequired'])
        article_defaults_layout.addWidget(self.default_isRequired_check)

        self.default_useIndependent_check = QCheckBox("使用独立目标完成率")
        self.default_useIndependent_check.setChecked(self.article_defaults['useIndependentCheckRate'])
        article_defaults_layout.addWidget(self.default_useIndependent_check)

        layout.addWidget(article_defaults_group)

        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel("每日阅读 · 文章管理器"))
        about_layout.addWidget(QLabel("版本 1.0.0"))
        about_layout.addWidget(QLabel("用于「每日阅读」APP 的本地数据管理工具"))
        layout.addWidget(about_group)

        func_group = QGroupBox("功能说明")
        func_layout = QVBoxLayout(func_group)
        func_layout.addWidget(QLabel("• 文章管理：增删改查、自动统计汉字数、快速粘贴添加"))
        func_layout.addWidget(QLabel("• 备份恢复：本地备份、导入导出 JSON"))
        func_layout.addWidget(QLabel("• WebDAV 同步：支持坚果云、Nextcloud 等服务"))
        layout.addWidget(func_group)

        layout.addStretch()

    def on_save_settings(self):
        """保存全部设置"""
        # 快捷键
        self.shortcuts['add_article'] = self.add_article_edit.text().strip()
        self.shortcuts['search_article'] = self.search_article_edit.text().strip()
        self.save_shortcuts()
        # 文章默认设置
        self.article_defaults['isReading'] = self.default_isReading_check.isChecked()
        self.article_defaults['isRequired'] = self.default_isRequired_check.isChecked()
        self.article_defaults['useIndependentCheckRate'] = self.default_useIndependent_check.isChecked()
        self.save_article_defaults()
        QMessageBox.information(self, "成功", "设置已保存，添加新文章时将生效")

    def on_reset_settings(self):
        """恢复所有默认设置"""
        # 快捷键
        self.shortcuts = {
            'add_article': 'Ctrl+N',
            'search_article': 'Ctrl+F'
        }
        self.add_article_edit.setText('Ctrl+N')
        self.search_article_edit.setText('Ctrl+F')
        self.save_shortcuts()
        # 文章默认设置
        self.article_defaults = {
            'isReading': True,
            'isRequired': False,
            'useIndependentCheckRate': False
        }
        self.default_isReading_check.setChecked(True)
        self.default_isRequired_check.setChecked(False)
        self.default_useIndependent_check.setChecked(False)
        self.save_article_defaults()
        QMessageBox.information(self, "成功", "已恢复默认设置")


# ==================== 主窗口 ====================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.data_model = DataModel()
        self.setup_ui()
        self.restore_window_geometry()
        self.auto_save_timer()

    def setup_ui(self):
        self.setWindowTitle("每日阅读 · 文章与概念管理器")
        self.setMinimumSize(1000, 700)

        # 设置应用图标
        import os
        icon_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.article_page = ArticlePage(self.data_model, self)
        self.backup_page = BackupPage(self.data_model, self)
        self.settings_page = SettingsPage(self)

        self.tabs.addTab(self.article_page, "📖 文章管理")
        self.tabs.addTab(self.backup_page, "💾 备份与恢复")
        self.tabs.addTab(self.settings_page, "⚙️ 设置")

        self.setCentralWidget(self.tabs)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def auto_save_timer(self):
        """自动保存定时器"""
        self.save_timer = QTimer(self)
        self.save_timer.timeout.connect(self.data_model.save)
        self.save_timer.start(60000)

    def restore_window_geometry(self):
        """恢复窗口几何信息"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        geometry = settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            center_window(self)

    def save_window_geometry(self):
        """保存窗口几何信息"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        settings.setValue("window_geometry", self.saveGeometry())

    def refresh_all(self):
        """刷新所有页面"""
        if self.article_page:
            self.article_page.refresh_table()

    def closeEvent(self, event):
        """关闭时保存数据"""
        self.save_window_geometry()
        self.data_model.save()
        event.accept()


# ==================== 程序入口 ====================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    app.setApplicationName("每日阅读 · 文章与概念管理器")
    app.setOrganizationName("DailyRead")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
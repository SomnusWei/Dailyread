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
import threading
import uuid
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QSize, QByteArray, QBuffer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QImage
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
    QCheckBox, QDialogButtonBox, QTabWidget, QMainWindow,
    QStatusBar, QGroupBox, QProgressBar, QScrollArea
)

# 大版本更新：用户体系 + 云同步
from api_client import api_client
from sync_service import sync_service
from auth_dialogs import show_login_or_register
from migration_dialog import MigrationDialog
from app_paths import data_path, resource_path


# ==================== 数据模型 ====================

class DataModel:
    """数据模型：管理文章"""

    APP_DATA_FILE = data_path("app_data.json")
    BACKUP_FILE = data_path("daily_read_backup_windows.json")
    WEBDAV_CONFIG_FILE = data_path("webdav_config.json")

    def __init__(self):
        self.articles: list = []
        # 保留兼容性字段（旧版本备份可能包含）
        self.concepts: list = []
        self.clinical_notes: list = []
        self.next_article_id = 1
        self.next_concept_id = 1
        self.next_clinical_note_id = 1
        self.version = 8
        self.load()

    @staticmethod
    def generate_client_id() -> str:
        """生成全局唯一的 clientId（w 前缀 + UUID）"""
        return 'w' + uuid.uuid4().hex[:16]

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
                    # 兼容旧数据：补齐 iscontent 默认 True
                    for a in self.articles:
                        a.setdefault('iscontent', True)
                    # 回填 clientId（旧数据无此字段，用 migrate-{id} 保证两端一致）
                    self._backfill_client_ids()
            except Exception as e:
                print(f"加载数据失败: {e}")
                self.articles = []
                self.concepts = []
                self.clinical_notes = []
        else:
            self.load_backup_sample()

    def _backfill_client_ids(self):
        """为缺少 clientId 的旧文章补齐（migrate-{id} 格式，保证多端一致）"""
        changed = False
        for a in self.articles:
            if not a.get('clientId'):
                a['clientId'] = f"migrate-{a.get('id', 0)}"
                changed = True
        if changed:
            self.save()

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
                    # 兼容旧数据：补齐 iscontent 默认 True
                    for a in self.articles:
                        a.setdefault('iscontent', True)
                    # 回填 clientId
                    self._backfill_client_ids()
            except Exception as e:
                print(f"加载备份样例失败: {e}")

    def save(self):
        """保存数据到文件（异步序列化+写盘，不阻塞 UI）"""
        # 深拷贝快照，避免后台线程序列化时主线程修改数据
        data = {
            'version': self.version,
            'articles': list(self.articles),
            'concepts': [],
            'clinical_notes': [],
            'next_article_id': self.next_article_id,
            'next_concept_id': 1,
            'next_clinical_note_id': 1
        }
        # 序列化 + 文件写入都放到后台线程，彻底不阻塞 UI
        t = threading.Thread(
            target=self._serialize_and_write,
            args=(self.APP_DATA_FILE, data),
            daemon=True
        )
        t.start()

    def _serialize_and_write(self, filepath: str, data: dict):
        """后台线程：序列化为 JSON 并写盘"""
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        except Exception as e:
            print(f"保存数据失败: {e}")

    def save_sync(self):
        """同步保存（关闭窗口时确保数据写完）"""
        data = {
            'version': self.version,
            'articles': self.articles,
            'concepts': [],
            'clinical_notes': [],
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
        article_data['clientId'] = self.generate_client_id()
        article_data['chineseChars'] = self.count_chinese_chars(article_data.get('content', ''))
        article_data.setdefault('imagewebp', '')
        article_data.setdefault('iscontent', True)
        _now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        article_data['createTime'] = _now
        article_data['lastModified'] = _now
        self.articles.append(article_data)
        self.next_article_id += 1
        if save_now:
            self.save()
        # 云同步钩子（异步，不阻塞 UI）
        try:
            sync_service.enqueue_article_create(article_data)
        except Exception as e:
            print(f"[Sync] enqueue create 失败: {e}")
        return article_data['id']

    def update_article(self, article_id: int, article_data: dict):
        """更新文章"""
        for i, article in enumerate(self.articles):
            if article['id'] == article_id:
                article_data['id'] = article_id
                article_data['clientId'] = article.get('clientId', '')
                article_data['chineseChars'] = self.count_chinese_chars(article_data.get('content', ''))
                article_data['createTime'] = article.get('createTime', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
                article_data['lastModified'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                article_data.setdefault('imagewebp', article.get('imagewebp', ''))
                # iscontent: 优先用传入值，否则保留旧值，再否则默认 True
                if 'iscontent' not in article_data:
                    article_data['iscontent'] = article.get('iscontent', True)
                self.articles[i] = article_data
                self.save()
                # 云同步钩子（异步，不阻塞 UI）
                try:
                    sync_service.enqueue_article_update(article_data)
                except Exception as e:
                    print(f"[Sync] enqueue update 失败: {e}")
                return True
        return False

    def delete_articles(self, article_ids: list):
        """删除文章"""
        ids_set = set(article_ids)
        # 云同步钩子：查找每篇文章的 clientId 入队
        for aid in article_ids:
            try:
                cid = None
                for a in self.articles:
                    if a['id'] == aid:
                        cid = a.get('clientId')
                        break
                if cid:
                    sync_service.enqueue_article_delete(cid)
            except Exception as e:
                print(f"[Sync] enqueue delete 失败: {e}")
        self.articles = [a for a in self.articles if a['id'] not in ids_set]
        self.save()

    def rebuild_article_ids(self):
        """重构文章 ID，从 1 开始顺序排列"""
        for i, article in enumerate(self.articles):
            article['id'] = i + 1
            article['lastModified'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        self.next_article_id = len(self.articles) + 1
        self.save()

    def clear_local_data(self):
        """清空本地文章数据（切换账号时调用）"""
        self.articles = []
        self.concepts = []
        self.clinical_notes = []
        self.next_article_id = 1
        self.next_concept_id = 1
        self.next_clinical_note_id = 1
        self.save_sync()

    def batch_update_articles(self, article_ids: list, updates: dict):
        """批量更新文章字段"""
        ids_set = set(article_ids)
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        for article in self.articles:
            if article['id'] in ids_set:
                for key, value in updates.items():
                    article[key] = value
                article['lastModified'] = now
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
            # 兼容旧数据：补齐 iscontent 默认 True + clientId
            for a in self.articles:
                if not isinstance(a, dict):
                    continue
                a.setdefault('iscontent', True)
                if not a.get('clientId'):
                    a['clientId'] = f"migrate-{a.get('id', 0)}"
            if self.articles:
                self.next_article_id = max(a['id'] for a in self.articles if isinstance(a, dict)) + 1
            self.save()
            # 导入后推送服务端（异步，不阻塞 UI）
            self._push_articles_to_server_async(self.articles)

    def _push_articles_to_server_async(self, articles):
        """批量推送文章到服务端（后台线程）"""
        if not articles or not api_client.is_logged_in():
            return
        # 准备 payload：确保每篇文章有 clientId 和必要字段
        payload_articles = []
        for a in articles:
            if not isinstance(a, dict):
                continue
            item = dict(a)
            item['clientId'] = str(item.get('clientId') or item.get('id') or '')
            payload_articles.append(item)
        if not payload_articles:
            return

        def _do_push():
            try:
                # 分批推送，每批 50 篇
                batch_size = 50
                total_added = 0
                for i in range(0, len(payload_articles), batch_size):
                    batch = payload_articles[i:i + batch_size]
                    r = api_client.migrate_import(batch, [])
                    if r and r.get('code') == 0:
                        stats = (r.get('data') or {}).get('articles', {})
                        total_added += stats.get('added', 0)
                        print(f"[Sync] 第 {i // batch_size + 1} 批推送成功: added={stats.get('added', 0)}")
                    else:
                        print(f"[Sync] 第 {i // batch_size + 1} 批推送失败: {r}")
                print(f"[Sync] 导入文章推送完成，共推送 {len(payload_articles)} 篇，新增 {total_added} 篇")
            except Exception as e:
                print(f"[Sync] 推送导入文章异常: {e}")

        threading.Thread(target=_do_push, daemon=True).start()

    def export_articles_json(self, filepath: str):
        """导出文章为 JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)

    def import_articles_json(self, filepath: str, replace: bool = False):
        """导入文章 JSON（兼容多种格式：纯数组 / 带 articles 包装的备份）"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 兼容多种格式：纯数组 [{...}] 或备份对象 {"articles": [...], ...}
        if isinstance(data, list):
            articles = data
        elif isinstance(data, dict):
            articles = data.get('articles', [])
            if not articles:
                articles = data.get('checkins', []) or data.get('checkInRecords', [])
            if not articles and data.get('id'):
                # 单篇文章
                articles = [data]
            if not articles:
                raise ValueError("文件中未找到有效的文章数据")
        else:
            raise ValueError(f"无法识别的 JSON 格式: {type(data).__name__}")

        if replace:
            self.articles = articles
        else:
            existing_ids = {a['id'] for a in self.articles}
            for article in articles:
                if article['id'] not in existing_ids:
                    self.articles.append(article)
        # 兼容旧数据：补齐 iscontent 默认 True + clientId
        for a in self.articles:
            a.setdefault('iscontent', True)
            if not a.get('clientId'):
                a['clientId'] = f"migrate-{a.get('id', 0)}"
        if self.articles:
            self.next_article_id = max(a['id'] for a in self.articles) + 1
        self.save()
        # 导入后推送服务端（异步，不阻塞 UI）
        self._push_articles_to_server_async(self.articles)


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

def compress_qimage_to_webp_base64(image: QImage, max_size_kb: int = 25) -> str:
    """
    将 QImage 对象转换为 WebP 格式并压缩到指定大小以下，返回纯 base64 字符串（无前缀）
    保持原始宽高比，不修改尺寸，仅通过质量压缩控制文件大小
    参数：
        image: QImage 对象（来自文件或剪贴板）
        max_size_kb: 最大文件大小，单位 KB，默认 25KB
    """
    try:
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


def compress_image_to_webp_base64(filepath: str, max_size_kb: int = 25) -> str:
    """
    将图片文件转换为 WebP 格式并压缩到指定大小以下，返回纯 base64 字符串（无前缀）
    保持原始宽高比，不修改尺寸，仅通过质量压缩控制文件大小
    参数：
        filepath: 图片文件路径
        max_size_kb: 最大文件大小，单位 KB，默认 25KB
    """
    image = QImage(filepath)
    return compress_qimage_to_webp_base64(image, max_size_kb)


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

        self.pasteImageBtn = QPushButton("粘贴截图")
        self.pasteImageBtn.setToolTip("从剪贴板粘贴截图（Ctrl+V 也可）")
        self.pasteImageBtn.clicked.connect(self.on_paste_image)
        image_btn_layout.addWidget(self.pasteImageBtn)

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

        # 显示文章内容
        self.isContentCheck = QCheckBox("显示文章内容")
        options_layout.addRow("显示:", self.isContentCheck)

        # 设置初始值
        if self.article:
            self.isReadingCheck.setChecked(self.article.get('isReading', False))
            self.isRequiredCheck.setChecked(self.article.get('isRequired', False))
            self.useIndependentCheckRateCheck.setChecked(self.article.get('useIndependentCheckRate', False))
            self.isContentCheck.setChecked(self.article.get('iscontent', True))
        else:
            from PyQt6.QtCore import QSettings
            settings = QSettings("DailyRead", "ArticleConceptManager")
            self.isReadingCheck.setChecked(settings.value("article_default_isReading", True, type=bool))
            self.isRequiredCheck.setChecked(settings.value("article_default_isRequired", False, type=bool))
            self.useIndependentCheckRateCheck.setChecked(
                settings.value("article_default_useIndependentCheckRate", False, type=bool)
            )
            self.isContentCheck.setChecked(settings.value("article_default_iscontent", True, type=bool))

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

    def on_paste_image(self):
        """从剪贴板粘贴图片并压缩为WebP"""
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        # 优先处理图片数据
        if mime.hasImage():
            image = clipboard.image()
            if image.isNull():
                QMessageBox.warning(self, "提示", "剪贴板中没有有效图片")
                return
            b64 = compress_qimage_to_webp_base64(image, max_size_kb=25)
            if not b64:
                QMessageBox.warning(self, "提示", "图片处理失败，请重试")
                return
            self.imagewebp_data = b64
            self.update_image_preview()
            return

        # 若剪贴板中是文件 URL（例如截屏保存为文件后复制）
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    filepath = url.toLocalFile()
                    ext = filepath.lower().rsplit('.', 1)[-1] if '.' in filepath else ''
                    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'webp', 'gif'):
                        b64 = compress_image_to_webp_base64(filepath, max_size_kb=25)
                        if b64:
                            self.imagewebp_data = b64
                            self.update_image_preview()
                            return
            QMessageBox.warning(self, "提示", "剪贴板中的文件不是有效图片")
            return

        QMessageBox.warning(self, "提示", "剪贴板中没有图片\n请先截图或复制图片再粘贴")

    def keyPressEvent(self, event):
        """支持 Ctrl+V 粘贴图片"""
        from PyQt6.QtCore import Qt
        # Ctrl+V
        if event.key() == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.on_paste_image()
            return
        super().keyPressEvent(event)

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
                            'imagewebp': '',
                            'iscontent': True
                        })
            return result if result else [{'title': title, 'content': content, 'imagewebp': '', 'iscontent': True}]

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
            'imagewebp': self.imagewebp_data,
            'iscontent': self.isContentCheck.isChecked()
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

class BatchEditDialog(QDialog):
    """批量修改对话框"""

    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"批量修改 {count} 篇文章")
        self.setMinimumWidth(380)
        self._count = count
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel(f"勾选要修改的字段，未勾选的保持不变（共 {self._count} 篇文章）")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 正在阅读开关
        reading_group = QGroupBox("正在阅读")
        reading_layout = QHBoxLayout(reading_group)
        self.reading_check = QCheckBox("修改")
        self.reading_combo = QComboBox()
        self.reading_combo.addItems(["是", "否"])
        self.reading_combo.setEnabled(False)
        self.reading_check.toggled.connect(self.reading_combo.setEnabled)
        reading_layout.addWidget(self.reading_check)
        reading_layout.addWidget(self.reading_combo)
        layout.addWidget(reading_group)

        # 必读开关
        required_group = QGroupBox("必读")
        required_layout = QHBoxLayout(required_group)
        self.required_check = QCheckBox("修改")
        self.required_combo = QComboBox()
        self.required_combo.addItems(["是", "否"])
        self.required_combo.setEnabled(False)
        self.required_check.toggled.connect(self.required_combo.setEnabled)
        required_layout.addWidget(self.required_check)
        required_layout.addWidget(self.required_combo)
        layout.addWidget(required_group)

        # 独立完成率开关
        indep_switch_group = QGroupBox("使用独立目标完成率")
        indep_switch_layout = QHBoxLayout(indep_switch_group)
        self.indep_switch_check = QCheckBox("修改")
        self.indep_switch_combo = QComboBox()
        self.indep_switch_combo.addItems(["开启", "关闭"])
        self.indep_switch_combo.setEnabled(False)
        self.indep_switch_check.toggled.connect(self.indep_switch_combo.setEnabled)
        indep_switch_layout.addWidget(self.indep_switch_check)
        indep_switch_layout.addWidget(self.indep_switch_combo)
        layout.addWidget(indep_switch_group)

        # 独立完成率百分比
        indep_rate_group = QGroupBox("独立目标完成率 (%)")
        indep_rate_layout = QHBoxLayout(indep_rate_group)
        self.indep_rate_check = QCheckBox("修改")
        self.indep_rate_spin = QSpinBox()
        self.indep_rate_spin.setRange(0, 100)
        self.indep_rate_spin.setValue(100)
        self.indep_rate_spin.setEnabled(False)
        self.indep_rate_check.toggled.connect(self.indep_rate_spin.setEnabled)
        indep_rate_layout.addWidget(self.indep_rate_check)
        indep_rate_layout.addWidget(self.indep_rate_spin)
        layout.addWidget(indep_rate_group)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定修改")
        ok_btn.setStyleSheet("background-color: #107c10; color: white; padding: 6px 20px;")
        ok_btn.clicked.connect(self.on_confirm)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def on_confirm(self):
        """确认：至少勾选一项"""
        if not any([
            self.reading_check.isChecked(),
            self.required_check.isChecked(),
            self.indep_switch_check.isChecked(),
            self.indep_rate_check.isChecked()
        ]):
            QMessageBox.warning(self, "提示", "请至少勾选一个要修改的字段")
            return
        self.accept()

    def get_updates(self) -> dict:
        """返回要更新的字段字典"""
        updates = {}
        if self.reading_check.isChecked():
            updates['isReading'] = self.reading_combo.currentText() == "是"
        if self.required_check.isChecked():
            updates['isRequired'] = self.required_combo.currentText() == "是"
        if self.indep_switch_check.isChecked():
            updates['useIndependentCheckRate'] = self.indep_switch_combo.currentText() == "开启"
        if self.indep_rate_check.isChecked():
            updates['independentCheckRate'] = self.indep_rate_spin.value()
        return updates

    def get_summary_list(self) -> list:
        """返回修改摘要列表"""
        items = []
        if self.reading_check.isChecked():
            items.append(f"正在阅读={self.reading_combo.currentText()}")
        if self.required_check.isChecked():
            items.append(f"必读={self.required_combo.currentText()}")
        if self.indep_switch_check.isChecked():
            items.append(f"独立完成率开关={self.indep_switch_combo.currentText()}")
        if self.indep_rate_check.isChecked():
            items.append(f"独立完成率={self.indep_rate_spin.value()}%")
        return items


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

        batch_edit_btn = QPushButton("批量修改")
        batch_edit_btn.setStyleSheet("background-color: #107c10; color: white; padding: 5px 15px;")
        batch_edit_btn.clicked.connect(self.batch_edit_articles)
        toolbar_layout.addWidget(batch_edit_btn)

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
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "标题", "汉字数", "在读", "显示文章", "独立打卡率",
            "独立目标完成率", "必读", "累计打卡天数", "完成率", "图片", "内容"
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
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        # 显示文章列：缩小宽度
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 60)
        for i in range(5, 11):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)

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
            # 显示文章
            item_display = _QTableWidgetItem("是" if article.get('iscontent', True) else "仅图")
            item_display.setTextAlignment(_align)
            self.table.setItem(row, 4, item_display)
            # 独立打卡率
            item5 = _QTableWidgetItem(str(article.get('independentCheckRate', 0)) + "%")
            item5.setTextAlignment(_align)
            self.table.setItem(row, 5, item5)
            # 独立目标完成率
            item6 = _QTableWidgetItem("是" if article.get('useIndependentCheckRate') else "否")
            item6.setTextAlignment(_align)
            self.table.setItem(row, 6, item6)
            # 必读
            item7 = _QTableWidgetItem("是" if article.get('isRequired') else "否")
            item7.setTextAlignment(_align)
            self.table.setItem(row, 7, item7)
            # 累计打卡
            item8 = _QTableWidgetItem(str(article.get('checkInDays', 0)))
            item8.setTextAlignment(_align)
            self.table.setItem(row, 8, item8)
            # 完成率
            item9 = _QTableWidgetItem(str(article.get('completionRate', 0)) + "%")
            item9.setTextAlignment(_align)
            self.table.setItem(row, 9, item9)
            # 图片
            has_image = bool(article.get('imagewebp', ''))
            if has_image:
                size_kb = get_base64_size_kb(article.get('imagewebp', ''))
                item_img = _QTableWidgetItem(f"✓ 有图({size_kb:.0f}KB)")
            else:
                item_img = _QTableWidgetItem("—")
            item_img.setTextAlignment(_align)
            self.table.setItem(row, 10, item_img)
            # 内容
            content = article.get('content', '')
            display_content = content[:50] + "..." if len(content) > 50 else content
            item_content = _QTableWidgetItem(display_content)
            item_content.setTextAlignment(_align)
            self.table.setItem(row, 11, item_content)

        # 恢复重绘，只触发一次完整刷新
        self.table.setUpdatesEnabled(True)

    def update_table_cells(self, article_ids: list):
        """局部刷新：只更新选中行变化的列，避免全表重建"""
        ids_set = set(article_ids)
        _align = Qt.AlignmentFlag.AlignCenter
        _QTableWidgetItem = QTableWidgetItem

        for row in range(self.table.rowCount()):
            item_id = self.table.item(row, 0)
            if not item_id:
                continue
            article_id = int(item_id.text())
            if article_id not in ids_set:
                continue

            # 从数据模型中找到对应文章
            article = next((a for a in self.data_model.articles if a['id'] == article_id), None)
            if not article:
                continue

            # 只更新可能变化的列：在读(3)、显示文章(4)、独立打卡率(5)、独立开关(6)、必读(7)、完成率(9)
            item3 = _QTableWidgetItem("是" if article.get('isReading') else "否")
            item3.setTextAlignment(_align)
            self.table.setItem(row, 3, item3)

            # 显示文章
            item_display = _QTableWidgetItem("是" if article.get('iscontent', True) else "仅图")
            item_display.setTextAlignment(_align)
            self.table.setItem(row, 4, item_display)

            item5 = _QTableWidgetItem(str(article.get('independentCheckRate', 0)) + "%")
            item5.setTextAlignment(_align)
            self.table.setItem(row, 5, item5)

            item6 = _QTableWidgetItem("是" if article.get('useIndependentCheckRate') else "否")
            item6.setTextAlignment(_align)
            self.table.setItem(row, 6, item6)

            item7 = _QTableWidgetItem("是" if article.get('isRequired') else "否")
            item7.setTextAlignment(_align)
            self.table.setItem(row, 7, item7)

            item9 = _QTableWidgetItem(str(article.get('completionRate', 0)) + "%")
            item9.setTextAlignment(_align)
            self.table.setItem(row, 9, item9)

    def update_table_row(self, article_id: int):
        """局部刷新单行所有列（编辑文章后调用，避免全表重建）"""
        _align = Qt.AlignmentFlag.AlignCenter
        _QTableWidgetItem = QTableWidgetItem

        # 找到表格中对应的行
        target_row = -1
        for row in range(self.table.rowCount()):
            item_id = self.table.item(row, 0)
            if item_id and int(item_id.text()) == article_id:
                target_row = row
                break
        if target_row < 0:
            return

        # 从数据模型中找到对应文章
        article = next((a for a in self.data_model.articles if a['id'] == article_id), None)
        if not article:
            return

        # 禁用重绘，避免每个 setItem 触发布局
        self.table.setUpdatesEnabled(False)
        try:
            # 标题(1)
            item1 = _QTableWidgetItem(article.get('title', ''))
            item1.setTextAlignment(_align)
            self.table.setItem(target_row, 1, item1)
            # 汉字数(2)
            item2 = _QTableWidgetItem(str(article.get('chineseChars', 0)))
            item2.setTextAlignment(_align)
            self.table.setItem(target_row, 2, item2)
            # 正在阅读(3)
            item3 = _QTableWidgetItem("是" if article.get('isReading') else "否")
            item3.setTextAlignment(_align)
            self.table.setItem(target_row, 3, item3)
            # 显示文章(4)
            item_display = _QTableWidgetItem("是" if article.get('iscontent', True) else "仅图")
            item_display.setTextAlignment(_align)
            self.table.setItem(target_row, 4, item_display)
            # 独立打卡率(5)
            item5 = _QTableWidgetItem(str(article.get('independentCheckRate', 0)) + "%")
            item5.setTextAlignment(_align)
            self.table.setItem(target_row, 5, item5)
            # 独立目标完成率(6)
            item6 = _QTableWidgetItem("是" if article.get('useIndependentCheckRate') else "否")
            item6.setTextAlignment(_align)
            self.table.setItem(target_row, 6, item6)
            # 必读(7)
            item7 = _QTableWidgetItem("是" if article.get('isRequired') else "否")
            item7.setTextAlignment(_align)
            self.table.setItem(target_row, 7, item7)
            # 完成率(9)
            item9 = _QTableWidgetItem(str(article.get('completionRate', 0)) + "%")
            item9.setTextAlignment(_align)
            self.table.setItem(target_row, 9, item9)
            # 图片(10)
            has_image = bool(article.get('imagewebp', ''))
            if has_image:
                size_kb = get_base64_size_kb(article.get('imagewebp', ''))
                item_img = _QTableWidgetItem(f"✓ 有图({size_kb:.0f}KB)")
            else:
                item_img = _QTableWidgetItem("—")
            item_img.setTextAlignment(_align)
            self.table.setItem(target_row, 10, item_img)
            # 内容(11)
            content = article.get('content', '')
            display_content = content[:50] + "..." if len(content) > 50 else content
            item_content = _QTableWidgetItem(display_content)
            item_content.setTextAlignment(_align)
            self.table.setItem(target_row, 11, item_content)
        finally:
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
            # 局部刷新单行，避免全表重建卡顿
            self.update_table_row(article['id'])
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

    def batch_edit_articles(self):
        """批量修改选中文章的属性"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要修改的文章")
            return
        ids = [int(self.table.item(row.row(), 0).text()) for row in selected_rows]
        dialog = BatchEditDialog(len(ids), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updates = dialog.get_updates()
            if not updates:
                QMessageBox.warning(self, "提示", "未勾选任何修改项")
                return
            # 二次确认
            summary = "、".join(dialog.get_summary_list())
            reply = QMessageBox.question(self, "确认修改",
                f"将对 {len(ids)} 篇文章执行以下修改：\n{summary}\n\n是否继续？")
            if reply == QMessageBox.StandardButton.Yes:
                self.data_model.batch_update_articles(ids, updates)
                self.update_table_cells(ids)
                self.window().statusBar().showMessage(f"已批量修改 {len(ids)} 篇文章", 3000)

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
        local_group = QGroupBox("本地备份（离线缓存）")
        local_layout = QVBoxLayout(local_group)

        export_btn = QPushButton("导出备份")
        export_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 5px 15px;")
        export_btn.clicked.connect(self.export_backup)
        local_layout.addWidget(export_btn)

        import_btn = QPushButton("导入备份")
        import_btn.clicked.connect(self.import_backup)
        local_layout.addWidget(import_btn)

        layout.addWidget(local_group)

        # 云同步（替代 WebDAV）
        cloud_group = QGroupBox("云同步")
        cloud_layout = QVBoxLayout(cloud_group)

        self.sync_status_label = QLabel("同步状态: 就绪")
        cloud_layout.addWidget(self.sync_status_label)

        sync_now_btn = QPushButton("立即同步")
        sync_now_btn.clicked.connect(self.sync_now)
        cloud_layout.addWidget(sync_now_btn)

        pull_btn = QPushButton("从云端拉取增量")
        pull_btn.clicked.connect(self.pull_from_cloud)
        cloud_layout.addWidget(pull_btn)

        layout.addWidget(cloud_group)

        # 数据迁移（旧 JSON 导入到服务端）
        migrate_group = QGroupBox("数据迁移")
        migrate_layout = QVBoxLayout(migrate_group)
        migrate_btn = QPushButton("导入旧 JSON 备份到云端")
        migrate_btn.clicked.connect(self.open_migration)
        migrate_layout.addWidget(migrate_btn)
        layout.addWidget(migrate_group)

        # 底栏进度条
        progress_group = QGroupBox("同步进度")
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
        default_name = os.path.basename(self.data_model.BACKUP_FILE)
        filepath, _ = QFileDialog.getSaveFileName(self, "保存备份文件", default_name, "JSON Files (*.json)")
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

    def sync_now(self):
        """立即触发同步（推送本地队列 + 拉取增量）"""
        if not api_client.is_logged_in():
            QMessageBox.warning(self, "提示", "请先登录")
            return
        self.progressStatusLabel.setText("正在同步...")
        self.progressBar.setRange(0, 0)  # 不确定进度
        try:
            # 拉取服务端增量
            sync_service.pull_articles(self._on_articles_pulled)
            sync_service.pull_checkins(self._on_checkins_pulled)
            queue_size = sync_service.queue.size()
            self.sync_status_label.setText(f"同步状态: 队列剩余 {queue_size} 条")
            self.progressStatusLabel.setText("同步完成")
        except Exception as e:
            self.progressStatusLabel.setText(f"同步失败: {e}")
        finally:
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(100)

    def _on_articles_pulled(self, remote_articles, next_since):
        """服务端增量文章合并到本地（按 clientId 去重，保留本地 id）"""
        existing_by_cid = {}
        for a in self.data_model.articles:
            cid = a.get('clientId')
            if cid:
                existing_by_cid[str(cid)] = a
        for ra in remote_articles:
            cid = str(ra.get('clientId') or '')
            if not cid:
                continue
            ra['clientId'] = cid
            if cid in existing_by_cid:
                # 更新本地：保留本地 id，其他字段用服务端
                local = existing_by_cid[cid]
                ra['id'] = local.get('id')
                for i, a in enumerate(self.data_model.articles):
                    if a is local:
                        self.data_model.articles[i] = ra
                        break
                existing_by_cid[cid] = ra
            else:
                # 新增到本地
                ra['id'] = self.data_model.next_article_id
                self.data_model.next_article_id += 1
                self.data_model.articles.append(ra)
                existing_by_cid[cid] = ra
        self.data_model.save()
        self.refresh_all_tables()

    def _on_checkins_pulled(self, remote_checkins, next_since):
        """服务端打卡增量合并到本地（Win 端仅更新 checkInDays 累计值）"""
        # Win 端没有独立打卡表，这里仅记录日志
        print(f"[Sync] 拉取 {len(remote_checkins)} 条打卡记录")

    def pull_from_cloud(self):
        """仅拉取云端增量"""
        if not api_client.is_logged_in():
            QMessageBox.warning(self, "提示", "请先登录")
            return
        self.progressStatusLabel.setText("正在拉取增量...")
        try:
            sync_service.pull_articles(self._on_articles_pulled)
            self.progressStatusLabel.setText("拉取完成")
        except Exception as e:
            self.progressStatusLabel.setText(f"拉取失败: {e}")

    def open_migration(self):
        """打开数据迁移对话框"""
        if not api_client.is_logged_in():
            QMessageBox.warning(self, "提示", "请先登录")
            return
        dlg = MigrationDialog(self)
        dlg.exec()
        # 迁移完成后拉取一次
        self.pull_from_cloud()

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


# ==================== 今日任务页面 ====================

class TodayTaskPage(QWidget):
    """今日阅读任务页面（从服务器获取）"""

    def __init__(self, data_model: DataModel = None, parent=None):
        super().__init__(parent)
        self.data_model = data_model
        self._task_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 顶部信息栏
        header_layout = QHBoxLayout()
        self.task_date_label = QLabel("今日任务")
        self.task_date_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.task_date_label)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 刷新任务")
        self.refresh_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 6px 16px;")
        self.refresh_btn.clicked.connect(self._refresh_tasks)
        header_layout.addWidget(self.refresh_btn)

        self.regenerate_btn = QPushButton("⚙️ 重新生成")
        self.regenerate_btn.setStyleSheet("background-color: #107c10; color: white; padding: 6px 16px;")
        self.regenerate_btn.clicked.connect(self._regenerate_tasks)
        header_layout.addWidget(self.regenerate_btn)

        layout.addLayout(header_layout)

        # 任务统计
        self.stats_label = QLabel("点击刷新按钮获取今日任务")
        self.stats_label.setStyleSheet("color: gray; padding: 8px;")
        layout.addWidget(self.stats_label)

        # 任务表格
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["序号", "文章标题", "目标字数", "类型", "必读", "打卡"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(self.table)

        # 自动加载
        self._refresh_tasks()

    def _refresh_tasks(self):
        """从服务器获取今日任务"""
        if not api_client.is_logged_in():
            self.stats_label.setText("请先登录以获取今日任务")
            self.stats_label.setStyleSheet("color: #d13438; padding: 8px;")
            self.table.setRowCount(0)
            return
        self.refresh_btn.setEnabled(False)
        self.stats_label.setText("正在加载...")
        from PyQt6.QtCore import QThread, pyqtSignal

        class FetchThread(QThread):
            finished = pyqtSignal(dict)

            def run(self_inner):
                try:
                    r = api_client.fetch_today_task()
                    self_inner.finished.emit(r)
                except Exception as e:
                    self_inner.finished.emit({'code': -1, 'message': str(e)})

        self._fetch_thread = FetchThread(self)
        self._fetch_thread.finished.connect(self._on_tasks_loaded)
        self._fetch_thread.start()

    def _regenerate_tasks(self):
        """强制重新生成今日任务"""
        if not api_client.is_logged_in():
            QMessageBox.warning(self, "提示", "请先登录")
            return
        reply = QMessageBox.question(
            self, "重新生成",
            "确定要强制重新生成今日任务吗？\n已有打卡状态将被重置。"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.regenerate_btn.setEnabled(False)
        self.stats_label.setText("正在重新生成...")
        from PyQt6.QtCore import QThread, pyqtSignal

        class GenThread(QThread):
            finished = pyqtSignal(dict)

            def run(self_inner):
                try:
                    r = api_client.generate_today_task(force=True)
                    self_inner.finished.emit(r)
                except Exception as e:
                    self_inner.finished.emit({'code': -1, 'message': str(e)})

        self._gen_thread = GenThread(self)
        self._gen_thread.finished.connect(self._on_tasks_loaded)
        self._gen_thread.start()

    def _on_tasks_loaded(self, result):
        """任务加载完成"""
        self.refresh_btn.setEnabled(True)
        self.regenerate_btn.setEnabled(True)
        if result.get('code') != 0:
            self.stats_label.setText(f"加载失败: {result.get('message', '')}")
            self.stats_label.setStyleSheet("color: #d13438; padding: 8px;")
            self.table.setRowCount(0)
            return

        data = result.get('data') or {}
        self._task_data = data
        items = data.get('items') or []
        task_date = data.get('taskDate', '')
        count = data.get('count', len(items))
        total_words = data.get('totalWords', 0)
        auto_generated = data.get('autoGenerated', False)

        # 格式化日期：处理 ISO 格式 (2026-08-18T16:00:00.000Z) 为 YYYY-MM-DD
        display_date = task_date
        if display_date and 'T' in str(display_date):
            try:
                from datetime import datetime as dt
                dt_obj = dt.fromisoformat(str(display_date).replace('Z', '+00:00'))
                display_date = dt_obj.strftime('%Y-%m-%d')
            except Exception:
                display_date = str(display_date)[:10]

        self.task_date_label.setText(f"📅 {display_date}")
        auto_tag = " (自动生成)" if auto_generated else ""
        self.stats_label.setText(
            f"共 {count} 篇文章，目标总字数 {total_words}{auto_tag}"
        )
        self.stats_label.setStyleSheet("color: #0078d4; padding: 8px;")

        # 填充表格
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._fill_task_row(row, item)

    def _fill_task_row(self, row, item):
        """填充一行任务"""
        article_title = item.get('articleTitle', '')
        word_target = item.get('wordTarget', 0)
        is_long = item.get('isLongArticle', False)
        is_required = item.get('isRequired', False)
        is_checked = item.get('isCheckedIn', False)

        # 序号
        item_no = QTableWidgetItem(str(row + 1))
        item_no.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, item_no)

        # 文章标题
        title_item = QTableWidgetItem(article_title)
        self.table.setItem(row, 1, title_item)

        # 目标字数
        word_item = QTableWidgetItem(f"{word_target} 字")
        word_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, word_item)

        # 类型
        type_item = QTableWidgetItem("长文" if is_long else "短文")
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        type_item.setForeground(QColor("#0078d4") if is_long else QColor("#107c10"))
        self.table.setItem(row, 3, type_item)

        # 必读
        req_item = QTableWidgetItem("必读" if is_required else "")
        req_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        req_item.setForeground(QColor("#d13438") if is_required else QColor("#888888"))
        self.table.setItem(row, 4, req_item)

        # 打卡状态
        check_item = QTableWidgetItem("✅ 已打卡" if is_checked else "⬜ 未打卡")
        check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        check_item.setForeground(QColor("#107c10") if is_checked else QColor("#888888"))
        self.table.setItem(row, 5, check_item)

    def refresh_table(self):
        """外部调用刷新"""
        self._refresh_tasks()

# ==================== 设置页面 ====================

class SettingsPage(QWidget):
    """设置页面（全新布局：本地设置 + 云同步 + 备份恢复 + 数据维护）"""

    def __init__(self, data_model: DataModel = None, parent=None):
        super().__init__(parent)
        self.data_model = data_model
        self.shortcuts = {
            'add_article': 'Ctrl+N',
            'search_article': 'Ctrl+F',
        }
        self.article_defaults = {
            'isReading': True,
            'isRequired': False,
            'useIndependentCheckRate': False
        }
        self._sync_debounce_timer = QTimer()
        self._sync_debounce_timer.setSingleShot(True)
        self._sync_debounce_timer.setInterval(500)
        self._sync_debounce_timer.timeout.connect(self._do_push_config)
        self.load_shortcuts()
        self.load_article_defaults()
        self.setup_ui()

    def load_shortcuts(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        for key in self.shortcuts:
            saved = settings.value(f"shortcut_{key}")
            if saved:
                self.shortcuts[key] = saved

    def save_shortcuts(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        for key, value in self.shortcuts.items():
            settings.setValue(f"shortcut_{key}", value)

    def load_article_defaults(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        self.article_defaults['isReading'] = settings.value("article_default_isReading", True, type=bool)
        self.article_defaults['isRequired'] = settings.value("article_default_isRequired", False, type=bool)
        self.article_defaults['useIndependentCheckRate'] = settings.value(
            "article_default_useIndependentCheckRate", False, type=bool
        )

    def save_article_defaults(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("DailyRead", "ArticleConceptManager")
        settings.setValue("article_default_isReading", self.article_defaults['isReading'])
        settings.setValue("article_default_isRequired", self.article_defaults['isRequired'])
        settings.setValue("article_default_useIndependentCheckRate", self.article_defaults['useIndependentCheckRate'])

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # ── 阅读设置（同步到服务器，修改即同步）──
        reading_group = QGroupBox("📖 阅读设置")
        reading_layout = QFormLayout(reading_group)

        self.daily_minutes_spin = QSpinBox()
        self.daily_minutes_spin.setRange(5, 240)
        self.daily_minutes_spin.setSuffix(" 分钟")
        self.daily_minutes_spin.setValue(20)
        self.daily_minutes_spin.valueChanged.connect(self._on_reading_setting_changed)
        reading_layout.addRow("每日阅读时长", self.daily_minutes_spin)

        self.target_rate_spin = QSpinBox()
        self.target_rate_spin.setRange(10, 100)
        self.target_rate_spin.setSuffix(" %")
        self.target_rate_spin.setValue(30)
        self.target_rate_spin.valueChanged.connect(self._on_reading_setting_changed)
        reading_layout.addRow("目标完成率", self.target_rate_spin)

        self.reading_config_status = QLabel("未登录")
        self.reading_config_status.setStyleSheet("color: gray;")
        reading_layout.addRow("同步状态", self.reading_config_status)

        layout.addWidget(reading_group)

        # ── 快捷键设置 ──
        shortcut_group = QGroupBox("⌨️ 快捷键设置")
        shortcut_layout = QFormLayout(shortcut_group)
        shortcut_layout.addRow(QLabel("点击输入框后，直接按下想要设置的快捷键组合即可"))

        self.add_article_edit = ShortcutEdit()
        self.add_article_edit.setText(self.shortcuts['add_article'])
        self.add_article_edit.textChanged.connect(self._on_shortcut_changed)
        self.search_article_edit = ShortcutEdit()
        self.search_article_edit.setText(self.shortcuts['search_article'])
        self.search_article_edit.textChanged.connect(self._on_shortcut_changed)

        shortcut_layout.addRow("添加文章", self.add_article_edit)
        shortcut_layout.addRow("搜索文章", self.search_article_edit)

        layout.addWidget(shortcut_group)

        # ── 文章默认设置 ──
        article_defaults_group = QGroupBox("📝 文章默认设置")
        article_defaults_layout = QVBoxLayout(article_defaults_group)

        self.default_isReading_check = QCheckBox("正在阅读")
        self.default_isReading_check.setChecked(self.article_defaults['isReading'])
        self.default_isReading_check.stateChanged.connect(self._on_article_defaults_changed)
        article_defaults_layout.addWidget(self.default_isReading_check)

        self.default_isRequired_check = QCheckBox("必读")
        self.default_isRequired_check.setChecked(self.article_defaults['isRequired'])
        self.default_isRequired_check.stateChanged.connect(self._on_article_defaults_changed)
        article_defaults_layout.addWidget(self.default_isRequired_check)

        self.default_useIndependent_check = QCheckBox("使用独立目标完成率")
        self.default_useIndependent_check.setChecked(self.article_defaults['useIndependentCheckRate'])
        self.default_useIndependent_check.stateChanged.connect(self._on_article_defaults_changed)
        article_defaults_layout.addWidget(self.default_useIndependent_check)

        layout.addWidget(article_defaults_group)

        # ── 备份与恢复 ──
        backup_group = QGroupBox("💾 备份与恢复")
        backup_layout = QHBoxLayout(backup_group)

        export_btn = QPushButton("📤 导出备份")
        export_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 6px 16px;")
        export_btn.clicked.connect(self._export_backup)
        backup_layout.addWidget(export_btn)

        import_btn = QPushButton("📥 导入备份")
        import_btn.clicked.connect(self._import_backup)
        backup_layout.addWidget(import_btn)

        layout.addWidget(backup_group)

        # ── 云同步 ──
        cloud_group = QGroupBox("☁️ 云同步")
        cloud_layout = QVBoxLayout(cloud_group)

        self.sync_status_label = QLabel("就绪")
        cloud_layout.addWidget(self.sync_status_label)

        sync_btn = QPushButton("🔄 立即同步")
        sync_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 6px 16px;")
        sync_btn.clicked.connect(self._sync_now)
        cloud_layout.addWidget(sync_btn)

        layout.addWidget(cloud_group)

        # ── 数据维护 ──
        data_group = QGroupBox("🔧 数据维护")
        data_layout = QVBoxLayout(data_group)

        recalc_btn = QPushButton("🔄 重新计算所有文章完成率")
        recalc_btn.setStyleSheet("background-color: #107c10; color: white; padding: 6px;")
        recalc_btn.clicked.connect(self._on_recalculate_completion_rate)
        data_layout.addWidget(recalc_btn)

        rebuild_btn = QPushButton("🔢 重构文章ID（从1开始）")
        rebuild_btn.setStyleSheet("background-color: #0078d4; color: white; padding: 6px;")
        rebuild_btn.clicked.connect(self._on_rebuild_article_ids)
        data_layout.addWidget(rebuild_btn)

        layout.addWidget(data_group)

        # ── 关于 ──
        about_group = QGroupBox("ℹ️ 关于")
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel("每日阅读 · 文章管理器"))
        about_layout.addWidget(QLabel("版本 1.51"))
        about_layout.addWidget(QLabel("用于「每日阅读」APP 的本地数据管理工具"))
        layout.addWidget(about_group)

        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.addWidget(scroll)

        self._load_server_config()

    # ── 自动同步 ──

    def _on_reading_setting_changed(self):
        self._sync_debounce_timer.start()

    def _do_push_config(self):
        if not api_client.is_logged_in():
            self.reading_config_status.setText("未登录，无法同步")
            self.reading_config_status.setStyleSheet("color: gray;")
            return
        try:
            r = api_client.push_config({
                'dailyMinutes': self.daily_minutes_spin.value(),
                'targetCheckRate': self.target_rate_spin.value()
            })
            if r.get('code') == 0:
                self.reading_config_status.setText("已同步 " + datetime.now().strftime('%H:%M:%S'))
                self.reading_config_status.setStyleSheet("color: green;")
            else:
                self.reading_config_status.setText("同步失败: " + r.get('message', ''))
                self.reading_config_status.setStyleSheet("color: red;")
        except Exception as e:
            self.reading_config_status.setText("同步异常: " + str(e))
            self.reading_config_status.setStyleSheet("color: red;")

    def _on_shortcut_changed(self):
        self.shortcuts['add_article'] = self.add_article_edit.text().strip()
        self.shortcuts['search_article'] = self.search_article_edit.text().strip()
        self.save_shortcuts()

    def _on_article_defaults_changed(self):
        self.article_defaults['isReading'] = self.default_isReading_check.isChecked()
        self.article_defaults['isRequired'] = self.default_isRequired_check.isChecked()
        self.article_defaults['useIndependentCheckRate'] = self.default_useIndependent_check.isChecked()
        self.save_article_defaults()

    def _load_server_config(self):
        if not api_client.is_logged_in():
            self.reading_config_status.setText("未登录")
            return
        try:
            r = api_client.fetch_config()
            if r.get('code') == 0:
                data = r['data']
                self.daily_minutes_spin.blockSignals(True)
                self.target_rate_spin.blockSignals(True)
                self.daily_minutes_spin.setValue(int(float(data.get('dailyMinutes', 20))))
                self.target_rate_spin.setValue(int(float(data.get('targetCheckRate', 30))))
                self.daily_minutes_spin.blockSignals(False)
                self.target_rate_spin.blockSignals(False)
                self.reading_config_status.setText("已同步")
                self.reading_config_status.setStyleSheet("color: green;")
            else:
                self.reading_config_status.setText("加载失败: " + r.get('message', ''))
                self.reading_config_status.setStyleSheet("color: red;")
        except Exception as e:
            self.reading_config_status.setText("加载异常: " + str(e))
            self.reading_config_status.setStyleSheet("color: red;")

    # ── 备份与恢复 ──

    def _export_backup(self):
        default_name = "dailyread_backup_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".json"
        filepath, _ = QFileDialog.getSaveFileName(self, "保存备份文件", default_name, "JSON Files (*.json)")
        if not filepath:
            return
        try:
            self.data_model.export_backup(filepath)
            count = len(self.data_model.articles)
            QMessageBox.information(self, "成功", "备份已保存到：" + filepath + "\n\n包含文章：" + str(count) + " 篇")
        except Exception as e:
            QMessageBox.critical(self, "错误", "导出失败：" + str(e))

    def _import_backup(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "JSON Files (*.json)")
        if not filepath:
            return
        reply = QMessageBox.question(self, "确认导入", "导入备份会覆盖当前所有数据，确定要继续吗？")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.data_model.import_backup(filepath)
                QMessageBox.information(self, "成功", "备份导入成功")
                main_win = self.window()
                if main_win and hasattr(main_win, 'refresh_all'):
                    main_win.refresh_all()
            except Exception as e:
                QMessageBox.critical(self, "错误", "导入失败：" + str(e))

    # ── 云同步 ──

    def _sync_now(self):
        if not api_client.is_logged_in():
            QMessageBox.warning(self, "提示", "请先登录")
            return
        self.sync_status_label.setText("正在同步...")
        try:
            sync_service.pull_articles(self._on_articles_pulled)
            sync_service.pull_checkins(lambda r, s: None)
            queue_size = sync_service.queue.size()
            self.sync_status_label.setText("同步完成，队列剩余 " + str(queue_size) + " 条")
        except Exception as e:
            self.sync_status_label.setText("同步失败: " + str(e))

    def _on_articles_pulled(self, remote_articles, next_since):
        existing_by_cid = {}
        for a in self.data_model.articles:
            cid = a.get('clientId')
            if cid:
                existing_by_cid[str(cid)] = a
        for ra in remote_articles:
            cid = str(ra.get('clientId') or '')
            if not cid:
                continue
            ra['clientId'] = cid
            if cid in existing_by_cid:
                local = existing_by_cid[cid]
                ra['id'] = local.get('id')
                for i, a in enumerate(self.data_model.articles):
                    if a is local:
                        self.data_model.articles[i] = ra
                        break
                existing_by_cid[cid] = ra
            else:
                ra['id'] = self.data_model.next_article_id
                self.data_model.next_article_id += 1
                self.data_model.articles.append(ra)
                existing_by_cid[cid] = ra
        self.data_model.save()
        main_win = self.window()
        if main_win and hasattr(main_win, 'refresh_all'):
            main_win.refresh_all()

    # ── 数据维护 ──

    def _on_recalculate_completion_rate(self):
        if not self.data_model:
            QMessageBox.warning(self, "错误", "数据模型未初始化")
            return
        reply = QMessageBox.question(self, "确认操作", "将重新计算所有文章的完成率，是否继续？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        today = datetime.now()
        max_days = (today.replace(day=1, month=today.month + 1) - today.replace(day=1)).days
        for article in self.data_model.articles:
            check_in_days = article.get('checkInDays', 0)
            article['completionRate'] = round((check_in_days / max_days) * 100) if max_days > 0 else 0
        self.data_model.save()
        main_win = self.window()
        if main_win and hasattr(main_win, 'article_page'):
            main_win.article_page.refresh_table()
        QMessageBox.information(self, "成功", "已重新计算完成率")

    def _on_rebuild_article_ids(self):
        if not self.data_model:
            QMessageBox.warning(self, "错误", "数据模型未初始化")
            return
        count = len(self.data_model.articles)
        if count == 0:
            QMessageBox.information(self, "提示", "没有文章数据")
            return
        reply = QMessageBox.question(self, "确认操作", "重构后 ID 将从 1 开始顺序排列，是否继续？")
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.data_model.rebuild_article_ids()
        main_win = self.window()
        if main_win and hasattr(main_win, 'article_page'):
            main_win.article_page.refresh_table()
        QMessageBox.information(self, "成功", "已重构文章ID")



# ==================== 主窗口 ====================

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.data_model = DataModel()
        self.setup_ui()
        self.restore_window_geometry()
        self.auto_save_timer()
        self._init_sync()

    def setup_ui(self):
        self.setWindowTitle("每日阅读 · 文章与概念管理器")
        self.setMinimumSize(1000, 700)

        # 设置应用图标
        icon_path = resource_path('logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.article_page = ArticlePage(self.data_model, self)
        self.today_task_page = TodayTaskPage(self.data_model, self)
        self.settings_page = SettingsPage(self.data_model, self)

        self.tabs.addTab(self.article_page, "📖 文章管理")
        self.tabs.addTab(self.today_task_page, "📋 今日任务")
        self.tabs.addTab(self.settings_page, "⚙️ 设置")

        self.setCentralWidget(self.tabs)

        # 账号菜单
        self._setup_account_menu()

        # 状态栏
        self.statusBar().showMessage("就绪")

    def _setup_account_menu(self):
        """账号菜单栏"""
        menubar = self.menuBar()
        account_menu = menubar.addMenu("账号")

        # 显示当前用户
        self.user_action = account_menu.addAction("未登录")
        self.user_action.setEnabled(False)

        account_menu.addSeparator()

        logout_action = account_menu.addAction("退出登录")
        logout_action.triggered.connect(self._on_logout)

    def _refresh_account_menu(self):
        if api_client.user:
            self.user_action.setText(f"当前用户: {api_client.user.get('username', '')}")
        else:
            self.user_action.setText("未登录")

    def _on_logout(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "退出登录", "确定要退出登录吗？\n退出后将清除本地数据并停止同步。")
        if reply == QMessageBox.StandardButton.Yes:
            api_client.logout()
            sync_service.stop()
            # 清空本地数据 + 重置同步状态
            self.data_model.clear_local_data()
            sync_service.reset_sync_state()
            self._refresh_account_menu()
            self.refresh_all()
            # 弹出登录对话框，允许立即重新登录
            logged_in = show_login_or_register()
            if logged_in:
                self._refresh_account_menu()
                sync_service.start()
                # 全量拉取：重置 since 后拉取服务端全部文章
                sync_service.reset_sync_state()
                try:
                    sync_service.pull_articles(self._on_articles_pulled_full)
                except Exception as e:
                    print(f"[Sync] 重新登录后拉取失败: {e}")
            else:
                # 用户取消登录，关闭程序
                self.close()

    def _init_sync(self):
        """初始化同步服务"""
        self._refresh_account_menu()
        # 同步状态回调
        sync_service.set_status_callback(self._on_sync_status)
        # 启动后台同步线程
        sync_service.start()
        # 启动时重置同步状态，全量拉取服务端数据
        sync_service.reset_sync_state()
        try:
            sync_service.pull_articles(self._on_articles_pulled_full)
        except Exception as e:
            print(f"[Sync] 启动拉取失败: {e}")

    def _on_sync_status(self, msg):
        """同步状态变更通知（在主线程更新 UI）"""
        from PyQt6.QtCore import QTimer
        # 通过 QTimer.singleTask 在主线程更新
        def update():
            self.statusBar().showMessage(f"同步: {msg}", 3000)
        # 跨线程安全更新
        QTimer.singleShot(0, update)

    def _on_articles_pulled_full(self, remote_articles, next_since):
        """全量替换：用服务端文章完全替换本地数据（切换账号/首次登录时调用）"""
        new_articles = []
        for ra in remote_articles:
            cid = str(ra.get('clientId') or '')
            if not cid:
                continue
            ra['clientId'] = cid
            ra['id'] = len(new_articles) + 1
            ra.setdefault('iscontent', True)
            new_articles.append(ra)
        self.data_model.articles = new_articles
        self.data_model.next_article_id = len(new_articles) + 1
        self.data_model.save_sync()
        self.refresh_all()

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
        if self.today_task_page:
            self.today_task_page._refresh_tasks()

    def closeEvent(self, event):
        """关闭时同步保存数据（确保写完再退出）"""
        self.save_window_geometry()
        self.data_model.save_sync()
        event.accept()


# ==================== 程序入口 ====================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    app.setApplicationName("每日阅读 · 文章与概念管理器")
    app.setOrganizationName("DailyRead")

    # 大版本更新：启动前必须登录（已有有效 token 则跳过）
    if not api_client.is_logged_in() or not api_client.verify_token():
        logged_in = show_login_or_register()
        if not logged_in:
            sys.exit(0)  # 用户取消登录，退出程序

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
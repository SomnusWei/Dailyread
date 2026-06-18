#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DailyRead数据管理器
功能：
1. WebDAV同步（下载、上传）- 与Android应用保持一致
2. 文章数据可视化管理
3. 穴位数据可视化管理
4. 概念数据可视化管理
5. 搜索、筛选、查看、修改
6. 多选批量删除
7. 密码保存功能
8. 穴位图片上传/预览
9. 概念图片上传/预览
"""

# 隐藏控制台窗口（Windows平台）
import sys
if sys.platform.startswith('win'):
    try:
        import ctypes
        # 检查是否有控制台窗口
        kernel32 = ctypes.windll.kernel32
        # 获取控制台窗口句柄
        hwnd = kernel32.GetConsoleWindow()
        # 如果有控制台窗口，隐藏它
        if hwnd:
            kernel32.ShowWindow(hwnd, 0)
    except:
        pass

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
import os
import sys
import threading
import base64
import hashlib
import time
from typing import Dict, List, Optional, Any

# 尝试导入依赖
try:
    import pandas as pd
except ImportError:
    print("Installing pandas...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

try:
    import openpyxl
except ImportError:
    print("Installing openpyxl...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# 尝试导入图片处理库
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def enable_dpi_awareness():
    """启用 DPI 感知，让应用在高 DPI 显示器下显示更好"""
    if sys.platform == 'win32':
        try:
            from ctypes import c_int, windll
            # 告诉 Windows 我们的程序可以处理 DPI 缩放
            windll.user32.SetProcessDPIAware()
        except Exception:
            pass


enable_dpi_awareness()


class DailyReadManager:
    def __init__(self, root):
        self.root = root
        self.root.title("DailyRead数据管理器 v2.3")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # 不再需要共享的双击检测变量
        
        # 数据存储
        self.articles_data: List[Dict] = []
        self.acupoints_data: List[Dict] = []
        self.concepts_data: List[Dict] = []
        self.config_data: Optional[Dict] = None
        
        # WebDAV配置 - 包含密码保存
        self.webdav_url = tk.StringVar()
        self.webdav_username = tk.StringVar()
        self.webdav_password = tk.StringVar()
        self.webdav_remote_path = tk.StringVar(value="/DailyRead")
        
        # 同步内容选择
        self.sync_articles = tk.BooleanVar(value=True)
        self.sync_acupoints = tk.BooleanVar(value=True)
        self.sync_concepts = tk.BooleanVar(value=True)
        
        # 进度条相关变量
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_status_var = tk.StringVar(value="就绪")
        
        # 搜索和筛选
        self.article_search_var = tk.StringVar()
        self.article_filter_var = tk.StringVar(value="全部")
        self.acupoint_search_var = tk.StringVar()
        self.acupoint_filter_var = tk.StringVar(value="全部")
        self.concept_search_var = tk.StringVar()
        self.concept_filter_var = tk.StringVar(value="全部")
        
        # 选中项
        self.selected_article_ids = set()
        self.selected_acupoint_ids = set()
        self.selected_concept_ids = set()
        
        # 本地文件路径
        self.current_json_path: Optional[str] = None
        
        # 创建UI
        self.create_widgets()
        
        # 尝试加载上次的WebDAV配置
        self.load_webdav_config()
        
        # 尝试加载本地数据
        self.load_local_data()
    
    def load_webdav_config(self):
        """加载WebDAV配置（包含密码）"""
        config_file = "webdav_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.webdav_url.set(config.get('url', ''))
                    self.webdav_username.set(config.get('username', ''))
                    self.webdav_password.set(config.get('password', ''))  # 新增：保存密码
                    self.webdav_remote_path.set(config.get('remote_path', '/DailyRead'))
            except Exception as e:
                print(f"加载配置失败: {e}")
    
    def save_webdav_config(self):
        """保存WebDAV配置（包含密码）"""
        config_file = "webdav_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'url': self.webdav_url.get(),
                    'username': self.webdav_username.get(),
                    'password': self.webdav_password.get(),
                    'remote_path': self.webdav_remote_path.get(),
                    'sync_articles': self.sync_articles.get(),
                    'sync_acupoints': self.sync_acupoints.get(),
                    'sync_concepts': self.sync_concepts.get()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def load_webdav_config(self):
        """加载WebDAV配置（包含密码）"""
        config_file = "webdav_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.webdav_url.set(config.get('url', ''))
                    self.webdav_username.set(config.get('username', ''))
                    self.webdav_password.set(config.get('password', ''))
                    self.webdav_remote_path.set(config.get('remote_path', '/DailyRead'))
                    self.sync_articles.set(config.get('sync_articles', True))
                    self.sync_acupoints.set(config.get('sync_acupoints', True))
                    self.sync_concepts.set(config.get('sync_concepts', True))
            except Exception as e:
                print(f"加载配置失败: {e}")
    
    def save_local_data(self):
        """保存本地数据到文件"""
        data_file = "daily_read_local_data.json"
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'articles': self.articles_data,
                    'acupoints': self.acupoints_data,
                    'concepts': self.concepts_data,
                    'config': self.config_data
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存本地数据失败: {e}")
    
    def load_local_data(self):
        """从文件加载本地数据"""
        data_file = "daily_read_local_data.json"
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.articles_data = data.get('articles', [])
                    self.acupoints_data = data.get('acupoints', [])
                    self.concepts_data = data.get('concepts', [])
                    self.config_data = data.get('config')
                    
                    # 刷新界面
                    self.refresh_article_table()
                    self.refresh_acupoint_table()
                    self.refresh_concept_table()
                    self.update_meridian_filter()
                    self.update_category_filter()
                    
                    print("本地数据加载成功")
            except Exception as e:
                print(f"加载本地数据失败: {e}")
    
    # ==================== 增量同步功能 ====================
    
    class SyncIndex:
        """同步索引类 - 跟踪文件版本信息"""
        def __init__(self, sync_time=None, files=None):
            self.version = 5
            self.sync_time = sync_time or datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            self.files = files or {}  # {type: {filename, syncTime, count, hash}}
        
        def to_dict(self):
            return {
                'version': self.version,
                'syncTime': self.sync_time,
                'files': self.files
            }
        
        @classmethod
        def from_dict(cls, data):
            if not data:
                return cls()
            return cls(
                sync_time=data.get('syncTime'),
                files=data.get('files', {})
            )
    
    def calculate_hash(self, data_str):
        """计算数据的SHA-256哈希值"""
        hash_obj = hashlib.sha256(data_str.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # 使用前16个字符
    
    def load_local_sync_index(self):
        """加载本地同步索引"""
        index_file = "sync_index.json"
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return self.SyncIndex.from_dict(data)
            except Exception as e:
                print(f"加载本地索引失败: {e}")
        return self.SyncIndex()
    
    def save_local_sync_index(self, sync_index):
        """保存本地同步索引"""
        index_file = "sync_index.json"
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(sync_index.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存本地索引失败: {e}")
    
    def webdav_download_file(self, server_url, username, password, remote_path, filename):
        """下载单个文件"""
        base_url = server_url.rstrip('/')
        clean_remote_path = remote_path if remote_path.startswith('/') else '/' + remote_path
        full_remote_path = f"{clean_remote_path.rstrip('/')}/{filename}"
        full_url = base_url + full_remote_path
        
        headers = {'Content-Type': 'application/json'}
        from requests.auth import HTTPBasicAuth
        
        response = requests.get(full_url, 
                                auth=HTTPBasicAuth(username, password),
                                headers=headers,
                                timeout=(60, 600))
        
        if response.status_code in [200, 207]:
            return response.text
        return None
    
    def webdav_upload_file(self, server_url, username, password, remote_path, filename, data_str):
        """上传单个文件，带进度显示"""
        base_url = server_url.rstrip('/')
        clean_remote_path = remote_path if remote_path.startswith('/') else '/' + remote_path
        full_remote_path = f"{clean_remote_path.rstrip('/')}/{filename}"
        full_url = base_url + full_remote_path
        
        headers = {'Content-Type': 'application/json'}
        from requests.auth import HTTPBasicAuth
        data_bytes = data_str.encode('utf-8')
        
        class ProgressUpload:
            def __init__(self, data, callback):
                self.data = data
                self.callback = callback
                self.total_size = len(data)
                self.bytes_read = 0
                self.last_update = time.time()
                self.last_bytes = 0
            
            def read(self, size=-1):
                if size == -1:
                    chunk = self.data[self.bytes_read:]
                else:
                    chunk = self.data[self.bytes_read:self.bytes_read + size]
                
                self.bytes_read += len(chunk)
                current_time = time.time()
                if self.callback and current_time - self.last_update >= 0.1:
                    progress = (self.bytes_read / self.total_size) * 100.0
                    bytes_delta = self.bytes_read - self.last_bytes
                    time_delta = current_time - self.last_update
                    speed = bytes_delta / time_delta if time_delta > 0 else 0
                    self.callback(progress, self.bytes_read, self.total_size, speed)
                    self.last_update = current_time
                    self.last_bytes = self.bytes_read
                
                return chunk
            
            def __len__(self):
                return self.total_size
        
        upload_obj = ProgressUpload(data_bytes, None)
        response = requests.put(full_url, 
                              data=upload_obj,
                              auth=HTTPBasicAuth(username, password),
                              headers=headers,
                              timeout=(60, 600))
        
        return response.status_code in [200, 201, 204]
    
    def create_widgets(self):
        """创建主界面"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding="10")
        toolbar.pack(fill=tk.X)
        
        # 文件操作
        file_frame = ttk.LabelFrame(toolbar, text="文件操作", padding="8")
        file_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(file_frame, text="打开JSON文件", command=self.open_json_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="保存JSON文件", command=self.save_json_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="导出Excel", command=self.export_excel).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="导入Excel", command=self.import_excel).pack(side=tk.LEFT, padx=2)
        
        # WebDAV操作
        webdav_frame = ttk.LabelFrame(toolbar, text="WebDAV同步", padding="8")
        webdav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Label(webdav_frame, text="URL:").pack(side=tk.LEFT)
        ttk.Entry(webdav_frame, textvariable=self.webdav_url, width=25).pack(side=tk.LEFT, padx=2)
        ttk.Label(webdav_frame, text="用户名:").pack(side=tk.LEFT)
        ttk.Entry(webdav_frame, textvariable=self.webdav_username, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Label(webdav_frame, text="密码:").pack(side=tk.LEFT)
        ttk.Entry(webdav_frame, textvariable=self.webdav_password, width=12, show="*").pack(side=tk.LEFT, padx=2)
        ttk.Label(webdav_frame, text="路径:").pack(side=tk.LEFT)
        ttk.Entry(webdav_frame, textvariable=self.webdav_remote_path, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(webdav_frame, text="测试连接", command=self.test_webdav).pack(side=tk.LEFT, padx=2)
        ttk.Button(webdav_frame, text="下载数据", command=self.webdav_download).pack(side=tk.LEFT, padx=2)
        ttk.Button(webdav_frame, text="强制全量下载", command=self.webdav_download_force_full).pack(side=tk.LEFT, padx=2)
        ttk.Button(webdav_frame, text="上传数据", command=self.webdav_upload).pack(side=tk.LEFT, padx=2)
        
        # 同步内容选择
        sync_options_frame = ttk.LabelFrame(toolbar, text="同步内容", padding="8")
        sync_options_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Checkbutton(sync_options_frame, text="文章", variable=self.sync_articles, command=self.save_webdav_config).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(sync_options_frame, text="穴位", variable=self.sync_acupoints, command=self.save_webdav_config).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(sync_options_frame, text="概念", variable=self.sync_concepts, command=self.save_webdav_config).pack(side=tk.LEFT, padx=5)
        
        # 主内容区 - 标签页
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 文章管理标签页
        articles_tab = ttk.Frame(notebook)
        notebook.add(articles_tab, text="文章管理")
        self.create_articles_tab(articles_tab)
        
        # 穴位管理标签页
        acupoints_tab = ttk.Frame(notebook)
        notebook.add(acupoints_tab, text="穴位管理")
        self.create_acupoints_tab(acupoints_tab)
        
        # 概念管理标签页
        concepts_tab = ttk.Frame(notebook)
        notebook.add(concepts_tab, text="概念管理")
        self.create_concepts_tab(concepts_tab)
        
        # 底部状态栏 - 增加进度条
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 进度条
        progress_frame = ttk.Frame(bottom_frame, padding="5 5 5 0")
        progress_frame.pack(fill=tk.X)
        ttk.Label(progress_frame, text="进度:").pack(side=tk.LEFT, padx=(5, 0))
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_status_var)
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        # 普通状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X)
    
    def create_articles_tab(self, parent):
        """创建文章管理标签页"""
        # 顶部操作栏
        top_frame = ttk.Frame(parent, padding="10")
        top_frame.pack(fill=tk.X)
        
        # 搜索和筛选
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        ttk.Entry(search_frame, textvariable=self.article_search_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_articles).pack(side=tk.LEFT)
        
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(filter_frame, text="筛选:").pack(side=tk.LEFT)
        article_filter_combo = ttk.Combobox(filter_frame, textvariable=self.article_filter_var, 
                                             values=["全部", "必读", "正在阅读", "使用独立完成率"],
                                             state="readonly", width=20)
        article_filter_combo.pack(side=tk.LEFT, padx=5)
        article_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_articles())
        
        # 操作按钮
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="添加文章", command=self.add_article).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="编辑选中", command=self.edit_article).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除选中", command=self.delete_selected_articles).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="全选", command=self.select_all_articles).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="取消全选", command=self.deselect_all_articles).pack(side=tk.LEFT, padx=2)
        
        # 数据表格
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.article_tree = ttk.Treeview(table_frame, 
                                         columns=("id", "title", "chineseChars", "isRequired", "isReading", 
                                                  "useIndependentCheckRate", "independentCheckRate"),
                                         show="headings", yscrollcommand=scrollbar.set)
        
        # 设置列标题
        self.article_tree.heading("id", text="ID")
        self.article_tree.heading("title", text="标题")
        self.article_tree.heading("chineseChars", text="字数")
        self.article_tree.heading("isRequired", text="必读")
        self.article_tree.heading("isReading", text="正在阅读")
        self.article_tree.heading("useIndependentCheckRate", text="独立完成率")
        self.article_tree.heading("independentCheckRate", text="独立完成率值")
        
        # 设置列宽
        self.article_tree.column("id", width=60)
        self.article_tree.column("title", width=300)
        self.article_tree.column("chineseChars", width=80)
        self.article_tree.column("isRequired", width=60)
        self.article_tree.column("isReading", width=80)
        self.article_tree.column("useIndependentCheckRate", width=100)
        self.article_tree.column("independentCheckRate", width=100)
        
        self.article_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.article_tree.yview)
        
        # 绑定事件
        self.article_tree.bind("<<TreeviewSelect>>", self.on_article_select)
        self.article_tree.bind("<Double-1>", self.on_article_double_click)
        
        # 统计信息
        self.article_stats_var = tk.StringVar(value="文章数: 0 | 选中: 0")
        stats_label = ttk.Label(parent, textvariable=self.article_stats_var)
        stats_label.pack(pady=5)
    
    def create_acupoints_tab(self, parent):
        """创建穴位管理标签页"""
        # 顶部操作栏
        top_frame = ttk.Frame(parent, padding="10")
        top_frame.pack(fill=tk.X)
        
        # 搜索和筛选
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        ttk.Entry(search_frame, textvariable=self.acupoint_search_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_acupoints).pack(side=tk.LEFT)
        
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(filter_frame, text="筛选经络:").pack(side=tk.LEFT)
        self.acupoint_filter_combo = ttk.Combobox(filter_frame, textvariable=self.acupoint_filter_var, 
                                                  values=["全部"], state="readonly", width=20)
        self.acupoint_filter_combo.pack(side=tk.LEFT, padx=5)
        self.acupoint_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_acupoints())
        
        # 操作按钮
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="添加穴位", command=self.add_acupoint).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="编辑选中", command=self.edit_acupoint).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除选中", command=self.delete_selected_acupoints).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="批量导入图片", command=self.batch_import_acupoint_images).pack(side=tk.LEFT, padx=2)
        
        # 数据表格
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.acupoint_tree = ttk.Treeview(table_frame, 
                                          columns=("id", "acupoint", "meridian", "acupointProperty", "location", 
                                                   "function", "indications"),
                                          show="headings", yscrollcommand=scrollbar.set)
        
        # 设置列标题
        self.acupoint_tree.heading("id", text="ID")
        self.acupoint_tree.heading("acupoint", text="穴位")
        self.acupoint_tree.heading("meridian", text="经络")
        self.acupoint_tree.heading("acupointProperty", text="穴性")
        self.acupoint_tree.heading("location", text="定位")
        self.acupoint_tree.heading("function", text="功效")
        self.acupoint_tree.heading("indications", text="主治")
        
        # 设置列宽
        self.acupoint_tree.column("id", width=60)
        self.acupoint_tree.column("acupoint", width=100)
        self.acupoint_tree.column("meridian", width=120)
        self.acupoint_tree.column("acupointProperty", width=100)
        self.acupoint_tree.column("location", width=200)
        self.acupoint_tree.column("function", width=200)
        self.acupoint_tree.column("indications", width=200)
        
        self.acupoint_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.acupoint_tree.yview)
        
        # 绑定事件
        self.acupoint_tree.bind("<<TreeviewSelect>>", self.on_acupoint_select)
        self.acupoint_tree.bind("<Double-1>", self.on_acupoint_double_click)
        
        # 统计信息
        self.acupoint_stats_var = tk.StringVar(value="穴位数: 0 | 选中: 0")
        stats_label = ttk.Label(parent, textvariable=self.acupoint_stats_var)
        stats_label.pack(pady=5)
    
    def create_concepts_tab(self, parent):
        """创建概念管理标签页"""
        # 顶部操作栏
        top_frame = ttk.Frame(parent, padding="10")
        top_frame.pack(fill=tk.X)
        
        # 搜索和筛选
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        ttk.Entry(search_frame, textvariable=self.concept_search_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_concepts).pack(side=tk.LEFT)
        
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(filter_frame, text="筛选分类:").pack(side=tk.LEFT)
        self.concept_filter_combo = ttk.Combobox(filter_frame, textvariable=self.concept_filter_var, 
                                                   values=["全部"], state="readonly", width=20)
        self.concept_filter_combo.pack(side=tk.LEFT, padx=5)
        self.concept_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_concepts())
        
        # 操作按钮
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="添加概念", command=self.add_concept).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="编辑选中", command=self.edit_concept).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除选中", command=self.delete_selected_concepts).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="全选", command=self.select_all_concepts).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="取消全选", command=self.deselect_all_concepts).pack(side=tk.LEFT, padx=2)
        
        # 数据表格
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.concept_tree = ttk.Treeview(table_frame, 
                                          columns=("id", "title", "category", "subject", "subChapter", "isEnabled"),
                                          show="headings", yscrollcommand=scrollbar.set)
        
        # 设置列标题
        self.concept_tree.heading("id", text="ID")
        self.concept_tree.heading("title", text="标题")
        self.concept_tree.heading("category", text="分类")
        self.concept_tree.heading("subject", text="科目")
        self.concept_tree.heading("subChapter", text="子章节")
        self.concept_tree.heading("isEnabled", text="启用")
        
        # 设置列宽
        self.concept_tree.column("id", width=60)
        self.concept_tree.column("title", width=200)
        self.concept_tree.column("category", width=120)
        self.concept_tree.column("subject", width=120)
        self.concept_tree.column("subChapter", width=120)
        self.concept_tree.column("isEnabled", width=60)
        
        self.concept_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.concept_tree.yview)
        
        # 绑定事件
        self.concept_tree.bind("<<TreeviewSelect>>", self.on_concept_select)
        self.concept_tree.bind("<Double-1>", self.on_concept_double_click)
        
        # 统计信息
        self.concept_stats_var = tk.StringVar(value="概念数: 0 | 选中: 0")
        stats_label = ttk.Label(parent, textvariable=self.concept_stats_var)
        stats_label.pack(pady=5)
    
    # ==================== 文件操作 ====================
    
    def open_json_file(self):
        """打开JSON文件"""
        file_path = filedialog.askopenfilename(
            title="打开JSON文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 尝试从articles字段读取（WebDAV同步格式），如果没有则尝试contents（备份格式）
            self.articles_data = data.get('articles', data.get('contents', []))
            self.acupoints_data = data.get('acupoints', [])
            self.concepts_data = data.get('concepts', [])
            self.config_data = data.get('config')
            
            self.current_json_path = file_path
            
            # 更新界面
            self.refresh_article_table()
            self.refresh_acupoint_table()
            self.refresh_concept_table()
            self.update_meridian_filter()
            self.update_category_filter()
            
            self.status_var.set(f"已加载: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", f"文件加载成功！\n文章: {len(self.articles_data)}条\n穴位: {len(self.acupoints_data)}个\n概念: {len(self.concepts_data)}个")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败：\n{str(e)}")
    
    def save_json_file(self):
        """保存JSON文件"""
        if not self.articles_data and not self.acupoints_data and not self.concepts_data:
            messagebox.showwarning("警告", "没有数据可保存！")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存JSON文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialfile=f"daily_read_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if not file_path:
            return
        
        try:
            now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
            # 清理和标准化数据 - 确保格式一致
            def normalize_article(article):
                normalized = article.copy()
                normalized.setdefault('id', 0)
                normalized.setdefault('title', '')
                normalized.setdefault('content', '')
                normalized.setdefault('contentHtml', None)
                normalized.setdefault('chineseChars', 0)
                normalized.setdefault('fontFamily', 'default')
                normalized.setdefault('fontSize', 16)
                normalized.setdefault('fontColor', '#000000')
                normalized.setdefault('isBold', False)
                normalized.setdefault('isReading', False)
                normalized.setdefault('isRequired', False)
                normalized.setdefault('requiredDays', '')
                normalized.setdefault('useIndependentCheckRate', False)
                normalized.setdefault('independentCheckRate', 30.0)
                normalized.setdefault('createTime', now)
                return normalized
            
            def normalize_acupoint(acupoint):
                normalized = acupoint.copy()
                normalized.setdefault('id', 0)
                normalized.setdefault('acupoint', '')
                normalized.setdefault('meridian', '')
                normalized.setdefault('acupointProperty', '')
                normalized.setdefault('location', '')
                normalized.setdefault('function', '')
                normalized.setdefault('indications', '')
                normalized.setdefault('anatomy', '')
                normalized.setdefault('operation', '')
                normalized.setdefault('contraindications', '')
                normalized.setdefault('locationImagePath', None)
                normalized.setdefault('locationImageBase64', None)
                normalized.setdefault('note', '')
                normalized.setdefault('createTime', now)
                return normalized
            
            def normalize_concept(concept):
                normalized = concept.copy()
                normalized.setdefault('id', 0)
                normalized.setdefault('title', '')
                normalized.setdefault('content', '')
                normalized.setdefault('category', '')
                normalized.setdefault('subject', '')
                normalized.setdefault('subChapter', '')
                normalized.setdefault('imagePath', None)
                normalized.setdefault('imageBase64', None)
                normalized.setdefault('note', '')
                normalized.setdefault('isEnabled', True)
                normalized.setdefault('createTime', now)
                normalized.setdefault('lastModified', now)
                return normalized
            
            # 标准化数据
            normalized_articles = [normalize_article(a) for a in self.articles_data]
            normalized_acupoints = [normalize_acupoint(a) for a in self.acupoints_data]
            normalized_concepts = [normalize_concept(c) for c in self.concepts_data]
            
            # 标准化config
            config_data = self.config_data or {}
            normalized_config = {
                'dailyMinutes': config_data.get('dailyMinutes', 20),
                'targetCheckRate': config_data.get('targetCheckRate', 30.0),
                'keepScreenOn': config_data.get('keepScreenOn', False),
                'autoSyncWebDav': config_data.get('autoSyncWebDav', False),
                'yesterdayLongArticleIds': config_data.get('yesterdayLongArticleIds', '')
            }
            
            # 保存为WebDAV同步格式（同时保留备份格式）
            export_data = {
                'version': 4,
                'exportTime': now,
                'dataType': 'all',
                'config': normalized_config,
                'articles': normalized_articles,  # WebDAV同步使用的字段
                'contents': normalized_articles,  # 备份格式使用的字段（保持兼容性）
                'checkIns': [],
                'acupoints': normalized_acupoints,
                'concepts': normalized_concepts
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.current_json_path = file_path
            self.status_var.set(f"已保存: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", "文件保存成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败：\n{str(e)}")
    
    def export_excel(self):
        """导出Excel文件"""
        if not self.articles_data and not self.acupoints_data and not self.concepts_data:
            messagebox.showwarning("警告", "没有数据可导出！")
            return
        
        # 选择导出类型
        choice = messagebox.askquestion("导出选择", "导出文章数据？\n（是=文章，否=穴位，取消=概念）", icon='question')
        
        data_type = 'articles'
        if choice == 'no':
            # 再次询问是穴位还是概念
            choice2 = messagebox.askquestion("导出选择", "导出穴位数据？\n（是=穴位，否=概念）", icon='question')
            data_type = 'acupoints' if choice2 == 'yes' else 'concepts'
        
        if data_type == 'articles':
            default_name = '文章数据.xlsx'
        elif data_type == 'acupoints':
            default_name = '穴位数据.xlsx'
        else:
            default_name = '概念数据.xlsx'
        
        file_path = filedialog.asksaveasfilename(
            title="导出Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=default_name
        )
        
        if not file_path:
            return
        
        try:
            if data_type == 'articles':
                df = pd.DataFrame(self.articles_data)
                # 只保留相关列
                cols_to_keep = ['id', 'title', 'content', 'contentHtml', 'chineseChars', 
                                'fontFamily', 'fontSize', 'fontColor', 'isBold', 
                                'isReading', 'isRequired', 'requiredDays', 
                                'useIndependentCheckRate', 'independentCheckRate']
                df = df[cols_to_keep] if all(c in df.columns for c in cols_to_keep) else df
            elif data_type == 'acupoints':
                df = pd.DataFrame(self.acupoints_data)
            else:
                df = pd.DataFrame(self.concepts_data)
                # 只保留相关列
                cols_to_keep = ['id', 'title', 'content', 'category', 'subject', 'subChapter', 
                                'note', 'isEnabled']
                df = df[cols_to_keep] if all(c in df.columns for c in cols_to_keep) else df
            
            df.to_excel(file_path, index=False, engine='openpyxl')
            messagebox.showinfo("成功", "Excel导出成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：\n{str(e)}")
    
    def import_excel(self):
        """导入Excel文件"""
        file_path = filedialog.askopenfilename(
            title="导入Excel",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        # 选择导入类型
        choice = messagebox.askquestion("导入选择", "导入文章数据？\n（是=文章，否=穴位，取消=概念）", icon='question')
        
        data_type = 'articles'
        if choice == 'no':
            # 再次询问是穴位还是概念
            choice2 = messagebox.askquestion("导入选择", "导入穴位数据？\n（是=穴位，否=概念）", icon='question')
            data_type = 'acupoints' if choice2 == 'yes' else 'concepts'
        
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            df = df.fillna('')
            
            now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            max_id = 0
            
            if data_type == 'articles':
                max_id = max((a.get('id', 0) for a in self.articles_data), default=0)
                
                for _, row in df.iterrows():
                    max_id += 1
                    article = {
                        'id': max_id,
                        'title': str(row.get('title', row.get('标题', ''))),
                        'content': str(row.get('content', row.get('内容', ''))),
                        'contentHtml': str(row.get('contentHtml', row.get('内容HTML', ''))) or None,
                        'chineseChars': int(row.get('chineseChars', row.get('中文字数', 0))),
                        'fontFamily': str(row.get('fontFamily', row.get('字体', 'default'))),
                        'fontSize': int(row.get('fontSize', row.get('字号', 16))),
                        'fontColor': str(row.get('fontColor', row.get('字体颜色', '#000000'))),
                        'isBold': bool(row.get('isBold', row.get('加粗', False))),
                        'isReading': bool(row.get('isReading', row.get('正在阅读', True))),
                        'isRequired': bool(row.get('isRequired', row.get('必读', False))),
                        'requiredDays': str(row.get('requiredDays', row.get('必读日期', ''))),
                        'useIndependentCheckRate': bool(row.get('useIndependentCheckRate', row.get('使用独立完成率', False))),
                        'independentCheckRate': float(row.get('independentCheckRate', row.get('独立完成率', 30.0))),
                        'createTime': now
                    }
                    self.articles_data.append(article)
                
                self.refresh_article_table()
            elif data_type == 'acupoints':
                max_id = max((a.get('id', 0) for a in self.acupoints_data), default=0)
                
                for _, row in df.iterrows():
                    max_id += 1
                    acupoint = {
                        'id': max_id,
                        'acupoint': str(row.get('acupoint', row.get('穴位', ''))),
                        'meridian': str(row.get('meridian', row.get('经络', ''))),
                        'acupointProperty': str(row.get('acupointProperty', row.get('穴性', ''))),
                        'location': str(row.get('location', row.get('定位', ''))),
                        'function': str(row.get('function', row.get('功效', ''))),
                        'indications': str(row.get('indications', row.get('主治', ''))),
                        'anatomy': str(row.get('anatomy', row.get('解剖', ''))),
                        'operation': str(row.get('operation', row.get('操作', ''))),
                        'contraindications': str(row.get('contraindications', row.get('禁忌', ''))),
                        'locationImagePath': str(row.get('locationImagePath', row.get('穴位定位图路径', ''))) or None,
                        'note': str(row.get('note', row.get('备注', ''))),
                        'createTime': now
                    }
                    self.acupoints_data.append(acupoint)
                
                self.refresh_acupoint_table()
                self.update_meridian_filter()
            else:
                # 导入概念数据
                max_id = max((c.get('id', 0) for c in self.concepts_data), default=0)
                
                for _, row in df.iterrows():
                    max_id += 1
                    concept = {
                        'id': max_id,
                        'title': str(row.get('title', row.get('标题', ''))),
                        'content': str(row.get('content', row.get('内容', ''))),
                        'category': str(row.get('category', row.get('分类', ''))),
                        'subject': str(row.get('subject', row.get('科目', ''))),
                        'subChapter': str(row.get('subChapter', row.get('子章节', ''))),
                        'note': str(row.get('note', row.get('备注', ''))),
                        'isEnabled': bool(row.get('isEnabled', row.get('启用', True))),
                        'createTime': now,
                        'lastModified': now
                    }
                    self.concepts_data.append(concept)
                
                self.refresh_concept_table()
                self.update_category_filter()
            
            messagebox.showinfo("成功", "Excel导入成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：\n{str(e)}")
    
    # ==================== WebDAV操作 - 完全按照Android实现 ====================
    
    def get_full_url(self, server_url, remote_path):
        """构建完整URL - 与Android保持一致"""
        base_url = server_url.rstrip('/')
        clean_path = remote_path if remote_path.startswith('/') else f"/{remote_path}"
        return f"{base_url}{clean_path}"
    
    def test_webdav(self):
        """测试WebDAV连接 - 与Android实现完全一致"""
        server_url = self.webdav_url.get()
        username = self.webdav_username.get()
        password = self.webdav_password.get()
        remote_path = self.webdav_remote_path.get()
        
        if not server_url:
            messagebox.showwarning("警告", "请输入WebDAV URL！")
            return
        
        self.save_webdav_config()
        
        def test():
            try:
                self.root.after(0, lambda: self.status_var.set("正在测试连接..."))
                
                # 构建与Android一致的URL
                base_url = server_url.rstrip('/')
                clean_remote_path = remote_path if remote_path.startswith('/') else '/' + remote_path
                full_url = base_url + clean_remote_path
                
                print(f"测试连接到: {full_url}")
                
                # PROPFIND body - 与Android完全一致
                propfind_body = """<?xml version="1.0" encoding="utf-8"?>
<propfind xmlns="DAV:">
    <prop>
        <resourcetype/>
    </prop>
</propfind>"""
                
                headers = {
                    'Content-Type': 'application/xml',
                    'Depth': '0'
                }
                
                from requests.auth import HTTPBasicAuth
                
                response = requests.request('PROPFIND', full_url, 
                                      auth=HTTPBasicAuth(username, password),
                                      headers=headers,
                                      data=propfind_body,
                                      timeout=(60, 120))  # (connect timeout, read timeout)
                
                print(f"PROPFIND响应状态码: {response.status_code}")
                
                if response.status_code in [200, 207]:
                    self.root.after(0, lambda: messagebox.showinfo("成功", "WebDAV连接成功！"))
                    self.root.after(0, lambda: self.status_var.set("WebDAV连接成功"))
                elif response.status_code == 404:
                    # 尝试创建目录
                    self.try_create_directory(server_url, remote_path, username, password)
                else:
                    error_msg = f"连接失败，状态码: {response.status_code}"
                    try:
                        error_detail = response.text
                        if error_detail:
                            error_msg += f"\n服务器响应: {error_detail}"
                    except:
                        pass
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    self.root.after(0, lambda: self.status_var.set("WebDAV连接失败"))
                    
            except Exception as e:
                import traceback
                print(f"连接异常: {str(e)}")
                print(traceback.format_exc())
                self.root.after(0, lambda: messagebox.showerror("错误", f"连接错误：\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("WebDAV连接失败"))
        
        threading.Thread(target=test, daemon=True).start()
    
    def try_create_directory(self, server_url, remote_path, username, password):
        """尝试创建目录 - 与Android一致"""
        def create():
            try:
                # 构建与Android一致的URL
                base_url = server_url.rstrip('/')
                clean_remote_path = remote_path if remote_path.startswith('/') else '/' + remote_path
                full_url = base_url + clean_remote_path
                
                print(f"尝试创建目录: {full_url}")
                
                from requests.auth import HTTPBasicAuth
                
                response = requests.request('MKCOL', full_url, 
                                      auth=HTTPBasicAuth(username, password),
                                      timeout=(60, 120))  # (connect timeout, read timeout)
                
                print(f"MKCOL响应状态码: {response.status_code}")
                
                if response.status_code in [200, 201, 405]:
                    self.root.after(0, lambda: messagebox.showinfo("成功", "WebDAV连接成功！"))
                    self.root.after(0, lambda: self.status_var.set("WebDAV连接成功"))
                else:
                    error_msg = f"创建目录失败，状态码: {response.status_code}"
                    try:
                        error_detail = response.text
                        if error_detail:
                            error_msg += f"\n服务器响应: {error_detail}"
                    except:
                        pass
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    self.root.after(0, lambda: self.status_var.set("WebDAV连接失败"))
                    
            except Exception as e:
                import traceback
                print(f"创建目录异常: {str(e)}")
                print(traceback.format_exc())
                self.root.after(0, lambda: messagebox.showerror("错误", f"创建目录错误：\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("WebDAV连接失败"))
        
        threading.Thread(target=create, daemon=True).start()
    
    def webdav_download(self):
        """从WebDAV下载数据 - 增量同步版，支持选择性同步"""
        server_url = self.webdav_url.get()
        username = self.webdav_username.get()
        password = self.webdav_password.get()
        remote_path = self.webdav_remote_path.get()
        
        if not server_url:
            messagebox.showwarning("警告", "请输入WebDAV URL！")
            return
        
        self.save_webdav_config()
        
        def download_incremental():
            try:
                self.root.after(0, lambda: self.status_var.set("正在检查远程索引..."))
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("检查远程索引..."))
                
                print("开始增量下载...")
                
                remote_sync_index_json = self.webdav_download_file(
                    server_url, username, password, remote_path, "sync_index.json"
                )
                
                if remote_sync_index_json:
                    try:
                        remote_sync_index = self.SyncIndex.from_dict(json.loads(remote_sync_index_json))
                        print(f"远程索引版本: {remote_sync_index.version}")
                        
                        local_sync_index = self.load_local_sync_index()
                        print(f"本地索引版本: {local_sync_index.version}")
                        
                        need_full_sync = False
                        changed_files = []
                        
                        # 只检查用户选择同步的文件
                        for file_type, remote_file_info in remote_sync_index.files.items():
                            # 检查是否是用户选择同步的类型
                            if file_type == 'articles' and not self.sync_articles.get():
                                continue
                            if file_type == 'acupoints' and not self.sync_acupoints.get():
                                continue
                            if file_type == 'concepts' and not self.sync_concepts.get():
                                continue
                            
                            local_file_info = local_sync_index.files.get(file_type, {})
                            remote_hash = remote_file_info.get('hash', '')
                            local_hash = local_file_info.get('hash', '')
                            
                            if remote_hash != local_hash:
                                changed_files.append(file_type)
                                print(f"文件 {file_type} 需要更新: 远程={remote_hash[:8]}, 本地={local_hash[:8] if local_hash else 'None'}")
                        
                        if not changed_files:
                            self.root.after(0, lambda: self.progress_var.set(100.0))
                            self.root.after(0, lambda: self.progress_status_var.set("已是最新！"))
                            self.root.after(0, lambda: messagebox.showinfo("成功", "选择的数据已是最新，无需下载！"))
                            self.root.after(0, lambda: self.status_var.set("已是最新"))
                            return
                        
                        self.root.after(0, lambda: self.progress_status_var.set(f"需要更新: {', '.join(changed_files)}"))
                        
                        for i, file_type in enumerate(changed_files):
                            progress_start = 10.0 + (i / len(changed_files)) * 70.0
                            progress_end = 10.0 + ((i + 1) / len(changed_files)) * 70.0
                            
                            self.root.after(0, lambda p=progress_start: self.progress_var.set(p))
                            self.root.after(0, lambda: self.progress_status_var.set(f"下载 {file_type}..."))
                            
                            filename = f"{file_type}.json"
                            file_content = self.webdav_download_file(
                                server_url, username, password, remote_path, filename
                            )
                            
                            if file_content:
                                file_data = json.loads(file_content)
                                if file_type == 'articles':
                                    self.articles_data = file_data
                                elif file_type == 'acupoints':
                                    self.acupoints_data = file_data
                                elif file_type == 'concepts':
                                    self.concepts_data = file_data
                                elif file_type == 'checkins':
                                    pass
                            
                            self.root.after(0, lambda p=progress_end: self.progress_var.set(p))
                        
                        # 构建新的索引，保留未同步文件的本地信息
                        new_files = {}
                        for file_type, file_info in remote_sync_index.files.items():
                            # 对于用户选择同步的，使用远程索引信息
                            if (file_type == 'articles' and self.sync_articles.get()) or \
                               (file_type == 'acupoints' and self.sync_acupoints.get()) or \
                               (file_type == 'concepts' and self.sync_concepts.get()) or \
                               file_type == 'checkins':
                                new_files[file_type] = file_info
                            # 对于未选择同步的，保留本地索引信息
                            elif file_type in local_sync_index.files:
                                new_files[file_type] = local_sync_index.files[file_type]
                        
                        new_sync_index = self.SyncIndex(
                            sync_time=remote_sync_index.sync_time,
                            files=new_files
                        )
                        
                        self.save_local_sync_index(new_sync_index)
                        
                        # 保存本地数据
                        self.save_local_data()
                        
                        self.root.after(0, lambda: self.progress_var.set(85.0))
                        self.root.after(0, lambda: self.progress_status_var.set("刷新界面..."))
                        
                        self.root.after(0, self.refresh_article_table)
                        self.root.after(0, self.refresh_acupoint_table)
                        self.root.after(0, self.refresh_concept_table)
                        self.root.after(0, self.update_meridian_filter)
                        self.root.after(0, self.update_category_filter)
                        
                        self.root.after(0, lambda: self.progress_var.set(100.0))
                        self.root.after(0, lambda: self.progress_status_var.set("完成！"))
                        
                        # 计算下载的统计信息
                        downloaded_article_count = len(self.articles_data) if 'articles' in changed_files else 0
                        downloaded_acupoint_count = len(self.acupoints_data) if 'acupoints' in changed_files else 0
                        downloaded_concept_count = len(self.concepts_data) if 'concepts' in changed_files else 0
                        
                        self.root.after(0, lambda: messagebox.showinfo("成功", 
                            f"增量下载成功！\n"
                            f"更新了: {', '.join(changed_files)}\n"
                            f"文章: {downloaded_article_count}条\n"
                            f"穴位: {downloaded_acupoint_count}个\n"
                            f"概念: {downloaded_concept_count}个"))
                        self.root.after(0, lambda: self.status_var.set("增量下载成功"))
                        
                    except json.JSONDecodeError as e:
                        print(f"解析远程索引失败: {e}, 尝试全量下载")
                        self.webdav_download_full(server_url, username, password, remote_path)
                else:
                    print("没有远程索引文件，尝试全量下载")
                    self.webdav_download_full(server_url, username, password, remote_path)
                    
            except Exception as e:
                import traceback
                print(f"增量下载异常: {str(e)}")
                print(traceback.format_exc())
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("失败，尝试全量下载"))
                self.webdav_download_full(server_url, username, password, remote_path)
        
        threading.Thread(target=download_incremental, daemon=True).start()
    
    def webdav_download_full(self, server_url, username, password, remote_path):
        """全量下载 - 作为回退方案，支持选择性同步"""
        def download_full():
            try:
                self.root.after(0, lambda: self.status_var.set("正在全量下载..."))
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("全量下载中..."))
                
                base_url = server_url.rstrip('/')
                clean_remote_path = remote_path if remote_path.startswith('/') else '/' + remote_path
                full_remote_path = f"{clean_remote_path.rstrip('/')}/daily_read_sync.json"
                full_url = base_url + full_remote_path
                
                print(f"全量下载: {full_url}")
                
                from requests.auth import HTTPBasicAuth
                
                self.root.after(0, lambda: self.progress_var.set(20.0))
                self.root.after(0, lambda: self.progress_status_var.set("下载 daily_read_sync.json..."))
                
                response = requests.get(full_url, 
                                      auth=HTTPBasicAuth(username, password),
                                      timeout=(60, 600),
                                      stream=True)
                
                if response.status_code == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    data_chunks = []
                    chunk_size = 8192
                    
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            data_chunks.append(chunk)
                            downloaded_size += len(chunk)
                            
                            if total_size > 0:
                                progress = 20.0 + (downloaded_size / total_size) * 50.0
                                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                                size_mb = downloaded_size / 1024 / 1024
                                self.root.after(0, lambda s=size_mb: self.progress_status_var.set(f"下载中... {s:.2f} MB"))
                    
                    data_content = b''.join(data_chunks)
                    data_text = data_content.decode('utf-8')
                    data = json.loads(data_text)
                    
                    self.root.after(0, lambda: self.progress_var.set(75.0))
                    self.root.after(0, lambda: self.progress_status_var.set("解析数据..."))
                    
                    # 只更新用户选择同步的数据，保留未选择的数据
                    if self.sync_articles.get():
                        self.articles_data = data.get('articles', data.get('contents', []))
                    if self.sync_acupoints.get():
                        self.acupoints_data = data.get('acupoints', [])
                    if self.sync_concepts.get():
                        self.concepts_data = data.get('concepts', [])
                    self.config_data = data.get('config')
                    
                    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    
                    # 构建新的索引
                    files_dict = {}
                    
                    if self.sync_articles.get():
                        files_dict['articles'] = {
                            'filename': 'articles.json',
                            'syncTime': now,
                            'count': len(self.articles_data),
                            'hash': self.calculate_hash(json.dumps(self.articles_data, ensure_ascii=False))
                        }
                    
                    if self.sync_acupoints.get():
                        files_dict['acupoints'] = {
                            'filename': 'acupoints.json',
                            'syncTime': now,
                            'count': len(self.acupoints_data),
                            'hash': self.calculate_hash(json.dumps(self.acupoints_data, ensure_ascii=False))
                        }
                    
                    if self.sync_concepts.get():
                        files_dict['concepts'] = {
                            'filename': 'concepts.json',
                            'syncTime': now,
                            'count': len(self.concepts_data),
                            'hash': self.calculate_hash(json.dumps(self.concepts_data, ensure_ascii=False))
                        }
                    
                    new_sync_index = self.SyncIndex(
                        sync_time=now,
                        files=files_dict
                    )
                    self.save_local_sync_index(new_sync_index)
                    
                    # 保存本地数据
                    self.save_local_data()
                    
                    self.root.after(0, lambda: self.progress_var.set(90.0))
                    self.root.after(0, lambda: self.progress_status_var.set("刷新界面..."))
                    
                    self.root.after(0, self.refresh_article_table)
                    self.root.after(0, self.refresh_acupoint_table)
                    self.root.after(0, self.refresh_concept_table)
                    self.root.after(0, self.update_meridian_filter)
                    self.root.after(0, self.update_category_filter)
                    
                    self.root.after(0, lambda: self.progress_var.set(100.0))
                    self.root.after(0, lambda: self.progress_status_var.set("完成！"))
                    
                    # 计算下载的统计信息
                    downloaded_article_count = len(self.articles_data) if self.sync_articles.get() else 0
                    downloaded_acupoint_count = len(self.acupoints_data) if self.sync_acupoints.get() else 0
                    downloaded_concept_count = len(self.concepts_data) if self.sync_concepts.get() else 0
                    
                    self.root.after(0, lambda: messagebox.showinfo("成功", 
                        f"全量下载成功！\n"
                        f"文章: {downloaded_article_count}条\n"
                        f"穴位: {downloaded_acupoint_count}个\n"
                        f"概念: {downloaded_concept_count}个"))
                    self.root.after(0, lambda: self.status_var.set("全量下载成功"))
                    
                elif response.status_code == 404:
                    self.root.after(0, lambda: self.progress_var.set(0.0))
                    self.root.after(0, lambda: self.progress_status_var.set("文件不存在"))
                    self.root.after(0, lambda: messagebox.showerror("错误", 
                            "下载失败，文件不存在！\n\n"
                            "请先在Android端同步数据，或检查路径是否正确。"))
                    self.root.after(0, lambda: self.status_var.set("下载失败"))
                else:
                    error_msg = f"下载失败，状态码: {response.status_code}"
                    self.root.after(0, lambda: self.progress_var.set(0.0))
                    self.root.after(0, lambda: self.progress_status_var.set("失败"))
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    self.root.after(0, lambda: self.status_var.set("下载失败"))
                    
            except Exception as e:
                import traceback
                print(f"全量下载异常: {str(e)}")
                print(traceback.format_exc())
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("失败"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"全量下载错误：\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("下载失败"))
        
        threading.Thread(target=download_full, daemon=True).start()
    
    def webdav_download_force_full(self):
        """强制全量下载 - 忽略本地索引，直接下载所有选择的分文件"""
        server_url = self.webdav_url.get()
        username = self.webdav_username.get()
        password = self.webdav_password.get()
        remote_path = self.webdav_remote_path.get()
        
        if not server_url:
            messagebox.showwarning("警告", "请输入WebDAV URL！")
            return
        
        self.save_webdav_config()
        
        def force_download_full():
            try:
                self.root.after(0, lambda: self.status_var.set("正在强制全量下载..."))
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("检查远程索引..."))
                
                print("开始强制全量下载...")
                
                # 先尝试获取远程索引
                remote_sync_index_json = self.webdav_download_file(
                    server_url, username, password, remote_path, "sync_index.json"
                )
                
                if remote_sync_index_json:
                    try:
                        remote_sync_index = self.SyncIndex.from_dict(json.loads(remote_sync_index_json))
                        print(f"远程索引版本: {remote_sync_index.version}")
                        
                        # 准备要下载的文件列表 - 所有用户选择的文件
                        files_to_download = []
                        if self.sync_articles.get():
                            files_to_download.append('articles')
                        if self.sync_acupoints.get():
                            files_to_download.append('acupoints')
                        if self.sync_concepts.get():
                            files_to_download.append('concepts')
                        files_to_download.append('checkins')
                        
                        if not files_to_download:
                            self.root.after(0, lambda: self.progress_var.set(0.0))
                            self.root.after(0, lambda: self.progress_status_var.set("无同步内容"))
                            self.root.after(0, lambda: messagebox.showwarning("警告", "请至少选择一项同步内容！"))
                            return
                        
                        self.root.after(0, lambda: self.progress_status_var.set(f"将下载: {', '.join(files_to_download)}"))
                        
                        # 逐个下载文件
                        for i, file_type in enumerate(files_to_download):
                            progress_start = 10.0 + (i / len(files_to_download)) * 70.0
                            progress_end = 10.0 + ((i + 1) / len(files_to_download)) * 70.0
                            
                            self.root.after(0, lambda p=progress_start: self.progress_var.set(p))
                            self.root.after(0, lambda: self.progress_status_var.set(f"下载 {file_type}..."))
                            
                            filename = f"{file_type}.json"
                            file_content = self.webdav_download_file(
                                server_url, username, password, remote_path, filename
                            )
                            
                            if file_content:
                                file_data = json.loads(file_content)
                                if file_type == 'articles':
                                    self.articles_data = file_data
                                elif file_type == 'acupoints':
                                    self.acupoints_data = file_data
                                elif file_type == 'concepts':
                                    self.concepts_data = file_data
                                elif file_type == 'checkins':
                                    pass
                            
                            self.root.after(0, lambda p=progress_end: self.progress_var.set(p))
                        
                        # 保存完整的远程索引
                        self.save_local_sync_index(remote_sync_index)
                        
                        # 保存本地数据
                        self.save_local_data()
                        
                        self.root.after(0, lambda: self.progress_var.set(85.0))
                        self.root.after(0, lambda: self.progress_status_var.set("刷新界面..."))
                        
                        self.root.after(0, self.refresh_article_table)
                        self.root.after(0, self.refresh_acupoint_table)
                        self.root.after(0, self.refresh_concept_table)
                        self.root.after(0, self.update_meridian_filter)
                        self.root.after(0, self.update_category_filter)
                        
                        self.root.after(0, lambda: self.progress_var.set(100.0))
                        self.root.after(0, lambda: self.progress_status_var.set("完成！"))
                        
                        # 计算下载的统计信息
                        downloaded_article_count = len(self.articles_data) if self.sync_articles.get() else 0
                        downloaded_acupoint_count = len(self.acupoints_data) if self.sync_acupoints.get() else 0
                        downloaded_concept_count = len(self.concepts_data) if self.sync_concepts.get() else 0
                        
                        self.root.after(0, lambda: messagebox.showinfo("成功", 
                            f"强制全量下载成功！\n"
                            f"已下载: {', '.join(files_to_download)}\n"
                            f"文章: {downloaded_article_count}条\n"
                            f"穴位: {downloaded_acupoint_count}个\n"
                            f"概念: {downloaded_concept_count}个"))
                        self.root.after(0, lambda: self.status_var.set("强制全量下载成功"))
                        
                    except json.JSONDecodeError as e:
                        print(f"解析远程索引失败: {e}, 尝试全量兼容模式")
                        self.webdav_download_full(server_url, username, password, remote_path)
                else:
                    print("没有远程索引文件，尝试全量兼容模式")
                    self.webdav_download_full(server_url, username, password, remote_path)
                    
            except Exception as e:
                import traceback
                print(f"强制全量下载异常: {str(e)}")
                print(traceback.format_exc())
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("失败"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"强制全量下载错误：\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("下载失败"))
        
        threading.Thread(target=force_download_full, daemon=True).start()
    
    def webdav_upload(self):
        """上传数据到WebDAV - 增量同步版，支持选择性同步"""
        server_url = self.webdav_url.get()
        username = self.webdav_username.get()
        password = self.webdav_password.get()
        remote_path = self.webdav_remote_path.get()
        
        if not server_url:
            messagebox.showwarning("警告", "请输入WebDAV URL！")
            return
        
        # 检查是否有选择要同步的数据
        has_data_to_sync = (self.sync_articles.get() and self.articles_data) or \
                          (self.sync_acupoints.get() and self.acupoints_data) or \
                          (self.sync_concepts.get() and self.concepts_data)
        if not has_data_to_sync:
            messagebox.showwarning("警告", "没有选择要同步的数据，或数据为空！")
            return
        
        self.save_webdav_config()
        
        def upload_incremental():
            try:
                self.root.after(0, lambda: self.status_var.set("正在准备数据..."))
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("准备中..."))
                
                print("开始增量上传...")
                
                local_sync_index = self.load_local_sync_index()
                is_first_sync = not local_sync_index.files
                print(f"首次同步: {is_first_sync}")
                
                now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                
                def normalize_article(article):
                    normalized = article.copy()
                    normalized.setdefault('id', 0)
                    normalized.setdefault('title', '')
                    normalized.setdefault('content', '')
                    normalized.setdefault('contentHtml', None)
                    normalized.setdefault('chineseChars', 0)
                    normalized.setdefault('fontFamily', 'default')
                    normalized.setdefault('fontSize', 16)
                    normalized.setdefault('fontColor', '#000000')
                    normalized.setdefault('isBold', False)
                    normalized.setdefault('isReading', False)
                    normalized.setdefault('isRequired', False)
                    normalized.setdefault('requiredDays', '')
                    normalized.setdefault('useIndependentCheckRate', False)
                    normalized.setdefault('independentCheckRate', 30.0)
                    normalized.setdefault('createTime', now)
                    normalized['lastModified'] = now
                    return normalized
                
                def normalize_acupoint(acupoint):
                    normalized = acupoint.copy()
                    normalized.setdefault('id', 0)
                    normalized.setdefault('acupoint', '')
                    normalized.setdefault('meridian', '')
                    normalized.setdefault('acupointProperty', '')
                    normalized.setdefault('location', '')
                    normalized.setdefault('function', '')
                    normalized.setdefault('indications', '')
                    normalized.setdefault('anatomy', '')
                    normalized.setdefault('operation', '')
                    normalized.setdefault('contraindications', '')
                    normalized.setdefault('locationImagePath', None)
                    normalized.setdefault('locationImageBase64', None)
                    normalized.setdefault('note', '')
                    normalized.setdefault('createTime', now)
                    normalized['lastModified'] = now
                    return normalized
                
                def normalize_concept(concept):
                    normalized = concept.copy()
                    normalized.setdefault('id', 0)
                    normalized.setdefault('title', '')
                    normalized.setdefault('content', '')
                    normalized.setdefault('category', '')
                    normalized.setdefault('subject', '')
                    normalized.setdefault('subChapter', '')
                    normalized.setdefault('imagePath', None)
                    normalized.setdefault('imageBase64', None)
                    normalized.setdefault('note', '')
                    normalized.setdefault('isEnabled', True)
                    normalized.setdefault('createTime', now)
                    normalized.setdefault('lastModified', now)
                    return normalized
                
                self.root.after(0, lambda: self.progress_var.set(10.0))
                self.root.after(0, lambda: self.progress_status_var.set("标准化数据..."))
                
                normalized_articles = [normalize_article(a) for a in self.articles_data]
                normalized_acupoints = [normalize_acupoint(a) for a in self.acupoints_data]
                normalized_concepts = [normalize_concept(c) for c in self.concepts_data]
                
                articles_json = json.dumps(normalized_articles, ensure_ascii=False)
                acupoints_json = json.dumps(normalized_acupoints, ensure_ascii=False)
                concepts_json = json.dumps(normalized_concepts, ensure_ascii=False)
                
                articles_hash = self.calculate_hash(articles_json)
                acupoints_hash = self.calculate_hash(acupoints_json)
                concepts_hash = self.calculate_hash(concepts_json)
                
                # 构建新的同步索引，保留未同步文件的旧信息
                new_files = {}
                
                # 处理文章
                if self.sync_articles.get():
                    new_files['articles'] = {
                        'filename': 'articles.json',
                        'syncTime': now,
                        'count': len(normalized_articles),
                        'hash': articles_hash
                    }
                elif 'articles' in local_sync_index.files:
                    new_files['articles'] = local_sync_index.files['articles']
                
                # 处理穴位
                if self.sync_acupoints.get():
                    new_files['acupoints'] = {
                        'filename': 'acupoints.json',
                        'syncTime': now,
                        'count': len(normalized_acupoints),
                        'hash': acupoints_hash
                    }
                elif 'acupoints' in local_sync_index.files:
                    new_files['acupoints'] = local_sync_index.files['acupoints']
                
                # 处理概念
                if self.sync_concepts.get():
                    new_files['concepts'] = {
                        'filename': 'concepts.json',
                        'syncTime': now,
                        'count': len(normalized_concepts),
                        'hash': concepts_hash
                    }
                elif 'concepts' in local_sync_index.files:
                    new_files['concepts'] = local_sync_index.files['concepts']
                
                new_sync_index = self.SyncIndex(
                    sync_time=now,
                    files=new_files
                )
                
                files_to_upload = []
                
                if is_first_sync:
                    print("首次同步，需要上传所有选择的文件和兼容文件")
                    if self.sync_articles.get():
                        files_to_upload.append('articles')
                    if self.sync_acupoints.get():
                        files_to_upload.append('acupoints')
                    if self.sync_concepts.get():
                        files_to_upload.append('concepts')
                    self.root.after(0, lambda: self.progress_status_var.set("首次同步，上传选择的文件..."))
                else:
                    # 检查需要上传的文件
                    if self.sync_articles.get():
                        local_articles_hash = local_sync_index.files.get('articles', {}).get('hash', '')
                        if articles_hash != local_articles_hash:
                            files_to_upload.append('articles')
                            print(f"文章有变化: 本地={local_articles_hash[:8] if local_articles_hash else 'None'}, 新={articles_hash[:8]}")
                    
                    if self.sync_acupoints.get():
                        local_acupoints_hash = local_sync_index.files.get('acupoints', {}).get('hash', '')
                        if acupoints_hash != local_acupoints_hash:
                            files_to_upload.append('acupoints')
                            print(f"穴位有变化: 本地={local_acupoints_hash[:8] if local_acupoints_hash else 'None'}, 新={acupoints_hash[:8]}")
                    
                    if self.sync_concepts.get():
                        local_concepts_hash = local_sync_index.files.get('concepts', {}).get('hash', '')
                        if concepts_hash != local_concepts_hash:
                            files_to_upload.append('concepts')
                            print(f"概念有变化: 本地={local_concepts_hash[:8] if local_concepts_hash else 'None'}, 新={concepts_hash[:8]}")
                    
                    if not files_to_upload:
                        self.root.after(0, lambda: self.progress_var.set(100.0))
                        self.root.after(0, lambda: self.progress_status_var.set("已是最新！"))
                        self.root.after(0, lambda: messagebox.showinfo("成功", "选择的数据没有变化，无需上传！"))
                        self.root.after(0, lambda: self.status_var.set("已是最新"))
                        return
                    
                    self.root.after(0, lambda: self.progress_status_var.set(f"需要上传: {', '.join(files_to_upload)}"))
                
                total_files = len(files_to_upload)
                uploaded_files = []
                
                for i, file_type in enumerate(files_to_upload):
                    progress_start = 15.0 + (i / total_files) * 65.0
                    progress_end = 15.0 + ((i + 1) / total_files) * 65.0
                    
                    self.root.after(0, lambda p=progress_start: self.progress_var.set(p))
                    self.root.after(0, lambda: self.progress_status_var.set(f"上传 {file_type}..."))
                    
                    filename = f"{file_type}.json"
                    
                    if file_type == 'articles':
                        data_str = articles_json
                    elif file_type == 'acupoints':
                        data_str = acupoints_json
                    elif file_type == 'concepts':
                        data_str = concepts_json
                    
                    success = self.webdav_upload_file(
                        server_url, username, password, remote_path, filename, data_str
                    )
                    
                    if success:
                        uploaded_files.append(file_type)
                        print(f"{file_type} 上传成功")
                    else:
                        print(f"{file_type} 上传失败")
                    
                    self.root.after(0, lambda p=progress_end: self.progress_var.set(p))
                
                self.root.after(0, lambda: self.progress_var.set(85.0))
                self.root.after(0, lambda: self.progress_status_var.set("上传索引..."))
                
                sync_index_json = json.dumps(new_sync_index.to_dict(), ensure_ascii=False, indent=2)
                self.webdav_upload_file(
                    server_url, username, password, remote_path, "sync_index.json", sync_index_json
                )
                print("sync_index.json 上传成功")
                
                if is_first_sync:
                    self.root.after(0, lambda: self.progress_var.set(90.0))
                    self.root.after(0, lambda: self.progress_status_var.set("上传兼容文件..."))
                    
                    # 兼容模式只上传选择的数据
                    legacy_articles = normalized_articles if self.sync_articles.get() else []
                    legacy_acupoints = normalized_acupoints if self.sync_acupoints.get() else []
                    legacy_concepts = normalized_concepts if self.sync_concepts.get() else []
                    
                    self.webdav_upload_full(server_url, username, password, remote_path, 
                                         legacy_articles, legacy_acupoints, legacy_concepts)
                    return
                
                self.save_local_sync_index(new_sync_index)
                
                # 保存本地数据
                self.save_local_data()
                
                self.root.after(0, lambda: self.progress_var.set(100.0))
                self.root.after(0, lambda: self.progress_status_var.set("完成！"))
                
                # 计算上传的统计信息
                uploaded_article_count = len(normalized_articles) if 'articles' in uploaded_files else 0
                uploaded_acupoint_count = len(normalized_acupoints) if 'acupoints' in uploaded_files else 0
                uploaded_concept_count = len(normalized_concepts) if 'concepts' in uploaded_files else 0
                
                self.root.after(0, lambda: messagebox.showinfo("成功", 
                    f"增量上传成功！\n"
                    f"上传了: {', '.join(uploaded_files)}\n"
                    f"文章: {uploaded_article_count}条\n"
                    f"穴位: {uploaded_acupoint_count}个\n"
                    f"概念: {uploaded_concept_count}个"))
                self.root.after(0, lambda: self.status_var.set("增量上传成功"))
                
            except Exception as e:
                import traceback
                print(f"增量上传异常: {str(e)}")
                print(traceback.format_exc())
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("失败"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"增量上传错误：\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("上传失败"))
        
        threading.Thread(target=upload_incremental, daemon=True).start()
    
    def webdav_upload_full(self, server_url, username, password, remote_path,
                         articles_data=None, acupoints_data=None, concepts_data=None):
        """全量上传 - 作为兼容方案"""
        def upload_full():
            try:
                self.root.after(0, lambda: self.status_var.set("正在准备全量上传..."))
                self.root.after(0, lambda: self.progress_var.set(90.0))
                self.root.after(0, lambda: self.progress_status_var.set("全量上传中..."))
                
                now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                
                if articles_data is None:
                    articles_data = self.articles_data
                if acupoints_data is None:
                    acupoints_data = self.acupoints_data
                if concepts_data is None:
                    concepts_data = self.concepts_data
                
                def normalize_article(article):
                    normalized = article.copy()
                    normalized.setdefault('id', 0)
                    normalized.setdefault('title', '')
                    normalized.setdefault('content', '')
                    normalized.setdefault('contentHtml', None)
                    normalized.setdefault('chineseChars', 0)
                    normalized.setdefault('fontFamily', 'default')
                    normalized.setdefault('fontSize', 16)
                    normalized.setdefault('fontColor', '#000000')
                    normalized.setdefault('isBold', False)
                    normalized.setdefault('isReading', False)
                    normalized.setdefault('isRequired', False)
                    normalized.setdefault('requiredDays', '')
                    normalized.setdefault('useIndependentCheckRate', False)
                    normalized.setdefault('independentCheckRate', 30.0)
                    normalized.setdefault('createTime', now)
                    normalized['lastModified'] = now
                    return normalized
                
                def normalize_acupoint(acupoint):
                    normalized = acupoint.copy()
                    normalized.setdefault('id', 0)
                    normalized.setdefault('acupoint', '')
                    normalized.setdefault('meridian', '')
                    normalized.setdefault('acupointProperty', '')
                    normalized.setdefault('location', '')
                    normalized.setdefault('function', '')
                    normalized.setdefault('indications', '')
                    normalized.setdefault('anatomy', '')
                    normalized.setdefault('operation', '')
                    normalized.setdefault('contraindications', '')
                    normalized.setdefault('locationImagePath', None)
                    normalized.setdefault('locationImageBase64', None)
                    normalized.setdefault('note', '')
                    normalized.setdefault('createTime', now)
                    normalized['lastModified'] = now
                    return normalized
                
                def normalize_concept(concept):
                    normalized = concept.copy()
                    normalized.setdefault('id', 0)
                    normalized.setdefault('title', '')
                    normalized.setdefault('content', '')
                    normalized.setdefault('category', '')
                    normalized.setdefault('subject', '')
                    normalized.setdefault('subChapter', '')
                    normalized.setdefault('imagePath', None)
                    normalized.setdefault('imageBase64', None)
                    normalized.setdefault('note', '')
                    normalized.setdefault('isEnabled', True)
                    normalized.setdefault('createTime', now)
                    normalized.setdefault('lastModified', now)
                    return normalized
                
                normalized_articles = [normalize_article(a) for a in articles_data]
                normalized_acupoints = [normalize_acupoint(a) for a in acupoints_data]
                normalized_concepts = [normalize_concept(c) for c in concepts_data]
                
                config_data = self.config_data or {}
                normalized_config = {
                    'dailyMinutes': config_data.get('dailyMinutes', 20),
                    'targetCheckRate': config_data.get('targetCheckRate', 30.0),
                    'keepScreenOn': config_data.get('keepScreenOn', False),
                    'autoSyncWebDav': config_data.get('autoSyncWebDav', False),
                    'yesterdayLongArticleIds': config_data.get('yesterdayLongArticleIds', '')
                }
                
                export_data = {
                    'version': 4,
                    'exportTime': now,
                    'articles': normalized_articles,
                    'checkIns': [],
                    'acupoints': normalized_acupoints,
                    'concepts': normalized_concepts,
                    'config': normalized_config
                }
                
                data_json = json.dumps(export_data, ensure_ascii=False)
                
                base_url = server_url.rstrip('/')
                clean_remote_path = remote_path if remote_path.startswith('/') else '/' + remote_path
                full_remote_path = f"{clean_remote_path.rstrip('/')}/daily_read_sync.json"
                full_url = base_url + full_remote_path
                
                print(f"全量上传到: {full_url}")
                
                from requests.auth import HTTPBasicAuth
                
                response = requests.put(full_url, 
                                      data=data_json,
                                      auth=HTTPBasicAuth(username, password),
                                      headers={'Content-Type': 'application/json'},
                                      timeout=(60, 600))
                
                if response.status_code in [200, 201, 204]:
                    print("daily_read_sync.json 上传成功")
                    
                    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    new_sync_index = self.SyncIndex(
                        sync_time=now,
                        files={
                            'articles': {
                                'filename': 'articles.json',
                                'syncTime': now,
                                'count': len(normalized_articles),
                                'hash': self.calculate_hash(json.dumps(normalized_articles, ensure_ascii=False))
                            },
                            'acupoints': {
                                'filename': 'acupoints.json',
                                'syncTime': now,
                                'count': len(normalized_acupoints),
                                'hash': self.calculate_hash(json.dumps(normalized_acupoints, ensure_ascii=False))
                            },
                            'concepts': {
                                'filename': 'concepts.json',
                                'syncTime': now,
                                'count': len(normalized_concepts),
                                'hash': self.calculate_hash(json.dumps(normalized_concepts, ensure_ascii=False))
                            }
                        }
                    )
                    self.save_local_sync_index(new_sync_index)
                    
                    self.root.after(0, lambda: self.progress_var.set(100.0))
                    self.root.after(0, lambda: self.progress_status_var.set("完成！"))
                    self.root.after(0, lambda: messagebox.showinfo("成功", 
                        f"全量上传成功！\n"
                        f"文章: {len(normalized_articles)}条\n"
                        f"穴位: {len(normalized_acupoints)}个\n"
                        f"概念: {len(normalized_concepts)}个"))
                    self.root.after(0, lambda: self.status_var.set("全量上传成功"))
                else:
                    error_msg = f"全量上传失败，状态码: {response.status_code}"
                    self.root.after(0, lambda: self.progress_var.set(0.0))
                    self.root.after(0, lambda: self.progress_status_var.set("失败"))
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    self.root.after(0, lambda: self.status_var.set("上传失败"))
                    
            except Exception as e:
                import traceback
                print(f"全量上传异常: {str(e)}")
                print(traceback.format_exc())
                self.root.after(0, lambda: self.progress_var.set(0.0))
                self.root.after(0, lambda: self.progress_status_var.set("失败"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"全量上传错误：\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("上传失败"))
        
        threading.Thread(target=upload_full, daemon=True).start()
    
    # ==================== 文章管理 ====================
    
    def refresh_article_table(self, data: Optional[List[Dict]] = None):
        """刷新文章表格"""
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        display_data = data if data is not None else self.articles_data
        
        for article in display_data:
            is_required = "是" if article.get('isRequired', False) else "否"
            is_reading = "是" if article.get('isReading', False) else "否"
            use_independent = "是" if article.get('useIndependentCheckRate', False) else "否"
            independent_rate = article.get('independentCheckRate', 30.0)
            
            self.article_tree.insert("", "end", values=(
                article.get('id', ''),
                article.get('title', ''),
                article.get('chineseChars', 0),
                is_required,
                is_reading,
                use_independent,
                f"{independent_rate}%"
            ))
        
        self.update_article_stats()
    
    def update_article_stats(self):
        """更新文章统计"""
        total = len(self.articles_data)
        selected = len(self.selected_article_ids)
        self.article_stats_var.set(f"文章数: {total} | 选中: {selected}")
    
    def on_article_select(self, event=None):
        sel = self.article_tree.selection()
        self.selected_article_ids = set()
        for i in sel:
            v = self.article_tree.item(i, "values")
            if v:
                self.selected_article_ids.add(int(v[0]))
        self.update_article_stats()
    
    def on_article_double_click(self, event):
        print("文章双击事件触发！")
        self.edit_article()
    
    def search_articles(self):
        """搜索文章"""
        keyword = self.article_search_var.get().lower()
        
        if not keyword:
            self.refresh_article_table()
            return
        
        filtered = [a for a in self.articles_data 
                   if keyword in a.get('title', '').lower() 
                   or keyword in a.get('content', '').lower()]
        
        self.refresh_article_table(filtered)
    
    def filter_articles(self):
        """筛选文章"""
        filter_type = self.article_filter_var.get()
        
        if filter_type == '全部':
            filtered = self.articles_data
        elif filter_type == '必读':
            filtered = [a for a in self.articles_data if a.get('isRequired', False)]
        elif filter_type == '正在阅读':
            filtered = [a for a in self.articles_data if a.get('isReading', False)]
        elif filter_type == '使用独立完成率':
            filtered = [a for a in self.articles_data if a.get('useIndependentCheckRate', False)]
        else:
            filtered = self.articles_data
        
        self.refresh_article_table(filtered)
    
    def select_all_articles(self):
        """全选文章"""
        for item in self.article_tree.get_children():
            self.article_tree.selection_add(item)
            values = self.article_tree.item(item, "values")
            if values:
                self.selected_article_ids.add(int(values[0]))
        self.update_article_stats()
    
    def deselect_all_articles(self):
        """取消全选"""
        self.article_tree.selection_remove(self.article_tree.selection())
        self.selected_article_ids = set()
        self.update_article_stats()
    
    def add_article(self):
        """添加文章"""
        dialog = ArticleEditDialog(self.root)
        if dialog.result:
            max_id = max((a.get('id', 0) for a in self.articles_data), default=0)
            dialog.result['id'] = max_id + 1
            dialog.result['createTime'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            self.articles_data.append(dialog.result)
            self.refresh_article_table()
            messagebox.showinfo("成功", "文章添加成功！")
    
    def edit_article(self):
        """编辑文章 - 简化版本"""
        selected = self.article_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个要编辑的文章！")
            return
        print(f"edit_article 被调用，选中项={selected}")
        item = selected[0]
        values = self.article_tree.item(item, "values")
        if not values or not values[0]:
            return
        
        article_id = int(values[0])
        article = next((a for a in self.articles_data if a.get('id') == article_id), None)
        if article:
            dialog = ArticleEditDialog(self.root, article)
            if dialog.result:
                index = self.articles_data.index(article)
                dialog.result['id'] = article_id
                dialog.result['createTime'] = article.get('createTime', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
                self.articles_data[index] = dialog.result
                self.refresh_article_table()
                messagebox.showinfo("成功", "文章更新成功！")
    
    def delete_selected_articles(self):
        """删除选中的文章"""
        if not self.selected_article_ids:
            messagebox.showwarning("警告", "请先选择要删除的文章！")
            return
        
        if messagebox.askyesno("确认", f"确定删除选中的 {len(self.selected_article_ids)} 个文章？"):
            self.articles_data = [a for a in self.articles_data if a.get('id') not in self.selected_article_ids]
            self.selected_article_ids = set()
            self.refresh_article_table()
            messagebox.showinfo("成功", "删除成功！")
    
    # ==================== 穴位管理 ====================
    
    def refresh_acupoint_table(self, data: Optional[List[Dict]] = None):
        """刷新穴位表格"""
        for item in self.acupoint_tree.get_children():
            self.acupoint_tree.delete(item)
        
        display_data = data if data is not None else self.acupoints_data
        
        for acupoint in display_data:
            self.acupoint_tree.insert("", "end", values=(
                acupoint.get('id', ''),
                acupoint.get('acupoint', ''),
                acupoint.get('meridian', ''),
                acupoint.get('acupointProperty', ''),
                acupoint.get('location', '')[:50] + '...' if len(str(acupoint.get('location', ''))) > 50 else acupoint.get('location', ''),
                acupoint.get('function', '')[:50] + '...' if len(str(acupoint.get('function', ''))) > 50 else acupoint.get('function', ''),
                acupoint.get('indications', '')[:50] + '...' if len(str(acupoint.get('indications', ''))) > 50 else acupoint.get('indications', '')
            ))
        
        self.update_acupoint_stats()
    
    def update_acupoint_stats(self):
        """更新穴位统计"""
        total = len(self.acupoints_data)
        selected = len(self.selected_acupoint_ids)
        self.acupoint_stats_var.set(f"穴位数: {total} | 选中: {selected}")
    
    def update_meridian_filter(self):
        """更新经络筛选选项"""
        meridians = sorted(list(set(a.get('meridian', '') for a in self.acupoints_data if a.get('meridian'))))
        values = ["全部"] + meridians
        self.acupoint_filter_combo['values'] = values
    
    def on_acupoint_select(self, event=None):
        sel = self.acupoint_tree.selection()
        self.selected_acupoint_ids = set()
        for i in sel:
            v = self.acupoint_tree.item(i, "values")
            if v:
                self.selected_acupoint_ids.add(int(v[0]))
        self.update_acupoint_stats()
    
    def on_acupoint_double_click(self, event):
        print("穴位双击事件触发！")
        self.edit_acupoint()
    
    def search_acupoints(self):
        """搜索穴位"""
        keyword = self.acupoint_search_var.get().lower()
        
        if not keyword:
            self.refresh_acupoint_table()
            return
        
        filtered = [a for a in self.acupoints_data 
                   if keyword in a.get('acupoint', '').lower() 
                   or keyword in a.get('meridian', '').lower()
                   or keyword in a.get('indications', '').lower()]
        
        self.refresh_acupoint_table(filtered)
    
    def filter_acupoints(self):
        """筛选穴位"""
        filter_meridian = self.acupoint_filter_var.get()
        
        if filter_meridian == '全部':
            filtered = self.acupoints_data
        else:
            filtered = [a for a in self.acupoints_data if a.get('meridian') == filter_meridian]
        
        self.refresh_acupoint_table(filtered)
    
    def select_all_acupoints(self):
        """全选穴位"""
        for item in self.acupoint_tree.get_children():
            self.acupoint_tree.selection_add(item)
            values = self.acupoint_tree.item(item, "values")
            if values:
                self.selected_acupoint_ids.add(int(values[0]))
        self.update_acupoint_stats()
    
    def deselect_all_acupoints(self):
        """取消全选"""
        self.acupoint_tree.selection_remove(self.acupoint_tree.selection())
        self.selected_acupoint_ids = set()
        self.update_acupoint_stats()
    
    def add_acupoint(self):
        """添加穴位"""
        dialog = AcupointEditDialog(self.root)
        if dialog.result:
            max_id = max((a.get('id', 0) for a in self.acupoints_data), default=0)
            dialog.result['id'] = max_id + 1
            dialog.result['createTime'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            self.acupoints_data.append(dialog.result)
            self.refresh_acupoint_table()
            self.update_meridian_filter()
            messagebox.showinfo("成功", "穴位添加成功！")
    
    def edit_acupoint(self):
        """编辑穴位 - 简化版本"""
        selected = self.acupoint_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个要编辑的穴位！")
            return
        print(f"edit_acupoint 被调用，选中项={selected}")
        item = selected[0]
        values = self.acupoint_tree.item(item, "values")
        if not values or not values[0]:
            return
        
        acupoint_id = int(values[0])
        acupoint = next((a for a in self.acupoints_data if a.get('id') == acupoint_id), None)
        if acupoint:
            dialog = AcupointEditDialog(self.root, acupoint)
            if dialog.result:
                index = self.acupoints_data.index(acupoint)
                dialog.result['id'] = acupoint_id
                dialog.result['createTime'] = acupoint.get('createTime', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
                self.acupoints_data[index] = dialog.result
                self.refresh_acupoint_table()
                self.update_meridian_filter()
                messagebox.showinfo("成功", "穴位更新成功！")
    
    def delete_selected_acupoints(self):
        """删除选中的穴位"""
        if not self.selected_acupoint_ids:
            messagebox.showwarning("警告", "请先选择要删除的穴位！")
            return
        
        if messagebox.askyesno("确认", f"确定删除选中的 {len(self.selected_acupoint_ids)} 个穴位？"):
            self.acupoints_data = [a for a in self.acupoints_data if a.get('id') not in self.selected_acupoint_ids]
            self.selected_acupoint_ids = set()
            self.refresh_acupoint_table()
            self.update_meridian_filter()
            messagebox.showinfo("成功", "删除成功！")
    
    def batch_import_acupoint_images(self):
        """批量导入穴位图片"""
        import os
        
        # 选择文件夹
        folder_path = filedialog.askdirectory(title="选择包含穴位图片的文件夹")
        if not folder_path:
            return
        
        # 支持的图片格式
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        
        # 统计信息
        total_images = 0
        matched_acupoints = 0
        updated_acupoints = 0
        added_acupoints = 0
        unmatched_files = []
        
        # 遍历文件夹中的图片
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # 检查是否是图片文件
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in image_extensions:
                    total_images += 1
                    
                    # 获取文件名（不含扩展名）作为穴位名
                    acupoint_name = os.path.splitext(filename)[0]
                    
                    # 查找匹配的穴位
                    found = False
                    for acupoint in self.acupoints_data:
                        if acupoint.get('acupoint', '') == acupoint_name:
                            found = True
                            matched_acupoints += 1
                            
                            # 检查是否已有图片
                            has_existing_image = (acupoint.get('locationImageBase64') is not None or 
                                                acupoint.get('locationImagePath') is not None)
                            
                            # 读取并编码图片
                            try:
                                with open(file_path, 'rb') as img_file:
                                    image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                                
                                # 更新穴位数据
                                acupoint['locationImagePath'] = file_path
                                acupoint['locationImageBase64'] = image_base64
                                
                                if has_existing_image:
                                    updated_acupoints += 1
                                else:
                                    added_acupoints += 1
                                    
                            except Exception as e:
                                print(f"读取图片失败 {filename}: {e}")
                            
                            break
                    
                    if not found:
                        unmatched_files.append(filename)
        
        # 刷新表格
        self.refresh_acupoint_table()
        
        # 显示结果
        result_msg = (
            f"批量导入完成！\n\n"
            f"扫描图片总数: {total_images}\n"
            f"匹配到的穴位: {matched_acupoints}\n"
            f"  - 更新已有图片: {updated_acupoints}\n"
            f"  - 添加新图片: {added_acupoints}\n"
        )
        
        if unmatched_files:
            result_msg += f"\n未匹配的文件 ({len(unmatched_files)}个):\n"
            result_msg += ", ".join(unmatched_files[:10])
            if len(unmatched_files) > 10:
                result_msg += f" ... 还有{len(unmatched_files)-10}个"
        
        messagebox.showinfo("导入结果", result_msg)
    
    # ==================== 概念管理 ====================
    
    def refresh_concept_table(self, data: Optional[List[Dict]] = None):
        """刷新概念表格"""
        for item in self.concept_tree.get_children():
            self.concept_tree.delete(item)
        
        display_data = data if data is not None else self.concepts_data
        
        for concept in display_data:
            is_enabled = "是" if concept.get('isEnabled', True) else "否"
            self.concept_tree.insert("", "end", values=(
                concept.get('id', ''),
                concept.get('title', ''),
                concept.get('category', ''),
                concept.get('subject', ''),
                concept.get('subChapter', ''),
                is_enabled
            ))
        
        self.update_concept_stats()
    
    def update_concept_stats(self):
        """更新概念统计"""
        total = len(self.concepts_data)
        selected = len(self.selected_concept_ids)
        self.concept_stats_var.set(f"概念数: {total} | 选中: {selected}")
    
    def update_category_filter(self):
        """更新分类筛选选项"""
        categories = sorted(list(set(c.get('category', '') for c in self.concepts_data if c.get('category'))))
        values = ["全部"] + categories
        self.concept_filter_combo['values'] = values
    
    def on_concept_select(self, event=None):
        sel = self.concept_tree.selection()
        self.selected_concept_ids = set()
        for i in sel:
            v = self.concept_tree.item(i, "values")
            if v:
                self.selected_concept_ids.add(int(v[0]))
        self.update_concept_stats()
    
    def on_concept_double_click(self, event):
        print("概念双击事件触发！")
        self.edit_concept()
    
    def search_concepts(self):
        """搜索概念"""
        keyword = self.concept_search_var.get().lower()
        
        if not keyword:
            self.refresh_concept_table()
            return
        
        filtered = [c for c in self.concepts_data 
                   if keyword in c.get('title', '').lower() 
                   or keyword in c.get('content', '').lower()
                   or keyword in c.get('note', '').lower()]
        
        self.refresh_concept_table(filtered)
    
    def filter_concepts(self):
        """筛选概念"""
        filter_category = self.concept_filter_var.get()
        
        if filter_category == '全部':
            filtered = self.concepts_data
        else:
            filtered = [c for c in self.concepts_data if c.get('category') == filter_category]
        
        self.refresh_concept_table(filtered)
    
    def select_all_concepts(self):
        """全选概念"""
        for item in self.concept_tree.get_children():
            self.concept_tree.selection_add(item)
            values = self.concept_tree.item(item, "values")
            if values:
                self.selected_concept_ids.add(int(values[0]))
        self.update_concept_stats()
    
    def deselect_all_concepts(self):
        """取消全选"""
        self.concept_tree.selection_remove(self.concept_tree.selection())
        self.selected_concept_ids = set()
        self.update_concept_stats()
    
    def add_concept(self):
        """添加概念"""
        dialog = ConceptEditDialog(self.root)
        if dialog.result:
            max_id = max((c.get('id', 0) for c in self.concepts_data), default=0)
            dialog.result['id'] = max_id + 1
            dialog.result['createTime'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            self.concepts_data.append(dialog.result)
            self.refresh_concept_table()
            self.update_category_filter()
            messagebox.showinfo("成功", "概念添加成功！")
    
    def edit_concept(self):
        """编辑概念 - 简化版本"""
        selected = self.concept_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个要编辑的概念！")
            return
        print(f"edit_concept 被调用，选中项={selected}")
        item = selected[0]
        values = self.concept_tree.item(item, "values")
        if not values or not values[0]:
            return
        
        concept_id = int(values[0])
        concept = next((c for c in self.concepts_data if c.get('id') == concept_id), None)
        if concept:
            dialog = ConceptEditDialog(self.root, concept)
            if dialog.result:
                index = self.concepts_data.index(concept)
                dialog.result['id'] = concept_id
                dialog.result['createTime'] = concept.get('createTime', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
                self.concepts_data[index] = dialog.result
                self.refresh_concept_table()
                self.update_category_filter()
                messagebox.showinfo("成功", "概念更新成功！")
    
    def delete_selected_concepts(self):
        """删除选中的概念"""
        if not self.selected_concept_ids:
            messagebox.showwarning("警告", "请先选择要删除的概念！")
            return
        
        if messagebox.askyesno("确认", f"确定删除选中的 {len(self.selected_concept_ids)} 个概念？"):
            self.concepts_data = [c for c in self.concepts_data if c.get('id') not in self.selected_concept_ids]
            self.selected_concept_ids = set()
            self.refresh_concept_table()
            self.update_category_filter()
            messagebox.showinfo("成功", "删除成功！")


# ==================== 编辑对话框 ====================

class ArticleEditDialog:
    def __init__(self, parent, article=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑文章" if article else "添加文章")
        self.dialog.geometry("700x850")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # 数据
        self.article = article or {}
        
        # 创建界面
        self.create_widgets()
        
        # 等待对话框关闭
        self.dialog.wait_window()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="标题 (*):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar(value=self.article.get('title', ''))
        ttk.Entry(main_frame, textvariable=self.title_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # 内容
        ttk.Label(main_frame, text="内容 (*):").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.content_text = tk.Text(main_frame, height=10, width=50)
        self.content_text.grid(row=1, column=1, sticky=tk.EW, pady=5)
        self.content_text.insert('1.0', self.article.get('content', ''))
        
        # 中文字数
        ttk.Label(main_frame, text="中文字数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.chars_var = tk.IntVar(value=self.article.get('chineseChars', 0))
        ttk.Entry(main_frame, textvariable=self.chars_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 字号
        ttk.Label(main_frame, text="字号:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.font_size_var = tk.IntVar(value=self.article.get('fontSize', 16))
        ttk.Spinbox(main_frame, from_=10, to=40, textvariable=self.font_size_var, width=18).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 加粗
        self.is_bold_var = tk.BooleanVar(value=self.article.get('isBold', False))
        ttk.Checkbutton(main_frame, text="加粗", variable=self.is_bold_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 正在阅读
        self.is_reading_var = tk.BooleanVar(value=self.article.get('isReading', True))
        ttk.Checkbutton(main_frame, text="正在阅读", variable=self.is_reading_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 必读
        self.is_required_var = tk.BooleanVar(value=self.article.get('isRequired', False))
        ttk.Checkbutton(main_frame, text="必读", variable=self.is_required_var).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 必读日期
        ttk.Label(main_frame, text="必读日期:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.required_days_var = tk.StringVar(value=self.article.get('requiredDays', ''))
        ttk.Entry(main_frame, textvariable=self.required_days_var, width=50).grid(row=7, column=1, sticky=tk.EW, pady=5)
        
        # 使用独立完成率
        self.use_independent_var = tk.BooleanVar(value=self.article.get('useIndependentCheckRate', False))
        ttk.Checkbutton(main_frame, text="使用独立完成率", variable=self.use_independent_var).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 独立完成率
        ttk.Label(main_frame, text="独立完成率:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.independent_rate_var = tk.DoubleVar(value=self.article.get('independentCheckRate', 30.0))
        ttk.Scale(main_frame, from_=0, to=100, variable=self.independent_rate_var, orient=tk.HORIZONTAL).grid(row=9, column=1, sticky=tk.EW, pady=5)
        ttk.Label(main_frame, textvariable=lambda: f"{self.independent_rate_var.get():.1f}%").grid(row=9, column=2, padx=5)
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=10, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        # 快速填充区域
        ttk.Label(main_frame, text="快速填充:").grid(row=11, column=0, sticky=tk.NW, pady=5)
        
        quick_fill_frame = ttk.Frame(main_frame)
        quick_fill_frame.grid(row=11, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(quick_fill_frame, text="格式: 标题,内容").pack(anchor=tk.W)
        
        self.quick_fill_text = tk.Text(quick_fill_frame, height=3, width=50)
        self.quick_fill_text.pack(fill=tk.X, pady=5)
        
        quick_btn_frame = ttk.Frame(quick_fill_frame)
        quick_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(quick_btn_frame, text="识别并填充", command=self.quick_fill).pack(side=tk.LEFT, padx=5)
        ttk.Label(quick_btn_frame, text="提示: 以 \",\" 分隔，顺序为 标题,内容").pack(side=tk.LEFT, padx=10)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=12, column=0, columnspan=3, pady=20)
        
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def quick_fill(self):
        """快速填充功能：从文本中解析内容并填充"""
        text = self.quick_fill_text.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "请先输入要识别的内容！")
            return
        
        # 以逗号分隔
        parts = [p.strip() for p in text.split(',')]
        
        # 填充对应字段
        if len(parts) >= 1 and parts[0]:
            self.title_var.set(parts[0])
        if len(parts) >= 2 and parts[1]:
            # 清空原有内容并填充
            self.content_text.delete('1.0', tk.END)
            self.content_text.insert('1.0', parts[1])
        
        # 如果有超过2个部分，将剩余部分也加入内容中
        if len(parts) > 2:
            remaining_content = ','.join(parts[2:])
            self.content_text.insert(tk.END, remaining_content)
        
        messagebox.showinfo("成功", f"已填充 {min(2, len(parts))} 个字段！")
    
    def on_ok(self):
        title = self.title_var.get().strip()
        content = self.content_text.get('1.0', tk.END).strip()
        
        if not title or not content:
            messagebox.showwarning("警告", "请填写标题和内容！")
            return
        
        # 自动计算中文字数（不包括标点符号、阿拉伯数字和英文）
        import re
        # 匹配中文字符（包括CJK统一汉字和常见汉字）
        chinese_chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', content)
        chinese_count = len(chinese_chars)
        self.chars_var.set(chinese_count)
        
        self.result = {
            'title': title,
            'content': content,
            'contentHtml': None,
            'chineseChars': chinese_count,
            'fontFamily': 'default',
            'fontSize': self.font_size_var.get(),
            'fontColor': '#000000',
            'isBold': self.is_bold_var.get(),
            'isReading': self.is_reading_var.get(),
            'isRequired': self.is_required_var.get(),
            'requiredDays': self.required_days_var.get(),
            'useIndependentCheckRate': self.use_independent_var.get(),
            'independentCheckRate': self.independent_rate_var.get()
        }
        
        self.dialog.destroy()


class AcupointEditDialog:
    def __init__(self, parent, acupoint=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑穴位" if acupoint else "添加穴位")
        self.dialog.geometry("800x900")  # 增加尺寸
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        self.acupoint = acupoint or {}
        self.image_path = tk.StringVar(value=self.acupoint.get('locationImagePath', ''))
        self.location_image_base64 = self.acupoint.get('locationImageBase64', None)
        self.create_widgets()
        self.dialog.wait_window()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 穴位
        ttk.Label(main_frame, text="穴位 (*):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.acupoint_var = tk.StringVar(value=self.acupoint.get('acupoint', ''))
        ttk.Entry(main_frame, textvariable=self.acupoint_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # 经络
        ttk.Label(main_frame, text="经络 (*):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.meridian_var = tk.StringVar(value=self.acupoint.get('meridian', ''))
        ttk.Entry(main_frame, textvariable=self.meridian_var, width=50).grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # 穴性
        ttk.Label(main_frame, text="穴性:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.property_var = tk.StringVar(value=self.acupoint.get('acupointProperty', ''))
        ttk.Entry(main_frame, textvariable=self.property_var, width=50).grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        # 定位
        ttk.Label(main_frame, text="定位:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        self.location_text = tk.Text(main_frame, height=3, width=50)
        self.location_text.grid(row=3, column=1, sticky=tk.EW, pady=5)
        self.location_text.insert('1.0', self.acupoint.get('location', ''))
        
        # 功效
        ttk.Label(main_frame, text="功效:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        self.function_text = tk.Text(main_frame, height=3, width=50)
        self.function_text.grid(row=4, column=1, sticky=tk.EW, pady=5)
        self.function_text.insert('1.0', self.acupoint.get('function', ''))
        
        # 主治
        ttk.Label(main_frame, text="主治:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.indications_text = tk.Text(main_frame, height=3, width=50)
        self.indications_text.grid(row=5, column=1, sticky=tk.EW, pady=5)
        self.indications_text.insert('1.0', self.acupoint.get('indications', ''))
        
        # 解剖
        ttk.Label(main_frame, text="解剖:").grid(row=6, column=0, sticky=tk.NW, pady=5)
        self.anatomy_text = tk.Text(main_frame, height=2, width=50)
        self.anatomy_text.grid(row=6, column=1, sticky=tk.EW, pady=5)
        self.anatomy_text.insert('1.0', self.acupoint.get('anatomy', ''))
        
        # 操作
        ttk.Label(main_frame, text="操作:").grid(row=7, column=0, sticky=tk.NW, pady=5)
        self.operation_text = tk.Text(main_frame, height=2, width=50)
        self.operation_text.grid(row=7, column=1, sticky=tk.EW, pady=5)
        self.operation_text.insert('1.0', self.acupoint.get('operation', ''))
        
        # 禁忌
        ttk.Label(main_frame, text="禁忌:").grid(row=8, column=0, sticky=tk.NW, pady=5)
        self.contraindications_text = tk.Text(main_frame, height=2, width=50)
        self.contraindications_text.grid(row=8, column=1, sticky=tk.EW, pady=5)
        self.contraindications_text.insert('1.0', self.acupoint.get('contraindications', ''))
        
        # 新增：图片选择和预览区
        ttk.Label(main_frame, text="穴位图片:").grid(row=9, column=0, sticky=tk.W, pady=5)
        
        img_frame = ttk.Frame(main_frame)
        img_frame.grid(row=9, column=1, sticky=tk.W, pady=5)
        
        # 图片路径显示
        ttk.Entry(img_frame, textvariable=self.image_path, width=40).pack(side=tk.LEFT, padx=5)
        
        # 选择图片按钮
        ttk.Button(img_frame, text="选择图片", command=self.select_image).pack(side=tk.LEFT, padx=5)
        
        # 预览区域
        self.img_preview = ttk.Label(main_frame, text="(无图片)")
        self.img_preview.grid(row=10, column=1, sticky=tk.W, pady=5)
        
        # 尝试显示已有图片
        self.update_image_preview()
        
        # 备注
        ttk.Label(main_frame, text="备注:").grid(row=11, column=0, sticky=tk.NW, pady=5)
        self.note_text = tk.Text(main_frame, height=2, width=50)
        self.note_text.grid(row=11, column=1, sticky=tk.EW, pady=5)
        self.note_text.insert('1.0', self.acupoint.get('note', ''))
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=12, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def select_image(self):
        """选择图片文件"""
        file_path = filedialog.askopenfilename(
            title="选择穴位图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            self.image_path.set(file_path)
            self.update_image_preview()
    
    def update_image_preview(self):
        """更新图片预览"""
        path = self.image_path.get()
        if path and os.path.exists(path):
            try:
                # 尝试加载并显示缩略图
                if HAS_PIL:
                    img = Image.open(path)
                    img.thumbnail((200, 200))  # 限制预览尺寸
                    photo = ImageTk.PhotoImage(img)
                    self.img_preview.config(image=photo, text='')
                    self.img_preview.image = photo  # 保持引用
                else:
                    self.img_preview.config(text=f"(需安装PIL库: pip install pillow)\n文件: {os.path.basename(path)}", image='')
            except Exception as e:
                self.img_preview.config(text=f"(图片加载失败: {str(e)[:30]})", image='')
        elif self.location_image_base64:
            try:
                # 尝试从 base64 编码加载图片
                if HAS_PIL:
                    from io import BytesIO
                    img_data = base64.b64decode(self.location_image_base64)
                    img = Image.open(BytesIO(img_data))
                    img.thumbnail((200, 200))  # 限制预览尺寸
                    photo = ImageTk.PhotoImage(img)
                    self.img_preview.config(image=photo, text='')
                    self.img_preview.image = photo  # 保持引用
                else:
                    self.img_preview.config(text="(Base64编码图片，需安装PIL库显示)", image='')
            except Exception as e:
                self.img_preview.config(text=f"(Base64图片加载失败: {str(e)[:30]})", image='')
        else:
            self.img_preview.config(text="(无图片)", image='')
    
    def on_ok(self):
        acupoint = self.acupoint_var.get().strip()
        meridian = self.meridian_var.get().strip()
        
        if not acupoint or not meridian:
            messagebox.showwarning("警告", "请填写穴位和经络！")
            return
        
        # 如果有图片文件，将其转换为base64
        location_image_base64 = self.location_image_base64
        image_path = self.image_path.get() or None
        
        if image_path and os.path.exists(image_path):
            try:
                # 验证图片文件大小，避免过大文件导致问题
                file_size = os.path.getsize(image_path)
                if file_size > 5 * 1024 * 1024:  # 5MB限制
                    messagebox.showwarning("警告", f"图片文件过大 ({file_size / 1024 / 1024:.1f}MB)，建议选择小于5MB的图片")
                    # 但仍然继续保存
                
                with open(image_path, 'rb') as img_file:
                    location_image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                print(f"图片编码成功，大小: {len(location_image_base64)} 字符")
            except Exception as e:
                print(f"图片编码失败: {e}")
                location_image_base64 = None  # 确保失败时不会保留错误数据
        
        # 保留原有数据中的createTime
        create_time = self.acupoint.get('createTime', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        
        self.result = {
            'acupoint': acupoint,
            'meridian': meridian,
            'acupointProperty': self.property_var.get(),
            'location': self.location_text.get('1.0', tk.END).strip(),
            'function': self.function_text.get('1.0', tk.END).strip(),
            'indications': self.indications_text.get('1.0', tk.END).strip(),
            'anatomy': self.anatomy_text.get('1.0', tk.END).strip(),
            'operation': self.operation_text.get('1.0', tk.END).strip(),
            'contraindications': self.contraindications_text.get('1.0', tk.END).strip(),
            'locationImagePath': image_path,
            'locationImageBase64': location_image_base64,
            'note': self.note_text.get('1.0', tk.END).strip(),
            'createTime': create_time
        }
        
        self.dialog.destroy()


class ConceptEditDialog:
    def __init__(self, parent, concept=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑概念" if concept else "添加概念")
        self.dialog.geometry("800x950")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        self.concept = concept or {}
        self.image_path = tk.StringVar(value=self.concept.get('imagePath', ''))
        self.image_base64 = self.concept.get('imageBase64', None)
        self.create_widgets()
        self.dialog.wait_window()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="标题 (*):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar(value=self.concept.get('title', ''))
        ttk.Entry(main_frame, textvariable=self.title_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # 分类
        ttk.Label(main_frame, text="分类:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value=self.concept.get('category', ''))
        ttk.Entry(main_frame, textvariable=self.category_var, width=50).grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # 科目
        ttk.Label(main_frame, text="科目:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.subject_var = tk.StringVar(value=self.concept.get('subject', ''))
        ttk.Entry(main_frame, textvariable=self.subject_var, width=50).grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        # 子章节
        ttk.Label(main_frame, text="子章节:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.subchapter_var = tk.StringVar(value=self.concept.get('subChapter', ''))
        ttk.Entry(main_frame, textvariable=self.subchapter_var, width=50).grid(row=3, column=1, sticky=tk.EW, pady=5)
        
        # 内容
        ttk.Label(main_frame, text="内容 (*):").grid(row=4, column=0, sticky=tk.NW, pady=5)
        self.content_text = tk.Text(main_frame, height=8, width=50)
        self.content_text.grid(row=4, column=1, sticky=tk.EW, pady=5)
        self.content_text.insert('1.0', self.concept.get('content', ''))
        
        # 图片
        ttk.Label(main_frame, text="概念图片:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        img_frame = ttk.Frame(main_frame)
        img_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # 图片路径显示
        ttk.Entry(img_frame, textvariable=self.image_path, width=40).pack(side=tk.LEFT, padx=5)
        
        # 选择图片按钮
        ttk.Button(img_frame, text="选择图片", command=self.select_image).pack(side=tk.LEFT, padx=5)
        
        # 预览区域
        self.img_preview = ttk.Label(main_frame, text="(无图片)")
        self.img_preview.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # 尝试显示已有图片
        self.update_image_preview()
        
        # 备注
        ttk.Label(main_frame, text="备注:").grid(row=7, column=0, sticky=tk.NW, pady=5)
        self.note_text = tk.Text(main_frame, height=3, width=50)
        self.note_text.grid(row=7, column=1, sticky=tk.EW, pady=5)
        self.note_text.insert('1.0', self.concept.get('note', ''))
        
        # 启用状态
        self.is_enabled_var = tk.BooleanVar(value=self.concept.get('isEnabled', True))
        ttk.Checkbutton(main_frame, text="启用", variable=self.is_enabled_var).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=15)
        
        # 快速填充区域
        ttk.Label(main_frame, text="快速填充:").grid(row=10, column=0, sticky=tk.NW, pady=5)
        
        quick_fill_frame = ttk.Frame(main_frame)
        quick_fill_frame.grid(row=10, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(quick_fill_frame, text="格式: 标题,分类,科目,子章节,内容").pack(anchor=tk.W)
        
        self.quick_fill_text = tk.Text(quick_fill_frame, height=4, width=50)
        self.quick_fill_text.pack(fill=tk.X, pady=5)
        
        quick_btn_frame = ttk.Frame(quick_fill_frame)
        quick_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(quick_btn_frame, text="识别并填充", command=self.quick_fill).pack(side=tk.LEFT, padx=5)
        ttk.Label(quick_btn_frame, text="提示: 以 \",\" 分隔，顺序为 标题,分类,科目,子章节,内容").pack(side=tk.LEFT, padx=10)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def quick_fill(self):
        """快速填充功能：从文本中解析内容并填充"""
        text = self.quick_fill_text.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "请先输入要识别的内容！")
            return
        
        # 以逗号分隔
        parts = [p.strip() for p in text.split(',')]
        
        # 填充对应字段
        if len(parts) >= 1 and parts[0]:
            self.title_var.set(parts[0])
        if len(parts) >= 2 and parts[1]:
            self.category_var.set(parts[1])
        if len(parts) >= 3 and parts[2]:
            self.subject_var.set(parts[2])
        if len(parts) >= 4 and parts[3]:
            self.subchapter_var.set(parts[3])
        if len(parts) >= 5 and parts[4]:
            # 清空原有内容并填充
            self.content_text.delete('1.0', tk.END)
            self.content_text.insert('1.0', parts[4])
        
        # 如果有超过5个部分，将剩余部分也加入内容中
        if len(parts) > 5:
            remaining_content = ','.join(parts[5:])
            self.content_text.insert(tk.END, remaining_content)
        
        messagebox.showinfo("成功", f"已填充 {min(5, len(parts))} 个字段！")
    
    def select_image(self):
        """选择图片文件"""
        file_path = filedialog.askopenfilename(
            title="选择概念图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            self.image_path.set(file_path)
            self.update_image_preview()
    
    def update_image_preview(self):
        """更新图片预览"""
        path = self.image_path.get()
        if path and os.path.exists(path):
            try:
                # 尝试加载并显示缩略图
                if HAS_PIL:
                    img = Image.open(path)
                    img.thumbnail((200, 200))  # 限制预览尺寸
                    photo = ImageTk.PhotoImage(img)
                    self.img_preview.config(image=photo, text='')
                    self.img_preview.image = photo  # 保持引用
                else:
                    self.img_preview.config(text=f"(需安装PIL库: pip install pillow)\n文件: {os.path.basename(path)}", image='')
            except Exception as e:
                self.img_preview.config(text=f"(图片加载失败: {str(e)[:30]})", image='')
        elif self.image_base64:
            try:
                # 尝试从 base64 编码加载图片
                if HAS_PIL:
                    from io import BytesIO
                    img_data = base64.b64decode(self.image_base64)
                    img = Image.open(BytesIO(img_data))
                    img.thumbnail((200, 200))  # 限制预览尺寸
                    photo = ImageTk.PhotoImage(img)
                    self.img_preview.config(image=photo, text='')
                    self.img_preview.image = photo  # 保持引用
                else:
                    self.img_preview.config(text="(Base64编码图片，需安装PIL库显示)", image='')
            except Exception as e:
                self.img_preview.config(text=f"(Base64图片加载失败: {str(e)[:30]})", image='')
        else:
            self.img_preview.config(text="(无图片)", image='')
    
    def on_ok(self):
        title = self.title_var.get().strip()
        content = self.content_text.get('1.0', tk.END).strip()
        
        if not title or not content:
            messagebox.showwarning("警告", "请填写标题和内容！")
            return
        
        # 如果有图片文件，将其转换为base64
        image_base64 = self.image_base64
        image_path = self.image_path.get() or None
        
        if image_path and os.path.exists(image_path):
            try:
                # 验证图片文件大小，避免过大文件导致问题
                file_size = os.path.getsize(image_path)
                if file_size > 5 * 1024 * 1024:  # 5MB限制
                    messagebox.showwarning("警告", f"图片文件过大 ({file_size / 1024 / 1024:.1f}MB)，建议选择小于5MB的图片")
                    # 但仍然继续保存
                
                with open(image_path, 'rb') as img_file:
                    image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                print(f"图片编码成功，大小: {len(image_base64)} 字符")
            except Exception as e:
                print(f"图片编码失败: {e}")
                image_base64 = None  # 确保失败时不会保留错误数据
        
        # 保留原有数据中的createTime
        create_time = self.concept.get('createTime', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        
        self.result = {
            'title': title,
            'content': content,
            'category': self.category_var.get(),
            'subject': self.subject_var.get(),
            'subChapter': self.subchapter_var.get(),
            'imagePath': image_path,
            'imageBase64': image_base64,
            'note': self.note_text.get('1.0', tk.END).strip(),
            'isEnabled': self.is_enabled_var.get(),
            'createTime': create_time
        }
        
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = DailyReadManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
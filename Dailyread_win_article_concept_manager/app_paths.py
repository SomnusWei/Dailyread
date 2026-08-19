# -*- coding: utf-8 -*-
"""应用路径统一管理

打包后（PyInstaller frozen）：
  - 数据文件（app_data.json、auth_token.json、offline_queue.json）保存在 exe 同目录，
    便于用户查看/备份，且无论从哪里启动（快捷方式/命令行）都保持一致。
  - 内置资源（logo.png）从 _MEIPASS 临时解压目录读取。

开发环境：
  - 数据文件保存在项目源码目录（与 .py 文件同目录）。
"""
import os
import sys


def _get_app_dir() -> str:
    """返回数据文件应存放的目录（绝对路径）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后：exe 所在目录
        return os.path.dirname(os.path.abspath(sys.executable))
    # 开发环境：源码目录
    return os.path.dirname(os.path.abspath(__file__))


def _get_resource_dir() -> str:
    """返回内置资源目录（logo.png 等）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller onefile/onedir：临时解压目录
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            return meipass
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _get_app_dir()
RESOURCE_DIR = _get_resource_dir()


def data_path(filename: str) -> str:
    """返回数据文件的完整绝对路径"""
    return os.path.join(APP_DIR, filename)


def resource_path(filename: str) -> str:
    """返回内置资源的完整绝对路径"""
    return os.path.join(RESOURCE_DIR, filename)

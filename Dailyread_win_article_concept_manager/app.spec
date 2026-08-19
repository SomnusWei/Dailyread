# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# 获取 spec 文件所在目录（源码目录），用于定位资源
spec_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['article_concept_manager.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        ('logo.png', '.'),
    ],
    hiddenimports=[
        'app_paths',
        'api_client',
        'sync_service',
        'auth_dialogs',
        'migration_dialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='每日阅读管理器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.png',
)

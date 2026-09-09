# -*- coding: utf-8 -*-
"""
每日阅读 · 备份助手
从部署服务器拉取备份包（MySQL 逻辑备份 + 站点数据）到本地/NAS 目录，
支持手动立即备份、定期自动备份（Windows 任务计划）、SHA-256 校验与保留清理。
技术栈：PyQt6 + paramiko(SFTP/SSH)。单文件自包含。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta

import paramiko
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QTimeEdit, QVBoxLayout, QWidget, QFormLayout
)

APP_NAME = '每日阅读备份助手'
APP_KEY = 'DailyReadBackup'
DEFAULT_HOST = '47.95.205.216'
DEFAULT_PORT = 22
DEFAULT_USER = 'root'
DEFAULT_REMOTE_ROOT = '/opt/dailyread-server/backups'
DEFAULT_REMOTE_SCRIPT = '/opt/dailyread-server/scripts/backup.sh'
BACKUP_PAT = re.compile(r'^backup-(\d{8})-(\d{4})$')
TASK_NAME = 'DailyReadBackupAuto'

MAIN_QSS = """
QMainWindow, QDialog { background: #f5f7fa; }
QWidget { font-family: "Microsoft YaHei", "PingFang SC"; font-size: 13px; color: #26313d; }
QGroupBox {
    background: #ffffff; border: 1px solid #e4e9f0; border-radius: 8px;
    margin-top: 12px; padding: 14px 12px 12px 12px; font-weight: 600; color: #1b6e5b;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; background: transparent; }
QLineEdit, QTimeEdit, QSpinBox, QComboBox {
    background: #fff; border: 1px solid #d5dce6; border-radius: 6px;
    padding: 5px 8px; selection-background-color: #34c98e;
}
QLineEdit:focus, QTimeEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #34c98e; }
QPushButton {
    background: #eef2f6; border: 1px solid #d5dce6; border-radius: 6px;
    padding: 6px 14px; font-weight: 500;
}
QPushButton:hover { background: #e2e9f0; }
QPushButton:disabled { color: #9aa7b4; background: #f0f3f6; }
QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #34c98e, stop:1 #1fae76);
    color: #fff; border: none; font-size: 14px; font-weight: 600; padding: 9px 22px;
}
QPushButton#primary:hover { background: #2fbd85; }
QPushButton#primary:disabled { background: #a9d8c6; color: #f0fbf6; }
QPushButton#danger { color: #c0392b; }
QPushButton#danger:hover { background: #fdecea; border-color: #f0c4bd; }
QTabWidget::pane { border: none; top: -1px; }
QTabBar::tab {
    background: transparent; padding: 8px 18px; margin-right: 4px;
    border-bottom: 3px solid transparent; color: #6b7a88; font-weight: 500;
}
QTabBar::tab:selected { color: #1fae76; border-bottom: 3px solid #34c98e; }
QTabBar::tab:hover { color: #2aa97b; }
QTableWidget {
    background: #fff; border: 1px solid #e4e9f0; border-radius: 6px;
    gridline-color: #eef2f6; selection-background-color: #e4f7ef;
    selection-color: #1b6e5b;
}
QHeaderView::section {
    background: #f0f4f8; border: none; border-bottom: 1px solid #dfe6ee;
    padding: 7px 8px; font-weight: 600; color: #4a5866;
}
QProgressBar {
    border: 1px solid #d5dce6; border-radius: 6px; background: #eef2f6;
    text-align: center; color: #4a5866; height: 18px;
}
QProgressBar::chunk { background: #34c98e; border-radius: 5px; }
QPlainTextEdit {
    background: #0f1b24; color: #c7e6d9; border: 1px solid #0f1b24;
    border-radius: 6px; font-family: Consolas, "Courier New"; font-size: 12px;
}
QLabel#hint { color: #8a97a5; font-size: 12px; }
"""


def app_dir() -> str:
    """应用数据目录（日志 / 配置），支持打包后的 exe"""
    base = os.environ.get('APPDATA') or os.path.expanduser('~')
    d = os.path.join(base, APP_KEY)
    os.makedirs(d, exist_ok=True)
    return d


def log_file_path() -> str:
    return os.path.join(app_dir(), 'logs', datetime.now().strftime('%Y-%m') + '.log')


def write_log_line(text: str):
    try:
        d = os.path.join(app_dir(), 'logs')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, datetime.now().strftime('%Y-%m') + '.log'),
                  'a', encoding='utf-8') as f:
            f.write('[%s] %s\n' % (datetime.now().strftime('%F %T'), text))
    except Exception:
        pass


def human_size(n: float) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return '%.1f %s' % (n, unit)
        n /= 1024
    return '%.1f TB' % n


def default_key_path() -> str:
    p = os.path.join(os.path.expanduser('~'), '.ssh', 'serverssh')
    return p if os.path.isfile(p) else os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa')


def parse_backup_name(name: str):
    m = BACKUP_PAT.match(name)
    if not m:
        return None
    return datetime.strptime('%s-%s' % (m.group(1), m.group(2)), '%Y%m%d-%H%M')


# ==================== 备份执行 Worker ====================

class BackupWorker(QThread):
    """后台执行 远程触发备份/拉取 -> 下载 -> SHA 校验 -> 落入目标目录"""
    log_sig = pyqtSignal(str)
    progress_sig = pyqtSignal(float)          # 0-100 总体进度
    file_sig = pyqtSignal(str, int, int)      # 文件名, 已传, 总字节
    done_sig = pyqtSignal(bool, str)          # 成功?, 摘要

    def __init__(self, cfg: dict, trigger_remote: bool, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.trigger_remote = trigger_remote
        self.cancel = False

    def _log(self, msg: str):
        self.log_sig.emit(msg)

    def stop(self):
        self.cancel = True

    # ---- 远程操作 ----
    def _ssh(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.cfg['host'], port=int(self.cfg['port']),
            username=self.cfg['user'], key_filename=self.cfg['key_path'],
            timeout=20, banner_timeout=20, auth_timeout=20)
        return ssh

    def _exec(self, ssh, cmd: str, timeout: int = 900) -> str:
        _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode('utf-8', 'replace')
        err = stderr.read().decode('utf-8', 'replace')
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            raise RuntimeError('远程命令失败(rc=%d): %s %s' % (rc, out[-800:], err[-800:]))
        return out

    def _latest_remote(self, sftp) -> str:
        root = self.cfg['remote_root']
        items = [a for a in sftp.listdir_attr(root)
                 if stat.S_ISDIR(a.st_mode) and BACKUP_PAT.match(a.filename)]
        if not items:
            raise RuntimeError('服务器备份目录为空（尚无 backup-* 产物）')
        items.sort(key=lambda a: a.st_mtime, reverse=True)
        return items[0].filename

    # ---- 主流程 ----
    def run(self):
        try:
            total_files = 1
            index = 0
            final_dir = None
            summary = ''
            ssh = None
            sftp = None
            try:
                ssh = self._ssh()
                self._log('SSH 已连接 %s:%s' % (self.cfg['host'], self.cfg['port']))

                if self.trigger_remote:
                    self.progress_sig.emit(2)
                    self._log('正在触发服务器备份脚本 %s …' % self.cfg['remote_script'])
                    self._exec(ssh, 'bash %s' % self.cfg['remote_script'])
                    self._log('服务器出包完成')

                sftp = ssh.open_sftp()
                name = self._latest_remote(sftp)
                self._log('发现服务器最新备份包：%s' % name)

                target_root = self.cfg['target_dir']
                os.makedirs(target_root, exist_ok=True)
                if not os.path.isdir(target_root):
                    raise RuntimeError('目标目录不可写：%s' % target_root)

                final_dir = os.path.join(target_root, name)

                # 已存在且 sha256.txt 一致 -> 跳过
                if os.path.isdir(final_dir) and self._dir_sha_ok(final_dir):
                    self._log('目标已存在且校验一致，跳过下载：%s' % name)
                    summary = '跳过（本地已是最新 %s）' % name
                    self.progress_sig.emit(100)
                    self.done_sig.emit(True, summary)
                    return

                stage = os.path.join(target_root, '.partial_' + name)
                if os.path.isdir(stage):
                    shutil.rmtree(stage, ignore_errors=True)
                os.makedirs(stage)

                # 收集远端文件清单（db-*.sql / site-*.tar.gz / sha256.txt，跳过日志）
                attrs = sftp.listdir_attr(self.cfg['remote_root'] + '/' + name)
                remote_files = []
                for a in attrs:
                    fn = a.filename
                    if fn == 'backup.log' or not stat.S_ISREG(a.st_mode):
                        continue
                    if fn == 'sha256.txt' or re.match(r'^(db-.+\.sql|site-.+\.tar\.gz)$', fn):
                        remote_files.append(fn)
                remote_files = sorted(set(remote_files))
                if not remote_files:
                    raise RuntimeError('服务器包内容为空：%s' % name)

                total_files = len(remote_files)
                done_bytes = 0
                total_bytes = sum(a.st_size for a in attrs if a.filename in remote_files)
                for fn in remote_files:
                    if self.cancel:
                        raise RuntimeError('已取消')
                    index += 1
                    rp = '%s/%s/%s' % (self.cfg['remote_root'], name, fn)
                    lp = os.path.join(stage, fn)
                    file_size = self._rstat(sftp, rp)
                    self._log('下载 %s (%s) [%d/%d] …' % (fn, human_size(file_size), index, total_files))
                    self.file_sig.emit(fn, index, total_files)
                    self._download_file(sftp, rp, lp, file_size, done_bytes, total_bytes)
                    done_bytes += file_size
                    self.progress_sig.emit(min(done_bytes / total_bytes * 100, 99))

                # SHA-256 校验
                self._log('正在进行 SHA-256 完整性校验 …')
                self._verify_dir(stage)
                self._log('SHA-256 校验通过')

                # 移入正式目录
                if os.path.isdir(final_dir):
                    shutil.rmtree(final_dir, ignore_errors=True)
                shutil.move(stage, final_dir)
                summary = '已备份 %s（共 %s）' % (name, human_size(total_bytes))

                # 保留策略清理
                removed = self._cleanup_expired(target_root, self.cfg['keep_days'])
                if removed:
                    self._log('按保留策略清理 %d 个过期备份' % removed)

                self.progress_sig.emit(100)
                self.done_sig.emit(True, summary)
            finally:
                if sftp:
                    try:
                        sftp.close()
                    except Exception:
                        pass
                if ssh:
                    try:
                        ssh.close()
                    except Exception:
                        pass
        except Exception as e:
            err = str(e)
            write_log_line('备份失败: ' + err)
            self.log_sig.emit('!! 备份失败：' + err)
            self.done_sig.emit(False, err)

    def _rstat(self, sftp, path) -> int:
        try:
            return int(sftp.stat(path).st_size)
        except Exception:
            return 0

    def _download_file(self, sftp, remote_path: str, local_path: str,
                       file_size: int, done_bytes: int, total_bytes: int):
        """手动分块下载——在 QThread 内直接读写 + emit 进度，
        不使用 paramiko callback（paramiko 从 Transport 线程回调，
        在打包 EXE 中跨线程发 Qt 信号会闪退）。"""
        CHUNK = 65536
        rf = sftp.open(remote_path, 'rb')
        rf.settimeout(60)
        written = 0
        last_pct = 0.0
        try:
            with open(local_path, 'wb') as lf:
                while True:
                    if self.cancel:
                        raise RuntimeError('已取消')
                    data = rf.read(CHUNK)
                    if not data:
                        break
                    lf.write(data)
                    written += len(data)
                    if total_bytes > 0:
                        pct = (done_bytes + written) / total_bytes * 100
                        if pct - last_pct >= 1.0 or written >= file_size:
                            last_pct = pct
                            self.progress_sig.emit(min(pct, 99))
        finally:
            try:
                rf.close()
            except Exception:
                pass

    def _sha_of(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def _parse_sha_file(self, sha_path: str) -> dict:
        res = {}
        try:
            with open(sha_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        res[os.path.basename(parts[1])] = parts[0]
        except Exception:
            pass
        return res

    def _verify_dir(self, folder: str):
        sha_path = os.path.join(folder, 'sha256.txt')
        if not os.path.isfile(sha_path):
            raise RuntimeError('缺少 sha256.txt，无法校验')
        expect = self._parse_sha_file(sha_path)
        for fn, h in expect.items():
            lp = os.path.join(folder, fn)
            if not os.path.isfile(lp):
                raise RuntimeError('文件缺失：%s' % fn)
            if self._sha_of(lp) != h:
                raise RuntimeError('SHA-256 校验失败：%s' % fn)

    def _dir_sha_ok(self, folder: str) -> bool:
        try:
            self._verify_dir(folder)
            return True
        except Exception:
            return False

    def _cleanup_expired(self, root: str, keep_days: int) -> int:
        """按目录名时间戳清理超过保留期的历史备份（保留 keep_days 天）"""
        if keep_days <= 0:
            return 0
        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0
        try:
            for name in os.listdir(root):
                d = parse_backup_name(name)
                if not d:
                    continue
                if d < cutoff:
                    shutil.rmtree(os.path.join(root, name), ignore_errors=True)
                    removed += 1
        except Exception:
            pass
        return removed


# ==================== 主窗口 ====================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(920, 640)
        self.cfg = self.load_config()
        self.worker = None
        self._build_ui()
        self._apply_cfg()
        self.refresh_history()
        QTimer.singleShot(80, self.refresh_task_state)

    # ---------- 配置 ----------
    def load_config(self) -> dict:
        try:
            p = os.path.join(app_dir(), 'config.json')
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self):
        cfg = {
            'host': self.ed_host.text().strip() or DEFAULT_HOST,
            'port': int(self.ed_port.text().strip() or DEFAULT_PORT),
            'user': self.ed_user.text().strip() or DEFAULT_USER,
            'key_path': self.ed_key.text().strip(),
            'remote_root': self.ed_remote.text().strip() or DEFAULT_REMOTE_ROOT,
            'remote_script': DEFAULT_REMOTE_SCRIPT,
            'target_dir': self.ed_target.text().strip(),
            'keep_days': self.sp_keep.value(),
            'auto_freq': self.cb_freq.currentIndex(),
            'auto_time': self.ed_time.time().toString('HH:mm'),
            'auto_catchup': self.chk_catchup.isChecked(),
        }
        try:
            with open(os.path.join(app_dir(), 'config.json'), 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log('保存配置失败：' + str(e))

    # ---------- UI ----------
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 12, 14, 12)

        head = QHBoxLayout()
        title = QLabel(APP_NAME)
        title.setStyleSheet('font-size:20px; font-weight:700; color:#176b54;')
        sub = QLabel('  服务器 → 本地/NAS 数据备份（SSH/SFTP）')
        sub.setObjectName('hint')
        head.addWidget(title)
        head.addWidget(sub)
        head.addStretch(1)
        outer.addLayout(head)

        tabs = QTabWidget()
        tabs.addTab(self._tab_main(), '立即备份')
        tabs.addTab(self._tab_history(), '历史备份')
        tabs.addTab(self._tab_auto(), '定期自动')
        outer.addWidget(tabs, 1)

        # 底部状态
        bottom = QHBoxLayout()
        self.lbl_state = QLabel('就绪')
        self.lbl_state.setObjectName('hint')
        self.progress = QProgressBar()
        self.progress.setFixedWidth(260)
        self.progress.setValue(0)
        btn_help = QPushButton('恢复指引')
        btn_help.setObjectName('hint_btn')
        btn_help.clicked.connect(self.show_recovery_guide)
        bottom.addWidget(self.lbl_state)
        bottom.addStretch(1)
        bottom.addWidget(btn_help)
        bottom.addWidget(self.progress)
        outer.addLayout(bottom)

        self.setStyleSheet(MAIN_QSS)

    # Tab1：连接 + 目标 + 立即备份 + 日志
    def _tab_main(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 6, 4, 0)

        g_server = QGroupBox('服务器连接（部署机）')
        form = QFormLayout(g_server)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ed_host = QLineEdit()
        self.ed_port = QLineEdit()
        self.ed_port.setFixedWidth(90)
        self.ed_user = QLineEdit()
        self.ed_key = QLineEdit()
        btn_key = QPushButton('…')
        btn_key.setFixedWidth(34)
        btn_key.clicked.connect(self._pick_key)
        row_key = QHBoxLayout()
        row_key.addWidget(self.ed_key, 1)
        row_key.addWidget(btn_key)
        self.ed_remote = QLineEdit()
        btn_test = QPushButton('测试连接')
        btn_test.clicked.connect(self.test_conn)
        hh = QHBoxLayout()
        hh.addWidget(self.ed_host, 1)
        hh.addWidget(self.ed_port)
        hh.addStretch(1)
        hh.addWidget(btn_test)
        form.addRow('地址/IP', hh)
        form.addRow('用户名', self.ed_user)
        form.addRow('私钥文件', row_key)
        form.addRow('远端备份目录', self.ed_remote)
        v.addWidget(g_server)

        g_target = QGroupBox('备份目标（本地目录或 NAS 共享，如 \\\\NAS\\DailyReadBackup）')
        t = QHBoxLayout(g_target)
        self.ed_target = QLineEdit()
        btn_pick = QPushButton('浏览…')
        btn_pick.clicked.connect(self._pick_target)
        btn_open = QPushButton('打开')
        btn_open.clicked.connect(self._open_target)
        t.addWidget(self.ed_target, 1)
        t.addWidget(btn_pick)
        t.addWidget(btn_open)
        lab_keep = QLabel('保留')
        self.sp_keep = QSpinBox()
        self.sp_keep.setRange(0, 3650)
        self.sp_keep.setSuffix(' 天')
        self.sp_keep.setToolTip('本地/NAS 仅保留最近 N 天备份，0 表示不清理')
        t.addWidget(lab_keep)
        t.addWidget(self.sp_keep)
        v.addWidget(g_target)

        ops = QHBoxLayout()
        self.btn_backup = QPushButton('立即备份（远程出包 + 拉取）')
        self.btn_backup.setObjectName('primary')
        self.btn_backup.clicked.connect(lambda: self.start_backup(True))
        self.btn_pull = QPushButton('仅拉取服务器最新包')
        self.btn_pull.clicked.connect(lambda: self.start_backup(False))
        self.btn_cancel = QPushButton('取消')
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_backup)
        ops.addWidget(self.btn_backup)
        ops.addWidget(self.btn_pull)
        ops.addStretch(1)
        ops.addWidget(self.btn_cancel)
        v.addLayout(ops)

        v.addWidget(QLabel('执行日志（同时写入 ' + os.path.join(app_dir(), 'logs') + '）'))
        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        v.addWidget(self.txt_log, 1)
        return w

    def _tab_history(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 6, 4, 0)
        bar = QHBoxLayout()
        bar.addWidget(QLabel('本地/NAS 已有的备份包：'))
        bar.addStretch(1)
        btn_verify = QPushButton('校验所选')
        btn_verify.clicked.connect(self.verify_selected)
        btn_del = QPushButton('删除所选')
        btn_del.setObjectName('danger')
        btn_del.clicked.connect(self.delete_selected)
        btn_refresh = QPushButton('刷新')
        btn_refresh.clicked.connect(self.refresh_history)
        bar.addWidget(btn_verify)
        bar.addWidget(btn_del)
        bar.addWidget(btn_refresh)
        v.addLayout(bar)
        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(['备份包目录', '数据库', '站点数据', 'SHA 校验状态'])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 4):
            self.tbl.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        v.addWidget(self.tbl, 1)
        return w

    def _tab_auto(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 6, 4, 0)

        g = QGroupBox('Windows 任务计划自动备份（服务器每天 03:10 已自动出包，本机定时拉取）')
        form = QFormLayout(g)
        hrow = QHBoxLayout()
        self.cb_freq = QComboBox()
        self.cb_freq.addItems(['每天', '每周一'])
        self.ed_time = QTimeEdit()
        self.ed_time.setDisplayFormat('HH:mm')
        self.ed_time.setTime(self.ed_time.time().fromString('03:40', 'HH:mm'))
        hrow.addWidget(self.cb_freq)
        hrow.addWidget(self.ed_time)
        self.chk_catchup = QCheckBox('错过计划时间后（如关机）开机尽快补跑一次')
        self.chk_catchup.setChecked(True)
        hrow.addWidget(self.chk_catchup)
        hrow.addStretch(1)
        form.addRow('执行频率', hrow)
        v.addWidget(g)

        ops = QHBoxLayout()
        self.btn_save = QPushButton('保存配置')
        self.btn_save.clicked.connect(self.save_config)
        btn_reg = QPushButton('注册 / 更新计划任务')
        btn_reg.setObjectName('primary')
        btn_reg.clicked.connect(self.register_task)
        btn_unreg = QPushButton('删除计划任务')
        btn_unreg.setObjectName('danger')
        btn_unreg.clicked.connect(self.unregister_task)
        btn_now = QPushButton('立即静默跑一次(--auto)')
        btn_now.setToolTip('等同计划任务触发的静默模式，用于自测')
        btn_now.clicked.connect(self.run_auto_now)
        ops.addWidget(self.btn_save)
        ops.addWidget(btn_reg)
        ops.addWidget(btn_unreg)
        ops.addWidget(btn_now)
        ops.addStretch(1)
        v.addLayout(ops)

        box = QGroupBox('当前计划任务状态')
        bb = QVBoxLayout(box)
        self.lbl_task = QLabel('查询中…')
        self.lbl_task.setWordWrap(True)
        bb.addWidget(self.lbl_task)
        v.addWidget(box)

        note = QLabel('提示：完整备份链路 = 服务器 cron 03:10 出包 → 本机计划任务拉取。'
                      '若备份目标为 NAS 共享目录，请先在本机资源管理器登录该共享（记住凭据），任务才能正常写入。')
        note.setObjectName('hint')
        note.setWordWrap(True)
        v.addWidget(note)
        v.addStretch(1)
        return w

    # ---------- 配置读写 ----------
    def _apply_cfg(self):
        c = self.cfg
        self.ed_host.setText(str(c.get('host', DEFAULT_HOST)))
        self.ed_port.setText(str(c.get('port', DEFAULT_PORT)))
        self.ed_user.setText(str(c.get('user', DEFAULT_USER)))
        self.ed_key.setText(str(c.get('key_path', default_key_path())))
        self.ed_remote.setText(str(c.get('remote_root', DEFAULT_REMOTE_ROOT)))
        self.ed_target.setText(str(c.get('target_dir', '')))
        self.sp_keep.setValue(int(c.get('keep_days', 30)))
        if 'auto_freq' in c:
            self.cb_freq.setCurrentIndex(int(c.get('auto_freq', 0)))
        if 'auto_time' in c:
            try:
                self.ed_time.setTime(self.ed_time.time().fromString(c['auto_time'], 'HH:mm'))
            except Exception:
                pass
        self.chk_catchup.setChecked(bool(c.get('auto_catchup', True)))

    # ---------- 交互 ----------
    def _pick_key(self):
        p, _ = QFileDialog.getOpenFileName(self, '选择 SSH 私钥', os.path.expanduser('~') + '/.ssh')
        if p:
            self.ed_key.setText(p)
            self.save_config()

    def _pick_target(self):
        p = QFileDialog.getExistingDirectory(self, '选择备份目标目录（可输入网络共享 \\\\NAS\\…）',
                                             self.ed_target.text() or os.path.expanduser('~'))
        if p:
            self.ed_target.setText(p)
            self.save_config()

    def _open_target(self):
        d = self.ed_target.text().strip()
        if not d:
            self._log('请先填写备份目标目录')
            return
        try:
            os.makedirs(d, exist_ok=True)
            os.startfile(d)
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, '无法打开目录：%s\n%s' % (d, e))

    def _log(self, msg: str):
        self.txt_log.appendPlainText('[%s] %s' % (datetime.now().strftime('%H:%M:%S'), msg))
        write_log_line(msg)

    def test_conn(self):
        self.save_config()
        host, port, user, key = (self.ed_host.text().strip(), int(self.ed_port.text().strip() or 22),
                                 self.ed_user.text().strip(), self.ed_key.text().strip())
        self._log('正在测试连接 %s@%s:%d …' % (user, host, port))
        def work():
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=host, port=port, username=user, key_filename=key,
                            timeout=20, banner_timeout=20, auth_timeout=20)
                _, out, _ = ssh.exec_command('echo CONNECT_OK; ls -d ' + DEFAULT_REMOTE_ROOT + ' 2>/dev/null && ls -t '
                                             + DEFAULT_REMOTE_ROOT + ' | head -3')
                data = out.read().decode('utf-8', 'replace')
                ssh.close()
                self._log('连接成功：\n' + data.strip())
            except Exception as e:
                self._log('!! 连接失败：' + str(e))
        threading.Thread(target=work, daemon=True).start()

    def _collect_cfg(self) -> dict:
        self.save_config()
        return self.load_config()

    def start_backup(self, trigger: bool):
        cfg = self._collect_cfg()
        if not cfg.get('target_dir'):
            QMessageBox.warning(self, APP_NAME, '请先选择备份目标目录（本地或 NAS 共享）。')
            return
        if not cfg.get('key_path') or not os.path.isfile(cfg['key_path']):
            QMessageBox.warning(self, APP_NAME, 'SSH 私钥文件不存在，请重新选择。')
            return
        if self.worker and self.worker.isRunning():
            return
        self.progress.setValue(0)
        self.btn_backup.setEnabled(False)
        self.btn_pull.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.lbl_state.setText('备份进行中…')
        self.worker = BackupWorker(cfg, trigger)
        self.worker.log_sig.connect(self._log)
        self.worker.progress_sig.connect(self.progress.setValue)
        self.worker.done_sig.connect(self._on_done)
        self.worker.start()

    def _on_done(self, ok: bool, msg: str):
        self.btn_backup.setEnabled(True)
        self.btn_pull.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.lbl_state.setText('成功：' + msg if ok else '失败')
        if ok:
            self._log('完成：' + msg)
        else:
            self._log('!! 备份失败：' + msg)
            QMessageBox.critical(self, APP_NAME, '备份失败：\n' + msg)
        self.refresh_history()

    def cancel_backup(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_cancel.setEnabled(False)
            self._log('正在取消…')

    # ---------- 历史 ----------
    def _target(self) -> str:
        return self.ed_target.text().strip()

    def refresh_history(self):
        root = self._target()
        self.tbl.setRowCount(0)
        if not root or not os.path.isdir(root):
            self.tbl.setRowCount(1)
            self.tbl.setItem(0, 0, QTableWidgetItem('（目标目录为空或不存在）'))
            self.tbl.setSpan(0, 0, 1, 4)
            return
        entries = []
        for name in os.listdir(root):
            d = os.path.join(root, name)
            if not os.path.isdir(d):
                continue
            ts = parse_backup_name(name)
            if not ts:
                continue
            db = site = 0
            for fn in os.listdir(d):
                if fn.startswith('db-') and fn.endswith('.sql'):
                    db += os.path.getsize(os.path.join(d, fn))
                elif fn.startswith('site-') and fn.endswith('.tar.gz'):
                    site += os.path.getsize(os.path.join(d, fn))
            entries.append((name, db, site, ts))
        entries.sort(key=lambda x: x[3], reverse=True)
        self.tbl.setRowCount(len(entries))
        for i, (name, db, site, ts) in enumerate(entries):
            folder = os.path.join(root, name)
            self.tbl.setItem(i, 0, QTableWidgetItem(name))
            self.tbl.setItem(i, 1, QTableWidgetItem(human_size(db)))
            self.tbl.setItem(i, 2, QTableWidgetItem(human_size(site)))
            ok = self._check_dir_quick(folder)
            it = QTableWidgetItem('通过' if ok else '待校验/异常')
            it.setForeground(QColor('#2aa97b') if ok else QColor('#c0392b'))
            self.tbl.setItem(i, 3, it)
            self.tbl.item(i, 0).setData(Qt.ItemDataRole.UserRole, folder)

    def _check_dir_quick(self, folder: str) -> bool:
        try:
            sha_p = os.path.join(folder, 'sha256.txt')
            if not os.path.isfile(sha_p):
                return False
            expect = {}
            with open(sha_p, 'r', encoding='utf-8') as f:
                for line in f:
                    p2 = line.strip().split()
                    if len(p2) >= 2:
                        expect[os.path.basename(p2[1])] = p2[0]
            for fn, h in expect.items():
                lp = os.path.join(folder, fn)
                if not os.path.isfile(lp):
                    return False
                digest = hashlib.sha256()
                with open(lp, 'rb') as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b''):
                        digest.update(chunk)
                if digest.hexdigest() != h:
                    return False
            return True
        except Exception:
            return False

    def _selected_folders(self):
        rows = set()
        for idx in self.tbl.selectedIndexes():
            if idx.column() == 0:
                rows.add(idx.row())
        folders = []
        for r in rows:
            item = self.tbl.item(r, 0)
            d = item.data(Qt.ItemDataRole.UserRole) if item else None
            if d:
                folders.append(d)
        return folders

    def verify_selected(self):
        folders = self._selected_folders()
        if not folders:
            QMessageBox.information(self, APP_NAME, '请先在列表中选择要校验的备份包。')
            return
        for folder in folders:
            name = os.path.basename(folder)
            if self._check_dir_quick(folder):
                self._log('校验通过：%s' % name)
            else:
                self._log('!! 校验失败或文件缺失：%s' % name)

    def delete_selected(self):
        folders = self._selected_folders()
        if not folders:
            QMessageBox.information(self, APP_NAME, '请先选择要删除的备份包。')
            return
        if QMessageBox.question(self, APP_NAME,
                                '确定删除所选 %d 个备份包？\n%s' % (len(folders),
                                '\n'.join(os.path.basename(x) for x in folders))) != QMessageBox.StandardButton.Yes:
            return
        for folder in folders:
            shutil.rmtree(folder, ignore_errors=True)
            self._log('已删除：%s' % os.path.basename(folder))
        self.refresh_history()

    # ---------- 计划任务 ----------
    def task_status_text(self) -> str:
        # 通过 ScheduledTaskInfo 读取运行时间（LastRunTime/NextRunTime 可为 null 或 0001/9999，须归一）
        ps = ('$t = Get-ScheduledTask -TaskName "%s" -ErrorAction SilentlyContinue;'
              ' if ($t) { $i = $t | Get-ScheduledTaskInfo;'
              ' $last = $null; $next = $null;'
              ' if ($null -ne $i) { $last = $i.LastTaskRunTime; $next = $i.NextRunTime };'
              ' if ($null -ne $last) { $last = $last.ToString("yyyy-MM-dd HH:mm") } else { $last = "NEVER" };'
              ' if ($null -ne $next) { $next = $next.ToString("yyyy-MM-dd HH:mm") } else { $next = "NEVER" };'
              ' "%s|" + $t.State + "|" + $last + "|" + $next } else { "NONE" }') % (TASK_NAME, TASK_NAME)
        try:
            r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                               capture_output=True, text=True, timeout=15,
                               encoding='utf-8', errors='replace')
            if r.returncode != 0 and not r.stdout.strip():
                return '查询失败：PowerShell 返回异常（%s）' % r.stderr.strip()[-200:]
            out = r.stdout.strip().split('|')
            if out and out[0] == TASK_NAME:
                state = out[1] if len(out) > 1 else '?'
                last = out[2] if len(out) > 2 and out[2] not in ('NEVER', '01/01/0001 00:00') else '从未'
                nxt = out[3] if len(out) > 3 and out[3] not in ('NEVER', '01/01/0001 00:00', '9999-12-31 00:00') else '未安排'
                return '状态：%s ｜ 上次运行：%s ｜ 下次运行：%s' % (state, last, nxt)
            return '尚未注册计划任务'
        except Exception as e:
            return '查询失败：' + str(e)

    def refresh_task_state(self):
        self.lbl_task.setText(self.task_status_text())

    def register_task(self):
        self.save_config()
        target = self.ed_target.text().strip()
        if not target:
            QMessageBox.warning(self, APP_NAME, '请先填写备份目标目录。')
            return
        exe = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
        arg = '--auto'
        hm = self.ed_time.time().toString('HH:mm')
        if self.cb_freq.currentIndex() == 0:
            trig = 'New-ScheduledTaskTrigger -Daily -At "{0}"'
        else:
            trig = 'New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "{0}"'
        trig = trig.format(hm)
        settings = 'New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)'
        cmd = ('$a = New-ScheduledTaskAction -Execute "{0}" -Argument "{1}";'
               '$t = {2}; $s = {3};'
               'Register-ScheduledTask -TaskName "{4}" -Action $a -Trigger $t -Settings $s '
               '-Description "DailyRead 定期拉取服务器备份" -Force | Out-Null; '
               'Write-Output "REG_OK"').format(exe, arg, trig, settings, TASK_NAME)
        self._log('注册计划任务：%s 每天 %s 执行 %s --auto' % (TASK_NAME, hm, exe))
        try:
            r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                               capture_output=True, text=True, timeout=30, encoding='utf-8')
            if 'REG_OK' in r.stdout:
                self._log('计划任务注册成功')
            else:
                self._log('!! 注册失败：%s %s' % (r.stdout.strip(), r.stderr.strip()))
                QMessageBox.critical(self, APP_NAME, '注册计划任务失败：\n%s %s' % (r.stdout, r.stderr))
        except Exception as e:
            self._log('!! 注册异常：' + str(e))
        self.refresh_task_state()

    def unregister_task(self):
        cmd = 'Unregister-ScheduledTask -TaskName "{0}" -Confirm:$false; Write-Output "DEL_OK"'.format(TASK_NAME)
        try:
            r = subprocess.run(['powershell', '-NoProfile', '-Command', cmd],
                               capture_output=True, text=True, timeout=30, encoding='utf-8')
            if 'DEL_OK' in r.stdout:
                self._log('计划任务已删除')
            else:
                self._log('!! 删除失败：%s %s' % (r.stdout.strip(), r.stderr.strip()))
        except Exception as e:
            self._log('!! 删除异常：' + str(e))
        self.refresh_task_state()

    def run_auto_now(self):
        self.refresh_task_state()
        self.start_backup(False)

    def show_recovery_guide(self):
        txt = (
            '恢复指引\n\n'
            '前提：目标目录下有 backup-<日期时间>/ 备份包，含 db-*.sql（数据库全量逻辑备份，含建库语句）'
            '与 site-*.tar.gz（站点数据）。\n\n'
            '【恢复数据库】\n'
            '  在目标服务器执行：\n'
            '    mysql -u<用户名> -p < db-20260909-2026.sql\n'
            '  或分两步：先建库再导入。应用连接的是 dailyread_db（详见 .env）。\n\n'
            '【恢复站点数据】\n'
            '  解压 site 包到服务器站点根目录并覆盖：\n'
            '    tar -xzf site-20260909-2026.tar.gz -C /opt/dailyread-server\n'
            '  覆盖内容为 public/、uploads/、schema.sql。\n\n'
            '【校验备份完整性】\n'
            '  应用历史页提供一键 SHA-256 校验；也可在包目录执行：\n'
            '    sha256sum -c sha256.txt\n\n'
            '【新增服务器】\n'
            '  1) 服务器部署本 backup.sh + db_env.js 并配 cron 每日 03:10；\n'
            '  2) 本机任务计划无需改动，自动拉取最新包。'
        )
        QMessageBox.information(self, '恢复指引', txt)


# ==================== 静默自动模式 ====================

def run_auto(cfg: dict) -> int:
    """计划任务触发的静默拉取，成功退出 0，失败 1"""
    log_head = '==== 自动备份启动（--auto） ===='
    write_log_line(log_head)
    if not cfg.get('target_dir'):
        write_log_line('自动备份失败：未配置目标目录')
        return 1
    if not cfg.get('key_path') or not os.path.isfile(cfg['key_path']):
        write_log_line('自动备份失败：SSH 私钥不存在')
        return 1
    result = {}

    w = BackupWorker(cfg, False)
    w.log_sig.connect(lambda m: write_log_line(m))
    w.progress_sig.connect(lambda p: None)

    from PyQt6.QtCore import QCoreApplication
    app = QCoreApplication(sys.argv)

    def on_done(ok, msg):
        result['ok'] = ok
        result['msg'] = msg
        app.quit()

    w.done_sig.connect(on_done)
    w.start()
    app.exec()
    w.wait()
    if result.get('ok'):
        write_log_line('自动备份完成：' + result['msg'])
        return 0
    write_log_line('自动备份失败：' + result.get('msg', ''))
    return 1


def main():
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument('--auto', action='store_true', help='静默执行一次拉取备份（供计划任务调用）')
    args = parser.parse_args()

    if args.auto:
        try:
            with open(os.path.join(app_dir(), 'config.json'), 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
        sys.exit(run_auto(cfg))

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
yixue-zonghe 个人工作平台 · 后端服务

零第三方依赖（仅 Python 标准库）。用于「用技能 · 加教材 · 管产物」：
  - 教材库管理：上传 / 同步（PDF→txt 解析）/ 重建索引 / 预览 / 删除
  - 跨库检索：调用 scripts/search_textbooks.py
  - 蒸馏入口：上传素材 → 生成蒸馏指令卡 → 检测产物 → 质检 → 安装到专家库

启动：
    <python> platform/start.py            # 默认 http://127.0.0.1:8770
    <python> platform/start.py --check    # 仅环境自检
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
import zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

# ==================== 常量 ====================

DEFAULT_PORT = 8770
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PYTHON = r"C:\Users\somnu\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

MAX_UPLOAD_BYTES = 500 * 1024 * 1024      # 教材上传上限 500MB
MAX_DISTILL_BYTES = 200 * 1024 * 1024     # 蒸馏素材/归档上限 200MB
INLINE_TEXT_LIMIT = 50 * 1024             # 指令卡内联素材的上限 50KB

TEXTBOOK_EXTS = {".pdf", ".docx", ".doc", ".txt"}
DISTILL_MATERIAL_EXTS = {".pdf", ".docx", ".doc", ".txt", ".md", ".epub"}
ARCHIVE_EXTS = {".zip"}

# 受保护、禁止删除的文件名（不含路径）
PROTECTED_NAMES = {"SKILL.md", ".gitkeep", "_quality.json", "_task.json"}
PROTECTED_PREFIXES = ("textbook-index",)


# ==================== 路径定位 ====================

def _first_existing(*candidates):
    for c in candidates:
        if c and os.path.isdir(c):
            return os.path.abspath(c)
    return None


def resolve_skill_root():
    """SKILL_ROOT 定位：环境变量 → 本平台所在技能包（platform 的上级）→ workbuddy 技能目录 → 当前目录

    优先绑定「本平台自己所在的技能包」，避免机器上存在多份技能副本时
    被其它副本抢占（曾出现：workbuddy 下的旧副本缺 platform/ 导致读取错目录）。
    """
    env = os.environ.get("YIXUE_SKILL_ROOT")
    if env and os.path.isfile(os.path.join(env, "SKILL.md")):
        return os.path.abspath(env)

    here = os.path.dirname(os.path.abspath(__file__))
    own_parent = os.path.abspath(os.path.join(here, ".."))
    home2 = os.path.expanduser("~/.workbuddy/skills/yixue-zonghe")

    root = _first_existing(
        own_parent if os.path.isfile(os.path.join(own_parent, "SKILL.md")) else None,
        home2 if os.path.isfile(os.path.join(home2, "SKILL.md")) else None,
        os.getcwd() if os.path.isfile(os.path.join(os.getcwd(), "SKILL.md")) else None,
    )
    if not root:
        raise RuntimeError(
            "无法定位 yixue-zonghe 技能根目录。请设置环境变量 YIXUE_SKILL_ROOT 指向技能目录。"
        )
    return root


def resolve_python():
    """Python 解释器：环境变量 → workbuddy 默认 → 当前解释器"""
    env = os.environ.get("YIXUE_PYTHON")
    if env and os.path.isfile(env):
        return env
    if os.path.isfile(DEFAULT_PYTHON):
        return DEFAULT_PYTHON
    return sys.executable


SKILL_ROOT = resolve_skill_root()
PYTHON_EXE = resolve_python()
PLATFORM_DIR = os.path.join(SKILL_ROOT, "platform")
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
REFERENCES_DIR = os.path.join(SKILL_ROOT, "references")
CANGJIE_SCRIPTS_DIR = os.path.join(SKILL_ROOT, "仓颉", "scripts")
PRODUCE_DIR = os.path.join(SKILL_ROOT, "蒸馏产出")
INBOX_DIR = os.path.join(PRODUCE_DIR, "_inbox")
TRASH_DIR = os.path.join(PLATFORM_DIR, ".trash")

TEXTBOOK_DIRS = {
    "中医": os.path.join(SKILL_ROOT, "中医教材"),
    "西医": os.path.join(SKILL_ROOT, "西医教材"),
}
INDEX_FILES = {
    "中医": os.path.join(REFERENCES_DIR, "textbook-index.md"),
    "西医": os.path.join(REFERENCES_DIR, "textbook-index-西医.md"),
}
EXPERT_DIRS = {
    "nihaixia": os.path.join(SKILL_ROOT, "倪海厦体系"),
    "shixuemin": os.path.join(SKILL_ROOT, "石学敏体系"),
    "cangjie": os.path.join(SKILL_ROOT, "仓颉"),
    "distilled": PRODUCE_DIR,
}
# 上传/删除允许的根目录
UPLOAD_ROOTS = list(TEXTBOOK_DIRS.values()) + [INBOX_DIR]
DELETE_ROOTS = list(TEXTBOOK_DIRS.values()) + [INBOX_DIR]


# ==================== 通用工具 ====================

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fmt_size(n):
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{int(n)}B" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def dir_stats(path, ignore_names=()):
    """统计目录下文件数与总大小"""
    files, size = 0, 0
    if not os.path.isdir(path):
        return files, size
    for root, dirs, fnames in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".trash")]
        for fn in fnames:
            if fn in ignore_names:
                continue
            try:
                size += os.path.getsize(os.path.join(root, fn))
                files += 1
            except OSError:
                pass
    return files, size


def safe_join(root, *parts):
    """拒绝路径穿越的拼接。返回绝对路径，越界抛 ValueError。"""
    target = os.path.abspath(os.path.join(root, *parts))
    root_abs = os.path.abspath(root)
    if target != root_abs and not target.startswith(root_abs + os.sep):
        raise ValueError(f"路径越界: {target}")
    return target


def safe_filename(name):
    """清理文件名：去目录分量 + 去 Windows 非法字符 + 保留名检查"""
    name = os.path.basename(str(name or "")).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip(". ")
    if not name:
        raise ValueError("非法文件名")
    stem = name.split(".")[0].upper()
    if stem in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(r"(COM|LPT)[1-9]", stem):
        name = "_" + name
    return name


def clean_slug(name):
    """对象名 → 目录 slug（保留中文、字母数字、- _，空格转 _）"""
    s = str(name or "").strip()
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", s)
    s = re.sub(r"\s+", "_", s)
    s = s.strip("._ ")
    if not s:
        raise ValueError("对象名不能为空或全为非法字符")
    return s[:60]


def is_protected(path):
    base = os.path.basename(path)
    if base in PROTECTED_NAMES:
        return True
    return base.startswith(PROTECTED_PREFIXES)


def in_roots(path, roots):
    p = os.path.abspath(path)
    for r in roots:
        ra = os.path.abspath(r)
        if p == ra or p.startswith(ra + os.sep):
            return True
    return False


def safe_extract_zip(zip_path, target_dir):
    """解压 zip 并防 zip-slip。返回解压出的顶层条目名列表。"""
    os.makedirs(target_dir, exist_ok=True)
    tgt = os.path.abspath(target_dir)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            dest = os.path.abspath(os.path.join(tgt, member))
            if dest != tgt and not dest.startswith(tgt + os.sep):
                raise ValueError(f"zip-slip 检测: {member}")
        zf.extractall(tgt)
        return sorted({m.split("/")[0] for m in zf.namelist() if m.strip("/")})


def extract_last_json(text):
    """从混杂输出中提取最后一段完整 JSON 对象"""
    if not text:
        return None
    start = text.rfind("\n{")
    if start == -1:
        start = text.find("{") - 1
    if start != -1:
        try:
            return json.loads(text[start + 1:].strip())
        except Exception:
            pass
    depth, begin = 0, -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                begin = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and begin != -1:
                try:
                    obj = json.loads(text[begin:i + 1])
                    if isinstance(obj, dict) and ("results" in obj or "stats" in obj):
                        return obj
                except Exception:
                    pass
    return None


def parse_multipart(body, boundary):
    """手写 multipart/form-data 解析（Python 3.13 已移除 cgi 模块）。
    返回 [(field_name, filename_or_None, content_bytes), ...]
    """
    sep = b"--" + boundary
    fields = []
    for part in body.split(sep)[1:]:
        if part in (b"--", b"--\r\n", b""):
            continue
        if part.startswith(b"\r\n"):
            part = part[2:]
        if part.endswith(b"\r\n"):
            part = part[:-2]
        head_end = part.find(b"\r\n\r\n")
        if head_end == -1:
            continue
        header = part[:head_end].decode("utf-8", errors="replace")
        content = part[head_end + 4:]
        m_name = re.search(r'name="([^"]*)"', header)
        if not m_name:
            continue
        m_file = re.search(r'filename="([^"]*)"', header)
        fields.append((m_name.group(1), m_file.group(1) if m_file else None, content))
    return fields


def parse_index_categories(index_path):
    """解析 textbook-index.md，返回 ({文件名: 类目}, {类目: 数量})"""
    file_cat, cat_count = {}, {}
    if not os.path.isfile(index_path):
        return file_cat, cat_count
    try:
        with open(index_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return file_cat, cat_count

    cur_cat = None
    for line in lines:
        s = line.strip()
        m = re.match(r"^##\s+(.+?)（(\d+)\s*部）\s*$", s)
        if m:
            cur_cat = m.group(1).strip()
            cat_count[cur_cat] = int(m.group(2))
            continue
        if s.startswith("## "):
            cur_cat = None
            continue
        if cur_cat:
            m2 = re.match(r"^-\s+`([^`]+)`", s)
            if m2:
                file_cat[m2.group(1)] = cur_cat
    return file_cat, cat_count


def read_text_safe(path, max_bytes=None):
    """按常见中文编码尝试读取文本，返回 (text, encoding)"""
    for enc in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return (f.read() if max_bytes is None else f.read(max_bytes)), enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return (f.read() if max_bytes is None else f.read(max_bytes)), "utf-8(replace)"


# ==================== 长任务管理 ====================

TASKS = {}
TASKS_LOCK = threading.Lock()


def start_task(cmd, cwd=None, title=""):
    tid = uuid.uuid4().hex[:10]
    proc = subprocess.Popen(
        cmd, cwd=cwd or SCRIPTS_DIR,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )
    with TASKS_LOCK:
        TASKS[tid] = {
            "id": tid, "title": title or " ".join(cmd[:3]),
            "cmd": " ".join(cmd), "proc": proc, "status": "running",
            "stdout": "", "stderr": "", "returncode": None,
            "started_at": now_str(), "ended_at": None,
        }
    threading.Thread(target=_drain_task, args=(tid,), daemon=True).start()
    return tid


def _drain_task(tid):
    with TASKS_LOCK:
        t = TASKS.get(tid)
    if not t:
        return
    proc = t["proc"]
    try:
        out, err = proc.communicate()
    except Exception as e:  # pragma: no cover
        out, err = "", str(e)
    with TASKS_LOCK:
        t["stdout"], t["stderr"] = out or "", err or ""
        t["returncode"] = proc.returncode
        t["status"] = "done" if proc.returncode == 0 else "failed"
        t["ended_at"] = now_str()


def task_snapshot(tid, tail=4000):
    with TASKS_LOCK:
        t = TASKS.get(tid)
        if not t:
            return None
        return {
            "id": t["id"], "title": t["title"], "cmd": t["cmd"],
            "status": t["status"], "returncode": t["returncode"],
            "started_at": t["started_at"], "ended_at": t["ended_at"],
            "stdout": t["stdout"][-tail:], "stderr": t["stderr"][-tail:],
        }


def run_short(cmd, cwd=None, timeout=120):
    """同步执行短命令，返回 (rc, stdout, stderr)"""
    try:
        p = subprocess.run(
            cmd, cwd=cwd or SCRIPTS_DIR, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", f"命令超时（>{timeout}s）"
    except Exception as e:
        return -1, "", str(e)


# ==================== 蒸馏指令卡 ====================

DISTILL_PROMPT_TEMPLATE = """# 仓颉蒸馏任务：{person}

> 把本文件内容整段复制给 TRAE（已加载 yixue-zonghe 技能）执行即可。
> 任务标识：{slug} ｜ 生成时间：{created_at}

## 任务参数
- 蒸馏类型：{type_label}
- 对象名：{person}
- 聚焦方向：{focus}
- 技能根目录：{skill_root}
- 产出目录：{produce_path}

## 素材（已就位）
{material_list}

## 执行要求
1. 严格遵循 `{skill_root}/仓颉/SKILL.md` 的 Step 0 → Step 7 完整蒸馏流程。
2. 医学场景适配见 `{skill_root}/references/cangjie-distill-guide.md`
   （Step 0 前置扫描 / L1-L7 语义映射 / 专家能力匹配规则表）。
3. 产出写入 `{produce_path}`：
   - `SKILL.md`（v3 模板：我是谁 / 我的认知上下文 / 我看问题的方式 /
     我绝不会做的事 / 我说话的方式 / Harness Engine · 运行时推理）
   - `references/research/01-sources.md`、`02-extraction-notes.md`、`03-key-quotes.md`
4. Step 4 必须向用户展示提取摘要并等待确认后再继续。
5. 完成后必须运行质检并达到 11/11：
   `"{python_exe}" "{skill_root}/仓颉/scripts/quality_check.py" "{produce_path}/SKILL.md"`
6. 质检通过后写 `{produce_path}/_quality.json`
   （字段：passed / total / detail / needs_fix / checked_at）。
7. 回到工作台「技能产物」页点「检测产物」→「质检」→「安装到蒸馏产出」。

## 素材原文
{inline_materials}
"""


def build_distill_prompt(task, materials_abs):
    """生成蒸馏指令卡文本"""
    slug = task["slug"]
    produce_path = os.path.join(PRODUCE_DIR, slug)
    material_list = "\n".join(f"- `{p}`" for p in materials_abs) or "（无）"

    inline_parts = []
    for p in materials_abs:
        ext = os.path.splitext(p)[1].lower()
        try:
            size = os.path.getsize(p)
        except OSError:
            size = 0
        if ext in (".txt", ".md") and size <= INLINE_TEXT_LIMIT:
            try:
                txt, _ = read_text_safe(p)
                inline_parts.append(f"### {os.path.basename(p)}\n\n```\n{txt}\n```")
                continue
            except Exception:
                pass
        inline_parts.append(
            f"### {os.path.basename(p)}\n\n（{fmt_size(size)}，非文本或过大，请用 Read 工具读取 `{p}`）"
        )
    inline = "\n\n".join(inline_parts) or "（无内联素材，请按上方路径读取）"

    return DISTILL_PROMPT_TEMPLATE.format(
        person=task.get("person", slug),
        slug=slug,
        created_at=task.get("created_at", now_str()),
        type_label="A 类人物蒸馏" if task.get("distill_type") == "A" else "B 类教材蒸馏",
        focus=task.get("focus") or "（未指定，按素材整体提炼）",
        skill_root=SKILL_ROOT,
        produce_path=produce_path,
        python_exe=PYTHON_EXE,
        material_list=material_list,
        inline_materials=inline,
    )


# ==================== 蒸馏任务读写 ====================

def task_dir(slug):
    return safe_join(INBOX_DIR, slug)


def read_task(slug):
    tj = os.path.join(task_dir(slug), "_task.json")
    if not os.path.isfile(tj):
        return None
    try:
        with open(tj, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_task(slug, data):
    d = task_dir(slug)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "_task.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def task_status(slug):
    """返回 (status, skill_md_path)；status ∈ pending/produced/quality_ok/quality_fail"""
    d = task_dir(slug)
    skill_md = os.path.join(d, "SKILL.md")
    if not os.path.isfile(skill_md):
        return "pending", None
    qj = os.path.join(d, "_quality.json")
    if os.path.isfile(qj):
        try:
            with open(qj, "r", encoding="utf-8") as f:
                q = json.load(f)
            if q.get("passed") == 11 and not q.get("needs_fix"):
                return "quality_ok", skill_md
            return "quality_fail", skill_md
        except Exception:
            pass
    return "produced", skill_md


def list_distill_tasks():
    tasks = []
    if not os.path.isdir(INBOX_DIR):
        return tasks
    for name in sorted(os.listdir(INBOX_DIR)):
        d = os.path.join(INBOX_DIR, name)
        if not os.path.isdir(d) or name.startswith("_"):
            continue
        data = read_task(name)
        if not data:
            continue
        status, _ = task_status(name)
        mats = []
        mats_dir = os.path.join(d, "materials")
        if os.path.isdir(mats_dir):
            for fn in sorted(os.listdir(mats_dir)):
                fp = os.path.join(mats_dir, fn)
                if os.path.isfile(fp):
                    mats.append({"name": fn, "size": os.path.getsize(fp)})
        q = None
        qj = os.path.join(d, "_quality.json")
        if os.path.isfile(qj):
            try:
                with open(qj, "r", encoding="utf-8") as f:
                    q = json.load(f)
            except Exception:
                q = None
        tasks.append({
            "slug": name,
            "person": data.get("person", name),
            "distill_type": data.get("distill_type", "A"),
            "focus": data.get("focus", ""),
            "created_at": data.get("created_at", ""),
            "status": status,
            "materials": mats,
            "has_prompt": os.path.isfile(os.path.join(d, "DISTILL_PROMPT.md")),
            "quality": q,
        })
    return tasks


def list_installed_experts():
    out = []
    if not os.path.isdir(PRODUCE_DIR):
        return out
    for name in sorted(os.listdir(PRODUCE_DIR)):
        d = os.path.join(PRODUCE_DIR, name)
        if not os.path.isdir(d) or name.startswith("_"):
            continue
        skill_md = os.path.join(d, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        desc = ""
        try:
            txt, _ = read_text_safe(skill_md, max_bytes=4000)
            m = re.search(r"^description:\s*(.+)$", txt, re.M)
            if m:
                desc = m.group(1).strip().strip('"').strip("'")
            else:
                m2 = re.search(r"^>\s*(.+)$", txt, re.M)
                desc = m2.group(1).strip() if m2 else ""
        except Exception:
            pass
        files, size = dir_stats(d)
        q = None
        qj = os.path.join(d, "_quality.json")
        if os.path.isfile(qj):
            try:
                with open(qj, "r", encoding="utf-8") as f:
                    q = json.load(f)
            except Exception:
                q = None
        out.append({"name": name, "desc": desc, "files": files,
                    "size": size, "quality": q, "path": d})
    return out


def quality_check(slug):
    """对 _inbox/<slug>/SKILL.md 跑仓颉质检，写入 _quality.json"""
    d = task_dir(slug)
    skill_md = os.path.join(d, "SKILL.md")
    if not os.path.isfile(skill_md):
        return {"ok": False, "error": "尚未检测到 SKILL.md，请先完成蒸馏"}

    script = os.path.join(CANGJIE_SCRIPTS_DIR, "quality_check.py")
    if not os.path.isfile(script):
        return {"ok": False, "error": f"质检脚本不存在: {script}"}

    rc, out, err = run_short([PYTHON_EXE, script, skill_md],
                             cwd=CANGJIE_SCRIPTS_DIR, timeout=120)
    # 输出中含多个 N/M（如「一手来源占比: 1/1」），必须锚定「结果:」汇总行
    passed = total = 0
    m = re.search(r"结果\s*[:：]\s*(\d+)\s*/\s*(\d+)", out or "")
    if m:
        passed, total = int(m.group(1)), int(m.group(2))
    else:
        allm = re.findall(r"(\d+)\s*/\s*(\d+)", out or "")
        if allm:
            passed, total = int(allm[-1][0]), int(allm[-1][1])
    ok = (rc == 0 and passed == 11 and total == 11)

    result = {
        "passed": passed, "total": total or 11, "ok": ok,
        "needs_fix": not ok, "checked_at": now_str(),
        "raw": (out or "") + (("\n[stderr]\n" + err) if err else ""),
    }
    try:
        with open(os.path.join(d, "_quality.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
    return result


# ==================== HTTP 服务 ====================

class Handler(BaseHTTPRequestHandler):
    server_version = "yixue-platform/1.0"
    protocol_version = "HTTP/1.1"

    # ---------- 响应工具 ----------

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def json_ok(self, data):
        self._send(200, json.dumps({"ok": True, "data": data}, ensure_ascii=False))

    def json_err(self, code, msg, **extra):
        payload = {"ok": False, "error": str(msg)}
        payload.update(extra)
        self._send(code, json.dumps(payload, ensure_ascii=False))

    def read_json(self, limit=2 * 1024 * 1024):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0:
            return {}
        raw = self.rfile.read(min(n, limit))
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def read_multipart(self, limit):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0:
            raise ValueError("空请求体")
        if n > limit:
            raise ValueError(f"请求体过大（{fmt_size(n)} > {fmt_size(limit)}）")
        ctype = self.headers.get("Content-Type") or ""
        m = re.search(r"boundary=([^;]+)", ctype)
        if not m:
            raise ValueError("缺少 multipart boundary")
        boundary = m.group(1).strip().strip('"').encode("utf-8")
        return parse_multipart(self.rfile.read(n), boundary)

    def log_message(self, fmt, *args):
        pass  # 静默，避免刷屏

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ---------- 路由 ----------

    def do_GET(self):
        try:
            u = urlparse(self.path)
            path, q = unquote(u.path), parse_qs(u.query)
            routes = {
                "/api/overview": lambda: self.api_overview(),
                "/api/textbooks": lambda: self.api_textbooks(q),
                "/api/search": lambda: self.api_search(q),
                "/api/experts": lambda: self.api_experts(q),
                "/api/status": lambda: self.api_status(),
                "/api/file": lambda: self.api_file(q),
                "/api/task": lambda: self.api_task(q),
                "/api/distill/tasks": lambda: self.api_distill_tasks(),
                "/api/distill/prompt": lambda: self.api_distill_prompt(q),
            }
            if path in ("/", "/index.html"):
                return self.serve_index()
            if path == "/favicon.ico":
                return self._send(204, b"", "image/x-icon")
            fn = routes.get(path)
            if fn:
                return fn()
            return self.json_err(404, f"未知路径 {path}")
        except Exception as e:
            return self.json_err(500, f"{type(e).__name__}: {e}")

    def do_POST(self):
        try:
            path = unquote(urlparse(self.path).path)
            routes = {
                "/api/upload": self.api_upload,
                "/api/sync": self.api_sync,
                "/api/rebuild-index": self.api_rebuild_index,
                "/api/extract-shixuemin": self.api_extract_shixuemin,
                "/api/distill/task": self.api_distill_create,
                "/api/distill/check": self.api_distill_check,
                "/api/distill/quality": self.api_distill_quality,
                "/api/distill/install": self.api_distill_install,
                "/api/distill/import": self.api_distill_import,
                "/api/shutdown": self.api_shutdown,
            }
            fn = routes.get(path)
            if not fn:
                return self.json_err(404, f"未知路径 {path}")
            return fn()
        except Exception as e:
            return self.json_err(500, f"{type(e).__name__}: {e}")

    def do_DELETE(self):
        try:
            u = urlparse(self.path)
            path, q = unquote(u.path), parse_qs(u.query)
            if path == "/api/delete":
                return self.api_delete(q)
            if path == "/api/distill/task":
                return self.api_distill_task_delete(q)
            return self.json_err(404, f"未知路径 {path}")
        except Exception as e:
            return self.json_err(500, f"{type(e).__name__}: {e}")

    # ---------- 静态 ----------

    def serve_index(self):
        idx = os.path.join(PLATFORM_DIR, "index.html")
        if not os.path.isfile(idx):
            return self._send(500, "index.html 缺失", "text/plain; charset=utf-8")
        with open(idx, "rb") as f:
            self._send(200, f.read(), "text/html; charset=utf-8")

    # ---------- 概览 ----------

    def api_overview(self):
        libs = {}
        for track, d in TEXTBOOK_DIRS.items():
            files, size = dir_stats(d, ignore_names=(".gitkeep",))
            _, cat_count = parse_index_categories(INDEX_FILES[track])
            idx = INDEX_FILES[track]
            libs[f"{track}教材"] = {
                "path": d, "files": files, "size": size, "categories": cat_count,
                "index": idx, "index_exists": os.path.isfile(idx),
                "index_mtime": (datetime.fromtimestamp(os.path.getmtime(idx))
                                .strftime("%Y-%m-%d %H:%M")
                                if os.path.isfile(idx) else None),
            }

        for key, label in (("nihaixia", "倪海厦体系"), ("shixuemin", "石学敏体系"),
                           ("cangjie", "仓颉")):
            d = EXPERT_DIRS[key]
            files, size = dir_stats(d)
            entry = {"path": d, "files": files, "size": size}
            if key == "shixuemin":
                entry["extracted"] = os.path.isfile(os.path.join(d, "针灸全集", "全文.txt"))
            libs[label] = entry

        files, size = dir_stats(PRODUCE_DIR)
        libs["蒸馏产出"] = {
            "path": PRODUCE_DIR, "files": files, "size": size,
            "installed": list_installed_experts(),
            "pending_tasks": len(list_distill_tasks()),
        }

        self.json_ok({
            "skill_root": SKILL_ROOT, "python_exe": PYTHON_EXE,
            "port": self.server.server_address[1], "libraries": libs,
        })

    # ---------- 状态自检 ----------

    def api_status(self):
        issues = []
        chk = os.path.join(SCRIPTS_DIR, "check_deps.py")
        deps_out, deps_rc = "", None
        if os.path.isfile(chk):
            deps_rc, deps_out, _ = run_short([PYTHON_EXE, chk], timeout=90)
            if deps_rc != 0:
                issues.append("依赖自检未通过")
        else:
            issues.append("scripts/check_deps.py 缺失")

        paths = {}
        for label, p in list(TEXTBOOK_DIRS.items()) + [
            ("倪海厦体系", EXPERT_DIRS["nihaixia"]),
            ("石学敏体系", EXPERT_DIRS["shixuemin"]),
            ("仓颉", EXPERT_DIRS["cangjie"]),
            ("蒸馏产出", PRODUCE_DIR),
            ("references", REFERENCES_DIR),
        ]:
            ok = os.path.isdir(p)
            paths[label] = ok
            if not ok:
                issues.append(f"目录缺失: {label}")

        if not os.path.isfile(os.path.join(SCRIPTS_DIR, "search_textbooks.py")):
            issues.append("scripts/search_textbooks.py 缺失")

        idx = INDEX_FILES["中医"]
        idx_age = round((time.time() - os.path.getmtime(idx)) / 3600, 1) \
            if os.path.isfile(idx) else None
        if idx_age is None:
            issues.append("中医索引文件缺失")

        self.json_ok({
            "skill_root": SKILL_ROOT, "python_exe": PYTHON_EXE,
            "python_version": sys.version.split()[0],
            "deps_rc": deps_rc, "deps_output": (deps_out or "")[-2000:],
            "paths": paths, "index_age_hours": idx_age,
            "shixuemin_extracted": os.path.isfile(
                os.path.join(EXPERT_DIRS["shixuemin"], "针灸全集", "全文.txt")),
            "issues": issues, "all_ok": not issues,
        })

    # ---------- 教材列表 ----------

    def api_textbooks(self, q):
        track = (q.get("track", ["中医"])[0] or "中医").strip()
        if track not in TEXTBOOK_DIRS:
            return self.json_err(400, f"未知体系: {track}")
        d = TEXTBOOK_DIRS[track]
        file_cat, _ = parse_index_categories(INDEX_FILES[track])

        category = (q.get("category", [""])[0] or "").strip()
        kw = (q.get("q", [""])[0] or "").strip().lower()
        ext_filter = (q.get("ext", [""])[0] or "").strip().lower()
        try:
            page = max(1, int(q.get("page", ["1"])[0]))
            page_size = min(500, max(10, int(q.get("page_size", ["100"])[0])))
        except ValueError:
            page, page_size = 1, 100

        items = []
        if os.path.isdir(d):
            names = sorted(os.listdir(d))
            stems_src = {os.path.splitext(n)[0].lower() for n in names
                         if n.lower().endswith((".pdf", ".docx", ".doc"))}
            for fn in names:
                fp = os.path.join(d, fn)
                if not os.path.isfile(fp) or fn == ".gitkeep":
                    continue
                ext = os.path.splitext(fn)[1].lower().lstrip(".")
                if ext_filter and ext != ext_filter:
                    continue
                if kw and kw not in fn.lower():
                    continue
                stem = os.path.splitext(fn)[0]
                cat = file_cat.get(fn, file_cat.get(stem + ".txt", ""))
                if category and cat != category:
                    continue
                items.append({
                    "name": fn, "path": fp, "ext": ext,
                    "size": os.path.getsize(fp),
                    "mtime": datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M"),
                    "category": cat,
                    "from_pdf": ext == "txt" and stem.lower() in stems_src,
                })

        total = len(items)
        start = (page - 1) * page_size
        self.json_ok({
            "track": track, "dir": d, "total": total,
            "page": page, "page_size": page_size,
            "items": items[start:start + page_size],
        })

    # ---------- 检索 ----------

    def api_search(self, q):
        keyword = (q.get("keyword", [""])[0] or "").strip()
        if not keyword:
            return self.json_err(400, "keyword 必填")
        track = (q.get("track", ["中医"])[0] or "中医").strip()
        source = (q.get("source", ["all"])[0] or "all").strip()
        category = (q.get("category", [""])[0] or "").strip()
        context = (q.get("context", ["6"])[0] or "6").strip()
        max_hits = (q.get("max_hits", ["20"])[0] or "20").strip()

        # 注意：不能加 --quiet，该脚本在 --quiet 下不填充 results（仅 stats）
        cmd = [PYTHON_EXE, os.path.join(SCRIPTS_DIR, "search_textbooks.py"),
               "--keyword", keyword, "--track", track, "--source", source,
               "--context", context, "--max-hits", max_hits, "--json"]
        if category:
            cmd += ["--category", category]

        rc, out, err = run_short(cmd, timeout=180)
        data = extract_last_json(out)
        if data is None:
            return self.json_err(500, "检索脚本未返回 JSON", returncode=rc,
                                 stdout=(out or "")[-2000:], stderr=(err or "")[-2000:])
        data["returncode"] = rc
        self.json_ok(data)

    # ---------- 专家体系 ----------

    def api_experts(self, q):
        def tree(path, max_entries=400):
            out = []
            if not os.path.isdir(path):
                return out
            for root, dirs, fnames in os.walk(path):
                dirs[:] = [x for x in dirs if x not in ("__pycache__", ".git")]
                for fn in sorted(fnames):
                    if fn == ".gitkeep":
                        continue
                    fp = os.path.join(root, fn)
                    try:
                        out.append({
                            "rel": os.path.relpath(fp, path).replace("\\", "/"),
                            "size": os.path.getsize(fp),
                            "ext": os.path.splitext(fn)[1].lower().lstrip("."),
                        })
                    except OSError:
                        pass
                    if len(out) >= max_entries:
                        return out
            return out

        self.json_ok({
            "nihaixia": {
                "name": "倪海厦体系", "path": EXPERT_DIRS["nihaixia"],
                "files": tree(EXPERT_DIRS["nihaixia"]),
                "skill_md": os.path.join(EXPERT_DIRS["nihaixia"], "SKILL.md"),
            },
            "shixuemin": {
                "name": "石学敏体系", "path": EXPERT_DIRS["shixuemin"],
                "files": tree(EXPERT_DIRS["shixuemin"], max_entries=200),
                "skill_md": os.path.join(EXPERT_DIRS["shixuemin"], "SKILL.md"),
                "extracted": os.path.isfile(
                    os.path.join(EXPERT_DIRS["shixuemin"], "针灸全集", "全文.txt")),
            },
            "cangjie": {
                "name": "仓颉蒸馏工具", "path": EXPERT_DIRS["cangjie"],
                "files": tree(EXPERT_DIRS["cangjie"], max_entries=100),
                "skill_md": os.path.join(EXPERT_DIRS["cangjie"], "SKILL.md"),
            },
            "distilled": {
                "name": "蒸馏产出（动态专家库）", "path": PRODUCE_DIR,
                "installed": list_installed_experts(),
                "pending_tasks": list_distill_tasks(),
            },
        })

    # ---------- 文件预览 ----------

    def api_file(self, q):
        raw = (q.get("path", [""])[0] or "").strip()
        if not raw:
            return self.json_err(400, "path 必填")
        p = os.path.abspath(raw)
        allowed = UPLOAD_ROOTS + [EXPERT_DIRS["nihaixia"], EXPERT_DIRS["shixuemin"],
                                  EXPERT_DIRS["cangjie"], REFERENCES_DIR]
        if not in_roots(p, allowed):
            return self.json_err(403, "路径不在允许范围内")
        if not os.path.isfile(p):
            return self.json_err(404, "文件不存在")
        if os.path.splitext(p)[1].lower() not in (".txt", ".md", ".json", ".html", ".csv"):
            return self.json_err(400, "仅支持预览文本类文件")
        try:
            lines_limit = min(2000, max(20, int(q.get("lines", ["300"])[0])))
        except ValueError:
            lines_limit = 300
        text, enc = read_text_safe(p)
        all_lines = text.splitlines()
        self.json_ok({
            "path": p, "encoding": enc, "size": os.path.getsize(p),
            "total_lines": len(all_lines),
            "truncated": len(all_lines) > lines_limit,
            "content": "\n".join(all_lines[:lines_limit]),
        })

    # ---------- 长任务 ----------

    def api_task(self, q):
        tid = (q.get("id", [""])[0] or "").strip()
        snap = task_snapshot(tid) if tid else None
        if not snap:
            return self.json_err(404, "任务不存在")
        self.json_ok(snap)

    # ---------- 上传教材 ----------

    def api_upload(self):
        fields = self.read_multipart(MAX_UPLOAD_BYTES)
        meta = {n: c.decode("utf-8", errors="replace").strip()
                for n, fn, c in fields if fn is None}
        track = meta.get("track", "中医")
        if track not in TEXTBOOK_DIRS:
            return self.json_err(400, f"未知体系: {track}")
        target_root = TEXTBOOK_DIRS[track]

        uploaded, failed = [], []
        for name, filename, content in fields:
            if filename is None or name != "file":
                continue
            try:
                fn = safe_filename(filename)
                ext = os.path.splitext(fn)[1].lower()
                if ext not in TEXTBOOK_EXTS:
                    raise ValueError(f"不支持的格式 {ext}（仅 {', '.join(sorted(TEXTBOOK_EXTS))}）")
                dest = safe_join(target_root, fn)
                with open(dest, "wb") as f:
                    f.write(content)
                uploaded.append({"name": fn, "size": len(content), "path": dest})
            except Exception as e:
                failed.append({"name": filename, "error": str(e)})
        if not uploaded and failed:
            return self.json_err(400, "; ".join(f"{x['name']}: {x['error']}" for x in failed))
        self.json_ok({"track": track, "uploaded": uploaded, "failed": failed})

    # ---------- 同步（长任务） ----------

    def api_sync(self):
        body = self.read_json()
        track = body.get("track", "中医")
        if track not in TEXTBOOK_DIRS:
            return self.json_err(400, f"未知体系: {track}")
        cmd = [PYTHON_EXE, os.path.join(SCRIPTS_DIR, "sync_new_materials.py"), "--track", track]
        if body.get("rebuild"):
            cmd.append("--rebuild")
        if body.get("only"):
            cmd += ["--only", str(body["only"])]
        if body.get("no_ocr"):
            cmd.append("--no-ocr")
        if body.get("no_images_ocr"):
            cmd.append("--no-images-ocr")
        if body.get("no_index"):
            cmd.append("--no-index")
        if body.get("dpi"):
            cmd += ["--dpi", str(body["dpi"])]
        self.json_ok({"task_id": start_task(cmd, title=f"同步教材（{track}）")})

    # ---------- 重建索引 ----------

    def api_rebuild_index(self):
        body = self.read_json()
        track = body.get("track", "中医")
        if track not in TEXTBOOK_DIRS:
            return self.json_err(400, f"未知体系: {track}")
        cmd = [PYTHON_EXE, os.path.join(SCRIPTS_DIR, "build_textbook_index.py"),
               "--track", track, "--textbook-dir", TEXTBOOK_DIRS[track],
               "--output", INDEX_FILES[track]]
        rc, out, err = run_short(cmd, timeout=180)
        if rc != 0:
            return self.json_err(500, "重建索引失败", rc=rc,
                                 stdout=out[-2000:], stderr=err[-2000:])
        self.json_ok({"track": track, "output": INDEX_FILES[track], "stdout": out[-2000:]})

    # ---------- 抽取石师全文 ----------

    def api_extract_shixuemin(self):
        script = os.path.join(PLATFORM_DIR, "extract_shixuemin.py")
        if not os.path.isfile(script):
            return self.json_err(404, "platform/extract_shixuemin.py 不存在")
        self.json_ok({"task_id": start_task([PYTHON_EXE, script], cwd=PLATFORM_DIR,
                                            title="抽取石学敏针灸全集")})

    # ---------- 蒸馏任务 ----------

    def api_distill_tasks(self):
        self.json_ok({
            "tasks": list_distill_tasks(),
            "installed": list_installed_experts(),
            "inbox_dir": INBOX_DIR, "produce_dir": PRODUCE_DIR,
        })

    def api_distill_prompt(self, q):
        slug = (q.get("task", [""])[0] or "").strip()
        if not slug:
            return self.json_err(400, "task 必填")
        p = safe_join(task_dir(slug), "DISTILL_PROMPT.md")
        if not os.path.isfile(p):
            return self.json_err(404, "指令卡不存在")
        text, _ = read_text_safe(p)
        self.json_ok({"slug": slug, "path": p, "prompt": text})

    def api_distill_create(self):
        fields = self.read_multipart(MAX_DISTILL_BYTES)
        meta = {n: c.decode("utf-8", errors="replace").strip()
                for n, fn, c in fields if fn is None}
        person = meta.get("person", "").strip()
        if not person:
            return self.json_err(400, "对象名（person）必填")
        try:
            slug = clean_slug(person)
        except ValueError as e:
            return self.json_err(400, str(e))

        d = task_dir(slug)
        mats_dir = os.path.join(d, "materials")
        os.makedirs(mats_dir, exist_ok=True)

        saved, failed = [], []
        for name, filename, content in fields:
            if filename is None or name != "file":
                continue
            try:
                fn = safe_filename(filename)
                ext = os.path.splitext(fn)[1].lower()
                if ext not in DISTILL_MATERIAL_EXTS:
                    raise ValueError(f"不支持的素材格式 {ext}")
                dest = safe_join(mats_dir, fn)
                with open(dest, "wb") as f:
                    f.write(content)
                saved.append(fn)
            except Exception as e:
                failed.append({"name": filename, "error": str(e)})

        all_mats = sorted(f for f in os.listdir(mats_dir)
                          if os.path.isfile(os.path.join(mats_dir, f)))
        if not all_mats:
            return self.json_err(400, "至少需要上传一个素材文件")

        old = read_task(slug)
        task = {
            "slug": slug, "person": person,
            "distill_type": "B" if meta.get("distill_type") == "B" else "A",
            "focus": meta.get("focus", ""),
            "created_at": (old or {}).get("created_at") or now_str(),
            "materials": [{"name": f, "size": os.path.getsize(os.path.join(mats_dir, f))}
                          for f in all_mats],
            "status": "pending",
        }
        mats_abs = [os.path.join(mats_dir, f) for f in all_mats]
        prompt = build_distill_prompt(task, mats_abs)
        with open(os.path.join(d, "DISTILL_PROMPT.md"), "w", encoding="utf-8") as f:
            f.write(prompt)
        write_task(slug, task)

        self.json_ok({
            "slug": slug, "person": person, "task_dir": d,
            "materials": task["materials"], "saved": saved, "failed": failed,
            "prompt": prompt, "merged": bool(old),
        })

    def api_distill_check(self):
        body = self.read_json()
        slug = (body.get("slug") or "").strip()
        if not slug or not os.path.isdir(task_dir(slug)):
            return self.json_err(404, "任务不存在")
        status, skill_md = task_status(slug)
        self.json_ok({
            "slug": slug, "status": status, "skill_md": skill_md,
            "message": {
                "pending": "尚未检测到 SKILL.md，请先在 TRAE 中执行蒸馏指令卡",
                "produced": "已检测到 SKILL.md，可进行质检",
                "quality_ok": "质检通过 11/11，可安装到蒸馏产出",
                "quality_fail": "已产出但质检未通过，请查看详情",
            }.get(status, ""),
        })

    def api_distill_quality(self):
        body = self.read_json()
        slug = (body.get("slug") or "").strip()
        if not slug or not os.path.isdir(task_dir(slug)):
            return self.json_err(404, "任务不存在")
        result = quality_check(slug)
        if result.get("error"):
            return self.json_err(400, result["error"])
        self.json_ok(result)

    def api_distill_install(self):
        body = self.read_json()
        slug = (body.get("slug") or "").strip()
        d = task_dir(slug)
        if not slug or not os.path.isdir(d):
            return self.json_err(404, "任务不存在")
        if not os.path.isfile(os.path.join(d, "SKILL.md")):
            return self.json_err(400, "尚未产出 SKILL.md，无法安装")

        status, _ = task_status(slug)
        if status != "quality_ok":
            r = quality_check(slug)
            if r.get("error"):
                return self.json_err(400, r["error"])
            if r.get("passed") != 11:
                return self.json_err(400, f"质检未通过（{r.get('passed')}/{r.get('total')}），请修复后重试",
                                     quality=r)

        target = os.path.join(PRODUCE_DIR, f"{slug}-perspective")
        if os.path.exists(target):
            return self.json_err(409, f"目标已存在: {os.path.basename(target)}")

        try:
            shutil.move(d, target)
        except Exception as e:
            return self.json_err(500, f"移动失败: {e}")

        for junk in ("DISTILL_PROMPT.md", "materials"):
            p = os.path.join(target, junk)
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.isfile(p):
                os.remove(p)

        self.json_ok({"installed": True, "path": target,
                      "name": os.path.basename(target)})

    def api_distill_import(self):
        fields = self.read_multipart(MAX_DISTILL_BYTES)
        saved = None
        for name, filename, content in fields:
            if filename is None or name != "file":
                continue
            fn = safe_filename(filename)
            if os.path.splitext(fn)[1].lower() not in ARCHIVE_EXTS:
                return self.json_err(400, "仅支持 .zip 归档")
            import_root = safe_join(INBOX_DIR, "_import")
            os.makedirs(import_root, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = safe_join(import_root, f"{stamp}_{fn}")
            with open(zip_path, "wb") as f:
                f.write(content)
            saved = zip_path
            break
        if not saved:
            return self.json_err(400, "未收到归档文件")

        stem = os.path.splitext(os.path.basename(saved))[0]
        extract_to = safe_join(INBOX_DIR, "_import", stem)
        try:
            tops = safe_extract_zip(saved, extract_to)
        except Exception as e:
            return self.json_err(400, f"解压失败: {e}")

        candidates = []
        for root, dirs, files in os.walk(extract_to):
            if "SKILL.md" in files:
                candidates.append(root)
        candidates = [c for c in candidates
                      if not any(c != o and c.startswith(o + os.sep) for o in candidates)]
        self.json_ok({"zip": saved, "extracted_to": extract_to,
                      "tops": tops, "candidates": candidates})

    def api_distill_task_delete(self, q):
        slug = (q.get("task", [""])[0] or "").strip()
        if (q.get("confirm", ["0"])[0] or "0") != "1":
            return self.json_err(400, "缺少确认参数 confirm=1")
        d = task_dir(slug)
        if not slug or not os.path.isdir(d):
            return self.json_err(404, "任务不存在")
        os.makedirs(TRASH_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = safe_join(TRASH_DIR, f"{stamp}_{slug}")
        try:
            shutil.move(d, dest)
        except Exception as e:
            return self.json_err(500, f"删除失败: {e}")
        self.json_ok({"deleted": slug, "recycled_to": dest})

    # ---------- 删除文件 ----------

    def api_delete(self, q):
        raw = (q.get("path", [""])[0] or "").strip()
        if (q.get("confirm", ["0"])[0] or "0") != "1":
            return self.json_err(400, "缺少确认参数 confirm=1")
        if not raw:
            return self.json_err(400, "path 必填")
        p = os.path.abspath(raw)
        if not in_roots(p, DELETE_ROOTS):
            return self.json_err(403, "路径不在允许删除范围内")
        if not os.path.isfile(p):
            return self.json_err(404, "文件不存在（仅支持删除文件）")
        if is_protected(p):
            return self.json_err(403, f"受保护文件不可删除: {os.path.basename(p)}")
        os.makedirs(TRASH_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = safe_join(TRASH_DIR, f"{stamp}_{safe_filename(os.path.basename(p))}")
        try:
            shutil.move(p, dest)
        except Exception as e:
            return self.json_err(500, f"删除失败: {e}")
        self.json_ok({"deleted": p, "recycled_to": dest})

    # ---------- 关闭 ----------

    def api_shutdown(self):
        self.json_ok({"message": "服务即将关闭"})
        threading.Timer(0.4, lambda: os._exit(0)).start()


# ==================== 自检 ====================

def run_self_check():
    ok = True
    print("=" * 62)
    print("yixue-zonghe 工作台 · 环境自检")
    print("=" * 62)
    print(f"技能根目录 : {SKILL_ROOT}")
    print(f"Python     : {PYTHON_EXE}")
    print(f"平台目录   : {PLATFORM_DIR}")
    print("-" * 62)

    def chk(label, cond, detail=""):
        nonlocal ok
        print(("✅ " if cond else "❌ ") + label + (f"  {detail}" if detail else ""))
        if not cond:
            ok = False

    chk("index.html 存在", os.path.isfile(os.path.join(PLATFORM_DIR, "index.html")))
    chk("scripts/ 目录", os.path.isdir(SCRIPTS_DIR))
    chk("search_textbooks.py", os.path.isfile(os.path.join(SCRIPTS_DIR, "search_textbooks.py")))
    chk("sync_new_materials.py", os.path.isfile(os.path.join(SCRIPTS_DIR, "sync_new_materials.py")))
    chk("build_textbook_index.py", os.path.isfile(os.path.join(SCRIPTS_DIR, "build_textbook_index.py")))
    chk("仓颉 quality_check.py", os.path.isfile(os.path.join(CANGJIE_SCRIPTS_DIR, "quality_check.py")))
    chk("中医教材目录", os.path.isdir(TEXTBOOK_DIRS["中医"]))
    chk("西医教材目录", os.path.isdir(TEXTBOOK_DIRS["西医"]))
    chk("蒸馏产出目录", os.path.isdir(PRODUCE_DIR))
    chk("倪海厦体系", os.path.isdir(EXPERT_DIRS["nihaixia"]))
    chk("石学敏体系", os.path.isdir(EXPERT_DIRS["shixuemin"]))
    chk("仓颉目录", os.path.isdir(EXPERT_DIRS["cangjie"]))
    chk("references/", os.path.isdir(REFERENCES_DIR))

    print("-" * 62)
    n_tcm = len([f for f in os.listdir(TEXTBOOK_DIRS["中医"]) if f.endswith(".txt")]) \
        if os.path.isdir(TEXTBOOK_DIRS["中医"]) else 0
    n_wm = len([f for f in os.listdir(TEXTBOOK_DIRS["西医"]) if f.endswith(".txt")]) \
        if os.path.isdir(TEXTBOOK_DIRS["西医"]) else 0
    print(f"ℹ️  中医教材 txt: {n_tcm} 部 ｜ 西医教材 txt: {n_wm} 部")
    print(f"ℹ️  蒸馏产出已安装专家: {len(list_installed_experts())} 个")
    print(f"ℹ️  待蒸馏任务: {len(list_distill_tasks())} 个")
    print("-" * 62)
    print("运行依赖自检（check_deps.py）…")
    rc, out, err = run_short([PYTHON_EXE, os.path.join(SCRIPTS_DIR, "check_deps.py")], timeout=120)
    if out:
        print(out.strip()[:1500])
    if err and rc != 0:
        print(err.strip()[:600])
    chk("依赖自检通过", rc == 0, f"(rc={rc})")

    print("=" * 62)
    print("✅ 全部通过，可以启动服务" if ok else "❌ 存在未通过项，请先修复")
    return 0 if ok else 1


# ==================== 入口 ====================

def main():
    ap = argparse.ArgumentParser(description="yixue-zonghe 个人工作平台")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--check", action="store_true", help="仅环境自检，不启动服务")
    ap.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = ap.parse_args()

    if args.check:
        sys.exit(run_self_check())

    if not os.path.isdir(SCRIPTS_DIR):
        print(f"❌ 找不到 scripts 目录: {SCRIPTS_DIR}")
        print("   请设置环境变量 YIXUE_SKILL_ROOT 指向 yixue-zonghe 技能目录")
        sys.exit(1)

    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(TRASH_DIR, exist_ok=True)

    try:
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        print(f"❌ 启动失败（端口 {args.port} 可能被占用）: {e}")
        print("   可改用其它端口：python start.py --port 8771")
        sys.exit(1)

    url = f"http://{args.host}:{args.port}/"
    print("=" * 62)
    print("  yixue-zonghe 个人工作平台")
    print("=" * 62)
    print(f"  技能根目录 : {SKILL_ROOT}")
    print(f"  Python     : {PYTHON_EXE}")
    print(f"  访问地址   : {url}")
    print("=" * 62)
    print("  按 Ctrl+C 退出")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭…")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()

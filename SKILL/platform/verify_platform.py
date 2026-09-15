# -*- coding: utf-8 -*-
"""
yixue-zonghe 工作台 · 端到端自检

在同一进程树内「起服务 + 发请求」（规避沙箱对 loopback 的隔离），
校验环境、路径、依赖与核心 API。

    <python> platform/verify_platform.py
"""
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PASS, FAIL = [], []


def chk(label, cond, detail=""):
    (PASS if cond else FAIL).append(label)
    print(("✅ " if cond else "❌ ") + label + (f"   {detail}" if detail else ""))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get(url, timeout=180):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    print("=" * 64)
    print("yixue-zonghe 工作台 · 端到端自检")
    print("=" * 64)

    # ---------- 1. 导入与路径 ----------
    try:
        import start as S
    except Exception as e:
        print(f"❌ 无法导入 start.py: {e}")
        return 1

    chk("技能根目录可定位", bool(S.SKILL_ROOT) and os.path.isdir(S.SKILL_ROOT), S.SKILL_ROOT)
    chk("Python 解释器存在", os.path.isfile(S.PYTHON_EXE), S.PYTHON_EXE)
    chk("index.html 存在", os.path.isfile(os.path.join(S.PLATFORM_DIR, "index.html")))
    chk("scripts/ 目录存在", os.path.isdir(S.SCRIPTS_DIR))

    for label, p in [("中医教材", S.TEXTBOOK_DIRS["中医"]), ("西医教材", S.TEXTBOOK_DIRS["西医"]),
                     ("倪海厦体系", S.EXPERT_DIRS["nihaixia"]),
                     ("石学敏体系", S.EXPERT_DIRS["shixuemin"]),
                     ("仓颉", S.EXPERT_DIRS["cangjie"]),
                     ("蒸馏产出", S.PRODUCE_DIR), ("references", S.REFERENCES_DIR)]:
        chk(f"目录 · {label}", os.path.isdir(p))

    for label, p in [("search_textbooks.py", os.path.join(S.SCRIPTS_DIR, "search_textbooks.py")),
                     ("sync_new_materials.py", os.path.join(S.SCRIPTS_DIR, "sync_new_materials.py")),
                     ("build_textbook_index.py", os.path.join(S.SCRIPTS_DIR, "build_textbook_index.py")),
                     ("仓颉 quality_check.py", os.path.join(S.CANGJIE_SCRIPTS_DIR, "quality_check.py"))]:
        chk(f"脚本 · {label}", os.path.isfile(p))

    # ---------- 2. 纯函数 ----------
    try:
        S.safe_join("/tmp/root", "..", "etc", "passwd")
        ok_traverse = False
    except ValueError:
        ok_traverse = True
    chk("safe_join 拦截路径穿越", ok_traverse)
    chk("safe_filename 去目录分量", S.safe_filename("../../etc/passwd") == "passwd")
    chk("clean_slug 保留中文", S.clean_slug(" 张三丰 医案 ") == "张三丰_医案")
    chk("is_protected 保护 SKILL.md", S.is_protected("/x/y/SKILL.md"))

    mp = S.parse_multipart(
        b'--B\r\nContent-Disposition: form-data; name="person"\r\n\r\n\xe5\xbc\xa0\xe4\xb8\x89\r\n'
        b'--B\r\nContent-Disposition: form-data; name="file"; filename="a.txt"\r\n\r\nhello\r\n--B--\r\n',
        b"B")
    chk("multipart 解析（2 字段）", len(mp) == 2,
        f"fields={[m[0] for m in mp]}")
    chk("multipart 文件名解析", any(m[1] == "a.txt" for m in mp))

    # ---------- 3. 起服务并打 API ----------
    port = free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), S.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.4)
    base = f"http://127.0.0.1:{port}"
    print("-" * 64)
    print(f"服务已启动于 {base}，开始 API 自检…")

    def api_ok(path, label, timeout=180):
        try:
            j = get(base + path, timeout=timeout)
            ok = bool(j.get("ok"))
            chk(f"API · {label}", ok, "" if ok else str(j.get("error"))[:120])
            return j.get("data") if ok else None
        except Exception as e:
            chk(f"API · {label}", False, str(e)[:140])
            return None

    d = api_ok("/api/overview", "GET /api/overview")
    if d:
        libs = d.get("libraries", {})
        chk("概览含 6 个库", len(libs) >= 6, "、".join(libs.keys()))
        tcm = libs.get("中医教材", {})
        chk("中医教材文件数 > 0", (tcm.get("files") or 0) > 0, f"{tcm.get('files')} 个")
        chk("中医类目已解析", len(tcm.get("categories") or {}) > 0,
            f"{len(tcm.get('categories') or {})} 个类目")

    st = api_ok("/api/status", "GET /api/status")
    if st:
        chk("status 返回 paths", bool(st.get("paths")))

    tb = api_ok("/api/textbooks?track=" + urllib.parse.quote("中医") + "&page=1&page_size=10",
                "GET /api/textbooks")
    if tb:
        chk("教材列表分页生效", len(tb.get("items", [])) <= 10,
            f"返回 {len(tb.get('items', []))} 条 / 共 {tb.get('total')}")

    ex = api_ok("/api/experts", "GET /api/experts")
    if ex:
        chk("专家体系含 4 库", all(k in ex for k in ("nihaixia", "shixuemin", "cangjie", "distilled")))

    dt = api_ok("/api/distill/tasks", "GET /api/distill/tasks")
    if dt:
        chk("蒸馏任务接口可用", "tasks" in dt and "installed" in dt,
            f"任务 {len(dt.get('tasks', []))} 个 / 已装 {len(dt.get('installed', []))} 个")

    sr = api_ok("/api/search?keyword=%E6%A1%82%E6%9E%9D%E6%B1%A4&track=%E4%B8%AD%E5%8C%BB&source=all&context=3&max_hits=5",
                "GET /api/search（桂枝汤）")
    if sr:
        chk("检索返回结果结构", "results" in sr and "stats" in sr)
        chk("检索有实际命中", len(sr.get("results", [])) > 0,
            f"命中 {len(sr.get('results', []))} 个文件")

    # ---------- 4. 蒸馏任务闭环（纯文件系统，不依赖 AI）----------
    print("-" * 64)
    print("蒸馏任务闭环自检（创建 → 检测 → 质检 → 清理）…")
    import io
    import uuid
    slug = "自检样例_" + uuid.uuid4().hex[:6]
    boundary = b"----verifyboundary"
    body = io.BytesIO()
    for name, val in (("person", slug), ("distill_type", "A"), ("focus", "自检")):
        body.write(b"--" + boundary + b"\r\n")
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(str(val).encode("utf-8") + b"\r\n")
    body.write(b"--" + boundary + b"\r\n")
    body.write('Content-Disposition: form-data; name="file"; filename="素材.txt"\r\n'.encode())
    body.write(b"Content-Type: text/plain\r\n\r\n")
    body.write("自检素材：论阳气。".encode("utf-8") + b"\r\n")
    body.write(b"--" + boundary + b"--\r\n")

    req = urllib.request.Request(
        base + "/api/distill/task", data=body.getvalue(), method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            j = json.loads(r.read().decode("utf-8"))
        chk("POST /api/distill/task 创建任务", j.get("ok"), str(j.get("error"))[:120])
        created = j.get("data", {}) if j.get("ok") else {}
        chk("任务生成指令卡", bool(created.get("prompt")) and "仓颉蒸馏任务" in created.get("prompt", ""))
        chk("素材落入 materials/", len(created.get("materials", [])) >= 1)
    except Exception as e:
        chk("POST /api/distill/task", False, str(e)[:140])

    def post_json(path, payload, label, expect_ok=True):
        data = json.dumps(payload).encode("utf-8")
        rq = urllib.request.Request(base + path, data=data, method="POST",
                                    headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(rq, timeout=180) as r:
                j = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                j = json.loads(e.read().decode("utf-8", "replace"))
            except Exception:
                j = {"ok": False, "error": f"HTTP {e.code}"}
        except Exception as e:
            chk(f"POST {path} · {label}", False, str(e)[:140])
            return None
        got = bool(j.get("ok"))
        chk(f"POST {path} · {label}", got == expect_ok,
            "" if got == expect_ok else str(j.get("error"))[:120])
        return j.get("data") if got else None

    ck = post_json("/api/distill/check", {"slug": slug}, "检测产物（应为 pending）")
    if ck:
        chk("待蒸馏状态判定正确", ck.get("status") == "pending", f"status={ck.get('status')}")

    post_json("/api/distill/quality", {"slug": slug}, "质检（无 SKILL.md 应被拒）",
              expect_ok=False)

    # 清理
    try:
        rq = urllib.request.Request(
            base + f"/api/distill/task?task={urllib.parse.quote(slug)}&confirm=1",
            method="DELETE")
        with urllib.request.urlopen(rq, timeout=60) as r:
            j = json.loads(r.read().decode("utf-8"))
        chk("DELETE 删除自检任务", j.get("ok"))
    except Exception as e:
        chk("DELETE 删除自检任务", False, str(e)[:140])

    httpd.shutdown()

    # ---------- 汇总 ----------
    print("=" * 64)
    print(f"通过 {len(PASS)} 项 ｜ 失败 {len(FAIL)} 项")
    if FAIL:
        print("失败清单：")
        for f in FAIL:
            print("  ❌ " + f)
    print("=" * 64)
    print("🎉 全部通过" if not FAIL else "⚠️ 存在失败项，请检查上方输出")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())

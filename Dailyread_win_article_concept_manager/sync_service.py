# -*- coding: utf-8 -*-
"""同步服务：离线写队列 + 增量拉取"""
import json
import os
import threading
import time
from datetime import datetime

from api_client import api_client
from app_paths import data_path


# ---------- 离线写队列 ----------
QUEUE_FILE = data_path("offline_queue.json")


class OfflineWriteQueue:
    """离线写队列（持久化到 JSON 文件）"""

    def __init__(self):
        self._lock = threading.Lock()
        self._items = []
        self._load()

    def _load(self):
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                    self._items = json.load(f)
            except Exception:
                self._items = []

    def _persist(self):
        try:
            with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._items, f, ensure_ascii=False)
        except Exception as e:
            print(f"[Queue] 持久化失败: {e}")

    def enqueue(self, op, entity, client_id, payload):
        with self._lock:
            self._items.append({
                'op': op,
                'entity': entity,
                'clientId': client_id,
                'payload': payload,
                'createdAt': datetime.now().isoformat(),
                'retry': 0
            })
            self._persist()

    def get_all(self):
        with self._lock:
            return list(self._items)

    def remove(self, item):
        with self._lock:
            if item in self._items:
                self._items.remove(item)
                self._persist()

    def size(self):
        with self._lock:
            return len(self._items)

    def clear(self):
        """清空队列"""
        with self._lock:
            self._items = []
            self._persist()


# ---------- 同步服务 ----------
class SyncService:
    """同步服务：消费写队列 + 增量拉取"""

    SYNC_STATE_FILE = data_path("sync_state.json")

    def __init__(self):
        self.queue = OfflineWriteQueue()
        self._stop = False
        self._thread = None
        self._on_status = None  # 回调：状态变更通知
        self._last_article_since = self._load_since('article')
        self._last_checkin_since = self._load_since('checkin')

    def _load_since(self, kind):
        if os.path.exists(self.SYNC_STATE_FILE):
            try:
                with open(self.SYNC_STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f).get(f'{kind}_since', '')
            except Exception:
                pass
        return ''

    def _save_since(self, kind, value):
        data = {}
        if os.path.exists(self.SYNC_STATE_FILE):
            try:
                with open(self.SYNC_STATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                pass
        data[f'{kind}_since'] = value
        try:
            with open(self.SYNC_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"[Sync] 保存 since 失败: {e}")

    def set_status_callback(self, cb):
        self._on_status = cb

    def _notify(self, msg):
        if self._on_status:
            try:
                self._on_status(msg)
            except Exception:
                pass

    # ---------- 写操作入队（供 DataModel 调用） ----------
    def enqueue_article_create(self, article):
        cid = str(article.get('clientId') or article.get('id') or '')
        self.queue.enqueue('create', 'article', cid, self._normalize_article(article))

    def enqueue_article_update(self, article):
        cid = str(article.get('clientId') or article.get('id') or '')
        self.queue.enqueue('update', 'article', cid, self._normalize_article(article))

    def enqueue_article_delete(self, client_id):
        self.queue.enqueue('delete', 'article', str(client_id), {'clientId': str(client_id)})

    def _normalize_article(self, article):
        """把本地文章字段转为服务端格式（clientId 为全局唯一标识）"""
        a = dict(article)
        a['clientId'] = str(a.get('clientId') or a.get('id') or '')
        a['lastModified'] = a.get('lastModified') or datetime.now().isoformat()
        return a

    # ---------- 消费队列 ----------
    def _consume_one(self, item):
        entity = item['entity']
        op = item['op']
        payload = item['payload']
        if entity == 'article':
            if op in ('create', 'update'):
                r = api_client.push_article(payload)
            elif op == 'delete':
                r = api_client.delete_article(payload.get('clientId'))
            else:
                return True
        elif entity == 'checkin':
            r = api_client.push_checkin(payload.get('articleId'),
                                       payload.get('checkInDate'),
                                       payload.get('checkInTime'),
                                       payload.get('lastModified'))
        else:
            return True
        return r.get('code') == 0

    def _consume_loop(self):
        while not self._stop:
            items = self.queue.get_all()
            if not items:
                time.sleep(3)
                continue
            self._notify(f"同步中... 剩余 {self.queue.size()} 条")
            for item in list(items):
                if self._stop:
                    break
                try:
                    ok = self._consume_one(item)
                    if ok:
                        self.queue.remove(item)
                    else:
                        item['retry'] = item.get('retry', 0) + 1
                        if item['retry'] >= 3:
                            self.queue.remove(item)
                            print(f"[Sync] 放弃重试: {item.get('op')} {item.get('clientId')}")
                        time.sleep(1)
                except Exception as e:
                    print(f"[Sync] 消费异常: {e}")
                    time.sleep(3)
            time.sleep(1)
        self._notify("同步空闲")

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop = False
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()
        self._notify("同步已启动")

    def stop(self):
        self._stop = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def reset_sync_state(self):
        """重置同步状态（切换账号时调用）"""
        self._last_article_since = ''
        self._last_checkin_since = ''
        self._save_since('article', '')
        self._save_since('checkin', '')
        # 清空离线写队列
        self.queue.clear()

    # ---------- 增量拉取 ----------
    def pull_articles(self, on_article_merged):
        """拉取服务端增量文章，合并到本地。
        on_article_merged(remote_articles: list, next_since: str)
        """
        r = api_client.fetch_articles(self._last_article_since)
        if r.get('code') != 0:
            self._notify(f"拉取文章失败: {r.get('message')}")
            return
        data = r.get('data') or {}
        articles = data.get('articles', [])
        next_since = data.get('nextSince', '')
        if articles:
            on_article_merged(articles, next_since)
        if next_since:
            self._last_article_since = next_since
            self._save_since('article', next_since)
        self._notify(f"拉取 {len(articles)} 篇增量文章")

    def pull_checkins(self, on_checkin_merged):
        r = api_client.fetch_checkins(self._last_checkin_since)
        if r.get('code') != 0:
            return
        data = r.get('data') or {}
        checkins = data.get('checkins', [])
        next_since = data.get('nextSince', '')
        if checkins:
            on_checkin_merged(checkins, next_since)
        if next_since:
            self._last_checkin_since = next_since
            self._save_since('checkin', next_since)


# 全局单例
sync_service = SyncService()

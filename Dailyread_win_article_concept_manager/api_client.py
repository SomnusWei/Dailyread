# -*- coding: utf-8 -*-
"""DailyRead API 客户端 - HTTP 调用 + JWT 持久化"""
import json
import os
import threading

import requests

from app_paths import data_path


class ApiClient:
    """服务端 API 客户端（线程安全：所有方法独立 session）"""

    BASE_URL = "https://dailyread.sonnusww.top"
    TOKEN_FILE = data_path("auth_token.json")  # 与 app_data.json 同目录

    def __init__(self):
        self.token = None
        self.user = None  # {id, username, nickname}
        self._lock = threading.Lock()
        self._load_token()

    # ---------- 鉴权状态 ----------
    def _load_token(self):
        if os.path.exists(self.TOKEN_FILE):
            try:
                with open(self.TOKEN_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    self.user = data.get('user')
            except Exception:
                pass

    def _save_token(self):
        try:
            with open(self.TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump({'token': self.token, 'user': self.user}, f, ensure_ascii=False)
        except Exception as e:
            print(f"[ApiClient] 保存 token 失败: {e}")

    def clear_token(self):
        self.token = None
        self.user = None
        try:
            if os.path.exists(self.TOKEN_FILE):
                os.remove(self.TOKEN_FILE)
        except Exception:
            pass

    def is_logged_in(self):
        return bool(self.token)

    # ---------- HTTP 封装 ----------
    def _headers(self):
        h = {"Content-Type": "application/json; charset=utf-8"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method, path, **kwargs):
        url = self.BASE_URL + path
        kwargs.setdefault('timeout', 30)
        kwargs.setdefault('headers', self._headers())
        try:
            resp = requests.request(method, url, **kwargs)
            if resp.status_code == 401:
                # token 过期
                self.clear_token()
                return {'code': 401, 'message': '登录已过期，请重新登录', 'data': None}
            try:
                return resp.json()
            except Exception:
                return {'code': resp.status_code, 'message': f'响应解析失败: {resp.text[:200]}', 'data': None}
        except requests.exceptions.ConnectionError:
            return {'code': -1, 'message': '网络连接失败，请检查网络', 'data': None}
        except requests.exceptions.Timeout:
            return {'code': -1, 'message': '请求超时', 'data': None}
        except Exception as e:
            return {'code': -1, 'message': f'请求异常: {e}', 'data': None}

    # ---------- 鉴权 API ----------
    def register(self, username, password, nickname=""):
        r = self._request('POST', '/api/auth/register',
                          json={'username': username, 'password': password, 'nickname': nickname})
        if r.get('code') == 0:
            data = r['data']
            self.token = data['token']
            self.user = data['user']
            self._save_token()
        return r

    def login(self, username, password):
        r = self._request('POST', '/api/auth/login',
                          json={'username': username, 'password': password})
        if r.get('code') == 0:
            data = r['data']
            self.token = data['token']
            self.user = data['user']
            self._save_token()
        return r

    def check_username(self, username):
        return self._request('POST', '/api/auth/check-username', json={'username': username})

    def logout(self):
        self.clear_token()

    def verify_token(self):
        """验证 token 是否仍然有效（用户是否仍存在）。
        返回 True 表示有效，False 表示无效（用户已删除/token 过期）。"""
        if not self.token:
            return False
        r = self._request('GET', '/api/auth/me')
        if r.get('code') == 0:
            # 更新用户信息
            data = r['data']
            self.user = {
                'id': data.get('id'),
                'username': data.get('username'),
                'nickname': data.get('nickname', '')
            }
            self._save_token()
            return True
        # 401（token 过期）或 404（用户已删除）：清除本地登录状态
        self.clear_token()
        return False

    # ---------- 文章 API ----------
    def fetch_articles(self, since=""):
        params = {'since': since} if since else {}
        return self._request('GET', '/api/articles', params=params)

    def push_article(self, article):
        """article 必须包含 clientId 字段"""
        return self._request('POST', '/api/articles', json=article)

    def push_articles_batch(self, articles):
        return self._request('POST', '/api/articles/batch', json=articles)

    def delete_article(self, client_id):
        return self._request('DELETE', f'/api/articles/{client_id}')

    # ---------- 打卡 API ----------
    def fetch_checkins(self, since=""):
        params = {'since': since} if since else {}
        return self._request('GET', '/api/checkins', params=params)

    def push_checkin(self, article_id, check_in_date, check_in_time=None, last_modified=None):
        return self._request('POST', '/api/checkins', json={
            'articleId': article_id,
            'checkInDate': check_in_date,
            'checkInTime': check_in_time,
            'lastModified': last_modified
        })

    # ---------- 每日任务 API ----------
    def fetch_today_task(self):
        return self._request('GET', '/api/daily-tasks/today')

    def save_today_task(self, payload):
        return self._request('POST', '/api/daily-tasks/today', json=payload)

    def checkin_task_item(self, item_id):
        return self._request('POST', '/api/daily-tasks/today/checkin', json={'itemId': item_id})

    # ---------- 配置 API ----------
    def fetch_config(self):
        return self._request('GET', '/api/config')

    def push_config(self, cfg):
        return self._request('PUT', '/api/config', json=cfg)

    # ---------- 每日任务 API ----------
    def fetch_today_task(self):
        return self._request('GET', '/api/daily-tasks/today')

    def generate_today_task(self, force=False):
        return self._request('POST', '/api/daily-tasks/generate', json={'force': force})

    # ---------- 迁移 API ----------
    def migrate_import(self, articles, checkins=None):
        return self._request('POST', '/api/migrate/import',
                            json={'articles': articles, 'checkins': checkins or []})


# 全局单例
api_client = ApiClient()

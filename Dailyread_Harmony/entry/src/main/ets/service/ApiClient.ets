/**
 * DailyRead API 客户端
 * 功能：HTTP 请求 + JWT 持久化（使用 Preferences）
 * 支持：设备ID生成、唯一设备登录、401冲突处理、文章PATCH部分更新
 */
import http from '@ohos.net.http';
import preferences from '@ohos.data.preferences';
import common from '@ohos.app.ability.common';
import { User, AuthResult } from '../model/User';
import {
  ApiResponse,
  RegisterBody,
  LoginBody,
  CheckUsernameBody,
  CheckinBody,
  TaskCheckinBody,
  CheckinByArticleBody,
  MigrateImportBody,
  ArticlePatchPayload,
  ArticlePayload,
  ConfigPayload,
  DailyTaskPayload,
  GenerateTaskBody
} from '../model/ApiTypes';

const BASE_URL: string = 'https://d.sonnusww.top';
const PREF_STORE: string = 'dailyread_auth';
const KEY_TOKEN: string = 'token';
const KEY_USER: string = 'user';
const KEY_ARTICLE_SINCE: string = 'article_since';
const KEY_CHECKIN_SINCE: string = 'checkin_since';
const KEY_DEVICE_ID: string = 'device_id';
const KEY_CONFIG_SINCE: string = 'config_since';

export class ApiClient {
  private static instance: ApiClient;
  private token: string = '';
  private user: User | null = null;
  private prefs: preferences.Preferences | null = null;
  private articleSince: string = '';
  private checkinSince: string = '';
  private configSince: string = '';
  private deviceId: string = '';
  private conflictCallback: ((msg: string) => void) | null = null;

  private constructor() {}

  static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  /**
   * 设置401冲突回调（设备冲突时通知UI）
   */
  setConflictCallback(cb: (msg: string) => void): void {
    this.conflictCallback = cb;
  }

  /**
   * 初始化 Preferences（在 EntryAbility 中调用）
   */
  async init(context: common.Context): Promise<void> {
    this.prefs = await preferences.getPreferences(context, PREF_STORE);
    this.token = await this.prefs.get(KEY_TOKEN, '') as string;
    const userStr = await this.prefs.get(KEY_USER, '') as string;
    if (userStr) {
      try {
        this.user = JSON.parse(userStr) as User;
      } catch (e) {
        console.error('ApiClient: 解析用户失败: ' + JSON.stringify(e));
      }
    }
    this.articleSince = await this.prefs.get(KEY_ARTICLE_SINCE, '') as string;
    this.checkinSince = await this.prefs.get(KEY_CHECKIN_SINCE, '') as string;
    this.configSince = await this.prefs.get(KEY_CONFIG_SINCE, '') as string;

    // 加载或生成设备ID
    this.deviceId = await this.prefs.get(KEY_DEVICE_ID, '') as string;
    if (!this.deviceId) {
      this.deviceId = this.generateDeviceId();
      await this.prefs.put(KEY_DEVICE_ID, this.deviceId);
      await this.prefs.flush();
      console.info('ApiClient: 生成新设备ID=' + this.deviceId);
    } else {
      console.info('ApiClient: 加载已有设备ID=' + this.deviceId);
    }

    console.info('ApiClient: 初始化完成, isLoggedIn=' + this.isLoggedIn() + ', deviceId=' + this.deviceId);
  }

  /**
   * 生成唯一设备ID（基于时间戳+随机数+鸿蒙特征）
   */
  private generateDeviceId(): string {
    const ts = Date.now().toString(36);
    const rand = Math.floor(Math.random() * 1000000).toString(36);
    return 'hm_device_' + ts + '_' + rand;
  }

  getDeviceId(): string {
    return this.deviceId;
  }

  isLoggedIn(): boolean {
    return this.token.length > 0;
  }

  getToken(): string {
    return this.token;
  }

  getUser(): User | null {
    return this.user;
  }

  private async saveAuth(token: string, user: User): Promise<void> {
    this.token = token;
    this.user = user;
    if (this.prefs) {
      await this.prefs.put(KEY_TOKEN, token);
      await this.prefs.put(KEY_USER, JSON.stringify(user));
      await this.prefs.flush();
    }
  }

  async clearAuth(): Promise<void> {
    this.token = '';
    this.user = null;
    this.articleSince = '';
    this.checkinSince = '';
    this.configSince = '';
    if (this.prefs) {
      await this.prefs.delete(KEY_TOKEN);
      await this.prefs.delete(KEY_USER);
      await this.prefs.delete(KEY_ARTICLE_SINCE);
      await this.prefs.delete(KEY_CHECKIN_SINCE);
      await this.prefs.delete(KEY_CONFIG_SINCE);
      await this.prefs.flush();
    }
  }

  getArticleSince(): string {
    return this.articleSince;
  }

  getCheckinSince(): string {
    return this.checkinSince;
  }

  getConfigSince(): string {
    return this.configSince;
  }

  async setArticleSince(since: string): Promise<void> {
    this.articleSince = since;
    if (this.prefs) {
      await this.prefs.put(KEY_ARTICLE_SINCE, since);
      await this.prefs.flush();
    }
  }

  async setCheckinSince(since: string): Promise<void> {
    this.checkinSince = since;
    if (this.prefs) {
      await this.prefs.put(KEY_CHECKIN_SINCE, since);
      await this.prefs.flush();
    }
  }

  async setConfigSince(since: string): Promise<void> {
    this.configSince = since;
    if (this.prefs) {
      await this.prefs.put(KEY_CONFIG_SINCE, since);
      await this.prefs.flush();
    }
  }

  /**
   * 通用 HTTP 请求
   */
  private async request(method: string, path: string, body?: Object): Promise<ApiResponse> {
    const url: string = BASE_URL + path;
    const httpRequest = http.createHttp();
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json; charset=utf-8'
      };
      if (this.token) {
        headers['Authorization'] = 'Bearer ' + this.token;
      }
      const option: http.HttpRequestOptions = {
        method: method as http.RequestMethod,
        header: headers,
        connectTimeout: 15000,
        readTimeout: 30000
      };
      if (body) {
        option.extraData = JSON.stringify(body);
      }
      const resp = await httpRequest.request(url, option);
      const bodyStr: string = resp.result as string;

      // 401 处理：检查是否为设备冲突
      if (resp.responseCode === 401) {
        try {
          const errData = JSON.parse(bodyStr) as Record<string, Object>;
          const errMsg = (errData['message'] as string) || '登录已过期';
          const errCode = (errData['code'] as number) || 401;
          const errResp: ApiResponse = { code: errCode, message: errMsg, data: errData['data'] || null };
          // 检查是否为设备冲突
          const dataObj = errData['data'] as Record<string, Object> | null;
          if (dataObj && dataObj['conflict'] === true) {
            console.warn('ApiClient: 设备冲突，账号已在其他设备登录');
            // 清除本地token
            await this.clearAuth();
            // 通知UI
            if (this.conflictCallback) {
              this.conflictCallback('账号已在其他设备登录，请重新登录');
            }
          } else {
            await this.clearAuth();
          }
          return errResp;
        } catch (e) {
          await this.clearAuth();
          const errResp: ApiResponse = { code: 401, message: '登录已过期', data: null };
          return errResp;
        }
      }

      try {
        return JSON.parse(bodyStr) as ApiResponse;
      } catch (e) {
        const errResp: ApiResponse = { code: resp.responseCode, message: '响应解析失败', data: null };
        return errResp;
      }
    } catch (e) {
      console.error('ApiClient request error: ' + JSON.stringify(e));
      const errResp: ApiResponse = { code: -1, message: '网络请求失败: ' + JSON.stringify(e), data: null };
      return errResp;
    } finally {
      httpRequest.destroy();
    }
  }

  // ---------- 鉴权 ----------
  async register(username: string, password: string, nickname: string): Promise<AuthResult | null> {
    const body: RegisterBody = {
      username: username,
      password: password,
      nickname: nickname,
      deviceId: this.deviceId
    };
    const r = await this.request('POST', '/api/auth/register', body);
    if (r.code === 0) {
      const data = r.data as Record<string, Object>;
      const token = data['token'] as string;
      const userObj = data['user'] as Record<string, Object>;
      const user: User = {
        id: userObj['id'] as number,
        username: userObj['username'] as string,
        nickname: userObj['nickname'] as string
      };
      await this.saveAuth(token, user);
      const result: AuthResult = { token: token, user: user };
      return result;
    }
    return null;
  }

  async login(username: string, password: string): Promise<AuthResult | null> {
    const body: LoginBody = {
      username: username,
      password: password,
      deviceId: this.deviceId
    };
    const r = await this.request('POST', '/api/auth/login', body);
    if (r.code === 0) {
      const data = r.data as Record<string, Object>;
      const token = data['token'] as string;
      const userObj = data['user'] as Record<string, Object>;
      const user: User = {
        id: userObj['id'] as number,
        username: userObj['username'] as string,
        nickname: userObj['nickname'] as string
      };
      await this.saveAuth(token, user);
      const result: AuthResult = { token: token, user: user };
      return result;
    }
    return null;
  }

  async checkUsername(username: string): Promise<boolean> {
    const body: CheckUsernameBody = { username: username };
    const r = await this.request('POST', '/api/auth/check-username', body);
    if (r.code === 0) {
      const data = r.data as Record<string, Object>;
      return data['available'] as boolean;
    }
    return false;
  }

  /**
   * 登出（通知服务端清除 device_id）
   */
  async logout(): Promise<void> {
    if (this.isLoggedIn()) {
      try {
        await this.request('POST', '/api/auth/logout');
      } catch (e) {
        console.error('logout API error: ' + JSON.stringify(e));
      }
    }
    await this.clearAuth();
  }

  // ---------- 文章 ----------
  async fetchArticles(since: string): Promise<Record<string, Object> | null> {
    const path: string = since ? '/api/articles?since=' + encodeURIComponent(since) : '/api/articles';
    const r = await this.request('GET', path);
    if (r.code === 0) {
      return r.data as Record<string, Object>;
    }
    return null;
  }

  async pushArticle(article: ArticlePayload): Promise<boolean> {
    const r = await this.request('POST', '/api/articles', article);
    return r.code === 0;
  }

  /**
   * PATCH 文章部分更新（仅更新指定字段，不需要title）
   * 用于同步打卡完成率等局部更新
   */
  async patchArticle(clientId: string, payload: ArticlePatchPayload): Promise<boolean> {
    const r = await this.request('PATCH', '/api/articles/' + clientId, payload);
    return r.code === 0;
  }

  async deleteArticle(clientId: string): Promise<boolean> {
    const r = await this.request('DELETE', '/api/articles/' + clientId);
    return r.code === 0;
  }

  // ---------- 打卡（articleId 为 clientId 字符串） ----------
  async pushCheckin(articleId: string, checkInDate: string, checkInTime: string): Promise<boolean> {
    const body: CheckinBody = {
      articleId: articleId, checkInDate: checkInDate, checkInTime: checkInTime,
      lastModified: new Date().toISOString()
    };
    const r = await this.request('POST', '/api/checkins', body);
    return r.code === 0;
  }

  async fetchCheckins(since: string): Promise<Record<string, Object> | null> {
    const path: string = since ? '/api/checkins?since=' + encodeURIComponent(since) : '/api/checkins';
    const r = await this.request('GET', path);
    if (r.code === 0) {
      return r.data as Record<string, Object>;
    }
    return null;
  }

  // ---------- 每日任务 ----------
  async fetchTodayTask(): Promise<Record<string, Object> | null> {
    const r = await this.request('GET', '/api/daily-tasks/today');
    if (r.code === 0) {
      return r.data as Record<string, Object>;
    }
    return null;
  }

  /**
   * 由服务端生成今日任务
   * @param force 是否强制重新生成（忽略已有任务）
   */
  async generateTodayTask(force: boolean = false): Promise<Record<string, Object> | null> {
    const body: GenerateTaskBody = {};
    if (force) {
      body.force = true;
    }
    const r = await this.request('POST', '/api/daily-tasks/generate', body);
    if (r.code === 0) {
      return r.data as Record<string, Object>;
    }
    return null;
  }

  async saveTodayTask(payload: DailyTaskPayload): Promise<boolean> {
    const r = await this.request('POST', '/api/daily-tasks/today', payload);
    return r.code === 0;
  }

  async checkinTaskItem(itemId: number): Promise<boolean> {
    const body: TaskCheckinBody = { itemId: itemId };
    const r = await this.request('POST', '/api/daily-tasks/today/checkin', body);
    return r.code === 0;
  }

  /**
   * 通过文章 client_id 打卡（多端安全，只设为1不回退）
   */
  async checkinByArticle(articleClientId: string): Promise<ApiResponse> {
    const body: CheckinByArticleBody = { articleId: articleClientId };
    const r = await this.request('POST', '/api/daily-tasks/today/checkin-by-article', body);
    return r;
  }

  // ---------- 配置 ----------
  async fetchConfig(): Promise<Record<string, Object> | null> {
    const r = await this.request('GET', '/api/config');
    if (r.code === 0) {
      return r.data as Record<string, Object>;
    }
    return null;
  }

  async pushConfig(cfg: ConfigPayload): Promise<boolean> {
    const r = await this.request('PUT', '/api/config', cfg);
    return r.code === 0;
  }

  // ---------- 迁移 ----------
  async migrateImport(articles: Object[], checkins: Object[]): Promise<Record<string, number> | null> {
    const body: MigrateImportBody = {
      articles: articles, checkins: checkins
    };
    const r = await this.request('POST', '/api/migrate/import', body);
    if (r.code === 0) {
      return r.data as Record<string, number>;
    }
    return null;
  }
}
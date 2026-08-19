/**
 * 同步服务
 * 功能：
 * 1. 消费离线写队列，上报服务端
 * 2. 增量拉取服务端数据，合并到本地
 * 3. 配置同步（拉取/推送）
 * 4. 每日任务同步
 * 5. 打卡记录同步
 */
import { ApiClient } from './ApiClient';
import { OfflineWriteQueue, QueueItem } from './OfflineWriteQueue';
import { ArticleRepository } from '../repository/ArticleRepository';
import { Article } from '../model/Article';
import { DeletePayload, CheckinEnqueuePayload, ArticlePatchPayload, ArticlePatchBucket, ArticlePayload, ConfigPayload, DailyTaskPayload, DailyTaskItemPayload } from '../model/ApiTypes';
import { ConfigRepository } from '../repository/ConfigRepository';
import { Config } from '../model/Config';
import { DailyTaskRepository, DailyTaskItem, DailyTaskRecord } from '../repository/DailyTaskRepository';
import { CheckInRepository } from '../repository/CheckInRepository';
import { CheckInRecord } from '../model/CheckInRecord';

const CONSUME_INTERVAL: number = 3000; // 3秒轮询

export class SyncService {
  private static instance: SyncService;
  private api: ApiClient = ApiClient.getInstance();
  private queue: OfflineWriteQueue = OfflineWriteQueue.getInstance();
  private timerHandle: number = -1;
  private running: boolean = false;
  private statusCallback: ((msg: string) => void) | null = null;

  private constructor() {}

  static getInstance(): SyncService {
    if (!SyncService.instance) {
      SyncService.instance = new SyncService();
    }
    return SyncService.instance;
  }

  setStatusCallback(cb: (msg: string) => void): void {
    this.statusCallback = cb;
  }

  private notify(msg: string): void {
    if (this.statusCallback) {
      this.statusCallback(msg);
    }
  }

  // ---------- 写操作入队（用 clientId 作为同步标识） ----------
  enqueueArticleCreate(article: Article): void {
    const payload: ArticlePayload = this.articleToPayload(article);
    this.queue.enqueue('create', 'article', article.clientId, payload);
  }

  enqueueArticleUpdate(article: Article): void {
    const payload: ArticlePayload = this.articleToPayload(article);
    this.queue.enqueue('update', 'article', article.clientId, payload);
  }

  /**
   * 入队文章部分更新（使用PATCH）
   * 用于打卡完成率等局部字段更新
   */
  enqueueArticlePatch(clientId: string, payload: ArticlePatchPayload): void {
    const bucket: ArticlePatchBucket = { clientId: payload.clientId };
    if (payload.checkInDays !== undefined) {
      bucket.checkInDays = payload.checkInDays;
    }
    if (payload.completionRate !== undefined) {
      bucket.completionRate = payload.completionRate;
    }
    if (payload.lastModified !== undefined) {
      bucket.lastModified = payload.lastModified;
    }
    if (payload.isReading !== undefined) {
      bucket.isReading = payload.isReading;
    }
    if (payload.isRequired !== undefined) {
      bucket.isRequired = payload.isRequired;
    }
    if (payload.useIndependentCheckRate !== undefined) {
      bucket.useIndependentCheckRate = payload.useIndependentCheckRate;
    }
    if (payload.independentCheckRate !== undefined) {
      bucket.independentCheckRate = payload.independentCheckRate;
    }
    if (payload.isBold !== undefined) {
      bucket.isBold = payload.isBold;
    }
    if (payload.fontSize !== undefined) {
      bucket.fontSize = payload.fontSize;
    }
    if (payload.fontColor !== undefined) {
      bucket.fontColor = payload.fontColor;
    }
    if (payload.fontFamily !== undefined) {
      bucket.fontFamily = payload.fontFamily;
    }
    if (payload.isLongArticle !== undefined) {
      bucket.isLongArticle = payload.isLongArticle;
    }
    if (payload.iscontent !== undefined) {
      bucket.iscontent = payload.iscontent;
    }
    if (payload.requiredDays !== undefined) {
      bucket.requiredDays = payload.requiredDays;
    }
    this.queue.enqueue('patch', 'article', clientId, bucket);
  }

  enqueueArticleDelete(clientId: string): void {
    const payload: DeletePayload = { clientId: clientId };
    this.queue.enqueue('delete', 'article', clientId, payload);
  }

  enqueueCheckin(clientId: string, checkInDate: string, checkInTime: string): void {
    const payload: CheckinEnqueuePayload = {
      articleId: clientId, checkInDate: checkInDate, checkInTime: checkInTime,
      lastModified: new Date().toISOString()
    };
    this.queue.enqueue('create', 'checkin', clientId + '_' + checkInDate, payload);
  }

  private articleToPayload(article: Article): ArticlePayload {
    const p: ArticlePayload = {
      clientId: article.clientId,
      title: article.title,
      content: article.content,
      contentHtml: article.contentHtml || '',
      chineseChars: article.chineseChars,
      fontFamily: article.fontFamily || 'default',
      fontSize: article.fontSize,
      fontColor: article.fontColor || '#000000',
      isBold: article.isBold ? 1 : 0,
      isReading: article.isReading ? 1 : 0,
      isRequired: article.isRequired ? 1 : 0,
      requiredDays: article.requiredDays || '',
      useIndependentCheckRate: article.useIndependentCheckRate ? 1 : 0,
      independentCheckRate: article.independentCheckRate,
      createTime: article.createTime || '',
      isLongArticle: article.isLongArticle ? 1 : 0,
      checkInDays: article.checkInDays,
      completionRate: article.completionRate,
      imagewebp: article.imagewebp || '',
      iscontent: article.iscontent ? 1 : 0,
      lastModified: article.lastModified || new Date().toISOString()
    };
    return p;
  }

  // ---------- 消费队列 ----------
  start(): void {
    if (this.running) {
      return;
    }
    this.running = true;
    this.notify('同步服务已启动');
    this.scheduleConsume();
  }

  stop(): void {
    this.running = false;
    if (this.timerHandle !== -1) {
      clearInterval(this.timerHandle);
      this.timerHandle = -1;
    }
    this.notify('同步服务已停止');
  }

  private scheduleConsume(): void {
    this.timerHandle = setInterval(() => {
      this.consumeOnce();
    }, CONSUME_INTERVAL);
  }

  private async consumeOnce(): Promise<void> {
    if (!this.api.isLoggedIn()) {
      return;
    }
    const items: QueueItem[] = this.queue.getAll();
    if (items.length === 0) {
      return;
    }
    this.notify('同步中... 队列剩余 ' + items.length + ' 条');
    for (let i = 0; i < items.length; i++) {
      const item: QueueItem = items[i];
      try {
        const ok: boolean = await this.consumeOne(item);
        if (ok) {
          this.queue.remove(item);
        } else {
          this.queue.incrementRetry(item);
        }
      } catch (e) {
        console.error('SyncService consume error: ' + JSON.stringify(e));
        this.queue.incrementRetry(item);
      }
    }
    this.notify('同步完成，队列剩余 ' + this.queue.size() + ' 条');
  }

  private async consumeOne(item: QueueItem): Promise<boolean> {
    if (item.entity === 'article') {
      if (item.op === 'create' || item.op === 'update') {
        const payload = JSON.parse(item.payload) as ArticlePayload;
        return await this.api.pushArticle(payload);
      } else if (item.op === 'patch') {
        // 使用PATCH部分更新
        const payload = JSON.parse(item.payload) as Record<string, Object>;
        const toBool = (v: Object | undefined): boolean | undefined => {
          if (v === undefined || v === null) {
            return undefined;
          }
          if (typeof v === 'boolean') {
            return v;
          }
          if (typeof v === 'number') {
            return v !== 0;
          }
          return undefined;
        };
        const toNum = (v: Object | undefined): number | undefined => {
          if (v === undefined || v === null) {
            return undefined;
          }
          if (typeof v === 'number') {
            return v;
          }
          const n = Number(v);
          return isNaN(n) ? undefined : n;
        };
        const toStr = (v: Object | undefined): string | undefined => {
          if (v === undefined || v === null) {
            return undefined;
          }
          return String(v);
        };
        const patchPayload: ArticlePatchPayload = {
          clientId: toStr(payload['clientId']) || '',
          checkInDays: toNum(payload['checkInDays']),
          completionRate: toNum(payload['completionRate']),
          lastModified: toStr(payload['lastModified']),
          isReading: toBool(payload['isReading']),
          isRequired: toBool(payload['isRequired']),
          useIndependentCheckRate: toBool(payload['useIndependentCheckRate']),
          independentCheckRate: toNum(payload['independentCheckRate']),
          isBold: toBool(payload['isBold']),
          fontSize: toNum(payload['fontSize']),
          fontColor: toStr(payload['fontColor']),
          fontFamily: toStr(payload['fontFamily']),
          isLongArticle: toBool(payload['isLongArticle']),
          iscontent: toBool(payload['iscontent']),
          requiredDays: toStr(payload['requiredDays'])
        };
        return await this.api.patchArticle(item.clientId, patchPayload);
      } else if (item.op === 'delete') {
        return await this.api.deleteArticle(item.clientId);
      }
    } else if (item.entity === 'checkin') {
      const payload = JSON.parse(item.payload) as Record<string, Object>;
      const articleId = payload['articleId'] as string;
      const checkInDate = payload['checkInDate'] as string;
      const checkInTime = payload['checkInTime'] as string;
      return await this.api.pushCheckin(articleId, checkInDate, checkInTime);
    }
    return true;
  }

  // ---------- 增量拉取 ----------
  async pullArticles(): Promise<number> {
    if (!this.api.isLoggedIn()) {
      return 0;
    }
    const since: string = this.api.getArticleSince();
    const data = await this.api.fetchArticles(since);
    if (!data) {
      return 0;
    }
    const articles = (data['articles'] as Object[]) || [];
    const nextSince = (data['nextSince'] as string) || '';
    let merged: number = 0;
    if (articles.length > 0) {
      merged = await this.mergeArticles(articles);
    }
    if (nextSince) {
      await this.api.setArticleSince(nextSince);
    }
    this.notify('拉取 ' + articles.length + ' 篇增量文章');
    return merged;
  }

  private async mergeArticles(remoteArticles: Object[]): Promise<number> {
    const repo = ArticleRepository.getInstance();
    let merged: number = 0;
    for (let i = 0; i < remoteArticles.length; i++) {
      const ra = remoteArticles[i] as Record<string, Object>;
      const clientId = (ra['clientId'] as string) || '';
      if (!clientId) {
        continue;
      }
      const article: Article = this.payloadToArticle(ra, clientId);
      const ok = await repo.upsertFromSync(article);
      if (ok) {
        merged++;
      }
    }
    return merged;
  }

  private payloadToArticle(p: Record<string, Object>, clientId: string): Article {
    const a: Article = {
      id: 0,
      clientId: clientId,
      title: (p['title'] as string) || '',
      content: (p['content'] as string) || '',
      contentHtml: (p['contentHtml'] as string) || '',
      chineseChars: (p['chineseChars'] as number) || 0,
      fontFamily: (p['fontFamily'] as string) || 'default',
      fontSize: (p['fontSize'] as number) || 16,
      fontColor: (p['fontColor'] as string) || '#000000',
      isBold: (p['isBold'] as number) === 1,
      isReading: (p['isReading'] as number) === 1,
      isRequired: (p['isRequired'] as number) === 1,
      requiredDays: (p['requiredDays'] as string) || '',
      useIndependentCheckRate: (p['useIndependentCheckRate'] as number) === 1,
      independentCheckRate: (p['independentCheckRate'] as number) || 0,
      createTime: (p['createTime'] as string) || '',
      isLongArticle: (p['isLongArticle'] as number) === 1,
      checkInDays: (p['checkInDays'] as number) || 0,
      completionRate: (p['completionRate'] as number) || 0,
      imagewebp: (p['imagewebp'] as string) || '',
      iscontent: (p['iscontent'] as number) === 1,
      lastModified: (p['lastModified'] as string) || ''
    };
    return a;
  }

  // ---------- 打卡记录同步 ----------
  /**
   * 拉取远程打卡记录并合并到本地
   */
  async pullCheckins(): Promise<number> {
    if (!this.api.isLoggedIn()) {
      return 0;
    }
    const since: string = this.api.getCheckinSince();
    const data = await this.api.fetchCheckins(since);
    if (!data) {
      return 0;
    }
    const checkins = (data['checkins'] as Object[]) || [];
    const nextSince = (data['nextSince'] as string) || '';
    let merged: number = 0;

    if (checkins.length > 0) {
      const checkInRepo = CheckInRepository.getInstance();
      const articleRepo = ArticleRepository.getInstance();

      for (let i = 0; i < checkins.length; i++) {
        const rc = checkins[i] as Record<string, Object>;
        const remoteArticleId = (rc['articleId'] as string) || ''; // 这是clientId
        const checkInDate = (rc['checkInDate'] as string) || '';
        const checkInTime = (rc['checkInTime'] as string) || '';

        // 通过 clientId 查找本地文章
        const articles = await articleRepo.getAllArticles();
        const article = articles.find(a => a.clientId === remoteArticleId);
        if (article) {
          const record = new CheckInRecord();
          record.articleId = article.id;
          record.checkInDate = checkInDate;
          record.checkInTime = checkInTime;
          record.lastModified = (rc['lastModified'] as string) || '';
          await checkInRepo.insertCheckInRecord(record);
          merged++;
        }
      }
    }
    if (nextSince) {
      await this.api.setCheckinSince(nextSince);
    }
    this.notify('拉取 ' + checkins.length + ' 条打卡记录');
    return merged;
  }

  // ---------- 配置同步 ----------
  /**
   * 从服务端拉取配置并合并到本地
   * 注意：keepScreenOn 保留本地设置（不从服务端覆盖）
   */
  async pullConfig(): Promise<boolean> {
    if (!this.api.isLoggedIn()) {
      return false;
    }
    try {
      const remoteData = await this.api.fetchConfig();
      if (!remoteData) {
        return false;
      }
      const localConfig = await ConfigRepository.getInstance().getConfig();
      const remoteDailyMinutes = (remoteData['dailyMinutes'] as number) || 20;
      const remoteTargetCheckRate = (remoteData['targetCheckRate'] as number) || 30;
      const remoteReaderFontSize = (remoteData['readerFontSize'] as number) || 26;
      const remoteLastResetMonth = (remoteData['lastResetMonth'] as string) || '';

      // 合并：以服务端为准（除了 keepScreenOn 保持本地）
      localConfig.dailyMinutes = remoteDailyMinutes;
      localConfig.targetCheckRate = remoteTargetCheckRate;
      localConfig.readerFontSize = remoteReaderFontSize;
      if (remoteLastResetMonth) {
        localConfig.lastResetMonth = remoteLastResetMonth;
      }

      await ConfigRepository.getInstance().updateConfig(localConfig);
      this.notify('配置已同步');
      return true;
    } catch (e) {
      console.error('pullConfig error: ' + JSON.stringify(e));
      return false;
    }
  }

  /**
   * 推送本地配置到服务端（keepScreenOn 除外，不同步）
   */
  async pushConfig(): Promise<boolean> {
    if (!this.api.isLoggedIn()) {
      return false;
    }
    try {
      const config = await ConfigRepository.getInstance().getConfig();
      const payload: ConfigPayload = {
        dailyMinutes: config.dailyMinutes,
        targetCheckRate: config.targetCheckRate,
        readerFontSize: config.readerFontSize,
        lastResetMonth: config.lastResetMonth,
        lastSyncTime: new Date().toISOString()
      };
      const ok = await this.api.pushConfig(payload);
      if (ok) {
        this.notify('配置已推送');
      }
      return ok;
    } catch (e) {
      console.error('pushConfig error: ' + JSON.stringify(e));
      return false;
    }
  }

  // ---------- 每日任务同步 ----------
  /**
   * 从服务端获取今日任务（服务端自动生成如果不存在）
   * 新流程：服务端生成 → 客户端读取 → 合并到本地
   * @param force 是否强制重新生成
   */
  async fetchOrGenerateTodayTasks(force: boolean = false): Promise<boolean> {
    if (!this.api.isLoggedIn()) {
      return false;
    }
    try {
      // 先触发服务端生成（如果不存在则生成，存在则返回现有；force=true 时强制重新生成）
      const remoteData = await this.api.generateTodayTask(force);
      if (!remoteData) {
        return false;
      }
      return this.mergeRemoteTasksToLocal(remoteData);
    } catch (e) {
      console.error('fetchOrGenerateTodayTasks error: ' + JSON.stringify(e));
      return false;
    }
  }

  /**
   * 拉取服务端今日任务并与本地合并（兼容旧流程 + 自动生成）
   */
  async pullTodayTasks(): Promise<boolean> {
    if (!this.api.isLoggedIn()) {
      return false;
    }
    try {
      const remoteData = await this.api.fetchTodayTask();
      if (!remoteData) {
        return false;
      }
      return this.mergeRemoteTasksToLocal(remoteData);
    } catch (e) {
      console.error('pullTodayTasks error: ' + JSON.stringify(e));
      return false;
    }
  }

  /**
   * 将服务端返回的任务数据合并到本地数据库
   */
  private async mergeRemoteTasksToLocal(remoteData: Record<string, Object>): Promise<boolean> {
    const remoteItems = (remoteData['items'] as Object[]) || [];
    let taskDate = (remoteData['taskDate'] as string) || '';
    const remoteCount = (remoteData['count'] as number) || 0;

    // 修复 ISO 日期格式: "2026-08-18T16:00:00.000Z" → "2026-08-19"
    if (taskDate && taskDate.indexOf('T') >= 0) {
      // 截取日期部分或转换
      const parsed = new Date(taskDate);
      if (!isNaN(parsed.getTime())) {
        const y = parsed.getFullYear();
        const m = (parsed.getMonth() + 1).toString().padStart(2, '0');
        const d = parsed.getDate().toString().padStart(2, '0');
        taskDate = `${y}-${m}-${d}`;
      } else {
        taskDate = taskDate.substring(0, 10);
      }
    }

    if (remoteItems.length === 0 || remoteCount === 0) {
      return false;
    }

    const taskRepo = DailyTaskRepository.getInstance();
    const localRecord = await taskRepo.getTodayTask();
    const articleRepo = ArticleRepository.getInstance();
    const articles = await articleRepo.getAllArticles();

    // 转换服务端数据为本地格式
    const newItems: DailyTaskItem[] = [];
    for (let i = 0; i < remoteItems.length; i++) {
      const ri = remoteItems[i] as Record<string, Object>;
      const clientId = (ri['articleId'] as string) || '';
      const article = articles.find(a => a.clientId === clientId);
      const localArticleId = article ? article.id : 0;
      newItems.push({
        taskId: 0,
        articleId: localArticleId,
        articleTitle: (ri['articleTitle'] as string) || '',
        wordTarget: (ri['wordTarget'] as number) || 0,
        isCheckedIn: (ri['isCheckedIn'] as number) === 1,
        isLongArticle: (ri['isLongArticle'] as number) === 1,
        isRequired: (ri['isRequired'] as number) === 1,
        displayName: (ri['displayName'] as string) || ''
      });
    }

    // 如果本地没有任务，直接插入服务端任务
    if (!localRecord || localRecord.count === 0) {
      if (newItems.length > 0 && taskDate) {
        const newRecord: DailyTaskRecord = {
          date: taskDate,
          count: remoteCount,
          totalWords: (remoteData['totalWords'] as number) || 0,
          lastLongArticleIds: (remoteData['lastLongArticleIds'] as string) || '',
          items: newItems,
          createTime: (remoteData['createTime'] as string) || new Date().toISOString(),
          lastModified: (remoteData['lastModified'] as string) || new Date().toISOString()
        };
        await taskRepo.insertTask(newRecord);
        this.notify('今日任务已从云端同步');
        return true;
      }
      return false;
    }

    // 本地已有任务：比较是否需要更新（以服务端为准）
    // 检查任务项是否一致
    const localItemIds = localRecord.items.map(item => item.articleId);
    const remoteItemLocalIds = newItems.map(item => item.articleId);
    const needUpdate = localItemIds.length !== remoteItemLocalIds.length ||
      localItemIds.some(id => !remoteItemLocalIds.includes(id)) ||
      remoteItemLocalIds.some(id => !localItemIds.includes(id));

    if (needUpdate) {
      // 任务列表不同，用服务端的替换本地
      if (taskDate) {
        const newRecord: DailyTaskRecord = {
          id: localRecord.id,
          date: taskDate,
          count: remoteCount,
          totalWords: (remoteData['totalWords'] as number) || 0,
          lastLongArticleIds: (remoteData['lastLongArticleIds'] as string) || '',
          items: newItems,
          createTime: localRecord.createTime,
          lastModified: (remoteData['lastModified'] as string) || new Date().toISOString()
        };
        await taskRepo.updateTask(newRecord);
        this.notify('今日任务已从云端更新');
      }
    } else {
      // 任务项相同，仅同步打卡状态
      let localTaskId = localRecord.id || 0;
      for (let i = 0; i < newItems.length; i++) {
        const remoteItem = newItems[i];
        if (remoteItem.isCheckedIn && localTaskId > 0) {
          await taskRepo.markArticleChecked(localTaskId, remoteItem.articleId);
        }
      }
      this.notify('今日任务打卡状态已同步');
    }
    return true;
  }

  /**
   * 推送本地今日任务到服务端
   */
  async pushTodayTasks(): Promise<boolean> {
    if (!this.api.isLoggedIn()) {
      return false;
    }
    try {
      const taskRepo = DailyTaskRepository.getInstance();
      const record = await taskRepo.getTodayTask();
      if (!record || record.count === 0) {
        return false;
      }

      // 构建服务端载荷（articleId 使用 clientId）
      const articleRepo = ArticleRepository.getInstance();
      const allArticles = await articleRepo.getAllArticles();

      const itemsPayload: DailyTaskItemPayload[] = [];
      for (let i = 0; i < record.items.length; i++) {
        const item = record.items[i];
        const article = allArticles.find(a => a.id === item.articleId);
        const clientId = article ? article.clientId : '';
        const itemPayload: DailyTaskItemPayload = {
          articleId: clientId,
          articleTitle: item.articleTitle,
          wordTarget: item.wordTarget,
          isCheckedIn: item.isCheckedIn ? 1 : 0,
          isLongArticle: item.isLongArticle ? 1 : 0,
          isRequired: item.isRequired ? 1 : 0,
          displayName: item.displayName
        };
        itemsPayload.push(itemPayload);
      }

      const payload: DailyTaskPayload = {
        count: record.count,
        totalWords: record.totalWords,
        lastLongArticleIds: record.lastLongArticleIds,
        items: itemsPayload
      };

      const ok = await this.api.saveTodayTask(payload);
      if (ok) {
        this.notify('今日任务已推送');
      }
      return ok;
    } catch (e) {
      console.error('pushTodayTasks error: ' + JSON.stringify(e));
      return false;
    }
  }

  /**
   * 同步打卡完成率到服务端（使用PATCH部分更新）
   */
  async syncArticleCompletionRate(clientId: string, checkInDays: number, completionRate: number): Promise<boolean> {
    if (!this.api.isLoggedIn()) {
      // 未登录时入队
      const patchPayload: ArticlePatchPayload = {
        clientId: clientId,
        checkInDays: checkInDays,
        completionRate: completionRate,
        lastModified: new Date().toISOString()
      };
      this.enqueueArticlePatch(clientId, patchPayload);
      return true;
    }
    try {
      const patchPayload: ArticlePatchPayload = {
        clientId: clientId,
        checkInDays: checkInDays,
        completionRate: completionRate,
        lastModified: new Date().toISOString()
      };
      return await this.api.patchArticle(clientId, patchPayload);
    } catch (e) {
      console.error('syncArticleCompletionRate error: ' + JSON.stringify(e));
      // 失败时入队
      const patchPayload: ArticlePatchPayload = {
        clientId: clientId,
        checkInDays: checkInDays,
        completionRate: completionRate,
        lastModified: new Date().toISOString()
      };
      this.enqueueArticlePatch(clientId, patchPayload);
      return false;
    }
  }

  /**
   * 全量同步：文章 + 打卡 + 配置 + 任务
   */
  async fullSync(): Promise<void> {
    if (!this.api.isLoggedIn()) {
      return;
    }
    this.notify('开始全量同步...');

    // 1. 拉取文章
    const articleMerged = await this.pullArticles();
    this.notify('文章同步完成: ' + articleMerged + ' 篇');

    // 2. 拉取打卡记录
    const checkinMerged = await this.pullCheckins();
    this.notify('打卡同步完成: ' + checkinMerged + ' 条');

    // 3. 拉取配置
    await this.pullConfig();

    // 4. 拉取今日任务（以服务端为准，合并打卡状态）
    await this.pullTodayTasks();

    // 5. 推送本地配置（除 keepScreenOn）
    await this.pushConfig();

    // 注意：不再在 fullSync 中 pushTodayTasks，避免覆盖其他设备的打卡
    // pushTodayTasks 仅在任务首次创建时调用（SplashPage/Settings 中的创建操作）

    this.notify('全量同步完成');
  }
}
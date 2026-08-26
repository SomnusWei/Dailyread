import relationalStore from '@ohos.data.relationalStore';
import { Article } from '../model/Article';
import { Config } from '../model/Config';
import { ConfigRepository } from './ConfigRepository';
import { AppDatabase, TableNames } from '../database/AppDatabase';
import { OfflineWriteQueue } from '../service/OfflineWriteQueue';
import { CheckinEnqueuePayload, ArticlePatchPayload, ArticlePayload, DeletePayload } from '../model/ApiTypes';
import { SyncService } from '../service/SyncService';

export class ArticleRepository {
  private static instance: ArticleRepository | null = null;

  static getInstance(): ArticleRepository {
    if (!ArticleRepository.instance) {
      ArticleRepository.instance = new ArticleRepository();
    }
    return ArticleRepository.instance;
  }

  async getAllArticles(): Promise<Article[]> {
    const db = AppDatabase.getInstance().getDb();
    const articles: Article[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colClientId: number = result.getColumnIndex('clientId');
      const colTitle: number = result.getColumnIndex('title');
      const colContent: number = result.getColumnIndex('content');
      const colContentHtml: number = result.getColumnIndex('contentHtml');
      const colChineseChars: number = result.getColumnIndex('chineseChars');
      const colFontFamily: number = result.getColumnIndex('fontFamily');
      const colFontSize: number = result.getColumnIndex('fontSize');
      const colFontColor: number = result.getColumnIndex('fontColor');
      const colIsBold: number = result.getColumnIndex('isBold');
      const colIsReading: number = result.getColumnIndex('isReading');
      const colIsRequired: number = result.getColumnIndex('isRequired');
      const colRequiredDays: number = result.getColumnIndex('requiredDays');
      const colUseIndependentCheckRate: number = result.getColumnIndex('useIndependentCheckRate');
      const colIndependentCheckRate: number = result.getColumnIndex('independentCheckRate');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colIsLongArticle: number = result.getColumnIndex('isLongArticle');
      const colCheckInDays: number = result.getColumnIndex('checkInDays');
      const colCompletionRate: number = result.getColumnIndex('completionRate');
      const colImageWebp: number = result.getColumnIndex('imagewebp');
      const colAudioBase64: number = result.getColumnIndex('audiobase64');
      if (colAudioBase64 < 0) {
        console.error('getAllArticles: audiobase64 列不存在！数据库 v21 迁移可能失败');
      }
      const colIsContent: number = result.getColumnIndex('iscontent');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const article: Article = new Article();
        article.id = result.getLong(colId);
        article.clientId = colClientId >= 0 && !result.isColumnNull(colClientId) ? result.getString(colClientId) : '';
        article.title = result.getString(colTitle);
        article.content = result.getString(colContent);
        if (!result.isColumnNull(colContentHtml)) {
          article.contentHtml = result.getString(colContentHtml);
        } else {
          article.contentHtml = null;
        }
        article.chineseChars = result.getLong(colChineseChars);
        article.fontFamily = result.getString(colFontFamily);
        article.fontSize = result.getLong(colFontSize);
        article.fontColor = result.getString(colFontColor);
        article.isBold = result.getLong(colIsBold) === 1;
        article.isReading = result.getLong(colIsReading) === 1;
        article.isRequired = result.getLong(colIsRequired) === 1;
        article.requiredDays = result.getString(colRequiredDays);
        article.useIndependentCheckRate = result.getLong(colUseIndependentCheckRate) === 1;
        article.independentCheckRate = result.getDouble(colIndependentCheckRate);
        article.createTime = result.getString(colCreateTime);
        article.isLongArticle = result.getLong(colIsLongArticle) === 1;
        article.checkInDays = result.getLong(colCheckInDays);
        article.completionRate = Math.round(result.getDouble(colCompletionRate));
        article.imagewebp = colImageWebp >= 0 && !result.isColumnNull(colImageWebp) ? result.getString(colImageWebp) : '';
        // audiobase64 大字段单独 try-catch，避免单篇读取失败导致遍历中断、后续文章全部丢失
        try {
          article.audiobase64 = colAudioBase64 >= 0 && !result.isColumnNull(colAudioBase64) ? result.getString(colAudioBase64) : '';
        } catch (audioErr) {
          console.error('getAllArticles: audiobase64 读取失败 id=' + article.id + ': ' + JSON.stringify(audioErr));
          article.audiobase64 = '';
        }
        article.iscontent = colIsContent >= 0 && !result.isColumnNull(colIsContent) ? result.getLong(colIsContent) === 1 : true;
        article.lastModified = result.getString(colLastModified);
        articles.push(article);
      }
      result.close();
    } catch (e) {
      console.error('getAllArticles error:', JSON.stringify(e));
    }
    return articles;
  }

  async getArticleById(id: number): Promise<Article[]> {
    const db = AppDatabase.getInstance().getDb();
    const articles: Article[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      predicates.equalTo('id', id);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colClientId: number = result.getColumnIndex('clientId');
      const colTitle: number = result.getColumnIndex('title');
      const colContent: number = result.getColumnIndex('content');
      const colContentHtml: number = result.getColumnIndex('contentHtml');
      const colChineseChars: number = result.getColumnIndex('chineseChars');
      const colFontFamily: number = result.getColumnIndex('fontFamily');
      const colFontSize: number = result.getColumnIndex('fontSize');
      const colFontColor: number = result.getColumnIndex('fontColor');
      const colIsBold: number = result.getColumnIndex('isBold');
      const colIsReading: number = result.getColumnIndex('isReading');
      const colIsRequired: number = result.getColumnIndex('isRequired');
      const colRequiredDays: number = result.getColumnIndex('requiredDays');
      const colUseIndependentCheckRate: number = result.getColumnIndex('useIndependentCheckRate');
      const colIndependentCheckRate: number = result.getColumnIndex('independentCheckRate');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colIsLongArticle: number = result.getColumnIndex('isLongArticle');
      const colCheckInDays: number = result.getColumnIndex('checkInDays');
      const colCompletionRate: number = result.getColumnIndex('completionRate');
      const colImageWebp: number = result.getColumnIndex('imagewebp');
      const colAudioBase64: number = result.getColumnIndex('audiobase64');
      const colIsContent: number = result.getColumnIndex('iscontent');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const article: Article = new Article();
        article.id = result.getLong(colId);
        article.clientId = colClientId >= 0 && !result.isColumnNull(colClientId) ? result.getString(colClientId) : '';
        article.title = result.getString(colTitle);
        article.content = result.getString(colContent);
        if (!result.isColumnNull(colContentHtml)) {
          article.contentHtml = result.getString(colContentHtml);
        } else {
          article.contentHtml = null;
        }
        article.chineseChars = result.getLong(colChineseChars);
        article.fontFamily = result.getString(colFontFamily);
        article.fontSize = result.getLong(colFontSize);
        article.fontColor = result.getString(colFontColor);
        article.isBold = result.getLong(colIsBold) === 1;
        article.isReading = result.getLong(colIsReading) === 1;
        article.isRequired = result.getLong(colIsRequired) === 1;
        article.requiredDays = result.getString(colRequiredDays);
        article.useIndependentCheckRate = result.getLong(colUseIndependentCheckRate) === 1;
        article.independentCheckRate = result.getDouble(colIndependentCheckRate);
        article.createTime = result.getString(colCreateTime);
        article.isLongArticle = result.getLong(colIsLongArticle) === 1;
        article.checkInDays = result.getLong(colCheckInDays);
        article.completionRate = Math.round(result.getDouble(colCompletionRate));
        article.imagewebp = colImageWebp >= 0 && !result.isColumnNull(colImageWebp) ? result.getString(colImageWebp) : '';
        // audiobase64 大字段单独 try-catch，避免读取失败导致整篇文章丢失（音频为空不影响阅读）
        try {
          article.audiobase64 = colAudioBase64 >= 0 && !result.isColumnNull(colAudioBase64) ? result.getString(colAudioBase64) : '';
        } catch (audioErr) {
          console.error('getArticleById: audiobase64 读取失败 id=' + article.id + ': ' + JSON.stringify(audioErr));
          article.audiobase64 = '';
        }
        article.iscontent = colIsContent >= 0 && !result.isColumnNull(colIsContent) ? result.getLong(colIsContent) === 1 : true;
        article.lastModified = result.getString(colLastModified);
        articles.push(article);
      }
      result.close();
    } catch (e) {
      console.error('getArticleById error:', JSON.stringify(e));
    }
    return articles;
  }

  async getPausedArticles(): Promise<Article[]> {
    const db = AppDatabase.getInstance().getDb();
    const articles: Article[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      predicates.equalTo('isReading', 0);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colClientId: number = result.getColumnIndex('clientId');
      const colTitle: number = result.getColumnIndex('title');
      const colContent: number = result.getColumnIndex('content');
      const colContentHtml: number = result.getColumnIndex('contentHtml');
      const colChineseChars: number = result.getColumnIndex('chineseChars');
      const colFontFamily: number = result.getColumnIndex('fontFamily');
      const colFontSize: number = result.getColumnIndex('fontSize');
      const colFontColor: number = result.getColumnIndex('fontColor');
      const colIsBold: number = result.getColumnIndex('isBold');
      const colIsReading: number = result.getColumnIndex('isReading');
      const colIsRequired: number = result.getColumnIndex('isRequired');
      const colRequiredDays: number = result.getColumnIndex('requiredDays');
      const colUseIndependentCheckRate: number = result.getColumnIndex('useIndependentCheckRate');
      const colIndependentCheckRate: number = result.getColumnIndex('independentCheckRate');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colIsLongArticle: number = result.getColumnIndex('isLongArticle');
      const colCheckInDays: number = result.getColumnIndex('checkInDays');
      const colCompletionRate: number = result.getColumnIndex('completionRate');
      const colImageWebp: number = result.getColumnIndex('imagewebp');
      const colAudioBase64: number = result.getColumnIndex('audiobase64');
      const colIsContent: number = result.getColumnIndex('iscontent');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const article: Article = new Article();
        article.id = result.getLong(colId);
        article.clientId = colClientId >= 0 && !result.isColumnNull(colClientId) ? result.getString(colClientId) : '';
        article.title = result.getString(colTitle);
        article.content = result.getString(colContent);
        if (!result.isColumnNull(colContentHtml)) {
          article.contentHtml = result.getString(colContentHtml);
        } else {
          article.contentHtml = null;
        }
        article.chineseChars = result.getLong(colChineseChars);
        article.fontFamily = result.getString(colFontFamily);
        article.fontSize = result.getLong(colFontSize);
        article.fontColor = result.getString(colFontColor);
        article.isBold = result.getLong(colIsBold) === 1;
        article.isReading = result.getLong(colIsReading) === 1;
        article.isRequired = result.getLong(colIsRequired) === 1;
        article.requiredDays = result.getString(colRequiredDays);
        article.useIndependentCheckRate = result.getLong(colUseIndependentCheckRate) === 1;
        article.independentCheckRate = result.getDouble(colIndependentCheckRate);
        article.createTime = result.getString(colCreateTime);
        article.isLongArticle = result.getLong(colIsLongArticle) === 1;
        article.checkInDays = result.getLong(colCheckInDays);
        article.completionRate = Math.round(result.getDouble(colCompletionRate));
        article.imagewebp = colImageWebp >= 0 && !result.isColumnNull(colImageWebp) ? result.getString(colImageWebp) : '';
        article.audiobase64 = colAudioBase64 >= 0 && !result.isColumnNull(colAudioBase64) ? result.getString(colAudioBase64) : '';
        article.iscontent = colIsContent >= 0 && !result.isColumnNull(colIsContent) ? result.getLong(colIsContent) === 1 : true;
        article.lastModified = result.getString(colLastModified);
        articles.push(article);
      }
      result.close();
    } catch (e) {
      console.error('getPausedArticles error:', JSON.stringify(e));
    }
    return articles;
  }

  /**
   * 生成全局唯一的 clientId（hm 前缀 + 时间戳 + 随机数）
   */
  private generateClientId(): string {
    return 'hm' + Date.now().toString(36) + Math.floor(Math.random() * 1000000).toString(36);
  }

  async insertArticle(article: Article): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    // 确保 clientId 存在
    if (!article.clientId) {
      article.clientId = this.generateClientId();
    }
    const valueBucket: relationalStore.ValuesBucket = {
      clientId: article.clientId,
      title: article.title,
      content: article.content,
      contentHtml: article.contentHtml,
      chineseChars: article.chineseChars,
      fontFamily: article.fontFamily,
      fontSize: article.fontSize,
      fontColor: article.fontColor,
      isBold: article.isBold ? 1 : 0,
      isReading: article.isReading ? 1 : 0,
      isRequired: article.isRequired ? 1 : 0,
      requiredDays: article.requiredDays,
      useIndependentCheckRate: article.useIndependentCheckRate ? 1 : 0,
      independentCheckRate: article.independentCheckRate,
      createTime: article.createTime,
      isLongArticle: article.isLongArticle ? 1 : 0,
      checkInDays: article.checkInDays,
      completionRate: article.completionRate,
      imagewebp: article.imagewebp,
      audiobase64: article.audiobase64,
      iscontent: article.iscontent ? 1 : 0,
      lastModified: article.lastModified
    };
    // 如果 article.id > 0，显式指定 ID（用于云同步时保留远程原始 ID）
    if (article.id > 0) {
      valueBucket.id = article.id;
    }
    const rowId = await db.insert(TableNames.ARTICLES, valueBucket);
    if (rowId > 0) {
      article.id = rowId;
    }
    // 云同步钩子：入离线写队列（异步，不阻塞）— 用 clientId 作为同步标识
    try {
      OfflineWriteQueue.getInstance().enqueue('create', 'article', article.clientId, this.articleToPayload(article));
    } catch (e) {
      console.error('enqueue create: ' + JSON.stringify(e));
    }
    return rowId;
  }

  async updateArticle(article: Article): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      clientId: article.clientId,
      title: article.title,
      content: article.content,
      contentHtml: article.contentHtml,
      chineseChars: article.chineseChars,
      fontFamily: article.fontFamily,
      fontSize: article.fontSize,
      fontColor: article.fontColor,
      isBold: article.isBold ? 1 : 0,
      isReading: article.isReading ? 1 : 0,
      isRequired: article.isRequired ? 1 : 0,
      requiredDays: article.requiredDays,
      useIndependentCheckRate: article.useIndependentCheckRate ? 1 : 0,
      independentCheckRate: article.independentCheckRate,
      createTime: article.createTime,
      isLongArticle: article.isLongArticle ? 1 : 0,
      checkInDays: article.checkInDays,
      completionRate: article.completionRate,
      imagewebp: article.imagewebp,
      audiobase64: article.audiobase64,
      iscontent: article.iscontent ? 1 : 0,
      lastModified: article.lastModified
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    predicates.equalTo('id', article.id);
    const affected = await db.update(valueBucket, predicates);
    // 云同步钩子：入离线写队列（异步，不阻塞）— 用 clientId 作为同步标识
    try {
      OfflineWriteQueue.getInstance().enqueue('update', 'article', article.clientId, this.articleToPayload(article));
    } catch (e) {
      console.error('enqueue update: ' + JSON.stringify(e));
    }
    return affected;
  }

  /**
   * 将文章转为服务端 payload（用于离线队列）— clientId 为全局唯一标识
   */
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
      audiobase64: article.audiobase64 || '',
      iscontent: article.iscontent ? 1 : 0,
      lastModified: article.lastModified || new Date().toISOString()
    };
    return p;
  }

  /**
   * 云同步合并：按 clientId upsert（服务端拉取的增量合并到本地）
   * 返回 true 表示有变更
   */
  async upsertFromSync(article: Article): Promise<boolean> {
    const db = AppDatabase.getInstance().getDb();
    // 先查本地是否存在（按 clientId 匹配，而非本地 id）
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    predicates.equalTo('clientId', article.clientId);
    const result: relationalStore.ResultSet = await db.query(predicates);
    const exists: boolean = result.goToNextRow();
    result.close();
    const valueBucket: relationalStore.ValuesBucket = {
      title: article.title,
      content: article.content,
      contentHtml: article.contentHtml,
      chineseChars: article.chineseChars,
      fontFamily: article.fontFamily,
      fontSize: article.fontSize,
      fontColor: article.fontColor,
      isBold: article.isBold ? 1 : 0,
      isReading: article.isReading ? 1 : 0,
      isRequired: article.isRequired ? 1 : 0,
      requiredDays: article.requiredDays,
      useIndependentCheckRate: article.useIndependentCheckRate ? 1 : 0,
      independentCheckRate: article.independentCheckRate,
      createTime: article.createTime,
      isLongArticle: article.isLongArticle ? 1 : 0,
      checkInDays: article.checkInDays,
      completionRate: article.completionRate,
      imagewebp: article.imagewebp,
      audiobase64: article.audiobase64,
      iscontent: article.iscontent ? 1 : 0,
      lastModified: article.lastModified
    };
    if (exists) {
      // 更新（不入队列，避免循环同步）
      await db.update(valueBucket, predicates);
    } else {
      // 插入（新文章来自其他设备，clientId 已由服务端提供）
      valueBucket.clientId = article.clientId;
      await db.insert(TableNames.ARTICLES, valueBucket);
    }
    return true;
  }

  /**
   * 打卡后调用：打卡天数 +1，并按今日日期重新计算完成率
   * @returns 更新后的完成率（0-100）
   */
  async incrementCheckInDays(id: number): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    // 1. 先读出当前值 + clientId
    let currentDays: number = 0;
    let articleClientId: string = '';
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      predicates.equalTo('id', id);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colCheckInDays: number = result.getColumnIndex('checkInDays');
      const colClientId: number = result.getColumnIndex('clientId');
      if (result.goToNextRow()) {
        currentDays = result.getLong(colCheckInDays);
        articleClientId = colClientId >= 0 && !result.isColumnNull(colClientId) ? result.getString(colClientId) : '';
      }
      result.close();
    } catch (e) {
      console.error('读取打卡天数失败:', JSON.stringify(e));
    }

    const newDays: number = currentDays + 1;
    const today: Date = new Date();
    const maxDays: number = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
    const rate: number = Math.round((newDays / maxDays) * 100);

    // 2. 更新
    const valueBucket: relationalStore.ValuesBucket = {
      checkInDays: newDays,
      completionRate: rate,
      lastModified: new Date().toISOString()
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    predicates.equalTo('id', id);
    await db.update(valueBucket, predicates);
    // 3. 云同步钩子：仅入队打卡明细，由 Reader.handleCheckIn 统一调用服务端更新完成率
    try {
      const todayStr: string = today.getFullYear() + '-' +
        String(today.getMonth() + 1).padStart(2, '0') + '-' +
        String(today.getDate()).padStart(2, '0');
      const checkinPayload: CheckinEnqueuePayload = {
        articleId: articleClientId, checkInDate: todayStr, checkInTime: new Date().toISOString(),
        lastModified: new Date().toISOString()
      };
      OfflineWriteQueue.getInstance().enqueue('create', 'checkin',
        articleClientId + '_' + todayStr, checkinPayload);
      // 注意：不再在此处调用 syncArticleCompletionRate，
      // 因为 Reader.handleCheckIn 中的 checkinByArticle 会独占服务端更新
    } catch (e) {
      console.error('enqueue checkin: ' + JSON.stringify(e));
    }
    return rate;
  }

  /**
   * 更新文章的打卡天数和完成率（由服务端返回权威数据后调用）
   */
  async updateCheckInDaysAndRate(id: number, checkInDays: number, completionRate: number): Promise<void> {
    const db = AppDatabase.getInstance().getDb();
    try {
      const valueBucket: relationalStore.ValuesBucket = {
        checkInDays: checkInDays,
        completionRate: completionRate,
        lastModified: new Date().toISOString()
      };
      const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      predicates.equalTo('id', id);
      await db.update(valueBucket, predicates);
    } catch (e) {
      console.error('updateCheckInDaysAndRate error: ' + JSON.stringify(e));
    }
  }

  /**
   * 应用启动时调用：检查是否跨月（月份变化），
   * 如果跨月，则将所有文章的打卡天数与完成率重置为 0。
   * 月份标识格式：YYYY-MM
   */
  async resetCheckInDaysIfNeeded(): Promise<boolean> {
    const db = AppDatabase.getInstance().getDb();
    try {
      // 1. 读 config 记录的上次重置月份
      const config: Config = await ConfigRepository.getInstance().getConfig();
      const today: Date = new Date();
      const currentMonth: string = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}`;

      if (config.lastResetMonth === currentMonth) {
        return false;
      }

      // 2. 跨月，重置所有文章的打卡天数和完成率
      const valueBucket: relationalStore.ValuesBucket = {
        checkInDays: 0,
        completionRate: 0,
        lastModified: new Date().toISOString()
      };
      const allPredicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      allPredicates.notEqualTo('id', 0);
      await db.update(valueBucket, allPredicates);

      // 3. 更新 config 中保存的重置月份
      config.lastResetMonth = currentMonth;
      await ConfigRepository.getInstance().updateConfig(config);

      console.info(`跨月重置打卡天数：${config.lastResetMonth} -> ${currentMonth}`);
      return true;
    } catch (e) {
      console.error('跨月重置打卡天数失败:', JSON.stringify(e));
      return false;
    }
  }

  async deleteArticle(id: number): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    // 先查出 clientId（删除后无法再查）
    let articleClientId: string = '';
    try {
      const qPredicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      qPredicates.equalTo('id', id);
      const result: relationalStore.ResultSet = await db.query(qPredicates);
      const colClientId: number = result.getColumnIndex('clientId');
      if (result.goToNextRow()) {
        articleClientId = colClientId >= 0 && !result.isColumnNull(colClientId) ? result.getString(colClientId) : '';
      }
      result.close();
    } catch (e) {
      console.error('deleteArticle 查询 clientId 失败: ' + JSON.stringify(e));
    }
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    predicates.equalTo('id', id);
    const affected = await db.delete(predicates);
    // 云同步钩子：用 clientId 入离线写队列
    try {
      if (articleClientId) {
        const delPayload: DeletePayload = { clientId: articleClientId };
        OfflineWriteQueue.getInstance().enqueue('delete', 'article', articleClientId, delPayload);
      }
    } catch (e) {
      console.error('enqueue delete: ' + JSON.stringify(e));
    }
    return affected;
  }

  async deleteAllArticles(): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    return await db.delete(predicates);
  }
}

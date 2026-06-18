import relationalStore from '@ohos.data.relationalStore';
import { Article } from '../model/Article';
import { Config } from '../model/Config';
import { ConfigRepository } from './ConfigRepository';
import { AppDatabase, TableNames } from '../database/AppDatabase';

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
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const article: Article = new Article();
        article.id = result.getLong(colId);
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
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const article: Article = new Article();
        article.id = result.getLong(colId);
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
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const article: Article = new Article();
        article.id = result.getLong(colId);
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
        article.lastModified = result.getString(colLastModified);
        articles.push(article);
      }
      result.close();
    } catch (e) {
      console.error('getPausedArticles error:', JSON.stringify(e));
    }
    return articles;
  }

  async insertArticle(article: Article): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
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
      lastModified: article.lastModified
    };
    return await db.insert(TableNames.ARTICLES, valueBucket);
  }

  async updateArticle(article: Article): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
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
      lastModified: article.lastModified
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    predicates.equalTo('id', article.id);
    return await db.update(valueBucket, predicates);
  }

  /**
   * 打卡后调用：打卡天数 +1，并按今日日期重新计算完成率
   * @returns 更新后的完成率（0-100）
   */
  async incrementCheckInDays(id: number): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    // 1. 先读出当前值
    let currentDays: number = 0;
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
      predicates.equalTo('id', id);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colCheckInDays: number = result.getColumnIndex('checkInDays');
      if (result.goToNextRow()) {
        currentDays = result.getLong(colCheckInDays);
      }
      result.close();
    } catch (e) {
      console.error('读取打卡天数失败:', JSON.stringify(e));
    }

    const newDays: number = currentDays + 1;
    const today: Date = new Date();
    const currentDay: number = today.getDate();
    const rate: number = Math.round((newDays / currentDay) * 100);

    // 2. 更新
    const valueBucket: relationalStore.ValuesBucket = {
      checkInDays: newDays,
      completionRate: rate,
      lastModified: new Date().toISOString()
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    predicates.equalTo('id', id);
    await db.update(valueBucket, predicates);
    return rate;
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
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    predicates.equalTo('id', id);
    return await db.delete(predicates);
  }

  async deleteAllArticles(): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.ARTICLES);
    return await db.delete(predicates);
  }
}

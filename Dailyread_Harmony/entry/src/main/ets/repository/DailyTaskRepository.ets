import relationalStore from '@ohos.data.relationalStore';
import { AppDatabase, TableNames } from '../database/AppDatabase';

/**
 * 每日任务项接口 - 单篇文章的任务信息
 */
export interface DailyTaskItem {
  id?: number;
  taskId: number;
  articleId: number;
  articleTitle: string;
  wordTarget: number;
  isCheckedIn: boolean;
  isLongArticle: boolean;
  isRequired: boolean;
  displayName: string;
}

/**
 * 每日任务记录接口 - 一天的任务信息
 */
export interface DailyTaskRecord {
  id?: number;
  date: string;
  count: number;
  totalWords: number;
  lastLongArticleIds: string;
  items: DailyTaskItem[];
  createTime: string;
  lastModified: string;
}

export class DailyTaskRepository {
  private static instance: DailyTaskRepository | null = null;

  static getInstance(): DailyTaskRepository {
    if (!DailyTaskRepository.instance) {
      DailyTaskRepository.instance = new DailyTaskRepository();
    }
    return DailyTaskRepository.instance;
  }

  /**
   * 获取今日日期字符串（YYYY-MM-DD）
   */
  private getTodayString(): string {
    const today = new Date();
    const year = today.getFullYear();
    const month = (today.getMonth() + 1).toString().padStart(2, '0');
    const day = today.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /**
   * 安全获取数字列，列不存在或索引无效时返回 defaultValue
   */
  private safeGetLong(result: relationalStore.ResultSet, colName: string, defaultValue: number): number {
    try {
      const idx = result.getColumnIndex(colName);
      if (idx < 0) {
        return defaultValue;
      }
      return result.getLong(idx);
    } catch (e) {
      return defaultValue;
    }
  }

  /**
   * 安全获取字符串列
   */
  private safeGetString(result: relationalStore.ResultSet, colName: string, defaultValue: string): string {
    try {
      const idx = result.getColumnIndex(colName);
      if (idx < 0) {
        return defaultValue;
      }
      const val = result.getString(idx);
      return val || defaultValue;
    } catch (e) {
      return defaultValue;
    }
  }

  /**
   * 获取指定日期的任务记录
   * 注意：即使 items 查询失败，只要主记录 count>0 就返回，
   * 以防止 items 查询异常时被误认为"没有任务"而重新生成。
   */
  async getTaskByDate(date: string): Promise<DailyTaskRecord | null> {
    const db = AppDatabase.getInstance().getDb();
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASKS);
      predicates.equalTo('date', date);
      const result = await db.query(predicates);

      if (result.rowCount === 0) {
        result.close();
        return null;
      }

      result.goToFirstRow();
      const record: DailyTaskRecord = {
        id: this.safeGetLong(result, 'id', 0),
        date: this.safeGetString(result, 'date', date),
        count: this.safeGetLong(result, 'count', 0),
        totalWords: this.safeGetLong(result, 'totalWords', 0),
        lastLongArticleIds: this.safeGetString(result, 'lastLongArticleIds', ''),
        items: [],
        createTime: this.safeGetString(result, 'createTime', ''),
        lastModified: this.safeGetString(result, 'lastModified', '')
      };
      result.close();

      // 获取任务项（即使子查询失败，主记录仍然有效——count>0 代表有任务）
      if (record.id && record.id > 0) {
        try {
          record.items = await this.getTaskItems(record.id);
        } catch (itemsErr) {
          console.error('DailyTaskRepository.getTaskByDate: getTaskItems failed, continuing with empty items. err:', JSON.stringify(itemsErr));
          record.items = [];
        }
        // 若 items 查询为空但 count>0，说明子表查询异常——基于 count 做一个保守回补（空占位）
        // 保持 items 为空数组即可，getOrGenerateTodayTasks 依赖 count 而不是 items.length
      }

      return record;
    } catch (e) {
      console.error('DailyTaskRepository.getTaskByDate error:', JSON.stringify(e));
      return null;
    }
  }

  /**
   * 获取今日任务记录
   */
  async getTodayTask(): Promise<DailyTaskRecord | null> {
    return await this.getTaskByDate(this.getTodayString());
  }

  /**
   * 是否有今日任务
   */
  async hasTodayTask(): Promise<boolean> {
    const record = await this.getTodayTask();
    return record !== null && record.count > 0;
  }

  /**
   * 获取任务项列表
   */
  private async getTaskItems(taskId: number): Promise<DailyTaskItem[]> {
    const db = AppDatabase.getInstance().getDb();
    const items: DailyTaskItem[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASK_ITEMS);
      predicates.equalTo('taskId', taskId);
      const result = await db.query(predicates);

      while (result.goToNextRow()) {
        items.push({
          id: this.safeGetLong(result, 'id', 0),
          taskId: this.safeGetLong(result, 'taskId', taskId),
          articleId: this.safeGetLong(result, 'articleId', 0),
          articleTitle: this.safeGetString(result, 'articleTitle', ''),
          wordTarget: this.safeGetLong(result, 'wordTarget', 0),
          isCheckedIn: this.safeGetLong(result, 'isCheckedIn', 0) === 1,
          isLongArticle: this.safeGetLong(result, 'isLongArticle', 0) === 1,
          isRequired: this.safeGetLong(result, 'isRequired', 0) === 1,
          displayName: this.safeGetString(result, 'displayName', '')
        });
      }
      result.close();
    } catch (e) {
      console.error('DailyTaskRepository.getTaskItems error:', JSON.stringify(e));
    }
    return items;
  }

  /**
   * 插入新任务记录（包含任务项）
   */
  async insertTask(record: DailyTaskRecord): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    try {
      // 先插入主记录
      const mainBucket: relationalStore.ValuesBucket = {
        date: record.date,
        count: record.count,
        totalWords: record.totalWords,
        lastLongArticleIds: record.lastLongArticleIds,
        createTime: record.createTime || new Date().toISOString(),
        lastModified: new Date().toISOString()
      };

      const taskId = await db.insert(TableNames.DAILY_TASKS, mainBucket);

      // 插入任务项
      for (let i = 0; i < record.items.length; i++) {
        const item = record.items[i];
        const itemBucket: relationalStore.ValuesBucket = {
          taskId: taskId,
          articleId: item.articleId,
          articleTitle: item.articleTitle,
          wordTarget: item.wordTarget,
          isCheckedIn: item.isCheckedIn ? 1 : 0,
          isLongArticle: item.isLongArticle ? 1 : 0,
          isRequired: item.isRequired ? 1 : 0,
          displayName: item.displayName
        };
        await db.insert(TableNames.DAILY_TASK_ITEMS, itemBucket);
      }

      return taskId;
    } catch (e) {
      console.error('DailyTaskRepository.insertTask error:', JSON.stringify(e));
      throw new Error('DailyTaskRepository.insertTask error: ' + JSON.stringify(e));
    }
  }

  /**
   * 更新任务记录（先删除旧任务项，再插入新的）
   */
  async updateTask(record: DailyTaskRecord): Promise<void> {
    const db = AppDatabase.getInstance().getDb();
    if (!record.id) {
      return;
    }

    try {
      // 更新主记录
      const mainBucket: relationalStore.ValuesBucket = {
        count: record.count,
        totalWords: record.totalWords,
        lastLongArticleIds: record.lastLongArticleIds,
        lastModified: new Date().toISOString()
      };

      const predicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASKS);
      predicates.equalTo('id', record.id);
      await db.update(mainBucket, predicates);

      // 先删除该任务下的所有旧任务项
      const deletePredicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASK_ITEMS);
      deletePredicates.equalTo('taskId', record.id);
      await db.delete(deletePredicates);

      // 插入新的任务项
      for (let i = 0; i < record.items.length; i++) {
        const item = record.items[i];
        const itemBucket: relationalStore.ValuesBucket = {
          taskId: record.id,
          articleId: item.articleId,
          articleTitle: item.articleTitle,
          wordTarget: item.wordTarget,
          isCheckedIn: item.isCheckedIn ? 1 : 0,
          isLongArticle: item.isLongArticle ? 1 : 0,
          isRequired: item.isRequired ? 1 : 0,
          displayName: item.displayName
        };
        await db.insert(TableNames.DAILY_TASK_ITEMS, itemBucket);
      }
    } catch (e) {
      console.error('DailyTaskRepository.updateTask error:', JSON.stringify(e));
      throw new Error('DailyTaskRepository.updateTask error: ' + JSON.stringify(e));
    }
  }

  /**
   * 删除指定日期的任务记录
   */
  async deleteTaskByDate(date: string): Promise<void> {
    const db = AppDatabase.getInstance().getDb();
    try {
      // 获取任务ID
      const record = await this.getTaskByDate(date);
      if (record && record.id) {
        // 删除任务项
        const itemPredicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASK_ITEMS);
        itemPredicates.equalTo('taskId', record.id);
        await db.delete(itemPredicates);

        // 删除主记录
        const mainPredicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASKS);
        mainPredicates.equalTo('date', date);
        await db.delete(mainPredicates);
      }
    } catch (e) {
      console.error('DailyTaskRepository.deleteTaskByDate error:', JSON.stringify(e));
      throw new Error('DailyTaskRepository.deleteTaskByDate error: ' + JSON.stringify(e));
    }
  }

  /**
   * 标记文章已完成
   */
  async markArticleChecked(taskId: number, articleId: number): Promise<void> {
    const db = AppDatabase.getInstance().getDb();
    try {
      const bucket: relationalStore.ValuesBucket = {
        isCheckedIn: 1
      };
      const predicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASK_ITEMS);
      predicates.equalTo('taskId', taskId).equalTo('articleId', articleId);
      await db.update(bucket, predicates);

      // 更新主记录的最后修改时间
      const mainBucket: relationalStore.ValuesBucket = {
        lastModified: new Date().toISOString()
      };
      const mainPredicates = new relationalStore.RdbPredicates(TableNames.DAILY_TASKS);
      mainPredicates.equalTo('id', taskId);
      await db.update(mainBucket, mainPredicates);
    } catch (e) {
      console.error('DailyTaskRepository.markArticleChecked error:', JSON.stringify(e));
      throw new Error('DailyTaskRepository.markArticleChecked error: ' + JSON.stringify(e));
    }
  }

  /**
   * 获取昨天的长文章ID列表
   */
  async getYesterdayLongArticleIds(): Promise<number[]> {
    const today = new Date();
    today.setDate(today.getDate() - 1);
    const yesterdayStr = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`;

    const record = await this.getTaskByDate(yesterdayStr);
    if (record && record.lastLongArticleIds) {
      try {
        return JSON.parse(record.lastLongArticleIds);
      } catch (e) {
        return [];
      }
    }
    return [];
  }

  /**
   * 清空今日任务
   */
  async clearTodayTask(): Promise<void> {
    await this.deleteTaskByDate(this.getTodayString());
  }
}

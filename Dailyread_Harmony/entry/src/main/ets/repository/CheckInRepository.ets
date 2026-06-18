import relationalStore from '@ohos.data.relationalStore';
import { CheckInRecord } from '../model/CheckInRecord';
import { AppDatabase, TableNames } from '../database/AppDatabase';

export class CheckInRepository {
  private static instance: CheckInRepository | null = null;

  static getInstance(): CheckInRepository {
    if (!CheckInRepository.instance) {
      CheckInRepository.instance = new CheckInRepository();
    }
    return CheckInRepository.instance;
  }

  async getAllCheckInRecords(): Promise<CheckInRecord[]> {
    const db = AppDatabase.getInstance().getDb();
    const records: CheckInRecord[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.CHECKINS);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colArticleId: number = result.getColumnIndex('articleId');
      const colCheckInDate: number = result.getColumnIndex('checkInDate');
      const colCheckInTime: number = result.getColumnIndex('checkInTime');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const record: CheckInRecord = new CheckInRecord();
        record.id = result.getLong(colId);
        record.articleId = result.getLong(colArticleId);
        record.checkInDate = result.getString(colCheckInDate);
        record.checkInTime = result.getString(colCheckInTime);
        record.lastModified = result.getString(colLastModified);
        records.push(record);
      }
      result.close();
    } catch (e) {
      console.error('getAllCheckInRecords error:', JSON.stringify(e));
    }
    return records;
  }

  async insertCheckInRecord(record: CheckInRecord): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      articleId: record.articleId,
      checkInDate: record.checkInDate,
      checkInTime: record.checkInTime,
      lastModified: record.lastModified
    };
    return await db.insert(TableNames.CHECKINS, valueBucket);
  }

  async deleteAllCheckInRecords(): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.CHECKINS);
    return await db.delete(predicates);
  }

  /**
   * 查询指定日期下已打卡的文章 ID 集合
   * 用于：首页渲染时，即便 daily_task_items.isCheckedIn 仍为 0，
   * 只要 check_in_records 中存在该日记录，就视为已打卡
   */
  async getArticleIdsCheckedInOnDate(date: string): Promise<Set<number>> {
    const db = AppDatabase.getInstance().getDb();
    const ids: Set<number> = new Set<number>();
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.CHECKINS);
      predicates.equalTo('checkInDate', date);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colArticleId: number = result.getColumnIndex('articleId');
      while (result.goToNextRow()) {
        ids.add(result.getLong(colArticleId));
      }
      result.close();
    } catch (e) {
      console.error('getArticleIdsCheckedInOnDate error:', JSON.stringify(e));
    }
    return ids;
  }
}

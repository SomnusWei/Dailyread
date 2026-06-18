/**
 * 应用配置数据模型
 * 与安卓端Config实体保持完全一致
 */
export class Config {
  id: number = 1;
  dailyMinutes: number = 20;
  targetCheckRate: number = 30.0;
  keepScreenOn: boolean = false;
  autoSyncWebDav: boolean = false;
  autoSyncEnabled: boolean = false;
  webdavUrl: string = '';
  webdavUsername: string = '';
  webdavPassword: string = '';
  webdavRemotePath: string = '/DailyRead';
  lastSyncTime: string = '';
  yesterdayLongArticleIds: string = '';
  syncArticlesEnabled: boolean = true;
  syncConceptsEnabled: boolean = true;
  syncClinicalNotesEnabled: boolean = true;
  lastResetMonth: string = '';

  constructor() {
  }
}

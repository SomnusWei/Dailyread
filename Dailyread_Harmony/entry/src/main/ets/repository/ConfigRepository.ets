import relationalStore from '@ohos.data.relationalStore';
import { Config } from '../model/Config';
import { AppDatabase, TableNames } from '../database/AppDatabase';

export class ConfigRepository {
  private static instance: ConfigRepository | null = null;

  static getInstance(): ConfigRepository {
    if (!ConfigRepository.instance) {
      ConfigRepository.instance = new ConfigRepository();
    }
    return ConfigRepository.instance;
  }

  async getConfig(): Promise<Config> {
    const db = AppDatabase.getInstance().getDb();
    let config: Config = new Config();
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.CONFIG);
      predicates.equalTo('id', 1);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colDailyMinutes: number = result.getColumnIndex('dailyMinutes');
      const colTargetCheckRate: number = result.getColumnIndex('targetCheckRate');
      const colKeepScreenOn: number = result.getColumnIndex('keepScreenOn');
      const colAutoSyncWebDav: number = result.getColumnIndex('autoSyncWebDav');
      const colWebdavUrl: number = result.getColumnIndex('webdavUrl');
      const colWebdavUsername: number = result.getColumnIndex('webdavUsername');
      const colWebdavPassword: number = result.getColumnIndex('webdavPassword');
      const colLastSyncTime: number = result.getColumnIndex('lastSyncTime');
      const colYesterdayLongArticleIds: number = result.getColumnIndex('yesterdayLongArticleIds');
      const colAutoSyncEnabled: number = result.getColumnIndex('autoSyncEnabled');
      const colWebdavRemotePath: number = result.getColumnIndex('webdavRemotePath');
      const colSyncArticlesEnabled: number = result.getColumnIndex('syncArticlesEnabled');
      const colSyncConceptsEnabled: number = result.getColumnIndex('syncConceptsEnabled');
      const colSyncClinicalNotesEnabled: number = result.getColumnIndex('syncClinicalNotesEnabled');
      const colLastResetMonth: number = result.getColumnIndex('lastResetMonth');
      if (result.goToFirstRow()) {
        config.id = result.getLong(colId);
        config.dailyMinutes = result.getLong(colDailyMinutes);
        config.targetCheckRate = result.getDouble(colTargetCheckRate);
        config.keepScreenOn = result.getLong(colKeepScreenOn) === 1;
        config.autoSyncWebDav = result.getLong(colAutoSyncWebDav) === 1;
        config.webdavUrl = result.getString(colWebdavUrl);
        config.webdavUsername = result.getString(colWebdavUsername);
        config.webdavPassword = result.getString(colWebdavPassword);
        config.lastSyncTime = result.getString(colLastSyncTime);
        config.yesterdayLongArticleIds = result.getString(colYesterdayLongArticleIds);
        config.autoSyncEnabled = result.getLong(colAutoSyncEnabled) === 1;
        config.webdavRemotePath = result.getString(colWebdavRemotePath);
        config.syncArticlesEnabled = result.getLong(colSyncArticlesEnabled) === 1;
        config.syncConceptsEnabled = result.getLong(colSyncConceptsEnabled) === 1;
        config.syncClinicalNotesEnabled = result.getLong(colSyncClinicalNotesEnabled) === 1;
        config.lastResetMonth = result.getString(colLastResetMonth);
      }
      result.close();
    } catch (e) {
      console.error('getConfig error:', JSON.stringify(e));
    }
    return config;
  }

  async updateConfig(config: Config): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      dailyMinutes: config.dailyMinutes,
      targetCheckRate: config.targetCheckRate,
      keepScreenOn: config.keepScreenOn ? 1 : 0,
      autoSyncWebDav: config.autoSyncWebDav ? 1 : 0,
      webdavUrl: config.webdavUrl,
      webdavUsername: config.webdavUsername,
      webdavPassword: config.webdavPassword,
      lastSyncTime: config.lastSyncTime,
      yesterdayLongArticleIds: config.yesterdayLongArticleIds,
      autoSyncEnabled: config.autoSyncEnabled ? 1 : 0,
      webdavRemotePath: config.webdavRemotePath,
      syncArticlesEnabled: config.syncArticlesEnabled ? 1 : 0,
      syncConceptsEnabled: config.syncConceptsEnabled ? 1 : 0,
      syncClinicalNotesEnabled: config.syncClinicalNotesEnabled ? 1 : 0,
      lastResetMonth: config.lastResetMonth
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.CONFIG);
    predicates.equalTo('id', 1);
    const rows = await db.update(valueBucket, predicates);
    return rows;
  }
}

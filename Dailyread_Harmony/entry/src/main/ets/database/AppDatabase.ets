import relationalStore from '@ohos.data.relationalStore';
import { common } from '@kit.AbilityKit';

const DB_NAME = 'daily_read.db';
const DB_VERSION = 18;

const TABLE_ARTICLES = 'contents';
const TABLE_ACUPOINTS = 'acupoints';
const TABLE_CONCEPTS = 'concepts';
const TABLE_CLINICAL_NOTES = 'clinical_notes';
const TABLE_CHECKINS = 'content_checkins';
const TABLE_CONFIG = 'config';
const TABLE_DAILY_TASKS = 'daily_tasks';
const TABLE_DAILY_TASK_ITEMS = 'daily_task_items';

const SQL_CREATE_ARTICLES = `
  CREATE TABLE IF NOT EXISTS ${TABLE_ARTICLES} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    contentHtml TEXT,
    chineseChars INTEGER NOT NULL,
    fontFamily TEXT DEFAULT 'default',
    fontSize INTEGER DEFAULT 16,
    fontColor TEXT DEFAULT '#000000',
    isBold INTEGER DEFAULT 0,
    isReading INTEGER DEFAULT 1,
    isRequired INTEGER DEFAULT 0,
    requiredDays TEXT DEFAULT '',
    useIndependentCheckRate INTEGER DEFAULT 0,
    independentCheckRate REAL DEFAULT 0.0,
    createTime TEXT,
    isLongArticle INTEGER DEFAULT 0,
    checkInDays INTEGER DEFAULT 0,
    completionRate REAL DEFAULT 0,
    imagewebp TEXT DEFAULT '',
    lastModified TEXT DEFAULT ''
  )
`;

const SQL_CREATE_ACUPOINTS = `
  CREATE TABLE IF NOT EXISTS ${TABLE_ACUPOINTS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acupoint TEXT NOT NULL,
    meridian TEXT NOT NULL,
    acupointProperty TEXT DEFAULT '',
    location TEXT DEFAULT '',
    function TEXT DEFAULT '',
    indications TEXT DEFAULT '',
    anatomy TEXT DEFAULT '',
    operation TEXT DEFAULT '',
    contraindications TEXT DEFAULT '',
    locationImagePath TEXT,
    locationImageBase64 TEXT,
    note TEXT DEFAULT '',
    createTime TEXT,
    name TEXT DEFAULT '',
    pinyin TEXT DEFAULT '',
    functionDesc TEXT DEFAULT '',
    isLearned INTEGER DEFAULT 0,
    lastModified TEXT DEFAULT ''
  )
`;

const SQL_CREATE_CONCEPTS = `
  CREATE TABLE IF NOT EXISTS ${TABLE_CONCEPTS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT DEFAULT '',
    category TEXT DEFAULT '',
    subject TEXT DEFAULT '',
    chapter TEXT DEFAULT '',
    content TEXT DEFAULT '',
    isReading INTEGER DEFAULT 0,
    createTime TEXT DEFAULT '',
    lastModified TEXT DEFAULT ''
  )
`;

const SQL_CREATE_CLINICAL_NOTES = `
  CREATE TABLE IF NOT EXISTS ${TABLE_CLINICAL_NOTES} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT DEFAULT '',
    pathogenesis TEXT DEFAULT '',
    treatment TEXT DEFAULT '',
    prescription TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    isReading INTEGER DEFAULT 0,
    createTime TEXT DEFAULT '',
    lastModified TEXT DEFAULT ''
  )
`;

const SQL_CREATE_CHECKINS = `
  CREATE TABLE IF NOT EXISTS ${TABLE_CHECKINS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articleId INTEGER NOT NULL,
    checkInDate TEXT NOT NULL,
    checkInTime TEXT NOT NULL,
    lastModified TEXT DEFAULT '',
    UNIQUE(articleId, checkInDate)
  )
`;

const SQL_CREATE_CONFIG = `
  CREATE TABLE IF NOT EXISTS ${TABLE_CONFIG} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dailyMinutes INTEGER DEFAULT 20,
    targetCheckRate REAL DEFAULT 30,
    keepScreenOn INTEGER DEFAULT 0,
    autoSyncWebDav INTEGER DEFAULT 0,
    webdavUrl TEXT DEFAULT '',
    webdavUsername TEXT DEFAULT '',
    webdavPassword TEXT DEFAULT '',
    lastSyncTime TEXT DEFAULT '',
    yesterdayLongArticleIds TEXT DEFAULT '',
    autoSyncEnabled INTEGER DEFAULT 0,
    webdavRemotePath TEXT DEFAULT '/DailyRead',
    syncArticlesEnabled INTEGER DEFAULT 1,
    syncConceptsEnabled INTEGER DEFAULT 1,
    syncClinicalNotesEnabled INTEGER DEFAULT 1,
    lastResetMonth TEXT DEFAULT ''
  )
`;

const SQL_CREATE_DAILY_TASKS = `
  CREATE TABLE IF NOT EXISTS ${TABLE_DAILY_TASKS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    count INTEGER DEFAULT 0,
    totalWords INTEGER DEFAULT 0,
    lastLongArticleIds TEXT DEFAULT '',
    createTime TEXT DEFAULT '',
    lastModified TEXT DEFAULT ''
  )
`;

const SQL_CREATE_DAILY_TASK_ITEMS = `
  CREATE TABLE IF NOT EXISTS ${TABLE_DAILY_TASK_ITEMS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taskId INTEGER NOT NULL,
    articleId INTEGER NOT NULL,
    articleTitle TEXT NOT NULL,
    wordTarget INTEGER DEFAULT 0,
    isCheckedIn INTEGER DEFAULT 0,
    isLongArticle INTEGER DEFAULT 0,
    isRequired INTEGER DEFAULT 0,
    displayName TEXT DEFAULT '',
    FOREIGN KEY (taskId) REFERENCES ${TABLE_DAILY_TASKS}(id) ON DELETE CASCADE
  )
`;

export class TableNames {
  static readonly ARTICLES: string = TABLE_ARTICLES;
  static readonly ACUPOINTS: string = TABLE_ACUPOINTS;
  static readonly CONCEPTS: string = TABLE_CONCEPTS;
  static readonly CLINICAL_NOTES: string = TABLE_CLINICAL_NOTES;
  static readonly CHECKINS: string = TABLE_CHECKINS;
  static readonly CONFIG: string = TABLE_CONFIG;
  static readonly DAILY_TASKS: string = TABLE_DAILY_TASKS;
  static readonly DAILY_TASK_ITEMS: string = TABLE_DAILY_TASK_ITEMS;
}

export class AppDatabase {
  private static instance: AppDatabase | null = null;
  private db: relationalStore.RdbStore | null = null;

  static getInstance(): AppDatabase {
    if (!AppDatabase.instance) {
      AppDatabase.instance = new AppDatabase();
    }
    return AppDatabase.instance;
  }

  async init(context: common.Context): Promise<void> {
    if (this.db) {
      return;
    }

    const config: relationalStore.StoreConfig = {
      name: DB_NAME,
      securityLevel: relationalStore.SecurityLevel.S1,
      dataGroupId: ''
    };

    this.db = await relationalStore.getRdbStore(context, config);
    
    // 启用 WAL 模式并设置同步模式
    await this.db.executeSql('PRAGMA journal_mode=WAL;');
    await this.db.executeSql('PRAGMA synchronous=FULL;');
    
    await this.db.executeSql(SQL_CREATE_ARTICLES);
    await this.db.executeSql(SQL_CREATE_ACUPOINTS);
    await this.db.executeSql(SQL_CREATE_CONCEPTS);
    await this.db.executeSql(SQL_CREATE_CLINICAL_NOTES);
    await this.db.executeSql(SQL_CREATE_CHECKINS);
    await this.db.executeSql(SQL_CREATE_CONFIG);
    await this.db.executeSql(SQL_CREATE_DAILY_TASKS);
    await this.db.executeSql(SQL_CREATE_DAILY_TASK_ITEMS);

    // 数据库升级：v10 -> v11，给 articles 表加 completionRate 列
    try {
      await this.db.executeSql(`ALTER TABLE ${TABLE_ARTICLES} ADD COLUMN completionRate REAL DEFAULT 0`);
    } catch (e) {
      // 列已存在时会报错，忽略即可
    }

    // 数据库升级：v11 -> v12，给 articles 表加 checkInDays 列
    try {
      await this.db.executeSql(`ALTER TABLE ${TABLE_ARTICLES} ADD COLUMN checkInDays INTEGER DEFAULT 0`);
    } catch (e) {
      // 列已存在时会报错，忽略即可
    }

    // 数据库升级：v12 -> v13，重建 concepts 表（简化字段）- 仅在首次升级时执行
    // 注意：此段代码已完成历史升级，不应再执行 DROP TABLE 操作
    // 如需修改表结构，请添加新的升级逻辑而非重建表

    // 数据库升级：v13 -> v14，给 config 表加 lastResetMonth 列
    try {
      await this.db.executeSql(`ALTER TABLE ${TABLE_CONFIG} ADD COLUMN lastResetMonth TEXT DEFAULT ''`);
    } catch (e) {
      // 列已存在时会报错，忽略即可
    }

    // 数据库升级：v14 -> v15，添加每日任务表
    try {
      await this.db.executeSql(SQL_CREATE_DAILY_TASKS);
    } catch (e) {
      // 表已存在时会报错，忽略即可
    }
    try {
      await this.db.executeSql(SQL_CREATE_DAILY_TASK_ITEMS);
    } catch (e) {
      // 表已存在时会报错，忽略即可
    }

    // 数据库升级：v15 -> v16，给 concepts 表加 isReading 列
    try {
      await this.db.executeSql(`ALTER TABLE ${TABLE_CONCEPTS} ADD COLUMN isReading INTEGER DEFAULT 0`);
    } catch (e) {
      // 列已存在时会报错，忽略即可
    }

    // 数据库升级：v16 -> v17，给 articles 表加 imagewebp 列（文章图片，WebP base64）
    try {
      await this.db.executeSql(`ALTER TABLE ${TABLE_ARTICLES} ADD COLUMN imagewebp TEXT DEFAULT ''`);
    } catch (e) {
      // 列已存在时会报错，忽略即可
    }

    // 升级补丁：确保 daily_tasks 表所有必需列都存在
    const dailyTasksRequiredCols = [
      'id', 'date', 'count', 'totalWords', 'lastLongArticleIds', 'createTime', 'lastModified'
    ];
    for (let ci = 0; ci < dailyTasksRequiredCols.length; ci++) {
      const colName = dailyTasksRequiredCols[ci];
      try {
        // 尝试在该列上读取（空表也能解析列）
        const predicates = new relationalStore.RdbPredicates(TABLE_DAILY_TASKS);
        predicates.equalTo('id', -1);
        const testResult = await this.db.query(predicates, [colName]);
        testResult.close();
      } catch (e) {
        // 列不存在，尝试添加
        if (colName === 'date') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASKS} ADD COLUMN date TEXT NOT NULL DEFAULT ''`); } catch (ignored) {}
        } else if (colName === 'count') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASKS} ADD COLUMN count INTEGER DEFAULT 0`); } catch (ignored) {}
        } else if (colName === 'totalWords') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASKS} ADD COLUMN totalWords INTEGER DEFAULT 0`); } catch (ignored) {}
        } else if (colName === 'lastLongArticleIds') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASKS} ADD COLUMN lastLongArticleIds TEXT DEFAULT ''`); } catch (ignored) {}
        } else if (colName === 'createTime') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASKS} ADD COLUMN createTime TEXT DEFAULT ''`); } catch (ignored) {}
        } else if (colName === 'lastModified') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASKS} ADD COLUMN lastModified TEXT DEFAULT ''`); } catch (ignored) {}
        }
      }
    }

    // 升级补丁：确保 daily_task_items 表所有必需列都存在
    const dailyItemsRequiredCols = [
      'id', 'taskId', 'articleId', 'articleTitle', 'wordTarget',
      'isCheckedIn', 'isLongArticle', 'isRequired', 'displayName'
    ];
    for (let ci2 = 0; ci2 < dailyItemsRequiredCols.length; ci2++) {
      const colName2 = dailyItemsRequiredCols[ci2];
      try {
        const predicates2 = new relationalStore.RdbPredicates(TABLE_DAILY_TASK_ITEMS);
        predicates2.equalTo('id', -1);
        const testResult2 = await this.db.query(predicates2, [colName2]);
        testResult2.close();
      } catch (e) {
        if (colName2 === 'taskId') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN taskId INTEGER NOT NULL DEFAULT 0`); } catch (ignored) {}
        } else if (colName2 === 'articleId') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN articleId INTEGER NOT NULL DEFAULT 0`); } catch (ignored) {}
        } else if (colName2 === 'articleTitle') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN articleTitle TEXT NOT NULL DEFAULT ''`); } catch (ignored) {}
        } else if (colName2 === 'wordTarget') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN wordTarget INTEGER DEFAULT 0`); } catch (ignored) {}
        } else if (colName2 === 'isCheckedIn') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN isCheckedIn INTEGER DEFAULT 0`); } catch (ignored) {}
        } else if (colName2 === 'isLongArticle') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN isLongArticle INTEGER DEFAULT 0`); } catch (ignored) {}
        } else if (colName2 === 'isRequired') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN isRequired INTEGER DEFAULT 0`); } catch (ignored) {}
        } else if (colName2 === 'displayName') {
          try { await this.db.executeSql(`ALTER TABLE ${TABLE_DAILY_TASK_ITEMS} ADD COLUMN displayName TEXT DEFAULT ''`); } catch (ignored) {}
        }
      }
    }

    // 数据库升级：v17 -> v18，给 config 表加 syncClinicalNotesEnabled 列
    try {
      await this.db.executeSql(`ALTER TABLE ${TABLE_CONFIG} ADD COLUMN syncClinicalNotesEnabled INTEGER DEFAULT 1`);
    } catch (e) {
      // 列已存在时会报错，忽略即可
    }

    await this.ensureDefaultConfig();
  }

  private async ensureDefaultConfig(): Promise<void> {
    if (!this.db) {
      return;
    }
    const predicates = new relationalStore.RdbPredicates(TABLE_CONFIG);
    const result = await this.db.query(predicates);
    if (result.rowCount === 0) {
      const valueBucket: relationalStore.ValuesBucket = {
        id: 1,
        dailyMinutes: 20,
        targetCheckRate: 30,
        keepScreenOn: 0,
        autoSyncWebDav: 0,
        webdavUrl: '',
        webdavUsername: '',
        webdavPassword: '',
        lastSyncTime: '',
        yesterdayLongArticleIds: '',
        autoSyncEnabled: 0,
        webdavRemotePath: '/DailyRead',
        syncArticlesEnabled: 1,
        syncConceptsEnabled: 1,
        syncClinicalNotesEnabled: 1,
        lastResetMonth: ''
      };
      await this.db.insert(TABLE_CONFIG, valueBucket);
    }
    result.close();
  }

  getDb(): relationalStore.RdbStore {
    if (!this.db) {
      throw new Error('Database not initialized');
    }
    return this.db;
  }

  static get TABLES(): TableNames {
    return new TableNames();
  }
}

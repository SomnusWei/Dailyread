import { WebDavClient, WebDavResult } from './WebDavClient';
import { Config } from '../model/Config';
import { ArticleRepository } from '../repository/ArticleRepository';
import { ConceptRepository } from '../repository/ConceptRepository';
import { ClinicalNoteRepository } from '../repository/ClinicalNoteRepository';
import { Article } from '../model/Article';
import { Concept } from '../model/Concept';
import { ClinicalNote } from '../model/ClinicalNote';
import { AppDatabase } from '../database/AppDatabase';
import { common } from '@kit.AbilityKit';

export class SyncResult {
  success: boolean = false;
  errorMessage: string = '';
  downloadedArticles: number = 0;
  uploadedArticles: number = 0;
  downloadedConcepts: number = 0;
  uploadedConcepts: number = 0;
  downloadedClinicalNotes: number = 0;
  uploadedClinicalNotes: number = 0;
}

/** 与 Article 字段完全对齐 */
export class SyncArticleData {
  id: number = 0;
  title: string = '';
  content: string = '';
  contentHtml: string = '';
  chineseChars: number = 0;
  fontFamily: string = 'default';
  fontSize: number = 16;
  fontColor: string = '#000000';
  isBold: boolean = false;
  isReading: boolean = false;
  isRequired: boolean = false;
  requiredDays: string = '';
  useIndependentCheckRate: boolean = false;
  independentCheckRate: number = 0;
  isLongArticle: boolean = false;
  checkInDays: number = 0;
  completionRate: number = 0;
  imagewebp: string = '';
  createTime: string = '';
  lastModified: string = '';
}

/** 与 Concept 字段完全对齐 */
export class SyncConceptData {
  id: number = 0;
  title: string = '';
  category: string = '';
  subject: string = '';
  chapter: string = '';
  content: string = '';
  isReading: boolean = false;
  createTime: string = '';
  lastModified: string = '';
}

/** 与 ClinicalNote 字段完全对齐 */
export class SyncClinicalNoteData {
  id: number = 0;
  title: string = '';
  pathogenesis: string = '';
  treatment: string = '';
  prescription: string = '';
  notes: string = '';
  isReading: boolean = false;
  createTime: string = '';
  lastModified: string = '';
}

export class SyncPayload {
  version: number = 2;
  exportTime: string = '';
  dataType: string = 'daily_read_backup';
  articles: SyncArticleData[] = [];
  concepts: SyncConceptData[] = [];
  clinicalNotes: SyncClinicalNoteData[] = [];
}

/** 远程文件路径：相对于 webdav 根目录 */
const REMOTE_FILE_NAME: string = 'DailyRead/daily_read_backup_windows.json';

/** 坚果云服务器域名检测 */
function isJianguoyun(url: string): boolean {
  return url.toLowerCase().includes('jianguoyun') || url.toLowerCase().includes('nutstore');
}

export class WebDavSyncService {
  private static instance: WebDavSyncService;
  private webDavClient: WebDavClient = WebDavClient.getInstance();
  private context: common.Context | null = null;

  private constructor() {}

  public static getInstance(): WebDavSyncService {
    if (WebDavSyncService.instance === undefined) {
      WebDavSyncService.instance = new WebDavSyncService();
    }
    return WebDavSyncService.instance;
  }

  public init(context: common.Context): void {
    this.context = context;
  }

  private getServerUrl(config: Config): string {
    let url: string = config.webdavUrl;
    if (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }
    return url;
  }

  public async testConnection(config: Config): Promise<SyncResult> {
    const result: SyncResult = new SyncResult();
    try {
      const baseUrl: string = this.getServerUrl(config);
      // 先测试根目录（确保 WebDAV 能访问）
      const rootTest: WebDavResult<boolean> = await this.webDavClient.testConnection(
        baseUrl, config.webdavUsername, config.webdavPassword, '/DailyRead');
      if (rootTest.success) {
        result.success = true;
      } else {
        // 再试直接 GET 目标文件
        const fileTest: WebDavResult<string> = await this.webDavClient.downloadFile(
          baseUrl, config.webdavUsername, config.webdavPassword, '/' + REMOTE_FILE_NAME);
        if (fileTest.success) {
          result.success = true;
        } else {
          result.success = false;
          result.errorMessage = '连接失败：' + (fileTest.message || rootTest.message || '未知错误');
        }
      }
    } catch (e) {
      result.success = false;
      result.errorMessage = '连接异常: ' + JSON.stringify(e);
    }
    return result;
  }

  /**
   * 从远程下载 daily_read_backup_windows.json，并合并到本地数据库
   */
  public async syncFromRemote(config: Config): Promise<SyncResult> {
    const result: SyncResult = new SyncResult();
    try {
      const baseUrl: string = this.getServerUrl(config);
      
      // 坚果云特殊处理：确保路径格式正确
      let remoteFullPath: string = '/' + REMOTE_FILE_NAME;
      if (isJianguoyun(baseUrl)) {
        // 坚果云需要去掉开头的斜杠
        remoteFullPath = REMOTE_FILE_NAME;
        console.info('WebDAV syncFromRemote: 检测到坚果云，调整路径格式');
      }
      
      console.info('WebDAV syncFromRemote: target=' + baseUrl + remoteFullPath);
      const downloadResult: WebDavResult<string> = await this.webDavClient.downloadFile(
        baseUrl, config.webdavUsername, config.webdavPassword, remoteFullPath);

      if (!downloadResult.success) {
        // 尝试另一种路径格式（坚果云可能需要 /dav/DailyRead/... 或其他格式）
        console.info('WebDAV syncFromRemote: 首次下载失败，尝试备用路径');
        const altPath: string = baseUrl.includes('/dav') 
          ? '/' + REMOTE_FILE_NAME 
          : '/dav/' + REMOTE_FILE_NAME;
        const altResult: WebDavResult<string> = await this.webDavClient.downloadFile(
          baseUrl.replace('/dav', ''), config.webdavUsername, config.webdavPassword, altPath);
        
        if (!altResult.success) {
          result.success = false;
          result.errorMessage = '下载失败: ' + (downloadResult.message || altResult.message);
          return result;
        }
        downloadResult.data = altResult.data;
        downloadResult.success = true;
      }

      const content: string = downloadResult.data || '';
      if (content === '') {
        result.success = true;
        result.errorMessage = '远程文件为空或不存在（404），无可合并内容';
        console.warn('WebDAV syncFromRemote: 远程内容为空');
        return result;
      }

      console.info('WebDAV syncFromRemote: content length=' + content.length + ', head=' + (content.length > 300 ? content.substring(0, 300) : content));

      let payload: SyncPayload = new SyncPayload();
      try {
        // 尝试解析JSON
        let raw: Object;
        try {
          raw = JSON.parse(content) as Object;
          console.info('WebDAV syncFromRemote: JSON 解析成功，类型=' + typeof raw);
        } catch (e) {
          console.error('WebDAV syncFromRemote: JSON 解析失败，尝试处理可能的编码问题');
          // 尝试处理可能的编码问题
          try {
            const fixedContent: string = content.replace(/\\u0000/g, '').replace(/[\x00-\x1F]/g, '');
            raw = JSON.parse(fixedContent) as Object;
            console.info('WebDAV syncFromRemote: 修复后 JSON 解析成功');
          } catch (e2) {
            result.success = false;
            result.errorMessage = '解析远程 JSON 失败: ' + JSON.stringify(e2);
            console.error('WebDAV syncFromRemote: ' + result.errorMessage);
            return result;
          }
        }
        
        const rawRec: Record<string, Object> = raw as Record<string, Object>;
        const keys: string[] = Object.keys(rawRec);
        console.info('WebDAV syncFromRemote: 数据键数量=' + keys.length + ', 键名=' + keys.join(','));
        
        // 解析文章 - 尝试多种键名
        let articlesRaw = rawRec['articles'];
        if (!articlesRaw) articlesRaw = rawRec['article'];
        if (!articlesRaw) articlesRaw = rawRec['contents'];
        console.info('WebDAV syncFromRemote: articles 字段存在=' + (articlesRaw !== undefined) + ', 类型=' + typeof articlesRaw + ', 是否数组=' + Array.isArray(articlesRaw));
        
        if (articlesRaw && Array.isArray(articlesRaw)) {
          const arr: Object[] = articlesRaw as Object[];
          console.info('WebDAV syncFromRemote: articles 数组长度=' + arr.length);
          for (let i: number = 0; i < arr.length; i++) {
            const it: Record<string, Object> = arr[i] as Record<string, Object>;
            const a: SyncArticleData = new SyncArticleData();
            a.id = Number(it['id']) || 0;
            a.title = String(it['title'] || '');
            a.content = String(it['content'] || '');
            a.contentHtml = String(it['contentHtml'] || '');
            a.chineseChars = Number(it['chineseChars']) || 0;
            a.fontFamily = String(it['fontFamily'] || 'default');
            a.fontSize = Number(it['fontSize']) || 16;
            a.fontColor = String(it['fontColor'] || '#000000');
            a.isBold = Boolean(it['isBold']);
            a.isReading = Boolean(it['isReading']);
            a.isRequired = it['isRequired'] !== undefined ? Boolean(it['isRequired']) : false;
            a.requiredDays = String(it['requiredDays'] || '');
            a.useIndependentCheckRate = it['useIndependentCheckRate'] !== undefined ? Boolean(it['useIndependentCheckRate']) : false;
            a.independentCheckRate = Number(it['independentCheckRate']) || 0;
            a.isLongArticle = it['isLongArticle'] !== undefined ? Boolean(it['isLongArticle']) : false;
            a.checkInDays = Number(it['checkInDays']) || 0;
            a.completionRate = Number(it['completionRate']) || 0;
            a.imagewebp = String(it['imagewebp'] || '');
            a.createTime = String(it['createTime'] || '');
            a.lastModified = String(it['lastModified'] || '');
            payload.articles.push(a);
          }
        } else {
          console.warn('WebDAV syncFromRemote: articles 字段不存在或不是数组');
        }
        
        // 解析概念 - 尝试多种键名
        let conceptsRaw = rawRec['concepts'];
        if (!conceptsRaw) conceptsRaw = rawRec['concept'];
        console.info('WebDAV syncFromRemote: concepts 字段存在=' + (conceptsRaw !== undefined) + ', 类型=' + typeof conceptsRaw + ', 是否数组=' + Array.isArray(conceptsRaw));
        
        if (conceptsRaw && Array.isArray(conceptsRaw)) {
          const arr: Object[] = conceptsRaw as Object[];
          console.info('WebDAV syncFromRemote: concepts 数组长度=' + arr.length);
          for (let i: number = 0; i < arr.length; i++) {
            const it: Record<string, Object> = arr[i] as Record<string, Object>;
            const c: SyncConceptData = new SyncConceptData();
            c.id = Number(it['id']) || 0;
            c.title = String(it['title'] || '');
            c.category = String(it['category'] || '');
            c.subject = String(it['subject'] || '');
            c.chapter = String(it['chapter'] || '');
            c.content = String(it['content'] || '');
            c.isReading = Boolean(it['isReading'] || true);
            c.createTime = String(it['createTime'] || '');
            c.lastModified = String(it['lastModified'] || '');
            payload.concepts.push(c);
          }
        } else {
          console.warn('WebDAV syncFromRemote: concepts 字段不存在或不是数组');
        }

        // 解析临床笔记
        let notesRaw = rawRec['clinicalNotes'];
        if (!notesRaw) notesRaw = rawRec['clinical_notes'];
        if (!notesRaw) notesRaw = rawRec['notes'];
        console.info('WebDAV syncFromRemote: clinicalNotes 字段存在=' + (notesRaw !== undefined) + ', 类型=' + typeof notesRaw + ', 是否数组=' + Array.isArray(notesRaw));

        if (notesRaw && Array.isArray(notesRaw)) {
          const arr: Object[] = notesRaw as Object[];
          console.info('WebDAV syncFromRemote: clinicalNotes 数组长度=' + arr.length);
          for (let i: number = 0; i < arr.length; i++) {
            const it: Record<string, Object> = arr[i] as Record<string, Object>;
            const n: SyncClinicalNoteData = new SyncClinicalNoteData();
            n.id = Number(it['id']) || 0;
            n.title = String(it['title'] || '');
            n.pathogenesis = String(it['pathogenesis'] || '');
            n.treatment = String(it['treatment'] || '');
            n.prescription = String(it['prescription'] || '');
            n.notes = String(it['notes'] || '');
            n.isReading = it['isReading'] !== undefined ? Boolean(it['isReading']) : false;
            n.createTime = String(it['createTime'] || '');
            n.lastModified = String(it['lastModified'] || '');
            payload.clinicalNotes.push(n);
          }
        } else {
          console.warn('WebDAV syncFromRemote: clinicalNotes 字段不存在或不是数组');
        }

        payload.version = Number(rawRec['version']) || 2;
        payload.exportTime = String(rawRec['exportTime'] || '');
        payload.dataType = String(rawRec['dataType'] || 'daily_read_backup');
        console.info('WebDAV syncFromRemote: 解析完成 articles=' + payload.articles.length + ' concepts=' + payload.concepts.length + ' clinicalNotes=' + payload.clinicalNotes.length);
      } catch (parseError) {
        result.success = false;
        result.errorMessage = '解析远程 JSON 失败: ' + JSON.stringify(parseError);
        console.error('WebDAV syncFromRemote: ' + result.errorMessage);
        return result;
      }

      result.downloadedArticles = await this.mergeArticles(payload.articles);
      result.downloadedConcepts = await this.mergeConcepts(payload.concepts);
      result.downloadedClinicalNotes = await this.mergeClinicalNotes(payload.clinicalNotes);
      console.info('WebDAV syncFromRemote: mergedArticles=' + result.downloadedArticles + ' mergedConcepts=' + result.downloadedConcepts + ' mergedClinicalNotes=' + result.downloadedClinicalNotes);
      config.lastSyncTime = new Date().toISOString();
      result.success = true;
    } catch (e) {
      result.success = false;
      result.errorMessage = '同步失败: ' + JSON.stringify(e);
      console.error('WebDAV syncFromRemote error: ' + result.errorMessage);
    }
    return result;
  }

  /**
   * 把当前本地所有文章 + 概念打包成 daily_read_backup_windows.json 上传到远程
   */
  public async syncToRemote(config: Config): Promise<SyncResult> {
    const result: SyncResult = new SyncResult();
    try {
      const baseUrl: string = this.getServerUrl(config);
      const payload: SyncPayload = new SyncPayload();
      payload.exportTime = new Date().toISOString();

      if (config.syncArticlesEnabled) {
        const articles: Article[] = await ArticleRepository.getInstance().getAllArticles();
        for (let i: number = 0; i < articles.length; i++) {
          const a: Article = articles[i];
          const data: SyncArticleData = new SyncArticleData();
          data.id = a.id;
          data.title = a.title;
          data.content = a.content;
          data.contentHtml = a.contentHtml || '';
          data.chineseChars = a.chineseChars;
          data.fontFamily = a.fontFamily || 'default';
          data.fontSize = a.fontSize || 16;
          data.fontColor = a.fontColor || '#000000';
          data.isBold = a.isBold || false;
          data.isReading = a.isReading;
          data.isRequired = a.isRequired || false;
          data.requiredDays = a.requiredDays || '';
          data.useIndependentCheckRate = a.useIndependentCheckRate || false;
          data.independentCheckRate = a.independentCheckRate || 0;
          data.isLongArticle = a.isLongArticle || false;
          data.checkInDays = a.checkInDays || 0;
          data.completionRate = a.completionRate || 0;
          data.imagewebp = a.imagewebp || '';
          data.createTime = a.createTime || '';
          data.lastModified = a.lastModified || payload.exportTime;
          payload.articles.push(data);
        }
        result.uploadedArticles = articles.length;
      }

      if (config.syncConceptsEnabled) {
        const concepts: Concept[] = await ConceptRepository.getInstance().getAllConcepts();
        for (let i: number = 0; i < concepts.length; i++) {
          const c: Concept = concepts[i];
          const data: SyncConceptData = new SyncConceptData();
          data.id = c.id;
          data.title = c.title;
          data.category = c.category || '';
          data.subject = c.subject || '';
          data.chapter = c.chapter || '';
          data.content = c.content;
          data.isReading = c.isReading;
          data.createTime = c.createTime || '';
          data.lastModified = c.lastModified || payload.exportTime;
          payload.concepts.push(data);
        }
        result.uploadedConcepts = concepts.length;
      }

      if (config.syncClinicalNotesEnabled) {
        const notes: ClinicalNote[] = await ClinicalNoteRepository.getInstance().getAllNotes();
        for (let i: number = 0; i < notes.length; i++) {
          const cn: ClinicalNote = notes[i];
          const data: SyncClinicalNoteData = new SyncClinicalNoteData();
          data.id = cn.id;
          data.title = cn.title;
          data.pathogenesis = cn.pathogenesis || '';
          data.treatment = cn.treatment || '';
          data.prescription = cn.prescription || '';
          data.notes = cn.notes || '';
          data.isReading = cn.isReading;
          data.createTime = cn.createTime || '';
          data.lastModified = cn.lastModified || payload.exportTime;
          payload.clinicalNotes.push(data);
        }
        result.uploadedClinicalNotes = notes.length;
      }

      const jsonContent: string = JSON.stringify(payload);
      
      // 坚果云特殊处理：调整路径格式
      let remotePath: string = '/' + REMOTE_FILE_NAME;
      if (isJianguoyun(baseUrl)) {
        remotePath = REMOTE_FILE_NAME;
      }
      
      let uploadResult: WebDavResult<boolean> = await this.webDavClient.uploadFile(
        baseUrl, config.webdavUsername, config.webdavPassword, remotePath, jsonContent);

      if (!uploadResult.success) {
        // 尝试备用路径格式
        const altPath: string = baseUrl.includes('/dav') 
          ? '/' + REMOTE_FILE_NAME 
          : '/dav/' + REMOTE_FILE_NAME;
        uploadResult = await this.webDavClient.uploadFile(
          baseUrl.replace('/dav', ''), config.webdavUsername, config.webdavPassword, altPath, jsonContent);
        
        if (!uploadResult.success) {
          result.success = false;
          result.errorMessage = '上传失败: ' + uploadResult.message;
          return result;
        }
      }

      config.lastSyncTime = new Date().toISOString();
      result.success = true;
    } catch (e) {
      result.success = false;
      result.errorMessage = '上传失败: ' + JSON.stringify(e);
    }
    return result;
  }

  private async mergeArticles(remoteArticles: SyncArticleData[]): Promise<number> {
    let mergedCount: number = 0;
    try {
      const existingArticles: Article[] = await ArticleRepository.getInstance().getAllArticles();
      const existingTitles: Map<string, Article> = new Map<string, Article>();
      for (let i: number = 0; i < existingArticles.length; i++) {
        existingTitles.set(existingArticles[i].title, existingArticles[i]);
      }
      console.info('WebDAV mergeArticles: 本地已有 articles=' + existingArticles.length + ' 条');

      for (let i: number = 0; i < remoteArticles.length; i++) {
        const remote: SyncArticleData = remoteArticles[i];
        const existing: Article | undefined = existingTitles.get(remote.title);

        if (!existing) {
          const article: Article = new Article();
          // 注意：不设置 article.id，由数据库自增主键处理
          article.title = remote.title;
          article.content = remote.content;
          article.contentHtml = remote.contentHtml || '';
          article.chineseChars = remote.chineseChars;
          article.fontFamily = remote.fontFamily || 'default';
          article.fontSize = remote.fontSize || 16;
          article.fontColor = remote.fontColor || '#000000';
          article.isBold = remote.isBold || false;
          article.isReading = remote.isReading;
          article.isRequired = remote.isRequired || false;
          article.requiredDays = remote.requiredDays || '';
          article.useIndependentCheckRate = remote.useIndependentCheckRate || false;
          article.independentCheckRate = remote.independentCheckRate || 0;
          article.isLongArticle = remote.isLongArticle || false;
          article.checkInDays = remote.checkInDays || 0;
          article.completionRate = remote.completionRate || 0;
          article.imagewebp = remote.imagewebp || '';
          article.createTime = remote.createTime || remote.lastModified;
          article.lastModified = remote.lastModified || new Date().toISOString();
          await ArticleRepository.getInstance().insertArticle(article);
          mergedCount++;
        } else {
          if (!existing.lastModified || (remote.lastModified && remote.lastModified > existing.lastModified)) {
            existing.title = remote.title;
            existing.content = remote.content;
            existing.contentHtml = remote.contentHtml || '';
            existing.chineseChars = remote.chineseChars;
            existing.fontFamily = remote.fontFamily || 'default';
            existing.fontSize = remote.fontSize || 16;
            existing.fontColor = remote.fontColor || '#000000';
            existing.isBold = remote.isBold || false;
            existing.isReading = remote.isReading;
            existing.isRequired = remote.isRequired !== undefined ? remote.isRequired : existing.isRequired;
            existing.requiredDays = remote.requiredDays !== undefined ? (remote.requiredDays || '') : existing.requiredDays;
            existing.useIndependentCheckRate = remote.useIndependentCheckRate !== undefined ? remote.useIndependentCheckRate : existing.useIndependentCheckRate;
            existing.independentCheckRate = remote.independentCheckRate !== undefined ? remote.independentCheckRate : existing.independentCheckRate;
            existing.isLongArticle = remote.isLongArticle !== undefined ? remote.isLongArticle : existing.isLongArticle;
            existing.checkInDays = remote.checkInDays !== undefined ? remote.checkInDays : existing.checkInDays;
            existing.completionRate = remote.completionRate !== undefined ? remote.completionRate : existing.completionRate;
            existing.imagewebp = remote.imagewebp !== undefined ? remote.imagewebp : existing.imagewebp;
            existing.createTime = remote.createTime || existing.createTime;
            existing.lastModified = remote.lastModified || new Date().toISOString();
            await ArticleRepository.getInstance().updateArticle(existing);
            mergedCount++;
          }
        }
      }
    } catch (e) {
      console.error('WebDAV mergeArticles 失败: ' + JSON.stringify(e));
    }
    return mergedCount;
  }

  private async mergeConcepts(remoteConcepts: SyncConceptData[]): Promise<number> {
    let mergedCount: number = 0;
    try {
      const existingConcepts: Concept[] = await ConceptRepository.getInstance().getAllConcepts();
      const existingTitles: Map<string, Concept> = new Map<string, Concept>();
      for (let i: number = 0; i < existingConcepts.length; i++) {
        existingTitles.set(existingConcepts[i].title, existingConcepts[i]);
      }
      console.info('WebDAV mergeConcepts: 本地已有 concepts=' + existingConcepts.length + ' 条');

      for (let i: number = 0; i < remoteConcepts.length; i++) {
        const remote: SyncConceptData = remoteConcepts[i];
        const existing: Concept | undefined = existingTitles.get(remote.title);

        if (!existing) {
          const concept: Concept = new Concept();
          concept.title = remote.title;
          concept.category = remote.category;
          concept.subject = remote.subject;
          concept.chapter = remote.chapter;
          concept.content = remote.content;
          concept.isReading = Boolean(remote.isReading || true);
          concept.createTime = remote.createTime || remote.lastModified;
          concept.lastModified = remote.lastModified || new Date().toISOString();
          await ConceptRepository.getInstance().insertConcept(concept);
          mergedCount++;
        } else {
          if (!existing.lastModified || (remote.lastModified && remote.lastModified > existing.lastModified)) {
            existing.title = remote.title;
            existing.category = remote.category;
            existing.subject = remote.subject;
            existing.chapter = remote.chapter;
            existing.content = remote.content;
            existing.isReading = Boolean(remote.isReading || true);
            existing.lastModified = remote.lastModified || new Date().toISOString();
            await ConceptRepository.getInstance().updateConcept(existing);
            mergedCount++;
          }
        }
      }
      
      
    } catch (e) {
      console.error('WebDAV mergeConcepts 失败: ' + JSON.stringify(e));
    }
    return mergedCount;
  }

  private async mergeClinicalNotes(remoteNotes: SyncClinicalNoteData[]): Promise<number> {
    let mergedCount: number = 0;
    try {
      const existingNotes: ClinicalNote[] = await ClinicalNoteRepository.getInstance().getAllNotes();
      const existingTitles: Map<string, ClinicalNote> = new Map<string, ClinicalNote>();
      for (let i: number = 0; i < existingNotes.length; i++) {
        existingTitles.set(existingNotes[i].title, existingNotes[i]);
      }
      console.info('WebDAV mergeClinicalNotes: 本地已有 clinicalNotes=' + existingNotes.length + ' 条');

      for (let i: number = 0; i < remoteNotes.length; i++) {
        const remote: SyncClinicalNoteData = remoteNotes[i];
        const existing: ClinicalNote | undefined = existingTitles.get(remote.title);

        if (!existing) {
          const note: ClinicalNote = new ClinicalNote();
          note.title = remote.title;
          note.pathogenesis = remote.pathogenesis || '';
          note.treatment = remote.treatment || '';
          note.prescription = remote.prescription || '';
          note.notes = remote.notes || '';
          note.isReading = remote.isReading !== undefined ? remote.isReading : false;
          note.createTime = remote.createTime || remote.lastModified;
          note.lastModified = remote.lastModified || new Date().toISOString();
          await ClinicalNoteRepository.getInstance().insertNote(note);
          mergedCount++;
        } else {
          if (!existing.lastModified || (remote.lastModified && remote.lastModified > existing.lastModified)) {
            existing.title = remote.title;
            existing.pathogenesis = remote.pathogenesis !== undefined ? (remote.pathogenesis || '') : existing.pathogenesis;
            existing.treatment = remote.treatment !== undefined ? (remote.treatment || '') : existing.treatment;
            existing.prescription = remote.prescription !== undefined ? (remote.prescription || '') : existing.prescription;
            existing.notes = remote.notes !== undefined ? (remote.notes || '') : existing.notes;
            existing.isReading = remote.isReading !== undefined ? remote.isReading : existing.isReading;
            existing.createTime = remote.createTime || existing.createTime;
            existing.lastModified = remote.lastModified || new Date().toISOString();
            await ClinicalNoteRepository.getInstance().updateNote(existing);
            mergedCount++;
          }
        }
      }
    } catch (e) {
      console.error('WebDAV mergeClinicalNotes 失败: ' + JSON.stringify(e));
    }
    return mergedCount;
  }
}

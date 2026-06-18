import { Article } from '../model/Article';
import { Concept } from '../model/Concept';
import { ClinicalNote } from '../model/ClinicalNote';
import { ArticleRepository } from '../repository/ArticleRepository';
import { ConceptRepository } from '../repository/ConceptRepository';
import { ClinicalNoteRepository } from '../repository/ClinicalNoteRepository';

export class BackupData {
  version: number = 6;
  exportTime: string = '';
  dataType: string = 'daily_read_backup';
  articles: BackupArticleData[] = [];
  concepts: BackupConceptData[] = [];
  clinicalNotes: BackupClinicalNoteData[] = [];

  constructor() {
  }
}

export class BackupArticleData {
  id: number = 0;
  title: string = '';
  content: string = '';
  contentHtml: string = '';
  chineseChars: number = 0;
  fontFamily: string = 'default';
  fontSize: number = 16;
  fontColor: string = '#000000';
  isBold: boolean = false;
  isReading: boolean = true;
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

  constructor() {
  }
}

export class BackupConceptData {
  id: number = 0;
  title: string = '';
  category: string = '';
  subject: string = '';
  chapter: string = '';
  content: string = '';
  isReading: boolean = false;
  createTime: string = '';
  lastModified: string = '';

  constructor() {
  }
}

export class BackupClinicalNoteData {
  id: number = 0;
  title: string = '';
  pathogenesis: string = '';
  treatment: string = '';
  prescription: string = '';
  notes: string = '';
  isReading: boolean = false;
  createTime: string = '';
  lastModified: string = '';

  constructor() {
  }
}

export class ImportResult {
  success: boolean = false;
  errorMessage: string = '';
  importedArticles: number = 0;
  importedConcepts: number = 0;
  importedClinicalNotes: number = 0;

  constructor() {
  }
}

export class JsonFieldReader {
  private data: object;

  constructor(data: object) {
    this.data = data;
  }

  hasField(keys: string[]): boolean {
    const record: Record<string, object> = this.data as Record<string, object>;
    for (let i: number = 0; i < keys.length; i++) {
      if (record[keys[i]] !== undefined && record[keys[i]] !== null) {
        return true;
      }
    }
    return false;
  }

  private asString(keys: string[], defaultValue: string): string {
    const record: Record<string, string> = this.data as Record<string, string>;
    for (let i: number = 0; i < keys.length; i++) {
      const val: string = record[keys[i]];
      if (val !== undefined && val !== null) {
        return val;
      }
    }
    return defaultValue;
  }

  private asNumber(keys: string[], defaultValue: number): number {
    const record: Record<string, number> = this.data as Record<string, number>;
    for (let i: number = 0; i < keys.length; i++) {
      const val: number = record[keys[i]];
      if (val !== undefined && val !== null) {
        return val;
      }
    }
    return defaultValue;
  }

  private asBoolean(keys: string[], defaultValue: boolean): boolean {
    const record: Record<string, boolean> = this.data as Record<string, boolean>;
    for (let i: number = 0; i < keys.length; i++) {
      const val: boolean = record[keys[i]];
      if (val !== undefined && val !== null) {
        return val;
      }
    }
    return defaultValue;
  }

  getString(keys: string[], defaultValue: string): string {
    const record: Record<string, string> = this.data as Record<string, string>;
    for (let i: number = 0; i < keys.length; i++) {
      const val: string = record[keys[i]];
      if (val !== undefined && val !== null && val.length > 0) {
        return val;
      }
    }
    return defaultValue;
  }

  getNumber(keys: string[], defaultValue: number): number {
    const record: Record<string, number> = this.data as Record<string, number>;
    for (let i: number = 0; i < keys.length; i++) {
      const val: number = record[keys[i]];
      if (val !== undefined && val !== null) {
        return val;
      }
    }
    return defaultValue;
  }

  getBoolean(keys: string[], defaultValue: boolean): boolean {
    const record: Record<string, boolean> = this.data as Record<string, boolean>;
    for (let i: number = 0; i < keys.length; i++) {
      const val: boolean = record[keys[i]];
      if (val !== undefined && val !== null) {
        return val;
      }
    }
    return defaultValue;
  }

  getNullableString(keys: string[], defaultValue: string): string {
    const record: Record<string, string> = this.data as Record<string, string>;
    for (let i: number = 0; i < keys.length; i++) {
      const val: string = record[keys[i]];
      if (val === null) {
        return defaultValue;
      }
      if (val !== undefined && val.length > 0) {
        return val;
      }
    }
    return defaultValue;
  }
}

export class BackupService {
  private static instance: BackupService;

  private constructor() {
  }

  public static getInstance(): BackupService {
    if (BackupService.instance === undefined) {
      BackupService.instance = new BackupService();
    }
    return BackupService.instance;
  }

  public async exportToJSON(): Promise<string> {
    const backup: BackupData = new BackupData();
    backup.version = 6;
    backup.exportTime = new Date().toISOString();
    backup.dataType = 'daily_read_backup';

    const articles: Article[] = await ArticleRepository.getInstance().getAllArticles();
    for (let i: number = 0; i < articles.length; i++) {
      const a: Article = articles[i];
      const bd: BackupArticleData = new BackupArticleData();
      bd.id = a.id;
      bd.title = a.title;
      bd.content = a.content;
      bd.contentHtml = a.contentHtml || '';
      bd.chineseChars = a.chineseChars;
      bd.fontFamily = a.fontFamily;
      bd.fontSize = a.fontSize;
      bd.fontColor = a.fontColor;
      bd.isBold = a.isBold;
      bd.isReading = a.isReading;
      bd.isRequired = a.isRequired;
      bd.requiredDays = a.requiredDays || '';
      bd.useIndependentCheckRate = a.useIndependentCheckRate;
      bd.independentCheckRate = a.independentCheckRate;
      bd.isLongArticle = a.isLongArticle;
      bd.checkInDays = a.checkInDays;
      bd.completionRate = a.completionRate;
      bd.imagewebp = a.imagewebp;
      bd.createTime = a.createTime;
      bd.lastModified = a.lastModified || a.createTime;
      backup.articles.push(bd);
    }

    const concepts: Concept[] = await ConceptRepository.getInstance().getAllConcepts();
    for (let m: number = 0; m < concepts.length; m++) {
      const cp: Concept = concepts[m];
      const bd: BackupConceptData = new BackupConceptData();
      bd.id = cp.id;
      bd.title = cp.title;
      bd.category = cp.category;
      bd.subject = cp.subject;
      bd.chapter = cp.chapter;
      bd.content = cp.content;
      bd.isReading = cp.isReading;
      bd.createTime = cp.createTime;
      bd.lastModified = cp.lastModified || cp.createTime;
      backup.concepts.push(bd);
    }

    const notes: ClinicalNote[] = await ClinicalNoteRepository.getInstance().getAllNotes();
    for (let n: number = 0; n < notes.length; n++) {
      const cn: ClinicalNote = notes[n];
      const bd: BackupClinicalNoteData = new BackupClinicalNoteData();
      bd.id = cn.id;
      bd.title = cn.title;
      bd.pathogenesis = cn.pathogenesis;
      bd.treatment = cn.treatment;
      bd.prescription = cn.prescription;
      bd.notes = cn.notes;
      bd.isReading = cn.isReading;
      bd.createTime = cn.createTime;
      bd.lastModified = cn.lastModified || cn.createTime;
      backup.clinicalNotes.push(bd);
    }

    return JSON.stringify(backup);
  }

  public async importFromJSON(jsonStr: string, clearBeforeImport: boolean): Promise<ImportResult> {
    const result: ImportResult = new ImportResult();
    try {
      const parsed: Object = JSON.parse(jsonStr) as Object;
      if (parsed === null || parsed === undefined) {
        result.success = false;
        result.errorMessage = 'JSON 内容为空';
        return result;
      }

      if (clearBeforeImport) {
        try {
          await ArticleRepository.getInstance().deleteAllArticles();
        } catch (err1) {
          console.error('删除文章失败: ' + JSON.stringify(err1));
        }
        try {
          await ConceptRepository.getInstance().deleteAllConcepts();
        } catch (err2) {
          console.error('删除概念失败: ' + JSON.stringify(err2));
        }
        try {
          await ClinicalNoteRepository.getInstance().deleteAllNotes();
        } catch (err3) {
          console.error('删除临床笔记失败: ' + JSON.stringify(err3));
        }
      }

      const existingArticleTitles: Set<string> = new Set<string>();
      const existingConceptTitles: Set<string> = new Set<string>();
      const existingNoteTitles: Set<string> = new Set<string>();

      if (!clearBeforeImport) {
        const existingArticles: Article[] = await ArticleRepository.getInstance().getAllArticles();
        for (let i: number = 0; i < existingArticles.length; i++) {
          existingArticleTitles.add(existingArticles[i].title);
        }

        const existingConcepts: Concept[] = await ConceptRepository.getInstance().getAllConcepts();
        for (let j: number = 0; j < existingConcepts.length; j++) {
          existingConceptTitles.add(existingConcepts[j].title);
        }

        const existingNotes: ClinicalNote[] = await ClinicalNoteRepository.getInstance().getAllNotes();
        for (let k: number = 0; k < existingNotes.length; k++) {
          existingNoteTitles.add(existingNotes[k].title);
        }
      }

      const nowIso: string = new Date().toISOString();

      const isRootArray: boolean = Array.isArray(parsed);
      const rootArrayData: object[] = isRootArray ? (parsed as object[]) : [];

      const articleArray: object[] = this.extractArray(parsed,
        ['articles', 'articleList', 'contents', 'contentList']);
      if (articleArray.length > 0) {
        for (let i: number = 0; i < articleArray.length; i++) {
          const raw: object = articleArray[i];
          const reader: JsonFieldReader = new JsonFieldReader(raw);
          const title: string = reader.getString(['title', 'biaoTi', 'name'], '');
          const content: string = reader.getString(['content', 'neirong', 'body', 'text'], '');
          if (title.length === 0) {
            continue;
          }

          if (existingArticleTitles.has(title)) {
            console.log('文章已存在，跳过: ' + title);
            continue;
          }

          const article: Article = new Article();
          article.title = title;
          article.content = content;
          article.contentHtml = reader.getNullableString(['contentHtml', 'content_html', 'htmlContent'], '');
          article.chineseChars = reader.getNumber(['chineseChars', 'chinese_chars', 'charCount', 'char_count'], 0);
          if (article.chineseChars === 0) {
            article.chineseChars = this.countChineseChars(content);
          }
          article.fontFamily = reader.getString(['fontFamily', 'font_family'], 'default');
          article.fontSize = reader.getNumber(['fontSize', 'font_size'], 16);
          article.fontColor = reader.getString(['fontColor', 'font_color'], '#000000');
          article.isBold = reader.getBoolean(['isBold', 'is_bold'], false);
          article.isReading = reader.getBoolean(['isReading', 'is_reading', 'reading'], true);
          article.isRequired = reader.getBoolean(['isRequired', 'is_required', 'required'], false);
          article.requiredDays = reader.getString(['requiredDays', 'required_days'], '');
          article.useIndependentCheckRate = reader.getBoolean(['useIndependentCheckRate', 'use_independent_check_rate', 'independentRateEnabled'], false);
          article.independentCheckRate = reader.getNumber(['independentCheckRate', 'independent_check_rate'], 0);
          article.isLongArticle = reader.getBoolean(['isLongArticle', 'is_long_article', 'longArticle'], false);
          article.checkInDays = reader.getNumber(['checkInDays', 'check_in_days', 'checkinDays'], 0);
          article.completionRate = reader.getNumber(['completionRate', 'completion_rate'], 0);
          article.imagewebp = reader.getString(['imagewebp'], '');
          article.createTime = reader.getString(['createTime', 'create_time', 'createAt', 'createdAt'], nowIso);
          article.lastModified = reader.getString(['lastModified', 'last_modified', 'updateTime', 'update_time'], '');
          if (article.lastModified.length === 0) {
            article.lastModified = article.createTime;
          }
          if (article.createTime.length === 0) {
            article.createTime = nowIso;
            article.lastModified = nowIso;
          }
          try {
            await ArticleRepository.getInstance().insertArticle(article);
            result.importedArticles++;
          } catch (err) {
            console.error('导入文章失败: ' + JSON.stringify(err));
          }
        }
      }

      const conceptArray: object[] = this.extractArray(parsed,
        ['concepts', 'conceptList', 'gainian', 'gainianList']);

      // 只有当根 JSON 本身是数组（而非带 articles/concepts 键的对象）时才跳过概念导入
      if (isRootArray) {
        console.log('检测到纯数组JSON，跳过概念导入');
      } else if (conceptArray.length > 0) {
        for (let m: number = 0; m < conceptArray.length; m++) {
          const raw: object = conceptArray[m];
          const reader: JsonFieldReader = new JsonFieldReader(raw);
          const title: string = reader.getString(['title', 'biaoTi', 'name'], '');
          const content: string = reader.getString(['content', 'neirong', 'body', 'text'], '');
          if (title.length === 0) {
            continue;
          }

          if (existingConceptTitles.has(title)) {
            console.log('概念已存在，跳过: ' + title);
            continue;
          }

          const cp: Concept = new Concept();
          cp.title = title;
          cp.category = reader.getString(['category', 'fenlei', 'type'], '');
          cp.subject = reader.getString(['subject', 'xueke', 'subjectName'], '');
          cp.chapter = reader.getString(['chapter', 'zhangjie', 'subChapter', 'sub_chapter', 'subchapter'], '');
          cp.content = content;
          cp.isReading = reader.getBoolean(['isReading', 'is_reading', 'reading'], true);
          cp.createTime = reader.getString(['createTime', 'create_time', 'createAt'], nowIso);
          cp.lastModified = reader.getString(['lastModified', 'last_modified', 'updateTime'], '');
          if (cp.lastModified.length === 0) {
            cp.lastModified = cp.createTime;
          }
          if (cp.createTime.length === 0) {
            cp.createTime = nowIso;
            cp.lastModified = nowIso;
          }
          try {
            await ConceptRepository.getInstance().insertConcept(cp);
            result.importedConcepts++;
          } catch (err) {
            console.error('导入概念失败: ' + JSON.stringify(err));
          }
        }
      }

      const noteArray: object[] = this.extractArray(parsed,
        ['clinicalNotes', 'clinical_notes', 'notes', 'noteList', 'linchuang', 'linchuangbiji']);
      if (noteArray.length > 0) {
        for (let p: number = 0; p < noteArray.length; p++) {
          const raw: object = noteArray[p];
          const reader: JsonFieldReader = new JsonFieldReader(raw);
          const title: string = reader.getString(['title', 'biaoTi', 'name'], '');
          if (title.length === 0) {
            continue;
          }

          if (existingNoteTitles.has(title)) {
            console.log('临床笔记已存在，跳过: ' + title);
            continue;
          }

          const note: ClinicalNote = new ClinicalNote();
          note.title = title;
          note.pathogenesis = reader.getString(['pathogenesis', 'bingji', 'bingJi'], '');
          note.treatment = reader.getString(['treatment', 'zhifa', 'zhiFa'], '');
          note.prescription = reader.getString(['prescription', 'chufang', 'chuFang'], '');
          note.notes = reader.getString(['notes', 'note', 'beizhu', 'beiZhu', 'remark'], '');
          note.isReading = reader.getBoolean(['isReading', 'is_reading', 'reading'], false);
          note.createTime = reader.getString(['createTime', 'create_time', 'createAt'], nowIso);
          note.lastModified = reader.getString(['lastModified', 'last_modified', 'updateTime'], '');
          if (note.lastModified.length === 0) {
            note.lastModified = note.createTime;
          }
          if (note.createTime.length === 0) {
            note.createTime = nowIso;
            note.lastModified = nowIso;
          }
          try {
            await ClinicalNoteRepository.getInstance().insertNote(note);
            result.importedClinicalNotes++;
          } catch (err) {
            console.error('导入临床笔记失败: ' + JSON.stringify(err));
          }
        }
      }

      result.success = true;
    } catch (e) {
      result.success = false;
      result.errorMessage = '导入失败: ' + JSON.stringify(e);
      console.error('导入失败: ' + JSON.stringify(e));
    }
    return result;
  }

  private extractArray(parsed: Object, possibleKeys: string[]): object[] {
    const result: object[] = [];
    const record: Record<string, object> = parsed as Record<string, object>;
    for (let k: number = 0; k < possibleKeys.length; k++) {
      const val: object | undefined = record[possibleKeys[k]];
      if (val !== undefined && val !== null && Array.isArray(val)) {
        const arr: object[] = val as object[];
        for (let i: number = 0; i < arr.length; i++) {
          const item: object = arr[i];
          if (item !== null && item !== undefined) {
            result.push(item);
          }
        }
        return result;
      }
    }
    if (Array.isArray(parsed)) {
      const rootArr: object[] = parsed as object[];
      for (let j: number = 0; j < rootArr.length; j++) {
        const item: object = rootArr[j];
        if (item !== null && item !== undefined) {
          result.push(item);
        }
      }
    }
    return result;
  }

  private countChineseChars(content: string): number {
    let count: number = 0;
    for (let i: number = 0; i < content.length; i++) {
      const charCode: number = content.charCodeAt(i);
      if (charCode >= 0x4E00 && charCode <= 0x9FFF) {
        count++;
      }
    }
    return count;
  }
}

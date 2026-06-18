import relationalStore from '@ohos.data.relationalStore';
import { Concept } from '../model/Concept';
import { AppDatabase, TableNames } from '../database/AppDatabase';

export class ConceptRepository {
  private static instance: ConceptRepository | null = null;

  static getInstance(): ConceptRepository {
    if (!ConceptRepository.instance) {
      ConceptRepository.instance = new ConceptRepository();
    }
    return ConceptRepository.instance;
  }

  // 将 ResultSet 行数据映射为 Concept 对象
  private mapRowToConcept(result: relationalStore.ResultSet, colId: number, colTitle: number,
    colCategory: number, colSubject: number, colChapter: number, colContent: number,
    colIsReading: number, colCreateTime: number, colLastModified: number): Concept {
    const concept: Concept = new Concept();
    concept.id = result.getLong(colId);
    concept.title = result.getString(colTitle);
    concept.category = result.getString(colCategory);
    concept.subject = result.getString(colSubject);
    concept.chapter = result.getString(colChapter);
    concept.content = result.getString(colContent);
    concept.isReading = result.getLong(colIsReading) === 1;
    concept.createTime = result.getString(colCreateTime);
    concept.lastModified = result.getString(colLastModified);
    return concept;
  }

  async getAllConcepts(): Promise<Concept[]> {
    const db = AppDatabase.getInstance().getDb();
    const concepts: Concept[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.CONCEPTS);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colTitle: number = result.getColumnIndex('title');
      const colCategory: number = result.getColumnIndex('category');
      const colSubject: number = result.getColumnIndex('subject');
      const colChapter: number = result.getColumnIndex('chapter');
      const colContent: number = result.getColumnIndex('content');
      const colIsReading: number = result.getColumnIndex('isReading');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        concepts.push(this.mapRowToConcept(result, colId, colTitle, colCategory, colSubject,
          colChapter, colContent, colIsReading, colCreateTime, colLastModified));
      }
      result.close();
    } catch (e) {
      console.error('getAllConcepts error:', JSON.stringify(e));
    }
    return concepts;
  }

  // 获取阅读状态开启的概念
  async getReadingConcepts(): Promise<Concept[]> {
    const db = AppDatabase.getInstance().getDb();
    const concepts: Concept[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.CONCEPTS);
      predicates.equalTo('isReading', 1);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colTitle: number = result.getColumnIndex('title');
      const colCategory: number = result.getColumnIndex('category');
      const colSubject: number = result.getColumnIndex('subject');
      const colChapter: number = result.getColumnIndex('chapter');
      const colContent: number = result.getColumnIndex('content');
      const colIsReading: number = result.getColumnIndex('isReading');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        concepts.push(this.mapRowToConcept(result, colId, colTitle, colCategory, colSubject,
          colChapter, colContent, colIsReading, colCreateTime, colLastModified));
      }
      result.close();
    } catch (e) {
      console.error('getReadingConcepts error:', JSON.stringify(e));
    }
    return concepts;
  }

  async insertConcept(concept: Concept): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      title: concept.title,
      category: concept.category,
      subject: concept.subject,
      chapter: concept.chapter,
      content: concept.content,
      isReading: concept.isReading ? 1 : 0,
      createTime: concept.createTime,
      lastModified: concept.lastModified
    };
    return await db.insert(TableNames.CONCEPTS, valueBucket);
  }

  async insertBulk(concepts: Concept[]): Promise<void> {
    const db = AppDatabase.getInstance().getDb();
    try {
      for (let i: number = 0; i < concepts.length; i++) {
        const valueBucket: relationalStore.ValuesBucket = {
          title: concepts[i].title,
          category: concepts[i].category,
          subject: concepts[i].subject,
          chapter: concepts[i].chapter,
          content: concepts[i].content,
          isReading: concepts[i].isReading ? 1 : 0,
          createTime: concepts[i].createTime,
          lastModified: concepts[i].lastModified
        };
        await db.insert(TableNames.CONCEPTS, valueBucket);
      }
    } catch (e) {
      console.error('insertBulk error:', JSON.stringify(e));
    }
  }

  async updateConcept(concept: Concept): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      title: concept.title,
      category: concept.category,
      subject: concept.subject,
      chapter: concept.chapter,
      content: concept.content,
      isReading: concept.isReading ? 1 : 0,
      lastModified: concept.lastModified
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.CONCEPTS);
    predicates.equalTo('id', concept.id);
    return await db.update(valueBucket, predicates);
  }

  // 仅更新阅读状态
  async updateReadingStatus(conceptId: number, isReading: boolean): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      isReading: isReading ? 1 : 0,
      lastModified: new Date().toISOString()
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.CONCEPTS);
    predicates.equalTo('id', conceptId);
    return await db.update(valueBucket, predicates);
  }

  async deleteConcept(id: number): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.CONCEPTS);
    predicates.equalTo('id', id);
    return await db.delete(predicates);
  }

  async deleteAllConcepts(): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.CONCEPTS);
    return await db.delete(predicates);
  }
}

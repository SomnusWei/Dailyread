import relationalStore from '@ohos.data.relationalStore';
import { ClinicalNote } from '../model/ClinicalNote';
import { AppDatabase, TableNames } from '../database/AppDatabase';

export class ClinicalNoteRepository {
  private static instance: ClinicalNoteRepository | null = null;

  static getInstance(): ClinicalNoteRepository {
    if (!ClinicalNoteRepository.instance) {
      ClinicalNoteRepository.instance = new ClinicalNoteRepository();
    }
    return ClinicalNoteRepository.instance;
  }

  private mapRowToNote(result: relationalStore.ResultSet, colId: number,
    colTitle: number, colPathogenesis: number, colTreatment: number,
    colPrescription: number, colNotes: number, colIsReading: number,
    colCreateTime: number, colLastModified: number): ClinicalNote {
    const note: ClinicalNote = new ClinicalNote();
    note.id = result.getLong(colId);
    note.title = result.getString(colTitle);
    note.pathogenesis = result.getString(colPathogenesis);
    note.treatment = result.getString(colTreatment);
    note.prescription = result.getString(colPrescription);
    note.notes = result.getString(colNotes);
    note.isReading = result.getLong(colIsReading) === 1;
    note.createTime = result.getString(colCreateTime);
    note.lastModified = result.getString(colLastModified);
    return note;
  }

  async getAllNotes(): Promise<ClinicalNote[]> {
    const db = AppDatabase.getInstance().getDb();
    const notes: ClinicalNote[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.CLINICAL_NOTES);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colTitle: number = result.getColumnIndex('title');
      const colPathogenesis: number = result.getColumnIndex('pathogenesis');
      const colTreatment: number = result.getColumnIndex('treatment');
      const colPrescription: number = result.getColumnIndex('prescription');
      const colNotes: number = result.getColumnIndex('notes');
      const colIsReading: number = result.getColumnIndex('isReading');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        notes.push(this.mapRowToNote(result, colId, colTitle, colPathogenesis,
          colTreatment, colPrescription, colNotes, colIsReading, colCreateTime, colLastModified));
      }
      result.close();
    } catch (e) {
      console.error('getAllNotes error:', JSON.stringify(e));
    }
    return notes;
  }

  async getReadingNotes(): Promise<ClinicalNote[]> {
    const db = AppDatabase.getInstance().getDb();
    const notes: ClinicalNote[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.CLINICAL_NOTES);
      predicates.equalTo('isReading', 1);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colTitle: number = result.getColumnIndex('title');
      const colPathogenesis: number = result.getColumnIndex('pathogenesis');
      const colTreatment: number = result.getColumnIndex('treatment');
      const colPrescription: number = result.getColumnIndex('prescription');
      const colNotes: number = result.getColumnIndex('notes');
      const colIsReading: number = result.getColumnIndex('isReading');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        notes.push(this.mapRowToNote(result, colId, colTitle, colPathogenesis,
          colTreatment, colPrescription, colNotes, colIsReading, colCreateTime, colLastModified));
      }
      result.close();
    } catch (e) {
      console.error('getReadingNotes error:', JSON.stringify(e));
    }
    return notes;
  }

  async insertNote(note: ClinicalNote): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      title: note.title,
      pathogenesis: note.pathogenesis,
      treatment: note.treatment,
      prescription: note.prescription,
      notes: note.notes,
      isReading: note.isReading ? 1 : 0,
      createTime: note.createTime,
      lastModified: note.lastModified
    };
    return await db.insert(TableNames.CLINICAL_NOTES, valueBucket);
  }

  async updateNote(note: ClinicalNote): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      title: note.title,
      pathogenesis: note.pathogenesis,
      treatment: note.treatment,
      prescription: note.prescription,
      notes: note.notes,
      isReading: note.isReading ? 1 : 0,
      lastModified: note.lastModified
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.CLINICAL_NOTES);
    predicates.equalTo('id', note.id);
    return await db.update(valueBucket, predicates);
  }

  async updateReadingStatus(noteId: number, isReading: boolean): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      isReading: isReading ? 1 : 0,
      lastModified: new Date().toISOString()
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.CLINICAL_NOTES);
    predicates.equalTo('id', noteId);
    return await db.update(valueBucket, predicates);
  }

  async deleteNote(id: number): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.CLINICAL_NOTES);
    predicates.equalTo('id', id);
    return await db.delete(predicates);
  }

  async deleteAllNotes(): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.CLINICAL_NOTES);
    return await db.delete(predicates);
  }
}

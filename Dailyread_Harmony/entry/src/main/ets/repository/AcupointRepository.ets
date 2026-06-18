import relationalStore from '@ohos.data.relationalStore';
import { Acupoint } from '../model/Acupoint';
import { AppDatabase, TableNames } from '../database/AppDatabase';

export class AcupointRepository {
  private static instance: AcupointRepository | null = null;

  static getInstance(): AcupointRepository {
    if (!AcupointRepository.instance) {
      AcupointRepository.instance = new AcupointRepository();
    }
    return AcupointRepository.instance;
  }

  async getAllAcupoints(): Promise<Acupoint[]> {
    const db = AppDatabase.getInstance().getDb();
    const acupoints: Acupoint[] = [];
    try {
      const predicates = new relationalStore.RdbPredicates(TableNames.ACUPOINTS);
      const result: relationalStore.ResultSet = await db.query(predicates);
      const colId: number = result.getColumnIndex('id');
      const colAcupoint: number = result.getColumnIndex('acupoint');
      const colMeridian: number = result.getColumnIndex('meridian');
      const colAcupointProperty: number = result.getColumnIndex('acupointProperty');
      const colLocation: number = result.getColumnIndex('location');
      const colFunction: number = result.getColumnIndex('function');
      const colIndications: number = result.getColumnIndex('indications');
      const colAnatomy: number = result.getColumnIndex('anatomy');
      const colOperation: number = result.getColumnIndex('operation');
      const colContraindications: number = result.getColumnIndex('contraindications');
      const colLocationImagePath: number = result.getColumnIndex('locationImagePath');
      const colLocationImageBase64: number = result.getColumnIndex('locationImageBase64');
      const colNote: number = result.getColumnIndex('note');
      const colCreateTime: number = result.getColumnIndex('createTime');
      const colName: number = result.getColumnIndex('name');
      const colPinyin: number = result.getColumnIndex('pinyin');
      const colFunctionDesc: number = result.getColumnIndex('functionDesc');
      const colIsLearned: number = result.getColumnIndex('isLearned');
      const colLastModified: number = result.getColumnIndex('lastModified');
      while (result.goToNextRow()) {
        const acupoint: Acupoint = new Acupoint();
        acupoint.id = result.getLong(colId);
        acupoint.acupoint = result.getString(colAcupoint);
        acupoint.meridian = result.getString(colMeridian);
        acupoint.acupointProperty = result.getString(colAcupointProperty);
        acupoint.location = result.getString(colLocation);
        acupoint.function = result.getString(colFunction);
        acupoint.indications = result.getString(colIndications);
        acupoint.anatomy = result.getString(colAnatomy);
        acupoint.operation = result.getString(colOperation);
        acupoint.contraindications = result.getString(colContraindications);
        if (!result.isColumnNull(colLocationImagePath)) {
          acupoint.locationImagePath = result.getString(colLocationImagePath);
        } else {
          acupoint.locationImagePath = null;
        }
        if (!result.isColumnNull(colLocationImageBase64)) {
          acupoint.locationImageBase64 = result.getString(colLocationImageBase64);
        } else {
          acupoint.locationImageBase64 = null;
        }
        acupoint.note = result.getString(colNote);
        acupoint.createTime = result.getString(colCreateTime);
        acupoint.name = result.getString(colName);
        acupoint.pinyin = result.getString(colPinyin);
        acupoint.functionDesc = result.getString(colFunctionDesc);
        acupoint.isLearned = result.getLong(colIsLearned) === 1;
        acupoint.lastModified = result.getString(colLastModified);
        acupoints.push(acupoint);
      }
      result.close();
    } catch (e) {
      console.error('getAllAcupoints error:', JSON.stringify(e));
    }
    return acupoints;
  }

  async insertAcupoint(acupoint: Acupoint): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      acupoint: acupoint.acupoint,
      meridian: acupoint.meridian,
      acupointProperty: acupoint.acupointProperty,
      location: acupoint.location,
      function: acupoint.function,
      indications: acupoint.indications,
      anatomy: acupoint.anatomy,
      operation: acupoint.operation,
      contraindications: acupoint.contraindications,
      locationImagePath: acupoint.locationImagePath,
      locationImageBase64: acupoint.locationImageBase64,
      note: acupoint.note,
      createTime: acupoint.createTime,
      name: acupoint.name,
      pinyin: acupoint.pinyin,
      functionDesc: acupoint.functionDesc,
      isLearned: acupoint.isLearned ? 1 : 0,
      lastModified: acupoint.lastModified
    };
    return await db.insert(TableNames.ACUPOINTS, valueBucket);
  }

  async updateAcupoint(acupoint: Acupoint): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const valueBucket: relationalStore.ValuesBucket = {
      acupoint: acupoint.acupoint,
      meridian: acupoint.meridian,
      acupointProperty: acupoint.acupointProperty,
      location: acupoint.location,
      function: acupoint.function,
      indications: acupoint.indications,
      anatomy: acupoint.anatomy,
      operation: acupoint.operation,
      contraindications: acupoint.contraindications,
      locationImagePath: acupoint.locationImagePath,
      locationImageBase64: acupoint.locationImageBase64,
      note: acupoint.note,
      createTime: acupoint.createTime,
      name: acupoint.name,
      pinyin: acupoint.pinyin,
      functionDesc: acupoint.functionDesc,
      isLearned: acupoint.isLearned ? 1 : 0,
      lastModified: acupoint.lastModified
    };
    const predicates = new relationalStore.RdbPredicates(TableNames.ACUPOINTS);
    predicates.equalTo('id', acupoint.id);
    return await db.update(valueBucket, predicates);
  }

  async deleteAllAcupoints(): Promise<number> {
    const db = AppDatabase.getInstance().getDb();
    const predicates = new relationalStore.RdbPredicates(TableNames.ACUPOINTS);
    return await db.delete(predicates);
  }
}

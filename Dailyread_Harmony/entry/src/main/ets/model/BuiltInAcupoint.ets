// 内置穴位数据模型：字段与 rawfile/acupoints.json 保持一致
// 只保留用于界面显示的字段，不再依赖数据库
export class BuiltInAcupoint {
  acupoint: string = '';
  acupointProperty: string = '';
  anatomy: string = '';
  contraindications: string = '';
  function: string = '';
  indications: string = '';
  location: string = '';
  locationImageBase64: string = '';
  imageUri: string = '';
  meridian: string = '';
  note: string = '';
  operation: string = '';

  constructor() {
  }
}

export class Acupoint {
  id: number = 0;
  acupoint: string = '';
  meridian: string = '';
  acupointProperty: string = '';
  location: string = '';
  function: string = '';
  indications: string = '';
  anatomy: string = '';
  operation: string = '';
  contraindications: string = '';
  locationImagePath: string | null = null;
  locationImageBase64: string | null = null;
  note: string = '';
  createTime: string = '';
  name: string = '';
  pinyin: string = '';
  functionDesc: string = '';
  isLearned: boolean = false;
  lastModified: string = '';

  constructor() {
  }
}
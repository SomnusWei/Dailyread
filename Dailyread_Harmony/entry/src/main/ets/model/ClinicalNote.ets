export class ClinicalNote {
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

// 与 rawfile/acupoints.json 字段对应的原始数据模型
// 仅用于 JSON.parse 的结果类型声明
export class RawAcupoint {
  acupoint: string | null = null;
  acupointProperty: string | null = null;
  anatomy: string | null = null;
  contraindications: string | null = null;
  function: string | null = null;
  indications: string | null = null;
  location: string | null = null;
  locationImageBase64: string | null = null;
  meridian: string | null = null;
  note: string | null = null;
  operation: string | null = null;

  constructor() {
  }
}

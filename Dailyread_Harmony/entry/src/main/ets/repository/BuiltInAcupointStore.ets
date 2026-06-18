import { BuiltInAcupoint } from '../model/BuiltInAcupoint';
import { RawAcupoint } from '../model/RawAcupoint';
import { PickResult } from '../model/PickResult';
import promptAction from '@ohos.promptAction';
import util from '@ohos.util';

export class BuiltInAcupointStore {
  private static instance: BuiltInAcupointStore | null = null;
  private acupoints: BuiltInAcupoint[] = [];
  private loaded: boolean = false;

  static getInstance(): BuiltInAcupointStore {
    if (BuiltInAcupointStore.instance === null) {
      BuiltInAcupointStore.instance = new BuiltInAcupointStore();
    }
    return BuiltInAcupointStore.instance;
  }

  private static copyStringField(target: BuiltInAcupoint, fieldName: string, value: string): void {
    if (fieldName === 'acupoint') {
      target.acupoint = value;
    } else if (fieldName === 'acupointProperty') {
      target.acupointProperty = value;
    } else if (fieldName === 'anatomy') {
      target.anatomy = value;
    } else if (fieldName === 'contraindications') {
      target.contraindications = value;
    } else if (fieldName === 'function') {
      target.function = value;
    } else if (fieldName === 'indications') {
      target.indications = value;
    } else if (fieldName === 'location') {
      target.location = value;
    } else if (fieldName === 'locationImageBase64') {
      target.locationImageBase64 = value;
    } else if (fieldName === 'imageUri') {
      target.imageUri = value;
    } else if (fieldName === 'meridian') {
      target.meridian = value;
    } else if (fieldName === 'note') {
      target.note = value;
    } else if (fieldName === 'operation') {
      target.operation = value;
    }
  }

  private static safeString(val: string | null | undefined): string {
    if (val === null || val === undefined) {
      return '';
    }
    return val;
  }

  async load(context: Context): Promise<BuiltInAcupoint[]> {
    if (this.loaded) {
      return this.acupoints;
    }

    try {
      const resourceMgr = context.resourceManager;
      const uint8: Uint8Array = await resourceMgr.getRawFileContent('acupoints.json');
      const decoder: util.TextDecoder = new util.TextDecoder('utf-8');
      const text: string = decoder.decodeWithStream(uint8, { stream: false });
      const parsedArr: RawAcupoint[] = JSON.parse(text) as RawAcupoint[];

      if (Array.isArray(parsedArr)) {
        const result: BuiltInAcupoint[] = [];
        const len: number = parsedArr.length;
        for (let i: number = 0; i < len; i++) {
          const raw: RawAcupoint = parsedArr[i];
          const ac: BuiltInAcupoint = new BuiltInAcupoint();
          BuiltInAcupointStore.copyStringField(ac, 'acupoint', BuiltInAcupointStore.safeString(raw.acupoint));
          BuiltInAcupointStore.copyStringField(ac, 'acupointProperty', BuiltInAcupointStore.safeString(raw.acupointProperty));
          BuiltInAcupointStore.copyStringField(ac, 'anatomy', BuiltInAcupointStore.safeString(raw.anatomy));
          BuiltInAcupointStore.copyStringField(ac, 'contraindications', BuiltInAcupointStore.safeString(raw.contraindications));
          BuiltInAcupointStore.copyStringField(ac, 'function', BuiltInAcupointStore.safeString(raw.function));
          BuiltInAcupointStore.copyStringField(ac, 'indications', BuiltInAcupointStore.safeString(raw.indications));
          BuiltInAcupointStore.copyStringField(ac, 'location', BuiltInAcupointStore.safeString(raw.location));
          const base64: string = BuiltInAcupointStore.safeString(raw.locationImageBase64);
          BuiltInAcupointStore.copyStringField(ac, 'locationImageBase64', base64);
          if (base64.length > 10) {
            BuiltInAcupointStore.copyStringField(ac, 'imageUri', 'data:image/webp;base64,' + base64);
          } else {
            BuiltInAcupointStore.copyStringField(ac, 'imageUri', '');
          }
          BuiltInAcupointStore.copyStringField(ac, 'meridian', BuiltInAcupointStore.safeString(raw.meridian));
          BuiltInAcupointStore.copyStringField(ac, 'note', BuiltInAcupointStore.safeString(raw.note));
          BuiltInAcupointStore.copyStringField(ac, 'operation', BuiltInAcupointStore.safeString(raw.operation));
          result.push(ac);
        }
        this.acupoints = result;
        this.loaded = true;
        return result;
      }

      this.loaded = true;
      return this.acupoints;
    } catch (e) {
      console.error('内置穴位数据加载失败:', JSON.stringify(e));
      try {
        promptAction.showToast({ message: '穴位数据加载失败', duration: 2000 });
      } catch (err) {
        console.error('toast failed:', JSON.stringify(err));
      }
      this.loaded = true;
      return this.acupoints;
    }
  }

  getAcupoints(): BuiltInAcupoint[] {
    return this.acupoints;
  }

  pickRandom(lastIndex: number): PickResult {
    const total: number = this.acupoints.length;
    if (total === 0) {
      return new PickResult(null, -1);
    }
    if (total === 1) {
      return new PickResult(this.acupoints[0], 0);
    }
    let nextIdx: number = Math.floor(Math.random() * total);
    if (nextIdx === lastIndex) {
      nextIdx = (nextIdx + 1) % total;
    }
    return new PickResult(this.acupoints[nextIdx], nextIdx);
  }
}

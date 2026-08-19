import { BuiltInAcupoint } from './BuiltInAcupoint';

// pickRandom 的返回类型，避免使用对象字面量
export class PickResult {
  item: BuiltInAcupoint | null;
  index: number;

  constructor(item: BuiltInAcupoint | null, index: number) {
    this.item = item;
    this.index = index;
  }
}

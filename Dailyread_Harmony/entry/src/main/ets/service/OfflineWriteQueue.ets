/**
 * 离线写队列
 * 功能：暂存增改删操作，联网后异步上报服务端
 * 持久化：JSON 文件存储在应用沙箱目录
 */
import fs from '@ohos.file.fs';
import buffer from '@ohos.buffer';
import common from '@ohos.app.ability.common';

export type OpType = 'create' | 'update' | 'delete' | 'patch';
export type EntityType = 'article' | 'checkin' | 'daily_task' | 'config';

export interface QueueItem {
  op: OpType;
  entity: EntityType;
  clientId: string;
  payload: string;  // JSON 字符串
  createdAt: string;
  retry: number;
}

const QUEUE_FILE: string = 'offline_queue.json';
const MAX_RETRY: number = 3;

export class OfflineWriteQueue {
  private static instance: OfflineWriteQueue;
  private items: QueueItem[] = [];
  private queueFilePath: string = '';
  private loaded: boolean = false;

  private constructor() {}

  static getInstance(): OfflineWriteQueue {
    if (!OfflineWriteQueue.instance) {
      OfflineWriteQueue.instance = new OfflineWriteQueue();
    }
    return OfflineWriteQueue.instance;
  }

  /**
   * 初始化：确定文件路径并加载
   */
  init(context: common.Context): void {
    this.queueFilePath = context.filesDir + '/' + QUEUE_FILE;
    this.load();
    this.loaded = true;
  }

  private load(): void {
    try {
      if (fs.accessSync(this.queueFilePath)) {
        const file = fs.openSync(this.queueFilePath, fs.OpenMode.READ_ONLY);
        const stat = fs.statSync(file.fd);
        const buf = new ArrayBuffer(stat.size);
        fs.readSync(file.fd, buf);
        fs.closeSync(file);
        const str = buffer.from(new Uint8Array(buf)).toString('utf-8');
        this.items = JSON.parse(str) as QueueItem[];
      }
    } catch (e) {
      console.warn('OfflineWriteQueue load: ' + JSON.stringify(e));
      this.items = [];
    }
  }

  private persist(): void {
    try {
      const str = JSON.stringify(this.items);
      const buf = buffer.from(str, 'utf-8');
      const file = fs.openSync(this.queueFilePath, fs.OpenMode.CREATE | fs.OpenMode.WRITE_ONLY | fs.OpenMode.TRUNC);
      fs.writeSync(file.fd, buf.buffer);
      fs.closeSync(file);
    } catch (e) {
      console.error('OfflineWriteQueue persist: ' + JSON.stringify(e));
    }
  }

  enqueue(op: OpType, entity: EntityType, clientId: string, payload: object): void {
    const item: QueueItem = {
      op: op,
      entity: entity,
      clientId: clientId,
      payload: JSON.stringify(payload),
      createdAt: new Date().toISOString(),
      retry: 0
    };
    this.items.push(item);
    this.persist();
  }

  getAll(): QueueItem[] {
    return this.items;
  }

  remove(item: QueueItem): void {
    const idx = this.items.indexOf(item);
    if (idx >= 0) {
      this.items.splice(idx, 1);
      this.persist();
    }
  }

  size(): number {
    return this.items.length;
  }

  incrementRetry(item: QueueItem): boolean {
    item.retry = item.retry + 1;
    if (item.retry >= MAX_RETRY) {
      this.remove(item);
      return false;
    }
    this.persist();
    return true;
  }
}

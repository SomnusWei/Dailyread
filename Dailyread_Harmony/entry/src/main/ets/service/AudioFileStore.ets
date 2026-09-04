/**
 * 大音频文件存储
 * 背景：鸿蒙 RDB 对单字段超过约 2MB 的文本写入会失效（insert 返回 rowId 但行不落库），
 *      导致带 2.7MB audiobase64 的文章无法同步入库（如"刺疟论"）。
 * 方案：>1MB 的 audiobase64 解码后写入沙箱文件，contents.audiobase64 列仅存 'file://绝对路径' 引用。
 *      - hasAudio 判断（audiobase64.length > 0）天然兼容 file:// 引用
 *      - 上行（推送/备份导出）前用 readAsBase64 还原，协议不变
 */
import fs from '@ohos.file.fs';
import { util } from '@kit.ArkTS';
import common from '@ohos.app.ability.common';
import { ImageCompressionService } from './ImageCompressionService';

export const AUDIO_FILE_PREFIX: string = 'file://';
export const AUDIO_BIG_LIMIT: number = 1000000; // >1MB 才落文件

// 模块级目录（init 注入；未 init 时回退默认沙箱路径，避免空指针）
let audioDir: string = '/data/storage/el2/base/haps/entry/files/audio';

export class AudioFileStore {
  /**
   * 应用启动时注入沙箱目录（EntryAbility/Splash 初始化阶段调用）
   */
  static init(context: common.Context | null): void {
    try {
      const base: string = (context && context.filesDir) ? context.filesDir : '/data/storage/el2/base/haps/entry/files';
      audioDir = base + '/audio';
      try {
        if (!fs.accessSync(audioDir)) {
          fs.mkdirSync(audioDir);
        }
      } catch (e) {
        console.error('AudioFileStore: 创建 audio 目录失败: ' + JSON.stringify(e));
      }
    } catch (e) {
      console.error('AudioFileStore.init 异常: ' + JSON.stringify(e));
    }
  }

  static isFileRef(value: string): boolean {
    return value !== null && value !== undefined && value.indexOf(AUDIO_FILE_PREFIX) === 0;
  }

  static pathOf(fileRef: string): string {
    return fileRef.substring(AUDIO_FILE_PREFIX.length);
  }

  private static audioPathFor(clientId: string): string {
    return audioDir + '/' + clientId + '.m4a';
  }

  /**
   * 把将要写入 RDB 的 audiobase64 转为存储形态：
   *  - 空 → 空
   *  - 已是 file:// → 原样（幂等）
   *  - 超过 AUDIO_BIG_LIMIT → 解码写沙箱文件，返回 file:// 引用
   *  - 其余（内嵌小音频）→ 原样返回
   */
  static toStoredValue(clientId: string, audio: string): string {
    const raw: string = audio || '';
    if (raw === '') {
      return '';
    }
    if (AudioFileStore.isFileRef(raw)) {
      return raw;
    }
    if (raw.length <= AUDIO_BIG_LIMIT) {
      return raw;
    }
    // 大音频落文件
    try {
      let bytes: Uint8Array;
      try {
        const clean: string = raw
          .replace(/^data:audio\/[a-z0-9]+;base64,/, '')
          .replace(/[\r\n\s]/g, '');
        const helper: util.Base64Helper = new util.Base64Helper();
        bytes = helper.decodeSync(clean);
      } catch (decodeErr) {
        console.error('AudioFileStore: base64 解码失败 clientId=' + clientId + ': ' + JSON.stringify(decodeErr));
        return raw; // 解码失败保底仍存 base64
      }
      if (bytes.length === 0) {
        return raw;
      }
      const filePath: string = AudioFileStore.audioPathFor(clientId);
      try {
        if (fs.accessSync(filePath)) {
          fs.unlinkSync(filePath); // 覆盖旧文件
        }
      } catch (e) { /* 不存在则忽略 */ }
      const f: fs.File = fs.openSync(filePath, fs.OpenMode.CREATE | fs.OpenMode.WRITE_ONLY | fs.OpenMode.TRUNC);
      fs.writeSync(f.fd, bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.length));
      fs.closeSync(f);
      console.info('AudioFileStore: 大音频已落文件 clientId=' + clientId + ' size=' + bytes.length + 'B path=' + filePath);
      return AUDIO_FILE_PREFIX + filePath;
    } catch (e) {
      console.error('AudioFileStore: 写文件失败 clientId=' + clientId + ': ' + JSON.stringify(e));
      return raw;
    }
  }

  /**
   * 读取 file:// 引用的音频并还原为 base64（供推送/备份导出等上行使用）
   */
  static async toBase64(storedValue: string): Promise<string> {
    if (!AudioFileStore.isFileRef(storedValue)) {
      return storedValue || '';
    }
    const filePath: string = AudioFileStore.pathOf(storedValue);
    try {
      const f: fs.File = fs.openSync(filePath, fs.OpenMode.READ_ONLY);
      const stat = fs.statSync(f.fd);
      const buf = new ArrayBuffer(stat.size);
      fs.readSync(f.fd, buf);
      fs.closeSync(f);
      const b64: string = ImageCompressionService.base64Encode(buf);
      console.info('AudioFileStore: 读文件还原 base64 path=' + filePath + ' size=' + stat.size + 'B');
      return b64;
    } catch (e) {
      console.error('AudioFileStore: 读文件失败 ' + filePath + ': ' + JSON.stringify(e));
      return '';
    }
  }

  /**
   * 同步读取 file:// 引用并还原为 base64（供同步调用链使用）
   */
  static toBase64Sync(storedValue: string): string {
    if (!AudioFileStore.isFileRef(storedValue)) {
      return storedValue || '';
    }
    const filePath: string = AudioFileStore.pathOf(storedValue);
    try {
      const f: fs.File = fs.openSync(filePath, fs.OpenMode.READ_ONLY);
      const stat = fs.statSync(f.fd);
      const buf = new ArrayBuffer(stat.size);
      fs.readSync(f.fd, buf);
      fs.closeSync(f);
      return ImageCompressionService.base64Encode(buf);
    } catch (e) {
      console.error('AudioFileStore: 同步读文件失败 ' + filePath + ': ' + JSON.stringify(e));
      return '';
    }
  }

  /**
   * 删除某 clientId 对应的音频文件（文章删除/覆盖时调用，忽略失败）
   */
  static removeByClientId(clientId: string): void {
    try {
      const filePath: string = AudioFileStore.audioPathFor(clientId);
      if (fs.accessSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    } catch (e) { /* ignore */ }
  }
}

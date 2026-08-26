import media from '@ohos.multimedia.media';
import fs from '@ohos.file.fs';
import { common } from '@kit.AbilityKit';
import { util } from '@kit.ArkTS';
import { ImageCompressionService } from './ImageCompressionService';

/**
 * 音频播放服务
 *
 * 工作流程（参考 ImageCompressionService 的 base64 解码模式）：
 *   1) base64 字符串 → Uint8Array（复用 ImageCompressionService.base64Decode）
 *   2) 写入沙箱临时文件（.m4a 扩展名，与 Win 端转码格式一致）
 *   3) openSync 打开文件拿到 fd → AVPlayer.url = 'fd://' + fd
 *   4) 注册 stateChange / timeUpdate / durationUpdate / error 回调
 *   5) await prepare() → 成功后由调用方 play()
 *
 * 资源释放顺序（关键，避免 fd 泄漏与崩溃）：
 *   await player.release()  →  closeSync(fd)  →  unlinkSync(临时文件)
 *
 * 生命周期由 Reader.ets 持有：aboutToDisappear 调用 release()
 */
export type AudioPlayerState = 'idle' | 'preparing' | 'prepared' | 'playing' | 'paused' | 'completed' | 'error' | 'released';

export class AudioService {
  private player: media.AVPlayer | null = null;
  private tempFilePath: string = '';
  private audioFd: number = -1;
  private fdFile: fs.File | null = null;  // 保存 fdFile 对象，避免被 GC 后 fd 失效
  private currentState: AudioPlayerState = 'idle';
  // 三组独立回调（避免 ArkTS 不接受含方法的接口对象字面量 arkts-no-untyped-obj-literals）
  private stateCallback: ((state: AudioPlayerState) => void) | null = null;
  private timeCallback: ((currentMs: number, durationMs: number) => void) | null = null;
  private errorCallback: ((message: string) => void) | null = null;
  private durationMs: number = 0;
  private prepared: boolean = false;

  setCallbacks(
    onState: (state: AudioPlayerState) => void,
    onTime: (currentMs: number, durationMs: number) => void,
    onError: (message: string) => void
  ): void {
    this.stateCallback = onState;
    this.timeCallback = onTime;
    this.errorCallback = onError;
  }

  getCurrentState(): AudioPlayerState {
    return this.currentState;
  }

  getDuration(): number {
    return this.durationMs;
  }

  hasPlayer(): boolean {
    return this.player !== null;
  }

  isPrepared(): boolean {
    return this.prepared;
  }

  private setState(s: AudioPlayerState): void {
    this.currentState = s;
    if (this.stateCallback) {
      this.stateCallback(s);
    }
  }

  /**
   * 从 base64 准备音频：解码 → 临时文件 → AVPlayer.prepare
   * 成功后状态为 prepared，调用方再调用 play() 自动播放
   */
  async prepare(base64: string, ctx: common.Context): Promise<void> {
    // 先释放旧实例（含 fd 与临时文件）
    await this.releaseInternal();

    // 1. base64 字符串清洗（去除 Data URL 前缀、换行符、空格，避免解码失败或音频损坏）
    //    服务端返回的 base64 可能含换行符，手写查表解码会失败，必须先清洗
    const cleanBase64: string = base64
      .replace(/^data:audio\/[a-z0-9]+;base64,/, '')
      .replace(/[\r\n\s]/g, '');
    console.info('AudioService: base64 原始长度=' + base64.length + ' 清洗后长度=' + cleanBase64.length);
    // 二进制安全解码：用系统 API util.Base64Helper.decodeSync（严禁用文本编码参与二进制音频解码）
    let bytes: Uint8Array;
    try {
      const base64Helper: util.Base64Helper = new util.Base64Helper();
      bytes = base64Helper.decodeSync(cleanBase64);
      console.info('AudioService: base64 解码 OK, 字节数=' + bytes.length);
    } catch (decodeErr) {
      console.error('AudioService: base64 解码失败: ' + JSON.stringify(decodeErr));
      this.setState('error');
      throw new Error('base64 decode failed: ' + JSON.stringify(decodeErr));
    }
    if (bytes.length === 0) {
      console.error('AudioService: base64 解码为空');
      this.setState('error');
      throw new Error('audio base64 decode empty');
    }

    // 2. 写入沙箱临时文件（.m4a 与 Win 端转码格式一致，鸿蒙 AVPlayer 原生支持）
    const tempName: string = 'tmp_audio_' + Date.now() + '.m4a';
    const tempPath: string = ImageCompressionService.getSandboxPath(ctx, tempName);
    this.tempFilePath = tempPath;
    try {
      const f: fs.File = fs.openSync(tempPath, fs.OpenMode.CREATE | fs.OpenMode.WRITE_ONLY);
      fs.writeSync(f.fd, bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.length));
      fs.closeSync(f);
      console.info('AudioService: 音频临时文件写入 OK path=' + tempPath + ', size=' + bytes.length + 'B');
    } catch (writeErr) {
      console.error('AudioService: 音频文件写入失败: ' + JSON.stringify(writeErr));
      this.setState('error');
      throw new Error('audio file write failed: ' + JSON.stringify(writeErr));
    }

    // 3. 打开文件拿 fd，保存 fdFile 对象避免被 GC 后 fd 失效
    //    AVPlayer 本地文件用 fd:// 协议（file:// 会报 401 权限错误）
    this.fdFile = fs.openSync(tempPath, fs.OpenMode.READ_ONLY);
    this.audioFd = this.fdFile.fd;
    console.info('AudioService: fd=' + this.audioFd);

    // 4. 创建 AVPlayer 并注册回调
    this.prepared = false;
    // createAVPlayer 返回 Promise，await 后用局部非空变量承载，避免 ArkTS 跨语句空值窄化失败
    const avPlayer: media.AVPlayer = await media.createAVPlayer();
    this.player = avPlayer;
    avPlayer.on('stateChange', (state: string, reason: media.StateChangeReason) => {
      console.info('AudioService: stateChange state=' + state + ' reason=' + reason);
      if (state === 'idle') {
        this.setState('idle');
      } else if (state === 'initialized') {
        // url 设置后进入 initialized，此时才能调用 prepare（否则报 5400102）
        console.info('AudioService: initialized, 开始 prepare...');
        avPlayer.prepare().then(() => {
          console.info('AudioService: prepare 完成，duration=' + this.durationMs + 'ms');
        }).catch((prepareErr: Error) => {
          console.error('AudioService: prepare 失败: ' + JSON.stringify(prepareErr));
          this.prepared = false;
          this.setState('error');
        });
      } else if (state === 'prepared') {
        this.prepared = true;
        this.setState('prepared');
      } else if (state === 'playing') {
        this.setState('playing');
      } else if (state === 'paused') {
        this.setState('paused');
      } else if (state === 'completed') {
        this.setState('completed');
      } else if (state === 'error') {
        this.prepared = false;
        this.setState('error');
      } else if (state === 'released') {
        this.prepared = false;
        this.setState('released');
      }
    });
    avPlayer.on('error', (err: Error) => {
      console.error('AudioService: AVPlayer error: ' + JSON.stringify(err));
      this.prepared = false;
      this.setState('error');
      if (this.errorCallback) {
        this.errorCallback(JSON.stringify(err));
      }
    });
    avPlayer.on('durationUpdate', (duration: number) => {
      this.durationMs = duration;
      if (this.timeCallback) {
        this.timeCallback(0, this.durationMs);
      }
    });
    avPlayer.on('timeUpdate', (time: number) => {
      if (this.timeCallback) {
        this.timeCallback(time, this.durationMs);
      }
    });
    avPlayer.on('endOfStream', () => {
      this.setState('completed');
    });

    // 5. 设置 url（idle → initialized），stateChange 回调在 initialized 时自动调用 prepare
    //    注意：不能在设置 url 后立即 await prepare()，否则会报 5400102（状态机错误）
    avPlayer.url = 'fd://' + this.audioFd.toString();
    this.setState('preparing');
    console.info('AudioService: url 已设置，等待 stateChange initialized 自动 prepare...');
  }

  /**
   * 自动播放（仅在 prepared/paused/completed 状态生效）
   */
  play(): void {
    if (this.player && (this.currentState === 'prepared' || this.currentState === 'paused' || this.currentState === 'completed')) {
      this.player.play();
    } else {
      console.warn('AudioService: play() 跳过，当前状态=' + this.currentState);
    }
  }

  pause(): void {
    if (this.player && this.currentState === 'playing') {
      this.player.pause();
    }
  }

  togglePlayPause(): void {
    if (this.currentState === 'playing') {
      this.pause();
    } else if (this.currentState === 'prepared' || this.currentState === 'paused' || this.currentState === 'completed') {
      this.play();
    }
  }

  seek(ms: number): void {
    if (this.player && this.currentState !== 'released' && this.currentState !== 'error') {
      this.player.seek(ms);
    }
  }

  async release(): Promise<void> {
    await this.releaseInternal();
  }

  private async releaseInternal(): Promise<void> {
    if (this.player) {
      try {
        await this.player.release();
      } catch (e) {
        console.warn('AudioService: player.release 异常: ' + JSON.stringify(e));
      }
      this.player = null;
    }
    // 释放 player 后才能 close fd（避免 fd 被占用崩溃）
    if (this.fdFile !== null) {
      try { fs.closeSync(this.fdFile); } catch (e) { /* ignore */ }
      this.fdFile = null;
    }
    this.audioFd = -1;
    if (this.tempFilePath.length > 0) {
      try { fs.unlinkSync(this.tempFilePath); } catch (e) { /* ignore */ }
      this.tempFilePath = '';
    }
    this.durationMs = 0;
    this.prepared = false;
    this.setState('released');
  }
}

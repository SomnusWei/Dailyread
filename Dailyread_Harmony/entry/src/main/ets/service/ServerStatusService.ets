/**
 * 服务器状态检测服务
 * 功能：定期检测服务器连通性，提供状态回调
 */
import http from '@ohos.net.http';

export type ServerStatus = 'online' | 'offline' | 'checking';

export class ServerStatusService {
  private static instance: ServerStatusService | null = null;
  private status: ServerStatus = 'checking';
  private listeners: Set<(status: ServerStatus) => void> = new Set();
  private timerId: number = -1;
  private isRunning: boolean = false;
  private readonly CHECK_INTERVAL: number = 10000; // 10秒检测一次
  private readonly HEALTH_URL: string = 'https://dailyread.sonnusww.top/health';

  static getInstance(): ServerStatusService {
    if (!ServerStatusService.instance) {
      ServerStatusService.instance = new ServerStatusService();
    }
    return ServerStatusService.instance;
  }

  getStatus(): ServerStatus {
    return this.status;
  }

  onStatusChange(callback: (status: ServerStatus) => void): () => void {
    this.listeners.add(callback);
    callback(this.status); // 立即回调当前状态
    return () => {
      this.listeners.delete(callback);
    };
  }

  start(): void {
    if (this.isRunning) {
      return;
    }
    this.isRunning = true;
    this.checkServer();
    this.timerId = setInterval(() => {
      this.checkServer();
    }, this.CHECK_INTERVAL);
  }

  stop(): void {
    this.isRunning = false;
    if (this.timerId !== -1) {
      clearInterval(this.timerId);
      this.timerId = -1;
    }
  }

  async checkServer(): Promise<void> {
    const prevStatus = this.status;
    // 仅在首次检测时显示 'checking' 状态，后续轮询不再闪黄
    if (prevStatus === 'checking') {
      this.notifyListeners();
    }

    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(this.HEALTH_URL, {
        method: http.RequestMethod.GET,
        connectTimeout: 5000,
        readTimeout: 5000
      });
      httpRequest.destroy();

      if (response.responseCode === 200) {
        this.status = 'online';
      } else {
        this.status = 'offline';
      }
    } catch (e) {
      this.status = 'offline';
    }

    // 检测完成后，状态变化才通知监听器
    if (prevStatus !== this.status) {
      this.notifyListeners();
    }
  }

  private notifyListeners(): void {
    this.listeners.forEach(callback => {
      try {
        callback(this.status);
      } catch (e) {
        console.error('ServerStatusService: listener error', e);
      }
    });
  }
}

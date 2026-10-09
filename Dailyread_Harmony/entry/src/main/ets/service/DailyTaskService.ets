import { DailyTaskRepository, DailyTaskItem } from '../repository/DailyTaskRepository';
import { ApiClient } from './ApiClient';
import { SyncService } from './SyncService';

/**
 * 每日任务服务
 * 今日任务统一由服务端生成；本端只负责从服务端拉取并缓存到本地，
 * 不再本地生成任务列表（离线且无缓存时返回空列表）。
 */
export class DailyTaskService {
  private static instance: DailyTaskService | null = null;
  private taskRepository: DailyTaskRepository;

  private constructor() {
    this.taskRepository = DailyTaskRepository.getInstance();
  }

  static getInstance(): DailyTaskService {
    if (!DailyTaskService.instance) {
      DailyTaskService.instance = new DailyTaskService();
    }
    return DailyTaskService.instance;
  }

  /**
   * 获取今日任务列表（本地缓存）
   * 注意：只要主记录存在且 count>0，即使 items 为空（查询异常）也认为有任务。
   */
  async getTodayTasks(): Promise<DailyTaskItem[]> {
    const record = await this.taskRepository.getTodayTask();
    if (!record) {
      return [];
    }
    return record.items;
  }

  /**
   * 是否有今日任务
   */
  async hasTodayTasks(): Promise<boolean> {
    return await this.taskRepository.hasTodayTask();
  }

  /**
   * 获取今日任务列表
   * 任务全部由服务端生成：优先使用本地缓存，缓存缺失时从服务端拉取（服务端不存在会自动生成）。
   * 未登录或服务端无任务时返回空列表，本地不再生成。
   */
  async getOrGenerateTodayTasks(): Promise<DailyTaskItem[]> {
    // 命中本地缓存直接返回
    const record = await this.taskRepository.getTodayTask();
    if (record && record.count > 0 && record.items.length > 0) {
      console.info('DailyTaskService.getOrGenerateTodayTasks: 命中今日任务记录，count=' + record.count
        + '，items.length=' + record.items.length);
      return record.items;
    }

    const api = ApiClient.getInstance();
    if (!api.isLoggedIn()) {
      console.info('DailyTaskService.getOrGenerateTodayTasks: 未登录，无今日任务');
      return [];
    }

    try {
      console.info('DailyTaskService.getOrGenerateTodayTasks: 从服务端拉取今日任务');
      const syncService = SyncService.getInstance();
      await syncService.fetchOrGenerateTodayTasks();
      const serverRecord = await this.taskRepository.getTodayTask();
      if (serverRecord && serverRecord.items && serverRecord.items.length > 0) {
        console.info('DailyTaskService.getOrGenerateTodayTasks: 服务端任务已同步，items=' + serverRecord.items.length);
        return serverRecord.items;
      }
      console.info('DailyTaskService.getOrGenerateTodayTasks: 服务端无任务，返回空列表');
      return [];
    } catch (e) {
      console.error('DailyTaskService.getOrGenerateTodayTasks: 服务端获取失败: ' + JSON.stringify(e));
      return [];
    }
  }

  /**
   * 标记文章已完成打卡
   */
  async markTaskCompleted(taskId: number, articleId: number): Promise<void> {
    await this.taskRepository.markArticleChecked(taskId, articleId);
  }

  /**
   * 强制刷新今日任务（先清除本地缓存，再从服务端重新拉取/生成）
   */
  async forceRefresh(): Promise<void> {
    await this.taskRepository.clearTodayTask();
    const api = ApiClient.getInstance();
    if (api.isLoggedIn()) {
      try {
        const syncService = SyncService.getInstance();
        // force=true：让服务端删除已有任务并重新生成
        await syncService.fetchOrGenerateTodayTasks(true);
      } catch (e) {
        console.error('forceRefresh server-side error: ' + JSON.stringify(e));
      }
    }
  }
}

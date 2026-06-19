import { Article } from '../model/Article';
import { Config } from '../model/Config';
import { ConfigRepository } from '../repository/ConfigRepository';
import { DailyTaskRepository, DailyTaskItem, DailyTaskRecord } from '../repository/DailyTaskRepository';

/**
 * 文章分类结果
 */
interface ArticleCategoryResult {
  longArticles: Article[];
  shortArticles: Article[];
}

/**
 * 每日任务生成服务
 * 负责：
 * 1. 任务池筛选（符合阅读条件的文章）
 * 2. 文章分类（长文章/短文章）
 * 3. 任务列表生成（三种分支策略）
 * 4. 防重复轮播机制
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
   * 获取文章的有效目标完成率
   * 如果文章有独立目标率且不为0，则使用独立目标率
   * 否则使用全局目标完成率
   */
  private getEffectiveTargetRate(article: Article, globalRate: number): number {
    if (article.useIndependentCheckRate && article.independentCheckRate > 0) {
      return article.independentCheckRate;
    }
    return globalRate;
  }

  /**
   * 筛选任务池
   * 条件：
   * 1. 文章阅读状态为"阅读中"（isReading = true）
   * 2. 当前完成率 < 全局目标完成率或独立目标完成率
   */
  private filterTaskPool(articles: Article[], globalTargetRate: number): Article[] {
    return articles.filter(article => {
      if (!article.isReading) {
        return false;
      }
      const effectiveRate = this.getEffectiveTargetRate(article, globalTargetRate);
      return article.completionRate < effectiveRate;
    });
  }

  /**
   * 计算最大字数上限
   * 公式：阅读时间(分钟) × 100 ×（1.01~1.11的随机数）
   */
  private calculateMaxWordLimit(dailyMinutes: number): number {
    const randomFactor = 1.01 + Math.random() * 0.1;
    return Math.floor(dailyMinutes * 100 * randomFactor);
  }

  /**
   * 判断是否为长文章
   * 长文章：字数 > 最大字数上限 * 30%
   */
  private isLongArticle(article: Article, maxWordLimit: number): boolean {
    const wordCount = article.chineseChars > 0 ? article.chineseChars : article.content.length;
    const threshold = maxWordLimit * 0.3;
    return wordCount > threshold;
  }

  /**
   * 分类文章为长文章和短文章
   */
  private categorizeArticles(taskPool: Article[], maxWordLimit: number): ArticleCategoryResult {
    const longArticles: Article[] = [];
    const shortArticles: Article[] = [];

    for (let i = 0; i < taskPool.length; i++) {
      const article = taskPool[i];
      if (this.isLongArticle(article, maxWordLimit)) {
        longArticles.push(article);
      } else {
        shortArticles.push(article);
      }
    }

    return { longArticles, shortArticles };
  }

  /**
   * 随机抽取短文章组合
   * 目标：组合后的总字数尽可能接近但不超过剩余字数
   */
  private selectShortArticles(shortArticles: Article[], remainingWord: number): Article[] {
    if (remainingWord <= 0 || shortArticles.length === 0) {
      return [];
    }

    const selected: Article[] = [];
    let totalWords = 0;
    const available: Article[] = [...shortArticles];
    const maxAttempts = 100;

    for (let attempt = 0; attempt < maxAttempts && available.length > 0; attempt++) {
      const randomIndex = Math.floor(Math.random() * available.length);
      const candidate = available[randomIndex];
      const wordCount = candidate.chineseChars > 0 ? candidate.chineseChars : candidate.content.length;

      if (totalWords + wordCount <= remainingWord) {
        selected.push(candidate);
        totalWords += wordCount;
      }
      available.splice(randomIndex, 1);
    }

    return selected;
  }

  /**
   * 检查两个数组是否完全相同（不考虑顺序）
   */
  private arraysEqualIgnoreOrder(a: number[], b: number[]): boolean {
    if (a.length !== b.length) {
      return false;
    }
    const sortedA = [...a].sort((x, y) => x - y);
    const sortedB = [...b].sort((x, y) => x - y);
    for (let i = 0; i < sortedA.length; i++) {
      if (sortedA[i] !== sortedB[i]) {
        return false;
      }
    }
    return true;
  }

  /**
   * 检查是否满足防重复条件
   * - 长文章总数 <= 2：不能与上次完全相同
   * - 长文章总数 >= 3：允许有1篇重复，但不能全部相同
   */
  private checkAntiDuplicate(
    currentIds: number[],
    lastIds: number[],
    totalLongCount: number
  ): boolean {
    if (lastIds.length === 0) {
      return true;
    }

    if (totalLongCount <= 2) {
      return !this.arraysEqualIgnoreOrder(currentIds, lastIds);
    } else {
      let hasNewArticle = false;
      for (let i = 0; i < currentIds.length; i++) {
        if (!lastIds.includes(currentIds[i])) {
          hasNewArticle = true;
          break;
        }
      }
      return hasNewArticle;
    }
  }

  /**
   * 随机组合长文章
   * 要求：总字数 < 最大字数上限 * 70%
   */
  private async selectLongArticles(
    longArticles: Article[],
    maxWordLimit: number
  ): Promise<Article[]> {
    const maxTotalWords = maxWordLimit * 0.7;
    const lastIds = await this.taskRepository.getYesterdayLongArticleIds();
    const totalLongCount = longArticles.length;
    const maxAttempts = 10;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const selected: Article[] = [];
      let totalWords = 0;
      const available: Article[] = [...longArticles];

      while (available.length > 0) {
        const randomIndex = Math.floor(Math.random() * available.length);
        const candidate = available[randomIndex];
        const wordCount = candidate.chineseChars > 0 ? candidate.chineseChars : candidate.content.length;

        if (totalWords + wordCount <= maxTotalWords) {
          selected.push(candidate);
          totalWords += wordCount;
        }
        available.splice(randomIndex, 1);
      }

      if (selected.length === 0) {
        let minLen = Number.MAX_VALUE;
        let minArticle: Article | null = null;
        for (let i = 0; i < longArticles.length; i++) {
          const wordCount = longArticles[i].chineseChars > 0 ? longArticles[i].chineseChars : longArticles[i].content.length;
          if (wordCount < minLen && wordCount <= maxTotalWords) {
            minLen = wordCount;
            minArticle = longArticles[i];
          }
        }
        if (minArticle !== null) {
          selected.push(minArticle);
        }
      }

      const currentIds = selected.map(a => a.id);
      if (this.checkAntiDuplicate(currentIds, lastIds, totalLongCount)) {
        return selected;
      }
    }

    console.warn('防重复校验多次失败，降级为允许重复');
    const selected: Article[] = [];
    let totalWords = 0;
    const available: Article[] = [...longArticles];

    while (available.length > 0 && totalWords < maxTotalWords) {
      const randomIndex = Math.floor(Math.random() * available.length);
      const candidate = available[randomIndex];
      const wordCount = candidate.chineseChars > 0 ? candidate.chineseChars : candidate.content.length;

      if (totalWords + wordCount <= maxTotalWords) {
        selected.push(candidate);
        totalWords += wordCount;
      }
      available.splice(randomIndex, 1);
    }

    if (selected.length === 0) {
      let minLen = Number.MAX_VALUE;
      let minArticle: Article | null = null;
      for (let i = 0; i < longArticles.length; i++) {
        const wordCount = longArticles[i].chineseChars > 0 ? longArticles[i].chineseChars : longArticles[i].content.length;
        if (wordCount < minLen && wordCount <= maxTotalWords) {
          minLen = wordCount;
          minArticle = longArticles[i];
        }
      }
      if (minArticle !== null) {
        selected.push(minArticle);
      }
    }

    return selected;
  }

  /**
   * 将文章转换为任务项
   */
  private articleToTaskItem(article: Article, taskId: number = 0): DailyTaskItem {
    const wordCount = article.chineseChars > 0 ? article.chineseChars : article.content.length;
    return {
      taskId: taskId,
      articleId: article.id,
      articleTitle: article.title,
      wordTarget: wordCount,
      isCheckedIn: false,
      isLongArticle: article.isLongArticle,
      isRequired: article.isRequired,
      displayName: article.title
    };
  }

  /**
   * 获取今日任务列表
   * 注意：只要主记录存在且 count>0，即使 items 为空（查询异常）也认为有任务。
   * 此时会尝试直接查询 daily_task_items 表做二次校验。
   */
  async getTodayTasks(): Promise<DailyTaskItem[]> {
    const record = await this.taskRepository.getTodayTask();
    if (!record) {
      return [];
    }
    // 若 items 为空但 count>0，说明子表查询失败，不要返回空以免 UI 显示为"没有任务"
    // 这里信任 count 字段，返回 record.items（如果后续 loadData 中需要再自行加载 articles）
    // 如果 items 确实为空而 count>0，调用方应通过 taskId 从 items 表中重新读取
    return record.items;
  }

  /**
   * 是否有今日任务
   */
  async hasTodayTasks(): Promise<boolean> {
    return await this.taskRepository.hasTodayTask();
  }

  /**
   * 获取或生成今日任务列表
   * 如果数据库中有当天的任务列表则返回，否则生成新的
   */
  async getOrGenerateTodayTasks(articles: Article[]): Promise<DailyTaskItem[]> {
    // 检查是否有今日任务缓存
    const record = await this.taskRepository.getTodayTask();
    if (record && record.count > 0) {
      // 主记录的 count > 0，说明今日任务已经生成并保存
      // —— 关键防御：如果 items 为空但 count>0，说明 items 查询异常
      //    不要返回空数组（否则首页会显示空列表）
      //    也不要重新生成（否则会重置任务列表打乱文章顺序）
      console.info('DailyTaskService.getOrGenerateTodayTasks: 命中今日任务记录，count=' + record.count
        + '，items.length=' + record.items.length);

      // 若 items 为空（可能查询异常），基于主记录中的文章信息做保守回退
      // —— 这里需要依赖 item 表中确实有数据，只要 Home.loadData 中通过 articleId 匹配 article
      //    即便 items 的部分字段缺失也能部分展示
      return record.items;
    }

    // 需要生成新的任务列表（记录不存在或 count=0）
    console.info('DailyTaskService.getOrGenerateTodayTasks: 无有效记录，生成新的今日任务列表'
      + '，count=' + (record ? record.count : 'N/A'));

    const config = await ConfigRepository.getInstance().getConfig();
    const globalTargetRate = config.targetCheckRate;
    const dailyMinutes = config.dailyMinutes;

    // 准备任务记录
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`;
    let resultItems: DailyTaskItem[] = [];
    let selectedLongArticleIds: number[] = [];

    if (dailyMinutes > 0 && articles.length > 0) {
      // 筛选任务池
      const taskPool = this.filterTaskPool(articles, globalTargetRate);

      if (taskPool.length > 0) {
        // ===== 必读文章前置：将 isRequired=true 的文章直接放入任务列表 =====
        const requiredArticles: Article[] = [];
        const remainingPool: Article[] = [];
        for (let i = 0; i < taskPool.length; i++) {
          if (taskPool[i].isRequired) {
            requiredArticles.push(taskPool[i]);
          } else {
            remainingPool.push(taskPool[i]);
          }
        }
        if (requiredArticles.length > 0) {
          console.info('检测到 ' + requiredArticles.length + ' 篇必读文章，加入任务列表最前面');
          for (let i = 0; i < requiredArticles.length; i++) {
            resultItems.push(this.articleToTaskItem(requiredArticles[i]));
          }
        }
        // ================================================================

        // 计算最大字数上限并分类（用剩余文章池进行分支策略选择）
        const maxWordLimit = this.calculateMaxWordLimit(dailyMinutes);
        const categoryResult = this.categorizeArticles(remainingPool, maxWordLimit);
        const longArticles = categoryResult.longArticles;
        const shortArticles = categoryResult.shortArticles;

        // 执行分支策略
        let selectedLongArticles: Article[] = [];
        let selectedShortArticles: Article[] = [];

        if (longArticles.length === 0) {
          console.info('执行分支A：无长文章（剩余池）');
          selectedShortArticles = this.selectShortArticles(shortArticles, maxWordLimit);
        } else if (longArticles.length === 1) {
          console.info('执行分支B：一篇长文章（剩余池）');
          const longArticle = longArticles[0];
          const longWordCount = longArticle.chineseChars > 0 ? longArticle.chineseChars : longArticle.content.length;

          if (longWordCount <= maxWordLimit) {
            selectedLongArticles = [longArticle];
            selectedLongArticleIds = [longArticle.id];
            const remainingWord = maxWordLimit - longWordCount;
            selectedShortArticles = this.selectShortArticles(shortArticles, remainingWord);
          } else {
            selectedShortArticles = this.selectShortArticles(shortArticles, maxWordLimit);
          }
        } else {
          console.info('执行分支C：多篇长文章（剩余池）');
          selectedLongArticles = await this.selectLongArticles(longArticles, maxWordLimit);
          selectedLongArticleIds = selectedLongArticles.map(a => a.id);

          let longTotalWords = 0;
          for (let i = 0; i < selectedLongArticles.length; i++) {
            const wordCount = selectedLongArticles[i].chineseChars > 0
              ? selectedLongArticles[i].chineseChars
              : selectedLongArticles[i].content.length;
            longTotalWords += wordCount;
          }

          const remainingWord = maxWordLimit - longTotalWords;
          selectedShortArticles = this.selectShortArticles(shortArticles, remainingWord);
        }

        // 转换为任务项
        for (let i = 0; i < selectedLongArticles.length; i++) {
          resultItems.push(this.articleToTaskItem(selectedLongArticles[i]));
        }

        for (let i = 0; i < selectedShortArticles.length; i++) {
          resultItems.push(this.articleToTaskItem(selectedShortArticles[i]));
        }
      } else {
        console.info('任务池为空，所有文章已完成本月目标');
      }
    } else {
      console.info('每日阅读时间配置为0或无文章');
    }

    // 计算总字数
    let totalWords = 0;
    for (let i = 0; i < resultItems.length; i++) {
      totalWords += resultItems[i].wordTarget;
    }

    // 创建任务记录
    const taskRecord: DailyTaskRecord = {
      date: todayStr,
      count: resultItems.length,
      totalWords: totalWords,
      lastLongArticleIds: JSON.stringify(selectedLongArticleIds),
      items: resultItems,
      createTime: new Date().toISOString(),
      lastModified: new Date().toISOString()
    };

    // 保存到数据库（如果已有记录则更新，否则插入）
    let taskId: number;
    if (record && record.id) {
      // 更新现有记录
      taskRecord.id = record.id;
      taskRecord.createTime = record.createTime; // 保留原创建时间
      await this.taskRepository.updateTask(taskRecord);
      taskId = record.id;
      console.info('今日任务已更新，taskId=' + taskId + '，items=' + resultItems.length);
    } else {
      // 插入新记录
      taskId = await this.taskRepository.insertTask(taskRecord);
      console.info('今日任务已持久化，taskId=' + taskId + '，items=' + resultItems.length);
    }

    // 更新任务项的 taskId
    for (let i = 0; i < resultItems.length; i++) {
      resultItems[i].taskId = taskId;
    }

    return resultItems;
  }

  /**
   * 标记文章已完成打卡
   */
  async markTaskCompleted(taskId: number, articleId: number): Promise<void> {
    await this.taskRepository.markArticleChecked(taskId, articleId);
  }

  /**
   * 强制刷新今日任务
   */
  async forceRefresh(): Promise<void> {
    await this.taskRepository.clearTodayTask();
  }
}

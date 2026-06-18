import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';
import { CheckInRecord } from '../model/CheckInRecord';
import { CheckInRepository } from '../repository/CheckInRepository';
import { Config } from '../model/Config';
import { ConfigRepository } from '../repository/ConfigRepository';
import { DailyTaskService } from '../service/DailyTaskService';
import { DailyTaskItem } from '../repository/DailyTaskRepository';

interface TaskItemUI {
  taskId: number;
  articleId: number;
  articleTitle: string;
  wordTarget: number;
  isCheckedIn: boolean;
  isRequired: boolean;
  isLongArticle: boolean;
  displayName: string;
  progressPercent: number;
}

@Entry
@Component
struct HomePage {
  @State tasks: TaskItemUI[] = [];
  @State isLoading: boolean = true;
  @State config: Config = new Config();
  @State totalCheckIns: number = 0;
  @State todayCheckIns: number = 0;
  @State totalWordsToday: number = 0;
  @State targetWordsToday: number = 0;
  @State completedTasksCount: number = 0;
  @State completedCount: number = 0;
  @State requiredTasksCount: number = 0;
  @State requiredCompleted: number = 0;

  @Watch('onRefreshSignalChanged')
  @StorageProp('dataRefreshSignal') refreshSignal: string = '';

  // 今日已打卡文章 ID 列表（格式: "日期|id1,id2,id3"）
  // Reader 打卡后会更新此值，Home 用 @StorageLink 实时读取，
  // 不依赖 aboutToShow / @Watch 的异步触发，确保返回后立即显示正确状态
  @StorageLink('todayCheckedInIds') todayCheckedInIds: string = '';

  // 数据预加载就绪标志 - 由 SplashPage 在预加载完成后设置
  @Watch('onDailyTaskPreloadedChanged')
  @StorageProp('dailyTaskPreloaded') dailyTaskPreloaded: boolean = false;

  aboutToAppear(): void {
    this.isLoading = true;
    // 关键修复 B: 启动时从数据库把今日打卡记录同步到 AppStorage。
    // 这样 TaskCard 渲染时用的 isArticleCheckedIn() 能直接读取
    // 最新状态（同步操作，不依赖异步生命周期）。
    this.syncTodayCheckedInIdsToStorage();
    this.loadData();
  }

  /**
   * 从 check_in_records 表读取今日打卡文章 ID，并同步到 AppStorage。
   * 格式: "2026-06-16|id1,id2,id3"
   * 作用: 让 TaskCard 在渲染时通过同步方法 isArticleCheckedIn() 直接读取
   *       最新的打卡状态，不依赖 @Watch 或 aboutToShow 的异步触发。
   */
  syncTodayCheckedInIdsToStorage(): void {
    const todayDate: Date = new Date();
    const year: number = todayDate.getFullYear();
    const month: string = (todayDate.getMonth() + 1).toString().padStart(2, '0');
    const day: string = todayDate.getDate().toString().padStart(2, '0');
    const todayStr: string = `${year}-${month}-${day}`;
    // 用异步 DB 查询，完成后写回 AppStorage
    CheckInRepository.getInstance().getArticleIdsCheckedInOnDate(todayStr)
      .then((ids: Set<number>) => {
        const idArray: number[] = Array.from(ids);
        const idStrs: string[] = [];
        for (let i: number = 0; i < idArray.length; i++) {
          idStrs.push(idArray[i].toString());
        }
        const idsStr: string = idStrs.join(',');
        AppStorage.set('todayCheckedInIds', todayStr + '|' + idsStr);
      })
      .catch((e: Error) => {
        console.error('Home.syncTodayCheckedInIdsToStorage 失败: ' + JSON.stringify(e));
      });
  }

  /**
   * 同步判断某篇文章是否今日已打卡。
   * 直接解析 AppStorage 中的 todayCheckedInIds 字符串，
   * 不依赖任何异步操作，渲染时即时生效。
   */
  isArticleCheckedIn(articleId: number, itemCheckedIn: boolean): boolean {
    // 优先判断原始的 item.isCheckedIn（来自 daily_task_items 表）
    if (itemCheckedIn) {
      return true;
    }
    // 再从 AppStorage 字符串中解析
    const raw: string = this.todayCheckedInIds;
    if (raw.length === 0) {
      return false;
    }
    const pipeIdx: number = raw.indexOf('|');
    if (pipeIdx < 0) {
      return false;
    }
    const todayDate: Date = new Date();
    const year: number = todayDate.getFullYear();
    const month: string = (todayDate.getMonth() + 1).toString().padStart(2, '0');
    const day: string = todayDate.getDate().toString().padStart(2, '0');
    const todayStr: string = `${year}-${month}-${day}`;
    const recordDate: string = raw.substring(0, pipeIdx);
    if (recordDate !== todayStr) {
      return false; // 跨天
    }
    const idsPart: string = raw.substring(pipeIdx + 1);
    if (idsPart.length === 0) {
      return false;
    }
    const idStr: string = articleId.toString();
    // 用逗号包裹判断，避免子串匹配（如 1 匹配 12）
    return (',' + idsPart + ',').indexOf(',' + idStr + ',') >= 0;
  }

  aboutToShow(): void {
    // 每次页面显示时执行双重刷新：
    // 1. 先用轻量级刷新快速更新"已完成"状态（无闪烁）
    // 2. 再执行完整刷新确保所有数据一致
    // 关键：这样即便 Router.back() 后 aboutToShow 触发不稳定，
    // 从 AppStorage 信号来的刷新也已经在进行中。
    this.quickRefreshCheckedInStatus();
    this.loadDataWithOptionalLoading(true);
  }

  /**
   * 轻量级"仅更新打卡状态"刷新。
   * 只查询 check_in_records 表，就地更新 tasks 数组中每篇文章的
   * isCheckedIn 标记，不重新加载任务列表，速度快且无闪烁。
   */
  async quickRefreshCheckedInStatus(): Promise<void> {
    try {
      const todayDate: Date = new Date();
      const year: number = todayDate.getFullYear();
      const month: string = (todayDate.getMonth() + 1).toString().padStart(2, '0');
      const day: string = todayDate.getDate().toString().padStart(2, '0');
      const todayStr: string = `${year}-${month}-${day}`;

      const checkedInArticleIds: Set<number> =
        await CheckInRepository.getInstance().getArticleIdsCheckedInOnDate(todayStr);

      // 就地更新 tasks 数组中每篇文章的 isCheckedIn 标记
      let changed: boolean = false;
      for (let i: number = 0; i < this.tasks.length; i++) {
        const shouldBeChecked: boolean = this.tasks[i].isCheckedIn ||
          checkedInArticleIds.has(this.tasks[i].articleId);
        if (this.tasks[i].isCheckedIn !== shouldBeChecked) {
          this.tasks[i] = {
            taskId: this.tasks[i].taskId,
            articleId: this.tasks[i].articleId,
            articleTitle: this.tasks[i].articleTitle,
            wordTarget: this.tasks[i].wordTarget,
            isCheckedIn: shouldBeChecked,
            isRequired: this.tasks[i].isRequired,
            isLongArticle: this.tasks[i].isLongArticle,
            displayName: this.tasks[i].displayName,
            progressPercent: this.tasks[i].progressPercent
          };
          changed = true;
        }
      }

      if (changed) {
        // 重新计算统计数字
        let completedCount: number = 0;
        let requiredDone: number = 0;
        for (let i: number = 0; i < this.tasks.length; i++) {
          if (this.tasks[i].isCheckedIn) {
            completedCount++;
            if (this.tasks[i].isRequired) {
              requiredDone++;
            }
          }
        }
        this.completedTasksCount = completedCount;
        this.requiredCompleted = requiredDone;
      }
    } catch (e) {
      console.error('Home.quickRefreshCheckedInStatus 失败: ' + JSON.stringify(e));
    }
  }

  /**
   * 带可选 loading 状态的刷新
   * showLoading=true: 显示 loading，覆盖旧数据
   * showLoading=false: 不显示 loading，直接用新数据覆盖（无闪烁）
   */
  async loadDataWithOptionalLoading(showLoading: boolean): Promise<void> {
    const prevTasks = [...this.tasks];
    if (showLoading) {
      this.isLoading = true;
    }
    try {
      await ArticleRepository.getInstance().resetCheckInDaysIfNeeded();

      this.config = await ConfigRepository.getInstance().getConfig();
      const rateWordsPerMin: number = 250;
      this.targetWordsToday = this.config.dailyMinutes * rateWordsPerMin;

      const allArticles: Article[] = await ArticleRepository.getInstance().getAllArticles();
      console.info('Home.loadData: allArticles.length=' + allArticles.length);

      const dailyTaskService = DailyTaskService.getInstance();
      // 先检查是否有今日任务（依赖 count 字段，避免 items 查询异常误判）
      const hasTodayTasks = await dailyTaskService.hasTodayTasks();
      console.info('Home.loadData: hasTodayTasks=' + hasTodayTasks);

      let taskItems = await dailyTaskService.getOrGenerateTodayTasks(allArticles);
      console.info('Home.loadData: taskItems.length after getOrGenerate=' + taskItems.length);

      // 防御性修复：如果 hasTodayTasks 为 true 但 items 为空，
      // 说明 items 查询可能有异常——再尝试一次 getTodayTasks
      if (hasTodayTasks && taskItems.length === 0) {
        console.warn('Home.loadData: hasTodayTasks=true 但 taskItems 为空，重试 getTodayTasks');
        taskItems = await dailyTaskService.getTodayTasks();
        console.info('Home.loadData: 重试后 taskItems.length=' + taskItems.length);
      }

      // 关键修复：用今日打卡记录做交叉校验。
      // 即便 daily_task_items.isCheckedIn 仍为 0（用户在打卡完成前返回首页），
      // 只要 check_in_records 中存在这篇文章的今日记录，就视为已打卡。
      const todayDateForCheck: Date = new Date();
      const yearForCheck: number = todayDateForCheck.getFullYear();
      const monthForCheck: string = (todayDateForCheck.getMonth() + 1).toString().padStart(2, '0');
      const dayForCheck: string = todayDateForCheck.getDate().toString().padStart(2, '0');
      const todayStrForCheck: string = `${yearForCheck}-${monthForCheck}-${dayForCheck}`;
      const checkedInArticleIds: Set<number> =
        await CheckInRepository.getInstance().getArticleIdsCheckedInOnDate(todayStrForCheck);
      console.info('Home.loadData: 今日打卡文章数=' + checkedInArticleIds.size);

      this.tasks = [];
      for (let i = 0; i < taskItems.length; i++) {
        const item = taskItems[i];
        const article = allArticles.find(a => a.id === item.articleId);
        const display = item.displayName && item.displayName.length > 0
          ? item.displayName
          : (item.articleTitle || (article ? article.title : '未命名文章'));
        this.tasks.push({
          taskId: item.taskId,
          articleId: item.articleId,
          articleTitle: item.articleTitle || (article ? article.title : ''),
          wordTarget: item.wordTarget > 0 ? item.wordTarget : (article ? article.chineseChars : 0),
          isCheckedIn: item.isCheckedIn || checkedInArticleIds.has(item.articleId),
          isRequired: item.isRequired,
          isLongArticle: item.isLongArticle,
          displayName: display,
          progressPercent: article ? article.completionRate : 0
        });
      }
      console.info('Home.loadData: 最终构建 tasks.length=' + this.tasks.length
        + '，其中已完成=' + this.tasks.filter(t => t.isCheckedIn).length);

      const allCheckIns: CheckInRecord[] = await CheckInRepository.getInstance().getAllCheckInRecords();
      const todayDate: Date = new Date();
      const year: number = todayDate.getFullYear();
      const month: string = (todayDate.getMonth() + 1).toString().padStart(2, '0');
      const day: string = todayDate.getDate().toString().padStart(2, '0');
      const todayStr: string = `${year}-${month}-${day}`;

      let todayCount: number = 0;
      for (let j: number = 0; j < allCheckIns.length; j++) {
        if (allCheckIns[j].checkInDate === todayStr) {
          todayCount = todayCount + 1;
        }
      }
      this.todayCheckIns = todayCount;
      this.totalCheckIns = allCheckIns.length;

      let wordsInToday: number = 0;
      let completedInToday: number = 0;
      let requiredInToday: number = 0;
      let requiredDoneInToday: number = 0;

      for (let i = 0; i < this.tasks.length; i++) {
        const item = this.tasks[i];
        wordsInToday += item.wordTarget;
        if (item.isCheckedIn) {
          completedInToday++;
        }
        if (item.isRequired) {
          requiredInToday++;
          if (item.isCheckedIn) {
            requiredDoneInToday++;
          }
        }
      }

      this.totalWordsToday = wordsInToday;
      this.completedTasksCount = completedInToday;
      this.requiredTasksCount = requiredInToday;
      this.requiredCompleted = requiredDoneInToday;
      // === 关键修复 D: 同步计算 completedCount ===
      // 基于今日打卡记录集合计算，用于 build() 渲染时直接显示
      // 不再需要在 build() 中声明变量（ArkTS 不允许在 UI 组件后声明 let）
      const todayDateCount: Date = new Date();
      const yearCount: number = todayDateCount.getFullYear();
      const monthCount: string = (todayDateCount.getMonth() + 1).toString().padStart(2, '0');
      const dayCount: string = todayDateCount.getDate().toString().padStart(2, '0');
      const todayStrCount: string = `${yearCount}-${monthCount}-${dayCount}`;
      const checkedIds: Set<number> =
        await CheckInRepository.getInstance().getArticleIdsCheckedInOnDate(todayStrCount);
      let realCompleted: number = 0;
      for (let k: number = 0; k < this.tasks.length; k++) {
        const t: TaskItemUI = this.tasks[k];
        if (t.isCheckedIn || checkedIds.has(t.articleId)) {
          realCompleted++;
        }
      }
      this.completedCount = realCompleted;
    } catch (e) {
      console.error('加载首页数据失败: ' + JSON.stringify(e));
      // 恢复之前的数据，避免白屏
      if (prevTasks.length > 0) {
        this.tasks = prevTasks;
      }
    } finally {
      this.isLoading = false;
    }
  }

  // 监听预加载标志位
  onDailyTaskPreloadedChanged(): void {
    console.info('Home: 检测到预加载完成，刷新数据');
    this.loadDataWithOptionalLoading(true);
  }

  onRefreshSignalChanged(): void {
    console.info('Home: 检测到刷新信号，刷新数据');
    // 先走轻量级快速刷新（仅更新 isCheckedIn 标记），再走完整刷新，
    // 确保从 Reader 返回后能最快显示"已完成"状态
    this.quickRefreshCheckedInStatus();
    this.loadDataWithOptionalLoading(false);
  }

  onRefresh(): void {
    this.loadDataWithOptionalLoading(true);
  }

  // 原有 loadData 保持兼容
  async loadData(): Promise<void> {
    await this.loadDataWithOptionalLoading(true);
  }

  /**
   * 从今日任务列表中随机挑一篇未打卡的文章并打开阅读页面。
   * 用于 "今日任务" 行右侧的图书图标按钮。
   */
  openRandomUncheckedArticle(): void {
    const unchecked: TaskItemUI[] = [];
    for (let i: number = 0; i < this.tasks.length; i++) {
      const t: TaskItemUI = this.tasks[i];
      if (!this.isArticleCheckedIn(t.articleId, t.isCheckedIn)) {
        unchecked.push(t);
      }
    }
    if (unchecked.length === 0) {
      promptAction.showToast({ message: '所有文章都已完成', duration: 1500 });
      return;
    }
    const randomIdx: number = Math.floor(Math.random() * unchecked.length);
    const picked: TaskItemUI = unchecked[randomIdx];
    router.pushUrl({
      url: 'pages/Reader',
      params: { articleId: picked.articleId }
    });
  }

  @Builder
  TaskCard(item: TaskItemUI): void {
    // === 关键修复 C: 直接内联调用 isArticleCheckedIn() ===
    // 不声明中间变量，直接在 UI 属性链中调用。
    // ArkTS @Builder 不允许出现变量声明。
    Column() {
      Row() {
        Column() {
          Row() {
            Text(item.displayName)
              .fontSize(16)
              .fontWeight(FontWeight.Bold)
              .fontColor(this.isArticleCheckedIn(item.articleId, item.isCheckedIn) ? '#999999' : '#333333')
              .layoutWeight(1)
              .maxLines(2)
              .textOverflow({ overflow: TextOverflow.Ellipsis });
            if (this.isArticleCheckedIn(item.articleId, item.isCheckedIn)) {
              Text('已完成')
                .fontSize(10)
                .backgroundColor('#4CAF50')
                .fontColor('#FFFFFF')
                .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                .borderRadius(4)
                .margin({ left: 8 });
            }
          }
          .width('100%');
          Row() {
            Text(`${item.wordTarget}字`)
              .fontSize(12)
              .fontColor('#999999');
          }
          .width('100%')
          .margin({ top: 4 });
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1);

        if (this.isArticleCheckedIn(item.articleId, item.isCheckedIn)) {
          Text('✓')
            .fontSize(24)
            .fontColor('#4CAF50')
            .fontWeight(FontWeight.Bold);
        } else {
          Text('○')
            .fontSize(24)
            .fontColor('#E0E0E0');
        }
      }
      .width('100%');
    }
    .width('100%')
    .padding(16)
    .backgroundColor(this.isArticleCheckedIn(item.articleId, item.isCheckedIn) ? '#E9DEEE' : '#F5F5F5')
    .borderRadius(8)
    .onClick(() => {
      router.pushUrl({
        url: 'pages/Reader',
        params: { articleId: item.articleId }
      });
    });
  }

  build(): void {
    Column() {
      Row() {
        Text('每日阅读')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .layoutWeight(1);
      }
      .width('100%')
      .padding({ left: 16, right: 16, top: 16, bottom: 8 })
      .backgroundColor('#FFFFFF');

      if (this.isLoading) {
        Column() {
          LoadingProgress()
            .width(40)
            .height(40);
          Text('加载中...')
            .fontSize(14)
            .fontColor('#999999')
            .margin({ top: 12 });
        }
        .width('100%')
        .height('100%')
        .alignItems(HorizontalAlign.Center)
        .justifyContent(FlexAlign.Start)
        .padding({ top: 100 })
        .backgroundColor('#F5F5F5');
      } else {
        Scroll() {
          Column({ space: 16 }) {
            Column() {
              Row() {
                Text('今日目标')
                  .fontSize(16)
                  .fontWeight(FontWeight.Bold);
                Blank();
                Text(`${this.completedCount}/${this.tasks.length}`)
                  .fontSize(14)
                  .fontColor('#666666');
              }
              .width('100%');
              Row({ space: 12 }) {
                Column({ space: 4 }) {
                  Text(`${this.targetWordsToday}`)
                    .fontSize(16)
                    .fontColor('#1976D2')
                    .fontWeight(FontWeight.Bold);
                  Text('目标字数')
                    .fontSize(12)
                    .fontColor('#999999');
                }
                .layoutWeight(1);
                Column({ space: 4 }) {
                  Text(`${this.totalWordsToday}`)
                    .fontSize(16)
                    .fontColor('#333333')
                    .fontWeight(FontWeight.Bold);
                  Text('今日文章字数')
                    .fontSize(12)
                    .fontColor('#999999');
                }
                .layoutWeight(1);
                Column({ space: 4 }) {
                  Text(`${Math.round(this.config.targetCheckRate)}%`)
                    .fontSize(16)
                    .fontColor('#4CAF50')
                    .fontWeight(FontWeight.Bold);
                  Text('目标完成率')
                    .fontSize(12)
                    .fontColor('#999999');
                }
                .layoutWeight(1);
              }
              .width('100%')
              .margin({ top: 8 });

              if (this.requiredTasksCount > 0) {
                Row({ space: 8 }) {
                  Text(`必读:${this.requiredCompleted}/${this.requiredTasksCount}`)
                    .fontSize(12)
                    .fontColor('#D32F2F')
                    .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                    .backgroundColor('#FFEBEE')
                    .borderRadius(4);
                }
                .width('100%')
                .margin({ top: 8 });
              }
            }
            .width('100%')
            .padding(16)
            .backgroundColor('#FFFFFF')
            .borderRadius(8);

            Column({ space: 8 }) {
              Row() {
                Text('今日任务')
                  .fontSize(20)
                  .fontWeight(FontWeight.Bold);
                Blank();
                Row() {
                  // 图书图标 - 矢量图：一本打开的书
                  Text('📖')
                    .fontSize(22)
                    .fontColor('#333333');
                  Text('随机阅读')
                    .fontSize(12)
                    .fontColor('#666666')
                    .margin({ left: 4 });
                }
                .padding({ left: 10, right: 10, top: 6, bottom: 6 })
                .borderRadius(16)
                .backgroundColor('#F5F5F5')
                .onClick(() => {
                  this.openRandomUncheckedArticle();
                });
              }
              .width('100%');

              if (this.tasks.length === 0) {
                Column() {
                  Text('暂无文章，请先在文章管理中添加文章并标记为"阅读中"')
                    .fontSize(14)
                    .fontColor('#999999')
                    .textAlign(TextAlign.Center);
                }
                .width('100%')
                .alignItems(HorizontalAlign.Center)
                .margin({ top: 16, bottom: 16 });
              } else {
                ForEach(this.tasks, (item: TaskItemUI) => {
                  this.TaskCard(item);
                }, (item: TaskItemUI) => `${item.taskId}-${item.articleId}`);
              }
            }
            .width('100%')
            .padding(16)
            .backgroundColor('#FFFFFF')
            .borderRadius(8);
          }
          .width('100%')
          .alignItems(HorizontalAlign.Start)
          .padding({ bottom: 80 });
        }
        .scrollBar(BarState.On)
        .width('100%')
        .layoutWeight(1)
        .padding({ top: 16 })
        .backgroundColor('#F5F5F5')
        .scrollable(ScrollDirection.Vertical);
      }

      this.BottomTabBar();
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5');
  }

  @Builder
  BottomTabBar(): void {
    Row() {
      Column({ space: 2 }) {
        Text('●')
          .fontSize(18)
          .fontColor('#999999');
        Text('首页')
          .fontSize(11)
          .fontColor('#1976D2')
          .fontWeight(FontWeight.Bold);
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 });

      Column({ space: 2 }) {
        Text('▣')
          .fontSize(16)
          .fontColor('#999999');
        Text('背临床')
          .fontSize(11)
          .fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => {
        router.pushUrl({ url: 'pages/ClinicalStudy' });
      });

      Column({ space: 2 }) {
        Text('◈')
          .fontSize(16)
          .fontColor('#999999');
        Text('随心阅读')
          .fontSize(11)
          .fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => {
        router.pushUrl({ url: 'pages/RandomRead' });
      });

      Column({ space: 2 }) {
        Text('◆')
          .fontSize(16)
          .fontColor('#999999');
        Text('背穴位')
          .fontSize(11)
          .fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => {
        router.pushUrl({ url: 'pages/AcupointStudy' });
      });

      Column({ space: 2 }) {
        Text('◇')
          .fontSize(16)
          .fontColor('#999999');
        Text('背概念')
          .fontSize(11)
          .fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => {
        router.pushUrl({ url: 'pages/ConceptStudy' });
      });

      Column({ space: 2 }) {
        Text('⚙')
          .fontSize(16)
          .fontColor('#999999');
        Text('设置')
          .fontSize(11)
          .fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => {
        router.pushUrl({ url: 'pages/Settings' });
      });
    }
    .width('100%')
    .backgroundColor('#FFFFFF');
  }
}

import router from '@ohos.router';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';
import { CheckInRecord } from '../model/CheckInRecord';
import { CheckInRepository } from '../repository/CheckInRepository';
import { DailyTaskService } from '../service/DailyTaskService';
import { DailyTaskRepository, DailyTaskItem } from '../repository/DailyTaskRepository';
import { ConfigRepository } from '../repository/ConfigRepository';
import { Config } from '../model/Config';
import { SyncService } from '../service/SyncService';
import { ApiClient } from '../service/ApiClient';
import { OfflineWriteQueue } from '../service/OfflineWriteQueue';
import promptAction from '@ohos.promptAction';
import image from '@ohos.multimedia.image';
import { common } from '@kit.AbilityKit';
import { ImageCompressionService, SizedPixelMap } from '../service/ImageCompressionService';

interface TextSegment {
  text: string;
  type: 'normal' | 'annotation' | 'bold';
}

@Entry
@Component
struct ReaderPage {
  @State contentSegments: TextSegment[] = [];
  @State article: Article | null = null;
  @State articlePixelMap: image.PixelMap | null = null;
  @State articlePixelRatio: number = 1.0; // width / height，用于等比自适应
  @State articleImageWidth: number = 0; // 图片原始宽度
  @State articleImageHeight: number = 0; // 图片原始高度
  @State isLoading: boolean = true;
  @State isCheckedIn: boolean = false;
  @State showBars: boolean = false;
  @State fontSize: number = 26;
  @State timerText: string = '00:00';
  @State shouldShowContent: boolean = true; // iscontent=true 或无图时 true，纯图时 false（UI 渲染条件缓存）
  @State taskCheckedInCount: number = 0; // 今日任务已打卡数
  @State taskTotalCount: number = 0; // 今日任务总数
  private articleId: number = 0;
  private startTimestamp: number = 0;
  private timerHandle: number = -1;
  private lastClickSide: string = '';  // 双击检测：'left' | 'right' | ''
  private lastClickTime: number = 0;

  aboutToAppear(): void {
    const params: Record<string, Object> = router.getParams() as Record<string, Object>;
    if (params && params['articleId'] !== undefined && params['articleId'] !== null) {
      const idNum: number = Number(params['articleId']);
      if (!Number.isNaN(idNum)) {
        this.articleId = idNum;
      }
    }
    this.loadData();
  }

  aboutToDisappear(): void {
    this.stopTimer();
  }

  async loadData(): Promise<void> {
    this.isLoading = true;
    this.articlePixelMap = null;
    try {
      // 读取阅读默认字号配置
      try {
        const config: Config = await ConfigRepository.getInstance().getConfig();
        if (config.readerFontSize && config.readerFontSize > 0) {
          this.fontSize = config.readerFontSize;
        }
      } catch (cfgErr) {
        console.error('Reader: 读取字号配置失败: ' + JSON.stringify(cfgErr));
      }

      const allArticles: Article[] = await ArticleRepository.getInstance().getAllArticles();
      for (let i: number = 0; i < allArticles.length; i++) {
        if (allArticles[i].id === this.articleId) {
          this.article = allArticles[i];
          if (this.article.content) {
            try {
              this.contentSegments = this.parseContent(this.article.content);
            } catch (e) {
              console.error('parseContent failed: ' + JSON.stringify(e));
              this.contentSegments = [{ text: this.article.content, type: 'normal' }];
            }
          }
          break;
        }
      }

      // 解码文章图片（WebP base64 → PixelMap + 尺寸）用于 Image 组件渲染
      if (this.article !== null && this.article.imagewebp && this.article.imagewebp.length > 0) {
        try {
          const ctx: common.Context = getContext(this) as common.Context;
          const sized: SizedPixelMap = await ImageCompressionService.base64ToPixelMap(
            ctx, this.article.imagewebp
          );
          this.articlePixelMap = sized.pixelMap;
          this.articleImageWidth = sized.width;
          this.articleImageHeight = sized.height;
          if (sized.height > 0) {
            this.articlePixelRatio = sized.width / sized.height;
          } else {
            this.articlePixelRatio = 1.0;
          }
        } catch (imgErr) {
          console.error('Reader: 图片解码失败: ' + JSON.stringify(imgErr));
          this.articlePixelMap = null;
          this.articlePixelRatio = 1.0;
          this.articleImageWidth = 0;
          this.articleImageHeight = 0;
        }
      } else {
        this.articlePixelMap = null;
        this.articlePixelRatio = 1.0;
        this.articleImageWidth = 0;
        this.articleImageHeight = 0;
      }

      // 计算文章内容显示开关（在非 UI 区域计算，避免声明式 UI 块内出现普通 TS 语句报错）
      if (this.article !== null) {
        const noContentFlag: boolean = this.article.iscontent === false;
        const hasImage: boolean = this.articlePixelMap !== null;
        if (noContentFlag && !hasImage) {
          console.warn('Reader: article.iscontent=false 但无配图，已自动降级显示文字');
          this.shouldShowContent = true;
        } else if (noContentFlag && hasImage) {
          this.shouldShowContent = false;
        } else {
          this.shouldShowContent = true;
        }
      } else {
        this.shouldShowContent = true;
      }

      const todayDate: Date = new Date();
      const year: number = todayDate.getFullYear();
      const month: string = (todayDate.getMonth() + 1).toString().padStart(2, '0');
      const day: string = todayDate.getDate().toString().padStart(2, '0');
      const today: string = `${year}-${month}-${day}`;

      const allCheckIns: CheckInRecord[] = await CheckInRepository.getInstance().getAllCheckInRecords();
      for (let j: number = 0; j < allCheckIns.length; j++) {
        if (allCheckIns[j].articleId === this.articleId && allCheckIns[j].checkInDate === today) {
          this.isCheckedIn = true;
          break;
        }
      }

      // 加载今日任务统计
      try {
        const stats = await DailyTaskRepository.getInstance().getTodayTaskStats();
        this.taskTotalCount = stats.total;
        this.taskCheckedInCount = stats.checkedIn;
      } catch (statsErr) {
        console.error('Reader: 加载任务统计失败: ' + JSON.stringify(statsErr));
      }

      this.startTimer();
    } catch (e) {
      console.error('加载文章失败: ' + JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  startTimer(): void {
    this.startTimestamp = Date.now();
    this.updateTimerText();
    this.timerHandle = setInterval(() => {
      this.updateTimerText();
    }, 1000);
  }

  stopTimer(): void {
    if (this.timerHandle !== -1) {
      clearInterval(this.timerHandle);
      this.timerHandle = -1;
    }
  }

  parseContent(rawContent: string): TextSegment[] {
    const segments: TextSegment[] = [];
    let currentText: string = '';
    let state: 'normal' | 'annotation' | 'bold' = 'normal';

    let i: number = 0;
    while (i < rawContent.length) {
      if (state === 'normal') {
        if (i + 1 < rawContent.length && rawContent[i] === '#' && rawContent[i + 1] === '#') {
          if (currentText) {
            segments.push({ text: currentText, type: 'normal' });
            currentText = '';
          }
          state = 'annotation';
          i += 2;
        } else if (i + 1 < rawContent.length && rawContent[i] === '*' && rawContent[i + 1] === '*') {
          if (currentText) {
            segments.push({ text: currentText, type: 'normal' });
            currentText = '';
          }
          state = 'bold';
          i += 2;
        } else {
          currentText += rawContent[i];
          i++;
        }
      } else if (state === 'annotation') {
        if (i + 1 < rawContent.length && rawContent[i] === '#' && rawContent[i + 1] === '#') {
          if (currentText) {
            segments.push({ text: currentText, type: 'annotation' });
            currentText = '';
          }
          state = 'normal';
          i += 2;
        } else {
          currentText += rawContent[i];
          i++;
        }
      } else if (state === 'bold') {
        if (i + 1 < rawContent.length && rawContent[i] === '*' && rawContent[i + 1] === '*') {
          if (currentText) {
            segments.push({ text: currentText, type: 'bold' });
            currentText = '';
          }
          state = 'normal';
          i += 2;
        } else {
          currentText += rawContent[i];
          i++;
        }
      }
    }

    if (currentText) {
      segments.push({ text: currentText, type: 'normal' });
    }

    return segments;
  }

  updateTimerText(): void {
    const diffMs: number = Date.now() - this.startTimestamp;
    const totalSeconds: number = Math.floor(diffMs / 1000);
    const hours: number = Math.floor(totalSeconds / 3600);
    const minutes: number = Math.floor((totalSeconds % 3600) / 60);
    const seconds: number = totalSeconds % 60;
    if (hours > 0) {
      this.timerText = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
      this.timerText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
  }

  /**
   * 阅读区域点击处理：1秒内同侧连续点击2次 = 打卡，否则切换工具栏
   */
  handleArticleAreaClick(event: ClickEvent): void {
    // 已打卡或无文章，只切换工具栏
    if (this.isCheckedIn || this.article === null) {
      this.toggleBars();
      return;
    }

    const clickX: number = event.x;
    const componentWidth: number = Number(event.target.area.width);
    const side: string = clickX < componentWidth / 2 ? 'left' : 'right';
    const now: number = Date.now();

    if (this.lastClickSide === side && (now - this.lastClickTime) < 1000) {
      // 同侧1秒内连续2次点击 → 打卡
      this.lastClickSide = '';
      this.lastClickTime = 0;
      this.handleCheckIn();
    } else {
      // 首次点击或不同侧或超时 → 切换工具栏
      this.lastClickSide = side;
      this.lastClickTime = now;
      this.toggleBars();
    }
  }

  toggleBars(): void {
    this.showBars = !this.showBars;
  }

  hideBarsOnScroll(): void {
    if (this.showBars) {
      this.showBars = false;
    }
  }

  decreaseFontSize(): void {
    if (this.fontSize > 12) {
      this.fontSize = this.fontSize - 1;
    }
  }

  increaseFontSize(): void {
    if (this.fontSize < 60) {
      this.fontSize = this.fontSize + 1;
    }
  }

  /**
   * 打卡后调用：将文章打卡天数 +1 并重新计算完成率。
   * 关键优化：
   *  - UI 状态立即更新为"已打卡"（避免用户反复点击）
   *  - CheckInRecord 先写入（作为"已打卡"的最终依据）
   *  - 文章打卡天数更新与任务项标记并行执行（减少用户等待）
   *  - 不再强制导航返回——由用户决定何时点击返回；
   *    首页 aboutToShow 会通过 CheckInRecord 交叉校验自动识别为已打卡
   *  - 今日任务全部完成时，检查并触发自动 WebDAV 同步
   */
  async handleCheckIn(): Promise<void> {
    if (this.isCheckedIn || this.article === null) {
      return;
    }

    // 立即更新 UI，避免反复点击
    this.isCheckedIn = true;

    const todayDate: Date = new Date();
    const year: number = todayDate.getFullYear();
    const month: string = (todayDate.getMonth() + 1).toString().padStart(2, '0');
    const day: string = todayDate.getDate().toString().padStart(2, '0');
    const dateStr: string = `${year}-${month}-${day}`;

    try {
      // 1. 写入打卡记录（这是"已打卡"的最终依据，首页会据此做交叉校验）
      const record: CheckInRecord = new CheckInRecord();
      record.articleId = this.article.id;
      record.checkInDate = dateStr;
      record.checkInTime = dateStr;
      record.lastModified = new Date().toISOString();
      await CheckInRepository.getInstance().insertCheckInRecord(record);

      // === 关键修复 A: 立即写入 AppStorage 今日打卡文章 ID 列表 ===
      // 格式: "日期|id1,id2,id3"（带日期校验，跨天自动失效）
      // Home 页面用 @StorageLink 直接读取，不依赖 aboutToShow/@Watch
      const storageKey: string = 'todayCheckedInIds';
      const existingRaw: string = AppStorage.get(storageKey) || '';
      const pipeIdx: number = existingRaw.indexOf('|');
      const existingDate: string = pipeIdx >= 0 ? existingRaw.substring(0, pipeIdx) : '';
      let idsPart: string = '';
      if (existingDate === dateStr) {
        idsPart = pipeIdx >= 0 ? existingRaw.substring(pipeIdx + 1) : '';
      } else {
        idsPart = ''; // 跨天，重置列表
      }
      const newId: string = this.article.id.toString();
      // 如果该文章 ID 不在现有列表中，追加（用分隔符包裹避免子串匹配问题）
      const wrappedIds: string = ',' + idsPart + ',';
      if (wrappedIds.indexOf(',' + newId + ',') < 0) {
        const newIds: string = idsPart.length > 0 ? idsPart + ',' + newId : newId;
        AppStorage.set(storageKey, dateStr + '|' + newIds);
      }
      // 发信号给 Home（如果 @Watch 能触发的话也能刷新）
      AppStorage.set('dataRefreshSignal', Date.now().toString());

      // 2. 更新文章打卡天数（checkInDays +1，重新计算完成率）
      const localRate: number = await ArticleRepository.getInstance().incrementCheckInDays(this.article.id);

      // 3. 标记今日任务项中的对应文章为已打卡（若任务记录存在）
      const todayTask = await DailyTaskRepository.getInstance().getTodayTask();
      let finalRate: number = localRate;
      if (todayTask && todayTask.id && todayTask.id > 0) {
        await DailyTaskRepository.getInstance().markArticleChecked(todayTask.id, this.article.id);
        // 同步任务打卡状态到服务端（使用单条打卡接口，避免覆盖其他设备的打卡）
        // 服务端会重新计算完成率，返回最新值
        if (ApiClient.getInstance().isLoggedIn() && this.article.clientId) {
          try {
            const resp = await ApiClient.getInstance().checkinByArticle(this.article.clientId);
            if (resp.code === 0) {
              console.info('Reader.handleCheckIn: 打卡状态已同步到服务端');
              // 使用服务端返回的完成率（权威数据源）
              const data = resp.data as Record<string, Object> | null;
              if (data) {
                const serverRate = data['completionRate'] as number;
                const serverDays = data['checkInDays'] as number;
                if (serverRate !== undefined) {
                  finalRate = serverRate;
                  // 用服务端数据更新本地
                  await ArticleRepository.getInstance().updateCheckInDaysAndRate(
                    this.article.id, serverDays, serverRate);
                }
              }
            } else {
              console.warn('Reader.handleCheckIn: 打卡状态同步失败: ' + resp.message);
            }
          } catch (e) {
            console.warn('Reader.handleCheckIn: 打卡状态同步异常: ' + (e as Error).message);
          }
        }
      } else {
        console.warn('Reader.handleCheckIn: todayTask.id 无效，跳过 markArticleChecked');
      }

      // 再次发信号（保证完成率也更新）
      AppStorage.set('dataRefreshSignal', Date.now().toString());

      // 更新任务统计
      this.taskCheckedInCount = this.taskCheckedInCount + 1;

      promptAction.showToast({ message: `打卡成功，完成率 ${finalRate}%`, duration: 1300 });

      // 4. 延迟检查：未完成则自动打开下一篇未完成文章，已完成则返回首页并同步
      setTimeout(() => {
        AppStorage.set('dataRefreshSignal', Date.now().toString());
        this.checkAndAutoContinueOrSync();
      }, 2000);
    } catch (e) {
      this.isCheckedIn = false;
      console.error('打卡失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '打卡失败，请重试', duration: 2000 });
    }
  }

  /**
   * 打卡后检查今日任务状态：
   * - 未全部完成：自动随机打开下一篇未完成的文章
   * 全部完成：返回首页并触发 WebDAV 同步
   */
  async checkAndAutoContinueOrSync(): Promise<void> {
    try {
      const todayTask = await DailyTaskRepository.getInstance().getTodayTask();
      if (!todayTask || !todayTask.items || todayTask.items.length === 0) {
        // 无今日任务，返回首页
        router.back();
        return;
      }

      // 收集未完成的文章项
      const uncheckedItems: DailyTaskItem[] = [];
      for (let i = 0; i < todayTask.items.length; i++) {
        if (!todayTask.items[i].isCheckedIn) {
          uncheckedItems.push(todayTask.items[i]);
        }
      }

      if (uncheckedItems.length > 0) {
        // 随机选一篇未完成的文章，替换当前页面为新 Reader
        const randomIndex: number = Math.floor(Math.random() * uncheckedItems.length);
        const nextArticleId: number = uncheckedItems[randomIndex].articleId;
        console.info(`Reader: 今日任务未全部完成（剩 ${uncheckedItems.length} 篇），自动打开下一篇 id=${nextArticleId}`);
        router.replaceUrl({ url: 'pages/Reader', params: { articleId: nextArticleId } });
      } else {
        // 全部完成，返回首页并触发 WebDAV 同步
        console.info('Reader: 今日任务已全部完成，返回首页并触发同步');
        this.checkAndTriggerAutoWebDavSync();
        router.back();
      }
    } catch (e) {
      console.error('Reader.checkAndAutoContinueOrSync 异常: ' + JSON.stringify(e));
      router.back();
    }
  }

  /**
   * 打卡后自动云同步。
   * 离线写队列会自动上报，这里触发一次增量拉取。
   */
  async checkAndTriggerAutoWebDavSync(): Promise<void> {
    const TAG: string = 'Reader.CloudSync';
    const startTime: number = Date.now();
    console.info(`[${TAG}] 触发打卡后云同步`);
    try {
      // 离线写队列已在 incrementCheckInDays 中入队，这里触发一次增量拉取
      const merged = await SyncService.getInstance().pullArticles();
      console.info(`[${TAG}] 云同步完成，合并 ${merged} 篇，耗时 ${Date.now() - startTime}ms`);
    } catch (e) {
      console.error(`[${TAG}] 云同步异常: ` + JSON.stringify(e));
    }
  }

  /**
   * 获取今天的日期字符串，格式: "2026-06-19"
   */
  private getTodayDateString(): string {
    const d: Date = new Date();
    const year: number = d.getFullYear();
    const month: string = (d.getMonth() + 1).toString().padStart(2, '0');
    const day: string = d.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  build(): void {
    Stack() {
      Column() {
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
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#FFFFFF');
        } else {
          if (this.article !== null) {
            Scroll() {
              Column() {
                // ====== 显示文章文字段（iscontent=true 或无图时强制显示）======
                // 注意：iscontent=false 但无图时自动降级为显示文字，避免空白页面
                if (this.shouldShowContent) {
                  Row() {
                    Text(this.article.title)
                      .fontSize(this.fontSize + 6)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#333333')
                      .layoutWeight(1)
                      .maxLines(2)
                      .textOverflow({ overflow: TextOverflow.Ellipsis })
                      .textAlign(TextAlign.Start);

                    if (this.taskTotalCount > 0) {
                      Text(`${this.taskCheckedInCount}/${this.taskTotalCount}`)
                        .fontSize(14)
                        .fontColor('#E53935')
                        .fontWeight(FontWeight.Medium)
                        .margin({ left: 8, bottom: 4 });
                    }
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Bottom)
                  .margin({ bottom: 8 });

                  Text(`${this.article.chineseChars} 字`)
                    .fontSize(12)
                    .fontColor('#999999')
                    .margin({ bottom: 16 })
                    .width('100%');

                  Text() {
                      ForEach(this.contentSegments, (segment: TextSegment, index: number) => {
                        Span(segment.text)
                          .fontSize(segment.type === 'annotation' ? this.fontSize - 4 : this.fontSize)
                          .fontColor(segment.type === 'annotation' ? '#FF0000' : '#333333')
                          .fontWeight(segment.type === 'bold' ? FontWeight.Bold : FontWeight.Normal);
                      }, (index: number) => `segment_${index}`)
                    }
                    .fontSize(this.fontSize)
                    .fontColor('#333333')
                    .lineHeight(this.fontSize * 1.8)
                    .width('100%')
                    .textAlign(TextAlign.Start);
                }

                // ===== 文章图片（WebP）=====
                // 如果图片原始宽度小于500px，显示原尺寸
                // 如果图片原始宽度大于等于500px，宽度100%，高度按原比例自适应
                if (this.articlePixelMap !== null) {
                  if (this.articleImageWidth > 0 && this.articleImageWidth < 500) {
                    // 图片宽度小于500px，使用原始尺寸居中显示
                    Row() {
                      Image(this.articlePixelMap)
                        .width(this.articleImageWidth)
                        .height(this.articleImageHeight)
                        .objectFit(ImageFit.Fill)
                        .borderRadius(8)
                        .backgroundColor('#F5F5F5');
                    }
                    .width('100%')
                    .justifyContent(FlexAlign.Center)
                    .margin({ top: this.shouldShowContent ? 24 : 0 });
                  } else {
                    // 图片宽度大于等于500px，宽度100%，高度按比例自适应
                    Image(this.articlePixelMap)
                      .width('100%')
                      .aspectRatio(this.articlePixelRatio)
                      .margin({ top: this.shouldShowContent ? 24 : 0 })
                      .borderRadius(8)
                      .objectFit(ImageFit.Auto)
                      .backgroundColor('#F5F5F5');
                  }
                }

                Column() {
                  if (this.isCheckedIn) {
                    Text('✓ 今日已打卡')
                      .fontSize(16)
                      .fontColor('#4CAF50')
                      .fontWeight(FontWeight.Bold)
                      .padding({ left: 24, right: 24, top: 12, bottom: 12 })
                      .backgroundColor('#E8F5E9')
                      .borderRadius(8);
                  } else {
                    Text('打卡此文章')
                      .fontSize(16)
                      .fontColor('#FFFFFF')
                      .fontWeight(FontWeight.Bold)
                      .padding({ left: 24, right: 24, top: 12, bottom: 12 })
                      .backgroundColor('#4CAF50')
                      .borderRadius(8)
                      .onClick(() => {
                        this.handleCheckIn();
                      });
                  }
                }
                .width('100%')
                .margin({ top: 32, bottom: 32 })
                .alignItems(HorizontalAlign.Center);
              }
              .width('100%')
              .alignItems(HorizontalAlign.Start)
              .padding(16);
            }
            .layoutWeight(1)
            .scrollBar(BarState.Auto)
            .width('100%')
            .align(Alignment.Top)
            .backgroundColor('#FFFFFF')
            .onScroll(() => {
              this.hideBarsOnScroll();
            })
            .onClick((event: ClickEvent) => {
              this.handleArticleAreaClick(event);
            });
          } else {
            Column() {
              Text('文章未找到')
                .fontSize(16)
                .fontColor('#999999');
            }
            .width('100%')
            .layoutWeight(1)
            .justifyContent(FlexAlign.Center)
            .backgroundColor('#FFFFFF');
          }
        }
      }
      .width('100%')
      .height('100%');

      if (this.showBars) {
        Column() {
          Row() {
            Row() {
              Text('←')
                .fontSize(22)
                .fontColor('#333333')
                .margin({ right: 8 });
              Text(this.article !== null ? this.article.title : '')
                .fontSize(16)
                .fontColor('#333333')
                .fontWeight(FontWeight.Medium)
                .maxLines(1)
                .textOverflow({ overflow: TextOverflow.Ellipsis })
                .layoutWeight(1);
            }
            .layoutWeight(1)
            .onClick(() => {
              AppStorage.set('dataRefreshSignal', Date.now().toString());
              router.back();
            });

            Text(this.timerText)
              .fontSize(16)
              .fontColor('#1976D2')
              .fontWeight(FontWeight.Bold)
              .margin({ left: 12 });
          }
          .width('100%')
          .padding({ left: 16, right: 16, top: 16, bottom: 16 })
          .backgroundColor('#FFFFFF');
        }
        .width('100%')
        .position({ x: 0, y: 0 });
      }

      if (this.showBars) {
        Column() {
          Row() {
            Text('A-')
              .fontSize(20)
              .fontColor('#333333')
              .padding({ left: 20, right: 20, top: 12, bottom: 12 })
              .onClick(() => {
                this.decreaseFontSize();
              });

            Text(this.fontSize.toString())
              .fontSize(18)
              .fontColor('#1976D2')
              .fontWeight(FontWeight.Bold)
              .layoutWeight(1)
              .textAlign(TextAlign.Center);

            Text('A+')
              .fontSize(20)
              .fontColor('#333333')
              .padding({ left: 20, right: 20, top: 12, bottom: 12 })
              .onClick(() => {
                this.increaseFontSize();
              });

            Text('编辑')
              .fontSize(14)
              .fontColor('#1976D2')
              .fontWeight(FontWeight.Medium)
              .padding({ left: 16, right: 4, top: 12, bottom: 12 })
              .onClick(() => {
                if (this.article !== null) {
                  router.pushUrl({ url: 'pages/ArticleManage', params: { editArticleId: this.article.id } });
                }
              });
          }
          .width('100%')
          .padding({ left: 16, right: 16, top: 12, bottom: 12 })
          .backgroundColor('#FFFFFF');
        }
        .width('100%')
        .position({ x: 0, y: '100%' })
        .translate({ y: '-100%' });
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#FFFFFF');
  }
}

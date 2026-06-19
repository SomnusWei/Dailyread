import router from '@ohos.router';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';
import { CheckInRecord } from '../model/CheckInRecord';
import { CheckInRepository } from '../repository/CheckInRepository';
import { DailyTaskService } from '../service/DailyTaskService';
import { DailyTaskRepository } from '../repository/DailyTaskRepository';
import { ConfigRepository } from '../repository/ConfigRepository';
import { Config } from '../model/Config';
import { WebDavSyncService } from '../service/WebDavSyncService';
import promptAction from '@ohos.promptAction';
import image from '@ohos.multimedia.image';
import { common } from '@kit.AbilityKit';
import { ImageCompressionService, SizedPixelMap } from '../service/ImageCompressionService';

@Entry
@Component
struct ReaderPage {
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
  private articleId: number = 0;
  private startTimestamp: number = 0;
  private timerHandle: number = -1;

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
      const allArticles: Article[] = await ArticleRepository.getInstance().getAllArticles();
      for (let i: number = 0; i < allArticles.length; i++) {
        if (allArticles[i].id === this.articleId) {
          this.article = allArticles[i];
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
      const rate: number = await ArticleRepository.getInstance().incrementCheckInDays(this.article.id);

      // 3. 标记今日任务项中的对应文章为已打卡（若任务记录存在）
      const todayTask = await DailyTaskRepository.getInstance().getTodayTask();
      if (todayTask && todayTask.id && todayTask.id > 0) {
        await DailyTaskRepository.getInstance().markArticleChecked(todayTask.id, this.article.id);
      } else {
        console.warn('Reader.handleCheckIn: todayTask.id 无效，跳过 markArticleChecked');
      }

      // 再次发信号（保证完成率也更新）
      AppStorage.set('dataRefreshSignal', Date.now().toString());

      promptAction.showToast({ message: `打卡成功，完成率 ${rate}%`, duration: 2000 });

      // 4. 检查是否今日全部完成，触发自动 WebDAV 同步
      this.checkAndTriggerAutoWebDavSync();
    } catch (e) {
      this.isCheckedIn = false;
      console.error('打卡失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '打卡失败，请重试', duration: 2000 });
    }
  }

  /**
   * 检查今日任务是否全部完成，如果是则触发自动 WebDAV 同步
   * 仅同步一次，跨天后可再次触发
   */
  async checkAndTriggerAutoWebDavSync(): Promise<void> {
    try {
      // 1. 检查 WebDAV 自动同步是否开启
      const config: Config = await ConfigRepository.getInstance().getConfig();
      if (!config.autoSyncWebDav) {
        console.info('Reader: WebDAV 自动同步未开启，跳过');
        return;
      }
      if (!config.webdavUrl || !config.webdavUsername || !config.webdavPassword) {
        console.info('Reader: WebDAV 配置不完整，跳过自动同步');
        return;
      }

      // 2. 检查今天是否已自动同步过（用 AppStorage 存储标记）
      const todayStr: string = this.getTodayDateString();
      const autoSyncKey: string = 'autoWebDavSynced_' + todayStr;
      const alreadySynced: boolean = AppStorage.get(autoSyncKey) === 'true';
      if (alreadySynced) {
        console.info('Reader: 今日已自动同步 WebDAV，跳过');
        return;
      }

      // 3. 获取今日任务列表和打卡情况
      const todayTask = await DailyTaskRepository.getInstance().getTodayTask();
      if (!todayTask || !todayTask.items || todayTask.items.length === 0) {
        console.info('Reader: 无今日任务，跳过自动同步');
        return;
      }

      // 4. 查询今日已打卡数量
      const checkedInIds: Set<number> = await CheckInRepository.getInstance()
        .getArticleIdsCheckedInOnDate(todayStr);
      const checkedInCount: number = checkedInIds.size;
      const totalCount: number = todayTask.items.length;

      // 5. 判断是否全部完成
      if (checkedInCount < totalCount) {
        console.info(`Reader: 今日任务 ${checkedInCount}/${totalCount}，未全部完成，跳过自动同步`);
        return;
      }

      // 6. 全部完成，执行 WebDAV 同步
      console.info('Reader: 今日任务全部完成，触发自动 WebDAV 同步');

      const syncService: WebDavSyncService = WebDavSyncService.getInstance();
      const syncConfig: Config = new Config();
      syncConfig.webdavUrl = config.webdavUrl;
      syncConfig.webdavUsername = config.webdavUsername;
      syncConfig.webdavPassword = config.webdavPassword;
      syncConfig.webdavRemotePath = config.webdavRemotePath || '/DailyRead';
      syncConfig.syncArticlesEnabled = config.syncArticlesEnabled ?? true;
      syncConfig.syncConceptsEnabled = config.syncConceptsEnabled ?? true;
      syncConfig.syncClinicalNotesEnabled = config.syncClinicalNotesEnabled ?? true;

      const result = await syncService.syncToRemote(syncConfig);

      if (result.success) {
        // 7. 标记今天已完成自动同步
        AppStorage.set(autoSyncKey, 'true');
        console.info(`Reader: 自动 WebDAV 同步成功，上传 ${result.uploadedArticles} 篇文章`);
        promptAction.showToast({ message: '数据已自动备份到云端', duration: 2000 });
      } else {
        console.error('Reader: 自动 WebDAV 同步失败: ' + result.errorMessage);
      }
    } catch (e) {
      console.error('Reader.checkAndTriggerAutoWebDavSync 异常: ' + JSON.stringify(e));
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
                Text(this.article.title)
                  .fontSize(this.fontSize + 6)
                  .fontWeight(FontWeight.Bold)
                  .fontColor('#333333')
                  .margin({ bottom: 8 })
                  .width('100%')
                  .textAlign(TextAlign.Start);

                Text(`${this.article.chineseChars} 字`)
                  .fontSize(12)
                  .fontColor('#999999')
                  .margin({ bottom: 16 })
                  .width('100%');

                Text(this.article.content)
                  .fontSize(this.fontSize)
                  .fontColor('#333333')
                  .lineHeight(this.fontSize * 1.8)
                  .width('100%')
                  .textAlign(TextAlign.Start);

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
                    .margin({ top: 24 });
                  } else {
                    // 图片宽度大于等于500px，宽度100%，高度按比例自适应
                    Image(this.articlePixelMap)
                      .width('100%')
                      .aspectRatio(this.articlePixelRatio)
                      .margin({ top: 24 })
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
            .onClick(() => {
              this.toggleBars();
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
              // 关键修复 #3: 用 replaceUrl 替代 back，强制 Home 页面重建
              // （避免 router.back() 后 Home 的 aboutToShow/@Watch 不触发的问题）
              AppStorage.set('dataRefreshSignal', Date.now().toString());
              router.replaceUrl({ url: 'pages/Home' });
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

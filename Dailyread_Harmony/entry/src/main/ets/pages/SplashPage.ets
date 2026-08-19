import router from '@ohos.router';
import common from '@ohos.app.ability.common';
import { ConfigRepository } from '../repository/ConfigRepository';
import { ArticleRepository } from '../repository/ArticleRepository';
import { DailyTaskService } from '../service/DailyTaskService';
import { ApiClient } from '../service/ApiClient';
import { SyncService } from '../service/SyncService';
import { OfflineWriteQueue } from '../service/OfflineWriteQueue';
import { AppDatabase } from '../database/AppDatabase';

/**
 * 启动过渡页
 * 功能：
 * 1. 初始化数据库
 * 2. 预加载今日任务（数据库中存在则直接使用，否则生成新的）
 * 3. 云端同步：文章、打卡、配置、任务全量同步
 * 4. 逐字显示文言文（PPT效果），3秒内完成
 * 5. 完成后跳转到首页
 */
@Entry
@Component
struct SplashPage {
  @State displayText: string = '凡大医治病，必当安神定志，无欲无求，先发大慈恻隐之心，誓愿普救含灵之苦。若有疾厄来求救者，不得问其贵贱贫富……';
  @State finishLoading: boolean = false;
  @State initMessage: string = '正在准备今日阅读…';
  @State statusMsg: string = '';

  private context: common.Context = getContext(this) as common.Context;
  private readonly totalDuration: number = 3000; // 3秒
  private navTimerHandle: number = -1;
  private navigated: boolean = false; // 防止重复跳转
  private isLoggedIn: boolean = false;

  aboutToAppear(): void {
    console.info('SplashPage: 启动过渡页开始');

    // 启动定时跳转（3秒后跳转到首页）
    this.startTimer();

    // 并行执行初始化与预加载
    this.initializeAndPreload();
  }

  aboutToDisappear(): void {
    if (this.navTimerHandle !== -1) {
      clearTimeout(this.navTimerHandle);
      this.navTimerHandle = -1;
    }
  }

  /**
   * 初始化与预加载任务
   */
  private async initializeAndPreload(): Promise<void> {
    try {
      // 重置预加载标志位，确保 Home 会重新加载
      AppStorage.set('dailyTaskPreloaded', false);

      // 1. 初始化数据库
      this.initMessage = '正在初始化数据库…';
      await AppDatabase.getInstance().init(this.context);
      console.info('SplashPage: AppDatabase 初始化完成');

      // 2. 初始化 API 客户端 + 离线队列
      this.initMessage = '正在初始化账号…';
      const api = ApiClient.getInstance();
      await api.init(this.context);
      OfflineWriteQueue.getInstance().init(this.context);

      // 3. 检查登录态，未登录则跳转登录页
      this.isLoggedIn = api.isLoggedIn();
      if (!this.isLoggedIn) {
        console.info('SplashPage: 未登录，跳转登录页');
        this.navigated = true;
        if (this.navTimerHandle !== -1) {
          clearTimeout(this.navTimerHandle);
          this.navTimerHandle = -1;
        }
        router.replaceUrl({ url: 'pages/Login' });
        return;
      }

      // 4. 设置401冲突回调
      api.setConflictCallback((msg: string) => {
        this.statusMsg = msg;
      });

      // 5. 加载配置（确保默认配置存在）
      this.initMessage = '正在加载配置…';
      await ConfigRepository.getInstance().getConfig();
      console.info('SplashPage: ConfigRepository 完成');

      // 6. 云端全量同步
      this.initMessage = '正在同步数据…';
      try {
        const syncService = SyncService.getInstance();
        syncService.start();

        // 6a. 拉取文章增量
        const merged = await syncService.pullArticles();
        if (merged > 0) {
          console.info('SplashPage: 文章同步成功，合并 ' + merged + ' 篇文章');
        }

        // 6b. 拉取打卡记录
        const checkinsMerged = await syncService.pullCheckins();
        if (checkinsMerged > 0) {
          console.info('SplashPage: 打卡同步成功，合并 ' + checkinsMerged + ' 条记录');
        }

        // 6c. 拉取配置（keepScreenOn保持本地）
        const configSynced = await syncService.pullConfig();
        if (configSynced) {
          console.info('SplashPage: 配置同步成功');
        }

        // 6d. 拉取今日任务
        const tasksSynced = await syncService.pullTodayTasks();
        if (tasksSynced) {
          console.info('SplashPage: 今日任务同步成功');
        }

        // 6e. 推送本地配置（确保多端一致，不推送任务以避免覆盖其他设备打卡）
        await syncService.pushConfig();

        console.info('SplashPage: 全量同步完成');
      } catch (e) {
        console.error('SplashPage: 云同步失败: ' + JSON.stringify(e));
      }

      // 7. 重新加载配置（可能被服务端更新）
      this.initMessage = '正在读取配置…';
      const updatedConfig = await ConfigRepository.getInstance().getConfig();

      // 8. 加载所有文章
      this.initMessage = '正在读取文章库…';
      const allArticles = await ArticleRepository.getInstance().getAllArticles();
      console.info('SplashPage: 已加载文章数=' + allArticles.length);

      // 9. 预加载今日任务
      this.initMessage = '正在生成今日阅读列表…';
      const tasks = await DailyTaskService.getInstance().getOrGenerateTodayTasks(allArticles);
      console.info('SplashPage: 预加载任务完成，数量=' + tasks.length);

      // 10. 保存最终配置
      await ConfigRepository.getInstance().updateConfig(updatedConfig);

      this.finishLoading = true;
      this.initMessage = '准备就绪';

      // 通知首页：今日任务已预加载就绪
      AppStorage.set('dailyTaskPreloaded', true);
      console.info('SplashPage: 预加载标志位已设置');

      // 如果定时器还没触发，这里标记已导航，防止后续重复跳转
      // （导航仍由定时器统一触发，保证过渡页动画完整）
    } catch (e) {
      console.error('SplashPage: 初始化失败: ' + JSON.stringify(e));
      this.initMessage = '初始化失败，将继续进入首页';
      this.finishLoading = true;
      // 即使失败也允许进入首页
      AppStorage.set('dailyTaskPreloaded', true);
    }
  }

  /**
   * 启动定时跳转
   */
  private startTimer(): void {
    this.navTimerHandle = setTimeout(() => {
      // 如果初始化已完成且已登录，跳转首页
      if (this.finishLoading && this.isLoggedIn && !this.navigated) {
        this.navigateToHome();
      } else if (!this.navigated) {
        // 初始化未完成时，延迟再检查一次
        this.navTimerHandle = setTimeout(() => {
          if (this.isLoggedIn && !this.navigated) {
            this.navigateToHome();
          } else if (!this.isLoggedIn && !this.navigated) {
            // 仍未登录，跳转登录页
            this.navigated = true;
            router.replaceUrl({ url: 'pages/Login' });
          }
        }, 2000);
      }
    }, this.totalDuration);
  }

  /**
   * 跳转到首页
   */
  private navigateToHome(): void {
    if (this.navTimerHandle !== -1) {
      clearTimeout(this.navTimerHandle);
      this.navTimerHandle = -1;
    }
    if (this.navigated) {
      return;
    }
    this.navigated = true;
    console.info('SplashPage: 动画完成，跳转首页');
    router.replaceUrl({ url: 'pages/Home' });
  }

  build(): void {
    Stack() {
      // 背景渐变
      Column() {
        // 顶部 logo / 标题
        Column() {
          Text('每日阅读')
            .fontSize(36)
            .fontWeight(FontWeight.Bold)
            .fontColor('#FFFFFF')
            .margin({ top: 120 });

          Text('Daily Reading')
            .fontSize(14)
            .fontColor('#FFFFFFCC')
            .margin({ top: 8 });

          // 文言文（直接显示在标题下方）
          Text(this.displayText)
            .fontSize(14)
            .fontColor('#FFFFFFCC')
            .lineHeight(24)
            .textAlign(TextAlign.Center)
            .padding({ left: 32, right: 32 })
            .margin({ top: 16 });
        }
        .width('100%')
        .alignItems(HorizontalAlign.Center);

        Blank();

        // 底部：加载状态
        Column() {
          if (!this.finishLoading) {
            LoadingProgress()
              .width(28)
              .height(28)
              .color('#FFFFFF');
            Text(this.initMessage)
              .fontSize(13)
              .fontColor('#FFFFFFCC')
              .margin({ top: 8 });
          } else {
            Text(this.initMessage)
              .fontSize(13)
              .fontColor('#FFFFFFCC');
          }
        }
        .width('100%')
        .height(80)
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
        .margin({ bottom: 80 });
      }
      .width('100%')
      .height('100%')
      .linearGradient({
        angle: 180,
        colors: [['#1976D2', 0.0], ['#0D47A1', 1.0]]
      });
    }
    .width('100%')
    .height('100%');
  }
}

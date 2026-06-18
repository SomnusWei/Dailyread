import router from '@ohos.router';
import common from '@ohos.app.ability.common';
import { ConfigRepository } from '../repository/ConfigRepository';
import { ArticleRepository } from '../repository/ArticleRepository';
import { DailyTaskService } from '../service/DailyTaskService';
import { AppDatabase } from '../database/AppDatabase';

/**
 * 启动过渡页
 * 功能：
 * 1. 初始化数据库
 * 2. 预加载今日任务（数据库中存在则直接使用，否则生成新的）
 * 3. 逐字显示文言文（PPT效果），3秒内完成
 * 4. 完成后跳转到首页
 */
@Entry
@Component
struct SplashPage {
  @State displayText: string = '凡大医治病，必当安神定志，无欲无求，先发大慈恻隐之心，誓愿普救含灵之苦。若有疾厄来求救者，不得问其贵贱贫富……';
  @State finishLoading: boolean = false;
  @State initMessage: string = '正在准备今日阅读…';

  private context: common.Context = getContext(this) as common.Context;
  private readonly totalDuration: number = 3000; // 3秒
  private navTimerHandle: number = -1;

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

      // 2. 加载配置（确保默认配置存在）
      this.initMessage = '正在加载配置…';
      await ConfigRepository.getInstance().getConfig();
      console.info('SplashPage: ConfigRepository 完成');

      // 3. 加载所有文章
      this.initMessage = '正在读取文章库…';
      const allArticles = await ArticleRepository.getInstance().getAllArticles();
      console.info('SplashPage: 已加载文章数=' + allArticles.length);

      // 4. 预加载今日任务（关键步骤）
      // 数据库中无今日记录 -> 自动生成 -> 写入数据库
      this.initMessage = '正在生成今日阅读列表…';
      const tasks = await DailyTaskService.getInstance().getOrGenerateTodayTasks(allArticles);
      console.info('SplashPage: 预加载任务完成，数量=' + tasks.length);

      this.finishLoading = true;
      this.initMessage = '准备就绪';

      // 通知首页：今日任务已预加载就绪
      AppStorage.set('dailyTaskPreloaded', true);
      console.info('SplashPage: 预加载标志位已设置');
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
      this.navigateToHome();
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

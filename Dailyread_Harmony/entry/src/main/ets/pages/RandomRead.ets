import router from '@ohos.router';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';

@Entry
@Component
struct RandomReadPage {
  @State article: Article | null = null;
  @State isLoading: boolean = true;
  private currentArticleId: number = -1;

  // ===== 全局数据刷新监听（和其他页面保持一致）=====
  @Watch('onRefreshSignalChanged')
  @StorageProp('dataRefreshSignal') refreshSignal: string = '';

  aboutToAppear(): void {
    this.loadRandomArticle();
  }

  aboutToShow(): void {
    this.loadRandomArticle();
  }

  onRefreshSignalChanged(): void {
    this.loadRandomArticle();
  }

  async loadRandomArticle(): Promise<void> {
    this.isLoading = true;
    try {
      const pausedArticles: Article[] = await ArticleRepository.getInstance().getPausedArticles();
      if (pausedArticles.length === 0) {
        this.article = null;
        this.currentArticleId = -1;
      } else if (pausedArticles.length === 1) {
        this.article = pausedArticles[0];
        this.currentArticleId = pausedArticles[0].id;
      } else {
        // 过滤掉当前文章，避免重复
        const candidates: Article[] = [];
        for (let i: number = 0; i < pausedArticles.length; i++) {
          if (pausedArticles[i].id !== this.currentArticleId) {
            candidates.push(pausedArticles[i]);
          }
        }
        let pool: Article[] = candidates;
        if (pool.length === 0) {
          pool = pausedArticles;
        }
        const randomIndex: number = Math.floor(Math.random() * pool.length);
        this.article = pool[randomIndex];
        this.currentArticleId = pool[randomIndex].id;
      }
    } catch (e) {
      console.error('加载随机文章失败: ' + JSON.stringify(e));
      this.article = null;
      this.currentArticleId = -1;
    } finally {
      this.isLoading = false;
    }
  }

  build(): void {
    Column() {
      // 顶部栏
      Row() {
        Text('随心阅读')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .padding({ left: 16, right: 16, top: 16, bottom: 8 });
        Blank();
      }
      .width('100%')
      .backgroundColor('#FFFFFF');

      // 内容区域（Stack 用来把刷新按钮叠在内容右下角）
      Stack({ alignContent: Alignment.BottomEnd }) {
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
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#FAFAFA');
        } else if (this.article === null) {
          Column() {
            Text('暂无暂停阅读的文章')
              .fontSize(16)
              .fontColor('#999999');
            Text('请先在文章管理中暂停一些文章')
              .fontSize(14)
              .fontColor('#CCCCCC')
              .margin({ top: 8 });
          }
          .width('100%')
          .height('100%')
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#FAFAFA');
        } else {
          Scroll() {
            Column() {
              Text(this.article.title)
                .fontSize(22)
                .fontWeight(FontWeight.Bold)
                .fontColor('#333333')
                .margin({ bottom: 8 })
                .width('100%');

              Text(`${this.article.chineseChars} 字`)
                .fontSize(12)
                .fontColor('#999999')
                .margin({ bottom: 16 })
                .width('100%');

              Text(this.article.content)
                .fontSize(16)
                .fontColor('#333333')
                .lineHeight(24)
                .width('100%')
                .textAlign(TextAlign.Start);

              Column()
                .height(72)
                .width('100%');
            }
            .width('100%')
            .padding(16)
            .alignItems(HorizontalAlign.Start)
            .justifyContent(FlexAlign.Start);
          }
          .scrollBar(BarState.Auto)
          .width('100%')
          .height('100%')
          .backgroundColor('#FAFAFA')
          .align(Alignment.TopStart);

          // 右下角正方形刷新按钮（浮在内容上方）
          Column() {
            Text('⟳')
              .fontSize(22)
              .fontColor('#FFFFFF')
              .fontWeight(FontWeight.Bold);
          }
          .width(48)
          .height(48)
          .justifyContent(FlexAlign.Center)
          .alignItems(HorizontalAlign.Center)
          .backgroundColor('#1976D2')
          .borderRadius(8)
          .margin({ right: 16, bottom: 16 })
          .onClick(() => {
            this.loadRandomArticle();
          });
        }
      }
      .width('100%')
      .layoutWeight(1);

      // 底栏
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
          .fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => {
        router.replaceUrl({ url: 'pages/Home' });
      });

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
          .fontColor('#1976D2')
          .fontWeight(FontWeight.Bold);
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 });

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

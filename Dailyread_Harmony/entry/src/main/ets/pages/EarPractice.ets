import router from '@ohos.router';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';
import { ServerStatusIndicator } from '../components/ServerStatusIndicator';

@Entry
@Component
struct EarPracticePage {
  @State audioArticles: Article[] = [];
  @State isLoading: boolean = true;
  @State totalCount: number = 0;

  // ===== 全局数据刷新监听 =====
  @Watch('onRefreshSignalChanged')
  @StorageProp('dataRefreshSignal') refreshSignal: string = '';

  aboutToAppear(): void {
    this.loadAudioArticles();
  }

  aboutToShow(): void {
    this.loadAudioArticles();
  }

  onRefreshSignalChanged(): void {
    this.loadAudioArticles();
  }

  async loadAudioArticles(): Promise<void> {
    this.isLoading = true;
    try {
      const all: Article[] = await ArticleRepository.getInstance().getAllArticles();
      const filtered: Article[] = [];
      for (let i: number = 0; i < all.length; i++) {
        const a: Article = all[i];
        if (a.audiobase64 && a.audiobase64.length > 0) {
          filtered.push(a);
        }
      }
      filtered.sort((a: Article, b: Article) => {
        // 按 createTime 倒序（新文章在前），再按标题排序
        if (a.lastModified && b.lastModified && a.lastModified !== b.lastModified) {
          return a.lastModified < b.lastModified ? 1 : -1;
        }
        return a.title.localeCompare(b.title);
      });
      this.audioArticles = filtered;
      this.totalCount = filtered.length;
      console.info('EarPractice: 加载有音频文章 ' + filtered.length + ' 篇');
    } catch (e) {
      console.error('EarPractice: 加载失败: ' + JSON.stringify(e));
      this.audioArticles = [];
      this.totalCount = 0;
    }
    this.isLoading = false;
  }

  openArticle(articleId: number): void {
    router.pushUrl({
      url: 'pages/EarPracticeReader',
      params: { articleId: articleId }
    });
  }

  @Builder
  BuildBottomTabBar(): void {
    Row() {
      // 首页
      Column({ space: 0 }) {
        Text('●')
          .fontSize(18)
          .fontColor('#999999')
          .width('100%')
          .height(36)
          .textAlign(TextAlign.Center);
        Blank().width('100%').height(2);
        Text('首页')
          .fontSize(11)
          .fontColor('#666666')
          .width('100%')
          .height(14)
          .textAlign(TextAlign.Center);
      }
      .layoutWeight(1)
      .width('100%')
      .height(72)
      .padding({ top: 10, bottom: 10 })
      .justifyContent(FlexAlign.Center)
      .alignItems(HorizontalAlign.Center)
      .onClick(() => {
        router.back({ url: 'pages/Home' });
      });

      // 文章管理
      Column({ space: 0 }) {
        Text('📄')
          .fontSize(16)
          .fontColor('#999999')
          .width('100%')
          .height(36)
          .textAlign(TextAlign.Center);
        Blank().width('100%').height(2);
        Text('文章管理')
          .fontSize(11)
          .fontColor('#666666')
          .width('100%')
          .height(14)
          .textAlign(TextAlign.Center);
      }
      .layoutWeight(1)
      .width('100%')
      .height(72)
      .padding({ top: 10, bottom: 10 })
      .justifyContent(FlexAlign.Center)
      .alignItems(HorizontalAlign.Center)
      .onClick(() => {
        router.pushUrl({ url: 'pages/ArticleManage' });
      });

      // 磨耳跟背（当前页，高亮）
      Column({ space: 0 }) {
        Text('🔊')
          .fontSize(16)
          .fontColor('#1976D2')
          .width('100%')
          .height(36)
          .textAlign(TextAlign.Center);
        Blank().width('100%').height(2);
        Text('磨耳跟背')
          .fontSize(11)
          .fontColor('#1976D2')
          .fontWeight(FontWeight.Bold)
          .width('100%')
          .height(14)
          .textAlign(TextAlign.Center);
      }
      .layoutWeight(1)
      .width('100%')
      .height(72)
      .padding({ top: 10, bottom: 10 })
      .justifyContent(FlexAlign.Center)
      .alignItems(HorizontalAlign.Center);

      // 随心阅读
      Column({ space: 0 }) {
        Text('◈')
          .fontSize(16)
          .fontColor('#999999')
          .width('100%')
          .height(36)
          .textAlign(TextAlign.Center);
        Blank().width('100%').height(2);
        Text('随心阅读')
          .fontSize(11)
          .fontColor('#666666')
          .width('100%')
          .height(14)
          .textAlign(TextAlign.Center);
      }
      .layoutWeight(1)
      .width('100%')
      .height(72)
      .padding({ top: 10, bottom: 10 })
      .justifyContent(FlexAlign.Center)
      .alignItems(HorizontalAlign.Center)
      .onClick(() => {
        router.pushUrl({ url: 'pages/RandomRead' });
      });

      // 设置
      Column({ space: 0 }) {
        Text('⚙')
          .fontSize(16)
          .fontColor('#999999')
          .width('100%')
          .height(36)
          .textAlign(TextAlign.Center);
        Blank().width('100%').height(2);
        Text('设置')
          .fontSize(11)
          .fontColor('#666666')
          .width('100%')
          .height(14)
          .textAlign(TextAlign.Center);
      }
      .layoutWeight(1)
      .width('100%')
      .height(72)
      .padding({ top: 10, bottom: 10 })
      .justifyContent(FlexAlign.Center)
      .alignItems(HorizontalAlign.Center)
      .onClick(() => {
        router.pushUrl({ url: 'pages/Settings' });
      });
    }
    .width('100%')
    .backgroundColor('#FFFFFF')
    .borderWidth({ top: 1 })
    .borderColor('#EEEEEE');
  }

  build(): void {
    Stack() {
      // 主内容和底栏（与 Home/Settings 结构一致：Column 内部分层，不是悬浮）
      Column() {
        // 顶部栏
        Row() {
          Text('磨耳跟背')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .padding({ left: 16, right: 8, top: 16, bottom: 8 });
          ServerStatusIndicator();
          Blank();
          Text('共 ' + this.totalCount + ' 篇')
            .fontSize(13)
            .fontColor('#999999')
            .padding({ right: 16, top: 16, bottom: 8 });
        }
        .width('100%')
        .backgroundColor('#FFFFFF')
        .borderWidth({ bottom: 1 })
        .borderColor('#EEEEEE');

        // 列表 / Loading / 空状态
        if (this.isLoading) {
          Column() {
            LoadingProgress().width(40).height(40);
            Text('加载中...').fontSize(14).fontColor('#999999').margin({ top: 12 });
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#FFFFFF');
        } else if (this.audioArticles.length === 0) {
          Column() {
            Text('暂无带音频的文章')
              .fontSize(16)
              .fontColor('#999999');
            Text('请在 Win 端给文章添加音频后同步')
              .fontSize(14)
              .fontColor('#CCCCCC')
              .margin({ top: 8 });
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#FFFFFF');
        } else {
          List() {
            ForEach(this.audioArticles, (article: Article) => {
              ListItem() {
                Row() {
                  Column({ space: 4 }) {
                    Text() {
                      Span(article.title)
                        .fontSize(17)
                        .fontColor('#222222')
                        .fontWeight(FontWeight.Medium);
                      Span(' 🔊')
                        .fontSize(14)
                        .fontColor('#1976D2');
                    }
                    .maxLines(2)
                    .textOverflow({ overflow: TextOverflow.Ellipsis })
                    .width('100%');

                    Row({ space: 8 }) {
                      if (article.chineseChars > 0) {
                        Text(article.chineseChars + ' 字')
                          .fontSize(11)
                          .fontColor('#AAAAAA');
                      }
                      if (article.completionRate > 0) {
                        Text('完成率 ' + Math.round(article.completionRate * 100).toString() + '%')
                          .fontSize(11)
                          .fontColor('#AAAAAA');
                      }
                      if (article.checkInDays > 0) {
                        Text('已打卡 ' + article.checkInDays + ' 天')
                          .fontSize(11)
                          .fontColor('#AAAAAA');
                      }
                    }
                    .width('100%');
                  }
                  .layoutWeight(1)
                  .alignItems(HorizontalAlign.Start);
                }
                .width('100%')
                .padding(16)
                .alignItems(VerticalAlign.Center);
              }
              .width('100%')
              .backgroundColor('#FFFFFF')
              .borderRadius(12)
              .margin({ bottom: 10 })
              .shadow({ radius: 1, color: '#1F000000', offsetX: 0, offsetY: 1 })
              .onClick(() => {
                this.openArticle(article.id);
              });
            }, (article: Article) => 'ea_' + article.id.toString());
          }
          .width('100%')
          .layoutWeight(1)
          .padding({ left: 12, right: 12, top: 12, bottom: 12 })
          .backgroundColor('#F5F5F5');
        }

        // 底部导航栏（置于 Column 最下方，不是悬浮）
        this.BuildBottomTabBar();
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#FFFFFF');
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#FFFFFF');
  }
}

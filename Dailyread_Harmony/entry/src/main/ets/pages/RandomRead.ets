import router from '@ohos.router';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';
import image from '@ohos.multimedia.image';
import { common } from '@kit.AbilityKit';
import { ImageCompressionService, SizedPixelMap } from '../service/ImageCompressionService';

interface TextSegment {
  text: string;
  type: 'normal' | 'annotation' | 'bold';
  id: string;
}

@Entry
@Component
struct RandomReadPage {
  @State article: Article | null = null;
  @State isLoading: boolean = true;
  @State contentSegments: TextSegment[] = [];
  @State articlePixelMap: image.PixelMap | null = null;
  @State articlePixelRatio: number = 1.0;
  @State articleImageWidth: number = 0;
  @State articleImageHeight: number = 0;
  @State fontSize: number = 26;
  @State showBars: boolean = false;
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
      let selectedArticle: Article | null = null;

      if (pausedArticles.length === 0) {
        selectedArticle = null;
      } else if (pausedArticles.length === 1) {
        selectedArticle = pausedArticles[0];
      } else {
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
        selectedArticle = pool[randomIndex];
      }

      if (selectedArticle !== null) {
        let parsedSegments: TextSegment[] = [];
        if (selectedArticle.content) {
          try {
            parsedSegments = this.parseContent(selectedArticle.content, selectedArticle.id);
          } catch (e) {
            console.error('parseContent failed: ' + JSON.stringify(e));
            parsedSegments = [{ text: selectedArticle.content, type: 'normal', id: `${selectedArticle.id}_seg_err` }];
          }
        }

        let pixelMap: image.PixelMap | null = null;
        let imgWidth: number = 0;
        let imgHeight: number = 0;
        let imgRatio: number = 1.0;

        if (selectedArticle.imagewebp && selectedArticle.imagewebp.length > 0) {
          try {
            const ctx: common.Context = getContext(this) as common.Context;
            const sized: SizedPixelMap = await ImageCompressionService.base64ToPixelMap(
              ctx, selectedArticle.imagewebp
            );
            pixelMap = sized.pixelMap;
            imgWidth = sized.width;
            imgHeight = sized.height;
            imgRatio = sized.height > 0 ? sized.width / sized.height : 1.0;
          } catch (imgErr) {
            console.error('RandomRead: 图片解码失败: ' + JSON.stringify(imgErr));
          }
        }

        this.currentArticleId = selectedArticle.id;
        this.article = selectedArticle;
        this.contentSegments = parsedSegments;
        this.articlePixelMap = pixelMap;
        this.articleImageWidth = imgWidth;
        this.articleImageHeight = imgHeight;
        this.articlePixelRatio = imgRatio;
      } else {
        this.article = null;
        this.contentSegments = [];
        this.articlePixelMap = null;
        this.currentArticleId = -1;
      }
    } catch (e) {
      console.error('加载随机文章失败: ' + JSON.stringify(e));
      this.article = null;
      this.contentSegments = [];
      this.articlePixelMap = null;
      this.currentArticleId = -1;
    } finally {
      this.isLoading = false;
    }
  }

  parseContent(rawContent: string, articleId: number): TextSegment[] {
    const segments: TextSegment[] = [];
    let currentText: string = '';
    let state: 'normal' | 'annotation' | 'bold' = 'normal';
    let segmentIndex: number = 0;

    let i: number = 0;
    while (i < rawContent.length) {
      if (state === 'normal') {
        if (i + 1 < rawContent.length && rawContent[i] === '#' && rawContent[i + 1] === '#') {
          if (currentText) {
            segments.push({ text: currentText, type: 'normal', id: `${articleId}_seg_${segmentIndex++}` });
            currentText = '';
          }
          state = 'annotation';
          i += 2;
        } else if (i + 1 < rawContent.length && rawContent[i] === '*' && rawContent[i + 1] === '*') {
          if (currentText) {
            segments.push({ text: currentText, type: 'normal', id: `${articleId}_seg_${segmentIndex++}` });
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
            segments.push({ text: currentText, type: 'annotation', id: `${articleId}_seg_${segmentIndex++}` });
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
            segments.push({ text: currentText, type: 'bold', id: `${articleId}_seg_${segmentIndex++}` });
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
      segments.push({ text: currentText, type: 'normal', id: `${articleId}_seg_${segmentIndex++}` });
    }

    return segments;
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

  build(): void {
    Stack() {
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
            .backgroundColor('#FFFFFF');
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
            .backgroundColor('#FFFFFF');
          } else {
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

                Text() {
                  ForEach(this.contentSegments, (segment: TextSegment) => {
                    Span(segment.text)
                      .fontSize(segment.type === 'annotation' ? this.fontSize - 2 : this.fontSize)
                      .fontColor(segment.type === 'annotation' ? '#FF0000' : '#333333')
                      .fontWeight(segment.type === 'bold' ? FontWeight.Bold : FontWeight.Normal);
                  }, (segment: TextSegment) => segment.id)
                }
                .fontSize(this.fontSize)
                .fontColor('#333333')
                .lineHeight(this.fontSize * 1.8)
                .width('100%')
                .textAlign(TextAlign.Start);

                if (this.articlePixelMap !== null) {
                  if (this.articleImageWidth > 0 && this.articleImageWidth < 500) {
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
                    Image(this.articlePixelMap)
                      .width('100%')
                      .aspectRatio(this.articlePixelRatio)
                      .margin({ top: 24 })
                      .borderRadius(8)
                      .objectFit(ImageFit.Auto)
                      .backgroundColor('#F5F5F5');
                  }
                }

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
            .backgroundColor('#FFFFFF')
            .align(Alignment.TopStart)
            .onScroll(() => {
              this.hideBarsOnScroll();
            })
            .onClick(() => {
              this.toggleBars();
            });

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
            .margin({ right: 16, bottom: 88 })
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
      .height('100%');

      // 底部字号工具栏（浮动）
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
        router.back({ url: 'pages/Home' });
      });

      Column({ space: 2 }) {
        Text('📄')
          .fontSize(16)
          .fontColor('#999999');
        Text('文章管理')
          .fontSize(11)
          .fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => {
        router.pushUrl({ url: 'pages/ArticleManage' });
      });

      Column({ space: 2 }) {
        Text('◈')
          .fontSize(16)
          .fontColor('#1976D2');
        Text('随心阅读')
          .fontSize(11)
          .fontColor('#1976D2')
          .fontWeight(FontWeight.Bold);
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 });

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

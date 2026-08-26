import router from '@ohos.router';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';
import { ConfigRepository } from '../repository/ConfigRepository';
import { Config } from '../model/Config';
import image from '@ohos.multimedia.image';
import { common } from '@kit.AbilityKit';
import { ImageCompressionService, SizedPixelMap } from '../service/ImageCompressionService';
import { AudioService, AudioPlayerState } from '../service/AudioService';

interface TextSegment {
  text: string;
  type: 'normal' | 'annotation' | 'bold';
}

@Entry
@Component
struct EarPracticeReaderPage {
  @State contentSegments: TextSegment[] = [];
  @State article: Article | null = null;
  @State articlePixelMap: image.PixelMap | null = null;
  @State articlePixelRatio: number = 1.0;
  @State articleImageWidth: number = 0;
  @State articleImageHeight: number = 0;
  @State isLoading: boolean = true;
  @State showBars: boolean = false;
  @State fontSize: number = 26;
  @State shouldShowContent: boolean = true;
  // ====== 音频播放状态 ======
  @State hasAudio: boolean = false;
  @State audioPrepared: boolean = false;
  @State isAudioPlaying: boolean = false;
  @State audioCurrentMs: number = 0;
  @State audioDurationMs: number = 0;
  @State audioLoadFailed: boolean = false;
  private autoPlayAudio: boolean = true;
  private loopAudio: boolean = false;
  private articleId: number = 0;
  private audioService: AudioService = new AudioService();

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
    this.audioService.release().catch((e: Error) => {
      console.warn('EarPracticeReader: 音频释放异常: ' + JSON.stringify(e));
    });
  }

  async loadData(): Promise<void> {
    this.isLoading = true;
    this.articlePixelMap = null;
    try {
      // 阅读默认字号和音频配置
      try {
        const config: Config = await ConfigRepository.getInstance().getConfig();
        if (config.readerFontSize && config.readerFontSize > 0) {
          this.fontSize = config.readerFontSize;
        }
        this.autoPlayAudio = config.autoPlayAudio;
        this.loopAudio = config.loopAudio;
      } catch (cfgErr) {
        console.error('EarPracticeReader: 读取配置失败: ' + JSON.stringify(cfgErr));
      }

      // 单篇查询 + 降级兜底
      const articlesById: Article[] = await ArticleRepository.getInstance().getArticleById(this.articleId);
      if (articlesById.length > 0) {
        this.article = articlesById[0];
        if (this.article.content) {
          try {
            this.contentSegments = this.parseContent(this.article.content);
          } catch (e) {
            console.error('parseContent failed: ' + JSON.stringify(e));
            this.contentSegments = [{ text: this.article.content, type: 'normal' }];
          }
        }
      } else {
        const allArticles: Article[] = await ArticleRepository.getInstance().getAllArticles();
        for (let i: number = 0; i < allArticles.length; i++) {
          if (allArticles[i].id === this.articleId) {
            this.article = allArticles[i];
            if (this.article.content) {
              try {
                this.contentSegments = this.parseContent(this.article.content);
              } catch (e) {
                this.contentSegments = [{ text: this.article.content, type: 'normal' }];
              }
            }
            break;
          }
        }
      }

      // 图片解码
      if (this.article !== null && this.article.imagewebp && this.article.imagewebp.length > 0) {
        try {
          const ctx: common.Context = getContext(this) as common.Context;
          const sized: SizedPixelMap = await ImageCompressionService.base64ToPixelMap(
            ctx, this.article.imagewebp
          );
          this.articlePixelMap = sized.pixelMap;
          this.articleImageWidth = sized.width;
          this.articleImageHeight = sized.height;
          this.articlePixelRatio = sized.height > 0 ? sized.width / sized.height : 1.0;
        } catch (imgErr) {
          this.articlePixelMap = null;
          this.articleImageWidth = 0;
          this.articleImageHeight = 0;
          this.articlePixelRatio = 1.0;
        }
      }

      // iscontent 判定（无图自动降级显示文字）
      if (this.article !== null) {
        const noContentFlag: boolean = this.article.iscontent === false;
        const hasImage: boolean = this.articlePixelMap !== null;
        if (noContentFlag && !hasImage) {
          this.shouldShowContent = true;
        } else if (noContentFlag && hasImage) {
          this.shouldShowContent = false;
        } else {
          this.shouldShowContent = true;
        }
      }

      // 异步准备音频（不阻塞页面渲染）
      this.prepareArticleAudio();
    } catch (e) {
      console.error('EarPracticeReader: 加载失败: ' + JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  async prepareArticleAudio(): Promise<void> {
    if (this.article === null) {
      return;
    }
    const audioB64: string = this.article.audiobase64;
    if (!audioB64 || audioB64.length === 0) {
      this.hasAudio = false;
      return;
    }
    this.hasAudio = true;
    this.audioLoadFailed = false;

    const ctx: common.Context = getContext(this) as common.Context;
    this.audioService.setCallbacks(
      (state: AudioPlayerState) => {
        this.onAudioStateChange(state);
      },
      (currentMs: number, durationMs: number) => {
        this.audioCurrentMs = currentMs;
        if (durationMs > 0) {
          this.audioDurationMs = durationMs;
        }
      },
      (message: string) => {
        console.error('EarPracticeReader: 音频错误: ' + message);
        this.audioLoadFailed = true;
        this.isAudioPlaying = false;
        this.audioPrepared = false;
      }
    );

    try {
      await this.audioService.prepare(audioB64, ctx);
    } catch (e) {
      console.error('EarPracticeReader: 音频 prepare 失败: ' + JSON.stringify(e));
      this.audioLoadFailed = true;
    }
  }

  onAudioStateChange(state: AudioPlayerState): void {
    if (state === 'prepared') {
      this.audioPrepared = true;
      if (this.autoPlayAudio) {
        this.audioService.play();
      }
    } else if (state === 'playing') {
      this.isAudioPlaying = true;
      this.audioPrepared = true;
    } else if (state === 'paused') {
      this.isAudioPlaying = false;
    } else if (state === 'completed') {
      this.isAudioPlaying = false;
      this.audioCurrentMs = 0;
      if (this.loopAudio) {
        this.audioService.seek(0);
        this.audioService.play();
      }
    } else if (state === 'error') {
      this.isAudioPlaying = false;
      this.audioPrepared = false;
      this.audioLoadFailed = true;
    } else if (state === 'released') {
      this.isAudioPlaying = false;
      this.audioPrepared = false;
    }
  }

  onAudioToggle(): void {
    this.audioService.togglePlayPause();
  }

  onAudioSeek(progress: number): void {
    if (this.audioDurationMs > 0) {
      const targetMs: number = Math.floor(this.audioDurationMs * progress / 100);
      this.audioService.seek(targetMs);
      this.audioCurrentMs = targetMs;
    }
  }

  formatAudioTime(ms: number): string {
    if (ms <= 0) {
      return '00:00';
    }
    const totalSec: number = Math.floor(ms / 1000);
    const m: number = Math.floor(totalSec / 60);
    const s: number = totalSec % 60;
    const mStr: string = m < 10 ? '0' + m.toString() : m.toString();
    const sStr: string = s < 10 ? '0' + s.toString() : s.toString();
    return mStr + ':' + sStr;
  }

  getAudioProgressPercent(): number {
    if (this.audioDurationMs <= 0) {
      return 0;
    }
    const p: number = this.audioCurrentMs * 100 / this.audioDurationMs;
    if (p < 0) return 0;
    if (p > 100) return 100;
    return p;
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
        if (this.isLoading) {
          Column() {
            LoadingProgress().width(40).height(40);
            Text('加载中...').fontSize(14).fontColor('#999999').margin({ top: 12 });
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#FFFFFF');
        } else {
          if (this.article !== null) {
            Scroll() {
              Column() {
                if (this.shouldShowContent) {
                  Text(this.article.title)
                    .fontSize(this.fontSize + 6)
                    .fontWeight(FontWeight.Bold)
                    .fontColor('#333333')
                    .margin({ bottom: 8 })
                    .width('100%')
                    .maxLines(2)
                    .textOverflow({ overflow: TextOverflow.Ellipsis })
                    .textAlign(TextAlign.Start);

                  Text(`${this.article.chineseChars} 字`)
                    .fontSize(12)
                    .fontColor('#999999')
                    .margin({ bottom: 16 })
                    .width('100%');

                  // ====== 音频播放控制条（标题下、内容上）======
                  if (this.hasAudio) {
                    Column() {
                      Row() {
                        Text('🔊').fontSize(16).margin({ right: 8 });
                        Text(this.audioLoadFailed ? '音频加载失败' : '朗读音频')
                          .fontSize(14)
                          .fontColor(this.audioLoadFailed ? '#F44336' : '#666666')
                          .fontWeight(FontWeight.Medium)
                          .layoutWeight(1);
                        Text(this.formatAudioTime(this.audioDurationMs))
                          .fontSize(12)
                          .fontColor('#999999');
                      }
                      .width('100%')
                      .alignItems(VerticalAlign.Center)
                      .margin({ bottom: 8 });

                      if (!this.audioLoadFailed) {
                        Row() {
                          Text(this.isAudioPlaying ? '⏸' : '▶')
                            .fontSize(20)
                            .fontColor('#1976D2')
                            .width(40)
                            .height(40)
                            .textAlign(TextAlign.Center)
                            .borderRadius(20)
                            .backgroundColor('#E3F2FD')
                            .onClick(() => {
                              this.onAudioToggle();
                            });

                          Text(this.formatAudioTime(this.audioCurrentMs))
                            .fontSize(12)
                            .fontColor('#666666')
                            .margin({ left: 12, right: 8 });

                          Slider({
                            value: this.getAudioProgressPercent(),
                            min: 0,
                            max: 100,
                            style: SliderStyle.OutSet
                          })
                            .layoutWeight(1)
                            .blockColor('#1976D2')
                            .selectedColor('#1976D2')
                            .trackColor('#E0E0E0')
                            .onChange((value: number, mode: SliderChangeMode) => {
                              this.onAudioSeek(value);
                            });

                          Text(this.formatAudioTime(this.audioDurationMs))
                            .fontSize(12)
                            .fontColor('#999999')
                            .margin({ left: 8 });
                        }
                        .width('100%')
                        .alignItems(VerticalAlign.Center);
                      }
                    }
                    .width('100%')
                    .margin({ bottom: 16 })
                    .padding(12)
                    .backgroundColor('#F5F5F5')
                    .borderRadius(8);
                  }

                  Text() {
                    ForEach(this.contentSegments, (segment: TextSegment) => {
                      Span(segment.text)
                        .fontSize(segment.type === 'annotation' ? this.fontSize - 4 : this.fontSize)
                        .fontColor(segment.type === 'annotation' ? '#FF0000' : '#333333')
                        .fontWeight(segment.type === 'bold' ? FontWeight.Bold : FontWeight.Normal);
                    });
                  }
                  .fontSize(this.fontSize)
                  .fontColor('#333333')
                  .lineHeight(this.fontSize * 1.8)
                  .width('100%')
                  .textAlign(TextAlign.Start);
                }

                // ===== 文章图片（WebP）=====
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
                    .margin({ top: this.shouldShowContent ? 24 : 0 });
                  } else {
                    Image(this.articlePixelMap)
                      .width('100%')
                      .aspectRatio(this.articlePixelRatio)
                      .margin({ top: this.shouldShowContent ? 24 : 0 })
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
              Text('文章未找到').fontSize(16).fontColor('#999999');
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

      // 顶部工具栏（切换显示/隐藏，无打卡按钮/计时器）
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
              router.back();
            });
          }
          .width('100%')
          .padding({ left: 16, right: 16, top: 16, bottom: 16 })
          .backgroundColor('#FFFFFF');
        }
        .width('100%')
        .position({ x: 0, y: 0 });
      }

      // 底部工具栏（只有字号，无打卡）
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

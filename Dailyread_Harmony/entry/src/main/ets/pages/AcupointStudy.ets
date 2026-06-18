import router from '@ohos.router';
import { BuiltInAcupoint } from '../model/BuiltInAcupoint';
import { BuiltInAcupointStore } from '../repository/BuiltInAcupointStore';
import display from '@ohos.display';

@Entry
@Component
struct AcupointStudyPage {
  @State currentIdx: number = -1;
  @State item: BuiltInAcupoint = new BuiltInAcupoint();
  @State isLoading: boolean = true;
  @State isLandscape: boolean = false;
  private store: BuiltInAcupointStore = BuiltInAcupointStore.getInstance();

  private pickItem(idx: number): void {
    const list: BuiltInAcupoint[] = this.store.getAcupoints();
    const total: number = list.length;
    if (total === 0) {
      this.item = new BuiltInAcupoint();
      this.currentIdx = -1;
      return;
    }
    let target: number = idx;
    if (target < 0 || target >= total) {
      target = 0;
    }
    const source: BuiltInAcupoint = list[target];
    const next: BuiltInAcupoint = new BuiltInAcupoint();
    next.acupoint = source.acupoint;
    next.acupointProperty = source.acupointProperty;
    next.anatomy = source.anatomy;
    next.contraindications = source.contraindications;
    next.function = source.function;
    next.indications = source.indications;
    next.location = source.location;
    next.locationImageBase64 = source.locationImageBase64;
    next.imageUri = source.imageUri;
    next.meridian = source.meridian;
    next.note = source.note;
    next.operation = source.operation;
    this.item = next;
    this.currentIdx = target;
  }

  aboutToAppear(): void {
    this.checkOrientation();
    this.initData();
    try {
      display.on('change', () => {
        this.checkOrientation();
      });
    } catch (e) {
      console.error('display onchange failed:', JSON.stringify(e));
    }
  }

  aboutToDisappear(): void {
    try {
      display.off('change');
    } catch (e) {
      console.error('display off failed:', JSON.stringify(e));
    }
  }

  private checkOrientation(): void {
    try {
      const displays = display.getDefaultDisplaySync();
      this.isLandscape = displays.width > displays.height;
    } catch (e) {
      console.error('getDefaultDisplaySync failed:', JSON.stringify(e));
      this.isLandscape = false;
    }
  }

  private async initData(): Promise<void> {
    this.isLoading = true;
    try {
      const ctx = getContext(this);
      await this.store.load(ctx);
      const list: BuiltInAcupoint[] = this.store.getAcupoints();
      if (list.length === 0) {
        this.item = new BuiltInAcupoint();
        this.currentIdx = -1;
      } else {
        const firstIdx: number = Math.floor(Math.random() * list.length);
        this.pickItem(firstIdx);
      }
    } catch (e) {
      console.error('初始化穴位失败:', JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  private randomNext(): number {
    const list: BuiltInAcupoint[] = this.store.getAcupoints();
    const total: number = list.length;
    if (total <= 1) {
      return 0;
    }
    let nextIdx: number = Math.floor(Math.random() * total);
    if (nextIdx === this.currentIdx) {
      nextIdx = (nextIdx + 1) % total;
    }
    return nextIdx;
  }

  private refresh(): void {
    try {
      const list: BuiltInAcupoint[] = this.store.getAcupoints();
      if (list.length === 0) {
        return;
      }
      this.pickItem(this.randomNext());
    } catch (e) {
      console.error('刷新穴位失败:', JSON.stringify(e));
    }
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
          .fontColor('#1976D2')
          .fontWeight(FontWeight.Bold);
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 });

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

  build(): void {
    Stack({ alignContent: Alignment.BottomEnd }) {
      Column() {
        Row() {
          Text('背穴位')
            .fontSize(20)
            .fontWeight(FontWeight.Bold);
        }
        .width('100%')
        .padding(16)
        .backgroundColor('#FFFFFF');

        if (this.isLoading) {
          Column() {
            Text('加载中...')
              .fontSize(14)
              .fontColor('#999999');
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center);
        } else if (this.currentIdx < 0) {
          Column() {
            Text('暂无穴位数据')
              .fontSize(16)
              .fontColor('#999999');
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center);
        } else {
          if (this.isLandscape) {
            Row() {
              Scroll() {
                Column() {
                  if (this.item.acupoint.length > 0) {
                    Text(this.item.acupoint)
                      .fontSize(32)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#222222')
                      .margin({ top: 4, bottom: 4 });
                  }
                  if (this.item.meridian.length > 0) {
                    Text(this.item.meridian)
                      .fontSize(20)
                      .fontWeight(FontWeight.Normal)
                      .fontColor('#888888')
                      .fontStyle(FontStyle.Italic)
                      .margin({ top: 4, bottom: 4 });
                  }
                  if (this.item.acupointProperty.length > 0) {
                    Row() {
                      Text('穴性: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.acupointProperty)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                  if (this.item.location.length > 0) {
                    Row() {
                      Text('定位: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.location)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                  if (this.item.function.length > 0) {
                    Row() {
                      Text('功效: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.function)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                  if (this.item.indications.length > 0) {
                    Row() {
                      Text('主治: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.indications)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                  if (this.item.anatomy.length > 0) {
                    Row() {
                      Text('解剖: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.anatomy)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                  if (this.item.operation.length > 0) {
                    Row() {
                      Text('操作: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.operation)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                  if (this.item.contraindications.length > 0) {
                    Row() {
                      Text('禁忌: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.contraindications)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                  if (this.item.note.length > 0) {
                    Row() {
                      Text('备注: ')
                        .fontSize(14)
                        .fontWeight(FontWeight.Bold)
                        .fontColor('#D32F2F')
                        .margin({ right: 4 });
                      Text(this.item.note)
                        .fontSize(15)
                        .fontColor('#333333')
                        .lineHeight(24)
                        .layoutWeight(1)
                        .maxLines(999);
                    }
                    .width('100%')
                    .alignItems(VerticalAlign.Top)
                    .margin({ top: 6, bottom: 6 });
                  }
                }
                .width('100%')
                .alignItems(HorizontalAlign.Start)
                .justifyContent(FlexAlign.Start)
                .padding(16);
              }
              .scrollBar(BarState.Off)
              .align(Alignment.Top)
              .layoutWeight(1)
              .height('100%');

              Column() {
                if (this.item.imageUri.length > 0) {
                  Image(this.item.imageUri)
                    .width('100%')
                    .height('100%')
                    .objectFit(ImageFit.Contain);
                } else {
                  Column() {
                    Text('暂无穴位图')
                      .fontSize(14)
                      .fontColor('#999999');
                  }
                  .width('100%')
                  .height('100%')
                  .justifyContent(FlexAlign.Center);
                }
              }
              .width('34%')
              .height('100%')
              .padding(16)
              .margin({ left: 8 });
            }
            .width('100%')
            .layoutWeight(1)
            .backgroundColor('#FAFAFA');
          } else {
            Scroll() {
              Column() {
                if (this.item.acupoint.length > 0) {
                  Text(this.item.acupoint)
                    .fontSize(28)
                    .fontWeight(FontWeight.Bold)
                    .fontColor('#222222')
                    .margin({ top: 4, bottom: 4 });
                }
                if (this.item.meridian.length > 0) {
                  Text(this.item.meridian)
                    .fontSize(18)
                    .fontWeight(FontWeight.Normal)
                    .fontColor('#888888')
                    .fontStyle(FontStyle.Italic)
                    .margin({ top: 4, bottom: 4 });
                }
                if (this.item.acupointProperty.length > 0) {
                  Row() {
                    Text('穴性: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.acupointProperty)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }
                if (this.item.location.length > 0) {
                  Row() {
                    Text('定位: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.location)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }
                if (this.item.function.length > 0) {
                  Row() {
                    Text('功效: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.function)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }
                if (this.item.indications.length > 0) {
                  Row() {
                    Text('主治: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.indications)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }
                if (this.item.anatomy.length > 0) {
                  Row() {
                    Text('解剖: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.anatomy)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }
                if (this.item.operation.length > 0) {
                  Row() {
                    Text('操作: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.operation)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }
                if (this.item.contraindications.length > 0) {
                  Row() {
                    Text('禁忌: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.contraindications)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }
                if (this.item.note.length > 0) {
                  Row() {
                    Text('备注: ')
                      .fontSize(14)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#D32F2F')
                      .margin({ right: 4 });
                    Text(this.item.note)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .layoutWeight(1)
                      .maxLines(999);
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Top)
                  .margin({ top: 6, bottom: 6 });
                }

                if (this.item.imageUri.length > 0) {
                  Image(this.item.imageUri)
                    .width('100%')
                    .height(400)
                    .objectFit(ImageFit.Contain)
                    .margin({ top: 16, bottom: 72 });
                }
              }
              .width('100%')
              .alignItems(HorizontalAlign.Start)
              .justifyContent(FlexAlign.Start)
              .padding(16);
            }
            .scrollBar(BarState.Auto)
            .width('100%')
            .layoutWeight(1)
            .backgroundColor('#FAFAFA')
            .align(Alignment.Top);
          }
        }

        this.BottomTabBar();
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#F5F5F5');

      if (!this.isLoading && this.currentIdx >= 0) {
        Column() {
          Text('⟳')
            .fontSize(32)
            .fontColor('#FFFFFF');
        }
        .width(56)
        .height(56)
        .borderRadius(8)
        .backgroundColor('#1976D2')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
        .margin({ right: 16, bottom: 96 })
        .shadow({ radius: 8, color: '#40000000', offsetX: 0, offsetY: 2 })
        .onClick(() => {
          this.refresh();
        });
      }
    }
    .width('100%')
    .height('100%');
  }
}

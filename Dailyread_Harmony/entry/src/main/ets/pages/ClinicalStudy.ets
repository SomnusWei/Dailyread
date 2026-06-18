import router from '@ohos.router';
import { ClinicalNote } from '../model/ClinicalNote';
import { ClinicalNoteRepository } from '../repository/ClinicalNoteRepository';

@Entry
@Component
struct ClinicalStudyPage {
  @State notes: ClinicalNote[] = [];
  @State currentIndex: number = 0;
  @State isLoading: boolean = true;

  aboutToAppear(): void {
    this.loadNotes();
  }

  aboutToShow(): void {
    this.loadNotes();
  }

  async loadNotes(): Promise<void> {
    this.isLoading = true;
    try {
      this.notes = await ClinicalNoteRepository.getInstance().getReadingNotes();
      if (this.notes.length > 0) {
        this.currentIndex = Math.floor(Math.random() * this.notes.length);
      }
    } catch (e) {
      console.error('加载临床笔记失败: ' + JSON.stringify(e));
      this.notes = [];
    } finally {
      this.isLoading = false;
    }
  }

  nextNote(): void {
    if (this.notes.length <= 1) {
      return;
    }
    let newIndex: number;
    do {
      newIndex = Math.floor(Math.random() * this.notes.length);
    } while (newIndex === this.currentIndex);
    this.currentIndex = newIndex;
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
          .fontColor('#1976D2');
        Text('背临床')
          .fontSize(11)
          .fontColor('#1976D2')
          .fontWeight(FontWeight.Bold);
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 });

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

  build(): void {
    Column() {
      Row() {
        Text('背临床')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .layoutWeight(1);
        Text('设置')
          .fontSize(14)
          .fontColor('#1976D2')
          .padding({ left: 12, right: 12, top: 6, bottom: 6 })
          .onClick(() => {
            router.pushUrl({ url: 'pages/ClinicalSettings' });
          });
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
        .layoutWeight(1)
        .width('100%')
        .justifyContent(FlexAlign.Center)
        .backgroundColor('#F5F5F5');
      } else {
        if (this.notes.length === 0) {
          Column() {
            Text('暂无需要背诵的临床笔记')
              .fontSize(16)
              .fontColor('#999999');
            Text('请在设置中添加并开启学习状态')
              .fontSize(13)
              .fontColor('#BBBBBB')
              .margin({ top: 8 });
          }
          .layoutWeight(1)
          .width('100%')
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#F5F5F5');
        } else {
          Scroll() {
            Column() {
              Text(this.notes[this.currentIndex].title)
                .fontSize(22)
                .fontWeight(FontWeight.Bold)
                .width('100%')
                .textAlign(TextAlign.Start)
                .margin({ bottom: 16 });

              Column({ space: 16 }) {
                if (this.notes[this.currentIndex].pathogenesis.length > 0) {
                  Column({ space: 8 }) {
                    Text('病机')
                      .fontSize(15)
                      .fontColor('#E53935')
                      .fontWeight(FontWeight.Bold)
                      .textAlign(TextAlign.Start);
                    Text(this.notes[this.currentIndex].pathogenesis)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .textAlign(TextAlign.Start);
                  }
                  .width('100%')
                  .padding(12)
                  .backgroundColor('#FFF5F5')
                  .borderRadius(8)
                  .alignItems(HorizontalAlign.Start);
                }

                if (this.notes[this.currentIndex].treatment.length > 0) {
                  Column({ space: 8 }) {
                    Text('治法')
                      .fontSize(15)
                      .fontColor('#16A34A')
                      .fontWeight(FontWeight.Bold)
                      .textAlign(TextAlign.Start);
                    Text(this.notes[this.currentIndex].treatment)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .textAlign(TextAlign.Start);
                  }
                  .width('100%')
                  .padding(12)
                  .backgroundColor('#F0FFF4')
                  .borderRadius(8)
                  .alignItems(HorizontalAlign.Start);
                }

                if (this.notes[this.currentIndex].prescription.length > 0) {
                  Column({ space: 8 }) {
                    Text('处方')
                      .fontSize(15)
                      .fontColor('#1D4ED8')
                      .fontWeight(FontWeight.Bold)
                      .textAlign(TextAlign.Start);
                    Text(this.notes[this.currentIndex].prescription)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .textAlign(TextAlign.Start);
                  }
                  .width('100%')
                  .padding(12)
                  .backgroundColor('#EFF6FF')
                  .borderRadius(8)
                  .alignItems(HorizontalAlign.Start);
                }

                if (this.notes[this.currentIndex].notes.length > 0) {
                  Column({ space: 8 }) {
                    Text('备注')
                      .fontSize(15)
                      .fontColor('#D97706')
                      .fontWeight(FontWeight.Bold)
                      .textAlign(TextAlign.Start);
                    Text(this.notes[this.currentIndex].notes)
                      .fontSize(15)
                      .fontColor('#333333')
                      .lineHeight(24)
                      .textAlign(TextAlign.Start);
                  }
                  .width('100%')
                  .padding(12)
                  .backgroundColor('#FFFBEB')
                  .borderRadius(8)
                  .alignItems(HorizontalAlign.Start);
                }
              }
              .width('100%')
              .alignItems(HorizontalAlign.Start)
              .justifyContent(FlexAlign.Start);
            }
            .width('100%')
            .padding(16)
            .backgroundColor('#FFFFFF')
            .alignItems(HorizontalAlign.Start)
            .justifyContent(FlexAlign.Start);
          }
          .layoutWeight(1)
          .scrollBar(BarState.Auto)
          .scrollBarColor('#CCCCCC')
          .scrollBarWidth(4)
          .align(Alignment.Top);

          Row() {
            Text(`${this.currentIndex + 1} / ${this.notes.length}`)
              .fontSize(12)
              .fontColor('#999999')
              .padding({ left: 12, right: 12 });

            Button('下一个')
              .fontSize(16)
              .fontColor('#FFFFFF')
              .backgroundColor('#1976D2')
              .width('60%')
              .onClick(() => {
                this.nextNote();
              });
          }
          .width('100%')
          .backgroundColor('#FFFFFF')
          .justifyContent(FlexAlign.Center)
          .padding({ top: 12, bottom: 12 })
          .margin({ top: 8 });
        }
      }

      this.BottomTabBar();
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5');
  }
}

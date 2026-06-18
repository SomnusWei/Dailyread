import router from '@ohos.router';
import { Concept } from '../model/Concept';
import { ConceptRepository } from '../repository/ConceptRepository';

@Entry
@Component
struct ConceptStudyPage {
  @State concepts: Concept[] = [];
  @State currentIndex: number = 0;
  @State isLoading: boolean = true;

  aboutToAppear(): void {
    this.loadConcepts();
  }

  aboutToShow(): void {
    // 每次页面显示时刷新数据（可能从设置页返回后状态已改变）
    this.loadConcepts();
  }

  async loadConcepts(): Promise<void> {
    this.isLoading = true;
    try {
      // 仅加载阅读状态开启的概念
      this.concepts = await ConceptRepository.getInstance().getReadingConcepts();
      // 初始随机选一个
      if (this.concepts.length > 0) {
        this.currentIndex = Math.floor(Math.random() * this.concepts.length);
      }
    } catch (e) {
      console.error('加载概念失败: ' + JSON.stringify(e));
      this.concepts = [];
    } finally {
      this.isLoading = false;
    }
  }

  // 下一个：不与当前重复的随机选择
  nextConcept(): void {
    if (this.concepts.length <= 1) {
      return;
    }
    let newIndex: number;
    do {
      newIndex = Math.floor(Math.random() * this.concepts.length);
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

  build(): void {
    Column() {
      // 顶部标题栏
      Row() {
        Text('背概念')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .layoutWeight(1);
        Text('设置')
          .fontSize(14)
          .fontColor('#1976D2')
          .padding({ left: 12, right: 12, top: 6, bottom: 6 })
          .onClick(() => {
            router.pushUrl({ url: 'pages/ConceptSettings' });
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
        if (this.concepts.length === 0) {
          Column() {
            Text('暂无需要背诵的概念')
              .fontSize(16)
              .fontColor('#999999');
            Text('请在设置中添加并开启阅读状态')
              .fontSize(13)
              .fontColor('#BBBBBB')
              .margin({ top: 8 });
          }
          .layoutWeight(1)
          .width('100%')
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#F5F5F5');
        } else {
          // 内容区域：顶部对齐
          Column() {
            Text(this.concepts[this.currentIndex].title)
              .fontSize(22)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Start)
              .margin({ bottom: 16 });

            if (this.concepts[this.currentIndex].category.length > 0 ||
              this.concepts[this.currentIndex].subject.length > 0 ||
              this.concepts[this.currentIndex].chapter.length > 0) {
              Row({ space: 8 }) {
                if (this.concepts[this.currentIndex].category.length > 0) {
                  Text('分类:' + this.concepts[this.currentIndex].category)
                    .fontSize(12)
                    .fontColor('#666666');
                }
                if (this.concepts[this.currentIndex].subject.length > 0) {
                  Text('学科:' + this.concepts[this.currentIndex].subject)
                    .fontSize(12)
                    .fontColor('#666666');
                }
                if (this.concepts[this.currentIndex].chapter.length > 0) {
                  Text('章节:' + this.concepts[this.currentIndex].chapter)
                    .fontSize(12)
                    .fontColor('#666666');
                }
              }
              .width('100%')
              .margin({ bottom: 16 });
            }

            Scroll() {
              Column({ space: 0 }) {
                Text(this.concepts[this.currentIndex].content)
                  .fontSize(16)
                  .fontColor('#333333')
                  .lineHeight(26)
                  .width('100%')
                  .textAlign(TextAlign.Start);
              }
              .width('100%')
              .alignItems(HorizontalAlign.Start)
              .justifyContent(FlexAlign.Start);
            }
            .scrollBar(BarState.Auto)
            .layoutWeight(1)
            .width('100%')
            .align(Alignment.TopStart);
          }
          .width('100%')
          .layoutWeight(1)
          .padding(16)
          .backgroundColor('#FFFFFF')
          .alignItems(HorizontalAlign.Start)
          .justifyContent(FlexAlign.Start);

          // 底部操作栏
          Row() {
            Text(`${this.currentIndex + 1} / ${this.concepts.length}`)
              .fontSize(12)
              .fontColor('#999999')
              .padding({ left: 12, right: 12 });

            Button('下一个')
              .fontSize(16)
              .fontColor('#FFFFFF')
              .backgroundColor('#1976D2')
              .width('60%')
              .onClick(() => {
                this.nextConcept();
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

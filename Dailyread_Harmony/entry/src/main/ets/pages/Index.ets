import router from '@ohos.router';

@Entry
@Component
struct Index {
  aboutToAppear(): void {
    router.replaceUrl({ url: 'pages/SplashPage' });
  }

  build() {
    Column() {
      Text('正在加载...')
        .fontSize(16)
        .fontColor('#666666');
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .backgroundColor('#FFFFFF');
  }
}
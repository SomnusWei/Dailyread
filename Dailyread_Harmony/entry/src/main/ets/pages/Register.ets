import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { ApiClient } from '../service/ApiClient';

/**
 * 注册页
 */
@Entry
@Component
struct Register {
  @State username: string = '';
  @State nickname: string = '';
  @State password: string = '';
  @State confirm: string = '';
  @State loading: boolean = false;
  @State statusMsg: string = '';
  @State usernameStatus: string = '';
  @State usernameOk: boolean = false;
  private checkTimer: number = -1;

  private checkUsername(): void {
    if (this.username.length < 3) {
      this.usernameStatus = '';
      this.usernameOk = false;
      return;
    }
    if (this.checkTimer !== -1) {
      clearTimeout(this.checkTimer);
    }
    this.checkTimer = setTimeout(() => { this.doCheckUsername(); }, 500);
  }

  private async doCheckUsername(): Promise<void> {
    try {
      const ok = await ApiClient.getInstance().checkUsername(this.username);
      if (ok) {
        this.usernameStatus = '✓ 用户名可用';
        this.usernameOk = true;
      } else {
        this.usernameStatus = '✗ 用户名已存在';
        this.usernameOk = false;
      }
    } catch (e) {
      this.usernameStatus = '';
      this.usernameOk = false;
    }
  }

  private async doRegister(): Promise<void> {
    if (this.username.length < 3) {
      this.statusMsg = '用户名至少 3 位';
      return;
    }
    if (this.password.length < 6) {
      this.statusMsg = '密码至少 6 位';
      return;
    }
    if (this.password !== this.confirm) {
      this.statusMsg = '两次密码不一致';
      return;
    }
    this.loading = true;
    this.statusMsg = '注册中...';
    try {
      const result = await ApiClient.getInstance().register(this.username, this.password, this.nickname);
      if (result) {
        promptAction.showToast({ message: '注册成功' });
        router.replaceUrl({ url: 'pages/SplashPage' });
      } else {
        this.statusMsg = '注册失败，用户名可能已存在';
      }
    } catch (e) {
      this.statusMsg = '网络错误: ' + JSON.stringify(e);
    } finally {
      this.loading = false;
    }
  }

  private goToLogin(): void {
    router.replaceUrl({ url: 'pages/Login' });
  }

  build() {
    Scroll() {
      Column() {
        Text('每日阅读')
          .fontSize(32)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1976D2')
          .margin({ top: 60, bottom: 8 });

        Text('注册新账号')
          .fontSize(14)
          .fontColor('#888888')
          .margin({ bottom: 32 });

        TextInput({ placeholder: '用户名（3-32位）', text: this.username })
          .onChange((v: string) => {
            this.username = v;
            this.checkUsername();
          })
          .height(48)
          .margin({ left: 32, right: 32, bottom: 8 })
          .backgroundColor('#F5F5F5')
          .borderRadius(8);

        if (this.usernameStatus.length > 0) {
          Text(this.usernameStatus)
            .fontSize(12)
            .fontColor(this.usernameOk ? '#2E7D32' : '#D32F2F')
            .margin({ left: 32, right: 32, bottom: 8 })
            .alignSelf(ItemAlign.Start)
            .width('100%')
            .textAlign(TextAlign.Start);
        }

        TextInput({ placeholder: '昵称（可选）', text: this.nickname })
          .onChange((v: string) => { this.nickname = v; })
          .height(48)
          .margin({ left: 32, right: 32, bottom: 16 })
          .backgroundColor('#F5F5F5')
          .borderRadius(8);

        TextInput({ placeholder: '密码（至少6位）', text: this.password })
          .type(InputType.Password)
          .onChange((v: string) => { this.password = v; })
          .height(48)
          .margin({ left: 32, right: 32, bottom: 16 })
          .backgroundColor('#F5F5F5')
          .borderRadius(8);

        TextInput({ placeholder: '确认密码', text: this.confirm })
          .type(InputType.Password)
          .onChange((v: string) => { this.confirm = v; })
          .height(48)
          .margin({ left: 32, right: 32, bottom: 16 })
          .backgroundColor('#F5F5F5')
          .borderRadius(8);

        if (this.statusMsg.length > 0) {
          Text(this.statusMsg)
            .fontSize(13)
            .fontColor('#D32F2F')
            .margin({ bottom: 16 });
        }

        Button(this.loading ? '注册中...' : '注册')
          .type(ButtonType.Capsule)
          .width('70%')
          .height(48)
          .backgroundColor('#1976D2')
          .fontColor('#FFFFFF')
          .enabled(!this.loading)
          .onClick(() => { this.doRegister(); })
          .margin({ bottom: 24 });

        Row() {
          Text('已有账号？')
            .fontSize(14)
            .fontColor('#666666');
          Text('去登录')
            .fontSize(14)
            .fontColor('#1976D2')
            .onClick(() => { this.goToLogin(); });
        }
        .margin({ bottom: 40 });
      }
      .width('100%')
      .alignItems(HorizontalAlign.Center);
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#FFFFFF');
  }
}

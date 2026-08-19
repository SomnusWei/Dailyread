import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import preferences from '@ohos.data.preferences';
import common from '@ohos.app.ability.common';
import { ApiClient } from '../service/ApiClient';

const PREF_STORE: string = 'dailyread_login';
const KEY_SAVED_USERNAME: string = 'saved_username';
const KEY_SAVED_PASSWORD: string = 'saved_password';
const KEY_REMEMBER: string = 'remember_password';

/**
 * 登录页
 * 功能：
 * 1. 账号密码登录
 * 2. 记住密码（本地保存账号密码）
 * 3. 401设备冲突处理
 * 4. 设备ID自动生成和传递（由ApiClient内部处理）
 */
@Entry
@Component
struct Login {
  @State username: string = '';
  @State password: string = '';
  @State loading: boolean = false;
  @State statusMsg: string = '';
  @State rememberPassword: boolean = false;

  private context: common.Context = getContext(this) as common.Context;
  private prefs: preferences.Preferences | null = null;

  aboutToAppear(): void {
    this.loadSavedCredentials();
  }

  private async loadSavedCredentials(): Promise<void> {
    try {
      this.prefs = await preferences.getPreferences(this.context, PREF_STORE);
      const remember = await this.prefs.get(KEY_REMEMBER, false) as boolean;
      this.rememberPassword = remember;
      if (remember) {
        this.username = await this.prefs.get(KEY_SAVED_USERNAME, '') as string;
        this.password = await this.prefs.get(KEY_SAVED_PASSWORD, '') as string;
      }
    } catch (e) {
      console.error('Login: 加载保存的凭证失败: ' + JSON.stringify(e));
    }
  }

  private async saveCredentials(): Promise<void> {
    if (!this.prefs) {
      this.prefs = await preferences.getPreferences(this.context, PREF_STORE);
    }
    try {
      await this.prefs.put(KEY_REMEMBER, this.rememberPassword);
      if (this.rememberPassword) {
        await this.prefs.put(KEY_SAVED_USERNAME, this.username);
        await this.prefs.put(KEY_SAVED_PASSWORD, this.password);
      } else {
        await this.prefs.delete(KEY_SAVED_USERNAME);
        await this.prefs.delete(KEY_SAVED_PASSWORD);
      }
      await this.prefs.flush();
    } catch (e) {
      console.error('Login: 保存凭证失败: ' + JSON.stringify(e));
    }
  }

  private async doLogin(): Promise<void> {
    if (this.username.length < 3) {
      this.statusMsg = '用户名至少 3 位';
      return;
    }
    if (this.password.length < 6) {
      this.statusMsg = '密码至少 6 位';
      return;
    }
    this.loading = true;
    this.statusMsg = '登录中...';
    try {
      const api = ApiClient.getInstance();

      // 设置401冲突回调
      api.setConflictCallback((msg: string) => {
        this.statusMsg = msg;
        this.loading = false;
      });

      const result = await api.login(this.username, this.password);
      if (result) {
        // 保存凭证
        await this.saveCredentials();
        promptAction.showToast({ message: '登录成功' });
        router.replaceUrl({ url: 'pages/SplashPage' });
      } else {
        this.statusMsg = '用户名或密码错误';
      }
    } catch (e) {
      const errStr = JSON.stringify(e);
      if (errStr.indexOf('401') >= 0 || errStr.indexOf('conflict') >= 0) {
        this.statusMsg = '账号已在其他设备登录，请重新登录';
      } else {
        this.statusMsg = '网络错误: ' + errStr;
      }
    } finally {
      this.loading = false;
    }
  }

  private goToRegister(): void {
    router.replaceUrl({ url: 'pages/Register' });
  }

  build() {
    Stack() {
      Column() {
        Text('每日阅读')
          .fontSize(32)
          .fontWeight(FontWeight.Bold)
          .fontColor('#1976D2')
          .margin({ top: 80, bottom: 8 });

        Text('账号登录')
          .fontSize(14)
          .fontColor('#888888')
          .margin({ bottom: 40 });

        TextInput({ placeholder: '用户名', text: this.username })
          .onChange((v: string) => { this.username = v; })
          .height(48)
          .margin({ left: 32, right: 32, bottom: 16 })
          .backgroundColor('#F5F5F5')
          .borderRadius(8);

        TextInput({ placeholder: '密码', text: this.password })
          .type(InputType.Password)
          .onChange((v: string) => { this.password = v; })
          .height(48)
          .margin({ left: 32, right: 32, bottom: 16 })
          .backgroundColor('#F5F5F5')
          .borderRadius(8)
          .onSubmit(() => { this.doLogin(); });

        // 记住密码复选框
        Row() {
          Checkbox()
            .select(this.rememberPassword)
            .onChange((checked: boolean) => {
              this.rememberPassword = checked;
            })
          Text('记住密码')
            .fontSize(14)
            .fontColor('#666666')
            .margin({ left: 8 });
        }
        .width('100%')
        .justifyContent(FlexAlign.Start)
        .margin({ left: 32, right: 32, bottom: 16 });

        if (this.statusMsg.length > 0) {
          Text(this.statusMsg)
            .fontSize(13)
            .fontColor('#D32F2F')
            .margin({ bottom: 16 });
        }

        Button(this.loading ? '登录中...' : '登录')
          .type(ButtonType.Capsule)
          .width('70%')
          .height(48)
          .backgroundColor('#1976D2')
          .fontColor('#FFFFFF')
          .enabled(!this.loading)
          .onClick(() => { this.doLogin(); })
          .margin({ bottom: 24 });

        Row() {
          Text('还没有账号？')
            .fontSize(14)
            .fontColor('#666666');
          Text('去注册')
            .fontSize(14)
            .fontColor('#1976D2')
            .onClick(() => { this.goToRegister(); });
        }
        .margin({ bottom: 40 });
      }
      .width('100%')
      .height('100%')
      .alignItems(HorizontalAlign.Center);
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#FFFFFF');
  }
}
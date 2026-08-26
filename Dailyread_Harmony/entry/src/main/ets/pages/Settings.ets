import router from '@ohos.router';
import { Config } from '../model/Config';
import { ConfigRepository } from '../repository/ConfigRepository';
import { ApiClient } from '../service/ApiClient';
import { SyncService } from '../service/SyncService';
import { BackupService, ImportResult } from '../service/BackupService';
import { common } from '@kit.AbilityKit';
import promptAction from '@ohos.promptAction';
import fs from '@ohos.file.fs';
import picker from '@ohos.file.picker';
import util from '@ohos.util';
import { setKeepScreenOn } from '../entryability/EntryAbility';

@Entry
@Component
struct SettingsPage {
  @State config: Config = new Config();
  @State isLoading: boolean = true;
  @State showWebDavConfig: boolean = false;
  @State showJianGuoYunGuide: boolean = false;
  @State webdavUrlInput: string = '';
  @State webdavUsernameInput: string = '';
  @State webdavPasswordInput: string = '';
  @State webdavRemotePathInput: string = '/DailyRead';
  @State isExporting: boolean = false;
  @State isImporting: boolean = false;
  
  private context: common.Context = getContext(this) as common.Context;

  aboutToAppear(): void {
    this.loadConfig();
  }

  async loadConfig(): Promise<void> {
    this.isLoading = true;
    try {
      this.config = await ConfigRepository.getInstance().getConfig();
      this.webdavUrlInput = this.config.webdavUrl;
      this.webdavUsernameInput = this.config.webdavUsername;
      this.webdavPasswordInput = this.config.webdavPassword;
      this.webdavRemotePathInput = this.config.webdavRemotePath;
    } catch (e) {
      console.error('加载配置失败: ' + JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  async updateConfig(): Promise<void> {
    try {
      await ConfigRepository.getInstance().updateConfig(this.config);
      // 配置变更时推送到服务端（keepScreenOn除外，由SyncService内部处理）
      if (ApiClient.getInstance().isLoggedIn()) {
        SyncService.getInstance().pushConfig();
      }
    } catch (e) {
      console.error('更新配置失败: ' + JSON.stringify(e));
    }
  }

  async exportData(): Promise<void> {
    if (this.isExporting) return;
    this.isExporting = true;
    try {
      const jsonContent: string = await BackupService.getInstance().exportToJSON();
      const timeStr: string = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName: string = 'daily_read_backup_' + timeStr + '.json';
      const filePath: string = this.context.filesDir + '/' + fileName;
      const tempFile: fs.File = fs.openSync(filePath, fs.OpenMode.READ_WRITE | fs.OpenMode.CREATE);
      fs.writeSync(tempFile.fd, jsonContent);
      fs.closeSync(tempFile);
      promptAction.showToast({ message: '已导出至应用目录: ' + fileName, duration: 3000 });
    } catch (e) {
      const errMsg: string = JSON.stringify(e);
      promptAction.showToast({ message: '导出失败: ' + errMsg, duration: 3000 });
      console.error('导出失败: ' + errMsg);
    } finally {
      this.isExporting = false;
    }
  }

  private readJsonFromUri(uri: string): string {
    const stat: fs.Stat = fs.statSync(uri);
    if (stat.size <= 0) return '';
    const uint8: Uint8Array = new Uint8Array(stat.size);
    const file: fs.File = fs.openSync(uri, fs.OpenMode.READ_ONLY);
    fs.readSync(file.fd, uint8.buffer);
    fs.closeSync(file);
    const decoder: util.TextDecoder = new util.TextDecoder('utf-8');
    return decoder.decodeWithStream(uint8, { stream: false });
  }

  async importData(): Promise<void> {
    if (this.isImporting) return;
    this.isImporting = true;
    try {
      const documentPicker: picker.DocumentViewPicker = new picker.DocumentViewPicker();
      const selectOpts: picker.DocumentSelectOptions = new picker.DocumentSelectOptions();
      selectOpts.fileSuffixFilters = ['.json'];
      selectOpts.maxSelectNumber = 1;
      const resultUris: string[] = await documentPicker.select(selectOpts);
      
      if (!resultUris || resultUris.length === 0) {
        promptAction.showToast({ message: '未选择文件', duration: 2000 });
        return;
      }
      
      let jsonContent: string = '';
      try {
        jsonContent = this.readJsonFromUri(resultUris[0]);
      } catch {
        promptAction.showToast({ message: '读取文件失败', duration: 3000 });
        return;
      }
      
      if (jsonContent.length === 0) {
        promptAction.showToast({ message: '文件为空', duration: 2000 });
        return;
      }

      const result: ImportResult = await BackupService.getInstance().importFromJSON(jsonContent, true);
      if (result.success) {
        promptAction.showToast({ message: '导入成功！文章:' + result.importedArticles, duration: 3000 });
      } else {
        promptAction.showToast({ message: '导入失败: ' + result.errorMessage, duration: 3000 });
      }
    } catch (e) {
      promptAction.showToast({ message: '导入失败', duration: 3000 });
      console.error('导入失败: ' + JSON.stringify(e));
    } finally {
      this.isImporting = false;
    }
  }

  @Builder
  BuildBottomTabBar(): void {
    Row() {
      Column({ space: 2 }) {
        Text('●').fontSize(18).fontColor('#999999');
        Text('首页').fontSize(11).fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => router.back({ url: 'pages/Home' }))

      Column({ space: 2 }) {
        Text('📄').fontSize(16).fontColor('#999999');
        Text('文章管理').fontSize(11).fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => router.pushUrl({ url: 'pages/ArticleManage' }));

      Column({ space: 2 }) {
        Text('◈').fontSize(16).fontColor('#999999');
        Text('随心阅读').fontSize(11).fontColor('#666666');
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
      .onClick(() => router.pushUrl({ url: 'pages/RandomRead' }))

      Column({ space: 2 }) {
        Text('⚙').fontSize(16).fontColor('#1976D2');
        Text('设置').fontSize(11).fontColor('#1976D2').fontWeight(FontWeight.Bold);
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
    }
    .width('100%')
    .backgroundColor('#FFFFFF')
  }

  @Builder
  BuildSectionTitle(title: string): void {
    Text(title)
      .fontSize(18)
      .fontWeight(FontWeight.Bold)
      .width('100%')
      .padding({ left: 16, right: 16, top: 8 })
  }

  build(): void {
    Stack() {
      // 主内容和底栏
      Column() {
        // 主内容区域
        Column() {
          Text('设置')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .padding({ left: 16, right: 16, top: 16, bottom: 8 })
            .width('100%')
            .backgroundColor('#FFFFFF')

          if (this.isLoading) {
            Column() {
              LoadingProgress().width(40).height(40)
              Text('加载中...').fontSize(14).fontColor('#999999').margin({ top: 12 })
            }
            .width('100%')
            .layoutWeight(1)
            .justifyContent(FlexAlign.Center)
          } else {
            Scroll() {
              Column({ space: 16 }) {
                this.BuildSectionTitle('阅读设置')

                // 每日阅读时间卡片
                Column() {
                  Text('每日阅读时间').fontSize(16).fontWeight(FontWeight.Medium).width('100%')
                  Row() {
                    Text(`${this.config.dailyMinutes} 分钟`).fontSize(16)
                    Blank()
                    Button('-5')
                      .fontSize(14)
                      .onClick(() => {
                        this.config.dailyMinutes = Math.max(5, this.config.dailyMinutes - 5);
                        this.updateConfig();
                      })
                    Button('+5')
                      .fontSize(14)
                      .margin({ left: 8 })
                      .onClick(() => {
                        this.config.dailyMinutes = Math.min(120, this.config.dailyMinutes + 5);
                        this.updateConfig();
                      })
                  }.width('100%').margin({ top: 8 })
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                // 目标完成率卡片
                Column() {
                  Text('目标完成率').fontSize(16).fontWeight(FontWeight.Medium).width('100%')
                  Row() {
                    Text(`${Math.round(this.config.targetCheckRate)}%`).fontSize(16)
                    Blank()
                    Slider({
                      value: this.config.targetCheckRate,
                      min: 5,
                      max: 100,
                      step: 5,
                      style: SliderStyle.OutSet
                    })
                      .onChange((value: number) => {
                        this.config.targetCheckRate = value;
                        this.updateConfig();
                      })
                      .layoutWeight(1)
                      .margin({ left: 16 })
                  }.width('100%').margin({ top: 8 })
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                // 阅读默认字号卡片
                Column() {
                  Text('阅读默认字号').fontSize(16).fontWeight(FontWeight.Medium).width('100%')
                  Row() {
                    Text(`${this.config.readerFontSize}`).fontSize(16)
                    Blank()
                    Slider({
                      value: this.config.readerFontSize,
                      min: 16,
                      max: 40,
                      step: 1,
                      style: SliderStyle.OutSet
                    })
                      .onChange((value: number) => {
                        this.config.readerFontSize = Math.round(value);
                        this.updateConfig();
                      })
                      .layoutWeight(1)
                      .margin({ left: 16 })
                  }.width('100%').margin({ top: 8 })
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                // 保持屏幕常亮卡片
                Column() {
                  Row() {
                    Column() {
                      Text('保持屏幕常亮').fontSize(16).fontWeight(FontWeight.Medium)
                      Text('应用在前台时屏幕不会自动休眠').fontSize(12).fontColor('#999999').margin({ top: 4 })
                    }
                    .alignItems(HorizontalAlign.Start)
                    .layoutWeight(1)
                    Toggle({ type: ToggleType.Switch, isOn: this.config.keepScreenOn })
                      .onChange((isOn: boolean) => {
                        this.config.keepScreenOn = isOn;
                        this.updateConfig();
                        try {
                          setKeepScreenOn(isOn);
                        } catch (e) {
                          console.error('应用keepScreenOn失败: ' + JSON.stringify(e));
                        }
                      })
                  }.width('100%').alignItems(VerticalAlign.Center)
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                // 音频自动播放卡片
                Column() {
                  Row() {
                    Column() {
                      Text('自动播放音频').fontSize(16).fontWeight(FontWeight.Medium)
                      Text('进入阅读页时自动播放文章音频').fontSize(12).fontColor('#999999').margin({ top: 4 })
                    }
                    .alignItems(HorizontalAlign.Start)
                    .layoutWeight(1)
                    Toggle({ type: ToggleType.Switch, isOn: this.config.autoPlayAudio })
                      .onChange((isOn: boolean) => {
                        this.config.autoPlayAudio = isOn;
                        this.updateConfig();
                      })
                  }.width('100%').alignItems(VerticalAlign.Center)
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                // 音频循环播放卡片
                Column() {
                  Row() {
                    Column() {
                      Text('循环播放音频').fontSize(16).fontWeight(FontWeight.Medium)
                      Text('音频播放结束后自动重新播放').fontSize(12).fontColor('#999999').margin({ top: 4 })
                    }
                    .alignItems(HorizontalAlign.Start)
                    .layoutWeight(1)
                    Toggle({ type: ToggleType.Switch, isOn: this.config.loopAudio })
                      .onChange((isOn: boolean) => {
                        this.config.loopAudio = isOn;
                        this.updateConfig();
                      })
                  }.width('100%').alignItems(VerticalAlign.Center)
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                this.BuildSectionTitle('数据管理')

                // 数据管理卡片
                Column() {
                  Row({ space: 8 }) {
                    Button('导出数据').layoutWeight(1).onClick(() => this.exportData())
                    Button('导入数据').layoutWeight(1).onClick(() => this.importData())
                  }.width('100%')
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                this.BuildSectionTitle('账号与云同步')

                // 账号信息卡片
                Column() {
                  Row() {
                    Column() {
                      Text('当前账号').fontSize(16).fontWeight(FontWeight.Medium)
                      Text(this.getAccountDisplay())
                        .fontSize(14).fontColor('#1976D2').margin({ top: 4 })
                    }
                    .alignItems(HorizontalAlign.Start)
                    .layoutWeight(1)
                    if (this.isLoggedIn()) {
                      Button('退出登录')
                        .fontSize(14)
                        .backgroundColor('#F5F5F5')
                        .fontColor('#D32F2F')
                        .height(36)
                        .onClick(() => this.logout())
                    } else {
                      Button('去登录')
                        .fontSize(14)
                        .backgroundColor('#1976D2')
                        .fontColor('#FFFFFF')
                        .height(36)
                        .onClick(() => {
                          router.replaceUrl({ url: 'pages/Login' });
                        })
                    }
                  }.width('100%').alignItems(VerticalAlign.Center)
                }
                .width('100%')
                .padding(16)
                .backgroundColor('#FFFFFF')
                .borderRadius(8)

                Text('版本号: 1.51')
                  .fontSize(12).fontColor('#999999').width('100%').textAlign(TextAlign.Center)
                  .margin({ top: 24, bottom: 24 })
              }
              .width('100%')
              .padding({ left: 16, right: 16, top: 16 })
            }
            .scrollable(ScrollDirection.Vertical)
            .scrollBar(BarState.On)
          }
        }
        .width('100%')
        .layoutWeight(1)
        .backgroundColor('#F5F5F5')
        .justifyContent(FlexAlign.Start)

        // 底部导航栏
        Row() {
          this.BuildBottomTabBar()
        }
        .width('100%')
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#F5F5F5')
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  /**
   * 获取账号显示文本
   */
  private getAccountDisplay(): string {
    const user = ApiClient.getInstance().getUser();
    if (user) {
      return user.username + (user.nickname ? ' (' + user.nickname + ')' : '');
    }
    return '未登录';
  }

  /**
   * 是否已登录
   */
  private isLoggedIn(): boolean {
    return ApiClient.getInstance().isLoggedIn();
  }

  /**
   * 退出登录
   */
  private async logout(): Promise<void> {
    await ApiClient.getInstance().logout();
    SyncService.getInstance().stop();
    promptAction.showToast({ message: '已退出登录', duration: 2000 });
    router.replaceUrl({ url: 'pages/Login' });
  }
}
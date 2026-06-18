import router from '@ohos.router';
import { Config } from '../model/Config';
import { ConfigRepository } from '../repository/ConfigRepository';
import { WebDavSyncService } from '../service/WebDavSyncService';
import { BackupService, ImportResult } from '../service/BackupService';
import { DailyTaskService } from '../service/DailyTaskService';
import { ArticleRepository } from '../repository/ArticleRepository';
import { common } from '@kit.AbilityKit';
import promptAction from '@ohos.promptAction';
import fs from '@ohos.file.fs';
import picker from '@ohos.file.picker';
import util from '@ohos.util';
// 从 EntryAbility 模块引入屏幕常亮控制函数
import { setKeepScreenOn } from '../entryability/EntryAbility';

@Entry
@Component
struct SettingsPage {
  @State config: Config = new Config();
  @State isLoading: boolean = true;
  @State isSyncing: boolean = false;
  @State syncMessage: string = '';
  @State showWebDavConfig: boolean = false;
  @State webdavUrlInput: string = '';
  @State webdavUsernameInput: string = '';
  @State webdavPasswordInput: string = '';
  @State webdavRemotePathInput: string = '/DailyRead';
  @State isExporting: boolean = false;
  @State isImporting: boolean = false;
  @State hasTodayTasks: boolean = false;
  // ===== 坚果云配置指引弹窗 =====
  @State showJianGuoYunGuide: boolean = false;
  private context: common.Context = getContext(this) as common.Context;

  aboutToAppear(): void {
    // SplashPage已经完成了初始化，这里只需要加载配置
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
      // 检查是否有今日任务
      this.hasTodayTasks = await DailyTaskService.getInstance().hasTodayTasks();
    } catch (e) {
      console.error('加载配置失败: ' + JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  async createOrResetTodayTasks(): Promise<void> {
    try {
      if (this.hasTodayTasks) {
        // 重置任务列表
        await DailyTaskService.getInstance().forceRefresh();
        promptAction.showToast({ message: '任务列表已重置', duration: 2000 });
      } else {
        // 创建任务列表
        const allArticles = await ArticleRepository.getInstance().getAllArticles();
        const dailyTaskService = DailyTaskService.getInstance();
        await dailyTaskService.getOrGenerateTodayTasks(allArticles);
        promptAction.showToast({ message: '今日阅读列表已创建', duration: 2000 });
      }
      // 更新状态
      this.hasTodayTasks = await DailyTaskService.getInstance().hasTodayTasks();
      // 触发全局刷新
      AppStorage.set('dataRefreshSignal', Date.now().toString());
    } catch (e) {
      console.error('创建/重置任务列表失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '操作失败', duration: 2000 });
    }
  }

  async updateConfig(): Promise<void> {
    try {
      await ConfigRepository.getInstance().updateConfig(this.config);
    } catch (e) {
      console.error('更新配置失败: ' + JSON.stringify(e));
    }
  }

  async testConnection(): Promise<void> {
    this.isSyncing = true;
    this.syncMessage = '正在测试连接...';
    try {
      const result = await WebDavSyncService.getInstance().testConnection(this.config);
      if (result.success) {
        promptAction.showToast({ message: '连接成功！', duration: 2000 });
        this.syncMessage = '连接成功';
      } else {
        promptAction.showToast({ message: result.errorMessage || '连接失败', duration: 2000 });
        this.syncMessage = '连接失败: ' + (result.errorMessage || '');
      }
    } catch (e) {
      promptAction.showToast({ message: '测试连接出错', duration: 2000 });
      this.syncMessage = '测试连接出错: ' + JSON.stringify(e);
    } finally {
      this.isSyncing = false;
    }
  }

  async downloadFromRemote(): Promise<void> {
    this.isSyncing = true;
    this.syncMessage = '正在从云端下载...';
    try {
      const result = await WebDavSyncService.getInstance().syncFromRemote(this.config);
      if (result.success) {
        const msg: string = '下载成功！文章:' + result.downloadedArticles +
          ', 概念:' + result.downloadedConcepts +
          ', 临床笔记:' + result.downloadedClinicalNotes;
        promptAction.showToast({ message: msg, duration: 3000 });
        this.syncMessage = msg;
        await this.loadConfig();
      } else {
        promptAction.showToast({ message: result.errorMessage || '下载失败', duration: 2000 });
        this.syncMessage = '下载失败: ' + (result.errorMessage || '');
      }
    } catch (e) {
      promptAction.showToast({ message: '下载出错', duration: 2000 });
      this.syncMessage = '下载出错: ' + JSON.stringify(e);
    } finally {
      this.isSyncing = false;
    }
  }

  async uploadToRemote(): Promise<void> {
    this.isSyncing = true;
    this.syncMessage = '正在上传到云端...';
    try {
      const result = await WebDavSyncService.getInstance().syncToRemote(this.config);
      if (result.success) {
        const msg: string = '上传成功！文章:' + result.uploadedArticles +
          ', 概念:' + result.uploadedConcepts +
          ', 临床笔记:' + result.uploadedClinicalNotes;
        promptAction.showToast({ message: msg, duration: 3000 });
        this.syncMessage = msg;
        await this.loadConfig();
      } else {
        promptAction.showToast({ message: result.errorMessage || '上传失败', duration: 2000 });
        this.syncMessage = '上传失败: ' + (result.errorMessage || '');
      }
    } catch (e) {
      promptAction.showToast({ message: '上传出错', duration: 2000 });
      this.syncMessage = '上传出错: ' + JSON.stringify(e);
    } finally {
      this.isSyncing = false;
    }
  }

  async saveWebDavConfig(): Promise<void> {
    this.config.webdavUrl = this.webdavUrlInput;
    this.config.webdavUsername = this.webdavUsernameInput;
    this.config.webdavPassword = this.webdavPasswordInput;
    this.config.webdavRemotePath = this.webdavRemotePathInput;
    await this.updateConfig();
    this.showWebDavConfig = false;
    promptAction.showToast({ message: 'WebDAV配置已保存', duration: 2000 });
  }

  async exportData(): Promise<void> {
    if (this.isExporting) {
      return;
    }
    this.isExporting = true;
    try {
      const jsonContent: string = await BackupService.getInstance().exportToJSON();
      const timeStr: string = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName: string = 'daily_read_backup_' + timeStr + '.json';
      const fallbackDir: string = this.context.filesDir;
      const filePath: string = fallbackDir + '/' + fileName;
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
    const size: number = stat.size;
    if (size <= 0) {
      return '';
    }
    const uint8: Uint8Array = new Uint8Array(size);
    const file: fs.File = fs.openSync(uri, fs.OpenMode.READ_ONLY);
    fs.readSync(file.fd, uint8.buffer);
    fs.closeSync(file);
    const decoder: util.TextDecoder = new util.TextDecoder('utf-8');
    return decoder.decodeWithStream(uint8, { stream: false });
  }

  async importData(): Promise<void> {
    if (this.isImporting) {
      return;
    }
    this.isImporting = true;
    try {
      const documentPicker: picker.DocumentViewPicker = new picker.DocumentViewPicker();
      const selectOpts: picker.DocumentSelectOptions = new picker.DocumentSelectOptions();
      selectOpts.fileSuffixFilters = ['.json'];
      selectOpts.maxSelectNumber = 1;
      const resultUris: string[] = await documentPicker.select(selectOpts);
      if (!resultUris || resultUris.length === 0) {
        promptAction.showToast({ message: '未选择文件', duration: 2000 });
        this.isImporting = false;
        return;
      }
      let jsonContent: string = '';
      try {
        jsonContent = this.readJsonFromUri(resultUris[0]);
      } catch (readErr) {
        promptAction.showToast({ message: '读取文件失败', duration: 3000 });
        this.isImporting = false;
        return;
      }
      if (jsonContent.length === 0) {
        promptAction.showToast({ message: '文件为空', duration: 2000 });
        this.isImporting = false;
        return;
      }

      const result: ImportResult = await BackupService.getInstance().importFromJSON(jsonContent, true);
      if (result.success) {
        const msg: string = '导入成功！文章:' + result.importedArticles +
          ', 概念:' + result.importedConcepts;
        promptAction.showToast({ message: msg, duration: 3000 });
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

  build(): void {
    Stack() {
      Column() {
        Text('设置')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .padding({ left: 16, right: 16, top: 16, bottom: 8 })
          .width('100%')
          .backgroundColor('#FFFFFF')

        if (this.isLoading) {
          Column() {
            LoadingProgress()
              .width(40)
              .height(40)
            Text('加载中...')
              .fontSize(14)
              .fontColor('#999999')
              .margin({ top: 12 })
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#F5F5F5')
        } else {
          Scroll() {
            Column({ space: 16 }) {
              // 阅读设置
              Text('阅读设置')
                .fontSize(18)
                .fontWeight(FontWeight.Bold)
                .width('100%')
                .padding({ left: 16, right: 16, top: 8 })

              // 文章管理入口
              Column() {
                Row() {
                  Column() {
                    Text('文章管理')
                      .fontSize(16)
                      .fontWeight(FontWeight.Medium)
                    Text('添加、编辑和管理你的文章')
                      .fontSize(12)
                      .fontColor('#999999')
                      .margin({ top: 4 })
                  }
                  .alignItems(HorizontalAlign.Start)
                  .layoutWeight(1)
                  Text('›')
                    .fontSize(22)
                    .fontColor('#999999')
                }
                .width('100%')
                .onClick(() => {
                  router.pushUrl({ url: 'pages/ArticleManage' });
                })
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(8)

              // 每日阅读时间卡片
              Column() {
                Text('每日阅读时间')
                  .fontSize(16)
                  .fontWeight(FontWeight.Medium)
                  .width('100%')
                Row() {
                  Text(`${this.config.dailyMinutes} 分钟`)
                    .fontSize(16)
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
                }
                .width('100%')
                .margin({ top: 8 })
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(8)

              // 目标完成率卡片
              Column() {
                Text('目标完成率')
                  .fontSize(16)
                  .fontWeight(FontWeight.Medium)
                  .width('100%')
                Row() {
                  Text(`${Math.round(this.config.targetCheckRate)}%`)
                    .fontSize(16)
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
                }
                .width('100%')
                .margin({ top: 8 })
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(8)

              // 保持屏幕常亮卡片
              Column() {
                Row() {
                  Column() {
                    Text('保持屏幕常亮')
                      .fontSize(16)
                      .fontWeight(FontWeight.Medium)
                    Text('应用在前台时屏幕不会自动休眠')
                      .fontSize(12)
                      .fontColor('#999999')
                      .margin({ top: 4 })
                  }
                  .alignItems(HorizontalAlign.Start)
                  .layoutWeight(1)

                  Toggle({ type: ToggleType.Switch, isOn: this.config.keepScreenOn })
                    .onChange((isOn: boolean) => {
                      this.config.keepScreenOn = isOn;
                      this.updateConfig();
                      // 立即应用到窗口（调用 EntryAbility 暴露的模块级函数）
                      try {
                        setKeepScreenOn(isOn);
                        console.info('Settings: keepScreenOn 已应用, isOn = ' + isOn);
                      } catch (e) {
                        console.error('Settings: 应用 keepScreenOn 失败: ' + JSON.stringify(e));
                      }
                    })
                }
                .width('100%')
                .alignItems(VerticalAlign.Center)
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(8)

              // 创建/重置今日阅读列表
              Column() {
                Row() {
                  Column() {
                    Text(this.hasTodayTasks ? '任务已锁定' : '创建今日阅读列表')
                      .fontSize(16)
                      .fontWeight(FontWeight.Medium)
                    Text(this.hasTodayTasks ? '点击按钮可重置今日任务列表' : '创建今日的阅读任务列表')
                      .fontSize(12)
                      .fontColor('#999999')
                      .margin({ top: 4 })
                  }
                  .alignItems(HorizontalAlign.Start)
                  .layoutWeight(1)

                  Button(this.hasTodayTasks ? '点击重置' : '创建')
                    .fontSize(14)
                    .backgroundColor(this.hasTodayTasks ? '#FF9800' : '#1976D2')
                    .fontColor('#FFFFFF')
                    .onClick(() => {
                      this.createOrResetTodayTasks();
                    })
                }
                .width('100%')
                .alignItems(VerticalAlign.Center)
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(8)

              // 数据管理
              Text('数据管理')
                .fontSize(18)
                .fontWeight(FontWeight.Bold)
                .width('100%')
                .padding({ left: 16, right: 16, top: 8 })

              Row({ space: 8 }) {
                Button('导出数据')
                  .layoutWeight(1)
                  .onClick(() => {
                    this.exportData();
                  })
                Button('导入数据')
                  .layoutWeight(1)
                  .onClick(() => {
                    this.importData();
                  })
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(8)

              // WebDAV同步
              Text('WebDAV 同步')
                .fontSize(18)
                .fontWeight(FontWeight.Bold)
                .width('100%')
                .padding({ left: 16, right: 16, top: 8 })

              Column() {
                Row() {
                  Column() {
                    Text('启用 WebDAV 同步')
                      .fontSize(16)
                      .fontWeight(FontWeight.Medium)
                    if (this.config.lastSyncTime) {
                      Text(`上次同步: ${this.config.lastSyncTime}`)
                        .fontSize(12)
                        .fontColor('#999999')
                        .margin({ top: 4 })
                    }
                  }
                  .alignItems(HorizontalAlign.Start)
                  .layoutWeight(1)

                  Toggle({ type: ToggleType.Switch, isOn: this.config.autoSyncWebDav })
                    .onChange((isOn: boolean) => {
                      this.config.autoSyncWebDav = isOn;
                      this.updateConfig();
                    })
                }
                .width('100%')
                .alignItems(VerticalAlign.Center)

                if (this.config.autoSyncWebDav) {
                  Row() {
                    Column() {
                      Text('自动同步')
                        .fontSize(16)
                        .fontWeight(FontWeight.Medium)
                      Text('数据增删改时自动上传到云端')
                        .fontSize(12)
                        .fontColor('#999999')
                        .margin({ top: 4 })
                    }
                    .alignItems(HorizontalAlign.Start)
                    .layoutWeight(1)

                    Toggle({ type: ToggleType.Switch, isOn: this.config.autoSyncEnabled })
                      .onChange((isOn: boolean) => {
                        this.config.autoSyncEnabled = isOn;
                        this.updateConfig();
                      })
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Center)
                  .margin({ top: 12 })

                  Text('同步内容设置')
                    .fontSize(14)
                    .fontWeight(FontWeight.Medium)
                    .width('100%')
                    .margin({ top: 12 })

                  Row() {
                    Text('同步文章数据')
                      .fontSize(14)
                      .layoutWeight(1)
                    Toggle({ type: ToggleType.Switch, isOn: this.config.syncArticlesEnabled })
                      .onChange((val: boolean) => {
                        this.config.syncArticlesEnabled = val;
                        this.updateConfig();
                      })
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Center)
                  .margin({ top: 8 })

                  Row() {
                    Text('同步概念数据')
                      .fontSize(14)
                      .layoutWeight(1)
                    Toggle({ type: ToggleType.Switch, isOn: this.config.syncConceptsEnabled })
                      .onChange((val: boolean) => {
                        this.config.syncConceptsEnabled = val;
                        this.updateConfig();
                      })
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Center)
                  .margin({ top: 8 })

                  Row() {
                    Text('同步临床笔记数据')
                      .fontSize(14)
                      .layoutWeight(1)
                    Toggle({ type: ToggleType.Switch, isOn: this.config.syncClinicalNotesEnabled })
                      .onChange((val: boolean) => {
                        this.config.syncClinicalNotesEnabled = val;
                        this.updateConfig();
                      })
                  }
                  .width('100%')
                  .alignItems(VerticalAlign.Center)
                  .margin({ top: 8 })

                  Button('配置 WebDAV')
                    .width('100%')
                    .margin({ top: 16 })
                    .onClick(() => {
                      this.showWebDavConfig = true;
                    })

                  Text('坚果云 WebDAV 同步配置指引')
                    .fontSize(14)
                    .fontColor('#1976D2')
                    .width('100%')
                    .textAlign(TextAlign.Center)
                    .margin({ top: 12 })
                    .onClick(() => {
                      this.showJianGuoYunGuide = true;
                    })

                  if (this.isSyncing) {
                    Row() {
                      LoadingProgress()
                        .width(20)
                        .height(20)
                      Text(this.syncMessage)
                        .fontSize(14)
                        .fontColor('#666666')
                        .margin({ left: 8 })
                    }
                    .width('100%')
                    .justifyContent(FlexAlign.Center)
                    .margin({ top: 8 })
                  } else {
                    Row({ space: 8 }) {
                      Button('测试连接')
                        .layoutWeight(1)
                        .onClick(() => {
                          this.testConnection();
                        })
                      Button('下载')
                        .layoutWeight(1)
                        .onClick(() => {
                          this.downloadFromRemote();
                        })
                      Button('上传')
                        .layoutWeight(1)
                        .onClick(() => {
                          this.uploadToRemote();
                        })
                    }
                    .width('100%')
                    .margin({ top: 8 })
                  }
                }
              }
              .width('100%')
              .padding(16)
              .backgroundColor('#FFFFFF')
              .borderRadius(8)

              Text('版本号: 1.6.0')
                .fontSize(12)
                .fontColor('#999999')
                .width('100%')
                .textAlign(TextAlign.Center)
                .margin({ top: 24, bottom: 24 })
            }
            .width('100%')
            .padding({ left: 16, right: 16, top: 16, bottom: 80 })
          }
          .width('100%')
          .layoutWeight(1)
          .backgroundColor('#F5F5F5')
        }

        // 底部功能栏（与首页一致）
        this.BottomTabBar()
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#F5F5F5')

      // WebDAV配置弹窗
      if (this.showWebDavConfig) {
        Column() {
          Column() {
            Text('WebDAV 配置')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center)

            Column() {
              Text('服务器地址')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%')
              TextInput({ text: this.webdavUrlInput, placeholder: '例如: http://192.168.1.100:8080' })
                .width('100%')
                .onChange((value: string) => {
                  this.webdavUrlInput = value;
                })
            }
            .width('100%')
            .margin({ top: 16 })

            Column() {
              Text('同步目录')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%')
              TextInput({ text: this.webdavRemotePathInput, placeholder: '/DailyRead' })
                .width('100%')
                .onChange((value: string) => {
                  this.webdavRemotePathInput = value;
                })
            }
            .width('100%')
            .margin({ top: 12 })

            Column() {
              Text('用户名')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%')
              TextInput({ text: this.webdavUsernameInput, placeholder: '请输入用户名' })
                .width('100%')
                .onChange((value: string) => {
                  this.webdavUsernameInput = value;
                })
            }
            .width('100%')
            .margin({ top: 12 })

            Column() {
              Text('密码')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%')
              TextInput({ text: this.webdavPasswordInput, placeholder: '请输入密码' })
                .width('100%')
                .type(InputType.Password)
                .onChange((value: string) => {
                  this.webdavPasswordInput = value;
                })
            }
            .width('100%')
            .margin({ top: 12 })

            Row() {
              Button('取消')
                .width('45%')
                .backgroundColor('#F5F5F5')
                .fontColor('#333333')
                .onClick(() => {
                  this.showWebDavConfig = false;
                })
              Button('保存')
                .width('45%')
                .onClick(() => {
                  this.saveWebDavConfig();
                })
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceAround)
            .margin({ top: 24 })
          }
          .width('85%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16)
        }
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0,0,0,0.5)')
        .justifyContent(FlexAlign.Center)
        .onClick(() => {
          this.showWebDavConfig = false;
        })
      }

      // 坚果云配置指引弹窗
      if (this.showJianGuoYunGuide) {
        Column() {
          Column() {
            Text('坚果云 WebDAV 配置指引')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center)

            Scroll() {
              Column({ space: 8 }) {
                // 步骤1
                Text('1. 在Windows坚果云客户端内新建名为"DailyRead"的文件夹')
                  .fontSize(26)
                  .fontColor('#333333')
                  .width('100%')
                  .textAlign(TextAlign.Start)

                Column() {
                  Image($rawfile('01.png'))
                    .width('80%')
                    .aspectRatio(1.0)
                    .objectFit(ImageFit.ScaleDown)
                    .borderRadius(8)
                }
                .width('100%')
                .alignItems(HorizontalAlign.Start)

                // 步骤2
                Text('2. 在设置中选择第三方应用管理')
                  .fontSize(26)
                  .fontColor('#333333')
                  .width('100%')
                  .textAlign(TextAlign.Start)

                Column() {
                  Image($rawfile('02.png'))
                    .width('80%')
                    .aspectRatio(1.0)
                    .objectFit(ImageFit.ScaleDown)
                    .borderRadius(8)
                }
                .width('100%')
                .alignItems(HorizontalAlign.Start)

                // 步骤3
                Text('3. 点击添加应用密码，获取WebDAV服务器、用户名、密码，并依次填入WebDAV配置中')
                  .fontSize(26)
                  .fontColor('#333333')
                  .width('100%')
                  .textAlign(TextAlign.Start)

                Column() {
                  Image($rawfile('03.png'))
                    .width('80%')
                    .aspectRatio(1.0)
                    .objectFit(ImageFit.ScaleDown)
                    .borderRadius(8)
                }
                .width('100%')
                .alignItems(HorizontalAlign.Start)
              }
              .width('100%')
              .alignItems(HorizontalAlign.Start)
              .padding({ top: 16 })
            }
            .width('100%')
            .layoutWeight(1)

            Button('关闭')
              .width('100%')
              .margin({ top: 16 })
              .onClick(() => {
                this.showJianGuoYunGuide = false;
              })
          }
          .width('85%')
          .height('70%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16)
        }
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0,0,0,0.5)')
        .justifyContent(FlexAlign.Center)
        .onClick(() => {
          this.showJianGuoYunGuide = false;
        })
      }
    }
    .width('100%')
    .height('100%')
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
      })

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
      })

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
      })

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
      })

      Column({ space: 2 }) {
        Text('⚙')
          .fontSize(16)
          .fontColor('#999999');
        Text('设置')
          .fontSize(11)
          .fontColor('#1976D2')
          .fontWeight(FontWeight.Bold);
      }
      .layoutWeight(1)
      .justifyContent(FlexAlign.Center)
      .padding({ top: 8, bottom: 8 })
    }
    .width('100%')
    .backgroundColor('#FFFFFF')
  }
}

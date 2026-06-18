import router from '@ohos.router';
import { Article } from '../model/Article';
import { ArticleRepository } from '../repository/ArticleRepository';
import { ImageCompressionService, SizedPixelMap } from '../service/ImageCompressionService';
import promptAction from '@ohos.promptAction';
import image from '@ohos.multimedia.image';
import fs from '@ohos.file.fs';
import { common } from '@kit.AbilityKit';

@Entry
@Component
struct ArticleManagePage {
  @State articles: Article[] = [];
  @State isLoading: boolean = true;
  @State refreshKey: number = 0; // 强制刷新：变化后 ForEach 用新 key 重建组件

  // ===== 关键字搜索 =====
  @State searchKeyword: string = '';

  // ===== 添加/编辑文章 Dialog =====
  @State showAddDialog: boolean = false;
  @State editingArticle: Article | null = null;
  @State newTitle: string = '';
  @State newContent: string = '';
  @State newIsReading: boolean = true;
  @State newIsRequired: boolean = false;
  @State newImageWebp: string = '';
  @State previewPixelMap: image.PixelMap | null = null;

  // ===== 独立目标率 Dialog =====
  @State showRateDialog: boolean = false;
  @State rateTargetArticle: Article | null = null;
  @State tempRate: number = 30;

  // ===== 长按多选 - 批量删除 =====
  @State isMultiSelectMode: boolean = false;
  @State selectedIds: number[] = [];

  // ===== 根据关键字过滤文章 =====
  // 匹配规则：关键字为空返回全部；否则在标题或内容中做忽略大小写的子串匹配
  private getFilteredArticles(): Article[] {
    const keyword: string = this.searchKeyword.trim();
    if (keyword.length === 0) {
      return this.articles;
    }
    const lowerKeyword: string = keyword.toLowerCase();
    return this.articles.filter((a: Article): boolean => {
      const titleLower: string = a.title.toLowerCase();
      const contentLower: string = a.content.toLowerCase();
      const titleHit: boolean = titleLower.indexOf(lowerKeyword) !== -1;
      const contentHit: boolean = contentLower.indexOf(lowerKeyword) !== -1;
      return titleHit || contentHit;
    });
  }

  aboutToAppear(): void {
    this.loadData();
  }

  aboutToShow(): void {
    this.loadData();
  }

  async loadData(): Promise<void> {
    this.isLoading = true;
    try {
      const list: Article[] = await ArticleRepository.getInstance().getAllArticles();
      // 整体赋值触发 @State 更新
      this.articles = list;
      // refreshKey 自增，确保 ForEach 用新 key 重建所有 ListItem（含 Toggle/Checkbox 内部状态）
      this.refreshKey = this.refreshKey + 1;
    } catch (e) {
      console.error('加载数据失败: ' + JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  async saveArticle(): Promise<void> {
    if (this.newTitle.length === 0) {
      promptAction.showToast({ message: '请输入标题', duration: 2000 });
      return;
    }
    if (this.newContent.length === 0 && this.newImageWebp.length === 0) {
      promptAction.showToast({ message: '请输入内容或上传图片', duration: 2000 });
      return;
    }

    try {
      const article: Article = new Article();
      article.title = this.newTitle;
      article.content = this.newContent;
      article.contentHtml = '';
      // 简单统计中文字数
      let count: number = 0;
      for (let i: number = 0; i < this.newContent.length; i++) {
        const charCode: number = this.newContent.charCodeAt(i);
        if (charCode >= 0x4E00 && charCode <= 0x9FFF) {
          count = count + 1;
        }
      }
      article.chineseChars = count;
      article.isReading = this.newIsReading;
      article.isRequired = this.newIsRequired;
      article.requiredDays = '';
      article.useIndependentCheckRate = false;
      article.independentCheckRate = 30.0;
      article.isLongArticle = false;
      article.imagewebp = this.newImageWebp;
      article.createTime = new Date().toISOString();
      article.lastModified = article.createTime;

      if (this.editingArticle !== null) {
        article.id = this.editingArticle.id;
        article.fontFamily = this.editingArticle.fontFamily;
        article.fontSize = this.editingArticle.fontSize;
        article.fontColor = this.editingArticle.fontColor;
        article.isBold = this.editingArticle.isBold;
        // 编辑时保留原有 imagewebp（或用户刚上传的新图片覆盖原值）
        if (this.newImageWebp.length === 0 && this.editingArticle.imagewebp && this.editingArticle.imagewebp.length > 0) {
          article.imagewebp = this.editingArticle.imagewebp;
        } else {
          article.imagewebp = this.newImageWebp;
        }
        // 保留原有完成率
        article.completionRate = this.editingArticle.completionRate;
        await ArticleRepository.getInstance().updateArticle(article);
        promptAction.showToast({ message: '修改成功', duration: 2000 });
      } else {
        await ArticleRepository.getInstance().insertArticle(article);
        promptAction.showToast({ message: '添加成功', duration: 2000 });
      }

      this.showAddDialog = false;
      this.resetForm();
      await this.loadData();
    } catch (e) {
      console.error('保存文章失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '保存失败', duration: 2000 });
    }
  }

  async deleteArticle(article: Article): Promise<void> {
    promptAction.showDialog({
      title: '确认删除',
      message: `确定要删除文章「${article.title}」吗？`,
      buttons: [
        { text: '取消', color: '#666666' },
        { text: '删除', color: '#D32F2F' }
      ]
    }).then((value) => {
      if (value.index === 1) {
        this.doDeleteArticle(article);
      }
    }).catch((err: Error) => {
      console.error('对话框异常: ' + JSON.stringify(err));
    });
  }

  async doDeleteArticle(article: Article): Promise<void> {
    try {
      await ArticleRepository.getInstance().deleteArticle(article.id);
      promptAction.showToast({ message: '删除成功', duration: 2000 });
      await this.loadData();
    } catch (e) {
      console.error('删除文章失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '删除失败', duration: 2000 });
    }
  }

  async toggleIndependentCheckRate(article: Article, newValue: boolean): Promise<void> {
    if (newValue) {
      // 打开开关：先弹出目标率设置对话框，用户确认后再写入并刷新
      this.rateTargetArticle = article;
      this.tempRate = Math.round(article.independentCheckRate > 0 ? article.independentCheckRate : 30);
      this.showRateDialog = true;
    } else {
      // 关闭开关：清零独立目标率并写入DB刷新
      try {
        const updateArticle: Article = article;
        updateArticle.useIndependentCheckRate = false;
        updateArticle.independentCheckRate = 0;
        updateArticle.lastModified = new Date().toISOString();
        await ArticleRepository.getInstance().updateArticle(updateArticle);
        AppStorage.set('dataRefreshSignal', Date.now().toString());
        await this.loadData();
      } catch (e) {
        console.error('更新独立目标率失败: ' + JSON.stringify(e));
        promptAction.showToast({ message: '更新失败', duration: 2000 });
      }
    }
  }

  async saveIndependentCheckRate(): Promise<void> {
    if (this.rateTargetArticle !== null) {
      try {
        const updateArticle: Article = this.rateTargetArticle;
        updateArticle.useIndependentCheckRate = true;
        updateArticle.independentCheckRate = this.tempRate;
        updateArticle.lastModified = new Date().toISOString();
        await ArticleRepository.getInstance().updateArticle(updateArticle);
        promptAction.showToast({ message: '目标率已设置', duration: 2000 });
        this.showRateDialog = false;
        this.rateTargetArticle = null;
        AppStorage.set('dataRefreshSignal', Date.now().toString());
        await this.loadData();
      } catch (e) {
        console.error('保存独立目标率失败: ' + JSON.stringify(e));
        promptAction.showToast({ message: '保存失败', duration: 2000 });
      }
    }
  }

  async cancelIndependentCheckRate(): Promise<void> {
    this.showRateDialog = false;
    this.rateTargetArticle = null;
    // 用户取消：列表中的开关视觉状态可能已被 Toggle 切到"开"，重新加载数据恢复真实状态
    await this.loadData();
  }

  resetForm(): void {
    this.newTitle = '';
    this.newContent = '';
    this.newIsReading = true;
    this.newIsRequired = false;
    this.newImageWebp = '';
    this.previewPixelMap = null;
    this.editingArticle = null;
  }

  /**
   * 选择图片并压缩为 WebP 格式
   */
  async pickImage(): Promise<void> {
    try {
      const ctx: common.Context = getContext(this) as common.Context;
      ImageCompressionService.getInstance().setContext(ctx);

      const base64: string = await ImageCompressionService.getInstance().pickAndCompressToWebP();
      if (base64 && base64.length > 0) {
        this.newImageWebp = base64;
        try {
          const sized: SizedPixelMap = await ImageCompressionService.base64ToPixelMap(
            ctx, base64
          );
          this.previewPixelMap = sized.pixelMap;
        } catch (previewErr) {
          console.error('ArticleManage: 预览图片解码失败: ' + JSON.stringify(previewErr));
          this.previewPixelMap = null;
        }
      }
    } catch (e) {
      console.error('选择图片失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '图片处理失败，请重试', duration: 2000 });
    }
  }

  removeImage(): void {
    this.newImageWebp = '';
    this.previewPixelMap = null;
  }

  async toggleIsReading(article: Article, newValue: boolean): Promise<void> {
    try {
      const updateArticle: Article = article;
      updateArticle.isReading = newValue;
      updateArticle.lastModified = new Date().toISOString();
      await ArticleRepository.getInstance().updateArticle(updateArticle);
      AppStorage.set('dataRefreshSignal', Date.now().toString());
      await this.loadData();
    } catch (e) {
      console.error('更新阅读状态失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '更新失败', duration: 2000 });
    }
  }

  // ===== 多选模式 =====
  enterMultiSelectMode(): void {
    this.isMultiSelectMode = true;
    this.selectedIds = [];
  }

  exitMultiSelectMode(): void {
    this.isMultiSelectMode = false;
    this.selectedIds = [];
  }

  toggleSelect(id: number): void {
    const idx = this.selectedIds.indexOf(id);
    if (idx >= 0) {
      this.selectedIds.splice(idx, 1);
    } else {
      this.selectedIds.push(id);
    }
  }

  selectAll(): void {
    const visibleArticles: Article[] = this.getFilteredArticles();
    const visibleIds: number[] = visibleArticles.map((a) => a.id);
    // 仅判断"当前可见文章是否全部已选中"：如果 visibleIds 中的每一个都在 selectedIds 里，就取消全选
    let allVisibleSelected: boolean = true;
    for (let i: number = 0; i < visibleIds.length; i++) {
      if (this.selectedIds.indexOf(visibleIds[i]) === -1) {
        allVisibleSelected = false;
        break;
      }
    }
    if (visibleIds.length > 0 && allVisibleSelected) {
      // 取消：把可见文章的 id 从 selectedIds 中移除，保留其它 id 不变
      const remaining: number[] = [];
      for (let j: number = 0; j < this.selectedIds.length; j++) {
        if (visibleIds.indexOf(this.selectedIds[j]) === -1) {
          remaining.push(this.selectedIds[j]);
        }
      }
      this.selectedIds = remaining;
    } else {
      // 合并当前可见文章 id 到 selectedIds（去重）
      const merged: number[] = [...this.selectedIds];
      for (let k: number = 0; k < visibleIds.length; k++) {
        if (merged.indexOf(visibleIds[k]) === -1) {
          merged.push(visibleIds[k]);
        }
      }
      this.selectedIds = merged;
    }
  }

  confirmBatchDelete(): void {
    if (this.selectedIds.length === 0) {
      promptAction.showToast({ message: '请先选择要删除的文章', duration: 2000 });
      return;
    }
    promptAction.showDialog({
      title: '批量删除',
      message: `确定要删除选中的 ${this.selectedIds.length} 篇文章吗？`,
      buttons: [
        { text: '取消', color: '#666666' },
        { text: '删除', color: '#D32F2F' }
      ]
    }).then((value) => {
      if (value.index === 1) {
        this.doBatchDelete();
      }
    }).catch((err: Error) => {
      console.error('批量删除对话框异常: ' + JSON.stringify(err));
    });
  }

  async doBatchDelete(): Promise<void> {
    try {
      const ids: number[] = [...this.selectedIds];
      for (let i: number = 0; i < ids.length; i++) {
        await ArticleRepository.getInstance().deleteArticle(ids[i]);
      }
      promptAction.showToast({ message: `已删除 ${ids.length} 篇文章`, duration: 2000 });
      this.exitMultiSelectMode();
      await this.loadData();
    } catch (e) {
      console.error('批量删除失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '删除失败', duration: 2000 });
    }
  }

  // ===== 页面主体 =====
  build(): void {
    Stack() {
      Column() {
        Column() {
          // 模式标题栏：普通模式 / 多选模式
          if (!this.isMultiSelectMode) {
            Row() {
              Text('文章管理')
                .fontSize(24)
                .fontWeight(FontWeight.Bold)
                .fontColor('#333333');
              Blank();
              Text('多选')
                .fontSize(14)
                .fontColor('#1976D2')
                .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                .onClick(() => {
                  this.enterMultiSelectMode();
                });
              Text('+')
                .fontSize(28)
                .fontWeight(FontWeight.Bold)
                .fontColor('#1976D2')
                .padding({ left: 12, right: 12, top: 4, bottom: 4 })
                .onClick(() => {
                  this.resetForm();
                  this.showAddDialog = true;
                });
            }
            .width('100%');
          } else {
            Row() {
              Text(`已选 ${this.selectedIds.length}`)
                .fontSize(16)
                .fontWeight(FontWeight.Bold)
                .fontColor('#333333');
              Blank();
              Text('全选')
                .fontSize(14)
                .fontColor('#1976D2')
                .padding({ left: 10, right: 10, top: 6, bottom: 6 })
                .onClick(() => {
                  this.selectAll();
                });
              Text('删除')
                .fontSize(14)
                .fontColor('#D32F2F')
                .padding({ left: 10, right: 10, top: 6, bottom: 6 })
                .backgroundColor('#FFEBEE')
                .borderRadius(4)
                .margin({ left: 8 })
                .onClick(() => {
                  this.confirmBatchDelete();
                });
              Text('取消')
                .fontSize(14)
                .fontColor('#666666')
                .padding({ left: 10, right: 10, top: 6, bottom: 6 })
                .margin({ left: 8 })
                .onClick(() => {
                  this.exitMultiSelectMode();
                });
            }
            .width('100%');
          }

          // ===== 搜索输入框（两种模式下都显示） =====
          // 输入关键字后，实时过滤标题或内容中包含关键字的文章
          Row() {
            Text('🔍')
              .fontSize(16)
              .margin({ right: 8 });
            TextInput({
              text: this.searchKeyword,
              placeholder: '输入关键字搜索文章标题或内容'
            })
              .layoutWeight(1)
              .height(36)
              .backgroundColor('#F5F5F5')
              .borderRadius(18)
              .padding({ left: 12, right: 12 })
              .fontSize(14)
              .onChange((value: string) => {
                this.searchKeyword = value;
              });
            if (this.searchKeyword.length > 0) {
              Text('✕')
                .fontSize(16)
                .fontColor('#999999')
                .padding({ left: 8 })
                .onClick(() => {
                  this.searchKeyword = '';
                });
            }
          }
          .width('100%')
          .margin({ top: 12 });
        }
        .width('100%')
        .padding({ left: 16, right: 16, top: 16, bottom: 12 })
        .backgroundColor('#FFFFFF');

        // ===== 搜索结果提示 =====
        if (!this.isLoading && this.searchKeyword.trim().length > 0) {
          Row() {
            Text(`搜索"${this.searchKeyword.trim()}"，共找到 ${this.getFilteredArticles().length} 篇文章`)
              .fontSize(13)
              .fontColor('#1976D2');
          }
          .width('100%')
          .padding({ left: 16, right: 16, top: 8, bottom: 8 });
        }

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
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#F5F5F5');
        } else if (this.getFilteredArticles().length === 0) {
          Column() {
            if (this.searchKeyword.trim().length > 0) {
              Text('未找到匹配的文章')
                .fontSize(16)
                .fontColor('#999999');
              Text('请尝试更换关键字或清除搜索')
                .fontSize(13)
                .fontColor('#BBBBBB')
                .margin({ top: 8 });
            } else {
              Text('暂无文章')
                .fontSize(16)
                .fontColor('#999999');
            }
          }
          .width('100%')
          .layoutWeight(1)
          .justifyContent(FlexAlign.Center)
          .backgroundColor('#F5F5F5');
        } else {
          List() {
            ForEach(this.getFilteredArticles(), (item: Article) => {
              ListItem() {
                this.ArticleItemBuilder(item);
              }
            }, (item: Article) => item.id.toString() + '_' + this.refreshKey.toString());
          }
          .width('100%')
          .layoutWeight(1)
          .backgroundColor('#F5F5F5');
        }

        this.BottomTabBar();
      }
      .width('100%')
      .height('100%')
      .backgroundColor('#F5F5F5');

      // ===== 添加/编辑文章 Dialog =====
      if (this.showAddDialog) {
        Column() {
          Column() {
            Text(this.editingArticle !== null ? '编辑文章' : '添加文章')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center);

            Column() {
              Text('标题')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.newTitle, placeholder: '请输入标题' })
                .width('100%')
                .onChange((value: string) => {
                  this.newTitle = value;
                });
            }
            .width('100%')
            .margin({ top: 16 });

            Column() {
              Text('内容')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextArea({ text: this.newContent, placeholder: '请输入内容' })
                .width('100%')
                .height(150)
                .onChange((value: string) => {
                  this.newContent = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Row() {
              Checkbox({ name: 'isReading' })
                .select(this.newIsReading)
                .onChange((checked: boolean) => {
                  this.newIsReading = checked;
                });
              Text('阅读中')
                .fontSize(14)
                .margin({ left: 8 });
            }
            .width('100%')
            .margin({ top: 12 });

            Row() {
              Checkbox({ name: 'isRequired' })
                .select(this.newIsRequired)
                .onChange((checked: boolean) => {
                  this.newIsRequired = checked;
                });
              Text('必读')
                .fontSize(14)
                .margin({ left: 8 });
            }
            .width('100%')
            .margin({ top: 8 });

            // ===== 图片上传区块 =====
            Column() {
              if (this.newImageWebp.length > 0 && this.previewPixelMap !== null) {
                // 显示图片预览
                Row() {
                  Image(this.previewPixelMap)
                    .width(120)
                    .height(120)
                    .borderRadius(8)
                    .margin({ right: 12 });
                  Column({ space: 6 }) {
                    Text('✓ 已添加图片')
                      .fontSize(13)
                      .fontColor('#1976D2');
                    Text('已压缩为 WebP (<25KB)')
                      .fontSize(12)
                      .fontColor('#999999');
                  }
                  .alignItems(HorizontalAlign.Start);
                  Blank();
                  Text('×移除')
                    .fontSize(13)
                    .fontColor('#D32F2F')
                    .onClick(() => {
                      this.removeImage();
                    });
                }
                .width('100%');
              } else {
                // 未添加图片，显示上传按钮
                Row() {
                  Text('🖼')
                    .fontSize(20)
                    .margin({ right: 12 });
                  Column({ space: 4 }) {
                    Text('上传图片')
                      .fontSize(14)
                      .fontColor('#333333');
                    Text('将转换为 WebP 格式 (<25KB)')
                      .fontSize(12)
                      .fontColor('#999999');
                  }
                  .alignItems(HorizontalAlign.Start);
                  Blank();
                  Text('选择')
                    .fontSize(14)
                    .fontColor('#FFFFFF')
                    .backgroundColor('#1976D2')
                    .padding({ left: 16, right: 16, top: 6, bottom: 6 })
                    .borderRadius(6)
                    .onClick(() => {
                      this.pickImage();
                    });
                }
                .width('100%');
              }
            }
            .width('100%')
            .padding(12)
            .margin({ top: 12 })
            .border({ width: 1, color: '#E0E0E0' })
            .borderRadius(8);

            Row() {
              Button('取消')
                .width('45%')
                .backgroundColor('#F5F5F5')
                .fontColor('#333333')
                .onClick(() => {
                  this.showAddDialog = false;
                  this.resetForm();
                });
              Button('保存')
                .width('45%')
                .onClick(() => {
                  this.saveArticle();
                });
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceAround)
            .margin({ top: 24 });
          }
          .width('90%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16);
        }
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0,0,0,0.5)')
        .justifyContent(FlexAlign.Center);
      }

      // ===== 独立目标率设置 Dialog =====
      if (this.showRateDialog) {
        Column() {
          Column() {
            Text('设置独立目标率')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center);

            Row() {
              Slider({
                value: this.tempRate,
                min: 1,
                max: 100,
                step: 1,
                style: SliderStyle.OutSet
              })
                .blockColor('#1976D2')
                .trackColor('#E3F2FD')
                .selectedColor('#1976D2')
                .layoutWeight(1)
                .onChange((value: number) => {
                  this.tempRate = Math.round(value);
                });

              Text(`${this.tempRate}%`)
                .fontSize(16)
                .fontColor('#1976D2')
                .fontWeight(FontWeight.Bold)
                .width(60)
                .textAlign(TextAlign.End)
                .margin({ left: 8 });
            }
            .width('100%')
            .margin({ top: 24 });

            Row() {
              Button('取消')
                .width('45%')
                .backgroundColor('#F5F5F5')
                .fontColor('#333333')
                .onClick(() => {
                  this.cancelIndependentCheckRate();
                });
              Button('保存')
                .width('45%')
                .onClick(() => {
                  this.saveIndependentCheckRate();
                });
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceAround)
            .margin({ top: 24 });
          }
          .width('90%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16);
        }
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0,0,0,0.5)')
        .justifyContent(FlexAlign.Center);
      }
    }
    .width('100%')
    .height('100%');
  }

  @Builder
  ArticleItemBuilder(item: Article): void {
    Column() {
      Row() {
        if (this.isMultiSelectMode) {
          Checkbox({ name: 'select' + item.id })
            .select(this.selectedIds.indexOf(item.id) >= 0)
            .onChange((value: boolean) => {
              this.toggleSelect(item.id);
            })
            .margin({ right: 10 });
        }

        // 左侧：标题 + 阅读状态标签 + 字数完成率
        Column({ space: 4 }) {
          Row({ space: 8 }) {
            Text(item.title)
              .fontSize(18)
              .fontWeight(FontWeight.Bold)
              .fontColor('#333333')
              .maxLines(1)
              .textOverflow({ overflow: TextOverflow.Ellipsis });

            if (item.isRequired) {
              Text('★')
                .fontSize(18)
                .fontColor('#D32F2F')
                .margin({ left: 4 });
            }

            Blank();

            if (item.isReading) {
              Text('阅读中')
                .fontSize(11)
                .backgroundColor('#1976D2')
                .fontColor('#FFFFFF')
                .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                .borderRadius(10);
            } else {
              Text('已暂停')
                .fontSize(11)
                .fontColor('#999999')
                .padding({ left: 8, right: 8, top: 3, bottom: 3 })
                .border({ width: 1, color: '#CCCCCC' })
                .borderRadius(10);
            }
          }
          .width('100%');

          Text(`${item.chineseChars} 字 · 完成率 ${item.completionRate}%`)
            .fontSize(13)
            .fontColor('#666666');

          if (item.useIndependentCheckRate) {
            Text(`独立目标 ${Math.round(item.independentCheckRate)}%`)
              .fontSize(12)
              .fontColor('#1976D2');
          }
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1);

        // 右侧：编辑、删除、独立目标完成率开关（离右侧边界更远）
        if (!this.isMultiSelectMode) {
          Column({ space: 8 }) {
            Row({ space: 10 }) {
              Text('编辑')
                .fontSize(13)
                .fontColor('#1976D2')
                .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                .backgroundColor('#FFFFFF')
                .borderRadius(4)
                .onClick(async () => {
                  this.editingArticle = item;
                  this.newTitle = item.title;
                  this.newContent = item.content;
                  this.newIsReading = item.isReading;
                  this.newIsRequired = item.isRequired;
                  this.newImageWebp = item.imagewebp && item.imagewebp.length > 0 ? item.imagewebp : '';
                  this.previewPixelMap = null;
                  if (this.newImageWebp.length > 0) {
                    try {
                      const ctx: common.Context = getContext(this) as common.Context;
                      const sized: SizedPixelMap = await ImageCompressionService.base64ToPixelMap(
                        ctx, this.newImageWebp
                      );
                      this.previewPixelMap = sized.pixelMap;
                    } catch (ignore) {
                      this.previewPixelMap = null;
                    }
                  }
                  this.showAddDialog = true;
                });
              Text('删除')
                .fontSize(13)
                .fontColor('#D32F2F')
                .padding({ left: 12, right: 12, top: 6, bottom: 6 })
                .backgroundColor('#FFFFFF')
                .borderRadius(4)
                .onClick(() => {
                  this.deleteArticle(item);
                });
            }

            Row() {
              Text('独立目标')
                .fontSize(12)
                .fontColor('#666666')
                .margin({ right: 6 });
              Toggle({ type: ToggleType.Switch, isOn: item.useIndependentCheckRate })
                .onChange((isCheck: boolean) => {
                  this.toggleIndependentCheckRate(item, isCheck);
                });
            }
          }
          .margin({ left: 20, right: 4 });
        }
      }
      .width('100%')
      .alignItems(VerticalAlign.Center);
    }
    .width('100%')
    .padding({ top: 16, bottom: 16, left: 16, right: 20 })
    .backgroundColor('#E9DEEE')
    .borderRadius(12)
    .margin({ left: 16, right: 16, top: 8 });
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
}

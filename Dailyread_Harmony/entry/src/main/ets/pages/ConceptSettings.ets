import router from '@ohos.router';
import { Concept } from '../model/Concept';
import { ConceptRepository } from '../repository/ConceptRepository';
import promptAction from '@ohos.promptAction';

@Entry
@Component
struct ConceptSettingsPage {
  @State concepts: Concept[] = [];
  @State isLoading: boolean = true;
  @State refreshKey: number = 0;
  
  // 搜索功能
  @State searchKeyword: string = '';
  
  // 修改对话框
  @State showEditDialog: boolean = false;
  @State editingConcept: Concept | null = null;
  @State editTitle: string = '';
  @State editCategory: string = '';
  @State editSubject: string = '';
  @State editChapter: string = '';
  @State editContent: string = '';
  
  // 删除确认对话框
  @State showDeleteConfirm: boolean = false;
  @State deletingConcept: Concept | null = null;
  
  // 新增概念对话框
  @State showAddDialog: boolean = false;
  @State addTitle: string = '';
  @State addCategory: string = '';
  @State addSubject: string = '';
  @State addChapter: string = '';
  @State addContent: string = '';

  aboutToAppear(): void {
    this.loadData();
  }

  aboutToShow(): void {
    this.loadData();
  }

  async loadData(): Promise<void> {
    this.isLoading = true;
    try {
      const list: Concept[] = await ConceptRepository.getInstance().getAllConcepts();
      this.concepts = list;
      this.refreshKey = this.refreshKey + 1;
    } catch (e) {
      console.error('加载数据失败: ' + JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  // 获取过滤后的概念列表
  private getFilteredConcepts(): Concept[] {
    const keyword: string = this.searchKeyword.trim();
    if (keyword.length === 0) {
      return this.concepts;
    }
    const lowerKeyword: string = keyword.toLowerCase();
    return this.concepts.filter((c: Concept): boolean => {
      const titleLower: string = c.title.toLowerCase();
      const categoryLower: string = c.category.toLowerCase();
      const subjectLower: string = c.subject.toLowerCase();
      const titleHit: boolean = titleLower.indexOf(lowerKeyword) !== -1;
      const categoryHit: boolean = categoryLower.indexOf(lowerKeyword) !== -1;
      const subjectHit: boolean = subjectLower.indexOf(lowerKeyword) !== -1;
      return titleHit || categoryHit || subjectHit;
    });
  }

  async toggleReading(concept: Concept, newValue: boolean): Promise<void> {
    try {
      await ConceptRepository.getInstance().updateReadingStatus(concept.id, newValue);
      await this.loadData();
    } catch (e) {
      console.error('更新阅读状态失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '更新失败', duration: 2000 });
    }
  }

  showDeleteConfirmDialog(concept: Concept): void {
    this.deletingConcept = concept;
    this.showDeleteConfirm = true;
  }

  async deleteConcept(): Promise<void> {
    if (!this.deletingConcept) {
      return;
    }
    try {
      await ConceptRepository.getInstance().deleteConcept(this.deletingConcept.id);
      await this.loadData();
      promptAction.showToast({ message: '删除成功', duration: 2000 });
    } catch (e) {
      console.error('删除失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '删除失败', duration: 2000 });
    } finally {
      this.showDeleteConfirm = false;
      this.deletingConcept = null;
    }
  }

  openEditDialog(concept: Concept): void {
    this.editingConcept = concept;
    this.editTitle = concept.title;
    this.editCategory = concept.category;
    this.editSubject = concept.subject;
    this.editChapter = concept.chapter;
    this.editContent = concept.content;
    this.showEditDialog = true;
  }

  async saveEdit(): Promise<void> {
    if (!this.editingConcept) {
      return;
    }
    try {
      const concept: Concept = new Concept();
      concept.id = this.editingConcept.id;
      concept.title = this.editTitle;
      concept.category = this.editCategory;
      concept.subject = this.editSubject;
      concept.chapter = this.editChapter;
      concept.content = this.editContent;
      concept.isReading = this.editingConcept.isReading;
      concept.createTime = this.editingConcept.createTime;
      concept.lastModified = new Date().toISOString();
      await ConceptRepository.getInstance().updateConcept(concept);
      await this.loadData();
      this.showEditDialog = false;
      promptAction.showToast({ message: '修改成功', duration: 2000 });
    } catch (e) {
      console.error('修改失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '修改失败', duration: 2000 });
    }
  }

  openAddDialog(): void {
    this.addTitle = '';
    this.addCategory = '';
    this.addSubject = '';
    this.addChapter = '';
    this.addContent = '';
    this.showAddDialog = true;
  }

  async saveNewConcept(): Promise<void> {
    if (this.addTitle.trim().length === 0) {
      promptAction.showToast({ message: '请输入标题', duration: 2000 });
      return;
    }
    try {
      const concept: Concept = new Concept();
      concept.title = this.addTitle;
      concept.category = this.addCategory;
      concept.subject = this.addSubject;
      concept.chapter = this.addChapter;
      concept.content = this.addContent;
      concept.isReading = false;
      const now: string = new Date().toISOString();
      concept.createTime = now;
      concept.lastModified = now;
      await ConceptRepository.getInstance().insertConcept(concept);
      await this.loadData();
      this.showAddDialog = false;
      promptAction.showToast({ message: '新增成功', duration: 2000 });
    } catch (e) {
      console.error('新增失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '新增失败', duration: 2000 });
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
      // 顶部标题栏
      Column() {
        Row() {
          Text('背概念设置')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .layoutWeight(1);
          // 新增概念按钮
          Text('+ 新增')
            .fontSize(14)
            .fontColor('#FFFFFF')
            .padding({ left: 12, right: 12, top: 6, bottom: 6 })
            .backgroundColor('#1976D2')
            .borderRadius(8)
            .margin({ right: 12 })
            .onClick(() => {
              this.openAddDialog();
            });
          Text('返回')
            .fontSize(14)
            .fontColor('#1976D2')
            .padding({ left: 12, right: 12, top: 6, bottom: 6 })
            .onClick(() => {
              router.back();
            });
        }
        .width('100%');

        // 搜索输入框
        Row() {
          Text('🔍')
            .fontSize(16)
            .margin({ right: 8 });
          TextInput({
            text: this.searchKeyword,
            placeholder: '搜索标题、分类、学科'
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

      // 搜索结果提示
      if (!this.isLoading && this.searchKeyword.trim().length > 0) {
        Row() {
          Text(`搜索"${this.searchKeyword.trim()}"，共找到 ${this.getFilteredConcepts().length} 条`)
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
      } else if (this.getFilteredConcepts().length === 0) {
        Column() {
          if (this.searchKeyword.trim().length > 0) {
            Text('未找到匹配的概念')
              .fontSize(16)
              .fontColor('#999999');
            Text('请尝试更换关键字或清除搜索')
              .fontSize(13)
              .fontColor('#BBBBBB')
              .margin({ top: 8 });
          } else {
            Text('暂无概念')
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
          ForEach(this.getFilteredConcepts(), (item: Concept) => {
            ListItem() {
              Column({ space: 12 }) {
                Row() {
                  Column({ space: 6 }) {
                    Text(item.title)
                      .fontSize(16)
                      .fontWeight(FontWeight.Bold)
                      .fontColor('#333333')
                      .maxLines(1)
                      .textOverflow({ overflow: TextOverflow.Ellipsis })
                      .width('100%');

                    Row({ space: 12 }) {
                      if (item.category.length > 0) {
                        Text('分类:' + item.category)
                          .fontSize(12)
                          .fontColor('#666666');
                      }
                      if (item.subject.length > 0) {
                        Text('学科:' + item.subject)
                          .fontSize(12)
                          .fontColor('#666666');
                      }
                      if (item.chapter.length > 0) {
                        Text('章节:' + item.chapter)
                          .fontSize(12)
                          .fontColor('#666666');
                      }
                    }
                    .width('100%');
                  }
                  .layoutWeight(1);

                  Column({ space: 16 }) {
                    Row({ space: 12 }) {
                      Text('编辑')
                        .fontSize(14)
                        .fontColor('#1976D2')
                        .padding({ left: 14, right: 14, top: 6, bottom: 6 })
                        .backgroundColor('#E3F2FD')
                        .borderRadius(8)
                        .onClick(() => {
                          this.openEditDialog(item);
                        });
                      Text('删除')
                        .fontSize(14)
                        .fontColor('#D32F2F')
                        .padding({ left: 14, right: 14, top: 6, bottom: 6 })
                        .backgroundColor('#FFEBEE')
                        .borderRadius(8)
                        .onClick(() => {
                          this.showDeleteConfirmDialog(item);
                        });
                    }
                    .alignItems(VerticalAlign.Center);

                    Toggle({ type: ToggleType.Switch, isOn: item.isReading })
                      .onChange((isCheck: boolean) => {
                        this.toggleReading(item, isCheck);
                      });
                  }
                  .alignItems(HorizontalAlign.Start)
                  .padding({ right: 24 });
                }
                .width('100%');
              }
              .width('100%')
              .padding({ top: 20, bottom: 20, left: 24, right: 24 });
            }
            .width('100%')
            .backgroundColor('#FFFFFF')
            .borderRadius(16)
            .margin({ left: 24, right: 24, top: 12 });
          }, (item: Concept) => item.id.toString() + '_' + this.refreshKey.toString());
        }
        .width('100%')
        .layoutWeight(1)
        .backgroundColor('#F5F5F5');
      }

      this.BottomTabBar();

      // 修改对话框
      if (this.showEditDialog) {
        Column() {
          Column() {
            Text('修改概念')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center);

            Column() {
              Text('标题')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editTitle, placeholder: '请输入标题' })
                .width('100%')
                .onChange((value: string) => {
                  this.editTitle = value;
                });
            }
            .width('100%')
            .margin({ top: 16 });

            Column() {
              Text('分类')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editCategory, placeholder: '请输入分类' })
                .width('100%')
                .onChange((value: string) => {
                  this.editCategory = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('学科')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editSubject, placeholder: '请输入学科' })
                .width('100%')
                .onChange((value: string) => {
                  this.editSubject = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('章节')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editChapter, placeholder: '请输入章节' })
                .width('100%')
                .onChange((value: string) => {
                  this.editChapter = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('内容')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editContent, placeholder: '请输入内容' })
                .width('100%')
                .height(100)
                .onChange((value: string) => {
                  this.editContent = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Row() {
              Button('取消')
                .width('45%')
                .backgroundColor('#F5F5F5')
                .fontColor('#333333')
                .onClick(() => {
                  this.showEditDialog = false;
                });
              Button('保存')
                .width('45%')
                .onClick(() => {
                  this.saveEdit();
                });
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceAround)
            .margin({ top: 24 });
          }
          .width('85%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16);
        }
        .width('100%')
        .height('100%')
        .position({ x: 0, y: 0 })
        .backgroundColor('rgba(0,0,0,0.5)')
        .justifyContent(FlexAlign.Center)
        .onClick(() => {
          this.showEditDialog = false;
        });
      }

      // 删除确认对话框
      if (this.showDeleteConfirm) {
        Column() {
          Column() {
            Text('确认删除')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center)
              .margin({ bottom: 16 });

            Text(`确定要删除概念「${this.deletingConcept?.title || ''}」吗？`)
              .fontSize(16)
              .fontColor('#666666')
              .width('100%')
              .textAlign(TextAlign.Center);

            Row() {
              Button('取消')
                .width('45%')
                .backgroundColor('#F5F5F5')
                .fontColor('#333333')
                .onClick(() => {
                  this.showDeleteConfirm = false;
                  this.deletingConcept = null;
                });
              Button('确认删除')
                .width('45%')
                .backgroundColor('#D32F2F')
                .fontColor('#FFFFFF')
                .onClick(() => {
                  this.deleteConcept();
                });
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceAround)
            .margin({ top: 24 });
          }
          .width('80%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16);
        }
        .width('100%')
        .height('100%')
        .position({ x: 0, y: 0 })
        .backgroundColor('rgba(0,0,0,0.5)')
        .justifyContent(FlexAlign.Center)
        .onClick(() => {
          this.showDeleteConfirm = false;
          this.deletingConcept = null;
        });
      }

      // 新增概念对话框
      if (this.showAddDialog) {
        Column() {
          Column() {
            Text('新增概念')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center)
              .margin({ bottom: 16 });

            Column() {
              Text('标题')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addTitle, placeholder: '请输入标题' })
                .width('100%')
                .onChange((value: string) => {
                  this.addTitle = value;
                });
            }
            .width('100%')
            .margin({ top: 8 });

            Column() {
              Text('分类')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addCategory, placeholder: '请输入分类' })
                .width('100%')
                .onChange((value: string) => {
                  this.addCategory = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('学科')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addSubject, placeholder: '请输入学科' })
                .width('100%')
                .onChange((value: string) => {
                  this.addSubject = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('章节')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addChapter, placeholder: '请输入章节' })
                .width('100%')
                .onChange((value: string) => {
                  this.addChapter = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('内容')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addContent, placeholder: '请输入内容' })
                .width('100%')
                .height(100)
                .onChange((value: string) => {
                  this.addContent = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Row() {
              Button('取消')
                .width('45%')
                .backgroundColor('#F5F5F5')
                .fontColor('#333333')
                .onClick(() => {
                  this.showAddDialog = false;
                });
              Button('保存')
                .width('45%')
                .onClick(() => {
                  this.saveNewConcept();
                });
            }
            .width('100%')
            .justifyContent(FlexAlign.SpaceAround)
            .margin({ top: 24 });
          }
          .width('85%')
          .padding(24)
          .backgroundColor('#FFFFFF')
          .borderRadius(16);
        }
        .width('100%')
        .height('100%')
        .position({ x: 0, y: 0 })
        .backgroundColor('rgba(0,0,0,0.5)')
        .justifyContent(FlexAlign.Center)
        .onClick(() => {
          this.showAddDialog = false;
        });
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5');
  }
}

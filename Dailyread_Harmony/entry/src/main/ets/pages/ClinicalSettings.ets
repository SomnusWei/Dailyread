import router from '@ohos.router';
import { ClinicalNote } from '../model/ClinicalNote';
import { ClinicalNoteRepository } from '../repository/ClinicalNoteRepository';
import promptAction from '@ohos.promptAction';

@Entry
@Component
struct ClinicalSettingsPage {
  @State notes: ClinicalNote[] = [];
  @State isLoading: boolean = true;
  @State refreshKey: number = 0;

  @State searchKeyword: string = '';

  @State showEditDialog: boolean = false;
  @State editingNote: ClinicalNote | null = null;
  @State editTitle: string = '';
  @State editPathogenesis: string = '';
  @State editTreatment: string = '';
  @State editPrescription: string = '';
  @State editNotes: string = '';

  @State showDeleteConfirm: boolean = false;
  @State deletingNote: ClinicalNote | null = null;

  @State showAddDialog: boolean = false;
  @State addTitle: string = '';
  @State addPathogenesis: string = '';
  @State addTreatment: string = '';
  @State addPrescription: string = '';
  @State addNotes: string = '';
  @State addIsReading: boolean = false;

  aboutToAppear(): void {
    this.loadData();
  }

  aboutToShow(): void {
    this.loadData();
  }

  async loadData(): Promise<void> {
    this.isLoading = true;
    try {
      const list: ClinicalNote[] = await ClinicalNoteRepository.getInstance().getAllNotes();
      this.notes = list;
      this.refreshKey = this.refreshKey + 1;
    } catch (e) {
      console.error('加载数据失败: ' + JSON.stringify(e));
    } finally {
      this.isLoading = false;
    }
  }

  private getFilteredNotes(): ClinicalNote[] {
    const keyword: string = this.searchKeyword.trim();
    if (keyword.length === 0) {
      return this.notes;
    }
    const lowerKeyword: string = keyword.toLowerCase();
    return this.notes.filter((n: ClinicalNote): boolean => {
      const titleHit: boolean = n.title.toLowerCase().indexOf(lowerKeyword) !== -1;
      const pathoHit: boolean = n.pathogenesis.toLowerCase().indexOf(lowerKeyword) !== -1;
      const treatHit: boolean = n.treatment.toLowerCase().indexOf(lowerKeyword) !== -1;
      const prescHit: boolean = n.prescription.toLowerCase().indexOf(lowerKeyword) !== -1;
      return titleHit || pathoHit || treatHit || prescHit;
    });
  }

  async toggleReading(note: ClinicalNote, newValue: boolean): Promise<void> {
    try {
      await ClinicalNoteRepository.getInstance().updateReadingStatus(note.id, newValue);
      await this.loadData();
    } catch (e) {
      console.error('更新学习状态失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '更新失败', duration: 2000 });
    }
  }

  showDeleteConfirmDialog(note: ClinicalNote): void {
    this.deletingNote = note;
    this.showDeleteConfirm = true;
  }

  async deleteNote(): Promise<void> {
    if (!this.deletingNote) {
      return;
    }
    try {
      await ClinicalNoteRepository.getInstance().deleteNote(this.deletingNote.id);
      await this.loadData();
      promptAction.showToast({ message: '删除成功', duration: 2000 });
    } catch (e) {
      console.error('删除失败: ' + JSON.stringify(e));
      promptAction.showToast({ message: '删除失败', duration: 2000 });
    } finally {
      this.showDeleteConfirm = false;
      this.deletingNote = null;
    }
  }

  openEditDialog(note: ClinicalNote): void {
    this.editingNote = note;
    this.editTitle = note.title;
    this.editPathogenesis = note.pathogenesis;
    this.editTreatment = note.treatment;
    this.editPrescription = note.prescription;
    this.editNotes = note.notes;
    this.showEditDialog = true;
  }

  async saveEdit(): Promise<void> {
    if (!this.editingNote) {
      return;
    }
    try {
      const note: ClinicalNote = new ClinicalNote();
      note.id = this.editingNote.id;
      note.title = this.editTitle;
      note.pathogenesis = this.editPathogenesis;
      note.treatment = this.editTreatment;
      note.prescription = this.editPrescription;
      note.notes = this.editNotes;
      note.isReading = this.editingNote.isReading;
      note.createTime = this.editingNote.createTime;
      note.lastModified = new Date().toISOString();
      await ClinicalNoteRepository.getInstance().updateNote(note);
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
    this.addPathogenesis = '';
    this.addTreatment = '';
    this.addPrescription = '';
    this.addNotes = '';
    this.addIsReading = false;
    this.showAddDialog = true;
  }

  async saveNewNote(): Promise<void> {
    if (this.addTitle.trim().length === 0) {
      promptAction.showToast({ message: '请输入标题', duration: 2000 });
      return;
    }
    try {
      const note: ClinicalNote = new ClinicalNote();
      note.title = this.addTitle;
      note.pathogenesis = this.addPathogenesis;
      note.treatment = this.addTreatment;
      note.prescription = this.addPrescription;
      note.notes = this.addNotes;
      note.isReading = this.addIsReading;
      const now: string = new Date().toISOString();
      note.createTime = now;
      note.lastModified = now;
      await ClinicalNoteRepository.getInstance().insertNote(note);
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
      Column() {
        Row() {
          Text('背临床设置')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .layoutWeight(1);
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

        Row() {
          Text('🔍')
            .fontSize(16)
            .margin({ right: 8 });
          TextInput({
            text: this.searchKeyword,
            placeholder: '搜索标题、病机、治法、处方'
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

      if (!this.isLoading && this.searchKeyword.trim().length > 0) {
        Row() {
          Text(`搜索"${this.searchKeyword.trim()}"，共找到 ${this.getFilteredNotes().length} 条`)
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
      } else if (this.getFilteredNotes().length === 0) {
        Column() {
          if (this.searchKeyword.trim().length > 0) {
            Text('未找到匹配的笔记')
              .fontSize(16)
              .fontColor('#999999');
            Text('请尝试更换关键字或清除搜索')
              .fontSize(13)
              .fontColor('#BBBBBB')
              .margin({ top: 8 });
          } else {
            Text('暂无笔记')
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
          ForEach(this.getFilteredNotes(), (item: ClinicalNote) => {
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
          }, (item: ClinicalNote) => item.id.toString() + '_' + this.refreshKey.toString());
        }
        .width('100%')
        .layoutWeight(1)
        .backgroundColor('#F5F5F5');
      }

      this.BottomTabBar();

      if (this.showEditDialog) {
        Column() {
          Column() {
            Text('修改临床笔记')
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
              Text('病机')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editPathogenesis, placeholder: '请输入病机' })
                .width('100%')
                .height(70)
                .onChange((value: string) => {
                  this.editPathogenesis = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('治法')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editTreatment, placeholder: '请输入治法' })
                .width('100%')
                .height(70)
                .onChange((value: string) => {
                  this.editTreatment = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('处方')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editPrescription, placeholder: '请输入处方' })
                .width('100%')
                .height(80)
                .onChange((value: string) => {
                  this.editPrescription = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('备注')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.editNotes, placeholder: '请输入备注' })
                .width('100%')
                .height(70)
                .onChange((value: string) => {
                  this.editNotes = value;
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

      if (this.showDeleteConfirm) {
        Column() {
          Column() {
            Text('确认删除')
              .fontSize(20)
              .fontWeight(FontWeight.Bold)
              .width('100%')
              .textAlign(TextAlign.Center)
              .margin({ bottom: 16 });

            Text(`确定要删除笔记「${this.deletingNote?.title || ''}」吗？`)
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
                  this.deletingNote = null;
                });
              Button('确认删除')
                .width('45%')
                .backgroundColor('#D32F2F')
                .fontColor('#FFFFFF')
                .onClick(() => {
                  this.deleteNote();
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
          this.deletingNote = null;
        });
      }

      if (this.showAddDialog) {
        Column() {
          Column() {
            Text('新增临床笔记')
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
            .width('100%');

            Column() {
              Text('病机')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addPathogenesis, placeholder: '请输入病机' })
                .width('100%')
                .height(70)
                .onChange((value: string) => {
                  this.addPathogenesis = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('治法')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addTreatment, placeholder: '请输入治法' })
                .width('100%')
                .height(70)
                .onChange((value: string) => {
                  this.addTreatment = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('处方')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addPrescription, placeholder: '请输入处方' })
                .width('100%')
                .height(80)
                .onChange((value: string) => {
                  this.addPrescription = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Column() {
              Text('备注内容')
                .fontSize(14)
                .fontColor('#333333')
                .width('100%');
              TextInput({ text: this.addNotes, placeholder: '请输入备注' })
                .width('100%')
                .height(70)
                .onChange((value: string) => {
                  this.addNotes = value;
                });
            }
            .width('100%')
            .margin({ top: 12 });

            Row() {
              Text('学习状态')
                .fontSize(14)
                .fontColor('#333333');
              Toggle({ type: ToggleType.Switch, isOn: this.addIsReading })
                .onChange((isCheck: boolean) => {
                  this.addIsReading = isCheck;
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
                  this.saveNewNote();
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

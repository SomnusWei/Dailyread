import UIAbility from '@ohos.app.ability.UIAbility';
import window from '@ohos.window';
import { AppDatabase } from '../database/AppDatabase';
import { WebDavSyncService } from '../service/WebDavSyncService';
import { ConfigRepository } from '../repository/ConfigRepository';
import { AbilityConstant, Want } from '@kit.AbilityKit';

// 全局共享 key，供页面在切换开关时读取/更新
const KEEP_SCREEN_ON_KEY = 'keepScreenOnState';

// 模块级单例引用（用显式类型，完全避免 unknown/any/Record 断言）
let sInstance: EntryAbility | null = null;

/** 供页面层调用：设置屏幕常亮 */
export function setKeepScreenOn(on: boolean): void {
  if (sInstance !== null) {
    sInstance.applyKeepScreenOn(on);
  } else {
    console.warn('EntryAbility.setKeepScreenOn: sInstance is null');
  }
}

/** 供页面层调用：读取当前的屏幕常亮状态（从 AppStorage 中拿） */
export function isKeepScreenOn(): boolean {
  const value: boolean | undefined = AppStorage.get<boolean>(KEEP_SCREEN_ON_KEY);
  return value === true;
}

export default class EntryAbility extends UIAbility {
  private mainWindowStage: window.WindowStage | null = null;

  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    console.info('EntryAbility onCreate');
    sInstance = this;
  }

  onDestroy(): void {
    console.info('EntryAbility onDestroy');
    sInstance = null;
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    console.info('EntryAbility onWindowStageCreate');
    this.mainWindowStage = windowStage;

    const initDatabase = async (): Promise<void> => {
      await AppDatabase.getInstance().init(this.context);
      WebDavSyncService.getInstance().init(this.context);

      try {
        const config = await ConfigRepository.getInstance().getConfig();
        console.info('EntryAbility: keepScreenOn config = ' + config.keepScreenOn);
        if (config.keepScreenOn) {
          this.applyKeepScreenOn(true);
        }
        AppStorage.setOrCreate<boolean>(KEEP_SCREEN_ON_KEY, config.keepScreenOn);
      } catch (configErr) {
        console.error('EntryAbility: failed to load config for keepScreenOn: ' + JSON.stringify(configErr));
      }
    };
    initDatabase().then(() => {
      console.info('Database initialized');
    }).catch((e: Error) => {
      console.error('Database init failed: ' + e.message);
    });

    windowStage.loadContent('pages/Index', (err: BusinessError) => {
      if (err.code) {
        console.error('Failed to load content. Cause: ' + JSON.stringify(err));
        return;
      }
      console.info('Succeeded in loading content.');
    });
  }

  onWindowStageDestroy(): void {
    console.info('EntryAbility onWindowStageDestroy');
    this.mainWindowStage = null;
  }

  onForeground(): void {
    console.info('EntryAbility onForeground');
    if (isKeepScreenOn()) {
      this.applyKeepScreenOn(true);
    }
  }

  onBackground(): void {
    console.info('EntryAbility onBackground');
  }

  applyKeepScreenOn(on: boolean): void {
    if (!this.mainWindowStage) {
      console.warn('EntryAbility.applyKeepScreenOn: mainWindowStage 为空');
      return;
    }
    try {
      this.mainWindowStage.getMainWindow().then((win: window.Window) => {
        try {
          win.setWindowKeepScreenOn(on).then(() => {
            console.info('EntryAbility: setWindowKeepScreenOn(' + on + ') 已应用');
            AppStorage.setOrCreate<boolean>(KEEP_SCREEN_ON_KEY, on);
          }).catch((err: Error) => {
            console.error('EntryAbility: setWindowKeepScreenOn(' + on + ') 失败: ' + err.message);
          });
        } catch (e) {
          console.error('EntryAbility: setWindowKeepScreenOn 异常: ' + JSON.stringify(e));
        }
      }).catch((err: Error) => {
        console.error('EntryAbility: 获取主窗口失败: ' + err.message);
      });
    } catch (e) {
      console.error('EntryAbility.applyKeepScreenOn 异常: ' + JSON.stringify(e));
    }
  }
}

import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { window } from '@kit.ArkUI';

export default class EntryAbility extends UIAbility {
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    hilog.info(0x0000, 'scMobile', 'Ability onCreate');
  }

  onDestroy(): void {
    hilog.info(0x0000, 'scMobile', 'Ability onDestroy');
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    windowStage.loadContent('pages/Index', (err) => {
      if (err.code) {
        hilog.error(0x0000, 'scMobile', 'Failed to load content: %{public}s', JSON.stringify(err) ?? '');
        return;
      }
      hilog.info(0x0000, 'scMobile', 'Succeeded in loading content.');
    });
  }

  onWindowStageDestroy(): void {
    hilog.info(0x0000, 'scMobile', 'Ability onWindowStageDestroy');
  }

  onForeground(): void {
    hilog.info(0x0000, 'scMobile', 'Ability onForeground');
  }

  onBackground(): void {
    hilog.info(0x0000, 'scMobile', 'Ability onBackground');
  }
}

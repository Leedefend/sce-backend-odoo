import { webview } from '@kit.ArkWeb';

@Entry
@Component
struct Index {
  private controller: webview.WebviewController = new webview.WebviewController();
  @State pageUrl: string = 'http://192.168.43.5:8092';

  build() {
    Column() {
      Row() {
        Text('智能工程')
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor('#111827')
          .layoutWeight(1)
          .maxLines(1)
          .textOverflow({ overflow: TextOverflow.Ellipsis })

        Button('刷新')
          .fontSize(13)
          .height(32)
          .padding({ left: 12, right: 12 })
          .onClick(() => {
            this.controller.refresh();
          })
      }
      .width('100%')
      .height(44)
      .padding({ left: 12, right: 12 })
      .backgroundColor('#FFFFFF')
      .border({
        width: { bottom: 1 },
        color: '#E5E7EB'
      })

      Web({ src: this.pageUrl, controller: this.controller })
        .width('100%')
        .layoutWeight(1)
        .javaScriptAccess(true)
        .domStorageAccess(true)
        .databaseAccess(true)
        .mixedMode(MixedMode.All)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F8FAFC')
  }
}

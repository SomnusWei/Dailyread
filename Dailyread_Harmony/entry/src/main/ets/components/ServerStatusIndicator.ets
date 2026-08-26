/**
 * 服务器状态指示灯组件
 * 功能：显示服务器连通状态，绿色=通畅，红色=不通
 */
import { ServerStatus, ServerStatusService } from '../service/ServerStatusService';

@Component
export struct ServerStatusIndicator {
  @State status: ServerStatus = 'checking';
  private unsubscribe: (() => void) | null = null;

  aboutToAppear(): void {
    const service = ServerStatusService.getInstance();
    this.unsubscribe = service.onStatusChange((newStatus: ServerStatus) => {
      this.status = newStatus;
    });
    service.start();
  }

  aboutToDisappear(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
  }

  build() {
    Row() {
      // 状态指示灯圆点
      Circle({ width: 8, height: 8 })
        .fill(this.getIndicatorColor())
        .margin({ right: 4 });

      // 状态文字
      Text(this.getStatusText())
        .fontSize(11)
        .fontColor(this.getIndicatorColor())
        .fontWeight(FontWeight.Medium);
    }
    .alignItems(VerticalAlign.Center)
    .margin({ left: 8 });
  }

  private getIndicatorColor(): string {
    switch (this.status) {
      case 'online':
        return '#4CAF50'; // 绿色
      case 'offline':
        return '#F44336'; // 红色
      case 'checking':
      default:
        return '#FFC107'; // 黄色（检测中）
    }
  }

  private getStatusText(): string {
    switch (this.status) {
      case 'online':
        return '已连接';
      case 'offline':
        return '离线';
      case 'checking':
      default:
        return '检测中';
    }
  }
}

/**
 * 用户模型
 */
export interface User {
  id: number;
  username: string;
  nickname: string;
}

/**
 * 登录响应
 */
export interface AuthResult {
  token: string;
  user: User;
}

/**
 * 同步状态
 */
export interface SyncState {
  articleSince: string;
  checkinSince: string;
  lastSyncTime: string;
}

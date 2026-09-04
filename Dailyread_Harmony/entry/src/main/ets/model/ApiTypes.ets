/**
 * API 通用类型定义
 * 遵循 ArkTS 严格模式：所有对象字面量必须对应显式声明的接口
 */

// ---------- 通用响应结构 ----------
export interface ApiResponse {
  code: number;
  message: string;
  data: Object | null;
}

// ---------- 请求体接口 ----------
export interface RegisterBody {
  username: string;
  password: string;
  nickname: string;
  deviceId?: string;
}

export interface LoginBody {
  username: string;
  password: string;
  deviceId?: string;
}

export interface CheckUsernameBody {
  username: string;
}

export interface CheckinBody {
  articleId: string;
  checkInDate: string;
  checkInTime: string;
  lastModified: string;
}

export interface TaskCheckinBody {
  itemId: number;
}

export interface CheckinByArticleBody {
  articleId: string;
}

export interface MigrateImportBody {
  articles: Object[];
  checkins: Object[];
}

// ---------- 离线写队列载荷接口 ----------
export interface DeletePayload {
  clientId: string;
}

export interface CheckinEnqueuePayload {
  articleId: string;
  checkInDate: string;
  checkInTime: string;
  lastModified: string;
}

export interface ArticleUpdateEnqueuePayload {
  clientId: string;
  checkInDays: number;
  completionRate: number;
  lastModified: string;
}

// ---------- 文章上传载荷（用于 pushArticle / enqueueArticleCreate） ----------
export interface ArticlePayload {
  clientId: string;
  title: string;
  content: string;
  contentHtml: string;
  chineseChars: number;
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  isBold: number;
  isReading: number;
  isRequired: number;
  requiredDays: string;
  useIndependentCheckRate: number;
  independentCheckRate: number;
  createTime: string;
  isLongArticle: number;
  checkInDays: number;
  completionRate: number;
  imagewebp: string;
  audiobase64: string;
  iscontent: number;
  lastModified: string;
}

// ---------- 文章部分更新载荷（用于 PATCH /api/articles/:clientId） ----------
export interface ArticlePatchPayload {
  clientId: string;
  checkInDays?: number;
  completionRate?: number;
  lastModified?: string;
  isReading?: boolean;
  isRequired?: boolean;
  useIndependentCheckRate?: boolean;
  independentCheckRate?: number;
  isBold?: boolean;
  fontSize?: number;
  fontColor?: string;
  fontFamily?: string;
  isLongArticle?: boolean;
  iscontent?: boolean;
  requiredDays?: string;
}

// ---------- 配置同步载荷 ----------
// dailyMinutes / targetCheckRate 仅 Win 端上传（鸿蒙端只拉取），故设为可选
export interface ConfigPayload {
  dailyMinutes?: number;
  targetCheckRate?: number;
  readerFontSize?: number;
  lastResetMonth: string;
  lastSyncTime: string;
}

// ---------- 每日任务生成请求 ----------
export interface GenerateTaskBody {
  force?: boolean;
}

// ---------- 每日任务同步载荷 ----------
export interface DailyTaskItemPayload {
  articleId: string;
  articleTitle: string;
  wordTarget: number;
  isCheckedIn: number;
  isLongArticle: number;
  isRequired: number;
  displayName: string;
}

export interface DailyTaskPayload {
  count: number;
  totalWords: number;
  lastLongArticleIds: string;
  items: DailyTaskItemPayload[];
}

// ---------- 文章 Patch 序列化桶（用于入队时的 JSON 序列化） ----------
export interface ArticlePatchBucket {
  clientId: string;
  checkInDays?: number;
  completionRate?: number;
  lastModified?: string;
  isReading?: boolean;
  isRequired?: boolean;
  useIndependentCheckRate?: boolean;
  independentCheckRate?: number;
  isBold?: boolean;
  fontSize?: number;
  fontColor?: string;
  fontFamily?: string;
  isLongArticle?: boolean;
  iscontent?: boolean;
  requiredDays?: string;
}

// ---------- 401 冲突响应 ----------
export interface ConflictResponse {
  conflict: boolean;
}

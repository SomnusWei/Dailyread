export interface User {
  id: number
  username: string
  email: string
  created_at: string
  updated_at: string
}

export interface Article {
  id: number
  title: string
  content: string
  contentHtml: string
  chineseChars: number
  fontFamily: string
  fontSize: number
  isReading: boolean
  isRequired: boolean
  useIndependentCheckRate: boolean
  independentCheckRate: number
  checkInDays: number
  completionRate: number
  imagewebp: string
  createTime: string
  lastModified: string
}

export interface Concept {
  id: number
  title: string
  category: string
  subject: string
  chapter: string
  content: string
  isReading: boolean
  createTime: string
  lastModified: string
}

export interface ClinicalNote {
  id: number
  title: string
  pathogenesis: string
  treatment: string
  prescription: string
  notes: string
  isReading: boolean
  createTime: string
  lastModified: string
}

export interface WebDavConfig {
  serverUrl: string
  username: string
  password: string
  remotePath: string
}

export interface BackupData {
  version: number
  exportTime: string
  dataType: string
  articles: Article[]
  concepts: Concept[]
  clinicalNotes: ClinicalNote[]
}

export interface LoginResponse {
  user: User
  token: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isLoggedIn: boolean
}

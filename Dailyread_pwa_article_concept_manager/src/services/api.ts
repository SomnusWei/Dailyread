/**
 * 后端 API 服务
 * 用于用户认证和 WebDAV 配置管理
 */

const API_BASE_URL = import.meta.env.PROD ? '' : 'http://localhost:3001/api'

export interface User {
  id: number
  username: string
}

export interface WebDavConfig {
  serverUrl: string
  username: string
  password: string
  remotePath: string
}

export interface AuthResponse {
  success: boolean
  token: string
  user: User
}

export interface ApiResponse<T> {
  success?: boolean
  data?: T
  error?: string
}

class ApiService {
  private getToken(): string | null {
    return localStorage.getItem('dailyread_token')
  }

  private setToken(token: string): void {
    localStorage.setItem('dailyread_token', token)
  }

  private removeToken(): void {
    localStorage.removeItem('dailyread_token')
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const token = this.getToken()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers
    })

    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || '请求失败')
    }
    
    return data
  }

  // ==================== 用户认证 ====================

  async register(username: string, password: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
    
    if (response.success && response.token) {
      this.setToken(response.token)
    }
    
    return response as AuthResponse
  }

  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
    
    if (response.success && response.token) {
      this.setToken(response.token)
    }
    
    return response as AuthResponse
  }

  async getUser(): Promise<User | null> {
    try {
      const response = await this.request<{ user: User }>('/auth/user')
      return response.user || null
    } catch {
      return null
    }
  }

  logout(): void {
    this.removeToken()
  }

  isLoggedIn(): boolean {
    return !!this.getToken()
  }

  // ==================== WebDAV 配置 ====================

  async getWebDavConfig(): Promise<WebDavConfig | null> {
    try {
      const response = await this.request<{ config: WebDavConfig | null }>('/webdav/config')
      return response.config || null
    } catch {
      return null
    }
  }

  async saveWebDavConfig(config: WebDavConfig): Promise<boolean> {
    try {
      await this.request('/webdav/config', {
        method: 'POST',
        body: JSON.stringify(config)
      })
      return true
    } catch {
      return false
    }
  }

  async deleteWebDavConfig(): Promise<boolean> {
    try {
      await this.request('/webdav/config', {
        method: 'DELETE'
      })
      return true
    } catch {
      return false
    }
  }
}

export const apiService = new ApiService()
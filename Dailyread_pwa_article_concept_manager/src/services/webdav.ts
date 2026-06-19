import { createClient } from 'webdav'
import type { WebDavConfig, BackupData } from '@/types'
import { apiService } from './api'

function getServerUrl(originalUrl: string): string {
  // 生产环境使用服务器代理
  if (originalUrl.includes('dav.jianguoyun.com')) {
    return '/api/webdav'
  }
  return originalUrl
}

export const webdavService = {
  /**
   * 从服务器获取 WebDAV 配置
   */
  async getConfig(): Promise<WebDavConfig | null> {
    return await apiService.getWebDavConfig()
  },
  
  /**
   * 保存 WebDAV 配置到服务器
   */
  async saveConfig(config: WebDavConfig): Promise<boolean> {
    return await apiService.saveWebDavConfig(config)
  },
  
  /**
   * 删除 WebDAV 配置
   */
  async deleteConfig(): Promise<boolean> {
    return await apiService.deleteWebDavConfig()
  },
  
  /**
   * 测试 WebDAV 连接
   */
  async testConnection(config: WebDavConfig): Promise<boolean> {
    try {
      const client = createClient(getServerUrl(config.serverUrl), {
        username: config.username,
        password: config.password
      })
      await client.exists(config.remotePath)
      return true
    } catch {
      return false
    }
  },
  
  /**
   * 上传备份到 WebDAV
   */
  async uploadBackup(config: WebDavConfig, data: BackupData): Promise<void> {
    const client = createClient(getServerUrl(config.serverUrl), {
      username: config.username,
      password: config.password
    })
    
    const content = JSON.stringify(data, null, 2)
    const filePath = `${config.remotePath}/daily_read_backup_windows.json`
    
    await client.putFileContents(filePath, content, {
      overwrite: true
    })
  },
  
  /**
   * 从 WebDAV 下载备份
   */
  async downloadBackup(config: WebDavConfig): Promise<BackupData> {
    const client = createClient(getServerUrl(config.serverUrl), {
      username: config.username,
      password: config.password
    })
    
    const filePath = `${config.remotePath}/daily_read_backup_windows.json`
    const content = await client.getFileContents(filePath)
    
    let jsonString: string
    if (typeof content === 'string') {
      jsonString = content
    } else {
      const decoder = new TextDecoder('utf-8')
      jsonString = decoder.decode(content as ArrayBuffer)
    }
    
    return JSON.parse(jsonString)
  }
}
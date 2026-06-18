import { createClient } from 'webdav'
import type { WebDavConfig, BackupData } from '@/types'

const STORAGE_KEY = 'dailyread_webdav_config'

function getServerUrl(originalUrl: string): string {
  if (originalUrl.includes('dav.jianguoyun.com')) {
    return '/api/webdav'
  }
  return originalUrl
}

export const webdavService = {
  async getConfig(): Promise<WebDavConfig> {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : {
      serverUrl: '',
      username: '',
      password: '',
      remotePath: '/DailyRead'
    }
  },
  
  async saveConfig(config: WebDavConfig): Promise<void> {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
  },
  
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

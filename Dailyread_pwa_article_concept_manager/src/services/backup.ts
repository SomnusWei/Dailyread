import type { BackupData } from '@/types'
import { articleService } from './article'

export const backupService = {
  async exportToJSON(): Promise<string> {
    const articles = await articleService.getAll()
    
    const backupData: BackupData = {
      version: 7,
      exportTime: new Date().toISOString(),
      dataType: 'daily_read_backup',
      articles,
      // 不导出概念和临床笔记数据
      concepts: [],
      clinicalNotes: []
    }
    
    return JSON.stringify(backupData, null, 2)
  },
  
  async importFromJSON(jsonString: string, clearBeforeImport: boolean = false): Promise<void> {
    const data = JSON.parse(jsonString)
    
    if (data.articles && Array.isArray(data.articles)) {
      if (clearBeforeImport) {
        await articleService.importFromJSON(JSON.stringify({ articles: data.articles }))
      } else {
        const existingArticles = await articleService.getAll()
        const newArticles = data.articles.filter((a: { title: string }) => 
          !existingArticles.some(ea => ea.title === a.title)
        )
        for (const article of newArticles) {
          await articleService.create({
            title: article.title,
            content: article.content || '',
            contentHtml: article.contentHtml || '',
            chineseChars: article.chineseChars || 0,
            fontFamily: article.fontFamily || 'default',
            fontSize: article.fontSize || 16,
            isReading: article.isReading || false,
            isRequired: article.isRequired || false,
            useIndependentCheckRate: article.useIndependentCheckRate || false,
            independentCheckRate: article.independentCheckRate || 0,
            checkInDays: article.checkInDays || 0,
            completionRate: article.completionRate || 0,
            imagewebp: article.imagewebp || ''
          })
        }
      }
    }
    
    // 保留旧备份文件兼容性：概念和临床笔记数据不导入
    if (data.concepts && Array.isArray(data.concepts) && data.concepts.length > 0) {
      console.log(`检测到旧备份文件包含 ${data.concepts.length} 条概念数据，已跳过导入`)
    }
    
    if (data.clinicalNotes && Array.isArray(data.clinicalNotes) && data.clinicalNotes.length > 0) {
      console.log(`检测到旧备份文件包含 ${data.clinicalNotes.length} 条临床笔记数据，已跳过导入`)
    }
  }
}

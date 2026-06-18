import type { BackupData } from '@/types'
import { articleService } from './article'
import { conceptService } from './concept'
import { clinicalService } from './clinical'

export const backupService = {
  async exportToJSON(): Promise<string> {
    const [articles, concepts, clinicalNotes] = await Promise.all([
      articleService.getAll(),
      conceptService.getAll(),
      clinicalService.getAll()
    ])
    
    const backupData: BackupData = {
      version: 6,
      exportTime: new Date().toISOString(),
      dataType: 'daily_read_backup',
      articles,
      concepts,
      clinicalNotes
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
    
    if (data.concepts && Array.isArray(data.concepts)) {
      if (clearBeforeImport) {
        await conceptService.importFromJSON(JSON.stringify({ concepts: data.concepts }))
      } else {
        const existingConcepts = await conceptService.getAll()
        const newConcepts = data.concepts.filter((c: { title: string }) =>
          !existingConcepts.some(ec => ec.title === c.title)
        )
        for (const concept of newConcepts) {
          await conceptService.create({
            title: concept.title,
            category: concept.category || '',
            subject: concept.subject || '',
            chapter: concept.chapter || '',
            content: concept.content || '',
            isReading: concept.isReading || false
          })
        }
      }
    }
    
    if (data.clinicalNotes && Array.isArray(data.clinicalNotes)) {
      if (clearBeforeImport) {
        const existingNotes = await clinicalService.getAll()
        for (const note of existingNotes) {
          await clinicalService.delete(note.id)
        }
      }
      const existingNotes = await clinicalService.getAll()
      const newNotes = data.clinicalNotes.filter((n: { title: string }) =>
        !existingNotes.some(en => en.title === n.title)
      )
      for (const note of newNotes) {
        await clinicalService.create({
          title: note.title,
          pathogenesis: note.pathogenesis || '',
          treatment: note.treatment || '',
          prescription: note.prescription || '',
          notes: note.notes || '',
          isReading: note.isReading || false
        })
      }
    }
  }
}

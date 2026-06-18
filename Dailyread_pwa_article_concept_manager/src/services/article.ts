import type { Article } from '@/types'

const STORAGE_KEY = 'dailyread_articles'

export const articleService = {
  async getAll(): Promise<Article[]> {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  },
  
  async create(article: Omit<Article, 'id' | 'createTime' | 'lastModified'>): Promise<Article> {
    const articles = await this.getAll()
    const now = new Date().toISOString()
    const newArticle: Article = {
      ...article,
      id: articles.length > 0 ? Math.max(...articles.map(a => a.id)) + 1 : 1,
      createTime: now,
      lastModified: now
    }
    articles.push(newArticle)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(articles))
    return newArticle
  },
  
  async update(id: number, data: Partial<Article>): Promise<Article> {
    const articles = await this.getAll()
    const index = articles.findIndex(a => a.id === id)
    if (index === -1) {
      throw new Error('文章不存在')
    }
    articles[index] = {
      ...articles[index],
      ...data,
      lastModified: new Date().toISOString()
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(articles))
    return articles[index]
  },
  
  async delete(id: number): Promise<void> {
    const articles = await this.getAll()
    const filtered = articles.filter(a => a.id !== id)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  },
  
  async bulkDelete(ids: number[]): Promise<void> {
    const articles = await this.getAll()
    const filtered = articles.filter(a => !ids.includes(a.id))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  },
  
  async importFromJSON(jsonData: string): Promise<void> {
    const data = JSON.parse(jsonData)
    if (data.articles && Array.isArray(data.articles)) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data.articles))
    }
  },
  
  async exportToJSON(): Promise<string> {
    const articles = await this.getAll()
    return JSON.stringify({ articles }, null, 2)
  }
}

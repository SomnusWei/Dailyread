import type { Concept } from '@/types'

const STORAGE_KEY = 'dailyread_concepts'

export const conceptService = {
  async getAll(): Promise<Concept[]> {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  },
  
  async create(concept: Omit<Concept, 'id' | 'createTime' | 'lastModified'>): Promise<Concept> {
    const concepts = await this.getAll()
    const now = new Date().toISOString()
    const newConcept: Concept = {
      ...concept,
      id: concepts.length > 0 ? Math.max(...concepts.map(c => c.id)) + 1 : 1,
      createTime: now,
      lastModified: now
    }
    concepts.push(newConcept)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(concepts))
    return newConcept
  },
  
  async update(id: number, data: Partial<Concept>): Promise<Concept> {
    const concepts = await this.getAll()
    const index = concepts.findIndex(c => c.id === id)
    if (index === -1) {
      throw new Error('概念不存在')
    }
    concepts[index] = {
      ...concepts[index],
      ...data,
      lastModified: new Date().toISOString()
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(concepts))
    return concepts[index]
  },
  
  async delete(id: number): Promise<void> {
    const concepts = await this.getAll()
    const filtered = concepts.filter(c => c.id !== id)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  },
  
  async bulkDelete(ids: number[]): Promise<void> {
    const concepts = await this.getAll()
    const filtered = concepts.filter(c => !ids.includes(c.id))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  },
  
  async importFromJSON(jsonData: string): Promise<void> {
    const data = JSON.parse(jsonData)
    if (data.concepts && Array.isArray(data.concepts)) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data.concepts))
    }
  },
  
  async exportToJSON(): Promise<string> {
    const concepts = await this.getAll()
    return JSON.stringify({ concepts }, null, 2)
  }
}

import type { ClinicalNote } from '@/types'

const STORAGE_KEY = 'dailyread_clinical_notes'

export const clinicalService = {
  async getAll(): Promise<ClinicalNote[]> {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  },
  
  async create(note: Omit<ClinicalNote, 'id' | 'createTime' | 'lastModified'>): Promise<ClinicalNote> {
    const notes = await this.getAll()
    const now = new Date().toISOString()
    const newNote: ClinicalNote = {
      ...note,
      id: notes.length > 0 ? Math.max(...notes.map(n => n.id)) + 1 : 1,
      createTime: now,
      lastModified: now
    }
    notes.push(newNote)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notes))
    return newNote
  },
  
  async update(id: number, data: Partial<ClinicalNote>): Promise<ClinicalNote> {
    const notes = await this.getAll()
    const index = notes.findIndex(n => n.id === id)
    if (index === -1) {
      throw new Error('临床笔记不存在')
    }
    notes[index] = {
      ...notes[index],
      ...data,
      lastModified: new Date().toISOString()
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notes))
    return notes[index]
  },
  
  async delete(id: number): Promise<void> {
    const notes = await this.getAll()
    const filtered = notes.filter(n => n.id !== id)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  },
  
  async bulkDelete(ids: number[]): Promise<void> {
    const notes = await this.getAll()
    const filtered = notes.filter(n => !ids.includes(n.id))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  },
  
  async importFromJSON(jsonData: string): Promise<void> {
    const data = JSON.parse(jsonData)
    if (data.clinicalNotes && Array.isArray(data.clinicalNotes)) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data.clinicalNotes))
    }
  },
  
  async exportToJSON(): Promise<string> {
    const notes = await this.getAll()
    return JSON.stringify({ clinicalNotes: notes }, null, 2)
  }
}

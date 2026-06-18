import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ClinicalNote } from '@/types'
import { clinicalService } from '@/services/clinical'

export const useClinicalStore = defineStore('clinical', () => {
  const clinicalNotes = ref<ClinicalNote[]>([])
  const loading = ref(false)
  
  const totalCount = computed(() => clinicalNotes.value.length)
  const readingCount = computed(() => clinicalNotes.value.filter(c => c.isReading).length)
  
  async function loadClinicalNotes() {
    loading.value = true
    try {
      clinicalNotes.value = await clinicalService.getAll()
    } catch (error) {
      console.error('加载临床笔记失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  async function addClinicalNote(note: Omit<ClinicalNote, 'id' | 'createTime' | 'lastModified'>) {
    const newNote = await clinicalService.create(note)
    clinicalNotes.value.push(newNote)
    return newNote
  }
  
  async function updateClinicalNote(id: number, data: Partial<ClinicalNote>) {
    const updated = await clinicalService.update(id, data)
    const index = clinicalNotes.value.findIndex(c => c.id === id)
    if (index !== -1) {
      clinicalNotes.value[index] = updated
    }
    return updated
  }
  
  async function deleteClinicalNote(id: number) {
    await clinicalService.delete(id)
    clinicalNotes.value = clinicalNotes.value.filter(c => c.id !== id)
  }
  
  async function deleteClinicalNotes(ids: number[]) {
    await clinicalService.bulkDelete(ids)
    clinicalNotes.value = clinicalNotes.value.filter(c => !ids.includes(c.id))
  }
  
  function getClinicalNoteById(id: number): ClinicalNote | undefined {
    return clinicalNotes.value.find(c => c.id === id)
  }
  
  return {
    clinicalNotes,
    loading,
    totalCount,
    readingCount,
    loadClinicalNotes,
    addClinicalNote,
    updateClinicalNote,
    deleteClinicalNote,
    deleteClinicalNotes,
    getClinicalNoteById
  }
})

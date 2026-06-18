import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Concept } from '@/types'
import { conceptService } from '@/services/concept'

export const useConceptStore = defineStore('concept', () => {
  const concepts = ref<Concept[]>([])
  const loading = ref(false)
  
  const totalCount = computed(() => concepts.value.length)
  const readingCount = computed(() => concepts.value.filter(c => c.isReading).length)
  
  async function loadConcepts() {
    loading.value = true
    try {
      concepts.value = await conceptService.getAll()
    } catch (error) {
      console.error('加载概念失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  async function addConcept(concept: Omit<Concept, 'id' | 'createTime' | 'lastModified'>) {
    const newConcept = await conceptService.create(concept)
    concepts.value.push(newConcept)
    return newConcept
  }
  
  async function updateConcept(id: number, data: Partial<Concept>) {
    const updated = await conceptService.update(id, data)
    const index = concepts.value.findIndex(c => c.id === id)
    if (index !== -1) {
      concepts.value[index] = updated
    }
    return updated
  }
  
  async function deleteConcept(id: number) {
    await conceptService.delete(id)
    concepts.value = concepts.value.filter(c => c.id !== id)
  }
  
  async function deleteConcepts(ids: number[]) {
    await conceptService.bulkDelete(ids)
    concepts.value = concepts.value.filter(c => !ids.includes(c.id))
  }
  
  function getConceptById(id: number): Concept | undefined {
    return concepts.value.find(c => c.id === id)
  }
  
  return {
    concepts,
    loading,
    totalCount,
    readingCount,
    loadConcepts,
    addConcept,
    updateConcept,
    deleteConcept,
    deleteConcepts,
    getConceptById
  }
})

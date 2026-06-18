import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Article } from '@/types'
import { articleService } from '@/services/article'

export const useArticleStore = defineStore('article', () => {
  const articles = ref<Article[]>([])
  const loading = ref(false)
  
  const totalCount = computed(() => articles.value.length)
  const readingCount = computed(() => articles.value.filter(a => a.isReading).length)
  
  async function loadArticles() {
    loading.value = true
    try {
      articles.value = await articleService.getAll()
    } catch (error) {
      console.error('加载文章失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  async function addArticle(article: Omit<Article, 'id' | 'createTime' | 'lastModified'>) {
    const newArticle = await articleService.create(article)
    articles.value.push(newArticle)
    return newArticle
  }
  
  async function updateArticle(id: number, data: Partial<Article>) {
    const updated = await articleService.update(id, data)
    const index = articles.value.findIndex(a => a.id === id)
    if (index !== -1) {
      articles.value[index] = updated
    }
    return updated
  }
  
  async function deleteArticle(id: number) {
    await articleService.delete(id)
    articles.value = articles.value.filter(a => a.id !== id)
  }
  
  async function deleteArticles(ids: number[]) {
    await articleService.bulkDelete(ids)
    articles.value = articles.value.filter(a => !ids.includes(a.id))
  }
  
  function getArticleById(id: number): Article | undefined {
    return articles.value.find(a => a.id === id)
  }
  
  return {
    articles,
    loading,
    totalCount,
    readingCount,
    loadArticles,
    addArticle,
    updateArticle,
    deleteArticle,
    deleteArticles,
    getArticleById
  }
})

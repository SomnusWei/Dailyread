import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { apiService } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  const isLoggedIn = computed(() => apiService.isLoggedIn())
  
  /**
   * 注册
   */
  async function register(username: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiService.register(username, password)
      if (response.success) {
        user.value = response.user
        return true
      }
      return false
    } catch (err) {
      error.value = err instanceof Error ? err.message : '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 登录
   */
  async function login(username: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiService.login(username, password)
      if (response.success) {
        user.value = response.user
        return true
      }
      return false
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 登出
   */
  function logout() {
    apiService.logout()
    user.value = null
  }
  
  /**
   * 初始化：从服务器获取用户信息
   */
  async function init() {
    if (isLoggedIn.value) {
      const userData = await apiService.getUser()
      if (userData) {
        user.value = userData
      } else {
        // token 无效，清除登录状态
        logout()
      }
    }
  }
  
  return {
    user,
    loading,
    error,
    isLoggedIn,
    register,
    login,
    logout,
    init
  }
})
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token') || null)
  
  const isLoggedIn = computed(() => !!token.value)
  
  function login(userData: User, tokenValue: string) {
    user.value = userData
    token.value = tokenValue
    localStorage.setItem('token', tokenValue)
  }
  
  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }
  
  function initFromStorage() {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      user.value = JSON.parse(savedUser)
    }
  }
  
  function saveUser() {
    if (user.value) {
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }
  
  return {
    user,
    token,
    isLoggedIn,
    login,
    logout,
    initFromStorage,
    saveUser
  }
})

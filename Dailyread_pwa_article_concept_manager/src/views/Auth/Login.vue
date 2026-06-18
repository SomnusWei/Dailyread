<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Eye, EyeOff, LogIn, User, Lock } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!email.value || !password.value) {
    error.value = '请输入邮箱和密码'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    // 模拟登录（实际项目中应调用后端API）
    const user = {
      id: 1,
      username: email.value.split('@')[0],
      email: email.value,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    
    authStore.login(user, 'mock-token-' + Date.now())
    authStore.saveUser()
    
    await router.push('/')
  } catch {
    error.value = '登录失败，请检查邮箱和密码'
  } finally {
    loading.value = false
  }
}

function goToRegister() {
  router.push('/register')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700">
    <div class="w-full max-w-md mx-4">
      <div class="card p-8">
        <div class="text-center mb-8">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <LogIn class="w-8 h-8 text-primary-600" />
          </div>
          <h1 class="text-2xl font-bold text-gray-800">每日阅读管理器</h1>
          <p class="text-gray-500 mt-2">登录您的账户</p>
        </div>
        
        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
            <div class="relative">
              <User class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                v-model="email"
                type="email"
                placeholder="请输入邮箱"
                class="input pl-10"
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                class="input pl-10 pr-10"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <Eye v-if="showPassword" class="w-5 h-5" />
                <EyeOff v-else class="w-5 h-5" />
              </button>
            </div>
          </div>
          
          <div v-if="error" class="p-3 bg-danger-50 text-danger-600 rounded-lg text-sm">
            {{ error }}
          </div>
          
          <button
            type="submit"
            :disabled="loading"
            class="btn btn-primary w-full"
          >
            <LogIn class="w-4 h-4 mr-2" />
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        
        <p class="text-center text-gray-500 text-sm mt-6">
          还没有账户？
          <button @click="goToRegister" class="text-primary-600 hover:text-primary-700 font-medium">
            立即注册
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Eye, EyeOff, UserPlus, User, Lock } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  if (!username.value || !password.value || !confirmPassword.value) {
    error.value = '请填写所有字段'
    return
  }
  
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  if (password.value.length < 6) {
    error.value = '密码长度至少为6位'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    // 调用服务器端注册 API
    const success = await authStore.register(username.value, password.value)
    
    if (success) {
      await router.push('/')
    } else {
      error.value = authStore.error || '注册失败，请重试'
    }
  } catch {
    error.value = '注册失败，请重试'
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700">
    <div class="w-full max-w-md mx-4">
      <div class="card p-8">
        <div class="text-center mb-8">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <UserPlus class="w-8 h-8 text-primary-600" />
          </div>
          <h1 class="text-2xl font-bold text-gray-800">每日阅读管理器</h1>
          <p class="text-gray-500 mt-2">创建新账户</p>
        </div>
        
        <form @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <div class="relative">
              <User class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                v-model="username"
                type="text"
                placeholder="请输入用户名"
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
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">确认密码</label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                v-model="confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请再次输入密码"
                class="input pl-10"
              />
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
            <UserPlus class="w-4 h-4 mr-2" />
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>
        
        <p class="text-center text-gray-500 text-sm mt-6">
          已有账户？
          <button @click="goToLogin" class="text-primary-600 hover:text-primary-700 font-medium">
            立即登录
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

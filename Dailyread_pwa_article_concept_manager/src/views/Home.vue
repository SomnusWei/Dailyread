<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useArticleStore } from '@/stores/article'
import { 
  BookOpen, 
  Settings, 
  LogOut,
  FileText,
  Clock,
  Target,
  ChevronRight
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const articleStore = useArticleStore()

const loading = ref(true)

onMounted(async () => {
  await articleStore.loadArticles()
  loading.value = false
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <header class="bg-white shadow-sm sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
            <BookOpen class="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 class="text-xl font-bold text-gray-800">每日阅读管理器</h1>
            <p class="text-sm text-gray-500">欢迎, {{ authStore.user?.username }}</p>
          </div>
        </div>
        <button
          @click="handleLogout"
          class="btn btn-secondary flex items-center space-x-2"
        >
          <LogOut class="w-4 h-4" />
          <span>退出登录</span>
        </button>
      </div>
    </header>
    
    <main class="max-w-7xl mx-auto px-4 py-8">
      <div v-if="loading" class="flex justify-center items-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
      
      <div v-else class="space-y-6">
        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div class="card p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500">文章总数</p>
                <p class="text-3xl font-bold text-gray-800 mt-1">{{ articleStore.totalCount }}</p>
                <p class="text-sm text-success-600 mt-1">{{ articleStore.readingCount }} 篇阅读中</p>
              </div>
              <div class="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center">
                <FileText class="w-7 h-7 text-primary-600" />
              </div>
            </div>
          </div>
          
          <div class="card p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500">备份状态</p>
                <p class="text-3xl font-bold text-gray-800 mt-1">-</p>
                <p class="text-sm text-gray-500 mt-1">查看备份详情</p>
              </div>
              <div class="w-14 h-14 bg-amber-100 rounded-xl flex items-center justify-center">
                <Target class="w-7 h-7 text-amber-600" />
              </div>
            </div>
          </div>
          
          <div class="card p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500">阅读进度</p>
                <p class="text-3xl font-bold text-gray-800 mt-1">-</p>
                <p class="text-sm text-gray-500 mt-1">持续阅读</p>
              </div>
              <div class="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center">
                <BookOpen class="w-7 h-7 text-green-600" />
              </div>
            </div>
          </div>
        </div>
        
        <!-- 功能入口 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            @click="router.push('/articles')"
            class="card p-6 text-left hover:shadow-md transition-shadow group"
          >
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-800">文章管理</h3>
                <p class="text-sm text-gray-500 mt-1">管理您的阅读文章</p>
              </div>
              <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                <BookOpen class="w-6 h-6 text-primary-600" />
              </div>
            </div>
            <ChevronRight class="w-5 h-5 text-gray-400 mt-4 group-hover:text-primary-500 group-hover:translate-x-1 transition-all" />
          </button>
          
          <button
            @click="router.push('/backup')"
            class="card p-6 text-left hover:shadow-md transition-shadow group"
          >
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-800">备份与恢复</h3>
                <p class="text-sm text-gray-500 mt-1">数据备份与WebDAV同步</p>
              </div>
              <div class="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center group-hover:bg-amber-200 transition-colors">
                <Target class="w-6 h-6 text-amber-600" />
              </div>
            </div>
            <ChevronRight class="w-5 h-5 text-gray-400 mt-4 group-hover:text-amber-500 group-hover:translate-x-1 transition-all" />
          </button>
          
          <button
            @click="router.push('/settings')"
            class="card p-6 text-left hover:shadow-md transition-shadow group"
          >
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-800">设置</h3>
                <p class="text-sm text-gray-500 mt-1">应用设置与偏好</p>
              </div>
              <div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <Settings class="w-6 h-6 text-gray-600" />
              </div>
            </div>
            <ChevronRight class="w-5 h-5 text-gray-400 mt-4 group-hover:text-gray-500 group-hover:translate-x-1 transition-all" />
          </button>
        </div>
        
        <!-- 快捷操作 -->
        <div class="card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-800">快捷操作</h3>
            <button
              @click="router.push('/settings')"
              class="flex items-center space-x-2 text-gray-600 hover:text-primary-600"
            >
              <Settings class="w-4 h-4" />
              <span class="text-sm">设置</span>
            </button>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button class="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <Clock class="w-8 h-8 text-gray-600 mb-2" />
              <span class="text-sm text-gray-700">今日阅读</span>
            </button>
            <button class="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <Target class="w-8 h-8 text-gray-600 mb-2" />
              <span class="text-sm text-gray-700">学习统计</span>
            </button>
            <button class="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <FileText class="w-8 h-8 text-gray-600 mb-2" />
              <span class="text-sm text-gray-700">导入数据</span>
            </button>
            <button class="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <BookOpen class="w-8 h-8 text-gray-600 mb-2" />
              <span class="text-sm text-gray-700">随机阅读</span>
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

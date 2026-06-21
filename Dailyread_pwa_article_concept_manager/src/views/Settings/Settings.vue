<script setup lang="ts">import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { User, Bell, Palette, HelpCircle, Info, LogOut } from 'lucide-vue-next';
const router = useRouter();
const authStore = useAuthStore();
const userInfo = ref({
 username: ''
});

onMounted(() => {
 if (authStore.user) {
 userInfo.value = {
 username: authStore.user.username
 };
 }
});
function handleLogout() {
 if (confirm('确定要退出登录吗？')) {
 authStore.logout();
 router.push('/login');
 }
}
function goBack() {
 router.push('/');
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <header class="bg-white shadow-sm sticky top-0 z-40">
      <div class="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button @click="goBack" class="text-gray-600 hover:text-gray-800">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
          </button>
          <div>
            <h1 class="text-xl font-bold text-gray-800">设置</h1>
            <p class="text-sm text-gray-500">管理您的账户和偏好设置</p>
          </div>
        </div>
      </div>
    </header>
    
    <main class="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <!-- 用户信息 -->
      <div class="card p-6">
        <div class="flex items-center space-x-4">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
            <User class="w-8 h-8 text-primary-600" />
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-800">{{ userInfo.username }}</h2>
          </div>
        </div>
      </div>
      
      <!-- 设置选项 -->
      <div class="card overflow-hidden">
        <div class="border-b border-gray-200">
          <button
            @click="router.push('/articles')"
            class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors"
          >
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
              </svg>
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">文章管理</p>
              <p class="text-sm text-gray-500">管理您的阅读文章</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
        
        <div class="border-b border-gray-200">
          <button
            @click="router.push('/concepts')"
            class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors"
          >
            <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
              </svg>
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">概念管理</p>
              <p class="text-sm text-gray-500">管理您的概念数据</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
        
        <div class="border-b border-gray-200">
          <button
            @click="router.push('/clinical')"
            class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors"
          >
            <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
              </svg>
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">临床笔记</p>
              <p class="text-sm text-gray-500">管理您的临床笔记</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
        
        <div class="border-b border-gray-200">
          <button
            @click="router.push('/backup')"
            class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors"
          >
            <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
              </svg>
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">备份与恢复</p>
              <p class="text-sm text-gray-500">数据备份与 WebDAV 同步</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- 其他设置 -->
      <div class="card overflow-hidden">
        <div class="border-b border-gray-200">
          <button class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors">
            <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Bell class="w-5 h-5 text-gray-600" />
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">通知设置</p>
              <p class="text-sm text-gray-500">管理推送通知和提醒</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
        
        <div class="border-b border-gray-200">
          <button class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors">
            <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Palette class="w-5 h-5 text-gray-600" />
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">外观主题</p>
              <p class="text-sm text-gray-500">自定义界面颜色和字体</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
        
        <div class="border-b border-gray-200">
          <button class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors">
            <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <HelpCircle class="w-5 h-5 text-gray-600" />
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">帮助与支持</p>
              <p class="text-sm text-gray-500">获取使用帮助和常见问题解答</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
        
        <div>
          <button class="w-full px-6 py-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors">
            <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Info class="w-5 h-5 text-gray-600" />
            </div>
            <div class="text-left flex-1">
              <p class="font-medium text-gray-800">关于</p>
              <p class="text-sm text-gray-500">版本信息和更新日志</p>
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- 退出登录 -->
      <button
        @click="handleLogout"
        class="w-full card p-4 flex items-center space-x-3 hover:bg-gray-50 transition-colors"
      >
        <div class="w-10 h-10 bg-danger-100 rounded-lg flex items-center justify-center">
          <LogOut class="w-5 h-5 text-danger-600" />
        </div>
        <span class="font-medium text-danger-600">退出登录</span>
      </button>
    </main>
  </div>
</template>

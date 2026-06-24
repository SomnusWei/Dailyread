import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Auth/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Auth/Register.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/articles',
    name: 'Articles',
    component: () => import('@/views/Article/ArticleList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/backup',
    name: 'Backup',
    component: () => import('@/views/Backup/Backup.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings/Settings.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 等待初始化完成
  if (!authStore.initialized) {
    await authStore.init()
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router

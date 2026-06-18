<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  authStore.initFromStorage()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <router-view />
  </div>
</template>

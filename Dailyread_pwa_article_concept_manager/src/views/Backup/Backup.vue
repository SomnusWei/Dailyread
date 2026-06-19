<script setup lang="ts">import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { backupService } from '@/services/backup';
import { webdavService } from '@/services/webdav';
import type { WebDavConfig, BackupData } from '@/types';
import { useArticleStore } from '@/stores/article';
import { useConceptStore } from '@/stores/concept';
import { useClinicalStore } from '@/stores/clinical';
import { Download, Upload, Settings, RefreshCw, Check, AlertCircle } from 'lucide-vue-next';
const router = useRouter();
const articleStore = useArticleStore();
const conceptStore = useConceptStore();
const clinicalStore = useClinicalStore();
const webdavConfig = ref<WebDavConfig>({
 serverUrl: '',
 username: '',
 password: '',
 remotePath: '/DailyRead'
});
const showWebDavModal = ref(false);
const loading = ref(false);
const message = ref('');
const messageType = ref<'success' | 'error'>('success');
onMounted(async () => {
 // 从服务器获取 WebDAV 配置
 const config = await webdavService.getConfig();
 if (config) {
   webdavConfig.value = config;
 }
});
function showMessage(msg: string, type: 'success' | 'error' = 'success') {
 message.value = msg;
 messageType.value = type;
 setTimeout(() => {
 message.value = '';
 }, 3000);
}
async function handleExportBackup() {
 loading.value = true;
 try {
 const data = await backupService.exportToJSON();
 const blob = new Blob([data], { type: 'application/json' });
 const url = URL.createObjectURL(blob);
 const a = document.createElement('a');
 a.href = url;
 a.download = 'daily_read_backup_windows.json';
 a.click();
 URL.revokeObjectURL(url);
 showMessage('备份导出成功！');
 }
 catch (error) {
 console.error('导出失败:', error);
 showMessage('导出失败，请重试', 'error');
 }
 finally {
 loading.value = false;
 }
}
async function handleImportBackup() {
 const input = document.createElement('input');
 input.type = 'file';
 input.accept = '.json';
 input.onchange = async (e) => {
 const file = (e.target as HTMLInputElement).files?.[0];
 if (file) {
 loading.value = true;
 try {
 const reader = new FileReader();
 reader.onload = async (event) => {
 try {
 await backupService.importFromJSON(event.target?.result as string, false);
 await Promise.all([
 articleStore.loadArticles(),
 conceptStore.loadConcepts(),
 clinicalStore.loadClinicalNotes()
 ]);
 showMessage('备份导入成功！');
 }
 catch (error) {
 console.error('导入失败:', error);
 showMessage('导入失败，请检查文件格式', 'error');
 }
 finally {
 loading.value = false;
 }
 };
 reader.readAsText(file);
 }
 catch (error) {
 console.error('读取文件失败:', error);
 showMessage('读取文件失败', 'error');
 loading.value = false;
 }
 }
 };
 input.click();
}
async function testWebDavConnection() {
 if (!webdavConfig.value.serverUrl || !webdavConfig.value.username || !webdavConfig.value.password) {
 showMessage('请先填写 WebDAV 配置', 'error');
 return;
 }
 loading.value = true;
 try {
 const success = await webdavService.testConnection(webdavConfig.value);
 if (success) {
 showMessage('连接成功！');
 }
 else {
 showMessage('连接失败，请检查配置', 'error');
 }
 }
 catch (error) {
 console.error('测试连接失败:', error);
 showMessage('连接失败，请检查配置', 'error');
 }
 finally {
 loading.value = false;
 }
}
async function saveWebDavConfig() {
 if (!webdavConfig.value.serverUrl || !webdavConfig.value.username || !webdavConfig.value.password) {
 showMessage('请填写完整的配置信息', 'error');
 return;
 }
 loading.value = true;
 try {
 const success = await webdavService.saveConfig(webdavConfig.value);
 if (success) {
   showMessage('配置保存成功！');
   showWebDavModal.value = false;
 } else {
   showMessage('保存失败，请重试', 'error');
 }
 }
 catch (error) {
 console.error('保存配置失败:', error);
 showMessage('保存失败，请重试', 'error');
 }
 finally {
 loading.value = false;
 }
}
async function uploadToWebDav() {
 if (!webdavConfig.value.serverUrl || !webdavConfig.value.username || !webdavConfig.value.password) {
 showMessage('请先配置并测试 WebDAV', 'error');
 return;
 }
 loading.value = true;
 try {
 const data = JSON.parse(await backupService.exportToJSON()) as BackupData;
 await webdavService.uploadBackup(webdavConfig.value, data);
 showMessage('上传成功！');
 }
 catch (error) {
 console.error('上传失败:', error);
 showMessage('上传失败，请检查网络和配置', 'error');
 }
 finally {
 loading.value = false;
 }
}
async function downloadFromWebDav() {
 if (!webdavConfig.value.serverUrl || !webdavConfig.value.username || !webdavConfig.value.password) {
 showMessage('请先配置并测试 WebDAV', 'error');
 return;
 }
 if (!confirm('确定要从云端下载并覆盖本地数据吗？'))
 return;
 loading.value = true;
 try {
 const data = await webdavService.downloadBackup(webdavConfig.value);
 await backupService.importFromJSON(JSON.stringify(data), true);
 await Promise.all([
 articleStore.loadArticles(),
 conceptStore.loadConcepts(),
 clinicalStore.loadClinicalNotes()
 ]);
 showMessage('下载成功！');
 }
 catch (error) {
 console.error('下载失败:', error);
 showMessage('下载失败，请检查网络和配置', 'error');
 }
 finally {
 loading.value = false;
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
            <h1 class="text-xl font-bold text-gray-800">备份与恢复</h1>
            <p class="text-sm text-gray-500">管理您的数据备份</p>
          </div>
        </div>
      </div>
    </header>
    
    <main class="max-w-3xl mx-auto px-4 py-6">
      <!-- 消息提示 -->
      <div v-if="message" class="mb-6">
        <div
          :class="[
            'p-4 rounded-lg flex items-center space-x-3',
            messageType === 'success' ? 'bg-success-50 text-success-700' : 'bg-danger-50 text-danger-700'
          ]"
        >
          <Check v-if="messageType === 'success'" class="w-5 h-5" />
          <AlertCircle v-else class="w-5 h-5" />
          <span>{{ message }}</span>
        </div>
      </div>
      
      <!-- 本地备份 -->
      <div class="card p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">本地备份</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            @click="handleExportBackup"
            :disabled="loading"
            class="btn btn-primary flex items-center justify-center space-x-2"
          >
            <Download class="w-5 h-5" />
            <span>{{ loading ? '导出中...' : '导出备份' }}</span>
          </button>
          <button
            @click="handleImportBackup"
            :disabled="loading"
            class="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <Upload class="w-5 h-5" />
            <span>{{ loading ? '导入中...' : '导入备份' }}</span>
          </button>
        </div>
        <p class="text-sm text-gray-500 mt-4">
          备份文件格式：daily_read_backup_windows.json（包含文章、概念、临床笔记）
        </p>
      </div>
      
      <!-- WebDAV 同步 -->
      <div class="card p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-800">WebDAV 同步</h2>
          <button
            @click="showWebDavModal = true"
            class="btn btn-secondary flex items-center space-x-2"
          >
            <Settings class="w-4 h-4" />
            <span>配置</span>
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            @click="uploadToWebDav"
            :disabled="loading"
            class="btn btn-primary flex items-center justify-center space-x-2"
          >
            <Upload class="w-5 h-5" />
            <span>{{ loading ? '上传中...' : '上传到云端' }}</span>
          </button>
          <button
            @click="downloadFromWebDav"
            :disabled="loading"
            class="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <Download class="w-5 h-5" />
            <span>{{ loading ? '下载中...' : '从云端下载' }}</span>
          </button>
        </div>
        <div class="mt-4 p-4 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-600">
            <strong>支持的服务：</strong>坚果云、Nextcloud 等遵循 WebDAV 协议的云存储服务
          </p>
          <p class="text-sm text-gray-500 mt-2">
            坚果云服务器地址：<code class="px-2 py-1 bg-white rounded">https://dav.jianguoyun.com/dav/</code>
          </p>
        </div>
      </div>
      
      <!-- 数据统计 -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">数据统计</h2>
        <div class="grid grid-cols-3 gap-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-primary-600">{{ articleStore.totalCount }}</p>
            <p class="text-sm text-gray-500">文章</p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-bold text-purple-600">{{ conceptStore.totalCount }}</p>
            <p class="text-sm text-gray-500">概念</p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-bold text-green-600">{{ clinicalStore.totalCount }}</p>
            <p class="text-sm text-gray-500">临床笔记</p>
          </div>
        </div>
      </div>
    </main>
    
    <!-- WebDAV 配置弹窗 -->
    <div v-if="showWebDavModal" class="modal-overlay" @click.self="showWebDavModal = false">
      <div class="modal-content">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold text-gray-800">配置 WebDAV</h2>
            <button
              @click="showWebDavModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <form @submit.prevent="saveWebDavConfig" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">服务器地址</label>
              <input
                v-model="webdavConfig.serverUrl"
                type="text"
                placeholder="如：https://dav.jianguoyun.com/dav/"
                class="input"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
              <input
                v-model="webdavConfig.username"
                type="text"
                placeholder="您的用户名"
                class="input"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
              <input
                v-model="webdavConfig.password"
                type="password"
                placeholder="您的密码"
                class="input"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">远程路径</label>
              <input
                v-model="webdavConfig.remotePath"
                type="text"
                placeholder="/DailyRead"
                class="input"
              />
            </div>
            
            <div class="flex space-x-3">
              <button
                type="button"
                @click="testWebDavConnection"
                :disabled="loading"
                class="btn btn-secondary flex-1 flex items-center justify-center space-x-2"
              >
                <RefreshCw :class="['w-4 h-4', loading ? 'animate-spin' : '']" />
                <span>测试连接</span>
              </button>
              <button type="submit" :disabled="loading" class="btn btn-primary flex-1">
                保存配置
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

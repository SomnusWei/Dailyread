<script setup lang="ts">import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useArticleStore } from '@/stores/article';
import type { Article } from '@/types';
import { compressImage, countChineseChars } from '@/utils/imageCompression';
import { Plus, Search, Edit2, Trash2, Upload, Download, X, Check } from 'lucide-vue-next';
const router = useRouter();
const articleStore = useArticleStore();
const searchQuery = ref('');
const selectedIds = ref<number[]>([]);
const showModal = ref(false);
const isEditing = ref(false);
const selectedArticle = ref<Article | null>(null);
const form = ref({
 title: '',
 content: '',
 contentHtml: '',
 chineseChars: 0,
 fontFamily: '',
 fontSize: 16,
 isReading: true,
 isRequired: false,
 useIndependentCheckRate: false,
 independentCheckRate: 0,
 checkInDays: 0,
 completionRate: 0,
 imagewebp: ''
});
const imagePreview = ref('');
const uploadedFile = ref<File | null>(null);
const filteredArticles = computed(() => {
 if (!searchQuery.value)
 return articleStore.articles;
 const query = searchQuery.value.toLowerCase();
 return articleStore.articles.filter(a => a.title.toLowerCase().includes(query) ||
 a.content.toLowerCase().includes(query));
});
const isAllSelected = computed(() => {
 return selectedIds.value.length === filteredArticles.value.length && filteredArticles.value.length > 0;
});
onMounted(() => {
 articleStore.loadArticles();
});
function toggleSelectAll() {
 if (isAllSelected.value) {
 selectedIds.value = [];
 }
 else {
 selectedIds.value = filteredArticles.value.map(a => a.id);
 }
}
function toggleSelect(id: number) {
 const index = selectedIds.value.indexOf(id);
 if (index === -1) {
 selectedIds.value.push(id);
 }
 else {
 selectedIds.value.splice(index, 1);
 }
}
async function openAddModal() {
 isEditing.value = false;
 selectedArticle.value = null;
 form.value = {
 title: '',
 content: '',
 contentHtml: '',
 chineseChars: 0,
 fontFamily: '',
 fontSize: 16,
 isReading: true,
 isRequired: false,
 useIndependentCheckRate: false,
 independentCheckRate: 0,
 checkInDays: 0,
 completionRate: 0,
 imagewebp: ''
 };
 imagePreview.value = '';
 uploadedFile.value = null;
 showModal.value = true;
}
async function openEditModal(article: Article) {
 isEditing.value = true;
 selectedArticle.value = article;
 form.value = {
 title: article.title,
 content: article.content,
 contentHtml: article.contentHtml,
 chineseChars: article.chineseChars,
 fontFamily: article.fontFamily,
 fontSize: article.fontSize,
 isReading: article.isReading,
 isRequired: article.isRequired,
 useIndependentCheckRate: article.useIndependentCheckRate,
 independentCheckRate: article.independentCheckRate,
 checkInDays: article.checkInDays,
 completionRate: article.completionRate,
 imagewebp: article.imagewebp
 };
 if (article.imagewebp) {
 imagePreview.value = `data:image/webp;base64,${article.imagewebp}`;
 }
 else {
 imagePreview.value = '';
 }
 uploadedFile.value = null;
 showModal.value = true;
}
async function handleFileUpload(event: Event) {
 const target = event.target as HTMLInputElement;
 const file = target.files?.[0];
 if (file) {
 uploadedFile.value = file;
 try {
 form.value.imagewebp = await compressImage(file);
 imagePreview.value = `data:image/webp;base64,${form.value.imagewebp}`;
 }
 catch (error) {
 console.error('图片上传失败:', error);
 alert('图片上传失败，请重试');
 }
 }
}
function removeImage() {
 form.value.imagewebp = '';
 imagePreview.value = '';
 uploadedFile.value = null;
}
async function handleSubmit() {
 if (!form.value.title.trim()) {
 alert('请输入文章标题');
 return;
 }
 form.value.chineseChars = countChineseChars(form.value.content);
 try {
 if (isEditing.value && selectedArticle.value) {
 await articleStore.updateArticle(selectedArticle.value.id, form.value);
 }
 else {
 await articleStore.addArticle(form.value);
 }
 showModal.value = false;
 }
 catch (error) {
 console.error('保存失败:', error);
 alert('保存失败，请重试');
 }
}
async function handleDelete(id: number) {
 if (!confirm('确定要删除这篇文章吗？'))
 return;
 try {
 await articleStore.deleteArticle(id);
 }
 catch (error) {
 console.error('删除失败:', error);
 alert('删除失败，请重试');
 }
}
async function handleBatchDelete() {
 if (selectedIds.value.length === 0) {
 alert('请选择要删除的文章');
 return;
 }
 if (!confirm(`确定要删除选中的 ${selectedIds.value.length} 篇文章吗？`))
 return;
 try {
 await articleStore.deleteArticles(selectedIds.value);
 selectedIds.value = [];
 }
 catch (error) {
 console.error('批量删除失败:', error);
 alert('批量删除失败，请重试');
 }
}
function handleImport() {
 const input = document.createElement('input');
 input.type = 'file';
 input.accept = '.json';
 input.onchange = async (e) => {
 const file = (e.target as HTMLInputElement).files?.[0];
 if (file) {
 const reader = new FileReader();
 reader.onload = async () => {
 try {
 await articleStore.loadArticles();
 alert('导入成功');
 }
 catch (error) {
 console.error('导入失败:', error);
 alert('导入失败，请检查文件格式');
 }
 };
 reader.readAsText(file);
 }
 };
 input.click();
}
async function handleExport() {
 try {
 const data = JSON.stringify({ articles: articleStore.articles }, null, 2);
 const blob = new Blob([data], { type: 'application/json' });
 const url = URL.createObjectURL(blob);
 const a = document.createElement('a');
 a.href = url;
 a.download = 'articles_backup.json';
 a.click();
 URL.revokeObjectURL(url);
 }
 catch (error) {
 console.error('导出失败:', error);
 alert('导出失败，请重试');
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
      <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button @click="goBack" class="text-gray-600 hover:text-gray-800">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
          </button>
          <div>
            <h1 class="text-xl font-bold text-gray-800">文章管理</h1>
            <p class="text-sm text-gray-500">共 {{ articleStore.totalCount }} 篇文章</p>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <button @click="handleImport" class="btn btn-secondary flex items-center space-x-2">
            <Upload class="w-4 h-4" />
            <span>导入 JSON</span>
          </button>
          <button @click="handleExport" class="btn btn-secondary flex items-center space-x-2">
            <Download class="w-4 h-4" />
            <span>导出 JSON</span>
          </button>
          <button @click="openAddModal" class="btn btn-primary flex items-center space-x-2">
            <Plus class="w-4 h-4" />
            <span>添加文章</span>
          </button>
        </div>
      </div>
    </header>
    
    <main class="max-w-7xl mx-auto px-4 py-6">
      <!-- 搜索栏 -->
      <div class="card p-4 mb-6">
        <div class="flex items-center space-x-4">
          <div class="flex-1 relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索文章标题或内容..."
              class="input pl-10 w-full"
            />
          </div>
          <button
            v-if="selectedIds.length > 0"
            @click="handleBatchDelete"
            class="btn btn-danger flex items-center space-x-2"
          >
            <Trash2 class="w-4 h-4" />
            <span>删除选中 ({{ selectedIds.length }})</span>
          </button>
        </div>
      </div>
      
      <!-- 文章列表 -->
      <div class="card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th class="w-12">
                  <label class="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      :checked="isAllSelected"
                      @change="toggleSelectAll"
                      class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    />
                  </label>
                </th>
                <th>标题</th>
                <th class="w-20">汉字数</th>
                <th class="w-16">在读</th>
                <th class="w-16">必读</th>
                <th class="w-24">打卡天数</th>
                <th class="w-20">完成率</th>
                <th class="w-16">图片</th>
                <th class="w-24">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="article in filteredArticles" :key="article.id">
                <td>
                  <input
                    type="checkbox"
                    :checked="selectedIds.includes(article.id)"
                    @change="toggleSelect(article.id)"
                    class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  />
                </td>
                <td class="max-w-md truncate" :title="article.title">
                  {{ article.title }}
                  <span v-if="article.isRequired" class="text-red-500 ml-1">★</span>
                </td>
                <td>{{ article.chineseChars }}</td>
                <td>
                  <Check v-if="article.isReading" class="w-5 h-5 text-success-500" />
                  <X v-else class="w-5 h-5 text-gray-300" />
                </td>
                <td>
                  <Check v-if="article.isRequired" class="w-5 h-5 text-success-500" />
                  <X v-else class="w-5 h-5 text-gray-300" />
                </td>
                <td>{{ article.checkInDays }}</td>
                <td>{{ article.completionRate }}%</td>
                <td>
                  <Check v-if="article.imagewebp" class="w-5 h-5 text-success-500" />
                  <X v-else class="w-5 h-5 text-gray-300" />
                </td>
                <td>
                  <div class="flex items-center space-x-2">
                    <button
                      @click="openEditModal(article)"
                      class="p-2 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                    >
                      <Edit2 class="w-4 h-4" />
                    </button>
                    <button
                      @click="handleDelete(article.id)"
                      class="p-2 text-gray-500 hover:text-danger-600 hover:bg-danger-50 rounded-lg"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div v-if="filteredArticles.length === 0" class="text-center py-12">
          <p class="text-gray-500">暂无文章</p>
          <button @click="openAddModal" class="btn btn-primary mt-4">
            <Plus class="w-4 h-4 mr-2" />
            添加第一篇文章
          </button>
        </div>
      </div>
    </main>
    
    <!-- 弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold text-gray-800">
              {{ isEditing ? '编辑文章' : '添加文章' }}
            </h2>
            <button
              @click="showModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <X class="w-6 h-6" />
            </button>
          </div>
          
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
              <input
                v-model="form.title"
                type="text"
                placeholder="请输入文章标题"
                class="input"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">内容</label>
              <textarea
                v-model="form.content"
                rows="6"
                placeholder="请输入文章内容"
                class="input resize-none"
              ></textarea>
            </div>
            
            <!-- 图片上传 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">文章图片</label>
              <div v-if="imagePreview" class="relative mb-2">
                <img :src="imagePreview" alt="预览" class="max-w-full max-h-48 object-contain border rounded-lg" />
                <button
                  type="button"
                  @click="removeImage"
                  class="absolute top-2 right-2 p-1 bg-white/80 rounded-full hover:bg-white"
                >
                  <X class="w-4 h-4 text-gray-600" />
                </button>
              </div>
              <input
                type="file"
                accept="image/*"
                @change="handleFileUpload"
                class="input"
              />
            </div>
            
            <div class="flex flex-wrap gap-4">
              <label class="flex items-center space-x-2 cursor-pointer">
                <input
                  v-model="form.isReading"
                  type="checkbox"
                  class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <span class="text-sm text-gray-700">阅读中</span>
              </label>
              <label class="flex items-center space-x-2 cursor-pointer">
                <input
                  v-model="form.isRequired"
                  type="checkbox"
                  class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <span class="text-sm text-gray-700">必读</span>
              </label>
              <label class="flex items-center space-x-2 cursor-pointer">
                <input
                  v-model="form.useIndependentCheckRate"
                  type="checkbox"
                  class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <span class="text-sm text-gray-700">使用独立目标完成率</span>
              </label>
            </div>
            
            <div v-if="form.useIndependentCheckRate">
              <label class="block text-sm font-medium text-gray-700 mb-1">独立目标完成率 (%)</label>
              <input
                v-model.number="form.independentCheckRate"
                type="number"
                min="0"
                max="100"
                class="input w-32"
              />
            </div>
            
            <div class="flex space-x-3 pt-4">
              <button
                type="button"
                @click="showModal = false"
                class="btn btn-secondary flex-1"
              >
                取消
              </button>
              <button type="submit" class="btn btn-primary flex-1">
                {{ isEditing ? '保存修改' : '添加文章' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

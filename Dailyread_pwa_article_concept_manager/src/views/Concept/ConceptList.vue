<script setup lang="ts">import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useConceptStore } from '@/stores/concept';
import type { Concept } from '@/types';
import { Plus, Search, Edit2, Trash2, Upload, Download, X, Check } from 'lucide-vue-next';
const router = useRouter();
const conceptStore = useConceptStore();
const searchQuery = ref('');
const selectedIds = ref<number[]>([]);
const showModal = ref(false);
const isEditing = ref(false);
const selectedConcept = ref<Concept | null>(null);
const form = ref({
 title: '',
 category: '',
 subject: '',
 chapter: '',
 content: '',
 isReading: true
});
const filteredConcepts = computed(() => {
 if (!searchQuery.value)
 return conceptStore.concepts;
 const query = searchQuery.value.toLowerCase();
 return conceptStore.concepts.filter(c => c.title.toLowerCase().includes(query) ||
 c.category.toLowerCase().includes(query) ||
 c.subject.toLowerCase().includes(query) ||
 c.content.toLowerCase().includes(query));
});
const isAllSelected = computed(() => {
 return selectedIds.value.length === filteredConcepts.value.length && filteredConcepts.value.length > 0;
});
onMounted(() => {
 conceptStore.loadConcepts();
});
function toggleSelectAll() {
 if (isAllSelected.value) {
 selectedIds.value = [];
 }
 else {
 selectedIds.value = filteredConcepts.value.map(c => c.id);
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
function openAddModal() {
 isEditing.value = false;
 selectedConcept.value = null;
 form.value = {
 title: '',
 category: '',
 subject: '',
 chapter: '',
 content: '',
 isReading: true
 };
 showModal.value = true;
}
function openEditModal(concept: Concept) {
 isEditing.value = true;
 selectedConcept.value = concept;
 form.value = {
 title: concept.title,
 category: concept.category,
 subject: concept.subject,
 chapter: concept.chapter,
 content: concept.content,
 isReading: concept.isReading
 };
 showModal.value = true;
}
async function handleSubmit() {
 if (!form.value.title.trim()) {
 alert('请输入概念标题');
 return;
 }
 try {
 if (isEditing.value && selectedConcept.value) {
 await conceptStore.updateConcept(selectedConcept.value.id, form.value);
 }
 else {
 await conceptStore.addConcept(form.value);
 }
 showModal.value = false;
 }
 catch (error) {
 console.error('保存失败:', error);
 alert('保存失败，请重试');
 }
}
async function handleDelete(id: number) {
 if (!confirm('确定要删除这个概念吗？'))
 return;
 try {
 await conceptStore.deleteConcept(id);
 }
 catch (error) {
 console.error('删除失败:', error);
 alert('删除失败，请重试');
 }
}
async function handleBatchDelete() {
 if (selectedIds.value.length === 0) {
 alert('请选择要删除的概念');
 return;
 }
 if (!confirm(`确定要删除选中的 ${selectedIds.value.length} 个概念吗？`))
 return;
 try {
 await conceptStore.deleteConcepts(selectedIds.value);
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
 await conceptStore.loadConcepts();
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
 const data = JSON.stringify({ concepts: conceptStore.concepts }, null, 2);
 const blob = new Blob([data], { type: 'application/json' });
 const url = URL.createObjectURL(blob);
 const a = document.createElement('a');
 a.href = url;
 a.download = 'concepts_backup.json';
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
            <h1 class="text-xl font-bold text-gray-800">概念管理</h1>
            <p class="text-sm text-gray-500">共 {{ conceptStore.totalCount }} 个概念</p>
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
            <span>添加概念</span>
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
              placeholder="搜索概念标题、分类、学科..."
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
      
      <!-- 概念列表 -->
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
                <th class="w-24">分类</th>
                <th class="w-24">学科</th>
                <th class="w-24">章节</th>
                <th class="w-16">学习中</th>
                <th class="w-24">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="concept in filteredConcepts" :key="concept.id">
                <td>
                  <input
                    type="checkbox"
                    :checked="selectedIds.includes(concept.id)"
                    @change="toggleSelect(concept.id)"
                    class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  />
                </td>
                <td class="max-w-md truncate" :title="concept.title">
                  {{ concept.title }}
                </td>
                <td>{{ concept.category || '-' }}</td>
                <td>{{ concept.subject || '-' }}</td>
                <td>{{ concept.chapter || '-' }}</td>
                <td>
                  <Check v-if="concept.isReading" class="w-5 h-5 text-success-500" />
                  <X v-else class="w-5 h-5 text-gray-300" />
                </td>
                <td>
                  <div class="flex items-center space-x-2">
                    <button
                      @click="openEditModal(concept)"
                      class="p-2 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                    >
                      <Edit2 class="w-4 h-4" />
                    </button>
                    <button
                      @click="handleDelete(concept.id)"
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
        
        <div v-if="filteredConcepts.length === 0" class="text-center py-12">
          <p class="text-gray-500">暂无概念</p>
          <button @click="openAddModal" class="btn btn-primary mt-4">
            <Plus class="w-4 h-4 mr-2" />
            添加第一个概念
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
              {{ isEditing ? '编辑概念' : '添加概念' }}
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
                placeholder="请输入概念标题"
                class="input"
              />
            </div>
            
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
                <input
                  v-model="form.category"
                  type="text"
                  placeholder="分类"
                  class="input"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">学科</label>
                <input
                  v-model="form.subject"
                  type="text"
                  placeholder="学科"
                  class="input"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">章节</label>
                <input
                  v-model="form.chapter"
                  type="text"
                  placeholder="章节"
                  class="input"
                />
              </div>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">内容</label>
              <textarea
                v-model="form.content"
                rows="6"
                placeholder="请输入概念内容"
                class="input resize-none"
              ></textarea>
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                v-model="form.isReading"
                type="checkbox"
                class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label class="text-sm text-gray-700">学习中</label>
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
                {{ isEditing ? '保存修改' : '添加概念' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

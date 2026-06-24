<script setup lang="ts">
import { ref } from 'vue'
import { X, Download, Link2, Loader2, AlertCircle, CheckCircle, Info } from 'lucide-vue-next'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const url = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)
const progress = ref('')

// 检测是否为微信文章
function isWechatArticle(url: string): boolean {
  return url.includes('mp.weixin.qq.com') || url.includes('weixin.qq.com')
}

async function convertToPdf() {
  if (!url.value.trim()) {
    error.value = '请输入网页链接'
    return
  }

  try {
    new URL(url.value)
  } catch {
    error.value = '请输入有效的URL地址'
    return
  }

  // 如果是微信文章，提供特殊提示
  if (isWechatArticle(url.value)) {
    error.value = '微信公众号文章无法直接转换。请在微信内置浏览器中打开文章，使用浏览器的"打印"功能（Ctrl+P）来生成PDF。'
    return
  }

  loading.value = true
  error.value = ''
  success.value = false
  progress.value = '正在获取网页内容...'

  try {
    const proxyUrls = [
      `https://api.allorigins.win/raw?url=${encodeURIComponent(url.value)}`,
      `https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(url.value)}`
    ]

    let html = ''
    let fetchSuccess = false

    for (const proxyUrl of proxyUrls) {
      try {
        const response = await fetch(proxyUrl)
        if (response.ok) {
          html = await response.text()
          fetchSuccess = true
          break
        }
      } catch {
        continue
      }
    }

    if (!fetchSuccess) {
      throw new Error('无法获取网页内容，请检查链接是否可访问')
    }

    progress.value = '正在处理内容...'

    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')

    // 提取body内容
    const body = doc.querySelector('body')
    if (!body) {
      throw new Error('无法解析网页内容')
    }

    // 清理内容，移除script和style
    const clone = body.cloneNode(true) as HTMLElement
    clone.querySelectorAll('script, style, nav, footer, header, aside').forEach(el => el.remove())

    // 构建干净的HTML
    const cleanHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <style>
            @page { size: A4; margin: 15mm; }
            * { box-sizing: border-box; }
            body {
              width: 794px;
              margin: 0;
              padding: 20px;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              font-size: 14px;
              line-height: 1.6;
              color: #333;
            }
            img { max-width: 100%; height: auto; }
            table { max-width: 100%; border-collapse: collapse; }
            pre, code { white-space: pre-wrap; word-wrap: break-word; }
          </style>
        </head>
        <body>${clone.innerHTML}</body>
      </html>
    `

    progress.value = '正在生成PDF...'

    // 使用html2pdf生成PDF
    const html2pdf = (window as any).html2pdf
    if (!html2pdf) {
      throw new Error('PDF生成库未加载')
    }

    await html2pdf().set({
      margin: 10,
      filename: `网页_${Date.now()}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    }).from(cleanHtml).save()

    success.value = true
    progress.value = ''
  } catch (err) {
    error.value = err instanceof Error ? err.message : '转换失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="emit('close')">
    <div class="modal-container">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-4 border-b">
        <h3 class="text-lg font-semibold">链接转PDF</h3>
        <button @click="emit('close')" class="p-1 hover:bg-gray-100 rounded">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- 内容 -->
      <div class="p-6 space-y-4">
        <div class="p-3 bg-blue-50 rounded-lg flex items-start gap-2">
          <Info class="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <p class="text-sm text-blue-700">输入网页链接，可将其转换为A4大小的PDF文件下载保存。</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">网页链接</label>
          <div class="relative">
            <Link2 class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="url"
              type="url"
              placeholder="请输入网页地址，如 https://example.com"
              class="input pl-10"
              :disabled="loading"
              @keyup.enter="convertToPdf"
            />
          </div>
        </div>

        <!-- 状态提示 -->
        <div v-if="loading" class="flex items-center gap-2 text-sm text-gray-600">
          <Loader2 class="w-4 h-4 animate-spin" />
          <span>{{ progress }}</span>
        </div>

        <div v-if="error" class="p-3 bg-red-50 rounded-lg flex items-start gap-2">
          <AlertCircle class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p class="text-sm text-red-700">{{ error }}</p>
        </div>

        <div v-if="success" class="p-3 bg-green-50 rounded-lg flex items-start gap-2">
          <CheckCircle class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <p class="text-sm text-green-700">PDF已生成并开始下载！</p>
        </div>

        <!-- 转换按钮 -->
        <button
          @click="convertToPdf"
          :disabled="loading || !url.trim()"
          class="btn btn-primary w-full flex items-center justify-center gap-2"
        >
          <Download v-if="!loading" class="w-4 h-4" />
          <Loader2 v-else class="w-4 h-4 animate-spin" />
          {{ loading ? '转换中...' : '转换为PDF' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-container {
  background: white;
  border-radius: 1rem;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.input:disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
}
</style>

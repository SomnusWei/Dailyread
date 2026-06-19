<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Bold, Italic, Underline, Palette, Eraser } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  modelValue: string
  htmlValue?: string
  placeholder?: string
  fontSize?: number
}>(), {
  fontSize: 26
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:htmlValue', value: string): void
}>()

const editorRef = ref<HTMLDivElement | null>(null)
const isBold = ref(false)
const isItalic = ref(false)
const isUnderline = ref(false)

// 初始化编辑器内容
onMounted(() => {
  if (editorRef.value) {
    if (props.htmlValue && props.htmlValue !== props.modelValue) {
      editorRef.value.innerHTML = props.htmlValue
    } else if (props.modelValue) {
      editorRef.value.textContent = props.modelValue
    }
  }
})

// 监听外部值变化
watch(() => props.htmlValue, (newVal) => {
  if (editorRef.value && newVal) {
    if (editorRef.value.innerHTML !== newVal) {
      editorRef.value.innerHTML = newVal
    }
  }
})

watch(() => props.modelValue, (newVal) => {
  if (editorRef.value && !props.htmlValue) {
    if (editorRef.value.textContent !== newVal) {
      editorRef.value.textContent = newVal
    }
  }
})

// 更新内容，嵌入字号样式
function updateContent() {
  if (editorRef.value) {
    const plainText = editorRef.value.textContent || ''
    let html = editorRef.value.innerHTML
    // 嵌入字号样式
    html = wrapHtmlWithFontSize(html, props.fontSize)
    emit('update:modelValue', plainText)
    emit('update:htmlValue', html)
  }
}

// 包装HTML添加字号样式
function wrapHtmlWithFontSize(html: string, fontSize: number): string {
  if (!html || html === '<br>' || html === '<div><br></div>') {
    return ''
  }
  const style = `font-size: ${fontSize}px; line-height: ${fontSize * 1.8}px; color: #333333;`
  // 如果没有包裹span，直接返回原HTML（用户设置的样式优先）
  // RichText组件会使用HTML中的样式
  return html
}

// 格式化命令
function execCommand(command: string, value?: string) {
  document.execCommand(command, false, value)
  updateToolbarState()
  updateContent()
  editorRef.value?.focus()
}

// 切换粗体
function toggleBold() {
  execCommand('bold')
}

// 切换斜体
function toggleItalic() {
  execCommand('italic')
}

// 切换下划线
function toggleUnderline() {
  execCommand('underline')
}

// 设置字体颜色
function setFontColor() {
  const input = document.createElement('input')
  input.type = 'color'
  input.value = '#000000'
  input.onchange = (e) => {
    const color = (e.target as HTMLInputElement).value
    execCommand('foreColor', color)
  }
  input.click()
}

// 设置背景颜色
function setBgColor() {
  const input = document.createElement('input')
  input.type = 'color'
  input.value = '#ffff00'
  input.onchange = (e) => {
    const color = (e.target as HTMLInputElement).value
    execCommand('hiliteColor', color)
  }
  input.click()
}

// 清除格式
function clearFormat() {
  execCommand('removeFormat')
}

// 更新工具栏状态
function updateToolbarState() {
  isBold.value = document.queryCommandState('bold')
  isItalic.value = document.queryCommandState('italic')
  isUnderline.value = document.queryCommandState('underline')
}

// 监听选区变化
document.addEventListener('selectionchange', () => {
  if (editorRef.value && editorRef.value.contains(document.activeElement)) {
    updateToolbarState()
  }
})
</script>

<template>
  <div class="rich-text-editor">
    <!-- 工具栏 -->
    <div class="toolbar flex items-center gap-2 p-2 bg-gray-100 rounded-t-lg border border-b-0 border-gray-300">
      <button
        @click="toggleBold"
        :class="{ 'bg-gray-200': isBold }"
        class="toolbar-btn p-1.5 rounded hover:bg-gray-200 transition-colors"
        title="粗体"
      >
        <Bold class="w-4 h-4" :class="{ 'text-gray-800': isBold, 'text-gray-500': !isBold }" />
      </button>
      
      <button
        @click="toggleItalic"
        :class="{ 'bg-gray-200': isItalic }"
        class="toolbar-btn p-1.5 rounded hover:bg-gray-200 transition-colors"
        title="斜体"
      >
        <Italic class="w-4 h-4" :class="{ 'text-gray-800': isItalic, 'text-gray-500': !isItalic }" />
      </button>
      
      <button
        @click="toggleUnderline"
        :class="{ 'bg-gray-200': isUnderline }"
        class="toolbar-btn p-1.5 rounded hover:bg-gray-200 transition-colors"
        title="下划线"
      >
        <Underline class="w-4 h-4" :class="{ 'text-gray-800': isUnderline, 'text-gray-500': !isUnderline }" />
      </button>
      
      <div class="w-px h-5 bg-gray-300 mx-1"></div>
      
      <button
        @click="setFontColor"
        class="toolbar-btn p-1.5 rounded hover:bg-gray-200 transition-colors"
        title="字体颜色"
      >
        <Palette class="w-4 h-4 text-gray-500" />
      </button>
      
      <button
        @click="setBgColor"
        class="toolbar-btn p-1.5 rounded hover:bg-gray-200 transition-colors"
        title="背景颜色"
      >
        <div class="w-4 h-4 rounded bg-yellow-200 border border-gray-400"></div>
      </button>
      
      <div class="w-px h-5 bg-gray-300 mx-1"></div>
      
      <button
        @click="clearFormat"
        class="toolbar-btn p-1.5 rounded hover:bg-gray-200 transition-colors"
        title="清除格式"
      >
        <Eraser class="w-4 h-4 text-gray-500" />
      </button>
    </div>
    
    <!-- 编辑区域 -->
    <div
      ref="editorRef"
      @input="updateContent"
      @keyup="updateToolbarState"
      @mouseup="updateToolbarState"
      class="editor-area p-3 min-h-[120px] bg-white border border-gray-300 rounded-b-lg focus:outline-none focus:ring-2 focus:ring-primary-500 overflow-auto"
      :contenteditable="true"
      :data-placeholder="placeholder"
    ></div>
  </div>
</template>

<style scoped>
.rich-text-editor {
  width: 100%;
}

.editor-area:empty:before {
  content: attr(data-placeholder);
  color: #9ca3af;
  pointer-events: none;
}

.editor-area:focus:empty:before {
  content: attr(data-placeholder);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
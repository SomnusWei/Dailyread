/**
 * 图片压缩工具
 * 参考鸿蒙端的多级压缩逻辑，实现高质量 WebP 压缩
 */

const MAX_BYTES = 25 * 1024 // 25KB
const WIDTH_STEPS = [480, 360, 280, 200, 140, 100, 70]
const QUALITY_STEPS = [0.8, 0.6, 0.45, 0.3, 0.2, 0.1]

/**
 * 将图片文件压缩为 WebP 格式的 base64 字符串
 * @param file 图片文件
 * @returns base64 字符串（不含前缀）
 */
export async function compressImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const dataUrl = e.target?.result as string
        const img = new Image()
        img.onload = async () => {
          try {
            const result = await compressImageToWebP(img)
            resolve(result)
          } catch (error) {
            reject(error)
          }
        }
        img.onerror = reject
        img.src = dataUrl
      } catch (error) {
        reject(error)
      }
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/**
 * 多级压缩：逐步尝试不同尺寸和质量组合
 * @param img 图片对象
 * @returns base64 字符串（不含前缀）
 */
async function compressImageToWebP(img: HTMLImageElement): Promise<string> {
  const originalWidth = img.width
  const originalHeight = img.height
  
  let bestResult = ''
  let bestSize = Infinity
  
  // 逐步尝试不同尺寸
  for (const targetWidth of WIDTH_STEPS) {
    // 如果目标宽度大于原图宽度，跳过
    if (targetWidth > originalWidth) continue
    
    // 计算目标高度（保持宽高比）
    const scale = targetWidth / originalWidth
    const targetHeight = Math.max(1, Math.floor(originalHeight * scale))
    
    // 逐步尝试不同质量
    for (const quality of QUALITY_STEPS) {
      const canvas = document.createElement('canvas')
      canvas.width = targetWidth
      canvas.height = targetHeight
      
      const ctx = canvas.getContext('2d')
      if (!ctx) continue
      
      // 使用高质量缩放
      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      ctx.drawImage(img, 0, 0, targetWidth, targetHeight)
      
      // 转换为 WebP
      const dataUrl = canvas.toDataURL('image/webp', quality)
      const base64 = dataUrl.split(',')[1]
      
      // 计算 base64 对应的实际字节大小
      const byteSize = Math.ceil(base64.length * 3 / 4)
      
      console.log(`尝试压缩: ${targetWidth}x${targetHeight}, quality=${quality}, size=${byteSize}B`)
      
      // 如果满足大小要求，立即返回
      if (byteSize <= MAX_BYTES) {
        console.log(`命中目标: ${byteSize}B <= ${MAX_BYTES}B`)
        return base64
      }
      
      // 记录最佳结果
      if (byteSize < bestSize) {
        bestSize = byteSize
        bestResult = base64
      }
    }
  }
  
  // 如果所有组合都不满足要求，返回最佳结果
  if (bestResult) {
    console.log(`未命中目标，使用最佳结果: ${bestSize}B`)
    return bestResult
  }
  
  // 如果原图太小，直接返回原图的 WebP 版本
  const canvas = document.createElement('canvas')
  canvas.width = originalWidth
  canvas.height = originalHeight
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(img, 0, 0)
    const dataUrl = canvas.toDataURL('image/webp', 0.8)
    return dataUrl.split(',')[1]
  }
  
  throw new Error('图片压缩失败')
}

/**
 * 统计汉字数量
 * @param text 文本内容
 * @returns 汉字数量
 */
export function countChineseChars(text: string): number {
  const chineseRegex = /[\u4e00-\u9fa5]/g
  const matches = text.match(chineseRegex)
  return matches ? matches.length : 0
}

/**
 * 将 base64 WebP 字符串转换为可显示的 URL
 * @param base64 base64 字符串（不含前缀）
 * @returns data URL
 */
export function webpBase64ToUrl(base64: string): string {
  return `data:image/webp;base64,${base64}`
}
import imageCompression from 'browser-image-compression'

export async function compressImage(file: File): Promise<string> {
  const options = {
    maxSizeMB: 0.025,
    maxWidthOrHeight: 480,
    useWebWorker: true,
    initialQuality: 0.5
  }
  
  try {
    const compressedFile = await imageCompression(file, options)
    const reader = new FileReader()
    
    return new Promise((resolve, reject) => {
      reader.onload = (e) => {
        const result = e.target?.result as string
        // 移除 data:image/webp;base64, 前缀
        const base64 = result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(compressedFile)
    })
  } catch (error) {
    console.error('图片压缩失败:', error)
    throw error
  }
}

export function countChineseChars(text: string): number {
  const chineseRegex = /[\u4e00-\u9fa5]/g
  const matches = text.match(chineseRegex)
  return matches ? matches.length : 0
}

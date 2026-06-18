import picker from '@ohos.file.picker';
import image from '@ohos.multimedia.image';
import fs from '@ohos.file.fs';
import promptAction from '@ohos.promptAction';
import { common } from '@kit.AbilityKit';

/**
 * PixelMap + 尺寸（当前 SDK 的 PixelMap 不暴露 width/height，
 * 需要通过 ImageSource.getImageInfo 读取尺寸，再由调用方按需使用
 */
export interface SizedPixelMap {
  pixelMap: image.PixelMap;
  width: number;
  height: number;
}

/**
 * 图片选择与压缩服务
 *
 * 工作流程（核心修正点）：
 *   1) PhotoViewPicker 选择图片 → content:// 或 file:// URI
 *   2) fs.openSync + readSync 把文件读到 ArrayBuffer
 *   3) 写入沙箱得到绝对路径
 *      （避开 image.createImageSource(Uint8Array)
 *   4) image.createImageSource(绝对路径) → ImageSource
 *   5) 尺寸序列 × quality × format('image/webp') 依次尝试 packing
 *      - 命中 <= 25KB 立即返回；否则返回体积最小的一份作为兜底
 *   6) ArrayBuffer → base64 字符串（正确的 3→4 查表编码）
 *
 * 显示端（Reader / ArticleManage 预览）：
 *   - base64 字符串 → 解码为 Uint8Array（正确的 4→3 查表）
 *   - 写入沙箱临时文件 → image.createImageSource(绝对路径) → createPixelMap()
 *   - 把 PixelMap 传给 Image 组件（不依赖 data URI）
 *
 * 统一的工具方法（均在此文件中实现：
 *   - ImageCompressionService.base64Encode(buffer)  → string
 *   - ImageCompressionService.base64Decode(str)       → Uint8Array
 *   - ImageCompressionService.base64ToPixelMap(ctx, base64)  → SizedPixelMap
 *   - ImageCompressionService.getSandboxPath(ctx, filename)  → string
 */
export class ImageCompressionService {

  private static instance: ImageCompressionService | null = null;
  private appContext: common.Context | null = null;

  static getInstance(): ImageCompressionService {
    if (!ImageCompressionService.instance) {
      ImageCompressionService.instance = new ImageCompressionService();
    }
    return ImageCompressionService.instance;
  }

  setContext(ctx: common.Context): void {
    this.appContext = ctx;
  }

  private getFilesDir(): string {
    if (this.appContext && this.appContext.filesDir) {
      return this.appContext.filesDir;
    }
    return '/data/storage/el2/base/haps/entry/files';
  }

  /**
   * 给定 Context，返回用于写入临时文件的目录
   */
  static getSandboxPath(ctx: common.Context | null, fileName: string): string {
    let dir: string = '/data/storage/el2/base/haps/entry/files';
    if (ctx && ctx.filesDir) {
      dir = ctx.filesDir;
    }
    return dir + '/' + fileName;
  }

  /**
   * base64 编码：ArrayBuffer → base64 字符串
   * (每 3 字节 -> 4 字符，不足补 =)
   */
  static base64Encode(buffer: ArrayBuffer): string {
    const table: string =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    const bytes: Uint8Array = new Uint8Array(buffer);
    const len: number = bytes.length;
    let output: string = '';
    const chunkSize: number = 1500;
    for (let chunkStart: number = 0; chunkStart < len; chunkStart = chunkStart + chunkSize) {
      const chunkEnd: number = Math.min(chunkStart + chunkSize, len);
      let piece: string = '';
      let i: number = chunkStart;
      while (i + 3 <= chunkEnd) {
        const b0: number = bytes[i];
        const b1: number = bytes[i + 1];
        const b2: number = bytes[i + 2];
        piece = piece +
          table[b0 >> 2] +
          table[((b0 & 0x03) << 4) | (b1 >> 4)] +
          table[((b1 & 0x0f) << 2) | (b2 >> 6)] +
          table[b2 & 0x3f];
        i = i + 3;
      }
      if (i < chunkEnd) {
        const remain: number = chunkEnd - i;
        if (remain === 1) {
          const b0: number = bytes[i];
          piece = piece +
            table[b0 >> 2] +
            table[(b0 & 0x03) << 4] +
            '==';
        } else if (remain === 2) {
          const b0: number = bytes[i];
          const b1: number = bytes[i + 1];
          piece = piece +
            table[b0 >> 2] +
            table[((b0 & 0x03) << 4) | (b1 >> 4)] +
            table[(b1 & 0x0f) << 2] +
            '=';
        }
      }
      output = output + piece;
    }
    return output;
  }

  /**
   * base64 解码：base64 字符串 → Uint8Array
   */
  static base64Decode(base64: string): Uint8Array {
    const lookup: Uint8Array = new Uint8Array(256);
    for (let k: number = 0; k < 256; k++) {
      lookup[k] = 0xFF;
    }
    const table: string =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    for (let k: number = 0; k < table.length; k++) {
      lookup[table.charCodeAt(k)] = k;
    }

    const src: string = base64;
    const srcLen: number = src.length;
    let maxOut: number = Math.floor(srcLen * 3 / 4) + 3;
    const out: Uint8Array = new Uint8Array(maxOut);
    let outIdx: number = 0;
    let buffer: number = 0;
    let bufferBits: number = 0;

    for (let i: number = 0; i < srcLen; i++) {
      const ch: number = src.charCodeAt(i);
      if (ch === 0x3D) continue; // '='
      if (ch <= 0x20 || ch === 0x09 || ch === 0x0A || ch === 0x0D) continue;
      if (ch >= 256) continue;
      const v: number = lookup[ch];
      if (v === 0xFF) continue;
      buffer = (buffer << 6) | v;
      bufferBits = bufferBits + 6;
      if (bufferBits >= 8) {
        bufferBits = bufferBits - 8;
        out[outIdx++] = (buffer >> bufferBits) & 0xFF;
      }
    }
    if (outIdx === out.length) {
      return out;
    }
    const trimmed: Uint8Array = new Uint8Array(outIdx);
    for (let k: number = 0; k < outIdx; k++) {
      trimmed[k] = out[k];
    }
    return trimmed;
  }

  /**
   * base64 → 沙箱临时文件 → PixelMap
   * 返回 SizedPixelMap（含宽高），便于调用方按比例自适应显示
   */
  static async base64ToPixelMap(ctx: common.Context | null, base64: string): Promise<SizedPixelMap> {
    const bytes: Uint8Array = ImageCompressionService.base64Decode(base64);

    const tempPath: string = ImageCompressionService.getSandboxPath(
      ctx, 'tmp_display_' + Date.now() + '.webp'
    );
    {
      const f: fs.File = fs.openSync(tempPath, fs.OpenMode.CREATE | fs.OpenMode.WRITE_ONLY);
      fs.writeSync(f.fd, bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.length));
      fs.closeSync(f);
    }

    const source: image.ImageSource = image.createImageSource(tempPath);
    let imgWidth: number = 0;
    let imgHeight: number = 0;
    try {
      const info: image.ImageInfo = await new Promise<image.ImageInfo>((resolve, reject) => {
        source.getImageInfo(0, (err: Error | null, data: image.ImageInfo) => {
          if (err) reject(err); else resolve(data);
        });
      });
      imgWidth = info.size.width;
      imgHeight = info.size.height;
    } catch (infoErr) {
      console.error('ImageCompressionService: 读取图片尺寸失败，降级为 1:1');
    }
    const pixelMap: image.PixelMap = await source.createPixelMap();
    try { source.release(); } catch (ignore) {}
    try { fs.unlinkSync(tempPath); } catch (ignore) {}

    if (imgWidth <= 0) { imgWidth = 1; }
    if (imgHeight <= 0) { imgHeight = imgWidth; }
    const result: SizedPixelMap = {
      pixelMap: pixelMap,
      width: imgWidth,
      height: imgHeight
    };
    return result;
  }

  // ----------------------------------------------------------------------
  // 图片上传主流程
  // ----------------------------------------------------------------------

  async pickAndCompressToWebP(): Promise<string> {
    const MAX_BYTES: number = 25 * 1024;

    // 1. 选择图片
    let photoUris: string[] = [];
    try {
      const photoPicker: picker.PhotoViewPicker = new picker.PhotoViewPicker();
      const photoSelectOptions: picker.PhotoSelectOptions = new picker.PhotoSelectOptions();
      photoSelectOptions.MIMEType = picker.PhotoViewMIMETypes.IMAGE_TYPE;
      photoSelectOptions.maxSelectNumber = 1;
      const resultObj: picker.PhotoSelectResult = await photoPicker.select(photoSelectOptions);
      photoUris = resultObj.photoUris;
    } catch (err) {
      console.error('ImageCompressionService: PhotoViewPicker.select 失败: ' + JSON.stringify(err));
      promptAction.showToast({ message: '未选择图片', duration: 1500 });
      return '';
    }
    if (photoUris.length === 0) {
      console.warn('ImageCompressionService: photoUris 为空');
      promptAction.showToast({ message: '未选择图片', duration: 1500 });
      return '';
    }

    const imageUri: string = photoUris[0];
    console.info('ImageCompressionService: 选中 URI=' + imageUri);

    // 2. 把文件读取到 ArrayBuffer
    const fileBuffer: ArrayBuffer = this.readFileToBuffer(imageUri);
    if (fileBuffer.byteLength === 0) {
      console.error('ImageCompressionService: 文件为空');
      promptAction.showToast({ message: '图片读取失败', duration: 1500 });
      return '';
    }
    console.info('ImageCompressionService: 原始文件大小=' + fileBuffer.byteLength + 'B');

    // 3. 写入沙箱目录，拿到绝对路径
    const sandboxPath: string = this.writeBufferToSandbox(fileBuffer, 'tmpimg_' + Date.now() + '.jpg');
    if (sandboxPath.length === 0) {
      console.error('ImageCompressionService: 写入沙箱失败');
      promptAction.showToast({ message: '图片处理失败', duration: 1500 });
      return '';
    }
    console.info('ImageCompressionService: 沙箱路径=' + sandboxPath);

    // 4. 压缩为 WebP（路径字符串创建 ImageSource）
    const webpBuffer: ArrayBuffer = await this.compressPathToWebP(sandboxPath, MAX_BYTES);

    try { fs.unlinkSync(sandboxPath); } catch (ignore) {}

    if (webpBuffer.byteLength === 0) {
      console.error('ImageCompressionService: 压缩返回空 buffer');
      promptAction.showToast({ message: '图片压缩失败', duration: 1500 });
      return '';
    }

    // 5. base64 编码 —— 使用正确的 3→4 查表实现
    const base64: string = ImageCompressionService.base64Encode(webpBuffer);
    console.info('ImageCompressionService: 完成，WebP=' + webpBuffer.byteLength +
      'B, base64_len=' + base64.length);

    if (webpBuffer.byteLength > MAX_BYTES) {
      promptAction.showToast({
        message: '图片已添加（约 ' + Math.round(webpBuffer.byteLength / 1024) + 'KB）',
        duration: 1500
      });
    } else {
      promptAction.showToast({ message: '图片已添加', duration: 1500 });
    }
    return base64;
  }

  private readFileToBuffer(uri: string): ArrayBuffer {
    let path: string = uri;
    if (path.startsWith('file://')) {
      path = path.substring('file://'.length);
    }

    let fileObj: fs.File | null = null;
    let fd: number = -1;

    try {
      fileObj = fs.openSync(path, fs.OpenMode.READ_ONLY);
      fd = fileObj.fd;
      console.info('ImageCompressionService: fs.openSync(去前缀) 成功, fd=' + fd);
    } catch (err1) {
      console.warn('ImageCompressionService: 策略1 失败: ' + JSON.stringify(err1));
      try {
        fileObj = fs.openSync(uri, fs.OpenMode.READ_ONLY);
        fd = fileObj.fd;
        console.info('ImageCompressionService: fs.openSync(原始 URI) 成功, fd=' + fd);
      } catch (err2) {
        console.error('ImageCompressionService: 策略2 也失败: ' + JSON.stringify(err2));
        return new ArrayBuffer(0);
      }
    }

    let fileSize: number = 0;
    try {
      const statResult: fs.Stat = fs.statSync(fileObj.path);
      fileSize = statResult.size;
      console.info('ImageCompressionService: stat size=' + fileSize);
    } catch (err) {
      console.warn('ImageCompressionService: stat 失败: ' + JSON.stringify(err));
      fileSize = 4 * 1024 * 1024;
    }
    if (fileSize <= 0) {
      fileSize = 4 * 1024 * 1024;
    }

    const buf: ArrayBuffer = new ArrayBuffer(fileSize);
    const bytesRead: number = fs.readSync(fd, buf, { offset: 0, length: fileSize });
    console.info('ImageCompressionService: readSync bytesRead=' + bytesRead);

    try { fs.closeSync(fileObj); } catch (ignore) {}

    if (bytesRead <= 0) {
      return new ArrayBuffer(0);
    }
    if (bytesRead !== fileSize) {
      const result: ArrayBuffer = new ArrayBuffer(bytesRead);
      new Uint8Array(result).set(new Uint8Array(buf, 0, bytesRead));
      return result;
    }
    return buf;
  }

  private writeBufferToSandbox(buffer: ArrayBuffer, fileName: string): string {
    const filesDir: string = this.getFilesDir();
    const fullPath: string = filesDir + '/' + fileName;
    try {
      const f: fs.File = fs.openSync(fullPath, fs.OpenMode.CREATE | fs.OpenMode.WRITE_ONLY);
      fs.writeSync(f.fd, buffer);
      fs.closeSync(f);
      console.info('ImageCompressionService: 写入沙箱成功, path=' + fullPath +
        ', size=' + buffer.byteLength);
      return fullPath;
    } catch (err) {
      console.error('ImageCompressionService: 写入沙箱失败: ' + JSON.stringify(err));
      return '';
    }
  }

  private async compressPathToWebP(filePath: string, maxBytes: number): Promise<ArrayBuffer> {
    console.info('ImageCompressionService: compressPathToWebP, filePath=' + filePath);

    let source: image.ImageSource | null = null;
    try {
      source = image.createImageSource(filePath);
      console.info('ImageCompressionService: createImageSource(路径字符串) 成功');
    } catch (err) {
      console.error('ImageCompressionService: createImageSource 失败: ' + JSON.stringify(err));
      return new ArrayBuffer(0);
    }

    let originalWidth: number = 800;
    let originalHeight: number = 800;
    try {
      const info: image.ImageInfo = await source.getImageInfo();
      originalWidth = info.size.width;
      originalHeight = info.size.height;
      console.info('ImageCompressionService: 原图 W=' + originalWidth +
        ', H=' + originalHeight + ', pixelFormat=' + info.pixelFormat);
    } catch (err) {
      console.warn('ImageCompressionService: getImageInfo 失败: ' + JSON.stringify(err));
    }

    const widthSteps: number[] = [480, 360, 280, 200, 140, 100, 70];
    const qualitySteps: number[] = [80, 60, 45, 30, 20, 10];
    const formatList: string[] = ['image/webp'];

    let bestBuffer: ArrayBuffer = new ArrayBuffer(0);

    for (let wIdx: number = 0; wIdx < widthSteps.length; wIdx++) {
      const targetWidth: number = widthSteps[wIdx];
      let scale: number = 1.0;
      if (targetWidth < originalWidth) {
        scale = targetWidth / originalWidth;
      }
      const targetHeight: number = Math.max(1, Math.floor(originalHeight * scale));

      let pm: image.PixelMap | null = null;
      try {
        const decodeOpts: image.DecodingOptions = {
          desiredSize: { width: targetWidth, height: targetHeight }
        };
        pm = await source.createPixelMap(decodeOpts);
        console.info('ImageCompressionService: createPixelMap desiredSize 成功, size=' +
          targetWidth + 'x' + targetHeight);
      } catch (err1) {
        console.warn('ImageCompressionService: desiredSize 解码失败: ' + JSON.stringify(err1));
        try {
          pm = await source.createPixelMap();
        } catch (err2) {
          console.error('ImageCompressionService: 原始尺寸解码也失败: ' + JSON.stringify(err2));
          continue;
        }
      }

      for (let qIdx: number = 0; qIdx < qualitySteps.length; qIdx++) {
        const quality: number = qualitySteps[qIdx];
        for (let fIdx: number = 0; fIdx < formatList.length; fIdx++) {
          const fmt: string = formatList[fIdx];
          let packer: image.ImagePacker | null = null;
          let data: ArrayBuffer = new ArrayBuffer(0);
          try {
            packer = image.createImagePacker();
            const packOpts: image.PackingOption = { format: fmt, quality: quality };
            data = await packer.packing(pm, packOpts);
          } catch (packErr) {
            console.warn('ImageCompressionService: packing 失败, format=' + fmt +
              ', quality=' + quality + ': ' + JSON.stringify(packErr));
            if (packer !== null) {
              try { packer.release(); } catch (ignore) {}
            }
            continue;
          }
          if (packer !== null) {
            try { packer.release(); } catch (ignore) {}
          }

          console.info('ImageCompressionService: [OK] size=' + targetWidth + 'x' + targetHeight +
            ', quality=' + quality + ', format=' + fmt + ', bytes=' + data.byteLength);

          if (data.byteLength <= 0) {
            continue;
          }
          if (data.byteLength <= maxBytes) {
            bestBuffer = data;
            if (pm !== null) { try { pm.release(); } catch (ignore) {} }
            try { source.release(); } catch (ignore) {}
            console.info('ImageCompressionService: 命中目标，返回 ' + data.byteLength + 'B');
            return bestBuffer;
          }
          if (bestBuffer.byteLength === 0 || data.byteLength < bestBuffer.byteLength) {
            bestBuffer = data;
          }
        }
      }

      if (pm !== null) { try { pm.release(); } catch (ignore) {} }
    }

    try { source.release(); } catch (ignore) {}

    if (bestBuffer.byteLength === 0) {
      console.error('ImageCompressionService: 所有压缩组合都失败');
    } else {
      console.info('ImageCompressionService: 未命中 ' + maxBytes +
        'B，兜底使用 ' + bestBuffer.byteLength + 'B');
    }
    return bestBuffer;
  }
}

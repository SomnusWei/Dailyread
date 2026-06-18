import http from '@ohos.net.http';
import { BusinessError } from '@kit.BasicServicesKit';

export class WebDavResult<T> {
  success: boolean;
  data: T | null;
  message: string;
  code: number;

  constructor(success: boolean, data: T | null, message: string, code: number) {
    this.success = success;
    this.data = data;
    this.message = message;
    this.code = code;
  }

  static buildSuccess<T>(data: T): WebDavResult<T> {
    return new WebDavResult<T>(true, data, '', 0);
  }

  static buildError<T>(message: string, code: number): WebDavResult<T> {
    return new WebDavResult<T>(false, null, message, code);
  }
}

/** 用于 doRequest 的返回类型（显式类，避免裸对象字面量） */
class HttpRequestResult {
  responseCode: number;
  result: string;

  constructor(responseCode: number, result: string) {
    this.responseCode = responseCode;
    this.result = result;
  }
}

/** 用于在 401 后记录 Digest 挑战信息（realm/nonce/qop 等） */
class DigestChallenge {
  realm: string = '';
  nonce: string = '';
  qop: string = '';
  algorithm: string = 'MD5';
  opaque: string = '';
  isValid: boolean = false;
}

/** 一个纯位运算实现的标准 MD5（RFC 1321），仅使用 Number 和位运算，ArkTS 完全兼容 */
class MD5Util {
  private static readonly S: number[] = [
    7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
    5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
    4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
    6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21
  ];

  private static readonly K: number[] = [
    0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
    0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
    0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
    0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
    0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
    0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
    0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
    0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
    0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
    0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
    0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
    0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
    0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
    0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
    0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
  ];

  private static u32(x: number): number {
    return x & 0xFFFFFFFF;
  }

  /** 把一个 32 位无符号整数按小端 hex 化（8 位 hex） */
  private static u32ToHex(v: number): string {
    const u: number = MD5Util.u32(v);
    let s: string = '';
    for (let k: number = 0; k < 4; k++) {
      const byteVal: number = (u >>> (k * 8)) & 0xFF;
      const h: string = byteVal.toString(16);
      s = s + (byteVal < 16 ? '0' + h : h);
    }
    return s;
  }

  static stringToUtf8Bytes(s: string): number[] {
    const out: number[] = [];
    for (let i: number = 0; i < s.length; i++) {
      let code: number = s.charCodeAt(i);
      if (code < 0x80) {
        out.push(code);
      } else if (code < 0x800) {
        out.push(0xC0 | (code >>> 6));
        out.push(0x80 | (code & 0x3F));
      } else if (code < 0xD800 || code >= 0xE000) {
        out.push(0xE0 | (code >>> 12));
        out.push(0x80 | ((code >>> 6) & 0x3F));
        out.push(0x80 | (code & 0x3F));
      } else {
        i++;
        const hi: number = code;
        const lo: number = s.charCodeAt(i);
        const codePoint: number = 0x10000 + ((hi - 0xD800) << 10) + (lo - 0xDC00);
        out.push(0xF0 | (codePoint >>> 18));
        out.push(0x80 | ((codePoint >>> 12) & 0x3F));
        out.push(0x80 | ((codePoint >>> 6) & 0x3F));
        out.push(0x80 | (codePoint & 0x3F));
      }
    }
    return out;
  }

  static hashBytes(bytes: number[]): string {
    const originalLen: number = bytes.length;
    const bitLenLow: number = (originalLen * 8) & 0xFFFFFFFF;
    const bitLenHigh: number = Math.floor(originalLen / 0x20000000);
    const msg: number[] = bytes.slice(0, originalLen);
    msg.push(0x80);
    while ((msg.length % 64) !== 56) {
      msg.push(0);
    }
    msg.push(bitLenLow & 0xFF);
    msg.push((bitLenLow >>> 8) & 0xFF);
    msg.push((bitLenLow >>> 16) & 0xFF);
    msg.push((bitLenLow >>> 24) & 0xFF);
    msg.push(bitLenHigh & 0xFF);
    msg.push((bitLenHigh >>> 8) & 0xFF);
    msg.push((bitLenHigh >>> 16) & 0xFF);
    msg.push((bitLenHigh >>> 24) & 0xFF);

    let a0: number = 0x67452301;
    let b0: number = 0xefcdab89;
    let c0: number = 0x98badcfe;
    let d0: number = 0x10325476;

    for (let chunk: number = 0; chunk < msg.length; chunk += 64) {
      const M: number[] = new Array(16);
      for (let j: number = 0; j < 16; j++) {
        const idx: number = chunk + j * 4;
        const word: number = (msg[idx] | (msg[idx + 1] << 8) | (msg[idx + 2] << 16) | (msg[idx + 3] << 24));
        M[j] = MD5Util.u32(word);
      }

      let A: number = a0;
      let B: number = b0;
      let C: number = c0;
      let D: number = d0;

      for (let i: number = 0; i < 64; i++) {
        let F: number = 0;
        let g: number = 0;
        if (i < 16) {
          F = (B & C) | ((~B) & D);
          g = i;
        } else if (i < 32) {
          F = (D & B) | ((~D) & C);
          g = (5 * i + 1) % 16;
        } else if (i < 48) {
          F = B ^ C ^ D;
          g = (3 * i + 5) % 16;
        } else {
          F = C ^ (B | (~D));
          g = (7 * i) % 16;
        }
        const fInt: number = MD5Util.u32(F + A + MD5Util.K[i] + M[g]);
        A = D;
        D = C;
        C = B;
        const shifted: number = MD5Util.u32((fInt << MD5Util.S[i]) | (fInt >>> (32 - MD5Util.S[i])));
        B = MD5Util.u32(B + shifted);
      }

      a0 = MD5Util.u32(a0 + A);
      b0 = MD5Util.u32(b0 + B);
      c0 = MD5Util.u32(c0 + C);
      d0 = MD5Util.u32(d0 + D);
    }

    return (MD5Util.u32ToHex(a0) + MD5Util.u32ToHex(b0) + MD5Util.u32ToHex(c0) + MD5Util.u32ToHex(d0)).toLowerCase();
  }

  static hashString(s: string): string {
    return MD5Util.hashBytes(MD5Util.stringToUtf8Bytes(s));
  }
}

export class WebDavClient {
  private static instance: WebDavClient | null = null;
  private httpRequest: http.HttpRequest | null = null;
  private static readonly METHOD_PROPFIND: http.RequestMethod = 'PROPFIND' as http.RequestMethod;
  private static readonly METHOD_MKCOL: http.RequestMethod = 'MKCOL' as http.RequestMethod;
  private static readonly METHOD_PUT: http.RequestMethod = http.RequestMethod.PUT;
  private static readonly METHOD_GET: http.RequestMethod = http.RequestMethod.GET;
  private static readonly BASE64_CHARS: string =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

  private ncCounter: number = 0;

  /**
   * 安全地把 HTTP 响应体转换为 string。
   * 不同 SDK 版本的 result 可能是 string / Uint8Array / ArrayBuffer / Object。
   */
  private safeResultToString(raw: Object): string {
    if (raw === null || raw === undefined) {
      console.info('WebDAV safeResultToString: raw is null/undefined');
      return '';
    }
    if (typeof raw === 'string') {
      console.info('WebDAV safeResultToString: raw is string, length=' + (raw as string).length);
      return raw as string;
    }
    
    console.info('WebDAV safeResultToString: raw type=' + typeof raw);
    
    // 处理 Uint8Array 或 ArrayBuffer（HarmonyOS HTTP 响应常见格式）
    let u8: Uint8Array | null = null;
    
    // 尝试获取 Uint8Array
    try {
      const buffer: ArrayBuffer = raw as ArrayBuffer;
      if (buffer.byteLength !== undefined && buffer.byteLength > 0) {
        u8 = new Uint8Array(buffer);
        console.info('WebDAV safeResultToString: got ArrayBuffer, byteLength=' + buffer.byteLength);
      }
    } catch (e) {
      console.warn('WebDAV safeResultToString: not ArrayBuffer');
    }
    
    // 如果不是 ArrayBuffer，尝试直接作为 Uint8Array
    if (!u8) {
      try {
        const tempU8: Uint8Array = raw as Uint8Array;
        if (tempU8.length !== undefined && tempU8.length > 0) {
          u8 = tempU8;
          console.info('WebDAV safeResultToString: got Uint8Array, length=' + tempU8.length);
        }
      } catch (e) {
        console.warn('WebDAV safeResultToString: not Uint8Array');
      }
    }
    
    if (u8 && u8.length > 0) {
      // 正确的 UTF-8 解码（处理多字节字符）
      let result: string = '';
      let i: number = 0;
      while (i < u8.length) {
        const byte: number = u8[i] & 0xFF;
        
        if (byte < 0x80) {
          // 单字节 ASCII
          result += String.fromCharCode(byte);
          i++;
        } else if (byte >= 0xC0 && byte < 0xE0 && i + 1 < u8.length) {
          // 双字节 UTF-8
          const byte2: number = u8[i + 1] & 0xFF;
          const codePoint: number = ((byte & 0x1F) << 6) | (byte2 & 0x3F);
          result += String.fromCharCode(codePoint);
          i += 2;
        } else if (byte >= 0xE0 && byte < 0xF0 && i + 2 < u8.length) {
          // 三字节 UTF-8（中文常用）
          const byte2: number = u8[i + 1] & 0xFF;
          const byte3: number = u8[i + 2] & 0xFF;
          const codePoint: number = ((byte & 0x0F) << 12) | ((byte2 & 0x3F) << 6) | (byte3 & 0x3F);
          result += String.fromCharCode(codePoint);
          i += 3;
        } else if (byte >= 0xF0 && byte < 0xF8 && i + 3 < u8.length) {
          // 四字节 UTF-8
          const byte2: number = u8[i + 1] & 0xFF;
          const byte3: number = u8[i + 2] & 0xFF;
          const byte4: number = u8[i + 3] & 0xFF;
          const codePoint: number = ((byte & 0x07) << 18) | ((byte2 & 0x3F) << 12) | 
                                   ((byte3 & 0x3F) << 6) | (byte4 & 0x3F);
          // 处理代理对
          if (codePoint > 0xFFFF) {
            const surrogate: number = codePoint - 0x10000;
            result += String.fromCharCode(0xD800 + (surrogate >> 10));
            result += String.fromCharCode(0xDC00 + (surrogate & 0x3FF));
          } else {
            result += String.fromCharCode(codePoint);
          }
          i += 4;
        } else {
          // 无效字节，跳过
          i++;
        }
      }
      console.info('WebDAV safeResultToString: UTF-8 decoded, result length=' + result.length);
      return result;
    }
    
    // 兜底：尝试其他方式
    try {
      const str: string = JSON.stringify(raw);
      console.info('WebDAV safeResultToString: using JSON.stringify, length=' + str.length);
      return str;
    } catch (e2) {
      const str: string = String(raw);
      console.info('WebDAV safeResultToString: using String(), length=' + str.length);
      return str;
    }
  }

  private truncate(s: string, maxLen: number): string {
    if (!s) return '';
    if (s.length <= maxLen) return s;
    return s.substring(0, maxLen) + '...(total=' + s.length.toString() + ')';
  }

  static getInstance(): WebDavClient {
    if (!WebDavClient.instance) {
      WebDavClient.instance = new WebDavClient();
    }
    return WebDavClient.instance;
  }

  private createRequest(): http.HttpRequest {
    if (this.httpRequest) {
      try {
        this.httpRequest.destroy();
      } catch (e) {
        console.error('destroy request error:', JSON.stringify(e));
      }
    }
    this.httpRequest = http.createHttp();
    return this.httpRequest;
  }

  private basicAuthHeader(username: string, password: string): string {
    const credentials: string = username + ':' + password;
    return 'Basic ' + this.base64Encode(credentials);
  }

  private base64Encode(inputStr: string): string {
    const bytes: number[] = MD5Util.stringToUtf8Bytes(inputStr);
    let result: string = '';
    let i: number = 0;
    while (i < bytes.length) {
      const c1: number = bytes[i++];
      const c2: number = i < bytes.length ? bytes[i++] : 0;
      const c3: number = i < bytes.length ? bytes[i++] : 0;
      const triplet: number = (c1 << 16) | (c2 << 8) | c3;
      result += WebDavClient.BASE64_CHARS.charAt((triplet >> 18) & 0x3F);
      result += WebDavClient.BASE64_CHARS.charAt((triplet >> 12) & 0x3F);
      result += i > bytes.length + 1 ? '=' : WebDavClient.BASE64_CHARS.charAt((triplet >> 6) & 0x3F);
      result += i > bytes.length ? '=' : WebDavClient.BASE64_CHARS.charAt(triplet & 0x3F);
    }
    return result;
  }

  private parseWwwAuthenticate(headerValue: string): DigestChallenge {
    const result: DigestChallenge = new DigestChallenge();
    if (!headerValue) {
      return result;
    }

    let digestBlock: string = '';
    const digestIdx: number = headerValue.toLowerCase().indexOf('digest');
    if (digestIdx >= 0) {
      digestBlock = headerValue.substring(digestIdx + 6);
    } else {
      digestBlock = headerValue;
    }

    const re: RegExp = /([a-zA-Z0-9_-]+)=(?:"([^"]*)"|([^,\s]+))/g;
    let m: RegExpExecArray | null = re.exec(digestBlock);
    while (m !== null) {
      const key: string = m[1].toLowerCase();
      const val: string = (m[2] !== undefined) ? m[2] : (m[3] || '');
      if (key === 'realm') result.realm = val;
      else if (key === 'nonce') result.nonce = val;
      else if (key === 'qop') result.qop = val;
      else if (key === 'algorithm') result.algorithm = val;
      else if (key === 'opaque') result.opaque = val;
      m = re.exec(digestBlock);
    }

    result.isValid = result.realm !== '' && result.nonce !== '';
    return result;
  }

  private generateCnonce(): string {
    const chars: string = 'abcdef0123456789';
    let out: string = '';
    for (let i: number = 0; i < 8; i++) {
      out += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return out;
  }

  private computeDigestHeader(challenge: DigestChallenge,
                              username: string, password: string,
                              method: string, uri: string): string {
    const qopAuth: boolean = challenge.qop.indexOf('auth') >= 0;
    const cnonce: string = this.generateCnonce();
    this.ncCounter = this.ncCounter + 1;
    const ncNum: number = this.ncCounter;
    let ncStr: string = ncNum.toString(16);
    while (ncStr.length < 8) {
      ncStr = '0' + ncStr;
    }

    const ha1: string = MD5Util.hashString(username + ':' + challenge.realm + ':' + password);
    const ha2: string = MD5Util.hashString(method + ':' + uri);

    let response: string = '';
    if (qopAuth && challenge.qop.length > 0) {
      response = MD5Util.hashString(
        ha1 + ':' + challenge.nonce + ':' + ncStr + ':' + cnonce + ':auth:' + ha2);
    } else {
      response = MD5Util.hashString(ha1 + ':' + challenge.nonce + ':' + ha2);
    }

    let headerStr: string = 'Digest username="' + username + '"';
    headerStr = headerStr + ', realm="' + challenge.realm + '"';
    headerStr = headerStr + ', nonce="' + challenge.nonce + '"';
    headerStr = headerStr + ', uri="' + uri + '"';
    headerStr = headerStr + ', response="' + response + '"';
    if (challenge.opaque !== '') {
      headerStr = headerStr + ', opaque="' + challenge.opaque + '"';
    }
    headerStr = headerStr + ', algorithm=' + challenge.algorithm;
    if (qopAuth && challenge.qop.length > 0) {
      headerStr = headerStr + ', qop="auth"';
      headerStr = headerStr + ', nc=' + ncStr;
      headerStr = headerStr + ', cnonce="' + cnonce + '"';
    }
    return headerStr;
  }

  private buildUrl(serverUrl: string, remotePath: string): string {
    const baseUrl: string = serverUrl.endsWith('/') ? serverUrl.slice(0, -1) : serverUrl;
    const cleanPath: string = remotePath.startsWith('/') ? remotePath : '/' + remotePath;
    return baseUrl + cleanPath;
  }

  /** 从响应对象中尝试读取指定 header（兼容不同 API 版本） */
  private readHeaderFromObject(respObj: Object, headerKey: string): string {
    if (!respObj) return '';
    const obj: Record<string, Object> = respObj as Record<string, Object>;
    const candidates: string[] = ['header', 'headers', 'responseHeader'];
    for (let i: number = 0; i < candidates.length; i++) {
      const h: Object | undefined = obj[candidates[i]];
      if (h) {
        const anyH: Record<string, Object> = h as Record<string, Object>;
        const keys: string[] = Object.keys(anyH);
        for (let j: number = 0; j < keys.length; j++) {
          const k: string = keys[j];
          if (k.toLowerCase() === headerKey.toLowerCase()) {
            const val: Object = anyH[k];
            if (typeof val === 'string') {
              return val as string;
            } else if (Array.isArray(val)) {
              const arr: string[] = val as string[];
              if (arr.length > 0) return arr[0];
            }
          }
        }
      }
    }
    return '';
  }

  private buildHeaderMap(headerKey: string, headerValue: string,
                         extraHeaders: Record<string, string>): Record<string, string> {
    const out: Record<string, string> = {};
    const keys: string[] = Object.keys(extraHeaders);
    for (let k: number = 0; k < keys.length; k++) {
      out[keys[k]] = extraHeaders[keys[k]];
    }
    out[headerKey] = headerValue;
    return out;
  }

  /**
   * 通用 HTTP 请求封装：
   * - 先尝试 Basic Auth（兼容老服务器）
   * - 若返回 401 且能读到 WWW-Authenticate 头，自动切换为 Digest 再发一次
   */
  private async doRequest(fullUrl: string, method: http.RequestMethod,
                          headers: Record<string, string>, body: string,
                          username: string, password: string,
                          timeout: number): Promise<HttpRequestResult> {
    const uri: string = fullUrl;
    const methodStr: string = String(method);
    console.info('WebDAV doRequest: ' + methodStr + ' ' + uri + ' (auth=' + (username !== '' ? 'yes' : 'no') + ')');

    // 第 1 次尝试：Basic Authorization
    let firstHeaders: Record<string, string> = {};
    const keys1: string[] = Object.keys(headers);
    for (let k: number = 0; k < keys1.length; k++) {
      firstHeaders[keys1[k]] = headers[keys1[k]];
    }
    if (username !== '') {
      firstHeaders = this.buildHeaderMap('Authorization', this.basicAuthHeader(username, password), firstHeaders);
    }

    let responseCode: number = 0;
    let responseBody: string = '';
    let firstResp: Object | null = null;

    const req1: http.HttpRequest = this.createRequest();
    try {
      const resp1 = await req1.request(uri, {
        method: method,
        header: firstHeaders,
        extraData: body,
        connectTimeout: timeout,
        readTimeout: timeout
      });
      responseCode = resp1.responseCode as number;
      responseBody = this.safeResultToString(resp1.result as Object);
      firstResp = resp1;
      console.info('WebDAV first response: code=' + responseCode + ', bodyHead=' + this.truncate(responseBody, 200));
    } catch (e) {
      const error: BusinessError = e as BusinessError;
      console.error('WebDAV first request error: ' + error.message);
      return new HttpRequestResult(-1, error.message);
    }

    // 401：尝试 Digest
    if (responseCode === 401 && username !== '') {
      console.info('WebDAV: 收到 401，尝试 Digest 认证');
      let wwwAuth: string = '';
      if (firstResp !== null) {
        wwwAuth = this.readHeaderFromObject(firstResp, 'www-authenticate');
        if (wwwAuth === '') {
          wwwAuth = this.readHeaderFromObject(firstResp, 'WWW-Authenticate');
        }
      }
      console.info('WebDAV WWW-Authenticate: ' + this.truncate(wwwAuth, 300));

      if (wwwAuth === '') {
        console.warn('WebDAV: 401 响应中未找到 WWW-Authenticate 头，无法使用 Digest');
        return new HttpRequestResult(responseCode, responseBody);
      }

      const challenge: DigestChallenge = this.parseWwwAuthenticate(wwwAuth);
      if (!challenge.isValid) {
        console.warn('WebDAV: 无法解析 Digest 挑战: ' + wwwAuth);
        return new HttpRequestResult(responseCode, responseBody);
      }

      // 第 2 次尝试：Digest Authorization
      const digestAuth: string = this.computeDigestHeader(challenge, username, password, methodStr, uri);
      let secondHeaders: Record<string, string> = {};
      const keys2: string[] = Object.keys(headers);
      for (let k: number = 0; k < keys2.length; k++) {
        secondHeaders[keys2[k]] = headers[keys2[k]];
      }
      secondHeaders = this.buildHeaderMap('Authorization', digestAuth, secondHeaders);

      const req2: http.HttpRequest = this.createRequest();
      try {
        const resp2 = await req2.request(uri, {
          method: method,
          header: secondHeaders,
          extraData: body,
          connectTimeout: timeout,
          readTimeout: timeout
        });
        responseCode = resp2.responseCode as number;
        responseBody = this.safeResultToString(resp2.result as Object);
        console.info('WebDAV digest response: code=' + responseCode + ', bodyHead=' + this.truncate(responseBody, 200));
      } catch (e) {
        const error: BusinessError = e as BusinessError;
        console.error('WebDAV Digest retry error: ' + error.message);
        return new HttpRequestResult(-2, error.message);
      }
    }

    return new HttpRequestResult(responseCode, responseBody);
  }

  async testConnection(serverUrl: string, username: string, password: string,
                       remotePath: string): Promise<WebDavResult<boolean>> {
    try {
      const fullUrl: string = this.buildUrl(serverUrl, remotePath);
      const body: string =
        '<?xml version="1.0" encoding="utf-8"?><propfind xmlns="DAV:"><prop><resourcetype/></prop></propfind>';
      const headers: Record<string, string> = {};
      headers['Depth'] = '0';
      headers['Content-Type'] = 'application/xml';
      const r: HttpRequestResult = await this.doRequest(fullUrl, WebDavClient.METHOD_PROPFIND, headers, body,
        username, password, 30000);
      const code: number = r.responseCode;
      if (code === 200 || code === 207) {
        return WebDavResult.buildSuccess<boolean>(true);
      } else if (code === 404) {
        return await this.createDirectory(serverUrl, username, password, remotePath);
      } else if (code === 405) {
        const fallbackResult: WebDavResult<boolean> = await this.tryGET(serverUrl, username, password,
          remotePath + '/index.json');
        if (fallbackResult.success) {
          return WebDavResult.buildSuccess<boolean>(true);
        } else {
          return WebDavResult.buildError<boolean>('连接失败: ' + code.toString(), code);
        }
      } else {
        return WebDavResult.buildError<boolean>('连接失败: ' + code.toString(), code);
      }
    } catch (e) {
      const error: BusinessError = e as BusinessError;
      return WebDavResult.buildError<boolean>('连接错误: ' + error.message, error.code);
    }
  }

  async tryGET(serverUrl: string, username: string, password: string,
               remotePath: string): Promise<WebDavResult<boolean>> {
    try {
      const fullUrl: string = this.buildUrl(serverUrl, remotePath);
      const emptyHeaders: Record<string, string> = {};
      const r: HttpRequestResult = await this.doRequest(fullUrl, WebDavClient.METHOD_GET, emptyHeaders, '',
        username, password, 30000);
      const code: number = r.responseCode;
      if (code === 200 || code === 404) {
        return WebDavResult.buildSuccess<boolean>(true);
      } else {
        return WebDavResult.buildError<boolean>('GET 请求失败: ' + code.toString(), code);
      }
    } catch (e) {
      const error: BusinessError = e as BusinessError;
      return WebDavResult.buildError<boolean>('GET 请求错误: ' + error.message, error.code);
    }
  }

  async createDirectory(serverUrl: string, username: string, password: string,
                         remotePath: string): Promise<WebDavResult<boolean>> {
    try {
      const fullUrl: string = this.buildUrl(serverUrl, remotePath);
      const emptyHeaders: Record<string, string> = {};
      const r: HttpRequestResult = await this.doRequest(fullUrl, WebDavClient.METHOD_MKCOL, emptyHeaders, '',
        username, password, 30000);
      const code: number = r.responseCode;
      if (code === 200 || code === 201 || code === 405) {
        return WebDavResult.buildSuccess<boolean>(true);
      } else {
        return WebDavResult.buildError<boolean>('创建目录失败: ' + code.toString(), code);
      }
    } catch (e) {
      const error: BusinessError = e as BusinessError;
      return WebDavResult.buildError<boolean>('创建目录错误: ' + error.message, error.code);
    }
  }

  async uploadFile(serverUrl: string, username: string, password: string,
                   remotePath: string, content: string): Promise<WebDavResult<boolean>> {
    try {
      const fullUrl: string = this.buildUrl(serverUrl, remotePath);
      const headers: Record<string, string> = {};
      headers['Content-Type'] = 'application/json';
      const r: HttpRequestResult = await this.doRequest(fullUrl, WebDavClient.METHOD_PUT, headers, content,
        username, password, 60000);
      const code: number = r.responseCode;
      if (code === 200 || code === 201 || code === 204) {
        return WebDavResult.buildSuccess<boolean>(true);
      } else {
        return WebDavResult.buildError<boolean>('上传失败: ' + code.toString(), code);
      }
    } catch (e) {
      const error: BusinessError = e as BusinessError;
      return WebDavResult.buildError<boolean>('上传错误: ' + error.message, error.code);
    }
  }

  async downloadFile(serverUrl: string, username: string, password: string,
                     remotePath: string): Promise<WebDavResult<string>> {
    try {
      const fullUrl: string = this.buildUrl(serverUrl, remotePath);
      // 添加请求头：禁用压缩、指定接受类型、处理编码
      const headers: Record<string, string> = {};
      headers['Accept'] = 'application/json, text/plain, */*';
      headers['Accept-Encoding'] = 'identity';  // 禁用 gzip 压缩
      headers['Accept-Charset'] = 'UTF-8';
      
      const r: HttpRequestResult = await this.doRequest(fullUrl, WebDavClient.METHOD_GET, headers, '',
        username, password, 60000);
      const code: number = r.responseCode;
      if (code === 200) {
        // 尝试解码响应，处理可能的 BOM 和编码问题
        let content: string = r.result;
        console.info('WebDAV downloadFile: raw content length=' + content.length + ', first 100 chars=' + this.truncate(content, 100));
        
        if (content.length > 0) {
          // 移除 UTF-8 BOM
          if (content.charCodeAt(0) === 0xFEFF) {
            content = content.substring(1);
            console.info('WebDAV downloadFile: 已移除 BOM');
          }
          
          // 检测是否需要 URL 解码（坚果云可能返回 URL 编码的内容）
          if (content.includes('%')) {
            try {
              const decoded: string = decodeURIComponent(content);
              // 只有当解码后的内容长度发生变化或包含原本没有的字符时才使用解码结果
              if (decoded.length !== content.length || decoded.includes('\u4e00') || decoded.includes('\u9fff')) {
                content = decoded;
                console.info('WebDAV downloadFile: 已进行 URL 解码');
              }
            } catch (e) {
              console.warn('WebDAV downloadFile: URL 解码失败，保持原样');
            }
          }
        }
        
        return WebDavResult.buildSuccess<string>(content);
      } else if (code === 404) {
        return WebDavResult.buildSuccess<string>('');
      } else {
        return WebDavResult.buildError<string>('下载失败: ' + code.toString(), code);
      }
    } catch (e) {
      const error: BusinessError = e as BusinessError;
      return WebDavResult.buildError<string>('下载错误: ' + error.message, error.code);
    }
  }

  async getFileLastModified(serverUrl: string, username: string, password: string,
                            remotePath: string): Promise<WebDavResult<string>> {
    try {
      const fullUrl: string = this.buildUrl(serverUrl, remotePath);
      const body: string =
        '<?xml version="1.0" encoding="utf-8"?><propfind xmlns="DAV:"><prop><getlastmodified/></prop></propfind>';
      const headers: Record<string, string> = {};
      headers['Depth'] = '0';
      headers['Content-Type'] = 'application/xml';
      const r: HttpRequestResult = await this.doRequest(fullUrl, WebDavClient.METHOD_PROPFIND, headers, body,
        username, password, 30000);
      const code: number = r.responseCode;
      if (code === 200 || code === 207) {
        const lastMod: string = this.parseLastModified(r.result);
        return WebDavResult.buildSuccess<string>(lastMod);
      } else if (code === 404) {
        return WebDavResult.buildSuccess<string>('');
      } else {
        return WebDavResult.buildError<string>('获取文件信息失败: ' + code.toString(), code);
      }
    } catch (e) {
      const error: BusinessError = e as BusinessError;
      return WebDavResult.buildError<string>('获取文件信息错误: ' + error.message, error.code);
    }
  }

  private parseLastModified(xml: string): string {
    if (!xml) return '';
    const regex: RegExp = /<D:getlastmodified>([^<]+)<\/D:getlastmodified>/i;
    const match: RegExpExecArray | null = regex.exec(xml);
    if (match !== null) {
      return match[1];
    }
    const regex2: RegExp = /<d:getlastmodified>([^<]+)<\/d:getlastmodified>/i;
    const match2: RegExpExecArray | null = regex2.exec(xml);
    if (match2 !== null) {
      return match2[1];
    }
    const regex3: RegExp = /<getlastmodified>([^<]+)<\/getlastmodified>/i;
    const match3: RegExpExecArray | null = regex3.exec(xml);
    if (match3 !== null) {
      return match3[1];
    }
    return '';
  }

  destroy(): void {
    if (this.httpRequest) {
      try {
        this.httpRequest.destroy();
        this.httpRequest = null;
      } catch (e) {
        console.error('destroy error:', JSON.stringify(e));
      }
    }
  }
}

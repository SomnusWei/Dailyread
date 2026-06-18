import http.client

print("=== 尝试连接服务器 ===")
try:
    conn = http.client.HTTPConnection('47.95.205.216', 80, timeout=10)
    conn.request('GET', '/')
    response = conn.getresponse()
    print(f"HTTP 状态码: {response.status}")
    print(f"响应头: {response.getheaders()}")
    conn.close()
except Exception as e:
    print(f"HTTP 连接错误: {e}")

print("\n=== 检查可能的文件 ===")
files_to_check = ['/index.html', '/favicon.svg', '/manifest.webmanifest', '/registerSW.js']
for file_path in files_to_check:
    try:
        conn = http.client.HTTPConnection('47.95.205.216', 80, timeout=5)
        conn.request('HEAD', file_path)
        response = conn.getresponse()
        print(f"{file_path}: {response.status}")
        conn.close()
    except Exception as e:
        print(f"{file_path}: 错误 - {e}")

print("\n=== 检查 HTTPS ===")
try:
    import ssl
    conn = http.client.HTTPSConnection('47.95.205.216', 443, timeout=10, context=ssl._create_unverified_context())
    conn.request('GET', '/')
    response = conn.getresponse()
    print(f"HTTPS 状态码: {response.status}")
    conn.close()
except Exception as e:
    print(f"HTTPS 连接错误: {e}")

print("\n=== 检查域名 dailyread.sonnusww.top ===")
try:
    conn = http.client.HTTPConnection('dailyread.sonnusww.top', 80, timeout=10)
    conn.request('GET', '/')
    response = conn.getresponse()
    print(f"HTTP 状态码: {response.status}")
    conn.close()
except Exception as e:
    print(f"连接错误: {e}")

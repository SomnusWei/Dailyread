import subprocess
import os

# 使用 curl 来尝试更多操作
def run_remote_command(cmd):
    try:
        # 使用 expect-like 方法
        script = f"""
        spawn ssh root@47.95.205.216
        expect "password:"
        send "Somnus890930\\r"
        expect "#"
        send "{cmd}\\r"
        expect "#"
        send "exit\\r"
        """
        # 写入临时脚本
        with open('temp_ssh.exp', 'w') as f:
            f.write(script)
        
        # 尝试执行
        result = subprocess.run(['expect', 'temp_ssh.exp'], capture_output=True, text=True, timeout=30)
        print(result.stdout)
        print(result.stderr)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists('temp_ssh.exp'):
            os.remove('temp_ssh.exp')

# 直接使用 curl 检查 nginx 状态
print("=== 检查 nginx 状态 ===")
try:
    result = subprocess.run(
        ['curl', '-s', 'http://47.95.205.216/nginx_status'],
        capture_output=True, text=True, timeout=10
    )
    print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")
except Exception as e:
    print(f"curl 错误: {e}")

# 检查网站根目录
print("\n=== 尝试查找网站根目录 ===")
try:
    result = subprocess.run(
        ['curl', '-s', '-I', 'http://47.95.205.216'],
        capture_output=True, text=True, timeout=10
    )
    print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")
except Exception as e:
    print(f"curl 错误: {e}")

# 尝试查看默认的 nginx 配置
print("\n=== 尝试获取默认页面路径 ===")
try:
    # 使用 python 发起 HTTP 请求来获取更多信息
    import urllib.request
    response = urllib.request.urlopen('http://47.95.205.216', timeout=10)
    html = response.read().decode('utf-8', errors='replace')
    print("页面标题:", html.split('<title>')[1].split('</title>')[0] if '<title>' in html else '未知')
except Exception as e:
    print(f"HTTP 请求错误: {e}")

print("\n=== 尝试使用 ftp ===")
try:
    from ftplib import FTP
    ftp = FTP('47.95.205.216')
    ftp.login('root', 'Somnus890930')
    print("FTP 登录成功")
    ftp.cwd('/var/www')
    files = ftp.nlst()
    print("/var/www 目录内容:", files)
    ftp.quit()
except Exception as e:
    print(f"FTP 错误: {e}")

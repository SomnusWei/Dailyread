import pexpect
import time

def ssh_execute(host, username, password, command, timeout=30):
    try:
        ssh = pexpect.spawn(f'ssh {username}@{host}', timeout=timeout)
        ssh.expect('password:')
        ssh.sendline(password)
        
        # 等待登录成功
        index = ssh.expect(['#', 'password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        if index == 1:
            print("密码错误")
            ssh.close()
            return None
        elif index == 2 or index == 3:
            print("连接超时或失败")
            ssh.close()
            return None
        
        # 执行命令
        ssh.sendline(command)
        ssh.expect('#', timeout=timeout)
        
        # 获取输出（去除命令本身和提示符）
        output = ssh.before.decode('utf-8', errors='replace').strip()
        # 去除命令回显
        lines = output.split('\n')
        if lines and command in lines[0]:
            output = '\n'.join(lines[1:])
        
        ssh.close()
        return output
    except Exception as e:
        print(f"SSH 错误: {e}")
        return None

print("=== 连接服务器 ===")
host = '47.95.205.216'
username = 'root'
password = 'Somnus890930'

print("\n1. 查找 nginx 配置文件")
result = ssh_execute(host, username, password, 'find /etc/nginx -name "*.conf" -type f | xargs grep -l "dailyread\\|sonnusww" 2>/dev/null')
if result:
    print("找到的配置文件:")
    print(result)
else:
    print("未找到相关配置文件")

print("\n2. 查看默认 nginx 配置")
result = ssh_execute(host, username, password, 'cat /etc/nginx/sites-available/default 2>/dev/null || cat /etc/nginx/nginx.conf | head -100')
if result:
    print(result[:2000])

print("\n3. 查找网站根目录")
result = ssh_execute(host, username, password, 'ls -la /var/www/ 2>/dev/null')
if result:
    print(result)
else:
    print("/var/www 不存在")

print("\n4. 查找 html 目录")
result = ssh_execute(host, username, password, 'ls -la /usr/share/nginx/html/ 2>/dev/null')
if result:
    print(result)
else:
    print("/usr/share/nginx/html 不存在")

print("\n5. 查找所有包含 pwa 的目录")
result = ssh_execute(host, username, password, 'find / -type d -name "*pwa*" 2>/dev/null')
if result:
    print(result)
else:
    print("未找到 pwa 目录")

print("\n6. 查找所有包含 dailyread 的目录")
result = ssh_execute(host, username, password, 'find / -type d -name "*dailyread*" 2>/dev/null')
if result:
    print(result)
else:
    print("未找到 dailyread 目录")

print("\n=== 操作完成 ===")

import paramiko
import time

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 等待锁释放
print('等待apt锁释放...')
time.sleep(10)

# 杀死可能阻塞的进程
ssh.exec_command('pkill -9 apt-get || true')
time.sleep(2)

# 重新安装
print('=== 安装 Chromium ===')
stdin, stdout, stderr = ssh.exec_command('rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock 2>/dev/null; dpkg --configure -a; apt-get update && apt-get install -y chromium 2>&1')
output = stdout.read().decode()
error = stderr.read().decode()
print(output[-2000:] if len(output) > 2000 else output)
print(error[-1000:] if len(error) > 1000 else error)

# 检查 chromium
print('\n=== 检查 chromium ===')
stdin, stdout, stderr = ssh.exec_command('which chromium && chromium --version')
result = stdout.read().decode()
err = stderr.read().decode()
print(result or '未找到')
print(err or '')

ssh.close()

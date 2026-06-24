import paramiko
import time

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

print('等待Chromium安装完成...')

# 等待安装完成（最多等待5分钟）
for i in range(60):
    stdin, stdout, stderr = ssh.exec_command('ps aux | grep "apt-get install" | grep -v grep')
    result = stdout.read().decode().strip()
    if not result:
        print('安装完成！')
        break
    if i % 10 == 0:
        print(f'等待中... ({i*5}秒)')
    time.sleep(5)

# 检查chromium
print('\n=== 检查Chromium ===')
stdin, stdout, stderr = ssh.exec_command('which chromium && chromium --version')
result = stdout.read().decode()
err = stderr.read().decode()
print(result or '未找到')
print(err or '')

ssh.close()

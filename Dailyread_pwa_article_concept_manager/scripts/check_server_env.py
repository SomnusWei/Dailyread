import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查内存
print('=== 内存情况 ===')
stdin, stdout, stderr = ssh.exec_command('free -h')
print(stdout.read().decode())

# 检查磁盘空间
print('\n=== 磁盘空间 ===')
stdin, stdout, stderr = ssh.exec_command('df -h')
print(stdout.read().decode())

# 检查是否已安装Chrome/Puppeteer
print('\n=== 检查Chrome ===')
stdin, stdout, stderr = ssh.exec_command('which google-chrome chromium-browser chromium 2>/dev/null || echo "未安装"')
print(stdout.read().decode())

# 检查Node版本
print('\n=== Node版本 ===')
stdin, stdout, stderr = ssh.exec_command('node --version')
print(stdout.read().decode())

ssh.close()

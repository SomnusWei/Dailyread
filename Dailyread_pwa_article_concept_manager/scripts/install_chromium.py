import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 安装 Chromium
print('=== 安装 Chromium ===')
stdin, stdout, stderr = ssh.exec_command('apt-get install -y chromium 2>&1')
output = stdout.read().decode()
error = stderr.read().decode()
print(output)
print(error)

# 检查 chromium 是否安装
print('\n=== 检查 chromium ===')
stdin, stdout, stderr = ssh.exec_command('which chromium && chromium --version')
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()

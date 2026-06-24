import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查chromium
print('=== 检查Chromium ===')
stdin, stdout, stderr = ssh.exec_command('which chromium && chromium --version')
result = stdout.read().decode()
err = stderr.read().decode()
print(result or '未找到')
print(err or '')

# 检查内存
print('\n=== 内存情况 ===')
stdin, stdout, stderr = ssh.exec_command('free -h')
print(stdout.read().decode())

ssh.close()

import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查进程
print('=== 运行中的进程 ===')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "apt|dpkg" | grep -v grep')
print(stdout.read().decode())

# 检查锁
print('\n=== 检查锁 ===')
stdin, stdout, stderr = ssh.exec_command('ls -la /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock 2>&1')
print(stdout.read().decode())

ssh.close()

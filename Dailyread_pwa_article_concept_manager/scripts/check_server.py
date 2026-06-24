import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查 Nginx 状态
print('=== Nginx 状态 ===')
stdin, stdout, stderr = ssh.exec_command('systemctl status nginx --no-pager')
print(stdout.read().decode())

# 检查后端进程
print('\n=== 后端进程 ===')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep node | grep -v grep')
print(stdout.read().decode())

# 检查 Nginx 配置
print('\n=== Nginx 配置 ===')
stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/default')
print(stdout.read().decode())

ssh.close()

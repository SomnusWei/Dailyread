import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查后端日志
print('=== 后端日志 ===')
stdin, stdout, stderr = ssh.exec_command('tail -50 /var/log/dailyread.log')
print(stdout.read().decode())
print(stderr.read().decode())

# 检查 node_modules 是否存在
print('\n=== 检查 node_modules ===')
stdin, stdout, stderr = ssh.exec_command('ls -la /opt/dailyread-server/node_modules 2>/dev/null | head -5 || echo "node_modules 不存在"')
print(stdout.read().decode())

# 检查端口 3001 是否监听
print('\n=== 检查端口 3001 ===')
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp | grep 3001')
print(stdout.read().decode() or '端口 3001 未监听')

ssh.close()

import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查后端日志
print('=== 后端日志 ===')
stdin, stdout, stderr = ssh.exec_command('cat /var/log/dailyread.log')
print(stdout.read().decode())

# 检查数据库权限
print('\n=== 数据库目录 ===')
stdin, stdout, stderr = ssh.exec_command('ls -la /opt/dailyread-server/data/')
print(stdout.read().decode())

# 检查 CORS 配置
print('\n=== 检查后端 CORS ===')
stdin, stdout, stderr = ssh.exec_command('curl -v -X OPTIONS http://127.0.0.1:3001/api/auth/login -H "Origin: http://47.95.205.216" -H "Access-Control-Request-Method: POST" 2>&1 | head -30')
print(stdout.read().decode())

ssh.close()

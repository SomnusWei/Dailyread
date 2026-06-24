import paramiko
import time

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

print('=== 安装 wkhtmltopdf ===')

# 安装 wkhtmltopdf
stdin, stdout, stderr = ssh.exec_command('apt-get update && apt-get install -y wkhtmltopdf')
print(stdout.read().decode())
print(stderr.read().decode())

# 检查是否安装成功
stdin, stdout, stderr = ssh.exec_command('wkhtmltopdf --version')
print('\n=== wkhtmltopdf 版本 ===')
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()

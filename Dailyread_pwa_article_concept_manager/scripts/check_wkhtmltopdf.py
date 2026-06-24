import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查 wkhtmltopdf
print('=== 检查 wkhtmltopdf ===')
stdin, stdout, stderr = ssh.exec_command('which wkhtmltopdf && wkhtmltopdf --version')
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()

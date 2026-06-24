import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 检查xvfb
print('=== 检查xvfb ===')
stdin, stdout, stderr = ssh.exec_command('which xvfb-run')
print(stdout.read().decode())

# 安装xvfb
print('\n=== 安装xvfb ===')
stdin, stdout, stderr = ssh.exec_command('apt-get install -y xvfb 2>&1')
print(stdout.read().decode()[-1000:])
print(stderr.read().decode()[-500:])

# 测试xvfb-run + chromium
print('\n=== 测试xvfb-run + chromium ===')
cmd = 'xvfb-run --auto-servernum --server-args="-screen 0 1024x768x24" chromium --no-sandbox --disable-gpu --headless --print-to-pdf=/tmp/test.pdf --print-to-pdf-no-header https://www.baidu.com 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
err = stderr.read().decode()
print('STDOUT:', result)
print('STDERR:', err)

# 检查PDF
print('\n=== 检查PDF ===')
stdin, stdout, stderr = ssh.exec_command('ls -la /tmp/test.pdf 2>&1')
print(stdout.read().decode())

ssh.close()

import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

# 测试chromium生成PDF
print('=== 测试Chromium PDF生成 ===')
# 使用--no-sandbox和--disable-gpu来避免GPU问题
cmd = 'echo "<html><body><h1>Test</h1></body></html>" | chromium --no-sandbox --disable-gpu --headless --print-to-pdf=/tmp/test.pdf --print-to-pdf-no-header 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
err = stderr.read().decode()
print('STDOUT:', result)
print('STDERR:', err)

# 检查PDF是否生成
print('\n=== 检查PDF ===')
stdin, stdout, stderr = ssh.exec_command('ls -la /tmp/test.pdf 2>&1')
print(stdout.read().decode())

ssh.close()

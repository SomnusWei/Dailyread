import paramiko
import time

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

LOCAL_SERVER_DIR = r'e:\item\DailyRead\Dailyread_pwa_article_concept_manager\server'
LOCAL_DIST_DIR = r'e:\item\DailyRead\Dailyread_pwa_article_concept_manager\dist'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)

print('=== 重启后端服务 ===')

# 杀掉旧进程
print('停止旧后端进程...')
ssh.exec_command('pkill -f "node src/index.js" || true')
time.sleep(1)

# 上传后端代码
print('上传后端代码...')
sftp = ssh.open_sftp()

# 上传所有 server 目录下的文件
import os
for root, dirs, files in os.walk(LOCAL_SERVER_DIR):
    for file in files:
        local_path = os.path.join(root, file)
        relative_path = os.path.relpath(local_path, LOCAL_SERVER_DIR)
        remote_path = f'/opt/dailyread-server/{relative_path}'

        # 确保远程目录存在
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.stat(remote_dir)
        except:
            sftp.mkdir(remote_dir, recursive=True)

        sftp.put(local_path, remote_path)
        print(f'  上传 {local_path} -> {remote_path}')

sftp.close()

# 启动后端
print('启动后端...')
ssh.exec_command('cd /opt/dailyread-server && nohup node src/index.js > /var/log/dailyread.log 2>&1 &')
time.sleep(2)

# 检查后端是否启动
print('\n检查后端状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep node | grep -v grep')
print(stdout.read().decode())

# 重启 Nginx
print('\n重启 Nginx...')
ssh.exec_command('nginx -s reload')

# 检查 Nginx 状态
stdin, stdout, stderr = ssh.exec_command('systemctl status nginx --no-pager | head -15')
print(stdout.read().decode())

print('\n部署完成！')

ssh.close()

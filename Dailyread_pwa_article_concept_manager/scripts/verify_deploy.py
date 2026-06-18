import paramiko

def verify_deploy():
    hostname = '47.95.205.216'
    port = 22
    username = 'root'
    password = 'Somnus890930'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=10)
        
        print("=== 验证文件上传 ===")
        stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/html/')
        print(stdout.read().decode())
        
        print("\n=== 检查子目录 ===")
        stdin, stdout, stderr = ssh.exec_command('find /var/www/html -type f | head -30')
        print(stdout.read().decode())
        
        print("\n=== 检查 index.html 内容 ===")
        stdin, stdout, stderr = ssh.exec_command('cat /var/www/html/index.html | head -30')
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_deploy()

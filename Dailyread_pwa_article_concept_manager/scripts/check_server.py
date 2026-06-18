import paramiko

def check_server_config():
    hostname = '47.95.205.216'
    port = 22
    username = 'root'
    password = 'Somnus890930'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=10)
        
        print("=== 检查 Nginx 配置 ===")
        stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/nginx.conf')
        print(stdout.read().decode()[:1000])
        
        print("\n=== 检查 sites-enabled ===")
        stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/sites-enabled/')
        print(stdout.read().decode())
        
        print("\n=== 检查默认站点配置 ===")
        stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-enabled/default')
        print(stdout.read().decode())
        
        print("\n=== 检查文件权限 ===")
        stdin, stdout, stderr = ssh.exec_command('ls -la /usr/share/nginx/html/')
        print(stdout.read().decode())
        
        print("\n=== 检查目录结构 ===")
        stdin, stdout, stderr = ssh.exec_command('find /usr/share/nginx/html -type f | head -20')
        print(stdout.read().decode())
        
        print("\n=== 检查 Nginx 错误日志 ===")
        stdin, stdout, stderr = ssh.exec_command('tail -20 /var/log/nginx/error.log')
        print(stdout.read().decode())
        
        print("\n=== 检查 SELinux 状态 ===")
        stdin, stdout, stderr = ssh.exec_command('getenforce')
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_server_config()

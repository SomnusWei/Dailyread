import paramiko

def debug_webdav():
    hostname = '47.95.205.216'
    port = 22
    username = 'root'
    password = 'Somnus890930'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=10)
        
        print("=== 检查 Nginx 配置 ===")
        stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/default')
        print(stdout.read().decode())
        
        print("\n=== 检查 Nginx 日志 ===")
        stdin, stdout, stderr = ssh.exec_command('tail -30 /var/log/nginx/error.log')
        print(stdout.read().decode())
        
        print("\n=== 检查访问日志 ===")
        stdin, stdout, stderr = ssh.exec_command('tail -30 /var/log/nginx/access.log')
        print(stdout.read().decode())
        
        print("\n=== 测试代理连接 ===")
        stdin, stdout, stderr = ssh.exec_command('curl -v https://dav.jianguoyun.com/dav/DailyRead 2>&1 | head -50')
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_webdav()

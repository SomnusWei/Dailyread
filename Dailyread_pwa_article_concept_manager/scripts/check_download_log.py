import paramiko

def check_download_log():
    hostname = '47.95.205.216'
    port = 22
    username = 'root'
    password = 'Somnus890930'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=10)
        
        print("=== 检查最近的访问日志 ===")
        stdin, stdout, stderr = ssh.exec_command('tail -40 /var/log/nginx/access.log')
        print(stdout.read().decode())
        
        print("\n=== 检查错误日志 ===")
        stdin, stdout, stderr = ssh.exec_command('tail -20 /var/log/nginx/error.log')
        print(stdout.read().decode())
        
        print("\n=== 测试下载文件 ===")
        stdin, stdout, stderr = ssh.exec_command('curl -v -u "username:password" https://dav.jianguoyun.com/dav/DailyRead/daily_read_backup_windows.json 2>&1 | head -60')
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_download_log()

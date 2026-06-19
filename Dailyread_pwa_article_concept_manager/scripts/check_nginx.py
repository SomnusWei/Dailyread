"""
检查并修复 Nginx 配置
"""
import paramiko

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f'连接服务器 {SERVER_IP}...')
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)
        
        # 查看当前配置
        print('\\n查看当前 Nginx 配置...')
        stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/default')
        config = stdout.read().decode()
        print(config[:2000])
        
        # 检查 /api/ 配置
        print('\\n检查 /api/ 配置...')
        if 'location /api/' in config:
            print('已有 /api/ 配置')
            # 检查配置是否正确
            if 'proxy_pass http://localhost:3001' in config:
                print('proxy_pass 配置正确')
            else:
                print('proxy_pass 配置不正确')
        else:
            print('没有 /api/ 配置，需要添加')
        
        # 测试本地 API
        print('\\n测试本地 API...')
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3001/api/auth/user')
        print(stdout.read().decode())
        
        # 测试通过 Nginx
        print('\\n测试通过 Nginx...')
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost/api/auth/user')
        print(stdout.read().decode())
        
    except Exception as e:
        print(f'错误: {e}')
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
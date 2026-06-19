"""
配置 Nginx 代理并重新部署前端
"""
import paramiko
import os

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f'连接服务器 {SERVER_IP}...')
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)
        
        # 1. 配置 Nginx 代理
        print('\\n配置 Nginx 代理...')
        
        # 获取当前 Nginx 配置
        stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/default')
        current_config = stdout.read().decode()
        
        # 检查是否已有 /api/ 代理
        if '/api/' not in current_config:
            # 添加 API 代理配置
            api_proxy = '''
        # 后端 API 代理
        location /api/ {
            proxy_pass http://localhost:3001/api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_cache_bypass $http_upgrade;
        }
'''
            # 在 server { 后添加配置
            cmd = f'''sed -i '/server {{/a '{api_proxy}' /etc/nginx/sites-available/default'''
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()
            
            # 测试 Nginx 配置
            stdin, stdout, stderr = ssh.exec_command('nginx -t')
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err and 'successful' not in err:
                print(f'Nginx 配置错误: {err}')
                return
            
            # 重载 Nginx
            stdin, stdout, stderr = ssh.exec_command('systemctl reload nginx')
            stdout.read()
            print('Nginx 配置完成')
        else:
            print('Nginx 已有 /api/ 代理配置')
        
        # 2. 测试外部 API 访问
        print('\\n测试外部 API 访问...')
        stdin, stdout, stderr = ssh.exec_command('curl -s http://47.95.205.216/api/auth/user')
        print(stdout.read().decode())
        
        print('\\n部署完成！')
        print('后端 API 地址: http://47.95.205.216/api/')
        
    except Exception as e:
        print(f'错误: {e}')
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
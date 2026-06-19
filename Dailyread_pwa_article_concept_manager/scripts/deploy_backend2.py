"""
分步部署后端服务到服务器
"""
import paramiko
import time

SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

def run_command(ssh, cmd, timeout=60):
    """执行命令并返回输出"""
    print(f'执行: {cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out[:500])
    if err:
        print(f'错误: {err[:500]}')
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f'连接服务器 {SERVER_IP}...')
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)
        
        # 1. 安装 better-sqlite3 的编译依赖
        print('\\n1. 安装编译依赖...')
        run_command(ssh, 'apt install -y build-essential python3', timeout=120)
        
        # 2. 安装 npm 依赖
        print('\\n2. 安装 npm 依赖...')
        run_command(ssh, 'cd /opt/dailyread-server && npm install --build-from-source', timeout=300)
        
        # 3. 创建 systemd 服务
        print('\\n3. 创建 systemd 服务...')
        service = '''[Unit]
Description=DailyRead Backend Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dailyread-server
ExecStart=/usr/bin/node src/index.js
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target'''
        
        run_command(ssh, f'echo "{service}" > /etc/systemd/system/dailyread-server.service')
        
        # 4. 启动服务
        print('\\n4. 启动服务...')
        run_command(ssh, 'systemctl daemon-reload')
        run_command(ssh, 'systemctl enable dailyread-server')
        run_command(ssh, 'systemctl restart dailyread-server')
        
        # 5. 检查服务状态
        print('\\n5. 检查服务状态...')
        time.sleep(3)
        run_command(ssh, 'systemctl status dailyread-server --no-pager')
        
        # 6. 配置 Nginx
        print('\\n6. 配置 Nginx...')
        run_command(ssh, '''
cat > /tmp/api_proxy.conf << 'EOF'
        location /api/ {
            proxy_pass http://localhost:3001/api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
EOF
''')
        run_command(ssh, 'sed -i "/server {/r /tmp/api_proxy.conf" /etc/nginx/sites-available/default')
        run_command(ssh, 'nginx -t')
        run_command(ssh, 'systemctl reload nginx')
        
        print('\\n部署完成！')
        
    except Exception as e:
        print(f'错误: {e}')
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
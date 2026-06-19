"""
部署后端服务到服务器
"""
import paramiko
import os

# 服务器信息
SERVER_IP = '47.95.205.216'
SERVER_PASSWORD = 'Somnus890930'
SERVER_USER = 'root'

# 本地后端目录
LOCAL_SERVER_DIR = os.path.join(os.path.dirname(__file__), '..', 'server')

def deploy_backend():
    """部署后端服务"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f'连接服务器 {SERVER_IP}...')
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD)
        
        # 1. 检查 Node.js 是否安装
        print('检查 Node.js...')
        stdin, stdout, stderr = ssh.exec_command('node --version')
        node_version = stdout.read().decode().strip()
        
        if not node_version:
            print('Node.js 未安装，正在安装...')
            stdin, stdout, stderr = ssh.exec_command('apt update && apt install -y nodejs npm')
            stdout.read()
            print('Node.js 安装完成')
        else:
            print(f'Node.js 版本: {node_version}')
        
        # 2. 创建后端目录
        print('创建后端目录...')
        stdin, stdout, stderr = ssh.exec_command('mkdir -p /opt/dailyread-server/data')
        stdout.read()
        
        # 3. 上传后端代码
        print('上传后端代码...')
        sftp = ssh.open_sftp()
        
        # 上传 package.json
        local_package = os.path.join(LOCAL_SERVER_DIR, 'package.json')
        remote_package = '/opt/dailyread-server/package.json'
        sftp.put(local_package, remote_package)
        print(f'上传 {local_package} -> {remote_package}')
        
        # 上传 index.js
        local_index = os.path.join(LOCAL_SERVER_DIR, 'src', 'index.js')
        remote_index = '/opt/dailyread-server/src/index.js'
        stdin, stdout, stderr = ssh.exec_command('mkdir -p /opt/dailyread-server/src')
        stdout.read()
        sftp.put(local_index, remote_index)
        print(f'上传 {local_index} -> {remote_index}')
        
        sftp.close()
        
        # 4. 安装依赖
        print('安装依赖...')
        stdin, stdout, stderr = ssh.exec_command('cd /opt/dailyread-server && npm install')
        stdout.read()
        print('依赖安装完成')
        
        # 5. 创建 systemd 服务
        print('创建 systemd 服务...')
        service_content = '''[Unit]
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
WantedBy=multi-user.target
'''
        
        stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/systemd/system/dailyread-server.service << \'EOF\'\n{service_content}\nEOF')
        stdout.read()
        
        # 6. 启动服务
        print('启动服务...')
        stdin, stdout, stderr = ssh.exec_command('systemctl daemon-reload && systemctl enable dailyread-server && systemctl restart dailyread-server')
        stdout.read()
        
        # 7. 检查服务状态
        stdin, stdout, stderr = ssh.exec_command('systemctl status dailyread-server')
        status = stdout.read().decode()
        print(f'服务状态:\n{status}')
        
        # 8. 配置 Nginx 代理
        print('配置 Nginx 代理...')
        nginx_config = '''
        location /api/ {
            proxy_pass http://localhost:3001/api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
'''
        
        stdin, stdout, stderr = ssh.exec_command(f'''
sed -i '/location \\/api\\/webdav\\/ {{/i '{nginx_config}' /etc/nginx/sites-available/default
''')
        stdout.read()
        
        stdin, stdout, stderr = ssh.exec_command('nginx -t && systemctl reload nginx')
        stdout.read()
        print('Nginx 配置完成')
        
        print('\\n部署完成！后端服务已启动在 http://localhost:3001')
        
    except Exception as e:
        print(f'部署失败: {e}')
    finally:
        ssh.close()

if __name__ == '__main__':
    deploy_backend()
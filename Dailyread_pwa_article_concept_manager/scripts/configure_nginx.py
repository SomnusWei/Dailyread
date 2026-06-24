import paramiko

def configure_nginx():
    hostname = '47.95.205.216'
    port = 22
    username = 'root'
    password = 'Somnus890930'
    
    nginx_config = '''server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/www/html;
        index index.html index.htm index.nginx-debian.html;

        server_name _;

        # 后端 API 反向代理配置
        location /api/ {
            proxy_pass http://127.0.0.1:3001/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebDAV 反向代理配置 - 解决跨域问题
        location /api/webdav/ {
            proxy_pass https://dav.jianguoyun.com/;
            
            # SSL 支持
            proxy_ssl_server_name on;
            proxy_ssl_protocols TLSv1.2 TLSv1.3;

            # 传递必要的头部信息
            proxy_set_header Host dav.jianguoyun.com;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebDAV 特有的配置
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
            proxy_buffering off;
        }

        location / {
            try_files $uri $uri/ /index.html;
        }
    }
    '''
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=10)
        
        print("备份原始配置...")
        stdin, stdout, stderr = ssh.exec_command('cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.bak')
        stdout.read()
        
        print("写入新配置...")
        sftp = ssh.open_sftp()
        with sftp.open('/etc/nginx/sites-available/default', 'w') as f:
            f.write(nginx_config)
        sftp.close()
        
        print("验证配置...")
        stdin, stdout, stderr = ssh.exec_command('nginx -t')
        result = stdout.read().decode()
        error = stderr.read().decode()
        print(result)
        if error:
            print(f"错误: {error}")
        
        print("重启 Nginx...")
        stdin, stdout, stderr = ssh.exec_command('systemctl restart nginx')
        stdout.read()
        
        print("检查状态...")
        stdin, stdout, stderr = ssh.exec_command('systemctl status nginx')
        result = stdout.read().decode()
        print(result[:500])
        
        ssh.close()
        print("\n✓ Nginx 配置完成！")
        
    except Exception as e:
        print(f"配置失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    configure_nginx()

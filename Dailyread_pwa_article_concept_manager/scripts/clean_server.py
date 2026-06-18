import paramiko

def clean_old_pwa():
    hostname = '47.95.205.216'
    port = 22
    username = 'root'
    password = 'Somnus890930'
    
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"正在连接服务器 {hostname}...")
        ssh.connect(hostname, port, username, password, timeout=10)
        
        # 查找可能的PWA目录
        print("\n查找可能的PWA目录...")
        possible_paths = [
            '/var/www/html/',
            '/var/www/',
            '/www/',
            '/root/',
            '/home/',
            '/opt/web/',
            '/usr/share/nginx/html/'
        ]
        
        found_paths = []
        for path in possible_paths:
            stdin, stdout, stderr = ssh.exec_command(f'find {path} -maxdepth 2 -type d -name "*pwa*" -o -type d -name "*PWA*" 2>/dev/null | head -20')
            result = stdout.read().decode().strip()
            if result:
                found_paths.extend(result.split('\n'))
                print(f"\n在 {path} 下找到:")
                for line in result.split('\n'):
                    print(f"  - {line}")
        
        # 查找包含index.html的目录
        print("\n查找包含 index.html 的目录...")
        stdin, stdout, stderr = ssh.exec_command('find /var/www /usr/share/nginx/html /root -maxdepth 3 -name "index.html" 2>/dev/null | head -20')
        html_files = stdout.read().decode().strip()
        if html_files:
            print(html_files)
            for line in html_files.split('\n'):
                dir_path = line.replace('/index.html', '')
                if dir_path not in found_paths:
                    found_paths.append(dir_path)
        
        if not found_paths:
            print("\n未找到旧版PWA目录")
            ssh.close()
            return
        
        print("\n\n找到以下可能包含旧版PWA的目录:")
        for i, path in enumerate(found_paths, 1):
            print(f"{i}. {path}")
        
        print("\n正在清空这些目录...")
        for path in found_paths:
            try:
                # 先检查目录是否存在
                stdin, stdout, stderr = ssh.exec_command(f'ls -la {path}')
                output = stdout.read().decode().strip()
                if output:
                    print(f"\n清空目录: {path}")
                    print(f"原内容: {output[:200]}...")
                    
                    # 删除目录内所有文件
                    stdin, stdout, stderr = ssh.exec_command(f'rm -rf {path}/*')
                    stdout.read()
                    
                    # 验证清空
                    stdin, stdout, stderr = ssh.exec_command(f'ls -la {path}')
                    result = stdout.read().decode().strip()
                    if not result or result == 'total 8':
                        print(f"✓ 目录 {path} 已清空")
                    else:
                        print(f"✗ 清空失败: {result}")
            except Exception as e:
                print(f"处理 {path} 时出错: {e}")
        
        print("\n✓ 操作完成")
        ssh.close()
        
    except Exception as e:
        print(f"连接或执行命令失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    clean_old_pwa()

import paramiko

print("=== 使用 paramiko 连接服务器 ===")

try:
    # 创建 SSH 客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 连接服务器
    print("正在连接...")
    ssh.connect('47.95.205.216', username='root', password='Somnus890930', timeout=30)
    print("连接成功！")
    
    # 执行命令
    commands = [
        'ls -la /var/www/',
        'ls -la /usr/share/nginx/html/',
        'find / -type d -name "*pwa*" 2>/dev/null | head -10',
        'find / -type d -name "*dailyread*" 2>/dev/null | head -10',
        'cat /etc/nginx/sites-available/default 2>/dev/null || echo "default not found"',
        'ls -la /etc/nginx/sites-available/',
        'ls -la /etc/nginx/sites-enabled/'
    ]
    
    for cmd in commands:
        print(f"\n--- 执行: {cmd} ---")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # 获取输出
        output = stdout.read().decode('utf-8', errors='replace').strip()
        error = stderr.read().decode('utf-8', errors='replace').strip()
        
        if output:
            print(output)
        if error:
            print(f"错误: {error}")
    
    ssh.close()
    print("\n=== 操作完成 ===")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

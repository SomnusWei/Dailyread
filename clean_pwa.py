import paramiko

print("=== 查看并清理旧版 PWA 项目 ===")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('47.95.205.216', username='root', password='Somnus890930', timeout=30)
    print("连接成功！")
    
    # 查看网站根目录的完整内容（包括隐藏文件）
    print("\n--- 1. 查看 /var/www/html/ 目录内容 ---")
    stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/html/')
    print(stdout.read().decode('utf-8'))
    
    # 查看 /root/my-pwa-site 目录
    print("\n--- 2. 查看 /root/my-pwa-site 目录内容 ---")
    stdin, stdout, stderr = ssh.exec_command('ls -la /root/my-pwa-site/')
    output = stdout.read().decode('utf-8')
    print(output)
    
    # 查看 /opt/web/my-pwa-site 目录
    print("\n--- 3. 查看 /opt/web/my-pwa-site 目录内容 ---")
    stdin, stdout, stderr = ssh.exec_command('ls -la /opt/web/my-pwa-site/')
    output = stdout.read().decode('utf-8')
    print(output)
    
    # 检查是否有 dist 目录
    print("\n--- 4. 检查是否有 dist 目录 ---")
    stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/html/dist/ 2>/dev/null || ls -la /root/my-pwa-site/dist/ 2>/dev/null || ls -la /opt/web/my-pwa-site/dist/ 2>/dev/null')
    output = stdout.read().decode('utf-8')
    if output:
        print(output)
    else:
        print("未找到 dist 目录")
    
    # 清空 /var/www/html/ 目录（这是当前 nginx 服务的目录）
    print("\n--- 5. 清空 /var/www/html/ 目录 ---")
    stdin, stdout, stderr = ssh.exec_command('rm -rf /var/www/html/*')
    stdout.read()
    stderr.read()
    print("已清空 /var/www/html/ 目录")
    
    # 清空旧的 pwa-site 目录
    print("\n--- 6. 清空旧的 PWA 项目目录 ---")
    stdin, stdout, stderr = ssh.exec_command('rm -rf /root/my-pwa-site /opt/web/my-pwa-site')
    stdout.read()
    stderr.read()
    print("已删除旧的 PWA 项目目录")
    
    # 验证清理结果
    print("\n--- 7. 验证清理结果 ---")
    stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/html/')
    print("/var/www/html/:")
    print(stdout.read().decode('utf-8'))
    
    stdin, stdout, stderr = ssh.exec_command('ls /root/my-pwa-site 2>/dev/null || echo "已删除"')
    print("/root/my-pwa-site:", stdout.read().decode('utf-8').strip())
    
    stdin, stdout, stderr = ssh.exec_command('ls /opt/web/my-pwa-site 2>/dev/null || echo "已删除"')
    print("/opt/web/my-pwa-site:", stdout.read().decode('utf-8').strip())
    
    ssh.close()
    print("\n=== 清理完成 ===")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

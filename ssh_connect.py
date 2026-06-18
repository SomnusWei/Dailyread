import paramiko
import time

try:
    print("尝试连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect('47.95.205.216', username='root', password='Somnus890930', timeout=30, banner_timeout=30)
        print("连接成功！")
    except Exception as conn_err:
        print(f"连接失败: {conn_err}")
        raise
    
    print("\n=== 查找pwa和dailyread相关目录 ===")
    stdin, stdout, stderr = ssh.exec_command('find / -type d -name "*pwa*" 2>/dev/null')
    time.sleep(2)
    result1 = stdout.read().decode('utf-8').strip()
    stderr1 = stderr.read().decode('utf-8').strip()
    if result1:
        print(result1)
    else:
        print("未找到pwa目录")
    if stderr1:
        print(f"错误: {stderr1}")
    
    stdin, stdout, stderr = ssh.exec_command('find / -type d -name "*dailyread*" 2>/dev/null')
    time.sleep(2)
    result2 = stdout.read().decode('utf-8').strip()
    stderr2 = stderr.read().decode('utf-8').strip()
    if result2:
        print(result2)
    else:
        print("未找到dailyread目录")
    if stderr2:
        print(f"错误: {stderr2}")
    
    print("\n=== 查看/var/www目录 ===")
    stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/ 2>/dev/null')
    time.sleep(1)
    result3 = stdout.read().decode('utf-8').strip()
    stderr3 = stderr.read().decode('utf-8').strip()
    if result3:
        print(result3)
    else:
        print("/var/www目录不存在或为空")
    if stderr3:
        print(f"错误: {stderr3}")
    
    print("\n=== 查看nginx sites-available目录 ===")
    stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/sites-available/ 2>/dev/null')
    time.sleep(1)
    result4 = stdout.read().decode('utf-8').strip()
    stderr4 = stderr.read().decode('utf-8').strip()
    if result4:
        print(result4)
    else:
        print("sites-available目录不存在")
    if stderr4:
        print(f"错误: {stderr4}")
    
    print("\n=== 查看nginx sites-enabled目录 ===")
    stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/sites-enabled/ 2>/dev/null')
    time.sleep(1)
    result5 = stdout.read().decode('utf-8').strip()
    stderr5 = stderr.read().decode('utf-8').strip()
    if result5:
        print(result5)
    else:
        print("sites-enabled目录不存在")
    if stderr5:
        print(f"错误: {stderr5}")
    
    ssh.close()
    print("\n操作完成")
    
except Exception as e:
    print(f"总错误: {e}")
    import traceback
    traceback.print_exc()

import paramiko
import os

def deploy_to_server():
    hostname = '47.95.205.216'
    port = 22
    username = 'root'
    password = 'Somnus890930'
    
    local_dist_path = 'e:\\item\\DailyRead\\Dailyread_pwa_article_concept_manager\\dist'
    remote_path = '/var/www/html'
    
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"正在连接服务器 {hostname}...")
        ssh.connect(hostname, port, username, password, timeout=10)
        
        # 清空目标目录
        print("清空目标目录...")
        stdin, stdout, stderr = ssh.exec_command(f'rm -rf {remote_path}/*')
        stdout.read()
        
        # 使用SFTP上传文件
        print("\n正在上传文件...")
        sftp = ssh.open_sftp()
        
        for root, dirs, files in os.walk(local_dist_path):
            for file in files:
                local_file = os.path.join(root, file)
                # 计算相对路径
                rel_path = os.path.relpath(local_file, local_dist_path)
                remote_file = os.path.join(remote_path, rel_path).replace('\\', '/')
                
                # 创建远程目录
                remote_dir = os.path.dirname(remote_file).replace('\\', '/')
                stdin, stdout, stderr = ssh.exec_command(f'mkdir -p "{remote_dir}"')
                stdout.read()
                
                print(f"上传: {rel_path} -> {remote_file}")
                sftp.put(local_file, remote_file)
        
        sftp.close()
        
        # 设置权限
        print("\n设置文件权限...")
        stdin, stdout, stderr = ssh.exec_command(f'chown -R www-data:www-data {remote_path}')
        stdout.read()
        stdin, stdout, stderr = ssh.exec_command(f'chmod -R 755 {remote_path}')
        stdout.read()
        
        # 验证上传
        print("\n验证上传...")
        stdin, stdout, stderr = ssh.exec_command(f'ls -la "{remote_path}"')
        result = stdout.read().decode().strip()
        print(result)
        
        # 重启Nginx
        print("\n重启Nginx服务...")
        stdin, stdout, stderr = ssh.exec_command('systemctl restart nginx')
        stdout.read()
        
        # 检查Nginx状态
        stdin, stdout, stderr = ssh.exec_command('systemctl status nginx')
        result = stdout.read().decode().strip()
        print(result[:500])
        
        ssh.close()
        print("\n✓ 部署完成！")
        print(f"项目已部署到: http://{hostname}/")
        
    except Exception as e:
        print(f"部署失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    deploy_to_server()

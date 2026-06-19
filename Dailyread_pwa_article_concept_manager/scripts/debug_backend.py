"""
检查并修复后端服务
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
        
        # 检查文件是否存在
        print('\\n检查文件...')
        stdin, stdout, stderr = ssh.exec_command('ls -la /opt/dailyread-server/')
        print(stdout.read().decode())
        
        stdin, stdout, stderr = ssh.exec_command('ls -la /opt/dailyread-server/src/')
        print(stdout.read().decode())
        
        # 检查 node_modules
        print('\\n检查 node_modules...')
        stdin, stdout, stderr = ssh.exec_command('ls -la /opt/dailyread-server/node_modules/ | head -20')
        print(stdout.read().decode())
        
        # 手动启动服务测试
        print('\\n手动启动服务测试...')
        stdin, stdout, stderr = ssh.exec_command('cd /opt/dailyread-server && timeout 5 node src/index.js 2>&1 || true')
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 检查错误日志
        print('\\n检查 systemd 日志...')
        stdin, stdout, stderr = ssh.exec_command('journalctl -u dailyread-server --no-pager -n 50')
        print(stdout.read().decode())
        
    except Exception as e:
        print(f'错误: {e}')
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
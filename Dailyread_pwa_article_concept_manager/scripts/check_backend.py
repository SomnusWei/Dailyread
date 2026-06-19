"""
检查后端服务状态
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
        
        # 检查服务状态
        print('\\n检查 dailyread-server 服务状态...')
        stdin, stdout, stderr = ssh.exec_command('systemctl status dailyread-server --no-pager')
        print(stdout.read().decode())
        
        # 检查端口
        print('\\n检查端口 3001...')
        stdin, stdout, stderr = ssh.exec_command('netstat -tlnp | grep 3001')
        print(stdout.read().decode())
        
        # 测试 API
        print('\\n测试 API...')
        stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3001/api/auth/user')
        print(stdout.read().decode())
        
    except Exception as e:
        print(f'错误: {e}')
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
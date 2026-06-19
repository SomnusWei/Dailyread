"""
修复 better-sqlite3 编译问题
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
        
        # 重新编译 better-sqlite3
        print('\\n重新编译 better-sqlite3...')
        stdin, stdout, stderr = ssh.exec_command('cd /opt/dailyread-server && npm rebuild better-sqlite3', timeout=300)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print(f'错误: {err}')
        
        # 再次测试启动
        print('\\n测试启动...')
        stdin, stdout, stderr = ssh.exec_command('cd /opt/dailyread-server && timeout 5 node src/index.js 2>&1 || true')
        print(stdout.read().decode())
        
        # 如果成功，启动服务
        print('\\n启动服务...')
        stdin, stdout, stderr = ssh.exec_command('systemctl restart dailyread-server')
        stdout.read()
        
        # 检查状态
        print('\\n检查状态...')
        stdin, stdout, stderr = ssh.exec_command('systemctl status dailyread-server --no-pager')
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
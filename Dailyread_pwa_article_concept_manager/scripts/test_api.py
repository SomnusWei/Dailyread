"""
测试后端 API
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
        
        # 测试注册
        print('\\n测试注册 API...')
        stdin, stdout, stderr = ssh.exec_command('curl -s -X POST http://localhost:3001/api/auth/register -H "Content-Type: application/json" -d \'{"username":"testuser","password":"test123456"}\'')
        print(stdout.read().decode())
        
        # 测试登录
        print('\\n测试登录 API...')
        stdin, stdout, stderr = ssh.exec_command('curl -s -X POST http://localhost:3001/api/auth/login -H "Content-Type: application/json" -d \'{"username":"testuser","password":"test123456"}\'')
        result = stdout.read().decode()
        print(result)
        
        # 获取 token
        import json
        try:
            data = json.loads(result)
            token = data.get('token', '')
            if token:
                # 测试获取用户信息
                print('\\n测试获取用户信息 API...')
                stdin, stdout, stderr = ssh.exec_command(f'curl -s http://localhost:3001/api/auth/user -H "Authorization: Bearer {token}"')
                print(stdout.read().decode())
                
                # 测试 WebDAV 配置
                print('\\n测试 WebDAV 配置 API...')
                stdin, stdout, stderr = ssh.exec_command(f'curl -s http://localhost:3001/api/webdav/config -H "Authorization: Bearer {token}"')
                print(stdout.read().decode())
        except:
            pass
        
        # 检查服务状态
        print('\\n服务状态...')
        stdin, stdout, stderr = ssh.exec_command('systemctl status dailyread-server --no-pager | head -10')
        print(stdout.read().decode())
        
    except Exception as e:
        print(f'错误: {e}')
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
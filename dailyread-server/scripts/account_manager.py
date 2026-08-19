"""
DailyRead 服务器账号管理工具
功能：添加、删除、修改、查询线上数据库中的用户账号
使用方法：
  pip install mysql-connector-python bcrypt
  python account_manager.py --host <host> --user <user> --password <pwd> --database <db>
  
示例：
  # 列出所有用户
  python account_manager.py list
  
  # 添加用户
  python account_manager.py add --username test123 --password "mypassword" --nickname "测试"
  
  # 删除用户
  python account_manager.py delete --username test123
  
  # 修改密码
  python account_manager.py change-password --username test123 --new-password "newpass"
"""

import argparse
import sys
import os
from datetime import datetime

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("请先安装 mysql-connector-python: pip install mysql-connector-python")
    sys.exit(1)

try:
    import bcrypt
except ImportError:
    print("请先安装 bcrypt: pip install bcrypt")
    sys.exit(1)


class AccountManager:
    """DailyRead 账号管理器"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4'
        }
        self.conn = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = mysql.connector.connect(**self.config)
            if self.conn.is_connected():
                print(f"✓ 已连接到数据库 {self.config['host']}:{self.config['port']}/{self.config['database']}")
                return True
        except Error as e:
            print(f"✗ 数据库连接失败: {e}")
            return False
        return False

    def close(self):
        """关闭连接"""
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("✓ 数据库连接已关闭")

    def list_users(self):
        """列出所有用户"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, username, nickname, created_at, last_login
                FROM users
                ORDER BY id ASC
            """)
            users = cursor.fetchall()
            cursor.close()

            if not users:
                print("暂无用户")
                return []

            print(f"\n共 {len(users)} 个用户:")
            print("-" * 80)
            print(f"{'ID':<6}{'用户名':<20}{'昵称':<20}{'创建时间':<25}{'最后登录':<25}")
            print("-" * 80)
            for u in users:
                created = str(u['created_at']) if u['created_at'] else ''
                last = str(u['last_login']) if u['last_login'] else '从未登录'
                print(f"{u['id']:<6}{u['username']:<20}{u['nickname'] or '':<20}{created:<25}{last:<25}")
            print("-" * 80)
            return users

        except Error as e:
            print(f"✗ 查询用户失败: {e}")
            return []

    def add_user(self, username: str, password: str, nickname: str = ''):
        """添加新用户"""
        # 校验
        if len(username) < 3 or len(username) > 32:
            print("✗ 用户名长度需为 3-32 字符")
            return False
        if len(password) < 6 or len(password) > 64:
            print("✗ 密码长度需为 6-64 字符")
            return False

        try:
            cursor = self.conn.cursor(dictionary=True)

            # 检查重名
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                print(f"✗ 用户名 '{username}' 已存在")
                cursor.close()
                return False

            # 加密密码
            pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=10))
            hash_str = pwd_hash.decode('utf-8')

            # 插入用户
            cursor.execute(
                "INSERT INTO users (username, password, nickname) VALUES (%s, %s, %s)",
                (username, hash_str, nickname)
            )
            user_id = cursor.lastrowid

            # 初始化用户配置
            cursor.execute("INSERT INTO user_configs (user_id) VALUES (%s)", (user_id,))

            self.conn.commit()
            cursor.close()

            print(f"✓ 用户创建成功:")
            print(f"  ID: {user_id}")
            print(f"  用户名: {username}")
            print(f"  昵称: {nickname or '(空)'}")
            print(f"  密码哈希: {hash_str}")
            return True

        except Error as e:
            self.conn.rollback()
            print(f"✗ 创建用户失败: {e}")
            return False

    def delete_user(self, username: str):
        """删除用户及其所有关联数据"""
        try:
            cursor = self.conn.cursor(dictionary=True)

            # 查找用户
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"✗ 用户 '{username}' 不存在")
                cursor.close()
                return False

            user_id = user['id']

            # 确认删除
            confirm = input(f"⚠ 确认删除用户 '{username}' (ID={user_id}) 及其所有文章、打卡、任务数据？[y/N]: ")
            if confirm.lower() != 'y':
                print("已取消删除")
                cursor.close()
                return False

            # 开启事务，按外键依赖顺序删除
            self.conn.start_transaction()

            # 1. daily_task_items
            cursor.execute("""
                DELETE di FROM daily_task_items di
                INNER JOIN daily_tasks dt ON dt.id = di.task_id
                WHERE dt.user_id = %s
            """, (user_id,))
            items_del = cursor.rowcount
            print(f"  删除 daily_task_items: {items_del} 行")

            # 2. daily_tasks
            cursor.execute("DELETE FROM daily_tasks WHERE user_id = %s", (user_id,))
            tasks_del = cursor.rowcount
            print(f"  删除 daily_tasks: {tasks_del} 行")

            # 3. checkins
            cursor.execute("""
                DELETE FROM checkins
                WHERE article_id IN (SELECT id FROM articles WHERE user_id = %s)
            """, (user_id,))
            checkins_del = cursor.rowcount
            print(f"  删除 checkins: {checkins_del} 行")

            # 4. articles
            cursor.execute("DELETE FROM articles WHERE user_id = %s", (user_id,))
            articles_del = cursor.rowcount
            print(f"  删除 articles: {articles_del} 行")

            # 5. user_configs
            cursor.execute("DELETE FROM user_configs WHERE user_id = %s", (user_id,))
            print(f"  删除 user_configs: 1 行")

            # 6. users
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            print(f"  删除 users: 1 行")

            self.conn.commit()
            cursor.close()

            print(f"✓ 用户 '{username}' 及其所有关联数据已彻底删除")
            print(f"  共删除: articles={articles_del}, checkins={checkins_del}, "
                  f"tasks={tasks_del}, task_items={items_del}")
            return True

        except Error as e:
            self.conn.rollback()
            print(f"✗ 删除失败（已回滚）: {e}")
            return False

    def change_password(self, username: str, new_password: str):
        """修改用户密码"""
        if len(new_password) < 6 or len(new_password) > 64:
            print("✗ 密码长度需为 6-64 字符")
            return False

        try:
            cursor = self.conn.cursor(dictionary=True)

            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"✗ 用户 '{username}' 不存在")
                cursor.close()
                return False

            # 新密码哈希
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(rounds=10))
            hash_str = new_hash.decode('utf-8')

            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (hash_str, user['id'])
            )
            self.conn.commit()
            cursor.close()

            print(f"✓ 用户 '{username}' 密码已更新")
            print(f"  新密码哈希: {hash_str}")
            return True

        except Error as e:
            self.conn.rollback()
            print(f"✗ 修改密码失败: {e}")
            return False

    def show_user(self, username: str):
        """查看单个用户详情"""
        try:
            cursor = self.conn.cursor(dictionary=True)

            # 用户基本信息
            cursor.execute("""
                SELECT id, username, nickname, password, created_at, last_login
                FROM users WHERE username = %s
            """, (username,))
            user = cursor.fetchone()
            if not user:
                print(f"✗ 用户 '{username}' 不存在")
                cursor.close()
                return False

            print(f"\n用户详情:")
            print(f"  ID: {user['id']}")
            print(f"  用户名: {user['username']}")
            print(f"  昵称: {user['nickname'] or '(空)'}")
            print(f"  密码哈希: {user['password']}")
            print(f"  创建时间: {user['created_at']}")
            print(f"  最后登录: {user['last_login'] or '从未登录'}")

            # 统计文章数
            cursor.execute("SELECT COUNT(*) as cnt FROM articles WHERE user_id = %s AND deleted = 0", (user['id'],))
            article_count = cursor.fetchone()['cnt']
            print(f"\n文章数量: {article_count}")

            # 统计打卡次数
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM checkins ci
                INNER JOIN articles a ON a.id = ci.article_id
                WHERE a.user_id = %s
            """, (user['id'],))
            checkin_count = cursor.fetchone()['cnt']
            print(f"打卡次数: {checkin_count}")

            # 统计今日任务
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT count FROM daily_tasks WHERE user_id = %s AND task_date = %s",
                          (user['id'], today))
            task_row = cursor.fetchone()
            if task_row:
                print(f"今日任务: {task_row['count']} 篇")
            else:
                print("今日任务: 无")

            cursor.close()
            return True

        except Error as e:
            print(f"✗ 查询失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='DailyRead 服务器账号管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 在配置文件中设置数据库连接，然后运行:
  python account_manager.py list
  python account_manager.py add -u test123 -p "password123" -n "测试"
  python account_manager.py delete -u test123
  python account_manager.py change-password -u test123 -p "newpassword"
  python account_manager.py show -u test123
        """
    )

    # 数据库连接参数（从环境变量或默认值读取）
    parser.add_argument('--host', default=os.environ.get('DB_HOST', 'localhost'),
                        help='数据库主机 (默认: localhost)')
    parser.add_argument('--port', type=int, default=int(os.environ.get('DB_PORT', '3306')),
                        help='数据库端口 (默认: 3306)')
    parser.add_argument('--user', default=os.environ.get('DB_USER', 'root'),
                        help='数据库用户名 (默认: root)')
    parser.add_argument('--password', default=os.environ.get('DB_PASSWORD', ''),
                        help='数据库密码 (默认: 空)')
    parser.add_argument('--database', default=os.environ.get('DB_NAME', 'dailyread_db'),
                        help='数据库名 (默认: dailyread_db)')

    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='操作命令')

    # list 命令
    subparsers.add_parser('list', help='列出所有用户')

    # show 命令
    show_parser = subparsers.add_parser('show', help='查看单个用户详情')
    show_parser.add_argument('-u', '--username', required=True, help='用户名')

    # add 命令
    add_parser = subparsers.add_parser('add', help='添加新用户')
    add_parser.add_argument('-u', '--username', required=True, help='用户名 (3-32字符)')
    add_parser.add_argument('-p', '--password', required=True, help='密码 (6-64字符)')
    add_parser.add_argument('-n', '--nickname', default='', help='昵称 (可选)')

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除用户')
    delete_parser.add_argument('-u', '--username', required=True, help='要删除的用户名')

    # change-password 命令
    cp_parser = subparsers.add_parser('change-password', help='修改用户密码')
    cp_parser.add_argument('-u', '--username', required=True, help='用户名')
    cp_parser.add_argument('-p', '--password', required=True, help='新密码 (6-64字符)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 创建管理器并连接
    mgr = AccountManager(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )

    if not mgr.connect():
        sys.exit(1)

    try:
        if args.command == 'list':
            mgr.list_users()

        elif args.command == 'show':
            mgr.show_user(args.username)

        elif args.command == 'add':
            mgr.add_user(args.username, args.password, args.nickname)

        elif args.command == 'delete':
            mgr.delete_user(args.username)

        elif args.command == 'change-password':
            mgr.change_password(args.username, args.password)

    finally:
        mgr.close()


if __name__ == '__main__':
    main()

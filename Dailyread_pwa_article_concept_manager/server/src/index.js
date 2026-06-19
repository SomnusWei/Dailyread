const express = require('express')
const Database = require('better-sqlite3')
const jwt = require('jsonwebtoken')
const bcrypt = require('bcryptjs')
const cors = require('cors')
const path = require('path')

const app = express()
const PORT = 3001
const JWT_SECRET = 'dailyread_secret_key_2024'

// 中间件
app.use(cors())
app.use(express.json())

// 数据库初始化
const dbPath = path.join(__dirname, '..', 'data', 'dailyread.db')
const db = new Database(dbPath)

// 创建用户表
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`)

// 创建 WebDAV 配置表
db.exec(`
  CREATE TABLE IF NOT EXISTS webdav_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    server_url TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    remote_path TEXT DEFAULT '/DailyRead',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
  )
`)

// JWT 验证中间件
function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1]
  if (!token) {
    return res.status(401).json({ error: '未登录' })
  }
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET)
    req.userId = decoded.userId
    next()
  } catch (error) {
    return res.status(401).json({ error: 'token 无效' })
  }
}

// ==================== 用户认证 API ====================

// 注册
app.post('/api/auth/register', async (req, res) => {
  try {
    const { username, password } = req.body
    
    if (!username || !password) {
      return res.status(400).json({ error: '用户名和密码不能为空' })
    }
    
    // 检查用户是否已存在
    const existingUser = db.prepare('SELECT id FROM users WHERE username = ?').get(username)
    if (existingUser) {
      return res.status(400).json({ error: '用户名已存在' })
    }
    
    // 加密密码
    const hashedPassword = await bcrypt.hash(password, 10)
    
    // 创建用户
    const result = db.prepare('INSERT INTO users (username, password) VALUES (?, ?)').run(username, hashedPassword)
    
    // 生成 token
    const token = jwt.sign({ userId: result.lastInsertRowid }, JWT_SECRET, { expiresIn: '7d' })
    
    res.json({
      success: true,
      token,
      user: {
        id: result.lastInsertRowid,
        username
      }
    })
  } catch (error) {
    console.error('注册失败:', error)
    res.status(500).json({ error: '注册失败' })
  }
})

// 登录
app.post('/api/auth/login', async (req, res) => {
  try {
    const { username, password } = req.body
    
    if (!username || !password) {
      return res.status(400).json({ error: '用户名和密码不能为空' })
    }
    
    // 查找用户
    const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username)
    if (!user) {
      return res.status(400).json({ error: '用户不存在' })
    }
    
    // 验证密码
    const isValid = await bcrypt.compare(password, user.password)
    if (!isValid) {
      return res.status(400).json({ error: '密码错误' })
    }
    
    // 生成 token
    const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '7d' })
    
    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        username: user.username
      }
    })
  } catch (error) {
    console.error('登录失败:', error)
    res.status(500).json({ error: '登录失败' })
  }
})

// 获取用户信息
app.get('/api/auth/user', authMiddleware, (req, res) => {
  try {
    const user = db.prepare('SELECT id, username, created_at FROM users WHERE id = ?').get(req.userId)
    if (!user) {
      return res.status(404).json({ error: '用户不存在' })
    }
    res.json({ user })
  } catch (error) {
    res.status(500).json({ error: '获取用户信息失败' })
  }
})

// ==================== WebDAV 配置 API ====================

// 获取 WebDAV 配置
app.get('/api/webdav/config', authMiddleware, (req, res) => {
  try {
    const config = db.prepare('SELECT * FROM webdav_configs WHERE user_id = ?').get(req.userId)
    if (!config) {
      return res.json({ config: null })
    }
    res.json({
      config: {
        serverUrl: config.server_url,
        username: config.username,
        password: config.password,
        remotePath: config.remote_path
      }
    })
  } catch (error) {
    res.status(500).json({ error: '获取配置失败' })
  }
})

// 保存 WebDAV 配置
app.post('/api/webdav/config', authMiddleware, (req, res) => {
  try {
    const { serverUrl, username, password, remotePath } = req.body
    
    if (!serverUrl || !username || !password) {
      return res.status(400).json({ error: '服务器地址、用户名和密码不能为空' })
    }
    
    // 检查是否已有配置
    const existing = db.prepare('SELECT id FROM webdav_configs WHERE user_id = ?').get(req.userId)
    
    if (existing) {
      // 更新配置
      db.prepare(`
        UPDATE webdav_configs 
        SET server_url = ?, username = ?, password = ?, remote_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
      `).run(serverUrl, username, password, remotePath || '/DailyRead', req.userId)
    } else {
      // 创建配置
      db.prepare(`
        INSERT INTO webdav_configs (user_id, server_url, username, password, remote_path)
        VALUES (?, ?, ?, ?, ?)
      `).run(req.userId, serverUrl, username, password, remotePath || '/DailyRead')
    }
    
    res.json({ success: true })
  } catch (error) {
    console.error('保存配置失败:', error)
    res.status(500).json({ error: '保存配置失败' })
  }
})

// 删除 WebDAV 配置
app.delete('/api/webdav/config', authMiddleware, (req, res) => {
  try {
    db.prepare('DELETE FROM webdav_configs WHERE user_id = ?').run(req.userId)
    res.json({ success: true })
  } catch (error) {
    res.status(500).json({ error: '删除配置失败' })
  }
})

// ==================== 启动服务 ====================

app.listen(PORT, () => {
  console.log(`DailyRead 后端服务已启动: http://localhost:${PORT}`)
})
// 炎武班学习中心 API
// 独立于 DailyRead 用户体系（lc_ 前缀表），token 增加 scope:'lc' 标记
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const multer = require('multer');
const crypto = require('crypto');
const path = require('path');
const fs = require('fs');
const rateLimit = require('express-rate-limit');
const { body, validationResult } = require('express-validator');
const { pool } = require('../db');
const config = require('../config');
const { success, error } = require('../utils/response');

const router = express.Router();

// ---------- 角色定义 ----------
const ROLE_LABELS = {
  admin: '管理员',
  teacher: '教师',
  phd: '博士生',
  master: '研究生',
  bachelor: '本科生',
  apprentice: '师承生'
};
const ALL_ROLES = Object.keys(ROLE_LABELS);
// 作业布置可选的学员等级（不含管理员/教师）
const STUDENT_ROLES = ['phd', 'master', 'bachelor', 'apprentice'];
const STAFF_ROLES = ['admin', 'teacher'];

// 讲义分类（12 选 1）
const HANDOUT_CATEGORIES = ['基础学', '诊断学', '针灸腧穴', '中药', '方剂', '内科', '外科', '妇科', '儿科', '推拿', '养生', '经典'];

// 学生提交文件白名单（word/excel/pdf/图片）
const SUBMIT_ALLOWED_EXT = /\.(docx?|xlsx?|pdf|jpe?g|png|gif|webp)$/i;

// ---------- JWT ----------
function lcSignToken(user) {
  return jwt.sign(
    { scope: 'lc', lcId: user.id, username: user.username, role: user.role },
    config.jwt.secret,
    { expiresIn: config.jwt.expiresIn }
  );
}

function lcAuthRequired(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json(error('未登录', 401));
  }
  try {
    const decoded = jwt.verify(authHeader.split(' ')[1], config.jwt.secret);
    if (decoded.scope !== 'lc' || !decoded.lcId) {
      return res.status(401).json(error('token 无效', 401));
    }
    req.lcUser = { id: decoded.lcId, username: decoded.username, role: decoded.role };
    next();
  } catch (e) {
    return res.status(401).json(error('token 无效或已过期', 401));
  }
}

function lcRequireStaff(req, res, next) {
  if (!STAFF_ROLES.includes(req.lcUser.role)) {
    return res.status(403).json(error('无权限，仅管理员/教师可操作', 403));
  }
  next();
}

function lcRequireAdmin(req, res, next) {
  if (req.lcUser.role !== 'admin') {
    return res.status(403).json(error('无权限，仅管理员可操作', 403));
  }
  next();
}

// ---------- 工具 ----------
function parseLevels(raw) {
  let arr = raw;
  if (typeof raw === 'string') {
    try { arr = JSON.parse(raw); } catch (e) { return null; }
  }
  if (!Array.isArray(arr) || arr.length === 0) return null;
  const out = [];
  for (const lv of arr) {
    if (typeof lv !== 'string') return null;
    if (lv === 'all') out.push('all');
    else if (ALL_ROLES.includes(lv)) out.push(lv);
    else return null;
  }
  return [...new Set(out)];
}

// 按等级扇出收件箱（levels 含 'all' 表示全等级）
async function fanoutToLevels(levels, category, refId, title, senderName, content) {
  const includesAll = levels.includes('all');
  const roles = includesAll ? ALL_ROLES : levels;
  const placeholders = roles.map(() => '?').join(',');
  const [users] = await pool.query(
    `SELECT id FROM lc_users WHERE role IN (${placeholders})`,
    roles
  );
  if (users.length === 0) return 0;
  const body = content ? String(content).slice(0, 100000) : null;
  const values = users.map(u => [u.id, category, refId, String(title).slice(0, 180), senderName, body]);
  await pool.query(
    'INSERT INTO lc_inbox (user_id, category, ref_id, title, sender_name, content) VALUES ?',
    [values]
  );
  return users.length;
}

// ---------- 登录限流 ----------
const loginLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: Math.max(10, config.rateLimit.loginPerMin * 2),
  standardHeaders: true,
  legacyHeaders: false,
  message: error('登录尝试过多，请稍后再试', 429)
});

// ---------- 讲义上传目录 ----------
const HANDOUTS_DIR = path.join(__dirname, '..', '..', 'uploads', 'handouts');
if (!fs.existsSync(HANDOUTS_DIR)) {
  fs.mkdirSync(HANDOUTS_DIR, { recursive: true });
}
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, HANDOUTS_DIR),
  filename: (req, file, cb) => {
    const name = Date.now() + '-' + crypto.randomBytes(6).toString('hex') + '.html';
    cb(null, name);
  }
});
const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const okExt = /\.(html?|htm)$/i.test(file.originalname || '');
    const okMime = /html/i.test(file.mimetype || '');
    if (okExt || okMime) return cb(null, true);
    cb(new Error('仅支持 HTML 文件'));
  }
});

// ---------- 学生作业提交上传 ----------
const SUBMISSIONS_DIR = path.join(__dirname, '..', '..', 'uploads', 'submissions');
if (!fs.existsSync(SUBMISSIONS_DIR)) {
  fs.mkdirSync(SUBMISSIONS_DIR, { recursive: true });
}
const submitStorage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, SUBMISSIONS_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname || '').toLowerCase().slice(0, 10) || '.bin';
    cb(null, Date.now() + '-' + crypto.randomBytes(6).toString('hex') + ext);
  }
});
const uploadSubmit = multer({
  storage: submitStorage,
  limits: { fileSize: 20 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (SUBMIT_ALLOWED_EXT.test(file.originalname || '')) return cb(null, true);
    cb(new Error('仅支持 Word/Excel/PDF/图片 文件'));
  }
});

// 作业提交窗口校验（毫秒时间戳，在应用层比较以规避时区问题）
function submitWindowStatus(assignment) {
  const now = Date.now();
  if (assignment.start_at && now < Number(assignment.start_at)) return 'pending';
  if (assignment.due_at && now > Number(assignment.due_at)) return 'closed';
  return 'open';
}

// ============================================================
// 账号与登录
// ============================================================

// POST /api/learning/login
router.post('/login', loginLimiter, [
  body('username').isLength({ min: 3, max: 32 }),
  body('password').isLength({ min: 6, max: 64 })
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.status(400).json(error('用户名或密码格式错误', 400));
  }
  const { username, password } = req.body;
  try {
    const [rows] = await pool.query(
      'SELECT id, username, password, nickname, role FROM lc_users WHERE username = ? LIMIT 1',
      [username]
    );
    if (rows.length === 0) return res.status(401).json(error('用户名或密码错误', 401));
    const user = rows[0];
    const ok = await bcrypt.compare(password, user.password);
    if (!ok) return res.status(401).json(error('用户名或密码错误', 401));
    await pool.query('UPDATE lc_users SET last_login = NOW() WHERE id = ?', [user.id]);
    const token = lcSignToken(user);
    return res.json(success({
      token,
      user: { id: user.id, username: user.username, nickname: user.nickname, role: user.role, roleLabel: ROLE_LABELS[user.role] }
    }, '登录成功'));
  } catch (e) {
    console.error('[learning/login]', e);
    return res.status(500).json(error('登录失败: ' + e.message, 500));
  }
});

// GET /api/learning/me
router.get('/me', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id, username, nickname, role, created_at, last_login FROM lc_users WHERE id = ? LIMIT 1',
      [req.lcUser.id]
    );
    if (rows.length === 0) return res.status(404).json(error('用户不存在', 404));
    const u = rows[0];
    u.roleLabel = ROLE_LABELS[u.role];
    return res.json(success(u));
  } catch (e) {
    return res.status(500).json(error('查询失败', 500));
  }
});

// ============================================================
// 收件箱 / 消息
// ============================================================

// GET /api/learning/inbox
router.get('/inbox', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT id, category, ref_id, title, sender_name, content, is_read, created_at
       FROM lc_inbox WHERE user_id = ?
       ORDER BY created_at DESC, id DESC LIMIT 200`,
      [req.lcUser.id]
    );
    // 附带讲义的可读等级范围，便于前端展示
    for (const r of rows) {
      r.categoryLabel = r.category === 'handout' ? '讲义分发' : (r.category === 'assignment' ? '作业布置' : '通知消息');
    }
    const unread = rows.filter(r => !r.is_read).length;
    return res.json(success({ list: rows, unread }));
  } catch (e) {
    return res.status(500).json(error('查询失败', 500));
  }
});

// GET /api/learning/inbox/unread-count
router.get('/inbox/unread-count', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT COUNT(*) AS c FROM lc_inbox WHERE user_id = ? AND is_read = 0',
      [req.lcUser.id]
    );
    return res.json(success({ count: rows[0].c }));
  } catch (e) {
    return res.status(500).json(error('查询失败', 500));
  }
});

// POST /api/learning/inbox/read  { ids: [] 或 all: true }
router.post('/inbox/read', lcAuthRequired, async (req, res) => {
  try {
    if (req.body.all) {
      await pool.query('UPDATE lc_inbox SET is_read = 1 WHERE user_id = ?', [req.lcUser.id]);
    } else if (Array.isArray(req.body.ids) && req.body.ids.length > 0) {
      const ids = req.body.ids.map(Number).filter(n => Number.isInteger(n)).slice(0, 500);
      if (ids.length > 0) {
        const placeholders = ids.map(() => '?').join(',');
        await pool.query(
          `UPDATE lc_inbox SET is_read = 1 WHERE user_id = ? AND id IN (${placeholders})`,
          [req.lcUser.id, ...ids]
        );
      }
    }
    return res.json(success({ ok: true }));
  } catch (e) {
    return res.status(500).json(error('操作失败', 500));
  }
});

// ============================================================
// 讲义分发（HTML 文件上传）
// ============================================================

// GET /api/learning/handouts
router.get('/handouts', lcAuthRequired, async (req, res) => {
  try {
    const meRole = req.lcUser.role;
    const isStaff = STAFF_ROLES.includes(meRole);
    const cat = (req.query.category || '').toString();
    const [rows] = await pool.query(
      `SELECT h.id, h.uploader_id, h.title, h.category, h.filename, h.original_name, h.file_size, h.level_scope,
              h.created_at, COALESCE(NULLIF(u.nickname, ''), u.username) AS uploader_name
       FROM lc_handouts h LEFT JOIN lc_users u ON u.id = h.uploader_id
       ORDER BY h.created_at DESC, h.id DESC`
    );
    let visible;
    if (isStaff) {
      visible = rows;
    } else {
      visible = rows.filter(r => {
        let scope;
        try { scope = JSON.parse(r.level_scope); } catch (e) { scope = []; }
        return scope.includes('all') || scope.includes(meRole);
      });
    }
    if (cat) visible = visible.filter(r => (r.category || '') === cat);
    return res.json(success({
      list: visible.map(r => ({ ...r, level_scope: JSON.parse(r.level_scope || '[]') })),
      categories: HANDOUT_CATEGORIES
    }));
  } catch (e) {
    console.error('[learning/handouts:list]', e);
    return res.status(500).json(error('查询失败', 500));
  }
});

// POST /api/learning/handouts （multipart：file + title + levels）
router.post('/handouts', lcAuthRequired, lcRequireStaff, function (req, res, next) {
  upload.single('file')(req, res, function (err) {
    if (err) {
      return res.status(400).json(error('上传失败：' + err.message, 400));
    }
    next();
  });
}, [
  body('title').isLength({ min: 1, max: 128 }).withMessage('标题长度 1-128')
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    if (req.file) fs.unlink(req.file.path, () => {});
    return res.status(400).json(error(errs.array()[0].msg, 400));
  }
  if (!req.file) {
    return res.status(400).json(error('请选择 HTML 文件', 400));
  }
  const levels = parseLevels(req.body.levels || '["all"]');
  if (!levels) {
    fs.unlink(req.file.path, () => {});
    return res.status(400).json(error('分发等级参数无效', 400));
  }
  const category = HANDOUT_CATEGORIES.includes(req.body.category) ? req.body.category : '';
  try {
    const [result] = await pool.query(
      `INSERT INTO lc_handouts (uploader_id, title, category, filename, original_name, file_size, level_scope)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [req.lcUser.id, req.body.title.trim(), category, req.file.filename, req.file.originalname || '', req.file.size, JSON.stringify(levels)]
    );
    const n = await fanoutToLevels(levels, 'handout', result.insertId, '新讲义：' + req.body.title.trim(), req.lcUser.username);
    return res.json(success({ id: result.insertId, notified: n }, '讲义已发布并分发消息'));
  } catch (e) {
    console.error('[learning/handouts:create]', e);
    return res.status(500).json(error('发布失败: ' + e.message, 500));
  }
});

// DELETE /api/learning/handouts/:id （发布者本人或管理员）
router.delete('/handouts/:id', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, uploader_id, filename FROM lc_handouts WHERE id = ? LIMIT 1', [req.params.id]);
    if (rows.length === 0) return res.status(404).json(error('讲义不存在', 404));
    const h = rows[0];
    if (h.uploader_id !== req.lcUser.id && req.lcUser.role !== 'admin') {
      return res.status(403).json(error('无权限删除', 403));
    }
    await pool.query('DELETE FROM lc_handouts WHERE id = ?', [h.id]);
    fs.unlink(path.join(HANDOUTS_DIR, h.filename), () => {});
    return res.json(success({ ok: true }, '讲义已删除'));
  } catch (e) {
    return res.status(500).json(error('删除失败: ' + e.message, 500));
  }
});

// ============================================================
// 作业布置（富文本内容，仅学员四等级）
// ============================================================

// GET /api/learning/assignments
router.get('/assignments', lcAuthRequired, async (req, res) => {
  try {
    const meRole = req.lcUser.role;
    const isStaff = STAFF_ROLES.includes(meRole);
    const [rows] = await pool.query(
      `SELECT a.id, a.uploader_id, a.title, a.level_scope, a.start_at, a.due_at, a.created_at,
              LENGTH(a.content) AS content_len,
              COALESCE(NULLIF(u.nickname, ''), u.username) AS uploader_name
       FROM lc_assignments a LEFT JOIN lc_users u ON u.id = a.uploader_id
       ORDER BY a.created_at DESC, a.id DESC`
    );
    let visible;
    if (isStaff) {
      visible = rows;
    } else {
      visible = rows.filter(r => {
        let scope;
        try { scope = JSON.parse(r.level_scope); } catch (e) { scope = []; }
        return scope.includes(meRole);
      });
    }
    // 提交统计：staff 看各作业提交数；学生看自己是否已交/成绩
    const ids = visible.map(r => r.id);
    const stats = {};
    const mine = {};
    if (ids.length > 0) {
      const ph = ids.map(() => '?').join(',');
      if (isStaff) {
        const [st] = await pool.query(
          `SELECT assignment_id, COUNT(*) AS submitted, SUM(score IS NOT NULL) AS graded
           FROM lc_submissions WHERE assignment_id IN (${ph}) GROUP BY assignment_id`, ids);
        st.forEach(s => { stats[s.assignment_id] = { submitted: s.submitted, graded: Number(s.graded) || 0 }; });
      } else {
        const [ms] = await pool.query(
          `SELECT id, assignment_id, filename, original_name, submitted_at, score, comment, graded_at, graded_by
           FROM lc_submissions WHERE student_id = ? AND assignment_id IN (${ph})`, [req.lcUser.id, ...ids]);
        ms.forEach(s => { mine[s.assignment_id] = s; });
      }
    }
    return res.json(success({
      list: visible.map(r => ({
        ...r,
        level_scope: JSON.parse(r.level_scope || '[]'),
        window: submitWindowStatus(r),
        submit_stat: stats[r.id] || null,
        my_submission: mine[r.id] || null
      }))
    }));
  } catch (e) {
    console.error('[learning/assignments:list]', e);
    return res.status(500).json(error('查询失败', 500));
  }
});

// GET /api/learning/assignments/:id  内容详情
router.get('/assignments/:id', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT a.id, a.uploader_id, a.title, a.content, a.level_scope, a.start_at, a.due_at, a.created_at,
              COALESCE(NULLIF(u.nickname, ''), u.username) AS uploader_name
       FROM lc_assignments a LEFT JOIN lc_users u ON u.id = a.uploader_id
       WHERE a.id = ? LIMIT 1`,
      [req.params.id]
    );
    if (rows.length === 0) return res.status(404).json(error('作业不存在', 404));
    const a = rows[0];
    a.level_scope = JSON.parse(a.level_scope || '[]');
    const isStaff = STAFF_ROLES.includes(req.lcUser.role);
    const canGrade = isStaff && (a.uploader_id === req.lcUser.id || req.lcUser.role === 'admin');
    if (!isStaff && !a.level_scope.includes(req.lcUser.role)) {
      return res.status(403).json(error('该作业不属于你所在的等级', 403));
    }
    // 我的提交（学生本人）
    const [mine] = await pool.query(
      `SELECT id, filename, original_name, file_size, file_ext, submitted_at, score, comment, graded_at, graded_by
       FROM lc_submissions WHERE assignment_id = ? AND student_id = ? LIMIT 1`,
      [a.id, req.lcUser.id]
    );
    return res.json(success({
      ...a,
      window: submitWindowStatus(a),
      canGrade,
      my_submission: mine[0] || null
    }));
  } catch (e) {
    return res.status(500).json(error('查询失败', 500));
  }
});

// ---------- 学生提交作业 ----------
// POST /api/learning/assignments/:id/submit （multipart：file）
router.post('/assignments/:id/submit', lcAuthRequired, function (req, res, next) {
  uploadSubmit.single('file')(req, res, function (err) {
    if (err) {
      return res.status(400).json(error('上传失败：' + err.message, 400));
    }
    next();
  });
}, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id, uploader_id, level_scope, start_at, due_at FROM lc_assignments WHERE id = ? LIMIT 1',
      [req.params.id]
    );
    if (rows.length === 0) {
      if (req.file) fs.unlink(req.file.path, () => {});
      return res.status(404).json(error('作业不存在', 404));
    }
    const a = rows[0];
    let scope;
    try { scope = JSON.parse(a.level_scope); } catch (e) { scope = []; }
    if (STAFF_ROLES.includes(req.lcUser.role)) {
      if (req.file) fs.unlink(req.file.path, () => {});
      return res.status(403).json(error('教师/管理员无需提交作业', 403));
    }
    if (!scope.includes(req.lcUser.role)) {
      if (req.file) fs.unlink(req.file.path, () => {});
      return res.status(403).json(error('该作业不属于你所在的等级', 403));
    }
    const win = submitWindowStatus(a);
    if (win === 'pending') {
      if (req.file) fs.unlink(req.file.path, () => {});
      return res.status(400).json(error('作业尚未开始提交', 400));
    }
    if (win === 'closed') {
      if (req.file) fs.unlink(req.file.path, () => {});
      return res.status(400).json(error('作业已截止，不能再提交，仅可查看', 400));
    }
    if (!req.file) {
      return res.status(400).json(error('请选择要提交的文件', 400));
    }
    const [urows] = await pool.query('SELECT nickname FROM lc_users WHERE id = ? LIMIT 1', [req.lcUser.id]);
    const myNick = (urows[0] && urows[0].nickname) || req.lcUser.username;
    const ext = (path.extname(req.file.originalname || '').toLowerCase().replace('.', '') || '').slice(0, 8);
    const [prev] = await pool.query(
      'SELECT id, filename FROM lc_submissions WHERE assignment_id = ? AND student_id = ? LIMIT 1',
      [a.id, req.lcUser.id]
    );
    const now = Date.now();
    let saved;
    if (prev.length > 0) {
      // 覆盖提交：替换文件并重置成绩
      await pool.query(
        `UPDATE lc_submissions SET filename = ?, original_name = ?, file_size = ?, file_ext = ?,
                submitted_at = ?, score = NULL, comment = NULL, graded_at = NULL, graded_by = ''
         WHERE id = ?`,
        [req.file.filename, req.file.originalname || '', req.file.size, ext, now, prev[0].id]
      );
      fs.unlink(path.join(SUBMISSIONS_DIR, prev[0].filename), () => {});
      saved = prev[0].id;
    } else {
      const [result] = await pool.query(
        `INSERT INTO lc_submissions (assignment_id, student_id, student_username, student_nickname,
            filename, original_name, file_size, file_ext, submitted_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [a.id, req.lcUser.id, req.lcUser.username, myNick,
         req.file.filename, req.file.originalname || '', req.file.size, ext, now]
      );
      saved = result.insertId;
    }
    // 通知发布者（若非本人）
    if (a.uploader_id !== req.lcUser.id) {
      const fname = req.file.originalname || req.file.filename;
      await pool.query(
        `INSERT INTO lc_inbox (user_id, category, ref_id, title, sender_name, content)
         VALUES (?, 'message', 0, ?, ?, ?)`,
        [a.uploader_id, ('学员提交作业：' + myNick).slice(0, 180),
         myNick, (myNick + ' 提交了文件「' + fname + '」，请前往作业批改查看。').slice(0, 500)]
      );
    }
    return res.json(success({ id: saved }, prev.length > 0 ? '已重新提交并覆盖此前版本' : '作业提交成功'));
  } catch (e) {
    console.error('[learning/assignments:submit]', e);
    if (req.file) fs.unlink(req.file.path, () => {});
    return res.status(500).json(error('提交失败: ' + e.message, 500));
  }
});

// ---------- 查看提交列表（发布者或管理员） ----------
// GET /api/learning/assignments/:id/submissions
router.get('/assignments/:id/submissions', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, uploader_id FROM lc_assignments WHERE id = ? LIMIT 1', [req.params.id]);
    if (rows.length === 0) return res.status(404).json(error('作业不存在', 404));
    if (rows[0].uploader_id !== req.lcUser.id && req.lcUser.role !== 'admin') {
      return res.status(403).json(error('仅作业发布者或管理员可查看提交', 403));
    }
    const [list] = await pool.query(
      `SELECT id, student_id, student_username, student_nickname, original_name, file_ext, file_size,
              submitted_at, score, comment, graded_at, graded_by
       FROM lc_submissions WHERE assignment_id = ? ORDER BY submitted_at DESC`,
      [req.params.id]
    );
    return res.json(success({ list }));
  } catch (e) {
    return res.status(500).json(error('查询失败', 500));
  }
});

// ---------- 批改（发布者或管理员） ----------
// POST /api/learning/submissions/:id/grade { score, comment }
router.post('/submissions/:id/grade', lcAuthRequired, [
  body('score').custom(v => v === null || v === '' || (Number.isInteger(Number(v)) && Number(v) >= 0 && Number(v) <= 100)).withMessage('分数需为 0-100 整数或留空'),
  body('comment').optional().isLength({ max: 5000 }).withMessage('评语过长')
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.status(400).json(error(errs.array()[0].msg, 400));
  }
  try {
    const [rows] = await pool.query(
      `SELECT s.id, s.assignment_id, s.student_id, s.student_username, a.title AS assignment_title, a.uploader_id AS assign_uploader_id
       FROM lc_submissions s JOIN lc_assignments a ON a.id = s.assignment_id
       WHERE s.id = ? LIMIT 1`,
      [req.params.id]
    );
    if (rows.length === 0) return res.status(404).json(error('提交记录不存在', 404));
    const s = rows[0];
    if (s.assign_uploader_id !== req.lcUser.id && req.lcUser.role !== 'admin') {
      return res.status(403).json(error('仅作业发布者或管理员可批改', 403));
    }
    const score = (req.body.score === '' || req.body.score === null || req.body.score === undefined) ? null : Number(req.body.score);
    const comment = req.body.comment || '';
    await pool.query(
      'UPDATE lc_submissions SET score = ?, comment = ?, graded_at = ?, graded_by = ? WHERE id = ?',
      [score, comment, Date.now(), req.lcUser.nickname || req.lcUser.username, s.id]
    );
    // 通知学生批改结果
    try {
      const scoreTxt = score === null ? '（未打分）' : '得分 ' + score;
      await pool.query(
        `INSERT INTO lc_inbox (user_id, category, ref_id, title, sender_name, content)
         VALUES (?, 'message', 0, ?, ?, ?)`,
        [s.student_id, ('作业批改：《' + s.assignment_title + '》 ' + scoreTxt).slice(0, 180),
         req.lcUser.nickname || req.lcUser.username,
         (comment || '老师已批改你的作业，' + scoreTxt + '。').slice(0, 5000)]
      );
    } catch (e2) { /* 通知失败不影响批改 */ }
    return res.json(success({ ok: true, score, comment }, '批改已保存并通知学生'));
  } catch (e) {
    console.error('[learning/submissions:grade]', e);
    return res.status(500).json(error('批改失败: ' + e.message, 500));
  }
});

// ---------- 提交文件查看/下载 ----------
// GET /api/learning/submissions/:id/file
router.get('/submissions/:id/file', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT s.id, s.student_id, s.filename, s.original_name, a.uploader_id AS assign_uploader_id
       FROM lc_submissions s JOIN lc_assignments a ON a.id = s.assignment_id
       WHERE s.id = ? LIMIT 1`,
      [req.params.id]
    );
    if (rows.length === 0) return res.status(404).json(error('提交记录不存在', 404));
    const s = rows[0];
    const me = req.lcUser;
    if (s.student_id !== me.id && s.assign_uploader_id !== me.id && me.role !== 'admin') {
      return res.status(403).json(error('无权限查看该文件', 403));
    }
    const filePath = path.join(SUBMISSIONS_DIR, s.filename);
    if (!fs.existsSync(filePath)) return res.status(404).json(error('文件已丢失', 404));
    res.setHeader('Content-Disposition', 'attachment; filename*=UTF-8\'\'' + encodeURIComponent(s.original_name || s.filename));
    return res.sendFile(filePath);
  } catch (e) {
    return res.status(500).json(error('读取失败', 500));
  }
});

// POST /api/learning/assignments
router.post('/assignments', lcAuthRequired, lcRequireStaff, [
  body('title').isLength({ min: 1, max: 128 }).withMessage('标题长度 1-128'),
  body('content').isLength({ min: 1 }).withMessage('作业内容不能为空')
    .custom(v => v.length <= 300000).withMessage('内容过长')
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.status(400).json(error(errs.array()[0].msg, 400));
  }
  const levels = parseLevels(JSON.stringify(req.body.levels || []))?.filter(lv => STUDENT_ROLES.includes(lv));
  if (!levels || levels.length === 0) {
    return res.status(400).json(error('请至少选择一个学员等级（博士/研究生/本科/师承生）', 400));
  }
  // 时间范围（毫秒时间戳，均可选；仅允许正整数，且开始须早于截止）
  let startAt = null, dueAt = null;
  if (req.body.startAt != null && req.body.startAt !== '') {
    startAt = Number(req.body.startAt);
    if (!Number.isFinite(startAt) || startAt <= 0) return res.status(400).json(error('开始时间无效', 400));
  }
  if (req.body.dueAt != null && req.body.dueAt !== '') {
    dueAt = Number(req.body.dueAt);
    if (!Number.isFinite(dueAt) || dueAt <= 0) return res.status(400).json(error('截止时间无效', 400));
  }
  if (startAt && dueAt && startAt >= dueAt) {
    return res.status(400).json(error('开始时间必须早于截止时间', 400));
  }
  // 消息中提示时间窗口（服务器为 UTC，按北京时间 +8 格式化）
  const fmt = ts => {
    const d = new Date(ts + 8 * 3600 * 1000);
    const p = n => String(n).padStart(2, '0');
    return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
  };
  let windowNote = '';
  if (startAt && dueAt) windowNote = `（提交窗口：${fmt(startAt)} 至 ${fmt(dueAt)}）`;
  else if (dueAt) windowNote = `（截止：${fmt(dueAt)}）`;
  else if (startAt) windowNote = `（开始：${fmt(startAt)}）`;
  try {
    const [result] = await pool.query(
      'INSERT INTO lc_assignments (uploader_id, title, content, level_scope, start_at, due_at) VALUES (?, ?, ?, ?, ?, ?)',
      [req.lcUser.id, req.body.title.trim(), req.body.content, JSON.stringify(levels), startAt, dueAt]
    );
    const n = await fanoutToLevels(levels, 'assignment', result.insertId, '新作业：' + req.body.title.trim(), req.lcUser.username, windowNote || null);
    return res.json(success({ id: result.insertId, notified: n }, '作业已发布并分发消息'));
  } catch (e) {
    console.error('[learning/assignments:create]', e);
    return res.status(500).json(error('发布失败: ' + e.message, 500));
  }
});

// DELETE /api/learning/assignments/:id （发布者本人或管理员）
router.delete('/assignments/:id', lcAuthRequired, async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, uploader_id FROM lc_assignments WHERE id = ? LIMIT 1', [req.params.id]);
    if (rows.length === 0) return res.status(404).json(error('作业不存在', 404));
    if (rows[0].uploader_id !== req.lcUser.id && req.lcUser.role !== 'admin') {
      return res.status(403).json(error('无权限删除', 403));
    }
    // 级联清理学生提交文件与记录
    const [subs] = await pool.query('SELECT filename FROM lc_submissions WHERE assignment_id = ?', [rows[0].id]);
    await pool.query('DELETE FROM lc_submissions WHERE assignment_id = ?', [rows[0].id]);
    await pool.query('DELETE FROM lc_assignments WHERE id = ?', [rows[0].id]);
    subs.forEach(s => fs.unlink(path.join(SUBMISSIONS_DIR, s.filename), () => {}));
    return res.json(success({ ok: true }, '作业已删除'));
  } catch (e) {
    return res.status(500).json(error('删除失败: ' + e.message, 500));
  }
});

// ============================================================
// 发送消息（管理员）{ title, content, levels[] } —— 可复选任意等级
// ============================================================
router.post('/messages', lcAuthRequired, lcRequireAdmin, [
  body('title').isLength({ min: 1, max: 120 }).withMessage('标题长度 1-120'),
  body('content').optional().isLength({ max: 100000 })
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.status(400).json(error(errs.array()[0].msg, 400));
  }
  const levels = parseLevels(JSON.stringify(req.body.levels || []));
  if (!levels || levels.length === 0) {
    return res.status(400).json(error('请至少选择一个接收等级', 400));
  }
  try {
    const title = '[管理员消息]' + req.body.title.trim();
    const content = req.body.content || '';
    const n = await fanoutToLevels(levels, 'message', 0, title.slice(0, 180), req.lcUser.username, content);
    return res.json(success({ notified: n, detail: { title: req.body.title.trim(), content, levels } }, '消息已发送'));
  } catch (e) {
    console.error('[learning/messages]', e);
    return res.status(500).json(error('发送失败: ' + e.message, 500));
  }
});

// GET /api/learning/roles  角色字典（供前端下拉使用）
router.get('/roles', lcAuthRequired, (req, res) => {
  return res.json(success({ allRoles: ALL_ROLES, labels: ROLE_LABELS, studentRoles: STUDENT_ROLES, categories: HANDOUT_CATEGORIES }));
});

// ============================================================
// 用户管理（管理员）
// ============================================================

// GET /api/learning/users
router.get('/users', lcAuthRequired, lcRequireAdmin, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT id, username, nickname, role, created_at, last_login FROM lc_users ORDER BY created_at ASC`
    );
    return res.json(success({ list: rows.map(r => ({ ...r, roleLabel: ROLE_LABELS[r.role] })) }));
  } catch (e) {
    return res.status(500).json(error('查询失败', 500));
  }
});

// POST /api/learning/users  新建账号
router.post('/users', lcAuthRequired, lcRequireAdmin, [
  body('username').isLength({ min: 3, max: 32 }).withMessage('用户名长度 3-32')
    .matches(/^[A-Za-z0-9_@.\-]+$/).withMessage('用户名仅限字母数字及 _ @ . -'),
  body('password').isLength({ min: 6, max: 64 }).withMessage('密码长度 6-64'),
  body('role').isIn(ALL_ROLES).withMessage('角色无效'),
  body('nickname').optional().isLength({ max: 64 })
], async (req, res) => {
  const errs = validationResult(req);
  if (!errs.isEmpty()) {
    return res.status(400).json(error(errs.array()[0].msg, 400));
  }
  const { username, password, role, nickname } = req.body;
  try {
    const [exist] = await pool.query('SELECT id FROM lc_users WHERE username = ? LIMIT 1', [username]);
    if (exist.length > 0) return res.status(409).json(error('用户名已存在', 409));
    const hash = await bcrypt.hash(password, 10);
    const [result] = await pool.query(
      'INSERT INTO lc_users (username, password, nickname, role) VALUES (?, ?, ?, ?)',
      [username, hash, nickname || '', role]
    );
    return res.json(success({
      id: result.insertId,
      username,
      role,
      roleLabel: ROLE_LABELS[role]
    }, '账号创建成功'));
  } catch (e) {
    console.error('[learning/users:create]', e);
    return res.status(500).json(error('创建失败: ' + e.message, 500));
  }
});

// PUT /api/learning/users/:id/role
router.put('/users/:id/role', lcAuthRequired, lcRequireAdmin, [
  body('role').isIn(ALL_ROLES)
], async (req, res) => {
  try {
    if (Number(req.params.id) === req.lcUser.id) {
      return res.status(400).json(error('不能修改自己的角色', 400));
    }
    const [result] = await pool.query('UPDATE lc_users SET role = ? WHERE id = ?', [req.body.role, req.params.id]);
    if (result.affectedRows === 0) return res.status(404).json(error('用户不存在', 404));
    return res.json(success({ ok: true, role: req.body.role, roleLabel: ROLE_LABELS[req.body.role] }, '角色已更新'));
  } catch (e) {
    return res.status(500).json(error('更新失败', 500));
  }
});

// PUT /api/learning/users/:id/password
router.put('/users/:id/password', lcAuthRequired, lcRequireAdmin, [
  body('password').isLength({ min: 6, max: 64 }).withMessage('密码长度 6-64')
], async (req, res) => {
  try {
    const hash = await bcrypt.hash(req.body.password, 10);
    const [result] = await pool.query('UPDATE lc_users SET password = ? WHERE id = ?', [hash, req.params.id]);
    if (result.affectedRows === 0) return res.status(404).json(error('用户不存在', 404));
    return res.json(success({ ok: true }, '密码已重置'));
  } catch (e) {
    return res.status(500).json(error('重置失败', 500));
  }
});

// DELETE /api/learning/users/:id
router.delete('/users/:id', lcAuthRequired, lcRequireAdmin, async (req, res) => {
  try {
    if (Number(req.params.id) === req.lcUser.id) {
      return res.status(400).json(error('不能删除自己', 400));
    }
    const [target] = await pool.query('SELECT id, role FROM lc_users WHERE id = ? LIMIT 1', [req.params.id]);
    if (target.length === 0) return res.status(404).json(error('用户不存在', 404));
    if (target[0].role === 'admin') {
      const [[cnt]] = await pool.query("SELECT COUNT(*) AS cnt FROM lc_users WHERE role = 'admin'");
      if (cnt.cnt <= 1) return res.status(400).json(error('需保留至少一名管理员', 400));
    }
    const conn = await pool.getConnection();
    try {
      await conn.beginTransaction();
      // 级联清理该学生的作业提交文件
      const [subs] = await conn.query('SELECT filename FROM lc_submissions WHERE student_id = ?', [req.params.id]);
      await conn.query('DELETE FROM lc_submissions WHERE student_id = ?', [req.params.id]);
      await conn.query('DELETE FROM lc_inbox WHERE user_id = ?', [req.params.id]);
      await conn.query('DELETE FROM lc_users WHERE id = ?', [req.params.id]);
      await conn.commit();
      subs.forEach(s => fs.unlink(path.join(SUBMISSIONS_DIR, s.filename), () => {}));
    } catch (e) {
      await conn.rollback();
      throw e;
    } finally {
      conn.release();
    }
    return res.json(success({ ok: true }, '用户已删除'));
  } catch (e) {
    return res.status(500).json(error('删除失败: ' + e.message, 500));
  }
});

module.exports = router;

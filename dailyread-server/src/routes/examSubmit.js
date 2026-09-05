// 考试系统成绩上报对接：试卷页（HTML 内嵌脚本）POST /api/exam/submit 上报成绩
// 归属规则（成绩关联学习中心账号）：
//   1) 优先按 HttpOnly Cookie lc_token（登录学习中心后自动携带，试卷同源作答）
//      ——成绩归属该账号（student_username=账号 username），卷内姓名仅作展示(student_display)
//   2) 无 Cookie（直接打开试卷未登录）——回退按卷内填写姓名记录（student_username=姓名）
const express = require('express');
const jwt = require('jsonwebtoken');
const { pool } = require('../db');
const config = require('../config');

const router = express.Router();

// 读取同名 Cookie 值
function readCookie(req, name) {
  const h = req.headers.cookie || '';
  const m = new RegExp('(?:^|;\\s*)' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '=([^;]*)').exec(h);
  return m ? decodeURIComponent(m[1]) : '';
}

// 'YYYY-MM-DD HH:mm:ss'（无时区标注的墙上时间）→ 本地 Date（与 learning.js 考试时间解析一致）
function parseLocalDT(str) {
  if (!str) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?$/.exec(String(str).trim());
  if (!m) return null;
  const d = new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0));
  return isNaN(d.getTime()) ? null : d;
}

// POST /api/exam/submit  { type:'exam_result', exam_id, student_name, final_score, ... }
router.post('/submit', async (req, res) => {
  try {
    const body = req.body || {};
    if (body.type !== 'exam_result') {
      return res.status(400).json({ code: 400, message: 'type 必须为 exam_result', data: null });
    }
    const examId = String(body.exam_id == null ? '' : body.exam_id).trim();
    const studentName = String(body.student_name == null ? '' : body.student_name).trim();
    if (!examId || !studentName) {
      return res.status(400).json({ code: 400, message: '缺少 exam_id 或 student_name', data: null });
    }
    // 归属账号（精确到学习中心账号），优先级：
    //   1) 试卷上报显式携带的 student_username（skill 生成的卷会自动附账号，见生成脚本）
    //   2) HttpOnly Cookie lc_token（登录学习中心后自动携带）
    //   3) 回退卷内填写姓名
    let ownerUsername = '';
    let ownerDisplay = studentName;
    const acctName = String(body.student_username == null ? '' : body.student_username).trim();
    if (acctName) {
      ownerUsername = acctName;
    } else {
      const lcTok = readCookie(req, 'lc_token');
      if (lcTok) {
        try {
          const dec = jwt.verify(lcTok, config.jwt.secret);
          if (dec && dec.scope === 'lc' && dec.lcId && dec.username) {
            ownerUsername = dec.username;
          }
        } catch (e) { /* cookie 无效则忽略 */ }
      }
      if (!ownerUsername) {
        ownerUsername = studentName;
      }
    }

    const [exams] = await pool.query(
      `SELECT id,
              DATE_FORMAT(start_at, '%Y-%m-%d %H:%i:%s') AS start_at,
              DATE_FORMAT(end_at, '%Y-%m-%d %H:%i:%s') AS end_at
       FROM lc_exams WHERE exam_code = ? LIMIT 1`,
      [examId]
    );
    if (exams.length === 0) {
      return res.status(404).json({ code: 404, message: '考试不存在', data: null });
    }
    const exam = exams[0];
    // 时间窗口校验：未开始或已截止则成绩不生效
    const now = Date.now();
    const start = parseLocalDT(exam.start_at);
    const end = parseLocalDT(exam.end_at);
    if ((start && now < start.getTime()) || (end && now > end.getTime())) {
      return res.status(400).json({ code: 400, message: '考试未开始或已截止，成绩不生效', data: null });
    }
    // 首次成绩锁定：已有记录直接忽略，不覆盖
    const [exist] = await pool.query(
      'SELECT id FROM lc_exam_scores WHERE exam_id = ? AND student_username = ? LIMIT 1',
      [exam.id, ownerUsername]
    );
    if (exist.length > 0) {
      return res.json({ ok: true, ignored: true });
    }
    const num = v => {
      const n = Number(v);
      return Number.isFinite(n) ? n : 0;
    };
    const submittedAt = String(body.submitted_at == null ? '' : body.submitted_at).slice(0, 32);
    await pool.query(
      `INSERT INTO lc_exam_scores
         (exam_id, student_username, student_display, final_score, total_score, objective_score, objective_max,
          subjective_self, subjective_max, accuracy, submitted_at, detail_json)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        exam.id, ownerUsername, ownerDisplay,
        num(body.final_score), num(body.total_score),
        num(body.objective_score), num(body.objective_max),
        num(body.subjective_self), num(body.subjective_max),
        num(body.accuracy), submittedAt,
        JSON.stringify(body)
      ]
    );
    return res.json({ ok: true });
  } catch (e) {
    console.error('[exam/submit]', e);
    return res.status(500).json({ code: 500, message: '成绩上报失败: ' + e.message, data: null });
  }
});

module.exports = router;

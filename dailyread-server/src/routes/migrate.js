// 数据迁移路由：批量导入旧 JSON 备份
const express = require('express');
const { pool } = require('../db');
const { authRequired } = require('../middleware/auth');
const { success, error } = require('../utils/response');

const router = express.Router();

// POST /api/migrate/import  批量导入旧 JSON 数据
// 请求体：{ articles: [...], checkins: [...] }
router.post('/import', authRequired, async (req, res) => {
  const { articles, checkins } = req.body;
  if (!Array.isArray(articles)) {
    return res.status(400).json(error('articles 需为数组', 400));
  }
  const stats = { articles: { added: 0, updated: 0, skipped: 0 }, checkins: { added: 0, skipped: 0 } };
  const now = new Date().toISOString();

  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();

    for (const a of articles) {
      // 优先使用 clientId（全局唯一标识），兼容旧数据无 clientId 时回退到 id
      const clientId = String(a.clientId || a.id || '');
      if (!clientId || !a.title) {
        stats.articles.skipped++;
        continue;
      }
      try {
        const [exist] = await conn.query(
          'SELECT id FROM articles WHERE user_id = ? AND client_id = ?',
          [req.userId, clientId]
        );
        const values = [
          req.userId, clientId, a.title, a.content || '', a.contentHtml || null, a.chineseChars || 0,
          a.fontFamily || 'default', a.fontSize || 16, a.fontColor || '#000000', a.isBold ? 1 : 0,
          a.isReading !== undefined ? (a.isReading ? 1 : 0) : 1, a.isRequired ? 1 : 0,
          a.requiredDays || '', a.useIndependentCheckRate ? 1 : 0, a.independentCheckRate || 0,
          a.createTime || null, a.isLongArticle ? 1 : 0, a.checkInDays || 0,
          a.completionRate || 0, a.imagewebp || null,
          a.iscontent !== undefined ? (a.iscontent ? 1 : 0) : 1,
          a.lastModified || now
        ];
        const sql = `INSERT INTO articles (
          user_id, client_id, title, content, content_html, chinese_chars,
          font_family, font_size, font_color, is_bold, is_reading, is_required,
          required_days, use_independent_check_rate, independent_check_rate,
          create_time, is_long_article, check_in_days, completion_rate,
          imagewebp, iscontent, last_modified, deleted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON DUPLICATE KEY UPDATE
          title=VALUES(title), content=VALUES(content), content_html=VALUES(content_html),
          chinese_chars=VALUES(chinese_chars), font_family=VALUES(font_family),
          font_size=VALUES(font_size), font_color=VALUES(font_color), is_bold=VALUES(is_bold),
          is_reading=VALUES(is_reading), is_required=VALUES(is_required),
          required_days=VALUES(required_days),
          use_independent_check_rate=VALUES(use_independent_check_rate),
          independent_check_rate=VALUES(independent_check_rate),
          create_time=VALUES(create_time), is_long_article=VALUES(is_long_article),
          check_in_days=VALUES(check_in_days), completion_rate=VALUES(completion_rate),
          imagewebp=VALUES(imagewebp), iscontent=VALUES(iscontent),
          last_modified=VALUES(last_modified), deleted=0`;
        await conn.query(sql, values);
        if (exist.length === 0) stats.articles.added++;
        else stats.articles.updated++;
      } catch (e) {
        stats.articles.skipped++;
      }
    }

    // 打卡记录迁移
    if (Array.isArray(checkins)) {
      for (const c of checkins) {
        try {
          // 找到该用户下 clientId 对应的服务端 articleId
          const clientId = String(c.clientId || c.articleId || '');
          const [aRow] = await conn.query('SELECT id FROM articles WHERE user_id = ? AND client_id = ?', [req.userId, clientId]);
          if (aRow.length === 0) {
            stats.checkins.skipped++;
            continue;
          }
          const articleId = aRow[0].id;
          await conn.query(
            `INSERT INTO checkins (user_id, article_id, check_in_date, check_in_time, last_modified)
             VALUES (?, ?, ?, ?, ?)
             ON DUPLICATE KEY UPDATE check_in_time = VALUES(check_in_time)`,
            [req.userId, articleId, c.checkInDate, c.checkInTime || null, c.lastModified || now]
          );
          stats.checkins.added++;
        } catch (e) {
          stats.checkins.skipped++;
        }
      }
    }

    await conn.commit();
    return res.json(success(stats, '导入完成'));
  } catch (e) {
    await conn.rollback();
    console.error('[migrate/import]', e);
    return res.status(500).json(error('导入失败: ' + e.message, 500));
  } finally {
    conn.release();
  }
});

module.exports = router;

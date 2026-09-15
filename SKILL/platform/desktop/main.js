// yixue-zonghe 个人工作台 · Electron 壳
// 职责：定位技能根与 Python → 拉起 platform/start.py 后端 → 服务就绪后在原生窗口打开界面
const { app, BrowserWindow, dialog, shell, Menu } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const http = require('http');
const net = require('net');

const SKILL_DIR_NAME = 'yixue-zonghe';
const START_READY_TIMEOUT_MS = 60000;

let mainWindow = null;
let backend = null;
let backendPort = null;
let currentSkillRoot = null;

// ==================== 配置读写 ====================

function configPath() {
  return path.join(app.getPath('userData'), 'config.json');
}

function readConfig() {
  try {
    return JSON.parse(fs.readFileSync(configPath(), 'utf8'));
  } catch (e) {
    return {};
  }
}

function writeConfig(patch) {
  const cfg = Object.assign(readConfig(), patch);
  try {
    fs.mkdirSync(path.dirname(configPath()), { recursive: true });
    fs.writeFileSync(configPath(), JSON.stringify(cfg, null, 2), 'utf8');
  } catch (e) { /* 忽略写入失败 */ }
  return cfg;
}

// ==================== 定位技能根 ====================

function isSkillRoot(dir) {
  if (!dir) return false;
  try {
    return fs.existsSync(path.join(dir, 'SKILL.md'))
      && fs.existsSync(path.join(dir, 'platform', 'start.py'));
  } catch (e) {
    return false;
  }
}

function findSkillRoot() {
  const candidates = [];

  // 1) 环境变量
  if (process.env.YIXUE_SKILL_ROOT) candidates.push(process.env.YIXUE_SKILL_ROOT);

  // 2) 上次成功记录
  const cfg = readConfig();
  if (cfg.skillRoot) candidates.push(cfg.skillRoot);

  // 3) 常见安装位置（技能生态的默认落盘目录）
  const home = os.homedir();
  candidates.push(path.join(home, '.workbuddy', 'skills', SKILL_DIR_NAME));
  candidates.push(path.join(home, '.trae-cn', 'skills', SKILL_DIR_NAME));
  candidates.push(path.join(home, '.trae', 'skills', SKILL_DIR_NAME));
  candidates.push(path.join(home, 'Documents', 'SKILL'));
  candidates.push(path.join(home, 'SKILL'));

  // 4) 可执行文件向上若干层（适用于文件夹版 / 开发态）
  let dir = path.dirname(app.getPath('exe'));
  for (let i = 0; i < 7; i++) {
    candidates.push(dir);
    candidates.push(path.join(dir, 'SKILL'));
    candidates.push(path.join(dir, SKILL_DIR_NAME));
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }

  // 5) app 所在目录（开发态）
  candidates.push(path.join(__dirname, '..'));

  for (const c of candidates) {
    if (isSkillRoot(c)) return path.resolve(c);
  }
  return null;
}

function pickSkillRootByDialog() {
  const picked = dialog.showOpenDialogSync({
    title: '请选择 yixue-zonghe 技能目录（内含 SKILL.md 与 platform 文件夹）',
    properties: ['openDirectory'],
  });
  if (!picked || !picked.length) return null;
  const dir = picked[0];
  if (!isSkillRoot(dir)) {
    dialog.showErrorBox(
      '目录无效',
      `所选目录不是有效的技能根：\n${dir}\n\n` +
      '该目录下必须同时存在 SKILL.md 与 platform\\start.py。'
    );
    return null;
  }
  writeConfig({ skillRoot: dir });
  return dir;
}

// ==================== 定位 Python ====================

const DEFAULT_PYTHON = 'C:\\Users\\somnu\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe';

function findPython(skillRoot) {
  const cands = [];
  if (process.env.YIXUE_PYTHON) cands.push(process.env.YIXUE_PYTHON);
  const cfg = readConfig();
  if (cfg.python) cands.push(cfg.python);

  cands.push(DEFAULT_PYTHON);

  // 技能根内可能自带的虚拟环境
  cands.push(path.join(skillRoot, 'platform', '.venv', 'Scripts', 'python.exe'));
  cands.push(path.join(skillRoot, '.venv', 'Scripts', 'python.exe'));

  for (const c of cands) {
    try { if (c && fs.existsSync(c)) return c; } catch (e) { /* skip */ }
  }
  return 'python'; // 交给 PATH
}

// ==================== 端口与就绪探测 ====================

function freePort() {
  return new Promise((resolve) => {
    const srv = net.createServer();
    srv.unref();
    srv.on('error', () => resolve(0));
    srv.listen(0, '127.0.0.1', () => {
      const p = srv.address().port;
      srv.close(() => resolve(p));
    });
  });
}

function ping(port) {
  return new Promise((resolve) => {
    const req = http.get(
      { host: '127.0.0.1', port, path: '/api/overview', timeout: 1500 },
      (res) => {
        res.resume();
        resolve(res.statusCode === 200);
      }
    );
    req.on('timeout', () => { req.destroy(); resolve(false); });
    req.on('error', () => resolve(false));
  });
}

async function waitReady(port, timeoutMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    if (backend && backend.exitCode !== null) return false; // 后端已退出
    if (await ping(port)) return true;
    await new Promise((r) => setTimeout(r, 400));
  }
  return false;
}

// ==================== 拉起后端 ====================

function startBackend(skillRoot, pythonExe, port) {
  const startPy = path.join(skillRoot, 'platform', 'start.py');
  const logDir = app.getPath('userData');
  const logFile = path.join(logDir, 'backend.log');

  let out = '';
  const child = spawn(
    pythonExe,
    [startPy, '--host', '127.0.0.1', '--port', String(port), '--no-browser'],
    { cwd: path.join(skillRoot, 'platform'), windowsHide: true }
  );

  const collect = (buf) => {
    out += buf.toString('utf8');
    if (out.length > 20000) out = out.slice(-20000);
  };
  child.stdout.on('data', collect);
  child.stderr.on('data', collect);

  child.on('exit', (code) => {
    try {
      fs.appendFileSync(logFile, `\n[exit ${code} @ ${new Date().toISOString()}]\n${out}\n`, 'utf8');
    } catch (e) { /* 忽略 */ }
  });

  backend = child;
  backend.getOutput = () => out;
  return child;
}

function killBackend() {
  if (!backend || backend.exitCode !== null) return;
  try {
    // Windows 下递归结束（后端可能派生了子进程）
    spawn('taskkill', ['/pid', String(backend.pid), '/T', '/F'], { windowsHide: true });
  } catch (e) {
    try { backend.kill(); } catch (e2) { /* 忽略 */ }
  }
  backend = null;
}

// ==================== 窗口 ====================

function buildMenu() {
  // 精简菜单：仅供排障与快速打开目录（默认收起，按 Alt 显示）
  const template = [
    {
      label: '视图',
      submenu: [
        { label: '重新加载', role: 'reload' },
        { label: '强制重新加载', role: 'forceReload' },
        { type: 'separator' },
        { label: '开发者工具', role: 'toggleDevTools' },
        { label: '实际大小', role: 'resetZoom' },
        { label: '放大', role: 'zoomIn' },
        { label: '缩小', role: 'zoomOut' },
        { type: 'separator' },
        { label: '全屏切换', role: 'togglefullscreen' },
      ],
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '打开技能目录',
          click: () => { if (currentSkillRoot) shell.openPath(currentSkillRoot); },
        },
        {
          label: '打开数据目录（配置与日志）',
          click: () => shell.openPath(app.getPath('userData')),
        },
        { type: 'separator' },
        {
          label: '关于',
          click: () => {
            dialog.showMessageBox({
              type: 'info',
              title: '关于',
              message: '医学综合 · 个人工作台',
              detail:
                `Electron 壳版本：${app.getVersion()}\n` +
                `Electron：${process.versions.electron}\n\n` +
                `技能目录：${currentSkillRoot || '（未定位）'}\n` +
                `后端端口：${backendPort || '—'}`,
              buttons: ['确定'],
            });
          },
        },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1320,
    height: 860,
    minWidth: 960,
    minHeight: 620,
    show: false,
    backgroundColor: '#f5f7f6',
    title: '医学综合 · 个人工作台',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  buildMenu();

  // 外部链接交给系统浏览器
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.loadFile(path.join(__dirname, 'loading.html'));
  mainWindow.once('ready-to-show', () => mainWindow.show());

  mainWindow.on('closed', () => { mainWindow = null; });
}

// ==================== 主流程 ====================

async function boot() {
  createWindow();

  const skillRoot = findSkillRoot() || pickSkillRootByDialog();
  if (!skillRoot) {
    dialog.showErrorBox(
      '未找到技能目录',
      '未能定位 yixue-zonghe 技能目录。\n\n' +
      '解决办法：设置环境变量 YIXUE_SKILL_ROOT 指向技能目录后重新启动，\n' +
      '或在下次弹窗中手动选择该目录。'
    );
    app.quit();
    return;
  }

  const pythonExe = findPython(skillRoot);
  const port = await freePort();
  backendPort = port || 8770;
  currentSkillRoot = skillRoot;

  startBackend(skillRoot, pythonExe, backendPort);
  const ok = await waitReady(backendPort, START_READY_TIMEOUT_MS);

  if (!ok) {
    const detail = (backend && backend.getOutput && backend.getOutput()) || '（无输出）';
    dialog.showErrorBox(
      '后端启动失败',
      `无法启动本地服务。\n\n技能目录：${skillRoot}\nPython：${pythonExe}\n\n` +
      `后端输出：\n${detail.slice(-1500)}`
    );
    killBackend();
    app.quit();
    return;
  }

  writeConfig({ skillRoot, python: pythonExe });

  if (mainWindow) {
    mainWindow.loadURL(`http://127.0.0.1:${backendPort}/`);
  }
}

// 单实例：重复启动时聚焦已有窗口
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(boot);

  app.on('window-all-closed', () => {
    killBackend();
    app.quit();
  });

  app.on('before-quit', killBackend);

  process.on('exit', killBackend);
}

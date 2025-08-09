#!/usr/bin/env node
/*
  自动安装 ccusage：
  - 优先尝试全局安装：npm install -g ccusage
  - 失败则本地安装：npm install ccusage --save
  - 均失败则输出警告但不阻塞安装
*/
const { spawnSync } = require('node:child_process');
const { existsSync } = require('node:fs');
const { join } = require('node:path');

function log(msg) {
  console.log(`[postinstall] ${msg}`);
}
function warn(msg) {
  console.warn(`[postinstall][warn] ${msg}`);
}
function run(cmd, args, opts = {}) {
  return spawnSync(cmd, args, { stdio: 'inherit', shell: true, ...opts });
}

function hasLocalCcusage() {
  const localBin = join(process.cwd(), 'node_modules', '.bin', process.platform === 'win32' ? 'ccusage.cmd' : 'ccusage');
  return existsSync(localBin);
}

(function main() {
  try {
    log('开始检测/安装 ccusage...');

    // 如果已经存在本地可执行，直接通过
    if (hasLocalCcusage()) {
      log('检测到本地 node_modules/.bin/ccusage，跳过安装');
      return;
    }

    // 尝试全局安装
    log('尝试全局安装: npm install -g ccusage');
    let r = run('npm', ['install', '-g', 'ccusage']);
    if (r.status === 0) {
      log('全局安装 ccusage 成功');
      return;
    }

    // 回退到本地安装
    log('全局安装失败，尝试本地安装: npm install ccusage --save');
    r = run('npm', ['install', 'ccusage', '--save']);
    if (r.status === 0) {
      log('本地安装 ccusage 成功');
      return;
    }

    warn('未能自动安装 ccusage。请手动执行: npm install -g ccusage');
  } catch (e) {
    warn(`postinstall 过程中发生错误: ${e && e.message ? e.message : e}`);
  }
})();

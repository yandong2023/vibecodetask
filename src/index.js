#!/usr/bin/env node

/**
 * VibeCodeTask 主程序入口
 * Claude Code 自动任务管理系统
 */

const { Command } = require('commander');
const chalk = require('chalk');
const figlet = require('figlet');
const VibeCodeTask = require('./core/VibeCodeTask');
const packageJson = require('../package.json');

const program = new Command();

// 显示欢迎横幅
function showBanner() {
  console.log(chalk.cyan(figlet.textSync('VCT', { horizontalLayout: 'full' })));
  console.log(chalk.gray(`VibeCodeTask v${packageJson.version}`));
  console.log(chalk.gray('Claude Code 自动任务管理系统\n'));
}

// 全局错误处理
process.on('uncaughtException', (error) => {
  console.error(chalk.red('\n❌ 未捕获的异常:'), error.message);
  console.error(chalk.gray('详细错误信息请查看日志文件'));
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error(chalk.red('\n❌ 未处理的 Promise 拒绝:'), reason);
  console.error(chalk.gray('在 Promise:'), promise);
  process.exit(1);
});

// 设置程序基本信息
program
  .name('vct')
  .description('Claude Code 自动任务管理系统')
  .version(packageJson.version, '-v, --version', '显示版本号')
  .option('--verbose', '显示详细输出')
  .option('--no-banner', '不显示启动横幅')
  .hook('preAction', (thisCommand) => {
    // 根据选项显示横幅
    if (thisCommand.opts().banner !== false && !thisCommand.args.includes('--help')) {
      showBanner();
    }
  });

// 初始化命令
program
  .command('init')
  .description('初始化配置文件和项目结构')
  .option('-f, --force', '强制覆盖已存在的配置文件')
  .action(async (options) => {
    try {
      const vct = new VibeCodeTask();
      await vct.init(options);
      console.log(chalk.green('✅ 初始化完成！'));
    } catch (error) {
      console.error(chalk.red('❌ 初始化失败:'), error.message);
      process.exit(1);
    }
  });

// 运行任务命令
program
  .command('run')
  .description('运行任务管理器')
  .option('-c, --config <file>', '指定配置文件路径', 'tasks.json')
  .option('--once', '只运行一次，不进入循环模式')
  .option('--daemon', '以守护进程模式运行')
  .action(async (options) => {
    try {
      const vct = new VibeCodeTask(options);
      await vct.initialize();
      
      if (options.once) {
        await vct.runOnce();
      } else if (options.daemon) {
        await vct.startDaemon();
      } else {
        await vct.start();
      }
    } catch (error) {
      console.error(chalk.red('❌ 运行失败:'), error.message);
      process.exit(1);
    }
  });

// 添加任务命令
program
  .command('add')
  .description('添加新任务')
  .argument('<description>', '任务描述')
  .option('-p, --priority <number>', '任务优先级 (1-10)', '5')
  .option('-t, --type <type>', '任务类型', 'development')
  .option('--schedule <schedule>', '调度策略', 'immediate')
  .option('--deps <dependencies>', '依赖任务ID (逗号分隔)')
  .action(async (description, options) => {
    try {
      const vct = new VibeCodeTask();
      await vct.initialize();
      
      const taskData = {
        name: description,
        requirements: description,
        priority: parseInt(options.priority),
        type: options.type,
        schedule: options.schedule
      };
      
      if (options.deps) {
        taskData.dependencies = options.deps.split(',').map(s => s.trim());
      }
      
      const task = await vct.addTask(taskData);
      console.log(chalk.green(`✅ 已添加任务: ${task.name}`));
      console.log(chalk.gray(`   ID: ${task.id}`));
      console.log(chalk.gray(`   优先级: ${task.priority}`));
    } catch (error) {
      console.error(chalk.red('❌ 添加任务失败:'), error.message);
      process.exit(1);
    }
  });

// 列出任务命令
program
  .command('list')
  .alias('ls')
  .description('列出所有任务')
  .option('-s, --status <status>', '按状态筛选 (pending|running|completed|failed)')
  .option('-t, --type <type>', '按类型筛选')
  .option('--json', '以 JSON 格式输出')
  .action(async (options) => {
    try {
      const vct = new VibeCodeTask();
      await vct.initialize();
      
      let tasks = vct.getAllTasks();
      
      // 应用筛选器
      if (options.status) {
        tasks = tasks.filter(t => t.status === options.status);
      }
      
      if (options.type) {
        tasks = tasks.filter(t => t.type === options.type);
      }
      
      if (options.json) {
        console.log(JSON.stringify(tasks, null, 2));
        return;
      }
      
      if (tasks.length === 0) {
        console.log(chalk.yellow('📋 没有找到任务'));
        return;
      }
      
      console.log(chalk.cyan('\n📋 任务列表:\n'));
      
      tasks.forEach(task => {
        const statusIcon = {
          pending: '⏳',
          running: '🔄',
          completed: '✅',
          failed: '❌'
        }[task.status] || '❓';
        
        const priorityColor = task.priority <= 3 ? 'red' : task.priority <= 6 ? 'yellow' : 'green';
        
        console.log(`${statusIcon} ${chalk[priorityColor](`[P${task.priority}]`)} ${chalk.bold(task.name)}`);
        console.log(`   ${chalk.gray('ID:')} ${task.id}`);
        console.log(`   ${chalk.gray('类型:')} ${task.type} | ${chalk.gray('状态:')} ${task.status}`);
        
        if (task.dependencies && task.dependencies.length > 0) {
          console.log(`   ${chalk.gray('依赖:')} ${task.dependencies.join(', ')}`);
        }
        
        if (task.error) {
          console.log(`   ${chalk.red('错误:')} ${task.error}`);
        }
        
        if (task.completedAt) {
          const duration = task.getDuration();
          console.log(`   ${chalk.gray('耗时:')} ${duration ? Math.round(duration / 1000) + 's' : '未知'}`);
        }
        
        console.log();
      });
    } catch (error) {
      console.error(chalk.red('❌ 获取任务列表失败:'), error.message);
      process.exit(1);
    }
  });

// 显示状态命令
program
  .command('status')
  .description('显示系统状态')
  .option('--json', '以 JSON 格式输出')
  .action(async (options) => {
    try {
      const vct = new VibeCodeTask();
      await vct.initialize();
      
      const stats = vct.getStats();
      const usage = await vct.checkUsage();
      
      if (options.json) {
        console.log(JSON.stringify({
          stats,
          usage,
          timestamp: new Date().toISOString()
        }, null, 2));
        return;
      }
      
      console.log(chalk.cyan('\n📊 系统状态:\n'));
      
      // 任务统计
      console.log(chalk.bold('📋 任务统计:'));
      console.log(`   总计: ${stats.total}`);
      console.log(`   ${chalk.yellow('待执行:')} ${stats.pending}`);
      console.log(`   ${chalk.blue('运行中:')} ${stats.running}`);
      console.log(`   ${chalk.green('已完成:')} ${stats.completed}`);
      console.log(`   ${chalk.red('失败:')} ${stats.failed}`);
      
      if (stats.total > 0) {
        const successRate = Math.round((stats.completed / stats.total) * 100);
        console.log(`   ${chalk.gray('成功率:')} ${successRate}%`);
      }
      
      // Claude 使用情况
      if (usage) {
        console.log(chalk.bold('\n🤖 Claude 使用情况:'));
        console.log(`   ${chalk.gray('总额度:')} ${usage.total} blocks`);
        console.log(`   ${chalk.gray('已使用:')} ${usage.used} blocks`);
        console.log(`   ${chalk.gray('剩余:')} ${usage.remaining} blocks`);
        console.log(`   ${chalk.gray('使用率:')} ${usage.percentageUsed}%`);
        
        if (usage.resetTime) {
          console.log(`   ${chalk.gray('重置时间:')} ${usage.resetTime.toLocaleString()}`);
        }
      }
      
      console.log();
      
    } catch (error) {
      console.error(chalk.red('❌ 获取状态失败:'), error.message);
      process.exit(1);
    }
  });

// 显示历史命令
program
  .command('history')
  .description('显示任务执行历史')
  .option('-n, --lines <number>', '显示行数', '20')
  .option('--json', '以 JSON 格式输出')
  .action(async (options) => {
    try {
      const vct = new VibeCodeTask();
      await vct.showHistory(parseInt(options.lines), options.json);
    } catch (error) {
      console.error(chalk.red('❌ 获取历史失败:'), error.message);
      process.exit(1);
    }
  });

// 显示日志命令
program
  .command('logs')
  .description('显示系统日志')
  .option('-n, --lines <number>', '显示行数', '50')
  .option('-f, --follow', '实时跟踪日志')
  .option('--level <level>', '日志级别 (error|warn|info|debug)')
  .action(async (options) => {
    try {
      const vct = new VibeCodeTask();
      await vct.showLogs(options);
    } catch (error) {
      console.error(chalk.red('❌ 获取日志失败:'), error.message);
      process.exit(1);
    }
  });

// 交互模式命令
program
  .command('interactive')
  .alias('i')
  .description('进入交互模式')
  .action(async () => {
    try {
      const vct = new VibeCodeTask();
      await vct.initialize();
      await vct.startInteractiveMode();
    } catch (error) {
      console.error(chalk.red('❌ 启动交互模式失败:'), error.message);
      process.exit(1);
    }
  });

// 停止命令
program
  .command('stop')
  .description('停止运行中的任务管理器')
  .action(async () => {
    try {
      console.log(chalk.yellow('🛑 正在停止任务管理器...'));
      // 这里可以实现向守护进程发送停止信号的逻辑
      console.log(chalk.green('✅ 任务管理器已停止'));
    } catch (error) {
      console.error(chalk.red('❌ 停止失败:'), error.message);
      process.exit(1);
    }
  });

// 检查配额命令
program
  .command('quota')
  .alias('usage')
  .description('检查 Claude 使用配额')
  .action(async () => {
    try {
      const vct = new VibeCodeTask();
      const usage = await vct.checkUsage();
      
      if (usage) {
        console.log(chalk.cyan('\n🤖 Claude 使用情况:\n'));
        console.log(`总额度: ${usage.total} blocks`);
        console.log(`已使用: ${usage.used} blocks`);
        console.log(`剩余: ${usage.remaining} blocks`);
        console.log(`使用率: ${usage.percentageUsed}%`);
        
        if (usage.resetTime) {
          console.log(`重置时间: ${usage.resetTime.toLocaleString()}`);
        }
      } else {
        console.log(chalk.red('❌ 无法获取使用情况'));
        console.log(chalk.gray('请确保 ccusage 命令可用'));
      }
    } catch (error) {
      console.error(chalk.red('❌ 检查配额失败:'), error.message);
      process.exit(1);
    }
  });

// 配置命令
program
  .command('config')
  .description('管理配置')
  .argument('[action]', '操作 (get|set|list)')
  .argument('[key]', '配置键')
  .argument('[value]', '配置值')
  .action(async (action = 'list', key, value) => {
    try {
      const vct = new VibeCodeTask();
      await vct.manageConfig(action, key, value);
    } catch (error) {
      console.error(chalk.red('❌ 配置操作失败:'), error.message);
      process.exit(1);
    }
  });

// 解析命令行参数
program.parse();

// 如果没有提供任何命令，显示帮助
if (process.argv.length === 2) {
  showBanner();
  program.help();
}
/**
 * VibeCodeTask 主要类
 * Claude Code 自动任务管理系统核心实现
 */

const EventEmitter = require('events');
const fs = require('fs').promises;
const path = require('path');
const chalk = require('chalk');
const inquirer = require('inquirer');
const ora = require('ora');

const { TaskManager } = require('./TaskManager');
const { TaskScheduler } = require('./TaskScheduler');
const ClaudeCodeExecutor = require('./ClaudeCodeExecutor');
const PromptOptimizer = require('../prompt/PromptOptimizer');
const Logger = require('../utils/Logger');
const ConfigManager = require('../config/ConfigManager');

class VibeCodeTask extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.options = options;
    this.configFile = options.config || 'tasks.json';
    this.verbose = options.verbose || false;
    
    // 核心组件
    this.taskManager = null;
    this.scheduler = null;
    this.executor = null;
    this.optimizer = null;
    this.logger = null;
    this.config = null;
    
    // 状态
    this.isRunning = false;
    this.isInitialized = false;
  }

  /**
   * 初始化系统
   */
  async initialize() {
    if (this.isInitialized) return;

    const spinner = ora('初始化 VibeCodeTask...').start();

    try {
      // 初始化日志系统
      this.logger = new Logger({
        level: this.verbose ? 'debug' : 'info'
      });
      this.logger.info('开始初始化系统...');

      // 初始化配置管理器
      this.config = new ConfigManager();
      await this.config.load();

      // 初始化任务管理器
      this.taskManager = new TaskManager({
        configFile: this.configFile,
        logger: this.logger
      });
      await this.taskManager.initialize();

      // 初始化 Claude Code 执行器
      this.executor = new ClaudeCodeExecutor({
        logger: this.logger,
        ...this.config.get('claude', {})
      });

      // 检查 Claude Code 可用性
      if (!await this.executor.checkAvailability()) {
        throw new Error('Claude Code CLI 不可用，请确保已正确安装');
      }

      // 初始化提示词优化器
      this.optimizer = new PromptOptimizer({
        logger: this.logger
      });

      // 初始化任务调度器
      this.scheduler = new TaskScheduler({
        taskManager: this.taskManager,
        executor: this.executor,
        optimizer: this.optimizer,
        logger: this.logger,
        ...this.config.get('scheduler', {})
      });

      // 设置事件监听
      this.setupEventListeners();

      this.isInitialized = true;
      spinner.succeed('系统初始化完成');
      
      this.logger.info('VibeCodeTask 初始化成功');

    } catch (error) {
      spinner.fail('初始化失败');
      this.logger.error('初始化失败:', error);
      throw error;
    }
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    // 任务管理器事件
    this.taskManager.on('taskAdded', (task) => {
      this.logger.info(`任务已添加: ${task.name}`);
      console.log(chalk.green(`✅ 任务已添加: ${task.name}`));
    });

    this.taskManager.on('taskStarted', (task) => {
      this.logger.info(`任务开始执行: ${task.name}`);
      console.log(chalk.blue(`🚀 开始执行: ${task.name}`));
    });

    this.taskManager.on('taskCompleted', (task, result) => {
      this.logger.info(`任务执行完成: ${task.name}`);
      console.log(chalk.green(`✅ 任务完成: ${task.name}`));
      
      if (this.verbose && result) {
        console.log(chalk.gray('执行结果:'));
        console.log(result.response?.substring(0, 200) + '...');
      }
    });

    this.taskManager.on('taskFailed', (task, error) => {
      this.logger.error(`任务执行失败: ${task.name}`, error);
      console.log(chalk.red(`❌ 任务失败: ${task.name}`));
      console.log(chalk.red(`   错误: ${error.message}`));
    });

    // 调度器事件
    this.scheduler.on('scheduleStart', () => {
      this.logger.info('任务调度器启动');
      console.log(chalk.cyan('📅 任务调度器已启动'));
    });

    this.scheduler.on('scheduleStop', () => {
      this.logger.info('任务调度器停止');
      console.log(chalk.yellow('📅 任务调度器已停止'));
    });

    this.scheduler.on('quotaInsufficient', (usage) => {
      this.logger.warn('Claude 使用额度不足', usage);
      console.log(chalk.yellow('⚠️ Claude 使用额度不足，等待重置...'));
    });

    // 全局错误处理
    this.on('error', (error) => {
      this.logger.error('系统错误:', error);
      console.error(chalk.red('❌ 系统错误:'), error.message);
    });
  }

  /**
   * 初始化项目配置
   */
  async init(options = {}) {
    const spinner = ora('初始化项目配置...').start();

    try {
      // 检查是否已存在配置文件
      const configExists = await this.fileExists(this.configFile);
      
      if (configExists && !options.force) {
        spinner.stop();
        
        const { overwrite } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'overwrite',
            message: '配置文件已存在，是否覆盖？',
            default: false
          }
        ]);
        
        if (!overwrite) {
          console.log(chalk.yellow('✨ 初始化已取消'));
          return;
        }
        
        spinner.start('覆盖现有配置...');
      }

      // 创建默认配置
      const defaultConfig = {
        tasks: [
          {
            id: 'example-task',
            name: '示例任务',
            priority: 1,
            type: 'development',
            requirements: '这是一个示例任务。请将此任务替换为您的实际需求。',
            schedule: 'immediate'
          }
        ],
        settings: {
          maxConcurrent: 1,
          checkInterval: 300000, // 5分钟
          retryLimit: 3,
          workHours: {
            start: '09:00',
            end: '18:00',
            timezone: 'Asia/Shanghai'
          },
          notifications: {
            onComplete: true,
            onError: true
          }
        }
      };

      await fs.writeFile(this.configFile, JSON.stringify(defaultConfig, null, 2));

      // 创建目录结构
      const dirs = ['logs', 'results', 'templates'];
      for (const dir of dirs) {
        await fs.mkdir(dir, { recursive: true });
      }

      // 创建示例模板
      const exampleTemplate = {
        type: 'development',
        structure: 'detailed',
        prompt: `# 开发任务执行

## 任务目标
{goal}

## 需求分析
{requirements}

## 执行步骤
1. 分析需求和技术选型
2. 设计技术方案
3. 实现核心功能
4. 编写测试用例
5. 完善文档

## 输出要求
- 代码符合最佳实践
- 包含必要的错误处理
- 添加适当的注释
- 提供使用示例

请开始执行任务...`
      };

      await fs.writeFile(
        path.join('templates', 'development.yaml'),
        `type: development\nstructure: detailed\nprompt: |\n  ${exampleTemplate.prompt.split('\n').join('\n  ')}`
      );

      // 创建 .gitignore
      const gitignore = `# Logs
logs/
*.log

# Results
results/
*.result

# Config
.env
config.local.json

# Dependencies
node_modules/

# OS
.DS_Store
Thumbs.db`;

      await fs.writeFile('.gitignore', gitignore);

      spinner.succeed('项目初始化完成');

      console.log(chalk.green('\n🎉 初始化完成！'));
      console.log(chalk.cyan('\n📝 后续步骤:'));
      console.log(`   1. 编辑 ${this.configFile} 添加您的任务`);
      console.log('   2. 运行 vct run 开始执行任务');
      console.log('   3. 运行 vct status 查看系统状态');
      console.log('   4. 运行 vct --help 查看所有命令');

    } catch (error) {
      spinner.fail('初始化失败');
      throw error;
    }
  }

  /**
   * 启动任务管理器
   */
  async start() {
    if (!this.isInitialized) {
      await this.initialize();
    }

    if (this.isRunning) {
      console.log(chalk.yellow('⚠️ 系统已在运行中'));
      return;
    }

    this.logger.info('启动 VibeCodeTask');
    console.log(chalk.cyan('🚀 启动 VibeCodeTask 任务管理器'));

    this.isRunning = true;
    
    try {
      // 启动调度器
      await this.scheduler.start();
      
      // 设置优雅退出处理
      this.setupGracefulShutdown();
      
      console.log(chalk.green('✅ 任务管理器运行中，按 Ctrl+C 停止'));
      
      // 保持进程运行
      await this.keepAlive();
      
    } catch (error) {
      this.isRunning = false;
      this.logger.error('启动失败:', error);
      throw error;
    }
  }

  /**
   * 只运行一次
   */
  async runOnce() {
    if (!this.isInitialized) {
      await this.initialize();
    }

    this.logger.info('运行一次任务检查');
    console.log(chalk.cyan('🔄 执行一次任务检查...'));

    try {
      const result = await this.scheduler.runOnce();
      
      if (result.executed > 0) {
        console.log(chalk.green(`✅ 执行了 ${result.executed} 个任务`));
      } else {
        console.log(chalk.yellow('📋 没有可执行的任务'));
      }

    } catch (error) {
      this.logger.error('执行失败:', error);
      throw error;
    }
  }

  /**
   * 以守护进程模式启动
   */
  async startDaemon() {
    console.log(chalk.cyan('🔧 守护进程模式启动...'));
    
    // 这里可以实现守护进程逻辑
    // 比如使用 pm2 或 自定义守护进程
    
    await this.start();
  }

  /**
   * 启动交互模式
   */
  async startInteractiveMode() {
    if (!this.isInitialized) {
      await this.initialize();
    }

    console.log(chalk.purple('🎮 进入交互模式'));
    console.log(chalk.gray('输入 help 查看命令，输入 quit 退出\n'));

    while (true) {
      try {
        const { command } = await inquirer.prompt([
          {
            type: 'input',
            name: 'command',
            message: chalk.cyan('vct>'),
            prefix: ''
          }
        ]);

        if (!command.trim()) continue;

        const [cmd, ...args] = command.trim().split(' ');

        switch (cmd.toLowerCase()) {
          case 'help':
            this.showInteractiveHelp();
            break;
            
          case 'quit':
          case 'exit':
            console.log(chalk.yellow('👋 退出交互模式'));
            return;
            
          case 'status':
            await this.showStatus();
            break;
            
          case 'list':
            await this.showTaskList();
            break;
            
          case 'run':
            if (args.length === 0) {
              console.log(chalk.red('❌ 请提供任务描述'));
            } else {
              await this.addAndRunTask(args.join(' '));
            }
            break;
            
          case 'quota':
            await this.showQuota();
            break;
            
          default:
            // 当作任务描述处理
            await this.addAndRunTask(command);
        }

      } catch (error) {
        if (error.message.includes('User force closed')) {
          console.log(chalk.yellow('\n👋 退出交互模式'));
          break;
        }
        console.error(chalk.red('❌ 错误:'), error.message);
      }
    }
  }

  /**
   * 添加任务
   */
  async addTask(taskData) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return await this.taskManager.addTask(taskData);
  }

  /**
   * 获取所有任务
   */
  getAllTasks() {
    return this.taskManager.getAllTasks();
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return this.taskManager.getStats();
  }

  /**
   * 检查 Claude 使用情况
   */
  async checkUsage() {
    if (!this.executor) {
      await this.initialize();
    }

    try {
      return await this.executor.getUsage();
    } catch (error) {
      this.logger.warn('获取使用情况失败:', error);
      return null;
    }
  }

  /**
   * 显示历史记录
   */
  async showHistory(lines = 20, json = false) {
    // 实现历史记录显示逻辑
    console.log(chalk.cyan(`📈 显示最近 ${lines} 条历史记录...`));
    
    if (json) {
      // JSON 格式输出
      console.log('[]'); // 临时空数组
    } else {
      console.log(chalk.gray('暂无历史记录'));
    }
  }

  /**
   * 显示日志
   */
  async showLogs(options = {}) {
    console.log(chalk.cyan('📋 显示系统日志...'));
    
    if (this.logger) {
      // 实现日志显示逻辑
      console.log(chalk.gray('日志功能开发中...'));
    }
  }

  /**
   * 配置管理
   */
  async manageConfig(action, key, value) {
    if (!this.config) {
      this.config = new ConfigManager();
      await this.config.load();
    }

    switch (action) {
      case 'get':
        if (key) {
          console.log(this.config.get(key));
        } else {
          console.log('请提供配置键名');
        }
        break;
        
      case 'set':
        if (key && value !== undefined) {
          this.config.set(key, value);
          await this.config.save();
          console.log(chalk.green(`✅ 已设置 ${key} = ${value}`));
        } else {
          console.log(chalk.red('请提供配置键名和值'));
        }
        break;
        
      case 'list':
      default:
        console.log(chalk.cyan('📝 当前配置:'));
        console.log(JSON.stringify(this.config.getAll(), null, 2));
        break;
    }
  }

  // 私有辅助方法

  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  showInteractiveHelp() {
    console.log(chalk.cyan('\n📚 交互模式命令:'));
    console.log('  help                    - 显示此帮助');
    console.log('  status                  - 显示系统状态');
    console.log('  list                    - 列出所有任务');
    console.log('  run <任务描述>          - 添加并执行任务');
    console.log('  quota                   - 检查使用配额');
    console.log('  quit/exit              - 退出交互模式');
    console.log('  <任务描述>             - 直接添加并执行任务');
    console.log();
  }

  async showStatus() {
    const stats = this.getStats();
    const usage = await this.checkUsage();
    
    console.log(chalk.cyan('\n📊 系统状态:'));
    console.log(`任务统计: 总计 ${stats.total}, 待执行 ${stats.pending}, 运行中 ${stats.running}, 已完成 ${stats.completed}, 失败 ${stats.failed}`);
    
    if (usage) {
      console.log(`Claude 配额: ${usage.remaining}/${usage.total} blocks 剩余`);
    }
  }

  async showTaskList() {
    const tasks = this.getAllTasks();
    
    if (tasks.length === 0) {
      console.log(chalk.yellow('📋 没有任务'));
      return;
    }
    
    console.log(chalk.cyan('\n📋 任务列表:'));
    tasks.forEach(task => {
      const statusIcon = { pending: '⏳', running: '🔄', completed: '✅', failed: '❌' }[task.status] || '❓';
      console.log(`${statusIcon} [P${task.priority}] ${task.name}`);
    });
  }

  async showQuota() {
    const usage = await this.checkUsage();
    
    if (usage) {
      console.log(chalk.cyan('\n🤖 Claude 使用情况:'));
      console.log(`剩余: ${usage.remaining}/${usage.total} blocks (${usage.percentageUsed}%)`);
    } else {
      console.log(chalk.red('❌ 无法获取使用情况'));
    }
  }

  async addAndRunTask(description) {
    try {
      const task = await this.addTask({
        name: description,
        requirements: description,
        priority: 5,
        type: 'development',
        schedule: 'immediate'
      });
      
      console.log(chalk.green(`✅ 任务已添加并将执行: ${task.name}`));
    } catch (error) {
      console.error(chalk.red('❌ 添加任务失败:'), error.message);
    }
  }

  setupGracefulShutdown() {
    const shutdown = async (signal) => {
      console.log(chalk.yellow(`\n🛑 接收到 ${signal} 信号，正在优雅关闭...`));
      
      this.isRunning = false;
      
      if (this.scheduler) {
        await this.scheduler.stop();
      }
      
      if (this.logger) {
        this.logger.info('系统正常关闭');
      }
      
      console.log(chalk.green('✅ 系统已安全关闭'));
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));
  }

  async keepAlive() {
    return new Promise((resolve) => {
      const check = () => {
        if (this.isRunning) {
          setTimeout(check, 1000);
        } else {
          resolve();
        }
      };
      check();
    });
  }
}

module.exports = VibeCodeTask;
# Shell 命令执行技术方案

## 1. 核心问题

如何在 Node.js 应用中安全、可靠地执行本地 Shell 命令，特别是 Claude Code CLI 命令。

## 2. Node.js Shell 执行方案

### 2.1 基础实现 - child_process 模块

Node.js 提供了多种执行 Shell 命令的方式：

#### 方式一：exec（适用于简单命令）
```javascript
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function executeCommand(command) {
  try {
    const { stdout, stderr } = await execPromise(command);
    return { success: true, output: stdout, error: stderr };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// 使用示例
const result = await executeCommand('ccusage blocks --live');
```

#### 方式二：spawn（适用于长时间运行的进程）
```javascript
const { spawn } = require('child_process');

function executeStreamCommand(command, args = []) {
  return new Promise((resolve, reject) => {
    const process = spawn(command, args);
    let output = '';
    let errorOutput = '';
    
    process.stdout.on('data', (data) => {
      output += data.toString();
      console.log(`输出: ${data}`);
    });
    
    process.stderr.on('data', (data) => {
      errorOutput += data.toString();
      console.error(`错误: ${data}`);
    });
    
    process.on('close', (code) => {
      if (code === 0) {
        resolve({ output, error: errorOutput });
      } else {
        reject(new Error(`进程退出码: ${code}, 错误: ${errorOutput}`));
      }
    });
  });
}

// 使用示例 - 实时流式输出
await executeStreamCommand('claude', ['--help']);
```

### 2.2 高级 Shell 执行器实现

```javascript
const { exec, spawn } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
const path = require('path');
const fs = require('fs').promises;

class ShellExecutor {
  constructor(options = {}) {
    this.workingDir = options.workingDir || process.cwd();
    this.timeout = options.timeout || 30000; // 30秒超时
    this.maxBuffer = options.maxBuffer || 1024 * 1024 * 10; // 10MB
    this.env = { ...process.env, ...options.env };
  }

  /**
   * 执行简单命令并返回结果
   */
  async execute(command, options = {}) {
    const execOptions = {
      cwd: options.cwd || this.workingDir,
      timeout: options.timeout || this.timeout,
      maxBuffer: options.maxBuffer || this.maxBuffer,
      env: { ...this.env, ...options.env }
    };

    try {
      console.log(`执行命令: ${command}`);
      const { stdout, stderr } = await execPromise(command, execOptions);
      
      return {
        success: true,
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        command: command,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        stdout: error.stdout?.trim() || '',
        stderr: error.stderr?.trim() || '',
        code: error.code,
        command: command,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * 执行交互式命令（支持流式输出）
   */
  async executeInteractive(command, args = [], options = {}) {
    return new Promise((resolve, reject) => {
      const spawnOptions = {
        cwd: options.cwd || this.workingDir,
        env: { ...this.env, ...options.env },
        shell: true
      };

      console.log(`执行交互式命令: ${command} ${args.join(' ')}`);
      const child = spawn(command, args, spawnOptions);
      
      let stdout = '';
      let stderr = '';
      const startTime = Date.now();

      // 设置超时
      const timeout = setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error(`命令超时 (${this.timeout}ms)`));
      }, options.timeout || this.timeout);

      // 处理标准输出
      child.stdout.on('data', (data) => {
        const chunk = data.toString();
        stdout += chunk;
        
        // 实时输出（可选）
        if (options.onStdout) {
          options.onStdout(chunk);
        } else {
          process.stdout.write(chunk);
        }
      });

      // 处理错误输出
      child.stderr.on('data', (data) => {
        const chunk = data.toString();
        stderr += chunk;
        
        // 实时输出（可选）
        if (options.onStderr) {
          options.onStderr(chunk);
        } else {
          process.stderr.write(chunk);
        }
      });

      // 处理进程退出
      child.on('close', (code) => {
        clearTimeout(timeout);
        const duration = Date.now() - startTime;
        
        const result = {
          success: code === 0,
          code: code,
          stdout: stdout.trim(),
          stderr: stderr.trim(),
          command: `${command} ${args.join(' ')}`,
          duration: duration,
          timestamp: new Date().toISOString()
        };

        if (code === 0) {
          resolve(result);
        } else {
          reject(result);
        }
      });

      // 处理错误
      child.on('error', (error) => {
        clearTimeout(timeout);
        reject({
          success: false,
          error: error.message,
          command: `${command} ${args.join(' ')}`,
          timestamp: new Date().toISOString()
        });
      });

      // 支持向进程发送输入
      if (options.input) {
        child.stdin.write(options.input);
        child.stdin.end();
      }
    });
  }

  /**
   * 批量执行命令
   */
  async executeBatch(commands, options = {}) {
    const results = [];
    
    for (const cmd of commands) {
      try {
        const result = await this.execute(cmd, options);
        results.push(result);
        
        // 如果命令失败且设置了停止标志，则停止执行
        if (!result.success && options.stopOnError) {
          break;
        }
      } catch (error) {
        results.push({
          success: false,
          error: error.message,
          command: cmd
        });
        
        if (options.stopOnError) {
          break;
        }
      }
    }
    
    return results;
  }

  /**
   * 执行脚本文件
   */
  async executeScript(scriptPath, args = [], options = {}) {
    const absolutePath = path.resolve(this.workingDir, scriptPath);
    
    // 检查文件是否存在
    try {
      await fs.access(absolutePath);
    } catch (error) {
      throw new Error(`脚本文件不存在: ${absolutePath}`);
    }

    // 根据文件扩展名选择执行器
    const ext = path.extname(scriptPath).toLowerCase();
    let executor = '';
    
    switch (ext) {
      case '.sh':
        executor = 'bash';
        break;
      case '.py':
        executor = 'python';
        break;
      case '.js':
        executor = 'node';
        break;
      default:
        executor = 'sh';
    }

    return this.executeInteractive(executor, [absolutePath, ...args], options);
  }
}

module.exports = ShellExecutor;
```

## 3. Claude Code CLI 专用执行器

```javascript
const ShellExecutor = require('./ShellExecutor');

class ClaudeCodeExecutor extends ShellExecutor {
  constructor(options = {}) {
    super(options);
    this.claudePath = options.claudePath || 'claude'; // Claude CLI 路径
    this.defaultModel = options.model || 'claude-3-opus-20240229';
    this.maxTokens = options.maxTokens || 4096;
  }

  /**
   * 检查 Claude Code 是否可用
   */
  async checkAvailability() {
    try {
      const result = await this.execute(`${this.claudePath} --version`);
      return result.success;
    } catch (error) {
      console.error('Claude Code 不可用:', error);
      return false;
    }
  }

  /**
   * 获取使用情况
   */
  async getUsage() {
    const result = await this.execute('ccusage blocks --live');
    
    if (!result.success) {
      throw new Error(`获取使用情况失败: ${result.error || result.stderr}`);
    }

    return this.parseUsageOutput(result.stdout);
  }

  /**
   * 解析使用情况输出
   */
  parseUsageOutput(output) {
    const usage = {
      totalBlocks: 0,
      usedBlocks: 0,
      remainingBlocks: 0,
      resetTime: null,
      raw: output
    };

    const lines = output.split('\n');
    
    for (const line of lines) {
      // 解析总块数
      if (line.includes('Total blocks') || line.includes('总块数')) {
        const match = line.match(/(\d+)/);
        if (match) usage.totalBlocks = parseInt(match[1]);
      }
      
      // 解析已使用块数
      if (line.includes('Used blocks') || line.includes('已使用')) {
        const match = line.match(/(\d+)/);
        if (match) usage.usedBlocks = parseInt(match[1]);
      }
      
      // 解析重置时间
      if (line.includes('Reset') || line.includes('重置')) {
        const timeMatch = line.match(/(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})/);
        if (timeMatch) {
          usage.resetTime = new Date(timeMatch[1]);
        }
      }
    }
    
    usage.remainingBlocks = usage.totalBlocks - usage.usedBlocks;
    usage.percentageUsed = usage.totalBlocks > 0 
      ? (usage.usedBlocks / usage.totalBlocks * 100).toFixed(2) 
      : 0;
    
    return usage;
  }

  /**
   * 执行 Claude 命令
   */
  async executeClaudeCommand(prompt, options = {}) {
    // 构建命令参数
    const args = [];
    
    // 添加模型参数
    if (options.model || this.defaultModel) {
      args.push('--model', options.model || this.defaultModel);
    }
    
    // 添加 token 限制
    if (options.maxTokens || this.maxTokens) {
      args.push('--max-tokens', String(options.maxTokens || this.maxTokens));
    }
    
    // 添加其他参数
    if (options.temperature) {
      args.push('--temperature', String(options.temperature));
    }
    
    // 添加项目目录（如果指定）
    if (options.project) {
      args.push('--project', options.project);
    }

    // 执行命令
    console.log(`\n执行 Claude 命令...`);
    console.log(`Prompt: ${prompt.substring(0, 100)}...`);
    
    try {
      // 使用交互式执行以支持流式输出
      const result = await this.executeInteractive(
        this.claudePath,
        [...args, prompt],
        {
          timeout: options.timeout || 120000, // 2分钟超时
          onStdout: options.onOutput,
          onStderr: options.onError
        }
      );
      
      return {
        success: true,
        response: result.stdout,
        error: result.stderr,
        duration: result.duration,
        timestamp: result.timestamp
      };
    } catch (error) {
      return {
        success: false,
        error: error.stderr || error.message,
        response: error.stdout || '',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * 执行带文件上下文的 Claude 命令
   */
  async executeWithContext(prompt, files = [], options = {}) {
    // 构建包含文件内容的增强提示词
    let enhancedPrompt = prompt;
    
    if (files.length > 0) {
      enhancedPrompt += '\n\n相关文件内容：\n';
      
      for (const file of files) {
        try {
          const content = await fs.readFile(file, 'utf-8');
          enhancedPrompt += `\n--- ${file} ---\n${content}\n`;
        } catch (error) {
          console.warn(`无法读取文件 ${file}: ${error.message}`);
        }
      }
    }
    
    return this.executeClaudeCommand(enhancedPrompt, options);
  }

  /**
   * 监控使用情况并执行任务
   */
  async executeWithMonitoring(prompt, options = {}) {
    // 执行前检查使用情况
    const usageBefore = await this.getUsage();
    console.log(`执行前使用情况: ${usageBefore.usedBlocks}/${usageBefore.totalBlocks} blocks`);
    
    if (usageBefore.remainingBlocks < 10) {
      throw new Error('剩余额度不足（少于10个blocks）');
    }
    
    // 执行命令
    const result = await this.executeClaudeCommand(prompt, options);
    
    // 执行后检查使用情况
    const usageAfter = await this.getUsage();
    console.log(`执行后使用情况: ${usageAfter.usedBlocks}/${usageAfter.totalBlocks} blocks`);
    
    // 计算本次消耗
    const blocksUsed = usageAfter.usedBlocks - usageBefore.usedBlocks;
    console.log(`本次消耗: ${blocksUsed} blocks`);
    
    return {
      ...result,
      usage: {
        before: usageBefore,
        after: usageAfter,
        consumed: blocksUsed
      }
    };
  }
}

module.exports = ClaudeCodeExecutor;
```

## 4. 安全性考虑

### 4.1 命令注入防护

```javascript
class SecureShellExecutor extends ShellExecutor {
  /**
   * 验证和清理命令参数
   */
  sanitizeInput(input) {
    // 移除潜在的危险字符
    const dangerous = [';', '&&', '||', '|', '`', '$', '>', '<', '&'];
    let sanitized = input;
    
    for (const char of dangerous) {
      sanitized = sanitized.replace(new RegExp(`\\${char}`, 'g'), '');
    }
    
    return sanitized;
  }

  /**
   * 使用参数数组代替字符串拼接
   */
  async executeSafe(command, args = [], options = {}) {
    // 验证命令白名单
    const allowedCommands = ['claude', 'ccusage', 'node', 'npm', 'git'];
    
    if (!allowedCommands.includes(command)) {
      throw new Error(`不允许执行的命令: ${command}`);
    }
    
    // 清理参数
    const safeArgs = args.map(arg => this.sanitizeInput(String(arg)));
    
    // 使用 spawn 执行（更安全）
    return this.executeInteractive(command, safeArgs, options);
  }

  /**
   * 沙箱执行
   */
  async executeInSandbox(command, options = {}) {
    const sandboxOptions = {
      ...options,
      env: {
        PATH: '/usr/local/bin:/usr/bin:/bin', // 限制 PATH
        HOME: '/tmp/sandbox', // 临时目录
        ...options.env
      },
      cwd: '/tmp/sandbox', // 工作目录
      timeout: options.timeout || 10000 // 10秒超时
    };
    
    return this.execute(command, sandboxOptions);
  }
}
```

## 5. 高级错误处理和重试机制

### 5.1 智能重试策略

```javascript
class RobustShellExecutor extends ShellExecutor {
  constructor(options = {}) {
    super(options);
    this.retryConfig = {
      maxRetries: options.maxRetries || 3,
      baseDelay: options.baseDelay || 1000,
      maxDelay: options.maxDelay || 10000,
      backoffFactor: options.backoffFactor || 2,
      jitterRange: options.jitterRange || 0.1
    };
  }

  /**
   * 带智能重试的执行
   */
  async executeWithRetry(command, options = {}, customRetryConfig = {}) {
    const config = { ...this.retryConfig, ...customRetryConfig };
    let lastError;
    let attempt = 0;
    
    while (attempt < config.maxRetries) {
      attempt++;
      
      try {
        console.log(`🔄 尝试执行命令 (${attempt}/${config.maxRetries}): ${command}`);
        const result = await this.execute(command, options);
        
        if (result.success) {
          if (attempt > 1) {
            console.log(`✅ 命令在第${attempt}次尝试后成功执行`);
          }
          return result;
        }
        
        lastError = result;
        
        // 检查是否为可重试的错误
        if (!this.isRetriableError(result)) {
          console.log('❌ 不可重试的错误，停止重试');
          break;
        }
        
        // 计算延迟时间
        if (attempt < config.maxRetries) {
          const delay = this.calculateDelay(attempt, config);
          console.log(`⏳ 等待 ${delay}ms 后重试...`);
          await this.sleep(delay);
        }
        
      } catch (error) {
        lastError = error;
        
        if (!this.isRetriableError(error)) {
          console.log('❌ 致命错误，停止重试');
          break;
        }
      }
    }
    
    // 处理最终失败
    await this.handleExecutionError(lastError, command);
    throw new Error(`命令执行失败（重试${attempt}次）: ${this.getErrorMessage(lastError)}`);
  }

  /**
   * 计算重试延迟（指数退避 + 抖动）
   */
  calculateDelay(attempt, config) {
    const exponentialDelay = Math.min(
      config.baseDelay * Math.pow(config.backoffFactor, attempt - 1),
      config.maxDelay
    );
    
    // 添加随机抖动
    const jitter = exponentialDelay * config.jitterRange * (Math.random() - 0.5);
    return Math.max(0, Math.round(exponentialDelay + jitter));
  }

  /**
   * 判断错误是否可重试
   */
  isRetriableError(error) {
    const nonRetriablePatterns = [
      /command not found/i,
      /permission denied/i,
      /no such file or directory/i,
      /invalid argument/i,
      /syntax error/i
    ];

    const retriablePatterns = [
      /timeout/i,
      /network/i,
      /connection/i,
      /temporary/i,
      /busy/i,
      /rate limit/i
    ];

    const errorMessage = this.getErrorMessage(error);
    
    // 检查非可重试错误
    for (const pattern of nonRetriablePatterns) {
      if (pattern.test(errorMessage)) {
        return false;
      }
    }
    
    // 检查明确可重试的错误
    for (const pattern of retriablePatterns) {
      if (pattern.test(errorMessage)) {
        return true;
      }
    }
    
    // 根据退出码判断
    if (error.code) {
      // 某些退出码表示临时错误
      const retriableCodes = [1, 2, 124, 125, 126, 130];
      return retriableCodes.includes(error.code);
    }
    
    // 默认可重试
    return true;
  }

  /**
   * 智能错误分析和处理
   */
  async handleExecutionError(error, command) {
    const errorMessage = this.getErrorMessage(error);
    console.error(`❌ 命令执行错误: ${command}`);
    console.error(`   错误信息: ${errorMessage}`);
    
    const errorHandlers = [
      {
        pattern: /command not found|not recognized/i,
        severity: 'fatal',
        handler: (error, cmd) => {
          const cmdName = cmd.split(' ')[0];
          console.log(`💡 解决建议:`);
          console.log(`   1. 检查 ${cmdName} 是否已正确安装`);
          console.log(`   2. 确认命令在 PATH 环境变量中`);
          console.log(`   3. 尝试使用完整路径执行命令`);
          
          if (cmdName === 'claude') {
            console.log(`   4. 安装 Claude Code: https://claude.ai/code`);
          }
        }
      },
      {
        pattern: /permission denied|access denied/i,
        severity: 'error',
        handler: (error, cmd) => {
          console.log(`💡 解决建议:`);
          console.log(`   1. 检查文件和目录权限`);
          console.log(`   2. 尝试使用 sudo 运行（如果适用）`);
          console.log(`   3. 确认用户有执行权限`);
          console.log(`   4. 检查文件是否被其他程序锁定`);
        }
      },
      {
        pattern: /timeout|timed out/i,
        severity: 'warning',
        handler: (error, cmd) => {
          console.log(`💡 解决建议:`);
          console.log(`   1. 增加超时时间设置`);
          console.log(`   2. 检查网络连接`);
          console.log(`   3. 优化命令执行效率`);
          console.log(`   4. 考虑拆分为更小的任务`);
        }
      },
      {
        pattern: /no space left|disk full/i,
        severity: 'fatal',
        handler: (error, cmd) => {
          console.log(`💡 解决建议:`);
          console.log(`   1. 清理磁盘空间`);
          console.log(`   2. 删除临时文件和日志`);
          console.log(`   3. 移动数据到其他分区`);
          console.log(`   4. 检查系统存储配置`);
        }
      },
      {
        pattern: /rate limit|too many requests/i,
        severity: 'warning',
        handler: (error, cmd) => {
          console.log(`💡 解决建议:`);
          console.log(`   1. 等待更长时间后重试`);
          console.log(`   2. 降低请求频率`);
          console.log(`   3. 检查 API 配额限制`);
          console.log(`   4. 考虑使用不同的账户或密钥`);
        }
      },
      {
        pattern: /network|connection|dns/i,
        severity: 'warning',
        handler: (error, cmd) => {
          console.log(`💡 解决建议:`);
          console.log(`   1. 检查网络连接`);
          console.log(`   2. 验证 DNS 设置`);
          console.log(`   3. 尝试使用不同的网络`);
          console.log(`   4. 检查防火墙和代理设置`);
        }
      }
    ];

    // 查找匹配的错误处理器
    let handled = false;
    for (const { pattern, severity, handler } of errorHandlers) {
      if (pattern.test(errorMessage)) {
        const icon = severity === 'fatal' ? '🚫' : 
                    severity === 'error' ? '❌' : '⚠️';
        console.log(`${icon} 错误级别: ${severity.toUpperCase()}`);
        handler(error, command);
        handled = true;
        break;
      }
    }

    if (!handled) {
      console.log(`💡 通用建议:`);
      console.log(`   1. 检查命令语法是否正确`);
      console.log(`   2. 验证输入参数`);
      console.log(`   3. 查看详细错误信息`);
      console.log(`   4. 搜索相关解决方案`);
    }

    // 保存错误日志
    await this.logError(error, command);
  }

  /**
   * 记录错误日志
   */
  async logError(error, command) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      command: command,
      error: this.getErrorMessage(error),
      code: error.code,
      signal: error.signal,
      stdout: error.stdout,
      stderr: error.stderr
    };

    try {
      const fs = require('fs').promises;
      const path = require('path');
      
      const logDir = path.join(process.cwd(), 'logs');
      await fs.mkdir(logDir, { recursive: true });
      
      const logFile = path.join(logDir, 'command-errors.log');
      const logLine = JSON.stringify(logEntry) + '\n';
      
      await fs.appendFile(logFile, logLine);
    } catch (logError) {
      console.warn('无法写入错误日志:', logError.message);
    }
  }

  /**
   * 获取统一的错误信息
   */
  getErrorMessage(error) {
    if (typeof error === 'string') return error;
    if (error.message) return error.message;
    if (error.stderr) return error.stderr;
    if (error.stdout) return error.stdout;
    return String(error);
  }

  /**
   * 异步睡眠
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 5.2 命令执行健康监控

```javascript
class HealthMonitor {
  constructor() {
    this.metrics = {
      totalExecutions: 0,
      successfulExecutions: 0,
      failedExecutions: 0,
      totalDuration: 0,
      avgDuration: 0,
      recentErrors: [],
      systemResources: {
        memory: 0,
        cpu: 0,
        disk: 0
      }
    };
    
    this.thresholds = {
      maxErrorRate: 0.2,         // 20% 错误率阈值
      maxAvgDuration: 300000,    // 5分钟平均执行时间阈值
      maxMemoryUsage: 0.8,       // 80% 内存使用率阈值
      maxRecentErrors: 10        // 最近错误数量阈值
    };
  }

  /**
   * 记录命令执行
   */
  recordExecution(command, duration, success, error = null) {
    this.metrics.totalExecutions++;
    this.metrics.totalDuration += duration;
    this.metrics.avgDuration = this.metrics.totalDuration / this.metrics.totalExecutions;

    if (success) {
      this.metrics.successfulExecutions++;
    } else {
      this.metrics.failedExecutions++;
      
      // 记录最近错误
      this.metrics.recentErrors.push({
        timestamp: new Date(),
        command: command,
        error: error,
        duration: duration
      });
      
      // 保持最近错误数量在限制内
      if (this.metrics.recentErrors.length > this.thresholds.maxRecentErrors) {
        this.metrics.recentErrors.shift();
      }
    }

    // 检查健康状态
    this.checkHealth();
  }

  /**
   * 检查系统健康状态
   */
  async checkHealth() {
    const issues = [];

    // 检查错误率
    const errorRate = this.getErrorRate();
    if (errorRate > this.thresholds.maxErrorRate) {
      issues.push({
        type: 'high_error_rate',
        message: `错误率过高: ${(errorRate * 100).toFixed(2)}%`,
        severity: 'warning'
      });
    }

    // 检查平均执行时间
    if (this.metrics.avgDuration > this.thresholds.maxAvgDuration) {
      issues.push({
        type: 'slow_execution',
        message: `平均执行时间过长: ${this.metrics.avgDuration}ms`,
        severity: 'warning'
      });
    }

    // 检查系统资源
    await this.updateSystemResources();
    if (this.metrics.systemResources.memory > this.thresholds.maxMemoryUsage) {
      issues.push({
        type: 'high_memory_usage',
        message: `内存使用率过高: ${(this.metrics.systemResources.memory * 100).toFixed(2)}%`,
        severity: 'critical'
      });
    }

    // 处理健康问题
    if (issues.length > 0) {
      this.handleHealthIssues(issues);
    }
  }

  /**
   * 更新系统资源信息
   */
  async updateSystemResources() {
    try {
      const os = require('os');
      
      // 内存使用率
      const totalMem = os.totalmem();
      const freeMem = os.freemem();
      this.metrics.systemResources.memory = (totalMem - freeMem) / totalMem;
      
      // CPU 使用率（简化版本）
      const cpus = os.cpus();
      this.metrics.systemResources.cpu = os.loadavg()[0] / cpus.length;
      
    } catch (error) {
      console.warn('获取系统资源信息失败:', error.message);
    }
  }

  /**
   * 处理健康问题
   */
  handleHealthIssues(issues) {
    console.warn('🚨 检测到系统健康问题:');
    
    issues.forEach(issue => {
      const icon = issue.severity === 'critical' ? '🔥' : '⚠️';
      console.warn(`${icon} ${issue.message}`);
      
      // 根据问题类型提供解决建议
      switch (issue.type) {
        case 'high_error_rate':
          console.log('   建议: 检查命令配置和系统环境');
          break;
        case 'slow_execution':
          console.log('   建议: 优化命令参数或增加超时时间');
          break;
        case 'high_memory_usage':
          console.log('   建议: 重启系统或关闭不必要的程序');
          break;
      }
    });
  }

  /**
   * 获取错误率
   */
  getErrorRate() {
    if (this.metrics.totalExecutions === 0) return 0;
    return this.metrics.failedExecutions / this.metrics.totalExecutions;
  }

  /**
   * 获取健康报告
   */
  getHealthReport() {
    return {
      timestamp: new Date().toISOString(),
      metrics: { ...this.metrics },
      errorRate: this.getErrorRate(),
      status: this.getHealthStatus(),
      recommendations: this.getRecommendations()
    };
  }

  /**
   * 获取健康状态
   */
  getHealthStatus() {
    const errorRate = this.getErrorRate();
    
    if (errorRate > 0.5) return 'critical';
    if (errorRate > 0.2 || this.metrics.avgDuration > this.thresholds.maxAvgDuration) return 'warning';
    return 'healthy';
  }

  /**
   * 获取改进建议
   */
  getRecommendations() {
    const recommendations = [];
    const errorRate = this.getErrorRate();
    
    if (errorRate > 0.1) {
      recommendations.push('考虑优化命令重试策略');
    }
    
    if (this.metrics.avgDuration > 60000) {
      recommendations.push('考虑拆分长时间运行的命令');
    }
    
    if (this.metrics.recentErrors.length > 5) {
      recommendations.push('检查最近的错误模式，可能需要系统维护');
    }
    
    return recommendations;
  }
}

module.exports = { RobustShellExecutor, HealthMonitor };
```

## 6. 使用示例

```javascript
// 初始化执行器
const executor = new ClaudeCodeExecutor({
  workingDir: process.cwd(),
  timeout: 60000,
  model: 'claude-3-opus-20240229'
});

// 示例1：检查 Claude Code 可用性
const isAvailable = await executor.checkAvailability();
console.log('Claude Code 可用:', isAvailable);

// 示例2：获取使用情况
const usage = await executor.getUsage();
console.log('剩余额度:', usage.remainingBlocks);

// 示例3：执行 Claude 任务
const result = await executor.executeWithMonitoring(
  '请帮我创建一个简单的 Express 服务器',
  {
    maxTokens: 2000,
    temperature: 0.7
  }
);

// 示例4：批量执行命令
const commands = [
  'git status',
  'npm test',
  'npm run build'
];

const results = await executor.executeBatch(commands, {
  stopOnError: true
});

// 示例5：带重试的执行
const robustExecutor = new RobustShellExecutor();
const result = await robustExecutor.executeWithRetry(
  'claude --help',
  {},
  3 // 最多重试3次
);
```

## 7. 跨平台兼容性

```javascript
const os = require('os');

class CrossPlatformExecutor extends ShellExecutor {
  constructor(options = {}) {
    super(options);
    this.platform = os.platform();
    this.isWindows = this.platform === 'win32';
    this.isMac = this.platform === 'darwin';
    this.isLinux = this.platform === 'linux';
  }

  /**
   * 获取平台特定的命令
   */
  getPlatformCommand(command) {
    const commandMap = {
      'clear': {
        win32: 'cls',
        default: 'clear'
      },
      'copy': {
        win32: 'copy',
        default: 'cp'
      },
      'move': {
        win32: 'move',
        default: 'mv'
      },
      'delete': {
        win32: 'del',
        default: 'rm'
      },
      'list': {
        win32: 'dir',
        default: 'ls'
      }
    };

    const mapping = commandMap[command];
    if (mapping) {
      return mapping[this.platform] || mapping.default;
    }
    
    return command;
  }

  /**
   * 执行跨平台命令
   */
  async executeCrossPlatform(command, options = {}) {
    const platformCommand = this.getPlatformCommand(command);
    
    // Windows 特殊处理
    if (this.isWindows) {
      options.shell = 'cmd.exe';
    }
    
    return this.execute(platformCommand, options);
  }

  /**
   * 获取 Claude 可执行文件路径
   */
  getClaudePath() {
    if (this.isWindows) {
      return 'claude.exe';
    }
    return 'claude';
  }
}
```

## 8. 总结

通过以上方案，我们可以实现：

1. **安全可靠的 Shell 命令执行**：使用 Node.js 的 child_process 模块
2. **Claude Code CLI 集成**：专门的执行器处理 Claude 命令
3. **实时监控和流式输出**：支持长时间运行的任务
4. **错误处理和重试机制**：提高系统稳定性
5. **跨平台兼容**：支持 Windows、Mac、Linux
6. **安全防护**：防止命令注入等安全问题

这样系统就能够在本地电脑上自动执行 Claude Code 命令，实现 24 小时无人值守运行。
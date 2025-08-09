# VibeCodeTask 技术方案

## 1. 项目概述

### 1.1 背景与问题

当前使用 Claude Code 进行开发时存在的痛点：
- **时间利用率低**：用户睡觉或离开时，Claude Code 处于闲置状态
- **任务管理分散**：需要手动逐个下达指令，无法批量管理
- **额度浪费**：订阅额度无法 24 小时充分利用
- **执行效率低**：缺乏系统化的任务拆解和执行策略

### 1.2 解决方案

构建一个自动化任务管理系统，实现：
- 任务队列自动化管理
- 基于使用额度的智能调度
- 提示词优化提高执行效率
- 24 小时无人值守运行

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     用户界面层                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ CLI 界面  │  │ 配置文件  │  │ Web UI   │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     应用服务层                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 任务管理器    │  │ 调度引擎      │  │ 监控服务      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     核心引擎层                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 提示词优化器  │  │ 任务执行器    │  │ 额度监控器    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     基础设施层                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Claude Code  │  │ 文件系统      │  │ 日志系统      │ │
│  │     CLI      │  │               │  │               │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心模块设计

#### 2.2.1 任务管理器 (Task Manager)

**职责**：
- 加载和解析任务配置
- 维护任务队列
- 管理任务状态和依赖关系

**核心数据结构**：
```javascript
class Task {
  id: string
  name: string
  priority: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  requirements: string
  dependencies: string[]
  result: any
  createdAt: Date
  startedAt: Date
  completedAt: Date
}

class TaskQueue {
  tasks: Map<string, Task>
  pendingQueue: PriorityQueue<Task>
  runningTasks: Set<string>
  completedTasks: Set<string>
}
```

#### 2.2.2 调度引擎 (Scheduler)

**职责**：
- 根据优先级和依赖关系调度任务
- 监控 Claude Code 使用额度
- 实现不同的调度策略

**调度策略**：
1. **智能调度**：基于额度、优先级、预估时间综合决策
2. **顺序调度**：按配置顺序执行
3. **手动调度**：用户手动触发

**核心算法**：
```javascript
function scheduleNext() {
  // 1. 检查当前运行任务数
  if (runningTasks.size >= maxConcurrent) return
  
  // 2. 获取可用额度
  const usage = await getClaudeUsage()
  if (!hasAvailableQuota(usage)) return
  
  // 3. 选择下一个任务
  const task = selectNextTask(pendingQueue, usage)
  if (!task) return
  
  // 4. 检查依赖
  if (!checkDependencies(task)) return
  
  // 5. 执行任务
  executeTask(task)
}
```

#### 2.2.3 提示词优化器 (Prompt Optimizer)

**职责**：
- 分析原始需求
- 生成结构化技术方案
- 创建细粒度任务清单
- 优化提示词格式

**优化流程**：
```
原始需求 → 需求分析 → 技术方案 → 任务拆解 → 优化提示词
```

**提示词模板**：
```markdown
## 任务目标
[明确的任务目标]

## 技术方案
[详细的实现方案]

## 任务清单
- [ ] 子任务1
- [ ] 子任务2
- [ ] 子任务3

## 执行要求
1. 按顺序完成每个子任务
2. 完成一项后标记为已完成
3. 遇到问题记录并继续下一项
4. 生成执行报告

## 输出格式
请以结构化格式输出结果...
```

#### 2.2.4 额度监控器 (Usage Monitor)

**职责**：
- 调用 `ccusage blocks --live` 获取使用情况
- 解析使用数据
- 预测剩余可用时间

**数据结构**：
```javascript
interface UsageInfo {
  totalBlocks: number
  usedBlocks: number
  remainingBlocks: number
  resetTime: Date
  estimatedTimeRemaining: number
}
```

#### 2.2.5 任务执行器 (Task Executor)

**职责**：
- 调用 Claude Code CLI
- 捕获执行输出
- 处理错误和重试
- 记录执行结果

**执行流程**：
```javascript
async function executeTask(task) {
  // 1. 优化提示词
  const prompt = await optimizePrompt(task)
  
  // 2. 构建命令
  const command = buildClaudeCommand(prompt)
  
  // 3. 执行命令
  const result = await executeCommand(command)
  
  // 4. 解析结果
  const parsed = parseResult(result)
  
  // 5. 更新任务状态
  updateTaskStatus(task, parsed)
  
  // 6. 记录日志
  logExecution(task, result)
}
```

## 3. 技术选型

### 3.1 开发语言与框架
- **主语言**：Node.js (JavaScript/TypeScript)
- **原因**：
  - 与 Claude Code CLI 集成方便
  - 异步处理能力强
  - 生态系统丰富

### 3.2 核心依赖
```json
{
  "dependencies": {
    "node-cron": "^3.0.0",      // 定时任务
    "commander": "^11.0.0",      // CLI 框架
    "winston": "^3.10.0",        // 日志系统
    "p-queue": "^7.3.0",         // 任务队列
    "chalk": "^5.3.0",           // 终端美化
    "inquirer": "^9.2.0",        // 交互式 CLI
    "yaml": "^2.3.0"             // YAML 配置解析
  }
}
```

### 3.3 数据存储
- **配置文件**：JSON/YAML 格式
- **任务状态**：内存 + 文件持久化
- **日志**：文本文件 + 轮转

## 4. 关键功能实现

### 4.1 项目初始化代码

**package.json**:
```json
{
  "name": "vibecodetask",
  "version": "1.0.0",
  "description": "Claude Code 自动任务管理系统",
  "main": "src/index.js",
  "bin": {
    "vibecodetask": "./bin/vct",
    "vct": "./bin/vct"
  },
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "lint": "eslint src/",
    "build": "pkg . --out-path dist/"
  },
  "dependencies": {
    "commander": "^11.0.0",
    "node-cron": "^3.0.2",
    "winston": "^3.10.0",
    "p-queue": "^7.4.1",
    "chalk": "^5.3.0",
    "inquirer": "^9.2.12",
    "yaml": "^2.3.4"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "nodemon": "^3.0.1",
    "eslint": "^8.50.0"
  },
  "keywords": ["claude", "ai", "automation", "task-management"],
  "author": "Your Name",
  "license": "MIT"
}
```

### 4.2 Claude Code 集成

```javascript
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

class ClaudeCodeClient {
  async getUsage() {
    const { stdout } = await execPromise('ccusage blocks --live');
    return this.parseUsage(stdout);
  }
  
  async executePrompt(prompt, options = {}) {
    const command = this.buildCommand(prompt, options);
    const { stdout, stderr } = await execPromise(command);
    return { output: stdout, error: stderr };
  }
  
  buildCommand(prompt, options) {
    // 构建 Claude Code 命令
    let cmd = 'claude';
    if (options.model) cmd += ` --model ${options.model}`;
    if (options.maxTokens) cmd += ` --max-tokens ${options.maxTokens}`;
    cmd += ` "${prompt.replace(/"/g, '\\"')}"`;
    return cmd;
  }
  
  parseUsage(output) {
    // 解析 ccusage blocks --live 输出
    const lines = output.split('\n');
    const usage = {};
    lines.forEach(line => {
      if (line.includes('Total blocks')) {
        usage.total = parseInt(line.match(/\d+/)[0]);
      }
      if (line.includes('Used blocks')) {
        usage.used = parseInt(line.match(/\d+/)[0]);
      }
      if (line.includes('Reset time')) {
        usage.resetTime = new Date(line.split(':').slice(1).join(':').trim());
      }
    });
    usage.remaining = usage.total - usage.used;
    return usage;
  }
}
```

### 4.2 任务调度实现

```javascript
const cron = require('node-cron');
const PQueue = require('p-queue').default;

class TaskScheduler {
  constructor() {
    this.queue = new PQueue({ concurrency: 1 });
    this.tasks = new Map();
    this.cronJob = null;
  }
  
  start() {
    // 每5分钟检查一次
    this.cronJob = cron.schedule('*/5 * * * *', async () => {
      await this.checkAndSchedule();
    });
  }
  
  async checkAndSchedule() {
    // 1. 检查使用额度
    const usage = await this.claudeClient.getUsage();
    if (usage.remaining < MIN_BLOCKS_REQUIRED) {
      console.log('额度不足，等待重置...');
      return;
    }
    
    // 2. 获取待执行任务
    const pendingTasks = this.getPendingTasks();
    if (pendingTasks.length === 0) {
      console.log('没有待执行任务');
      return;
    }
    
    // 3. 选择任务执行
    const task = this.selectTask(pendingTasks, usage);
    if (task) {
      await this.executeTask(task);
    }
  }
  
  selectTask(tasks, usage) {
    // 根据优先级、预估时间、额度选择任务
    return tasks
      .filter(t => this.canExecute(t, usage))
      .sort((a, b) => a.priority - b.priority)[0];
  }
  
  canExecute(task, usage) {
    // 检查依赖和额度
    const depsCompleted = task.dependencies.every(
      depId => this.tasks.get(depId)?.status === 'completed'
    );
    const hasEnoughQuota = usage.remaining >= task.estimatedBlocks;
    return depsCompleted && hasEnoughQuota;
  }
}
```

### 4.3 提示词优化实现

```javascript
const fs = require('fs').promises;
const path = require('path');

class PromptOptimizer {
  constructor() {
    this.templates = new Map();
    this.loadTemplates();
  }

  async loadTemplates() {
    // 加载提示词模板
    const templatesDir = path.join(__dirname, '../templates');
    try {
      const files = await fs.readdir(templatesDir);
      for (const file of files) {
        if (file.endsWith('.yaml')) {
          const content = await fs.readFile(path.join(templatesDir, file), 'utf-8');
          const template = yaml.load(content);
          this.templates.set(template.type, template);
        }
      }
    } catch (error) {
      console.warn('未能加载提示词模板:', error.message);
    }
  }

  optimize(task) {
    const analysis = this.analyzeRequirements(task.requirements);
    const plan = this.generatePlan(analysis, task.type);
    const checklist = this.createChecklist(plan);
    const template = this.getTemplate(task.type);
    
    return this.buildOptimizedPrompt({
      goal: task.name,
      requirements: analysis,
      plan: plan,
      checklist: checklist,
      template: template,
      context: task.context || {}
    });
  }
  
  analyzeRequirements(requirements) {
    // 使用正则表达式和 NLP 技术分析需求
    return {
      mainGoal: this.extractMainGoal(requirements),
      constraints: this.extractConstraints(requirements),
      expectedOutputs: this.extractOutputs(requirements),
      technologies: this.extractTechnologies(requirements),
      complexity: this.assessComplexity(requirements)
    };
  }

  extractMainGoal(requirements) {
    // 提取主要目标
    const goalKeywords = ['创建', '实现', '构建', '开发', '设计', '优化', '重构'];
    const sentences = requirements.split(/[。.!！]/);
    
    for (const sentence of sentences) {
      for (const keyword of goalKeywords) {
        if (sentence.includes(keyword)) {
          return sentence.trim();
        }
      }
    }
    
    return sentences[0]?.trim() || requirements.substring(0, 100);
  }

  extractConstraints(requirements) {
    // 提取约束条件
    const constraints = [];
    const constraintPatterns = [
      /必须使用\s*([^，,。.]+)/g,
      /不能使用\s*([^，,。.]+)/g,
      /需要支持\s*([^，,。.]+)/g,
      /兼容\s*([^，,。.]+)/g
    ];

    constraintPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(requirements)) !== null) {
        constraints.push(match[1].trim());
      }
    });

    return constraints;
  }

  extractTechnologies(requirements) {
    // 提取技术栈
    const techKeywords = [
      'React', 'Vue', 'Angular', 'Node.js', 'Express', 'Next.js',
      'TypeScript', 'JavaScript', 'Python', 'Django', 'Flask',
      'Docker', 'Kubernetes', 'AWS', 'MongoDB', 'PostgreSQL',
      'Redis', 'GraphQL', 'REST API'
    ];

    return techKeywords.filter(tech => 
      requirements.toLowerCase().includes(tech.toLowerCase())
    );
  }

  assessComplexity(requirements) {
    // 评估复杂度
    const complexityIndicators = {
      simple: ['创建', '生成', '添加'],
      medium: ['重构', '优化', '集成', '配置'],
      complex: ['架构', '系统', '平台', '框架']
    };

    for (const [level, indicators] of Object.entries(complexityIndicators)) {
      if (indicators.some(indicator => requirements.includes(indicator))) {
        return level;
      }
    }

    return 'simple';
  }
  
  generatePlan(analysis, taskType = 'development') {
    // 根据任务类型生成计划
    const planGenerators = {
      development: this.generateDevelopmentPlan.bind(this),
      testing: this.generateTestingPlan.bind(this),
      documentation: this.generateDocumentationPlan.bind(this),
      refactoring: this.generateRefactoringPlan.bind(this)
    };

    const generator = planGenerators[taskType] || planGenerators.development;
    return generator(analysis);
  }

  generateDevelopmentPlan(analysis) {
    const steps = [];
    
    // 根据复杂度生成不同的步骤
    switch (analysis.complexity) {
      case 'simple':
        steps.push(
          { description: '分析需求和技术选型', validation: '确认技术栈' },
          { description: '创建项目结构', validation: '验证文件结构' },
          { description: '实现核心功能', validation: '功能测试' },
          { description: '完善错误处理', validation: '异常测试' }
        );
        break;
      
      case 'complex':
        steps.push(
          { description: '需求分析和架构设计', validation: '架构评审' },
          { description: '创建项目脚手架', validation: '环境验证' },
          { description: '实现核心模块', validation: '单元测试' },
          { description: '集成各模块', validation: '集成测试' },
          { description: '性能优化', validation: '性能测试' },
          { description: '文档和部署', validation: '部署验证' }
        );
        break;
      
      default: // medium
        steps.push(
          { description: '分析需求和设计方案', validation: '方案确认' },
          { description: '搭建开发环境', validation: '环境测试' },
          { description: '实现主要功能', validation: '功能验证' },
          { description: '添加测试用例', validation: '测试通过' },
          { description: '代码优化和重构', validation: '代码审查' }
        );
    }

    return {
      approach: this.determineApproach(analysis),
      steps: steps,
      considerations: this.identifyConsiderations(analysis)
    };
  }

  generateTestingPlan(analysis) {
    return {
      approach: '采用 TDD 方法编写全面的测试用例',
      steps: [
        { description: '分析测试需求', validation: '测试计划确认' },
        { description: '设计测试用例', validation: '用例评审' },
        { description: '编写单元测试', validation: '单元测试通过' },
        { description: '编写集成测试', validation: '集成测试通过' },
        { description: '生成测试报告', validation: '覆盖率达标' }
      ],
      considerations: ['测试覆盖率', '边界条件', '异常处理', '性能测试']
    };
  }

  getTemplate(taskType) {
    return this.templates.get(taskType) || this.templates.get('default') || {
      structure: 'basic'
    };
  }
  
  createChecklist(plan) {
    // 创建详细的任务清单
    return plan.steps.map((step, index) => ({
      id: `step-${index + 1}`,
      description: step.description,
      validation: step.validation,
      completed: false,
      estimatedTime: this.estimateStepTime(step.description)
    }));
  }

  estimateStepTime(description) {
    // 基于任务描述估算时间
    const timeIndicators = {
      '分析|设计|规划': 30,
      '创建|搭建|初始化': 15,
      '实现|开发|编写': 60,
      '测试|验证|检查': 30,
      '优化|重构|改进': 45,
      '部署|发布|配置': 20
    };

    for (const [pattern, minutes] of Object.entries(timeIndicators)) {
      if (new RegExp(pattern).test(description)) {
        return `${minutes}m`;
      }
    }

    return '30m';
  }
  
  buildOptimizedPrompt(data) {
    const { goal, requirements, plan, checklist, template, context } = data;
    
    // 构建上下文信息
    let contextInfo = '';
    if (context.workspace) {
      contextInfo += `\n工作目录: ${context.workspace}`;
    }
    if (context.files && context.files.length > 0) {
      contextInfo += `\n相关文件: ${context.files.join(', ')}`;
    }

    return `# 🎯 任务：${goal}

## 📋 需求分析
**主要目标**: ${requirements.mainGoal}
**技术栈**: ${requirements.technologies.join(', ') || '根据需求选择'}
**复杂度**: ${requirements.complexity}
${requirements.constraints.length > 0 ? `**约束条件**: ${requirements.constraints.join(', ')}` : ''}
${contextInfo}

## 🔧 技术方案
${plan.approach}

### 关键考虑点
${plan.considerations.map(c => `- ${c}`).join('\n')}

## 📝 执行步骤
${plan.steps.map((s, i) => `### ${i + 1}. ${s.description}
- **验证标准**: ${s.validation}
- **预计时间**: ${this.estimateStepTime(s.description)}
`).join('\n')}

## ✅ 任务清单
${checklist.map(item => `- [ ] ${item.description} (${item.estimatedTime})`).join('\n')}

## 📖 执行要求
1. **分步执行**: 严格按照步骤顺序执行
2. **进度报告**: 每完成一步，输出 "✅ 已完成：{步骤描述}"
3. **错误处理**: 遇到错误时记录详细信息，尝试解决后继续
4. **代码规范**: 遵循最佳实践和编码规范
5. **测试验证**: 每个功能完成后进行相应测试
6. **文档更新**: 更新相关文档和注释

## 🎪 输出格式
请按以下格式输出结果：

\`\`\`
## 执行摘要
- 任务状态: [完成/部分完成/失败]
- 完成步骤: X/Y
- 耗时: XX分钟

## 主要成果
- 创建的文件: [文件列表]
- 实现的功能: [功能列表]
- 解决的问题: [问题列表]

## 遇到的问题
[如有问题，详细描述]

## 后续建议
[优化建议或下一步工作]
\`\`\`

🚀 **现在开始执行任务...**`;
  }
}

module.exports = PromptOptimizer;
```

## 5. 部署与运维

### 5.1 部署方式

1. **本地部署**
   ```bash
   git clone <repository>
   npm install
   npm run build
   npm start
   ```

2. **Docker 部署**
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   CMD ["npm", "start"]
   ```

3. **系统服务**
   ```bash
   # 使用 systemd
   sudo cp vibecodetask.service /etc/systemd/system/
   sudo systemctl enable vibecodetask
   sudo systemctl start vibecodetask
   ```

### 5.2 监控与日志

- **日志级别**：ERROR, WARN, INFO, DEBUG
- **日志轮转**：每日轮转，保留 30 天
- **监控指标**：
  - 任务成功率
  - 平均执行时间
  - 额度使用率
  - 系统资源占用

### 5.3 错误处理

1. **重试机制**：失败任务自动重试 3 次
2. **降级策略**：额度不足时延迟执行
3. **告警通知**：关键错误发送通知
4. **故障恢复**：崩溃后自动恢复任务状态

### 4.4 完整的任务管理器实现

```javascript
// src/core/TaskManager.js
const EventEmitter = require('events');
const fs = require('fs').promises;
const path = require('path');

class TaskManager extends EventEmitter {
  constructor(options = {}) {
    super();
    this.configFile = options.configFile || 'tasks.json';
    this.tasks = new Map();
    this.runningTasks = new Set();
    this.completedTasks = new Set();
    this.maxConcurrent = options.maxConcurrent || 1;
    this.autosave = options.autosave !== false;
  }

  async initialize() {
    await this.loadTasks();
    this.emit('initialized');
  }

  async loadTasks() {
    try {
      if (await this.fileExists(this.configFile)) {
        const data = await fs.readFile(this.configFile, 'utf-8');
        const config = JSON.parse(data);
        
        for (const taskData of config.tasks || []) {
          const task = new Task(taskData);
          this.tasks.set(task.id, task);
        }
        
        console.log(`已加载 ${this.tasks.size} 个任务`);
      } else {
        console.log('配置文件不存在，创建默认配置');
        await this.createDefaultConfig();
      }
    } catch (error) {
      console.error('加载任务失败:', error);
      throw error;
    }
  }

  async saveTasks() {
    const config = {
      tasks: Array.from(this.tasks.values()).map(task => task.toJSON()),
      lastUpdated: new Date().toISOString()
    };

    await fs.writeFile(this.configFile, JSON.stringify(config, null, 2));
  }

  async addTask(taskData) {
    const task = new Task(taskData);
    this.tasks.set(task.id, task);
    
    if (this.autosave) {
      await this.saveTasks();
    }
    
    this.emit('taskAdded', task);
    return task;
  }

  getTask(id) {
    return this.tasks.get(id);
  }

  getAllTasks() {
    return Array.from(this.tasks.values());
  }

  getPendingTasks() {
    return this.getAllTasks()
      .filter(task => task.status === 'pending')
      .sort((a, b) => a.priority - b.priority);
  }

  getNextTask() {
    const pendingTasks = this.getPendingTasks();
    
    for (const task of pendingTasks) {
      if (this.canExecuteTask(task)) {
        return task;
      }
    }
    
    return null;
  }

  canExecuteTask(task) {
    // 检查并发限制
    if (this.runningTasks.size >= this.maxConcurrent) {
      return false;
    }

    // 检查依赖
    if (task.dependencies && task.dependencies.length > 0) {
      return task.dependencies.every(depId => {
        const depTask = this.tasks.get(depId);
        return depTask && depTask.status === 'completed';
      });
    }

    return true;
  }

  async executeTask(task) {
    if (this.runningTasks.has(task.id)) {
      throw new Error(`任务 ${task.id} 已在运行中`);
    }

    this.runningTasks.add(task.id);
    task.status = 'running';
    task.startedAt = new Date();

    this.emit('taskStarted', task);

    try {
      const result = await this.runTask(task);
      
      task.status = 'completed';
      task.completedAt = new Date();
      task.result = result;
      
      this.runningTasks.delete(task.id);
      this.completedTasks.add(task.id);
      
      if (this.autosave) {
        await this.saveTasks();
      }
      
      this.emit('taskCompleted', task, result);
      return result;

    } catch (error) {
      task.status = 'failed';
      task.error = error.message;
      task.completedAt = new Date();
      
      this.runningTasks.delete(task.id);
      
      if (this.autosave) {
        await this.saveTasks();
      }
      
      this.emit('taskFailed', task, error);
      throw error;
    }
  }

  async runTask(task) {
    // 这里会被具体的执行器实现覆盖
    throw new Error('runTask method must be implemented by subclass');
  }

  getStats() {
    const all = this.getAllTasks();
    return {
      total: all.length,
      pending: all.filter(t => t.status === 'pending').length,
      running: all.filter(t => t.status === 'running').length,
      completed: all.filter(t => t.status === 'completed').length,
      failed: all.filter(t => t.status === 'failed').length
    };
  }

  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async createDefaultConfig() {
    const defaultConfig = {
      tasks: [
        {
          id: 'example-task',
          name: '示例任务',
          priority: 1,
          type: 'development',
          requirements: '这是一个示例任务，请替换为您的实际需求',
          schedule: 'immediate'
        }
      ],
      settings: {
        maxConcurrent: 1,
        checkInterval: 300000,
        retryLimit: 3
      }
    };

    await fs.writeFile(this.configFile, JSON.stringify(defaultConfig, null, 2));
  }
}

// Task 类定义
class Task {
  constructor(data) {
    this.id = data.id || this.generateId();
    this.name = data.name;
    this.priority = data.priority || 99;
    this.type = data.type || 'development';
    this.requirements = data.requirements;
    this.status = data.status || 'pending';
    this.dependencies = data.dependencies || [];
    this.schedule = data.schedule || 'immediate';
    this.estimatedTime = data.estimatedTime;
    this.context = data.context || {};
    this.retryCount = 0;
    this.maxRetries = data.maxRetries || 3;
    
    // 时间戳
    this.createdAt = data.createdAt ? new Date(data.createdAt) : new Date();
    this.startedAt = data.startedAt ? new Date(data.startedAt) : null;
    this.completedAt = data.completedAt ? new Date(data.completedAt) : null;
    
    // 结果
    this.result = data.result;
    this.error = data.error;
  }

  generateId() {
    return `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  toJSON() {
    return {
      id: this.id,
      name: this.name,
      priority: this.priority,
      type: this.type,
      requirements: this.requirements,
      status: this.status,
      dependencies: this.dependencies,
      schedule: this.schedule,
      estimatedTime: this.estimatedTime,
      context: this.context,
      retryCount: this.retryCount,
      maxRetries: this.maxRetries,
      createdAt: this.createdAt?.toISOString(),
      startedAt: this.startedAt?.toISOString(),
      completedAt: this.completedAt?.toISOString(),
      result: this.result,
      error: this.error
    };
  }

  canRetry() {
    return this.retryCount < this.maxRetries;
  }

  incrementRetry() {
    this.retryCount++;
  }

  getDuration() {
    if (this.startedAt && this.completedAt) {
      return this.completedAt - this.startedAt;
    }
    return null;
  }
}

module.exports = { TaskManager, Task };
```

### 4.5 主程序入口

```javascript
// src/index.js
#!/usr/bin/env node

const { Command } = require('commander');
const VibeCodeTask = require('./VibeCodeTask');
const chalk = require('chalk');
const packageJson = require('../package.json');

const program = new Command();

program
  .name('vct')
  .description('Claude Code 自动任务管理系统')
  .version(packageJson.version);

program
  .command('init')
  .description('初始化配置文件')
  .action(async () => {
    const vct = new VibeCodeTask();
    await vct.init();
    console.log(chalk.green('✅ 配置文件已创建'));
  });

program
  .command('run')
  .description('运行任务')
  .option('-c, --config <file>', '配置文件路径', 'tasks.json')
  .option('--once', '只运行一次')
  .action(async (options) => {
    const vct = new VibeCodeTask(options);
    
    if (options.once) {
      await vct.runOnce();
    } else {
      await vct.start();
    }
  });

program
  .command('add <description>')
  .description('添加新任务')
  .option('-p, --priority <number>', '优先级', 5)
  .option('-t, --type <type>', '任务类型', 'development')
  .action(async (description, options) => {
    const vct = new VibeCodeTask();
    await vct.initialize();
    
    const task = await vct.addTask({
      name: description,
      requirements: description,
      priority: parseInt(options.priority),
      type: options.type
    });
    
    console.log(chalk.green(`✅ 已添加任务: ${task.name}`));
  });

program
  .command('list')
  .description('列出所有任务')
  .action(async () => {
    const vct = new VibeCodeTask();
    await vct.initialize();
    
    const tasks = vct.getAllTasks();
    
    if (tasks.length === 0) {
      console.log('没有任务');
      return;
    }
    
    console.log('\n📋 任务列表:\n');
    
    tasks.forEach(task => {
      const status = task.status === 'completed' ? '✅' :
                   task.status === 'running' ? '🔄' :
                   task.status === 'failed' ? '❌' : '⏳';
      
      console.log(`${status} [${task.priority}] ${task.name}`);
      console.log(`   类型: ${task.type} | 状态: ${task.status}`);
      if (task.error) {
        console.log(chalk.red(`   错误: ${task.error}`));
      }
      console.log();
    });
  });

program
  .command('status')
  .description('显示系统状态')
  .action(async () => {
    const vct = new VibeCodeTask();
    await vct.initialize();
    
    const stats = vct.getStats();
    const usage = await vct.checkUsage();
    
    console.log('\n📊 系统状态:\n');
    console.log(`任务统计:`);
    console.log(`  总计: ${stats.total}`);
    console.log(`  待执行: ${chalk.yellow(stats.pending)}`);
    console.log(`  运行中: ${chalk.blue(stats.running)}`);
    console.log(`  已完成: ${chalk.green(stats.completed)}`);
    console.log(`  失败: ${chalk.red(stats.failed)}`);
    
    if (usage) {
      console.log(`\nClaude 使用情况:`);
      console.log(`  剩余额度: ${usage.remaining}/${usage.total} blocks`);
      console.log(`  使用率: ${usage.percentageUsed}%`);
    }
  });

program
  .command('logs')
  .description('显示日志')
  .option('-n, --lines <number>', '显示行数', 20)
  .action(async (options) => {
    const vct = new VibeCodeTask();
    await vct.showLogs(parseInt(options.lines));
  });

program
  .command('stop')
  .description('停止运行')
  .action(async () => {
    console.log('停止任务管理器...');
    process.exit(0);
  });

// 错误处理
process.on('unhandledRejection', (error) => {
  console.error(chalk.red('未处理的错误:'), error);
  process.exit(1);
});

program.parse();
```

## 6. 安全考虑

1. **敏感信息保护**
   - API 密钥使用环境变量
   - 配置文件加密存储
   - 日志脱敏处理

2. **权限控制**
   - 最小权限原则
   - 文件系统隔离
   - 命令注入防护

3. **资源限制**
   - 内存使用限制
   - CPU 使用限制
   - 磁盘空间监控

## 7. 测试策略

### 7.1 单元测试
- 核心模块 100% 覆盖
- Mock Claude Code CLI
- 测试各种边界情况

### 7.2 集成测试
- 端到端流程测试
- 调度器压力测试
- 错误恢复测试

### 7.3 性能测试
- 大量任务并发处理
- 内存泄漏检测
- 响应时间测试

## 8. 未来扩展

### 8.1 短期计划（1-2 个月）
- Web 管理界面
- 任务模板系统
- 更多调度策略

### 8.2 中期计划（3-6 个月）
- Gemini CLI 支持
- 多 AI 协作
- 任务市场

### 8.3 长期计划（6+ 个月）
- 分布式任务执行
- AI 自动优化
- 企业级功能

## 9. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| Claude Code API 变更 | 系统无法正常调用 | 版本兼容层，快速适配 |
| 额度耗尽 | 任务无法执行 | 智能调度，优先级管理 |
| 任务执行失败 | 影响后续任务 | 重试机制，依赖管理 |
| 系统崩溃 | 任务状态丢失 | 状态持久化，故障恢复 |

## 10. 总结

VibeCodeTask 通过自动化任务管理、智能调度和提示词优化，实现了 Claude Code 的 24 小时高效利用。系统设计考虑了可扩展性、稳定性和易用性，为开发者提供了强大的 AI 辅助开发工具。
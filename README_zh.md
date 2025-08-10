# VibeCodeTask - 实时版本

[English Version](README.md)

## 项目概述

VibeCodeTask 是一个基于 Claude Code CLI 的智能任务自动化平台，提供实时Token监控和自动化任务执行调度功能。

## 功能特性

### 🌍 国际化支持
- **多语言支持**：中英文界面切换
- **语言切换器**：轻松切换语言
- **智能检测**：默认英文，持久化语言偏好

### 💰 实时Token监控
- **实时使用跟踪**：实时Token消费监控
- **成本分析**：详细成本分解和预测
- **使用统计**：每日、每周、每月使用趋势
- **智能警报**：高使用量和预算限制通知

### 🚀 任务自动化
- **立即执行**：即时运行任务
- **定时任务**：设置特定执行时间
- **智能调度**：AI驱动的最优时机
- **队列管理**：任务优先级和依赖处理

### 📊 分析与历史
- **使用趋势**：可视化图表和图形
- **历史数据**：7/15/30天使用分析
- **性能指标**：任务完成率和执行时间
- **导出功能**：报告数据导出

### 🔧 技术功能
- **Claude Code集成**：直接CLI集成代码生成
- **文件管理**：自动工作空间组织
- **错误处理**：健壮的错误恢复和日志记录
- **响应式设计**：移动端友好界面

## 快速开始

### 先决条件
- Python 3.7+ 及所需包
- Claude Code CLI 已安装并配置
- 现代浏览器

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-repo/vibecodetask.git
   cd vibecodetask
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置 Claude Code**
   ```bash
   claude --configure
   # 按提示设置API密钥
   ```

4. **启动服务器**
   ```bash
   python realtime_server.py
   ```

5. **访问界面**
   在浏览器中打开 `http://localhost:8080`

## 使用指南

### 创建任务

1. **输入任务描述**：描述你想让Claude构建的内容
   - 例如："用HTML+JS创建贪吃蛇游戏"
   - 例如："用Python构建数据分析脚本"

2. **选择执行类型**：
   - **立即执行**：马上执行
   - **定时执行**：设置特定时间
   - **智能调度**：AI优化调度

3. **监控进度**：实时跟踪任务状态

### 语言切换

点击右上角的语言切换器在中英文之间切换。您的偏好设置会自动保存。

### Token管理

- 在仪表板中监控实时使用情况
- 设置预算管理警报
- 分析历史模式
- 导出会计用使用数据

## API接口

### 任务管理
- `POST /api/add-task` - 创建新任务
- `GET /api/tasks` - 列出所有任务
- `POST /api/execute-task` - 执行特定任务
- `POST /api/delete-task` - 删除任务

### 监控
- `GET /api/token-status` - 当前Token使用情况
- `GET /api/history/{days}` - 历史使用数据

### 国际化
- `GET /i18n/en.json` - 英文翻译
- `GET /i18n/zh.json` - 中文翻译

## 配置

### 环境变量
```bash
# 服务器配置
VIBE_PORT=8080
VIBE_HOST=localhost

# Claude配置
CLAUDE_API_KEY=your_api_key_here

# 工作空间
WORKSPACE_DIR=~/vibecodetask-workspace
```

### 语言设置
语言偏好存储在localStorage中，可以在 `i18n.js` 中配置。

## 文件结构

```
vibecodetask/
├── realtime_server.py          # 主服务器
├── realtime_interface.html     # 前端界面
├── claude_executor.py          # 任务执行引擎
├── i18n.js                    # 国际化
├── i18n/
│   ├── en.json               # 英文翻译
│   └── zh.json               # 中文翻译
├── tasks.db                  # 任务数据库
└── README_zh.md              # 本文件
```

## 开发

### 添加新语言

1. 在 `i18n/` 文件夹中创建翻译文件
2. 在 `i18n.js` 中更新可用语言
3. 在界面中添加语言按钮

### 扩展功能

系统模块化且易于扩展：
- 在 `claude_executor.py` 中添加新任务类型
- 在 `realtime_server.py` 中扩展API端点
- 在 `realtime_interface.html` 中自定义UI

## 故障排除

### 常见问题

**找不到Claude CLI**
```bash
# 安装Claude Code
npm install -g @anthropics/claude-code
# 或检查安装路径
which claude
```

**数据库锁定**
```bash
# 查找并终止阻塞进程
ps aux | grep sqlite
kill [process_id]
```

**连接问题**
- 检查服务器是否在正确端口运行
- 验证防火墙设置
- 确保Claude API密钥已配置

### 调试模式

启用详细日志记录：
```bash
export VIBE_DEBUG=true
python realtime_server.py
```

## 贡献

1. Fork仓库
2. 创建功能分支
3. 为新功能添加国际化
4. 测试两种语言
5. 提交Pull Request

## 许可证

MIT许可证 - 详见LICENSE文件

## 支持

- 问题反馈：[GitHub Issues](https://github.com/your-repo/vibecodetask/issues)
- 文档：[Wiki](https://github.com/your-repo/vibecodetask/wiki)
- 社区：[讨论区](https://github.com/your-repo/vibecodetask/discussions)

---

**用❤️和Claude Code构建**
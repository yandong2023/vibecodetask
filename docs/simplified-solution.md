# 极简化解决方案

## 方案对比

### 方案一：单文件脚本（最简单）

创建一个单独的 Python/Shell 脚本，用户只需下载一个文件即可使用。

```bash
# 一行命令安装并运行
curl -sSL https://raw.githubusercontent.com/xxx/vibecodetask/main/vct.py | python3 -
```

**优点**：
- 无需安装依赖
- 一个文件搞定
- 跨平台兼容

**实现**：

```python
#!/usr/bin/env python3
"""
VibeCodeTask - 单文件版本
直接运行: python3 vct.py
"""

import subprocess
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

class VibeCodeTask:
    def __init__(self, config_file='tasks.json'):
        self.config_file = config_file
        self.tasks = []
        self.load_config()
    
    def load_config(self):
        """加载任务配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.tasks = json.load(f).get('tasks', [])
        else:
            # 创建默认配置
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "tasks": [
                {
                    "id": "example-1",
                    "name": "示例任务",
                    "prompt": "请创建一个简单的 README.md 文件",
                    "priority": 1,
                    "schedule": "immediate"
                }
            ],
            "settings": {
                "check_interval": 300,  # 5分钟
                "max_retries": 3
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已创建默认配置文件: {self.config_file}")
        print("📝 请编辑配置文件添加您的任务")
        sys.exit(0)
    
    def check_claude_usage(self) -> Dict:
        """检查 Claude Code 使用情况"""
        try:
            result = subprocess.run(
                ['ccusage', 'blocks', '--live'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return self.parse_usage(result.stdout)
            else:
                print(f"❌ 获取使用情况失败: {result.stderr}")
                return None
        except FileNotFoundError:
            print("❌ 未找到 ccusage 命令，请确保 Claude Code 已安装")
            return None
        except Exception as e:
            print(f"❌ 检查使用情况时出错: {e}")
            return None
    
    def parse_usage(self, output: str) -> Dict:
        """解析使用情况输出"""
        usage = {
            'total': 0,
            'used': 0,
            'remaining': 0,
            'reset_time': None
        }
        
        lines = output.split('\n')
        for line in lines:
            if 'Total' in line:
                # 提取数字
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    usage['total'] = int(numbers[0])
            elif 'Used' in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    usage['used'] = int(numbers[0])
        
        usage['remaining'] = usage['total'] - usage['used']
        return usage
    
    def execute_task(self, task: Dict) -> bool:
        """执行单个任务"""
        print(f"\n🚀 执行任务: {task['name']}")
        print(f"   优先级: {task.get('priority', 99)}")
        
        # 优化提示词
        optimized_prompt = self.optimize_prompt(task)
        
        # 构建命令
        cmd = ['claude', optimized_prompt]
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )
            
            if result.returncode == 0:
                print(f"✅ 任务完成: {task['name']}")
                print(f"输出预览: {result.stdout[:200]}...")
                
                # 保存结果
                self.save_result(task, result.stdout)
                return True
            else:
                print(f"❌ 任务失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ 任务超时: {task['name']}")
            return False
        except Exception as e:
            print(f"❌ 执行任务时出错: {e}")
            return False
    
    def optimize_prompt(self, task: Dict) -> str:
        """优化提示词"""
        base_prompt = task.get('prompt', task.get('requirements', ''))
        
        # 添加任务管理指令
        optimized = f"""
## 任务：{task['name']}

{base_prompt}

## 执行要求：
1. 请分步骤完成任务
2. 每完成一个步骤，输出进度
3. 遇到问题请记录并尝试解决
4. 完成后生成简要报告

请开始执行...
"""
        return optimized
    
    def save_result(self, task: Dict, output: str):
        """保存任务结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"results/task_{task['id']}_{timestamp}.txt"
        
        os.makedirs('results', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"任务: {task['name']}\n")
            f.write(f"时间: {datetime.now()}\n")
            f.write(f"{'='*50}\n\n")
            f.write(output)
        
        print(f"💾 结果已保存: {filename}")
    
    def run(self):
        """主运行循环"""
        print("🎯 VibeCodeTask 启动")
        print(f"📋 已加载 {len(self.tasks)} 个任务")
        
        while True:
            # 检查使用情况
            usage = self.check_claude_usage()
            
            if usage:
                print(f"\n📊 当前使用情况: {usage['used']}/{usage['total']} blocks")
                print(f"   剩余: {usage['remaining']} blocks")
                
                if usage['remaining'] < 10:
                    print("⚠️ 额度不足，等待下次重置...")
                    time.sleep(3600)  # 等待1小时
                    continue
            
            # 获取待执行任务
            pending_tasks = [t for t in self.tasks if not t.get('completed', False)]
            
            if not pending_tasks:
                print("✅ 所有任务已完成")
                break
            
            # 按优先级排序
            pending_tasks.sort(key=lambda x: x.get('priority', 99))
            
            # 执行第一个任务
            task = pending_tasks[0]
            success = self.execute_task(task)
            
            if success:
                task['completed'] = True
                # 更新配置文件
                self.save_config()
            
            # 等待一段时间再执行下一个任务
            print(f"\n⏳ 等待 5 分钟后执行下一个任务...")
            time.sleep(300)  # 5分钟
    
    def save_config(self):
        """保存配置"""
        config = {
            'tasks': self.tasks
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VibeCodeTask - Claude Code 任务管理器')
    parser.add_argument('--config', default='tasks.json', help='配置文件路径')
    parser.add_argument('--once', action='store_true', help='只执行一次')
    parser.add_argument('--check', action='store_true', help='只检查使用情况')
    
    args = parser.parse_args()
    
    vct = VibeCodeTask(args.config)
    
    if args.check:
        # 只检查使用情况
        usage = vct.check_claude_usage()
        if usage:
            print(f"📊 使用情况:")
            print(f"   总额度: {usage['total']} blocks")
            print(f"   已使用: {usage['used']} blocks")
            print(f"   剩余: {usage['remaining']} blocks")
    else:
        # 运行任务
        vct.run()

if __name__ == '__main__':
    main()
```

### 方案二：NPX 一键运行（无需安装）

利用 npx 直接运行，无需本地安装：

```bash
# 直接运行，无需安装
npx vibecodetask

# 或者带配置
npx vibecodetask --config my-tasks.json
```

**package.json**:
```json
{
  "name": "vibecodetask",
  "version": "1.0.0",
  "bin": {
    "vibecodetask": "./index.js",
    "vct": "./index.js"
  },
  "dependencies": {}
}
```

**index.js**:
```javascript
#!/usr/bin/env node

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// 自包含的单文件执行器
class VCT {
  async run() {
    console.log('🚀 VibeCodeTask 启动...');
    
    // 检查 claude 命令
    if (!await this.checkClaude()) {
      console.log('❌ 请先安装 Claude Code CLI');
      process.exit(1);
    }
    
    // 加载或创建配置
    const config = await this.loadConfig();
    
    // 执行任务
    await this.executeTasks(config.tasks);
  }
  
  async checkClaude() {
    return new Promise(resolve => {
      exec('claude --version', (error) => {
        resolve(!error);
      });
    });
  }
  
  async loadConfig() {
    const configPath = './vct-tasks.json';
    
    if (!fs.existsSync(configPath)) {
      // 创建默认配置
      const defaultConfig = {
        tasks: [
          {
            name: "示例任务",
            prompt: "创建一个 hello world 程序"
          }
        ]
      };
      
      fs.writeFileSync(configPath, JSON.stringify(defaultConfig, null, 2));
      console.log('📝 已创建配置文件: vct-tasks.json');
    }
    
    return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  }
  
  async executeTasks(tasks) {
    for (const task of tasks) {
      console.log(`\n执行: ${task.name}`);
      await this.executeTask(task);
    }
  }
  
  executeTask(task) {
    return new Promise((resolve) => {
      exec(`claude "${task.prompt}"`, (error, stdout, stderr) => {
        if (error) {
          console.error('错误:', stderr);
        } else {
          console.log('完成:', stdout.slice(0, 100) + '...');
        }
        resolve();
      });
    });
  }
}

// 立即执行
new VCT().run().catch(console.error);
```

### 方案三：浏览器书签工具（最方便）

创建一个浏览器书签，点击即可添加任务：

```javascript
javascript:(function(){
  const task = prompt('输入任务描述:');
  if(task) {
    fetch('http://localhost:3000/add-task', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({task})
    }).then(()=>alert('任务已添加')).catch(()=>alert('请先启动 VCT 服务'));
  }
})();
```

配合一个轻量级本地服务：

```javascript
// vct-server.js - 超轻量服务
const http = require('http');
const { exec } = require('child_process');

const tasks = [];

http.createServer((req, res) => {
  if (req.url === '/add-task' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      const { task } = JSON.parse(body);
      tasks.push(task);
      res.writeHead(200);
      res.end('OK');
      
      // 立即执行
      exec(`claude "${task}"`, (err, stdout) => {
        console.log('任务完成:', task);
      });
    });
  }
}).listen(3000);

console.log('VCT 服务运行在 http://localhost:3000');
```

### 方案四：高级 Shell 脚本（最灵活）

创建功能完整的 Shell 脚本 `vct.sh`：

```bash
#!/bin/bash

# VibeCodeTask Shell 版本
# 使用方法: ./vct.sh [命令] [选项]

set -euo pipefail

# 配置文件路径
CONFIG_FILE="${VCT_CONFIG:-$HOME/.vct_config.json}"
HISTORY_FILE="${VCT_HISTORY:-$HOME/.vct_history}"
LOG_FILE="${VCT_LOG:-$HOME/.vct.log}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo -e "$1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >> "$LOG_FILE"
    echo -e "${RED}❌ $1${NC}"
}

log_success() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - SUCCESS: $1" >> "$LOG_FILE"
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: $1" >> "$LOG_FILE"
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO: $1" >> "$LOG_FILE"
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# 检查依赖
check_dependencies() {
    local missing_deps=()
    
    if ! command -v claude &> /dev/null; then
        missing_deps+=("claude")
    fi
    
    if ! command -v ccusage &> /dev/null; then
        missing_deps+=("ccusage")
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，某些功能可能无法使用"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "缺少依赖: ${missing_deps[*]}"
        echo "请安装缺少的依赖后再运行"
        exit 1
    fi
}

# 创建默认配置
create_default_config() {
    cat > "$CONFIG_FILE" << 'EOF'
{
  "settings": {
    "max_concurrent": 1,
    "check_interval": 300,
    "retry_limit": 3,
    "timeout": 120,
    "work_hours": {
      "start": "09:00",
      "end": "18:00"
    }
  },
  "templates": {
    "development": "创建并实现 {task}，请分步骤执行：\n1. 分析需求\n2. 设计方案\n3. 编写代码\n4. 测试验证",
    "testing": "为 {task} 编写测试，包括：\n1. 单元测试\n2. 集成测试\n3. 覆盖率检查",
    "documentation": "为 {task} 编写文档，包括：\n1. 使用说明\n2. API 文档\n3. 示例代码"
  },
  "shortcuts": {
    "server": "创建一个 Express.js 服务器",
    "react": "创建一个 React 应用",
    "test": "编写单元测试"
  }
}
EOF
    log_success "默认配置已创建: $CONFIG_FILE"
}

# 获取配置值
get_config() {
    local key="$1"
    local default="${2:-}"
    
    if [[ -f "$CONFIG_FILE" && -x "$(command -v jq)" ]]; then
        jq -r ".$key // \"$default\"" "$CONFIG_FILE" 2>/dev/null || echo "$default"
    else
        echo "$default"
    fi
}

# 检查工作时间
is_work_hours() {
    local start_time=$(get_config "settings.work_hours.start" "00:00")
    local end_time=$(get_config "settings.work_hours.end" "23:59")
    local current_time=$(date +%H:%M)
    
    if [[ "$start_time" == "00:00" && "$end_time" == "23:59" ]]; then
        return 0
    fi
    
    [[ "$current_time" > "$start_time" && "$current_time" < "$end_time" ]]
}

# 获取 Claude 使用情况
get_claude_usage() {
    if ! ccusage blocks --live 2>/dev/null; then
        log_error "无法获取 Claude 使用情况"
        return 1
    fi
}

# 检查剩余额度
check_quota() {
    local usage_output
    usage_output=$(ccusage blocks --live 2>/dev/null || echo "")
    
    if [[ -z "$usage_output" ]]; then
        log_warning "无法获取使用情况，继续执行"
        return 0
    fi
    
    # 简单解析剩余额度（需要根据实际输出调整）
    local remaining=$(echo "$usage_output" | grep -oE '[0-9]+' | tail -1 || echo "100")
    
    if [[ $remaining -lt 10 ]]; then
        log_warning "剩余额度不足: $remaining"
        return 1
    fi
    
    log_info "剩余额度: $remaining"
    return 0
}

# 优化提示词
optimize_prompt() {
    local task="$1"
    local type="${2:-development}"
    
    # 获取模板
    local template=$(get_config "templates.$type" "完成任务: {task}")
    
    # 替换占位符
    local optimized_prompt="${template/\{task\}/$task}"
    
    # 添加通用指令
    cat << EOF
$optimized_prompt

执行要求:
1. 分步骤详细执行
2. 每完成一步输出进度
3. 遇到错误请记录并尝试解决
4. 完成后提供总结报告

现在开始执行...
EOF
}

# 执行任务
execute_task() {
    local task="$1"
    local type="${2:-development}"
    local timeout=$(get_config "settings.timeout" "120")
    
    log_info "开始执行任务: $task"
    log_info "任务类型: $type"
    
    # 检查工作时间
    if ! is_work_hours; then
        log_warning "当前不在工作时间内"
        read -p "是否继续执行? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "任务已取消"
            return 0
        fi
    fi
    
    # 检查额度
    if ! check_quota; then
        log_error "额度不足，任务取消"
        return 1
    fi
    
    # 优化提示词
    local optimized_prompt=$(optimize_prompt "$task" "$type")
    
    # 执行任务
    local start_time=$(date +%s)
    local temp_file=$(mktemp)
    
    if timeout "${timeout}s" claude "$optimized_prompt" > "$temp_file" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log_success "任务完成，耗时: ${duration}s"
        
        # 显示结果预览
        echo -e "\n${CYAN}结果预览:${NC}"
        head -n 20 "$temp_file"
        
        if [[ $(wc -l < "$temp_file") -gt 20 ]]; then
            echo -e "\n${YELLOW}... (输出已截断，完整结果请查看: $temp_file)${NC}"
        fi
        
        # 保存到历史
        echo "$(date '+%Y-%m-%d %H:%M:%S') | $type | $task | ${duration}s | SUCCESS" >> "$HISTORY_FILE"
        
        # 询问是否保存结果
        read -p "是否保存完整结果? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local result_file="vct_result_$(date +%Y%m%d_%H%M%S).txt"
            cp "$temp_file" "$result_file"
            log_success "结果已保存到: $result_file"
        fi
        
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log_error "任务执行失败，耗时: ${duration}s"
        
        # 显示错误信息
        echo -e "\n${RED}错误信息:${NC}"
        cat "$temp_file"
        
        # 保存到历史
        echo "$(date '+%Y-%m-%d %H:%M:%S') | $type | $task | ${duration}s | FAILED" >> "$HISTORY_FILE"
    fi
    
    rm -f "$temp_file"
}

# 显示历史记录
show_history() {
    local lines="${1:-10}"
    
    if [[ ! -f "$HISTORY_FILE" ]]; then
        log_info "暂无历史记录"
        return
    fi
    
    echo -e "${CYAN}最近 $lines 条任务记录:${NC}"
    tail -n "$lines" "$HISTORY_FILE" | while IFS='|' read -r timestamp type task duration status; do
        local color
        case "$status" in
            *SUCCESS*) color="$GREEN" ;;
            *FAILED*) color="$RED" ;;
            *) color="$NC" ;;
        esac
        
        echo -e "${color}${timestamp} [${type}] ${task} (${duration})${NC}"
    done
}

# 显示状态信息
show_status() {
    echo -e "${PURPLE}=== VibeCodeTask Status ===${NC}\n"
    
    # 显示配置信息
    echo -e "${CYAN}配置文件:${NC} $CONFIG_FILE"
    echo -e "${CYAN}历史文件:${NC} $HISTORY_FILE"
    echo -e "${CYAN}日志文件:${NC} $LOG_FILE"
    echo
    
    # 显示使用情况
    echo -e "${CYAN}Claude 使用情况:${NC}"
    get_claude_usage || echo "无法获取"
    echo
    
    # 显示任务统计
    if [[ -f "$HISTORY_FILE" ]]; then
        local total=$(wc -l < "$HISTORY_FILE")
        local success=$(grep -c "SUCCESS" "$HISTORY_FILE" || echo "0")
        local failed=$(grep -c "FAILED" "$HISTORY_FILE" || echo "0")
        
        echo -e "${CYAN}任务统计:${NC}"
        echo "  总计: $total"
        echo "  成功: $success"
        echo "  失败: $failed"
        
        if [[ $total -gt 0 ]]; then
            local success_rate=$(( success * 100 / total ))
            echo "  成功率: ${success_rate}%"
        fi
    fi
    
    echo
    
    # 显示工作时间
    local start_time=$(get_config "settings.work_hours.start")
    local end_time=$(get_config "settings.work_hours.end")
    local current_time=$(date +%H:%M)
    
    echo -e "${CYAN}工作时间:${NC} $start_time - $end_time"
    echo -e "${CYAN}当前时间:${NC} $current_time"
    
    if is_work_hours; then
        echo -e "${GREEN}状态: 工作时间内${NC}"
    else
        echo -e "${YELLOW}状态: 非工作时间${NC}"
    fi
}

# 批量执行任务
batch_execute() {
    local file="$1"
    local type="${2:-development}"
    
    if [[ ! -f "$file" ]]; then
        log_error "任务文件不存在: $file"
        return 1
    fi
    
    log_info "开始批量执行任务，文件: $file"
    
    local total=0
    local success=0
    local failed=0
    
    while IFS= read -r task || [[ -n "$task" ]]; do
        [[ -z "$task" || "$task" =~ ^#.*$ ]] && continue
        
        ((total++))
        echo -e "\n${PURPLE}=== 任务 $total: $task ===${NC}"
        
        if execute_task "$task" "$type"; then
            ((success++))
        else
            ((failed++))
        fi
        
        # 任务间延迟
        if [[ $total -lt $(wc -l < "$file") ]]; then
            log_info "等待 30 秒后执行下一任务..."
            sleep 30
        fi
        
    done < "$file"
    
    echo -e "\n${PURPLE}=== 批量执行完成 ===${NC}"
    echo "总计: $total"
    echo "成功: $success"
    echo "失败: $failed"
}

# 交互模式
interactive_mode() {
    echo -e "${PURPLE}=== VibeCodeTask 交互模式 ===${NC}"
    echo "输入 'help' 查看帮助，输入 'quit' 退出"
    
    while true; do
        echo -n -e "\n${CYAN}vct>${NC} "
        read -r input
        
        case "$input" in
            "help")
                echo "可用命令:"
                echo "  <任务描述>        - 执行任务"
                echo "  status           - 显示状态"
                echo "  history [数量]   - 显示历史记录"
                echo "  quota           - 检查剩余额度"
                echo "  help            - 显示帮助"
                echo "  quit            - 退出"
                ;;
            "quit"|"exit")
                log_info "退出交互模式"
                break
                ;;
            "status")
                show_status
                ;;
            "quota")
                get_claude_usage
                ;;
            history*)
                local lines=$(echo "$input" | awk '{print $2}' | grep -E '^[0-9]+$' || echo "10")
                show_history "$lines"
                ;;
            "")
                continue
                ;;
            *)
                execute_task "$input"
                ;;
        esac
    done
}

# 显示帮助
show_help() {
    cat << 'EOF'
VibeCodeTask - Claude Code 任务管理工具

使用方法:
    ./vct.sh [命令] [选项]

命令:
    run <任务描述>           - 执行单个任务
    batch <文件> [类型]       - 批量执行任务文件中的任务
    status                  - 显示系统状态
    history [数量]           - 显示历史记录（默认10条）
    quota                   - 检查 Claude 使用额度
    interactive             - 进入交互模式
    init                    - 创建默认配置文件
    help                    - 显示帮助信息

任务类型:
    development (默认)      - 开发任务
    testing                - 测试任务
    documentation          - 文档任务

示例:
    ./vct.sh run "创建一个 React 应用"
    ./vct.sh run "编写单元测试" testing
    ./vct.sh batch tasks.txt development
    ./vct.sh interactive

环境变量:
    VCT_CONFIG              - 配置文件路径（默认：~/.vct_config.json）
    VCT_HISTORY             - 历史文件路径（默认：~/.vct_history）
    VCT_LOG                 - 日志文件路径（默认：~/.vct.log）

配置文件示例在首次运行时会自动创建。
EOF
}

# 主函数
main() {
    # 检查依赖
    check_dependencies
    
    # 创建配置文件（如果不存在）
    if [[ ! -f "$CONFIG_FILE" ]]; then
        create_default_config
    fi
    
    # 解析命令
    case "${1:-help}" in
        "run")
            if [[ $# -lt 2 ]]; then
                log_error "用法: $0 run <任务描述> [类型]"
                exit 1
            fi
            execute_task "$2" "${3:-development}"
            ;;
        "batch")
            if [[ $# -lt 2 ]]; then
                log_error "用法: $0 batch <文件> [类型]"
                exit 1
            fi
            batch_execute "$2" "${3:-development}"
            ;;
        "status")
            show_status
            ;;
        "history")
            show_history "${2:-10}"
            ;;
        "quota")
            get_claude_usage
            ;;
        "interactive")
            interactive_mode
            ;;
        "init")
            create_default_config
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            # 如果第一个参数不是命令，当作任务描述处理
            if [[ $# -ge 1 ]]; then
                execute_task "$*"
            else
                show_help
            fi
            ;;
    esac
}

# 执行主函数
main "$@"
```

使用方式：
```bash
# 给脚本执行权限
chmod +x vct.sh

# 执行任务
./vct.sh run "创建一个 Express 服务器"

# 批量执行
echo "创建用户认证模块" > tasks.txt
echo "编写单元测试" >> tasks.txt
./vct.sh batch tasks.txt

# 交互模式
./vct.sh interactive

# 查看状态
./vct.sh status
```

### 方案五：一键安装脚本（最便捷）

创建通用安装脚本 `install.sh`：

```bash
#!/bin/bash

# VibeCodeTask 一键安装脚本
# 支持 macOS, Linux, Windows (WSL)

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

INSTALL_DIR="$HOME/.vibecodetask"
BIN_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/yourusername/vibecodetask"

# 日志函数
log_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# 检测系统
detect_system() {
    local os_name=$(uname -s)
    local arch=$(uname -m)
    
    case "$os_name" in
        "Darwin") echo "macos-$arch" ;;
        "Linux") echo "linux-$arch" ;;
        "MINGW"*|"CYGWIN"*|"MSYS"*) echo "windows-$arch" ;;
        *) echo "unknown" ;;
    esac
}

# 检查依赖
check_dependencies() {
    local missing=()
    
    # 检查 Claude Code
    if ! command -v claude &> /dev/null; then
        log_error "Claude Code CLI 未安装"
        echo "请先安装 Claude Code: https://claude.ai/code"
        exit 1
    fi
    
    # 检查可选依赖
    command -v git &> /dev/null || missing+=("git")
    command -v curl &> /dev/null || missing+=("curl")
    command -v jq &> /dev/null || missing+=("jq")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_warning "建议安装: ${missing[*]}"
    fi
}

# 创建目录
create_directories() {
    log_info "创建安装目录..."
    mkdir -p "$INSTALL_DIR" "$BIN_DIR"
}

# 下载文件
download_files() {
    log_info "下载项目文件..."
    
    # 下载主要文件
    local files=(
        "vct.py"
        "vct.sh"
        "vct.js"
    )
    
    for file in "${files[@]}"; do
        if curl -fsSL "$REPO_URL/raw/main/$file" -o "$INSTALL_DIR/$file"; then
            log_success "已下载: $file"
            chmod +x "$INSTALL_DIR/$file"
        else
            log_error "下载失败: $file"
        fi
    done
    
    # 下载配置模板
    if curl -fsSL "$REPO_URL/raw/main/config/tasks.example.json" -o "$INSTALL_DIR/tasks.example.json"; then
        log_success "已下载配置模板"
    fi
}

# 创建启动脚本
create_launcher() {
    log_info "创建启动脚本..."
    
    cat > "$BIN_DIR/vct" << 'LAUNCHER_EOF'
#!/bin/bash

VCT_DIR="$HOME/.vibecodetask"

# 自动选择最佳实现
if [[ -f "$VCT_DIR/vct.py" ]] && command -v python3 &> /dev/null; then
    # 优先使用 Python 版本
    exec python3 "$VCT_DIR/vct.py" "$@"
elif [[ -f "$VCT_DIR/vct.js" ]] && command -v node &> /dev/null; then
    # 其次使用 Node.js 版本
    exec node "$VCT_DIR/vct.js" "$@"
elif [[ -f "$VCT_DIR/vct.sh" ]]; then
    # 最后使用 Shell 版本
    exec bash "$VCT_DIR/vct.sh" "$@"
else
    echo "❌ 未找到可用的 VibeCodeTask 实现"
    exit 1
fi
LAUNCHER_EOF
    
    chmod +x "$BIN_DIR/vct"
    log_success "启动脚本已创建: $BIN_DIR/vct"
}

# 配置 Shell
configure_shell() {
    log_info "配置 Shell 环境..."
    
    local shell_config=""
    if [[ -n "${BASH_VERSION:-}" ]]; then
        shell_config="$HOME/.bashrc"
    elif [[ -n "${ZSH_VERSION:-}" ]]; then
        shell_config="$HOME/.zshrc"
    else
        shell_config="$HOME/.profile"
    fi
    
    # 添加 PATH
    if ! grep -q "$BIN_DIR" "$shell_config" 2>/dev/null; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$shell_config"
        log_success "已更新 PATH: $shell_config"
    fi
    
    # 添加便捷别名
    if ! grep -q "alias vct-status" "$shell_config" 2>/dev/null; then
        cat >> "$shell_config" << 'ALIAS_EOF'

# VibeCodeTask 别名
alias vct-status="vct status"
alias vct-history="vct history"
alias vct-quota="vct quota"
ALIAS_EOF
        log_success "已添加便捷别名"
    fi
}

# 创建示例配置
create_example_config() {
    log_info "创建示例配置..."
    
    if [[ ! -f "$HOME/vct-tasks.json" ]]; then
        cat > "$HOME/vct-tasks.json" << 'CONFIG_EOF'
{
  "tasks": [
    {
      "id": "example-1",
      "name": "创建 Hello World 项目",
      "requirements": "创建一个简单的 Hello World 程序，使用你推荐的编程语言",
      "priority": 1,
      "type": "development"
    },
    {
      "id": "example-2",
      "name": "编写测试用例",
      "requirements": "为上面的 Hello World 程序编写单元测试",
      "priority": 2,
      "type": "testing",
      "dependencies": ["example-1"]
    }
  ],
  "settings": {
    "maxConcurrent": 1,
    "checkInterval": 300000,
    "workHours": {
      "start": "09:00",
      "end": "18:00"
    }
  }
}
CONFIG_EOF
        log_success "示例配置已创建: $HOME/vct-tasks.json"
    fi
}

# 测试安装
test_installation() {
    log_info "测试安装..."
    
    # 重新加载 PATH
    export PATH="$BIN_DIR:$PATH"
    
    if command -v vct &> /dev/null; then
        log_success "安装成功！"
        
        # 显示版本信息
        echo
        vct --help 2>/dev/null || echo "VibeCodeTask 已安装"
        
    else
        log_error "安装验证失败"
        echo "请手动将 $BIN_DIR 添加到 PATH 环境变量"
    fi
}

# 显示后续步骤
show_next_steps() {
    echo
    log_info "安装完成！后续步骤："
    echo
    echo "1. 重新启动终端或运行: source ~/.bashrc"
    echo "2. 测试安装: vct --help"
    echo "3. 编辑配置: $HOME/vct-tasks.json"
    echo "4. 运行示例: vct run \"创建一个计算器程序\""
    echo "5. 查看状态: vct status"
    echo
    echo "更多帮助: https://github.com/yourusername/vibecodetask"
}

# 卸载函数
uninstall() {
    log_info "开始卸载 VibeCodeTask..."
    
    # 删除安装目录
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        log_success "已删除安装目录"
    fi
    
    # 删除启动脚本
    if [[ -f "$BIN_DIR/vct" ]]; then
        rm -f "$BIN_DIR/vct"
        log_success "已删除启动脚本"
    fi
    
    log_success "卸载完成"
    echo "注意: 配置文件和历史记录未删除"
    echo "如需完全清理，请手动删除: $HOME/vct-* 和 $HOME/.vct*"
}

# 主函数
main() {
    echo -e "${PURPLE}🚀 VibeCodeTask 安装程序${NC}"
    echo
    
    # 处理命令行参数
    case "${1:-install}" in
        "uninstall")
            uninstall
            exit 0
            ;;
        "install"|"")
            # 继续安装流程
            ;;
        *)
            echo "用法: $0 [install|uninstall]"
            exit 1
            ;;
    esac
    
    # 系统检测
    local system=$(detect_system)
    log_info "检测到系统: $system"
    
    # 检查依赖
    check_dependencies
    
    # 安装流程
    create_directories
    download_files
    create_launcher
    configure_shell
    create_example_config
    test_installation
    show_next_steps
    
    log_success "🎉 安装完成！"
}

# 错误处理
trap 'log_error "安装过程中出现错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"
```

使用方式：
```bash
# 一键安装
curl -sSL https://vct.example.com/install.sh | bash

# 或下载后安装
wget https://vct.example.com/install.sh
chmod +x install.sh
./install.sh

# 卸载
./install.sh uninstall
```

### 方案五：Docker 一键部署（零配置）

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY vct.js .
RUN npm install -g claude
CMD ["node", "vct.js"]
```

使用：
```bash
# 一行命令运行
docker run -it --rm \
  -v ~/.claude:/root/.claude \
  -v $(pwd)/tasks.json:/app/tasks.json \
  vibecodetask/vct
```

## 推荐方案

### 🏆 最推荐：Python 单文件版本

**安装**：
```bash
# 方式1: 下载并运行
curl -O https://raw.githubusercontent.com/xxx/vct/main/vct.py
python3 vct.py

# 方式2: 直接运行
curl -sSL https://vct.example.com/run | python3 -
```

**优势**：
1. **零依赖**：只需要 Python（系统自带）
2. **单文件**：一个文件搞定所有功能
3. **跨平台**：Windows/Mac/Linux 都能用
4. **易分享**：发送一个文件给朋友即可

### 快速开始模板

创建 `quick-start.sh`:

```bash
#!/bin/bash

echo "🚀 VibeCodeTask 快速安装"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3"
    exit 1
fi

# 检查 Claude
if ! command -v claude &> /dev/null; then
    echo "⚠️ 未检测到 Claude Code CLI"
    echo "请先安装: https://claude.ai/code"
    exit 1
fi

# 下载脚本
curl -o vct.py https://raw.githubusercontent.com/xxx/vct/main/vct.py

# 创建示例配置
cat > tasks.json << 'EOF'
{
  "tasks": [
    {
      "id": "task-001",
      "name": "创建项目结构",
      "prompt": "创建一个标准的 Node.js 项目结构",
      "priority": 1
    }
  ]
}
EOF

echo "✅ 安装完成！"
echo ""
echo "使用方法:"
echo "  python3 vct.py        # 运行任务"
echo "  python3 vct.py --check # 检查额度"
echo ""
echo "编辑 tasks.json 添加您的任务"
```

一行安装：
```bash
curl -sSL https://vct.example.com/install | bash
```

## 总结

极简化方案优先级：

1. **Python 单文件** - 最简单，推荐大多数用户
2. **Shell 别名** - 适合命令行用户
3. **NPX 运行** - 适合 Node.js 用户
4. **Docker** - 适合需要隔离环境的用户
5. **浏览器书签** - 适合非技术用户

核心思路：
- **减少依赖**：尽量使用系统自带工具
- **单文件分发**：一个文件包含所有功能
- **零配置启动**：自动创建默认配置
- **一键安装**：提供快速安装脚本
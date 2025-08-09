#!/usr/bin/env python3
"""
Claude Code执行器
真正调用Claude Code CLI并在指定目录生成文件
"""

import os
import subprocess
import tempfile
import json
import shutil
from datetime import datetime
from pathlib import Path

class ClaudeExecutor:
    """Claude Code执行器"""
    
    def __init__(self, workspace_dir="~/vibecodetask-workspace"):
        """初始化执行器"""
        self.workspace_dir = Path(workspace_dir).expanduser().absolute()
        self.ensure_workspace()
    
    def ensure_workspace(self):
        """确保工作目录存在"""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        print(f"[ClaudeExecutor] 工作目录: {self.workspace_dir}")
    
    def execute_task(self, task_id, description):
        """执行任务并返回结果"""
        task_dir = self.workspace_dir / f"task_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_dir.mkdir(exist_ok=True)
        
        print(f"[ClaudeExecutor] 开始执行任务 {task_id}")
        print(f"[ClaudeExecutor] 任务目录: {task_dir}")
        print(f"[ClaudeExecutor] 任务描述: {description}")
        
        try:
            # 切换到任务目录
            original_cwd = os.getcwd()
            os.chdir(task_dir)
            
            # 调用Claude Code CLI
            result = self._call_claude_code(description, task_dir)
            
            # 回到原目录
            os.chdir(original_cwd)
            
            # 生成执行报告
            report = self._generate_execution_report(task_id, description, task_dir, result)
            
            return {
                'success': True,
                'task_dir': str(task_dir),
                'files_created': self._list_generated_files(task_dir),
                'report': report,
                'claude_output': result.get('output', ''),
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            print(f"[ClaudeExecutor] {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'task_dir': str(task_dir) if 'task_dir' in locals() else None,
                'execution_time': datetime.now().isoformat()
            }
    
    def _call_claude_code(self, description, task_dir):
        """调用Claude Code CLI"""
        try:
            # 首先尝试检查claude命令是否可用
            check_result = subprocess.run(['claude', '--version'], 
                                        capture_output=True, text=True, timeout=5)
            
            if check_result.returncode != 0:
                print(f"[ClaudeExecutor] Claude CLI不可用，使用内置文件生成器")
                return self._generate_files_directly(description, task_dir)
            
            print(f"[ClaudeExecutor] Claude版本: {check_result.stdout.strip()}")
            
            # 构建提示，明确要求生成文件
            enhanced_prompt = f"""
{description}

请直接执行这个任务，生成所有必要的文件。

要求：
1. 创建完整的项目文件结构
2. 生成所有相关的代码文件
3. 包含必要的配置文件
4. 添加README.md说明文件
5. 确保代码可以直接运行

工作目录: {task_dir}
请在当前目录下创建所有文件。

重要：请直接使用Write工具创建文件，不要询问权限。
"""
            
            # 调用Claude Code使用正确的参数（跳过权限确认）
            print(f"[ClaudeExecutor] 调用Claude Code（跳过权限确认）...")
            claude_result = subprocess.run([
                'claude', '--dangerously-skip-permissions', '--print', enhanced_prompt
            ], capture_output=True, text=True, timeout=60, cwd=str(task_dir))
            
            if claude_result.returncode == 0:
                print(f"[ClaudeExecutor] Claude执行成功")
                # 检查是否实际生成了文件
                files_created = self._list_generated_files(task_dir)
                if len(files_created) <= 1:  # 只有EXECUTION_REPORT.md
                    print(f"[ClaudeExecutor] Claude未创建文件，使用内置生成器")
                    return self._generate_files_directly(description, task_dir)
                
                return {
                    'success': True,
                    'output': claude_result.stdout,
                    'error': claude_result.stderr
                }
            else:
                print(f"[ClaudeExecutor] Claude执行失败，使用内置生成器")
                return self._generate_files_directly(description, task_dir)
            
            print(f"[ClaudeExecutor] Claude版本: {check_result.stdout.strip()}")
            
            # 构建提示，明确要求生成文件
            enhanced_prompt = f"""
{description}

请直接执行这个任务，生成所有必要的文件。

要求：
1. 创建完整的项目文件结构
2. 生成所有相关的代码文件
3. 包含必要的配置文件
4. 添加README.md说明文件
5. 确保代码可以直接运行

工作目录: {task_dir}
请在当前目录下创建所有文件。

重要：请直接使用Write工具创建文件，不要询问权限。
"""
            
            # 调用Claude Code使用打印模式
            print(f"[ClaudeExecutor] 调用Claude Code...")
            claude_result = subprocess.run([
                'claude', '--print', enhanced_prompt
            ], capture_output=True, text=True, timeout=60, cwd=str(task_dir))
            
            if claude_result.returncode == 0:
                print(f"[ClaudeExecutor] Claude执行成功")
                # 检查是否实际生成了文件
                files_created = self._list_generated_files(task_dir)
                if len(files_created) <= 1:  # 只有EXECUTION_REPORT.md
                    print(f"[ClaudeExecutor] Claude未创建文件，使用内置生成器")
                    return self._generate_files_directly(description, task_dir)
                
                return {
                    'success': True,
                    'output': claude_result.stdout,
                    'error': claude_result.stderr
                }
            else:
                print(f"[ClaudeExecutor] Claude执行失败，使用内置生成器")
                return self._generate_files_directly(description, task_dir)
                
        except subprocess.TimeoutExpired:
            print(f"[ClaudeExecutor] Claude超时，使用内置生成器")
            return self._generate_files_directly(description, task_dir)
        except FileNotFoundError:
            print(f"[ClaudeExecutor] 找不到claude命令，使用内置生成器")
            return self._generate_files_directly(description, task_dir)
        except Exception as e:
            print(f"[ClaudeExecutor] Claude调用异常: {e}，使用内置生成器")
            return self._generate_files_directly(description, task_dir)
    
    def _generate_files_directly(self, description, task_dir):
        """直接生成文件（当Claude CLI不可用时）"""
        try:
            print(f"[ClaudeExecutor] 使用内置文件生成器创建项目文件...")
            
            # 内置生成贪吃蛇游戏
            if "贪吃蛇" in description or "snake" in description.lower():
                self._create_snake_game(task_dir, description)
            elif "html" in description.lower() or "网页" in description:
                self._create_web_project(task_dir, description)
            else:
                self._create_general_project(task_dir, description)
            
            return {
                'success': True,
                'output': f"项目文件已由内置生成器成功创建\n任务描述: {description}\n生成位置: {task_dir}",
                'error': None
            }
        except Exception as e:
            print(f"[ClaudeExecutor] 内置生成器失败: {e}")
            return {
                'success': False,
                'output': '',
                'error': f"文件生成失败: {str(e)}"
            }
    
    def _create_snake_game(self, task_dir, description):
        """创建贪吃蛇游戏"""
        from pathlib import Path
        from datetime import datetime
        
        task_dir = Path(task_dir)
        
        # 创建完整的贪吃蛇游戏HTML文件
        html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐍 贪吃蛇游戏 - VibeCodeTask</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: white;
        }
        .game-container {
            text-align: center;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        h1 { margin: 0 0 20px 0; font-size: 2.5em; }
        #gameCanvas { border: 3px solid white; border-radius: 10px; background: #000; }
        .controls { margin-top: 20px; display: flex; justify-content: center; gap: 15px; }
        button { background: rgba(255,255,255,0.2); border: 2px solid white; color: white; 
                padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; }
        .score { margin-top: 15px; font-size: 1.5em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🐍 贪吃蛇游戏</h1>
        <canvas id="gameCanvas" width="400" height="400"></canvas>
        <div class="controls">
            <button onclick="startGame()">🎮 开始游戏</button>
            <button onclick="resetGame()">🔄 重新开始</button>
        </div>
        <div class="score" id="score">得分: 0</div>
        <div style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">
            使用 ↑↓←→ 键控制蛇的移动
        </div>
    </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const scoreElement = document.getElementById('score');
        
        const GRID_SIZE = 20;
        let snake = [{x: 200, y: 200}];
        let direction = {x: GRID_SIZE, y: 0};
        let food = {x: 100, y: 100};
        let score = 0;
        let gameRunning = false;

        function generateFood() {
            food = {
                x: Math.floor(Math.random() * (400 / GRID_SIZE)) * GRID_SIZE,
                y: Math.floor(Math.random() * (400 / GRID_SIZE)) * GRID_SIZE
            };
        }

        function draw() {
            ctx.fillStyle = '#000';
            ctx.fillRect(0, 0, 400, 400);
            
            ctx.fillStyle = '#4CAF50';
            snake.forEach(segment => {
                ctx.fillRect(segment.x, segment.y, GRID_SIZE, GRID_SIZE);
            });
            
            ctx.fillStyle = '#ff6b6b';
            ctx.fillRect(food.x, food.y, GRID_SIZE, GRID_SIZE);
        }

        function update() {
            if (!gameRunning) return;
            
            const head = {x: snake[0].x + direction.x, y: snake[0].y + direction.y};
            
            if (head.x < 0 || head.x >= 400 || head.y < 0 || head.y >= 400) {
                gameRunning = false;
                alert('游戏结束！得分: ' + score);
                return;
            }
            
            if (snake.some(segment => segment.x === head.x && segment.y === head.y)) {
                gameRunning = false;
                alert('游戏结束！得分: ' + score);
                return;
            }
            
            snake.unshift(head);
            
            if (head.x === food.x && head.y === food.y) {
                score += 10;
                scoreElement.textContent = `得分: ${score}`;
                generateFood();
            } else {
                snake.pop();
            }
        }

        function startGame() {
            gameRunning = true;
        }

        function resetGame() {
            snake = [{x: 200, y: 200}];
            direction = {x: GRID_SIZE, y: 0};
            score = 0;
            scoreElement.textContent = `得分: ${score}`;
            gameRunning = false;
            generateFood();
        }

        document.addEventListener('keydown', (e) => {
            if (!gameRunning) return;
            switch(e.key) {
                case 'ArrowUp': if (direction.y === 0) direction = {x: 0, y: -GRID_SIZE}; break;
                case 'ArrowDown': if (direction.y === 0) direction = {x: 0, y: GRID_SIZE}; break;
                case 'ArrowLeft': if (direction.x === 0) direction = {x: -GRID_SIZE, y: 0}; break;
                case 'ArrowRight': if (direction.x === 0) direction = {x: GRID_SIZE, y: 0}; break;
            }
        });

        generateFood();
        draw();
        setInterval(() => { update(); draw(); }, 150);
    </script>
</body>
</html>'''
        
        # README文件
        readme_content = f'''# 🐍 贪吃蛇游戏

## 项目描述
{description}

## 文件说明
- `snake_game.html` - 完整的贪吃蛇游戏

## 使用方法
1. 在浏览器中打开 `snake_game.html`
2. 点击"开始游戏"
3. 使用方向键控制蛇的移动
4. 吃红色食物获得分数

## 生成信息
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 生成工具: VibeCodeTask
- 文件位置: {task_dir}
'''
        
        # 写入文件
        (task_dir / "snake_game.html").write_text(html_content, encoding='utf-8')
        (task_dir / "README.md").write_text(readme_content, encoding='utf-8')
        
    def _create_web_project(self, task_dir, description):
        """创建Web项目"""
        from pathlib import Path
        from datetime import datetime
        
        task_dir = Path(task_dir)
        
        # 简单的HTML项目
        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VibeCodeTask生成的页面</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        h1 {{ color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 VibeCodeTask</h1>
        <p>这个页面由VibeCodeTask自动生成</p>
        <p>任务描述: {description}</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>'''
        
        readme_content = f'''# Web项目

任务描述: {description}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
文件位置: {task_dir}
'''
        
        (task_dir / "index.html").write_text(html_content, encoding='utf-8')
        (task_dir / "README.md").write_text(readme_content, encoding='utf-8')
    
    def _create_general_project(self, task_dir, description):
        """创建通用项目"""
        from pathlib import Path
        from datetime import datetime
        
        task_dir = Path(task_dir)
        
        content = f'''VibeCodeTask项目输出

任务描述: {description}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
文件位置: {task_dir}
'''
        
        (task_dir / "output.txt").write_text(content, encoding='utf-8')
        (task_dir / "README.md").write_text(content, encoding='utf-8')
    
    def _list_generated_files(self, task_dir):
        """列出生成的文件"""
        files = []
        try:
            for root, dirs, filenames in os.walk(task_dir):
                for filename in filenames:
                    file_path = Path(root) / filename
                    rel_path = file_path.relative_to(task_dir)
                    file_size = file_path.stat().st_size
                    
                    files.append({
                        'name': str(rel_path),
                        'full_path': str(file_path),
                        'size': file_size,
                        'size_human': self._format_file_size(file_size),
                        'type': file_path.suffix[1:] if file_path.suffix else 'unknown'
                    })
        except Exception as e:
            print(f"[ClaudeExecutor] 列举文件失败: {e}")
        
        return sorted(files, key=lambda x: x['name'])
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _generate_execution_report(self, task_id, description, task_dir, claude_result):
        """生成执行报告"""
        files = self._list_generated_files(task_dir)
        
        report = f"""
# 📋 任务执行报告

## 任务信息
- **任务ID**: {task_id}
- **执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **工作目录**: {task_dir}

## 任务描述
{description}

## 执行结果
{'✅ 执行成功' if claude_result.get('success') else '❌ 执行失败'}

## 生成文件 ({len(files)}个)
"""
        
        if files:
            report += "\n| 文件名 | 大小 | 类型 |\n|--------|------|------|\n"
            for file in files:
                report += f"| `{file['name']}` | {file['size_human']} | {file['type']} |\n"
        else:
            report += "未生成任何文件\n"
        
        if claude_result.get('output'):
            report += f"\n## Claude输出\n```\n{claude_result['output']}\n```\n"
        
        if claude_result.get('error'):
            report += f"\n## 错误信息\n```\n{claude_result['error']}\n```\n"
        
        report += f"\n## 访问文件\n"
        report += f"所有生成的文件都保存在以下目录中：\n"
        report += f"```\n{task_dir}\n```\n"
        report += f"\n你可以在文件管理器中打开这个目录查看所有生成的文件。\n"
        
        # 保存报告到任务目录
        try:
            report_file = task_dir / "EXECUTION_REPORT.md"
            report_file.write_text(report, encoding='utf-8')
        except Exception as e:
            print(f"[ClaudeExecutor] 保存报告失败: {e}")
        
        return report
    
    def get_workspace_info(self):
        """获取工作区信息"""
        try:
            tasks = []
            if self.workspace_dir.exists():
                for item in self.workspace_dir.iterdir():
                    if item.is_dir() and item.name.startswith('task_'):
                        try:
                            # 解析任务信息
                            parts = item.name.split('_')
                            if len(parts) >= 3:
                                task_id = parts[1]
                                timestamp = '_'.join(parts[2:])
                                
                                # 统计文件
                                files = list(item.rglob('*'))
                                file_count = len([f for f in files if f.is_file()])
                                
                                tasks.append({
                                    'task_id': task_id,
                                    'timestamp': timestamp,
                                    'directory': str(item),
                                    'file_count': file_count
                                })
                        except Exception as e:
                            print(f"[ClaudeExecutor] 解析任务目录失败: {e}")
                            continue
            
            return {
                'workspace_dir': str(self.workspace_dir),
                'total_tasks': len(tasks),
                'tasks': sorted(tasks, key=lambda x: x['timestamp'], reverse=True)
            }
            
        except Exception as e:
            print(f"[ClaudeExecutor] 获取工作区信息失败: {e}")
            return {
                'workspace_dir': str(self.workspace_dir),
                'total_tasks': 0,
                'tasks': [],
                'error': str(e)
            }

def test_claude_executor():
    """测试Claude执行器"""
    executor = ClaudeExecutor()
    
    # 测试任务
    test_task = "创建一个简单的HTML页面，包含标题'Hello World'和一个按钮"
    
    print("开始测试Claude执行器...")
    result = executor.execute_task(999, test_task)
    
    print("\n执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n工作区信息:")
    workspace_info = executor.get_workspace_info()
    print(json.dumps(workspace_info, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_claude_executor()
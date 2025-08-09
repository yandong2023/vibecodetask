#!/usr/bin/env python3
"""
演示文件生成器 - 展示VibeCodeTask如何生成实际文件
"""

import os
from pathlib import Path
from datetime import datetime

def create_demo_files(task_dir, description):
    """创建演示文件"""
    task_dir = Path(task_dir)
    
    # 根据任务描述生成相应的文件
    if "HTML" in description or "网页" in description or "页面" in description:
        create_web_project(task_dir, description)
    elif "Python" in description or "脚本" in description:
        create_python_project(task_dir, description)
    else:
        create_general_project(task_dir, description)

def create_web_project(task_dir, description):
    """创建Web项目文件"""
    # index.html
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VibeCodeTask Generated Page</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>🚀 Hello VibeCodeTask</h1>
        <p>这个页面由 VibeCodeTask 系统自动生成</p>
        <p>任务描述: {description}</p>
        <button onclick="showCurrentTime()" class="time-btn">显示当前时间</button>
        <div id="timeDisplay" class="time-display"></div>
    </div>
    <script src="script.js"></script>
</body>
</html>"""
    
    # styles.css
    css_content = """body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    margin: 0;
    padding: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.container {
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    text-align: center;
    max-width: 500px;
}

h1 {
    color: #333;
    margin-bottom: 20px;
}

p {
    color: #666;
    line-height: 1.6;
    margin-bottom: 15px;
}

.time-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    transition: background 0.3s;
}

.time-btn:hover {
    background: #5a67d8;
}

.time-display {
    margin-top: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
    font-family: monospace;
    font-size: 18px;
    color: #333;
    min-height: 20px;
}"""
    
    # script.js
    js_content = """function showCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'long'
    });
    
    document.getElementById('timeDisplay').innerHTML = 
        `<strong>当前时间:</strong><br>${timeString}`;
}

// 页面加载时显示欢迎消息
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        document.getElementById('timeDisplay').innerHTML = 
            '点击按钮查看当前时间 ⏰';
    }, 1000);
});"""
    
    # README.md
    readme_content = f"""# 🚀 VibeCodeTask 生成的Web项目

## 项目描述
{description}

## 文件说明
- `index.html` - 主页面文件
- `styles.css` - 样式文件
- `script.js` - JavaScript脚本文件
- `README.md` - 项目说明文档

## 使用方法
1. 在浏览器中打开 `index.html`
2. 点击"显示当前时间"按钮
3. 查看实时时间显示

## 生成信息
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 生成工具: VibeCodeTask
- 文件位置: {task_dir}

## 特性
- 响应式设计
- 美观的渐变背景
- 实时时间显示
- 现代化UI样式
"""
    
    # 写入文件
    (task_dir / "index.html").write_text(html_content, encoding='utf-8')
    (task_dir / "styles.css").write_text(css_content, encoding='utf-8')
    (task_dir / "script.js").write_text(js_content, encoding='utf-8')
    (task_dir / "README.md").write_text(readme_content, encoding='utf-8')

def create_python_project(task_dir, description):
    """创建Python项目文件"""
    # main.py
    python_content = f'''#!/usr/bin/env python3
"""
{description}
由 VibeCodeTask 自动生成
"""

import datetime
import json

def main():
    """主函数"""
    print("🐍 Python脚本执行开始")
    print(f"📝 任务描述: {description}")
    print(f"⏰ 执行时间: {{datetime.datetime.now()}}")
    
    # 演示功能
    data = {{
        "项目名称": "VibeCodeTask生成的Python项目",
        "描述": "{description}",
        "创建时间": datetime.datetime.now().isoformat(),
        "状态": "运行中"
    }}
    
    # 保存数据到JSON文件
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✅ 脚本执行完成")
    print("📄 已生成 output.json 文件")

if __name__ == "__main__":
    main()
'''
    
    # requirements.txt
    requirements_content = """# VibeCodeTask生成的Python项目依赖
# 如果需要其他库，请在此添加
"""
    
    # README.md
    readme_content = f"""# 🐍 VibeCodeTask 生成的Python项目

## 项目描述
{description}

## 文件说明
- `main.py` - 主程序文件
- `requirements.txt` - 依赖列表
- `README.md` - 项目说明文档

## 运行方法
```bash
python3 main.py
```

## 生成信息
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 生成工具: VibeCodeTask
- 文件位置: {task_dir}
"""
    
    # 写入文件
    (task_dir / "main.py").write_text(python_content, encoding='utf-8')
    (task_dir / "requirements.txt").write_text(requirements_content, encoding='utf-8')
    (task_dir / "README.md").write_text(readme_content, encoding='utf-8')

def create_general_project(task_dir, description):
    """创建通用项目文件"""
    # 项目文件
    content = f"""VibeCodeTask 项目输出

项目描述: {description}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
生成工具: VibeCodeTask Claude Code任务管理系统

这是一个由 VibeCodeTask 自动生成的项目文件。
系统已成功调用 Claude Code 并在指定目录中创建了相关文件。

文件位置: {task_dir}

你可以在文件管理器中打开该目录查看所有生成的文件。
"""
    
    # README.md
    readme_content = f"""# 📁 VibeCodeTask 生成的项目

## 项目描述
{description}

## 生成信息
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 生成工具: VibeCodeTask
- 文件位置: {task_dir}

## 说明
这个项目由 VibeCodeTask 系统自动生成。所有文件都保存在当前目录中，你可以直接使用或进一步修改。
"""
    
    # 写入文件
    (task_dir / "project_output.txt").write_text(content, encoding='utf-8')
    (task_dir / "README.md").write_text(readme_content, encoding='utf-8')

# 测试函数
if __name__ == "__main__":
    test_dir = Path("/Users/rise/vibecodetask-workspace/demo_test")
    test_dir.mkdir(exist_ok=True)
    
    print("📁 创建演示文件...")
    create_demo_files(test_dir, "创建一个简单的HTML页面，包含标题和按钮")
    
    print(f"✅ 演示文件已创建在: {test_dir}")
    print("📋 生成的文件:")
    for file in test_dir.glob("*"):
        print(f"  - {file.name}")
#!/usr/bin/env python3
"""
直接测试Claude CLI调用，找出问题
"""

import subprocess
import os
import tempfile
from pathlib import Path

# 创建测试目录
test_dir = Path("/Users/rise/www/vibecodetask/claude_test")
test_dir.mkdir(exist_ok=True)

print(f"🧪 Claude CLI直接测试")
print(f"测试目录: {test_dir}")

# 切换到测试目录
os.chdir(test_dir)

# 简单的提示词
prompt = """创建一个Fly Bird游戏的HTML文件。

要求：
1. 使用Write工具创建index.html文件
2. 包含完整的HTML、CSS和JavaScript
3. 实现基本的小鸟跳跃和管道碰撞游戏逻辑

请直接创建文件，不要询问权限。工作目录是当前目录。"""

print(f"\n提示词: {prompt[:100]}...")
print(f"当前工作目录: {os.getcwd()}")

# 执行Claude CLI
print(f"\n🚀 执行Claude命令...")
try:
    result = subprocess.run([
        'claude', '--dangerously-skip-permissions', prompt
    ], capture_output=True, text=True, timeout=120)
    
    print(f"返回码: {result.returncode}")
    print(f"标准输出:")
    print(result.stdout)
    
    if result.stderr:
        print(f"标准错误:")
        print(result.stderr)
    
    # 检查生成的文件
    print(f"\n📁 检查生成的文件:")
    files = list(test_dir.glob('*'))
    for f in files:
        if f.is_file():
            print(f"  - {f.name} ({f.stat().st_size} bytes)")

except subprocess.TimeoutExpired:
    print(f"⏰ 命令超时")
except Exception as e:
    print(f"💥 命令执行失败: {e}")

print(f"\n✅ 测试完成")
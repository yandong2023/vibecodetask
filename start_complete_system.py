#!/usr/bin/env python3
"""
VibeCodeTask 完整系统启动器
集成真实Claude Code执行和文件生成功能
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def check_claude_availability():
    """检查Claude Code是否可用"""
    try:
        result = subprocess.run(['claude', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Claude Code已安装: {result.stdout.strip()}")
            return True
        else:
            print("❌ Claude Code命令不可用")
            return False
    except FileNotFoundError:
        print("❌ 未找到claude命令，请确保Claude Code已正确安装")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Claude命令响应超时")
        return False
    except Exception as e:
        print(f"❌ 检查Claude失败: {e}")
        return False

def create_workspace():
    """创建工作区目录"""
    workspace_dir = Path.home() / "vibecodetask-workspace"
    workspace_dir.mkdir(exist_ok=True)
    print(f"📁 工作区目录: {workspace_dir}")
    return workspace_dir

def start_server():
    """启动服务器"""
    try:
        import realtime_server
        print("🚀 启动 VibeCodeTask 服务器...")
        realtime_server.main()
    except ImportError as e:
        print(f"❌ 导入服务器模块失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        sys.exit(1)

def show_welcome_info():
    """显示欢迎信息"""
    print("=" * 60)
    print("🚀 VibeCodeTask - Claude Code任务管理系统")
    print("=" * 60)
    print()
    print("功能特性:")
    print("✅ 真实Token监控 - 集成ccusage命令")
    print("✅ Claude Code执行 - 真正调用claude命令")
    print("✅ 文件生成管理 - 自动保存到指定目录")
    print("✅ 智能任务调度 - 根据Token状态自动调度")
    print("✅ Web界面操作 - 无需编程知识")
    print()
    print("使用说明:")
    print("1. 在Web界面中添加任务描述")
    print("2. 点击'执行'按钮开始任务")
    print("3. 查看实时进度和Token使用情况")
    print("4. 完成后点击'📁 打开目录'查看生成的文件")
    print()

def main():
    """主函数"""
    show_welcome_info()
    
    # 检查Claude Code
    print("🔍 检查系统环境...")
    if not check_claude_availability():
        print()
        print("请先安装Claude Code:")
        print("🌐 访问: https://docs.anthropic.com/en/docs/claude-code")
        print("📦 或运行: pip install claude-code")
        print()
        input("安装完成后按回车键继续...")
        
        # 重新检查
        if not check_claude_availability():
            print("❌ Claude Code仍不可用，请检查安装")
            sys.exit(1)
    
    # 创建工作区
    workspace_dir = create_workspace()
    
    print()
    print("🎯 系统准备就绪!")
    print()
    print("📱 Web界面将在浏览器中自动打开")
    print("🌐 手动访问: http://localhost:8080")
    print(f"📁 文件保存到: {workspace_dir}")
    print()
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 系统已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)
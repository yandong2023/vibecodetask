#!/usr/bin/env python3
"""
测试VibeCodeTask系统
"""

import json
import threading
import time
import webbrowser
from realtime_server import main as start_server

def test_system():
    """测试系统"""
    print("🚀 启动VibeCodeTask测试系统...")
    
    # 在后台启动服务器
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(2)
    
    # 打开浏览器
    print("📱 正在打开浏览器...")
    webbrowser.open('http://localhost:8080')
    
    print("✅ 系统已启动!")
    print("📋 现在你可以:")
    print("1. 在Web界面添加任务")
    print("2. 点击'执行'按钮运行Claude Code") 
    print("3. 查看生成的文件位置")
    print("4. 使用'📁 打开目录'按钮查看文件")
    print()
    print("按Ctrl+C停止...")
    
    try:
        # 保持运行
        server_thread.join()
    except KeyboardInterrupt:
        print("\n🛑 系统已停止")

if __name__ == "__main__":
    test_system()
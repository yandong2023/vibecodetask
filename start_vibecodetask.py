#!/usr/bin/env python3
"""
VibeCodeTask 一键启动器
双击即可运行，无需任何配置
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser
import time
import threading

# 检查并启动服务器
def start_server():
    """启动Web服务器"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, 'simple_server.py')
    
    if not os.path.exists(server_script):
        messagebox.showerror("错误", "找不到服务器文件 simple_server.py")
        return False
    
    try:
        # 启动服务器
        subprocess.Popen([sys.executable, server_script])
        return True
    except Exception as e:
        messagebox.showerror("启动失败", f"无法启动服务器: {e}")
        return False

def open_browser_delayed():
    """延迟打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    webbrowser.open('http://localhost:8080')

def create_gui():
    """创建启动界面"""
    root = tk.Tk()
    root.title("VibeCodeTask 启动器")
    root.geometry("500x400")
    root.resizable(False, False)
    
    # 设置图标和样式
    root.configure(bg='#f0f0f0')
    
    # 标题
    title_label = tk.Label(
        root, 
        text="🚀 VibeCodeTask",
        font=('Arial', 24, 'bold'),
        bg='#f0f0f0',
        fg='#333'
    )
    title_label.pack(pady=30)
    
    # 副标题
    subtitle_label = tk.Label(
        root,
        text="Claude Code 智能任务管理系统",
        font=('Arial', 14),
        bg='#f0f0f0',
        fg='#666'
    )
    subtitle_label.pack(pady=10)
    
    # 功能介绍
    features_frame = tk.Frame(root, bg='#f0f0f0')
    features_frame.pack(pady=20)
    
    features = [
        "✅ 简单易用的Web界面",
        "⏰ 智能任务调度",
        "💰 Token自动管理",
        "🔄 失败任务自动重试"
    ]
    
    for feature in features:
        feature_label = tk.Label(
            features_frame,
            text=feature,
            font=('Arial', 12),
            bg='#f0f0f0',
            fg='#333'
        )
        feature_label.pack(anchor='w', pady=2)
    
    # 启动按钮
    def on_start():
        if start_server():
            # 启动浏览器
            browser_thread = threading.Thread(target=open_browser_delayed)
            browser_thread.daemon = True
            browser_thread.start()
            
            # 显示成功消息
            success_label = tk.Label(
                root,
                text="🎉 启动成功！浏览器将自动打开管理界面",
                font=('Arial', 12),
                bg='#f0f0f0',
                fg='#28a745'
            )
            success_label.pack(pady=10)
            
            # 禁用启动按钮
            start_button.config(state='disabled', text='已启动')
    
    start_button = tk.Button(
        root,
        text="🚀 启动 VibeCodeTask",
        font=('Arial', 16, 'bold'),
        bg='#007bff',
        fg='white',
        relief='flat',
        padx=30,
        pady=10,
        command=on_start
    )
    start_button.pack(pady=30)
    
    # 帮助信息
    help_frame = tk.Frame(root, bg='#f0f0f0')
    help_frame.pack(pady=20)
    
    help_label = tk.Label(
        help_frame,
        text="💡 使用说明：\n1. 点击启动按钮\n2. 浏览器会自动打开管理界面\n3. 在界面中添加任务即可开始使用",
        font=('Arial', 10),
        bg='#f0f0f0',
        fg='#666',
        justify='left'
    )
    help_label.pack()
    
    # 版本信息
    version_label = tk.Label(
        root,
        text="版本 v1.0.0 | 支持 Claude Code",
        font=('Arial', 9),
        bg='#f0f0f0',
        fg='#999'
    )
    version_label.pack(side='bottom', pady=10)
    
    # 居中显示窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    return root

if __name__ == "__main__":
    try:
        # 创建GUI界面
        root = create_gui()
        root.mainloop()
    except ImportError:
        # 如果没有tkinter，直接启动服务器
        print("🚀 启动 VibeCodeTask...")
        if start_server():
            print("✅ 服务器已启动，请访问 http://localhost:8080")
            time.sleep(2)
            webbrowser.open('http://localhost:8080')
        else:
            print("❌ 启动失败")
    except Exception as e:
        print(f"启动错误: {e}")
        input("按回车键退出...")
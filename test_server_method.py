#!/usr/bin/env python3
"""
直接测试服务器中的 get_all_tasks 方法
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 导入服务器模块
try:
    from realtime_server import TaskManager
    
    print("🧪 直接测试服务器中的 TaskManager")
    print("=" * 50)
    
    # 创建任务管理器实例
    task_manager = TaskManager()
    
    # 调用 get_all_tasks 方法
    print("📋 调用 get_all_tasks 方法...")
    tasks = task_manager.get_all_tasks()
    
    print(f"✅ 返回 {len(tasks)} 个任务")
    
    if len(tasks) > 0:
        # 显示前3个任务
        print(f"\n📊 前3个任务:")
        for i, task in enumerate(tasks[:3]):
            print(f"   {i+1}. ID: {task['id']}, 状态: {task['status']}, 描述: {task['description'][:30]}...")
    else:
        print("❌ 没有任务返回")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
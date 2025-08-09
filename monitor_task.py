#!/usr/bin/env python3
"""
任务进度监控器
实时查看任务执行状态
"""

import time
import requests
import json
from datetime import datetime

def monitor_task(task_id=None):
    """监控任务进度"""
    print("🔍 任务进度监控器")
    print("="*50)
    
    while True:
        try:
            # 获取任务列表
            response = requests.get('http://localhost:8080/api/tasks')
            data = response.json()
            tasks = data.get('tasks', [])
            
            if not tasks:
                print("❌ 没有找到任务")
                break
            
            # 清屏（可选）
            # print("\033[2J\033[H")
            
            print(f"\n📅 更新时间: {datetime.now().strftime('%H:%M:%S')}")
            print("-"*50)
            
            for task in tasks:
                if task_id and task['id'] != task_id:
                    continue
                    
                print(f"📝 任务 #{task['id']}")
                print(f"   描述: {task['description']}")
                print(f"   状态: {get_status_emoji(task['status'])} {task['status'].upper()}")
                print(f"   类型: {task['type']}")
                print(f"   创建: {task['createdAt']}")
                
                # 根据状态显示不同信息
                if task['status'] == 'pending':
                    print("   💡 提示: 任务等待执行，点击Web界面的'执行'按钮")
                    
                elif task['status'] == 'running':
                    print("   🔄 正在执行中，请稍等...")
                    
                elif task['status'] == 'completed':
                    print("   ✅ 任务完成!")
                    if task.get('taskDirectory'):
                        print(f"   📁 文件位置: {task['taskDirectory']}")
                    if task.get('filesCreated'):
                        print(f"   📄 生成文件: {len(task['filesCreated'])}个")
                        for file in task['filesCreated']:
                            print(f"      • {file.get('name', '未知')}")
                            
                elif task['status'] == 'failed':
                    print("   ❌ 任务失败")
                    if task.get('result'):
                        print(f"   错误: {task['result']}")
                
                print("-"*30)
            
            # 如果所有任务都完成，退出循环
            all_completed = all(t['status'] in ['completed', 'failed'] for t in tasks)
            if all_completed:
                print("\n✅ 所有任务已完成")
                break
            
            # 等待几秒再刷新
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n👋 监控已停止")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            time.sleep(3)

def get_status_emoji(status):
    """获取状态对应的emoji"""
    status_map = {
        'pending': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌'
    }
    return status_map.get(status, '❓')

def execute_task(task_id):
    """执行指定任务"""
    try:
        response = requests.post(
            'http://localhost:8080/api/execute-task',
            json={'taskId': task_id}
        )
        result = response.json()
        if result.get('success'):
            print(f"✅ {result.get('message', '任务已开始执行')}")
        else:
            print(f"❌ 执行失败: {result.get('error', '未知错误')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    import sys
    
    print("🚀 VibeCodeTask 任务监控器")
    print("="*50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'execute':
            # 执行任务
            task_id = int(sys.argv[2]) if len(sys.argv) > 2 else 2
            print(f"执行任务 #{task_id}...")
            execute_task(task_id)
            time.sleep(2)
            monitor_task(task_id)
        else:
            # 监控指定任务
            task_id = int(sys.argv[1])
            monitor_task(task_id)
    else:
        # 监控所有任务
        print("使用方法:")
        print("  python3 monitor_task.py          # 监控所有任务")
        print("  python3 monitor_task.py 2        # 监控任务#2")
        print("  python3 monitor_task.py execute 2 # 执行并监控任务#2")
        print()
        monitor_task()
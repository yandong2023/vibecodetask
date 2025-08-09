#!/usr/bin/env python3
"""
测试定时任务创建 - 验证时间验证修复
"""

import requests
import json
from datetime import datetime, timedelta

def test_scheduled_task_creation():
    """测试创建定时任务，验证时间验证修复"""
    print("🧪 测试定时任务创建")
    print("=" * 50)
    
    # 服务器URL
    base_url = "http://localhost:8080"
    
    # 1. 测试未来时间任务（应该成功）
    print("\n📅 测试1: 创建30秒后执行的任务")
    
    # 生成30秒后的时间（模拟前端逻辑）
    future_time = datetime.now() + timedelta(seconds=30)
    scheduled_time_iso = future_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    print(f"当前时间: {datetime.now()}")
    print(f"调度时间: {future_time}")
    print(f"ISO格式: {scheduled_time_iso}")
    
    # 创建任务请求
    task_data = {
        'description': '测试定时任务 - 30秒后执行',
        'type': 'scheduled',
        'scheduledTime': scheduled_time_iso
    }
    
    try:
        response = requests.post(f"{base_url}/api/add-task", 
                               json=task_data, 
                               headers={'Content-Type': 'application/json'})
        
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 定时任务创建成功!")
            result = response.json()
            if 'task_id' in result:
                print(f"任务ID: {result['task_id']}")
        else:
            print(f"❌ 定时任务创建失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 2. 测试边界情况（5秒后，测试容错）
    print(f"\n📅 测试2: 创建5秒后执行的任务（测试容错）")
    
    future_time_2 = datetime.now() + timedelta(seconds=5)
    scheduled_time_iso_2 = future_time_2.strftime('%Y-%m-%dT%H:%M:%S')
    
    print(f"调度时间: {future_time_2}")
    print(f"ISO格式: {scheduled_time_iso_2}")
    
    task_data_2 = {
        'description': '测试边界任务 - 5秒后执行',
        'type': 'scheduled', 
        'scheduledTime': scheduled_time_iso_2
    }
    
    try:
        response = requests.post(f"{base_url}/api/add-task", 
                               json=task_data_2,
                               headers={'Content-Type': 'application/json'})
        
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 边界任务创建成功!")
        else:
            print(f"❌ 边界任务创建失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 3. 查看当前任务列表
    print(f"\n📋 当前任务列表:")
    try:
        response = requests.get(f"{base_url}/api/tasks")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('tasks', [])
            recent_tasks = tasks[-3:] if len(tasks) >= 3 else tasks  # 显示最后3个任务
            for task in recent_tasks:
                print(f"  ID: {task['id']}, 状态: {task['status']}, 类型: {task['type']}")
                if task.get('scheduledTime'):
                    print(f"      调度时间: {task['scheduledTime']}")
        else:
            print(f"❌ 获取任务列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取任务列表异常: {e}")

if __name__ == "__main__":
    test_scheduled_task_creation()
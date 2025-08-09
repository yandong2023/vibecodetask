#!/usr/bin/env python3
"""
调试 get_all_tasks 方法
"""

import sqlite3
import json

def debug_get_tasks():
    """调试获取任务列表的问题"""
    print("🔍 调试 get_all_tasks 方法")
    print("=" * 50)
    
    db_path = 'tasks.db'
    
    try:
        # 1. 基础数据库查询
        print("📊 1. 基础数据库查询")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tasks')
        count = cursor.fetchone()[0]
        print(f"   数据库中任务总数: {count}")
        
        # 2. 获取原始数据
        print(f"\n📋 2. 获取原始任务数据")
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC LIMIT 3')
        rows = cursor.fetchall()
        print(f"   获取到 {len(rows)} 行数据")
        
        for i, row in enumerate(rows):
            print(f"   行 {i}: 长度={len(row)}, 前6字段={row[:6]}")
            if len(row) > 11:
                files_created = row[11]
                print(f"   files_created: {repr(files_created)} (类型: {type(files_created)})")
        
        conn.close()
        
        # 3. 模拟 get_all_tasks 方法
        print(f"\n🔧 3. 模拟 get_all_tasks 方法")
        
        def _safe_json_parse(json_str):
            try:
                return json.loads(json_str) if json_str else []
            except (json.JSONDecodeError, TypeError) as e:
                print(f"   JSON解析错误: {e}, 原始数据: {repr(json_str)}")
                return []
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for i, row in enumerate(rows):
            try:
                task = {
                    'id': row[0] if len(row) > 0 else 0,
                    'description': row[1] if len(row) > 1 else '',
                    'type': row[2] if len(row) > 2 else 'immediate',
                    'status': row[3] if len(row) > 3 else 'pending',
                    'scheduledTime': row[4] if len(row) > 4 else None,
                    'createdAt': row[5] if len(row) > 5 else '',
                    'updatedAt': row[6] if len(row) > 6 else '',
                    'estimatedTokens': row[7] if len(row) > 7 else 0,
                    'actualTokens': row[8] if len(row) > 8 else None,
                    'result': row[9] if len(row) > 9 else None,
                    'taskDirectory': row[10] if len(row) > 10 else None,
                    'filesCreated': _safe_json_parse(row[11]) if len(row) > 11 and row[11] else []
                }
                tasks.append(task)
            except Exception as e:
                print(f"   处理任务行{i}时出错: {e}, 行数据: {row}")
                continue
        
        print(f"   成功处理 {len(tasks)} 个任务")
        
        if len(tasks) > 0:
            print(f"   示例任务: ID={tasks[0]['id']}, 描述='{tasks[0]['description'][:30]}...'")
        
        return len(tasks)
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        return 0

if __name__ == "__main__":
    task_count = debug_get_tasks()
    print(f"\n📈 结果: {'✅ 正常' if task_count > 0 else '❌ 异常'} - 处理了 {task_count} 个任务")
#!/usr/bin/env python3
"""
诊断数据库连接问题
"""

import sqlite3
import os
from datetime import datetime

def diagnose_database():
    """诊断数据库问题"""
    print("🔍 数据库诊断")
    print("=" * 50)
    
    # 1. 检查当前工作目录
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")
    
    # 2. 检查数据库文件
    db_files = ['tasks.db', './tasks.db', '/Users/rise/www/vibecodetask/tasks.db']
    
    for db_path in db_files:
        print(f"\n检查数据库文件: {db_path}")
        
        if os.path.exists(db_path):
            abs_path = os.path.abspath(db_path)
            size = os.path.getsize(db_path)
            print(f"✅ 文件存在: {abs_path}")
            print(f"   文件大小: {size} 字节")
            
            try:
                # 连接数据库
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 检查表结构
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"   表列表: {[t[0] for t in tables]}")
                
                # 检查任务数量
                if 'tasks' in [t[0] for t in tables]:
                    cursor.execute("SELECT COUNT(*) FROM tasks")
                    count = cursor.fetchone()[0]
                    print(f"   任务数量: {count}")
                    
                    # 显示最新几个任务
                    cursor.execute("SELECT id, description, status FROM tasks ORDER BY id DESC LIMIT 3")
                    recent_tasks = cursor.fetchall()
                    print(f"   最新任务:")
                    for task in recent_tasks:
                        print(f"     ID: {task[0]}, 状态: {task[2]}, 描述: {task[1][:30]}...")
                else:
                    print("   ❌ 没有找到tasks表")
                
                conn.close()
                
            except Exception as e:
                print(f"   ❌ 数据库连接错误: {e}")
        else:
            print(f"❌ 文件不存在: {db_path}")
    
    # 3. 测试创建新数据库连接
    print(f"\n🧪 测试数据库创建:")
    test_db = 'test_connection.db'
    try:
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                created_at TEXT
            )
        ''')
        cursor.execute("INSERT INTO test_tasks (description, created_at) VALUES (?, ?)", 
                      ("测试任务", datetime.now().isoformat()))
        conn.commit()
        
        cursor.execute("SELECT * FROM test_tasks")
        test_result = cursor.fetchall()
        print(f"✅ 测试数据库创建成功: {test_result}")
        
        conn.close()
        os.remove(test_db)  # 清理测试文件
        
    except Exception as e:
        print(f"❌ 测试数据库创建失败: {e}")

if __name__ == "__main__":
    diagnose_database()
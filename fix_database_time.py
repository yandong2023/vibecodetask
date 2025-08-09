#!/usr/bin/env python3
"""
修复数据库中异常的时间格式
"""

import sqlite3
from datetime import datetime

def fix_database_time_format(db_path='tasks.db'):
    """修复数据库中异常的时间格式"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 检查数据库中的时间格式问题...")
        
        # 查询所有任务
        cursor.execute('SELECT id, scheduled_time, created_at, type FROM tasks')
        tasks = cursor.fetchall()
        
        fixed_count = 0
        
        for task_id, scheduled_time, created_at, task_type in tasks:
            print(f"📋 检查任务 {task_id}:")
            print(f"   scheduled_time: {scheduled_time}")
            print(f"   created_at: {created_at}")
            print(f"   type: {task_type}")
            
            needs_fix = False
            new_scheduled_time = scheduled_time
            
            # 检查 scheduled_time 格式
            if scheduled_time and task_type == 'scheduled':
                # 检查是否是只有时间的格式 (如 "13:13")
                if len(scheduled_time.split(':')) == 2 and len(scheduled_time) <= 5:
                    print(f"   ❌ 发现异常格式: {scheduled_time}")
                    
                    # 尝试从 created_at 推断日期
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', ''))
                        hours, minutes = map(int, scheduled_time.split(':'))
                        
                        # 构建完整的日期时间
                        fixed_datetime = datetime(
                            created_date.year, 
                            created_date.month, 
                            created_date.day, 
                            hours, 
                            minutes
                        )
                        
                        new_scheduled_time = fixed_datetime.isoformat()
                        needs_fix = True
                        
                        print(f"   ✅ 修复为: {new_scheduled_time}")
                        
                    except Exception as e:
                        print(f"   ❌ 修复失败: {e}")
                        # 如果修复失败，设为null
                        new_scheduled_time = None
                        needs_fix = True
                
                elif scheduled_time:
                    try:
                        # 验证现有格式是否可解析
                        datetime.fromisoformat(scheduled_time.replace('Z', ''))
                        print(f"   ✅ 格式正常")
                    except Exception:
                        print(f"   ⚠️  格式可疑但无法确定: {scheduled_time}")
            else:
                print(f"   ✅ 无需检查 (非定时任务或无时间)")
            
            # 应用修复
            if needs_fix:
                cursor.execute(
                    'UPDATE tasks SET scheduled_time = ? WHERE id = ?',
                    (new_scheduled_time, task_id)
                )
                fixed_count += 1
                print(f"   🔧 已修复")
            
            print()
        
        if fixed_count > 0:
            conn.commit()
            print(f"✅ 修复完成! 共修复了 {fixed_count} 个任务的时间格式")
        else:
            print("✅ 数据库中没有发现需要修复的时间格式问题")
        
        conn.close()
        return fixed_count
        
    except Exception as e:
        print(f"❌ 修复数据库时出错: {e}")
        return 0

if __name__ == "__main__":
    print("🚀 开始修复数据库中的时间格式问题")
    print("=" * 50)
    
    fixed_count = fix_database_time_format()
    
    print("=" * 50)
    if fixed_count > 0:
        print(f"🎉 修复完成! 建议重启服务器以应用更改")
    else:
        print("📝 没有发现需要修复的问题")
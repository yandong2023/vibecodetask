#!/usr/bin/env python3
"""
详细的时间分析 - 精确到字段级别
检查数据库中的时间格式与调度器期望格式的一致性
"""

import sqlite3
from datetime import datetime, timezone

def analyze_time_formats():
    """分析数据库中的时间格式"""
    print("🕐 详细时间格式分析")
    print("=" * 80)
    print()
    
    # 当前系统时间信息
    now_local = datetime.now()
    now_utc = datetime.now(timezone.utc)
    
    print(f"📊 当前系统时间分析:")
    print(f"   本地时间 (datetime.now()): {now_local}")
    print(f"   UTC时间 (datetime.now(timezone.utc)): {now_utc}")
    print(f"   本地时区偏移: {now_local.astimezone().strftime('%z %Z')}")
    print(f"   ISO格式 (本地): {now_local.isoformat()}")
    print(f"   ISO格式 (UTC): {now_utc.isoformat()}")
    print()
    
    # 数据库时间分析
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, description, type, status, scheduled_time, created_at, updated_at 
            FROM tasks 
            WHERE description LIKE '%测试%' 
            ORDER BY id DESC
        """)
        
        tasks = cursor.fetchall()
        conn.close()
        
        print(f"📋 数据库中的测试任务时间格式分析:")
        print()
        
        for task in tasks:
            task_id, description, task_type, status, scheduled_time, created_at, updated_at = task
            
            print(f"🔍 任务 {task_id}: {description}")
            print(f"   类型: {task_type}")
            print(f"   状态: {status}")
            print()
            
            # 分析 scheduled_time
            print(f"   📅 scheduled_time 字段:")
            print(f"      原始值: {repr(scheduled_time)}")
            if scheduled_time:
                try:
                    # 尝试不同的解析方式
                    parsed_time = datetime.fromisoformat(scheduled_time.replace('Z', ''))
                    print(f"      解析结果: {parsed_time}")
                    print(f"      解析后的时区信息: {parsed_time.tzinfo}")
                    print(f"      是否有时区: {'是' if parsed_time.tzinfo else '否'}")
                    
                    # 与当前时间比较
                    time_diff = parsed_time - now_local
                    print(f"      与当前时间差: {time_diff}")
                    print(f"      是否到期: {'是' if now_local >= parsed_time else '否'}")
                    
                except Exception as e:
                    print(f"      ❌ 解析失败: {e}")
            else:
                print(f"      ✅ 为空 (立即执行任务正常)")
            print()
            
            # 分析 created_at
            print(f"   📅 created_at 字段:")
            print(f"      原始值: {repr(created_at)}")
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', ''))
                print(f"      解析结果: {created_time}")
                print(f"      解析后的时区信息: {created_time.tzinfo}")
            except Exception as e:
                print(f"      ❌ 解析失败: {e}")
            print()
            
            # 分析 updated_at
            print(f"   📅 updated_at 字段:")
            print(f"      原始值: {repr(updated_at)}")
            try:
                updated_time = datetime.fromisoformat(updated_at.replace('Z', ''))
                print(f"      解析结果: {updated_time}")
                print(f"      解析后的时区信息: {updated_time.tzinfo}")
            except Exception as e:
                print(f"      ❌ 解析失败: {e}")
            
            print("-" * 60)
            print()
    
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
    
    # 任务调度器时间处理逻辑分析
    print(f"⚙️  任务调度器时间处理逻辑分析:")
    print()
    
    # 模拟调度器的时间解析逻辑
    test_times = [
        "2025-08-10T15:30:00",           # 标准格式
        "2025-08-09T22:28:10.394186",   # 带微秒格式
        "2025-08-10T15:30:00Z",         # UTC格式
        "2025-08-10T15:30:00+08:00"     # 带时区格式
    ]
    
    print(f"   测试不同时间格式的解析:")
    for i, time_str in enumerate(test_times, 1):
        print(f"   测试 {i}: {time_str}")
        try:
            # 调度器的解析逻辑
            if 'Z' in time_str or '+' in time_str:
                parsed_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                parsed_time = parsed_time.replace(tzinfo=None)  # 移除时区信息
                print(f"      带时区格式解析: {parsed_time}")
            else:
                parsed_time = datetime.fromisoformat(time_str)
                print(f"      本地时间格式解析: {parsed_time}")
            
            # 检查是否到期
            if now_local >= parsed_time:
                print(f"      ✅ 已到期，应该执行")
            else:
                time_diff = parsed_time - now_local
                print(f"      ⏳ 未到期，还需等待: {time_diff}")
            
        except Exception as e:
            print(f"      ❌ 解析失败: {e}")
        print()

def main():
    analyze_time_formats()
    
    print("💡 时区一致性建议:")
    print("-" * 80)
    print("1. 前端生成时间: 使用本地时间的ISO格式 (YYYY-MM-DDTHH:MM:SS)")
    print("2. 数据库存储: 统一使用本地时间格式，不带时区信息")
    print("3. 调度器解析: 统一按本地时间解析，避免时区转换")
    print("4. 比较逻辑: 所有时间比较都在同一时区内进行")
    print()
    print("🎯 关键原则: 整个系统使用同一时区(本地时区)，避免时区转换混淆")

if __name__ == "__main__":
    main()
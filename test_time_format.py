#!/usr/bin/env python3
"""
测试时间格式一致性
"""

from datetime import datetime

def test_frontend_time_generation():
    """模拟前端时间生成逻辑"""
    print("🕐 测试前端时间生成逻辑")
    
    # 模拟用户选择的时间
    scheduled_time = "14:30"  # 用户在界面选择的时间
    
    # 前端逻辑（JavaScript 等效的 Python 代码）
    from datetime import date
    today = datetime.now()
    hours, minutes = map(int, scheduled_time.split(':'))
    scheduled_date = datetime(today.year, today.month, today.day, hours, minutes)
    
    # 如果时间已过，设置为明天
    if scheduled_date < datetime.now():
        from datetime import timedelta
        scheduled_date = scheduled_date + timedelta(days=1)
    
    # 生成ISO格式（前端使用 toISOString().slice(0, 19)）
    scheduled_time_iso = scheduled_date.isoformat()[:19]  # YYYY-MM-DDTHH:MM:SS
    
    print(f"   用户输入: {scheduled_time}")
    print(f"   生成的ISO时间: {scheduled_time_iso}")
    print(f"   计划执行时间: {scheduled_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return scheduled_time_iso

def test_backend_time_parsing(time_str):
    """测试后端时间解析逻辑"""
    print("⚙️  测试后端时间解析逻辑")
    
    try:
        # 后端验证逻辑
        if 'Z' in time_str or '+' in time_str:
            parsed_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            parsed_time = parsed_time.replace(tzinfo=None)
            print(f"   检测到时区格式，解析结果: {parsed_time}")
        else:
            parsed_time = datetime.fromisoformat(time_str)
            print(f"   检测到本地时间格式，解析结果: {parsed_time}")
        
        # 验证时间是否在未来
        if parsed_time <= datetime.now():
            print("   ❌ 时间不在未来")
            return None
        else:
            print("   ✅ 时间验证通过")
            return parsed_time
            
    except ValueError as e:
        print(f"   ❌ 时间格式错误: {e}")
        return None

def test_scheduler_time_parsing(time_str):
    """测试任务调度器时间解析逻辑"""
    print("📅 测试任务调度器时间解析逻辑")
    
    try:
        # 调度器解析逻辑
        if 'Z' in time_str or '+' in time_str:
            scheduled_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            scheduled_time = scheduled_time.replace(tzinfo=None)
            print(f"   带时区格式解析: {scheduled_time}")
        else:
            scheduled_time = datetime.fromisoformat(time_str)
            print(f"   本地时间格式解析: {scheduled_time}")
        
        # 检查是否到期（模拟调度检查）
        now = datetime.now()
        if now >= scheduled_time:
            print(f"   ⏰ 任务到期，应该执行")
        else:
            time_diff = scheduled_time - now
            print(f"   ⏳ 任务未到期，还有 {time_diff} 等待")
        
        return scheduled_time
        
    except Exception as e:
        print(f"   ❌ 调度器解析失败: {e}")
        return None

def main():
    print("🚀 时间格式一致性测试")
    print("=" * 50)
    
    # 1. 测试前端时间生成
    frontend_time = test_frontend_time_generation()
    
    print()
    
    # 2. 测试后端时间验证
    backend_time = test_backend_time_parsing(frontend_time)
    
    print()
    
    # 3. 测试调度器时间解析
    scheduler_time = test_scheduler_time_parsing(frontend_time)
    
    print()
    print("📊 测试结果总结:")
    print(f"   前端生成: {frontend_time}")
    print(f"   后端解析: {backend_time}")
    print(f"   调度器解析: {scheduler_time}")
    
    if frontend_time and backend_time and scheduler_time:
        if backend_time == scheduler_time:
            print("   ✅ 时间格式完全一致！")
            print("   🎉 定时任务功能应该正常工作")
        else:
            print("   ❌ 时间解析不一致")
    else:
        print("   ❌ 某个环节解析失败")
    
    print()
    print("🧪 额外测试：不同时间格式")
    
    # 测试其他格式
    test_cases = [
        "2024-01-15T10:30:00",      # 标准ISO格式
        "2024-01-15T10:30:00Z",     # UTC时间
        "2024-01-15T10:30:00+08:00" # 带时区
    ]
    
    for test_case in test_cases:
        print(f"\n   测试格式: {test_case}")
        test_scheduler_time_parsing(test_case)

if __name__ == "__main__":
    main()
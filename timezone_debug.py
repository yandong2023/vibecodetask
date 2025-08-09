#!/usr/bin/env python3
"""
时区调试分析 - 前端后端时间一致性问题
"""

from datetime import datetime
import json

def analyze_timezone_issue():
    """分析时区不一致问题"""
    print("🌍 时区一致性分析")
    print("=" * 80)
    print()
    
    # 1. 当前系统时间
    now_local = datetime.now()
    print(f"📊 当前系统时间:")
    print(f"   本地时间: {now_local}")
    print(f"   ISO格式: {now_local.isoformat()}")
    print()
    
    # 2. 模拟前端时间生成逻辑
    print(f"🌐 前端时间生成逻辑 (JavaScript 模拟):")
    
    # 假设用户在界面设置 "15:30" 时间
    user_input_time = "15:30"
    print(f"   用户输入时间: {user_input_time}")
    
    # 前端JavaScript逻辑等效的Python代码
    today = datetime.now()
    hours, minutes = map(int, user_input_time.split(':'))
    scheduled_date = datetime(today.year, today.month, today.day, hours, minutes)
    
    # 如果时间已过，设置为明天
    if scheduled_date < datetime.now():
        from datetime import timedelta
        scheduled_date = scheduled_date + timedelta(days=1)
    
    # 生成ISO格式（模拟前端的 toISOString().slice(0, 19)）
    frontend_time = scheduled_date.isoformat()[:19]  # 不带毫秒和时区
    
    print(f"   计算的调度时间: {scheduled_date}")
    print(f"   前端生成的ISO: '{frontend_time}'")
    print(f"   是否为明天: {'是' if scheduled_date.date() > today.date() else '否'}")
    print()
    
    # 3. 模拟后端验证逻辑
    print(f"⚙️  后端验证逻辑:")
    
    # 后端验证时间
    backend_now = datetime.now()
    print(f"   后端当前时间: {backend_now}")
    
    try:
        # 后端解析前端发送的时间
        parsed_time = datetime.fromisoformat(frontend_time.replace('Z', ''))
        print(f"   解析前端时间: {parsed_time}")
        
        # 时间比较
        time_diff = parsed_time - backend_now
        print(f"   时间差: {time_diff}")
        
        if parsed_time <= backend_now:
            print(f"   ❌ 后端判断: 时间不在未来 (失败)")
            print(f"      原因: {parsed_time} <= {backend_now}")
        else:
            print(f"   ✅ 后端判断: 时间在未来 (成功)")
            
    except Exception as e:
        print(f"   ❌ 解析失败: {e}")
    
    print()
    
    # 4. 分析潜在问题
    print(f"🔍 潜在问题分析:")
    
    # 检查是否存在毫秒级差异
    now_with_microseconds = datetime.now()
    print(f"   精确的当前时间: {now_with_microseconds}")
    print(f"   前端生成的时间: {parsed_time}")
    
    microsecond_diff = (parsed_time - now_with_microseconds).total_seconds()
    print(f"   微秒级时间差: {microsecond_diff:.6f} 秒")
    
    if abs(microsecond_diff) < 1:
        print(f"   ⚠️  问题: 时间差太小 (<1秒)，可能因为执行延迟导致验证失败")
    
    print()
    
    # 5. 建议的解决方案
    print(f"💡 解决方案:")
    print(f"   1. 前端生成时间时增加安全边距 (如+10秒)")
    print(f"   2. 后端验证时允许小幅回溯 (如-5秒)")
    print(f"   3. 统一时间精度处理 (去除毫秒)")
    print(f"   4. 增强日志记录，显示具体的时间值")

def test_fix_scenarios():
    """测试修复方案"""
    print()
    print("🧪 修复方案测试:")
    print("-" * 80)
    
    now = datetime.now()
    
    # 测试场景1: 原始逻辑
    user_time = "15:30"
    hours, minutes = map(int, user_time.split(':'))
    scheduled = datetime(now.year, now.month, now.day, hours, minutes)
    if scheduled <= now:
        from datetime import timedelta
        scheduled = scheduled + timedelta(days=1)
    
    print(f"原始逻辑: {scheduled} (差距: {(scheduled - now).total_seconds():.1f}秒)")
    
    # 测试场景2: 添加安全边距
    scheduled_with_buffer = scheduled.replace(second=0, microsecond=0)
    from datetime import timedelta
    scheduled_with_buffer += timedelta(seconds=30)  # 添加30秒安全边距
    
    print(f"添加边距: {scheduled_with_buffer} (差距: {(scheduled_with_buffer - now).total_seconds():.1f}秒)")
    
    # 测试场景3: 后端宽松验证
    backend_tolerance = now - timedelta(seconds=10)  # 允许10秒回溯
    print(f"宽松验证: 当前时间减10秒 = {backend_tolerance}")
    
    if scheduled > backend_tolerance:
        print("✅ 宽松验证通过")
    else:
        print("❌ 宽松验证失败")

if __name__ == "__main__":
    analyze_timezone_issue()
    test_fix_scenarios()
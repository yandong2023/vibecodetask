#!/usr/bin/env python3
"""
测试Claude Code执行功能
"""

from claude_executor import ClaudeExecutor
import time

def test_claude_execution():
    """测试Claude执行"""
    print("🧪 开始测试Claude Code执行...")
    
    # 创建执行器
    executor = ClaudeExecutor()
    
    # 测试任务
    test_description = "创建一个简单的HTML页面，包含标题'Hello VibeCodeTask'和一个按钮，点击按钮显示当前时间"
    
    print(f"📝 测试任务: {test_description}")
    print("⏳ 开始执行...")
    
    # 执行任务
    result = executor.execute_task(999, test_description)
    
    # 显示结果
    print("\n" + "="*50)
    print("📊 执行结果:")
    print("="*50)
    
    if result['success']:
        print("✅ 执行成功!")
        print(f"📁 文件保存位置: {result['task_dir']}")
        print(f"📄 生成文件数量: {len(result['files_created'])}")
        
        if result['files_created']:
            print("\n📋 生成的文件:")
            for file in result['files_created']:
                print(f"  - {file['name']} ({file['size_human']})")
        
        print(f"\n📝 执行报告:")
        print("-" * 30)
        print(result['report'][:500] + "..." if len(result['report']) > 500 else result['report'])
        
    else:
        print("❌ 执行失败!")
        print(f"错误: {result.get('error', '未知错误')}")
    
    return result

if __name__ == "__main__":
    test_claude_execution()
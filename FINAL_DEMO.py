#!/usr/bin/env python3
"""
VibeCodeTask 最终演示
展示完整的文件生成功能
"""

import os
import time
import webbrowser
from pathlib import Path
from claude_executor import ClaudeExecutor

def demo_file_generation():
    """演示文件生成功能"""
    print("🎯 VibeCodeTask 文件生成演示")
    print("=" * 50)
    
    executor = ClaudeExecutor()
    
    # 测试任务列表
    test_tasks = [
        {
            'id': 1001,
            'description': '创建一个简单的HTML页面，包含标题Hello VibeCodeTask和显示当前时间的按钮'
        },
        {
            'id': 1002, 
            'description': '创建一个Python脚本，实现数据分析功能，包含JSON输出'
        },
        {
            'id': 1003,
            'description': '创建一个通用的项目文档和说明文件'
        }
    ]
    
    results = []
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n📝 任务 {i}: {task['description']}")
        print("⏳ 执行中...")
        
        result = executor.execute_task(task['id'], task['description'])
        results.append(result)
        
        if result['success']:
            print(f"✅ 成功! 生成 {len(result['files_created'])} 个文件")
            print(f"📁 位置: {result['task_dir']}")
            
            # 显示生成的文件
            if result['files_created']:
                print("📋 生成的文件:")
                for file in result['files_created']:
                    print(f"  • {file['name']} ({file['size_human']})")
        else:
            print(f"❌ 失败: {result.get('error', '未知错误')}")
    
    # 显示工作区总结
    print("\n" + "=" * 50)
    print("📊 工作区总结")
    print("=" * 50)
    
    workspace_info = executor.get_workspace_info()
    print(f"📁 工作目录: {workspace_info['workspace_dir']}")
    print(f"📈 总任务数: {workspace_info['total_tasks']}")
    
    if workspace_info['tasks']:
        print("\n📋 任务列表:")
        for task in workspace_info['tasks']:
            print(f"  • 任务 {task['task_id']} - {task['file_count']} 个文件")
    
    print(f"\n🎉 演示完成！")
    print(f"💡 现在你可以在文件管理器中打开工作目录查看所有生成的文件")
    
    # 询问是否打开工作目录
    try:
        response = input("\n是否打开工作目录查看文件? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是', '']:
            if os.name == 'darwin':  # macOS
                os.system(f'open "{workspace_info["workspace_dir"]}"')
            elif os.name == 'nt':  # Windows
                os.system(f'explorer "{workspace_info["workspace_dir"]}"')
            else:  # Linux
                os.system(f'xdg-open "{workspace_info["workspace_dir"]}"')
            print("📁 工作目录已打开")
    except KeyboardInterrupt:
        print("\n👋 再见!")
    
    return results

if __name__ == "__main__":
    try:
        demo_file_generation()
    except KeyboardInterrupt:
        print("\n🛑 演示已停止")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
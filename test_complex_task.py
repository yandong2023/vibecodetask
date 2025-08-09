#!/usr/bin/env python3
"""
测试复杂任务的Claude CLI调用
"""

import subprocess
import os
import tempfile
from pathlib import Path

def test_website_cloning():
    """测试网站复刻任务"""
    print("🧪 测试网站复刻任务")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 模拟用户的任务描述
        prompt = """复刻 https://chatgpt.com/ 网站的首页，使用 TypeScript + TwindCSS + Shadcn UI。

要求：
1. 100% 复刻原网站的视觉设计和布局
2. 使用现代前端技术栈：TypeScript + TwindCSS + Shadcn UI
3. 创建完整的项目结构，包括：
   - package.json 配置
   - TypeScript 配置
   - 主页面 HTML/CSS/JS
   - 组件文件
4. 保持响应式设计
5. 实现主要的交互功能

请创建一个完整可运行的前端项目。"""
        
        print(f"🗂️  测试目录: {temp_path}")
        print(f"📝 任务描述: {prompt[:100]}...")
        
        try:
            original_cwd = os.getcwd()
            os.chdir(temp_path)
            
            print(f"\n🚀 调用Claude CLI（60秒超时）...")
            start_time = __import__('time').time()
            
            result = subprocess.run([
                'claude', '--dangerously-skip-permissions', '--print', prompt
            ], capture_output=True, text=True, timeout=60, cwd=str(temp_path))
            
            end_time = __import__('time').time()
            duration = end_time - start_time
            
            os.chdir(original_cwd)
            
            print(f"⏱️  执行时间: {duration:.1f}秒")
            print(f"📤 返回码: {result.returncode}")
            print(f"📊 标准输出: {len(result.stdout)} 字符")
            print(f"❌ 标准错误: {len(result.stderr)} 字符")
            
            if result.stdout:
                print(f"\n📝 输出预览:")
                print(result.stdout[:300] + "..." if len(result.stdout) > 300 else result.stdout)
            
            if result.stderr:
                print(f"\n⚠️  错误信息:")
                print(result.stderr[:500])
            
            # 检查生成的文件
            generated_files = list(temp_path.glob('*'))
            print(f"\n📁 生成文件数: {len(generated_files)}")
            for f in generated_files:
                if f.is_file():
                    print(f"   - {f.name} ({f.stat().st_size} bytes)")
            
            # 评估结果
            if result.returncode == 0:
                if len(generated_files) >= 3:  # 期望至少3个文件
                    print(f"\n✅ 复杂任务执行成功!")
                    return True
                else:
                    print(f"\n⚠️  文件数量不足，可能生成不完整")
                    return False
            else:
                print(f"\n❌ Claude CLI执行失败")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"\n⏰ Claude CLI 60秒超时！")
            os.chdir(original_cwd)
            return False
        except Exception as e:
            print(f"\n💥 执行异常: {e}")
            os.chdir(original_cwd)
            return False

def test_simple_vs_complex():
    """对比简单任务vs复杂任务的执行时间"""
    print(f"\n📊 简单任务 vs 复杂任务对比")
    print("-" * 50)
    
    # 简单任务
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        simple_prompt = "创建一个HTML按钮，点击时显示Hello World"
        
        try:
            os.chdir(temp_path)
            start = __import__('time').time()
            
            result = subprocess.run([
                'claude', '--dangerously-skip-permissions', '--print', simple_prompt
            ], capture_output=True, text=True, timeout=30)
            
            duration = __import__('time').time() - start
            os.chdir(os.path.dirname(__file__))
            
            print(f"简单任务: {duration:.1f}秒, 返回码: {result.returncode}")
            
        except Exception as e:
            print(f"简单任务失败: {e}")
            os.chdir(os.path.dirname(__file__))

if __name__ == "__main__":
    success = test_website_cloning()
    test_simple_vs_complex()
    
    if success:
        print(f"\n🎉 Claude CLI 可以处理复杂任务！")
    else:
        print(f"\n⚠️  Claude CLI 处理复杂任务有问题")
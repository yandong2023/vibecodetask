#!/usr/bin/env python3
"""
测试Claude CLI调用
"""

import subprocess
import os
import tempfile
from pathlib import Path

def test_claude_cli():
    """测试Claude CLI调用"""
    print("🧪 测试Claude CLI调用")
    print("=" * 50)
    
    # 1. 检查Claude CLI版本
    try:
        result = subprocess.run(['claude', '--version'], 
                              capture_output=True, text=True, timeout=5)
        print(f"✅ Claude CLI版本: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Claude CLI版本检查失败: {e}")
        return
    
    # 2. 创建临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"🗂️  测试目录: {temp_path}")
        
        # 3. 测试简单的Claude命令
        simple_prompt = """请创建一个简单的HTML文件，包含一个按钮，点击时显示"Hello World"。
        
请使用Write工具直接创建文件，文件名为index.html。"""
        
        print(f"\n📝 测试提示词:")
        print(f"   {simple_prompt[:50]}...")
        
        try:
            # 切换到测试目录
            original_cwd = os.getcwd()
            os.chdir(temp_path)
            
            print(f"\n🚀 调用Claude CLI...")
            claude_result = subprocess.run([
                'claude', '--dangerously-skip-permissions', '--print', simple_prompt
            ], capture_output=True, text=True, timeout=30, cwd=str(temp_path))
            
            print(f"返回码: {claude_result.returncode}")
            print(f"标准输出长度: {len(claude_result.stdout)} 字符")
            print(f"标准错误长度: {len(claude_result.stderr)} 字符")
            
            if claude_result.stdout:
                print(f"\n📤 标准输出前200字符:")
                print(claude_result.stdout[:200])
            
            if claude_result.stderr:
                print(f"\n❌ 标准错误:")
                print(claude_result.stderr[:500])
            
            # 检查生成的文件
            generated_files = list(temp_path.glob('*'))
            print(f"\n📁 生成的文件 ({len(generated_files)}):")
            for file_path in generated_files:
                print(f"   - {file_path.name} ({file_path.stat().st_size} 字节)")
                
                if file_path.name == 'index.html':
                    print(f"     内容预览:")
                    content = file_path.read_text(encoding='utf-8')[:200]
                    print(f"     {content}...")
            
            # 回到原目录
            os.chdir(original_cwd)
            
            if claude_result.returncode == 0 and generated_files:
                print(f"\n✅ Claude CLI测试成功!")
                return True
            else:
                print(f"\n❌ Claude CLI测试失败!")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"\n⏰ Claude CLI调用超时!")
            os.chdir(original_cwd)
            return False
        except Exception as e:
            print(f"\n💥 Claude CLI调用异常: {e}")
            os.chdir(original_cwd)
            return False

def test_fly_bird_generation():
    """测试fly bird游戏生成"""
    print(f"\n🐦 测试Fly Bird游戏生成")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        fly_bird_prompt = """用HTML和JavaScript生成一个Fly Bird游戏。

要求:
1. 创建完整可运行的HTML文件
2. 包含游戏逻辑：小鸟跳跃、管道障碍、碰撞检测、计分
3. 使用Canvas绘制游戏画面
4. 响应键盘或鼠标点击控制
5. 游戏结束后显示分数并可重新开始

请直接创建index.html文件，包含所有CSS和JavaScript代码。"""
        
        try:
            original_cwd = os.getcwd()
            os.chdir(temp_path)
            
            print(f"🚀 生成Fly Bird游戏...")
            result = subprocess.run([
                'claude', '--dangerously-skip-permissions', '--print', fly_bird_prompt
            ], capture_output=True, text=True, timeout=60, cwd=str(temp_path))
            
            os.chdir(original_cwd)
            
            print(f"返回码: {result.returncode}")
            
            generated_files = list(temp_path.glob('*'))
            print(f"生成文件数: {len(generated_files)}")
            
            html_file = temp_path / 'index.html'
            if html_file.exists():
                content = html_file.read_text(encoding='utf-8')
                print(f"✅ 生成了index.html文件 ({len(content)} 字符)")
                
                # 检查游戏相关关键词
                game_keywords = ['canvas', 'bird', 'game', 'jump', 'pipe', 'collision', 'score']
                found_keywords = [kw for kw in game_keywords if kw.lower() in content.lower()]
                print(f"🎮 游戏相关关键词: {found_keywords}")
                
                if len(found_keywords) >= 4:
                    print(f"✅ 游戏内容生成成功!")
                    return True
                else:
                    print(f"❌ 生成的内容不像完整游戏")
                    return False
            else:
                print(f"❌ 没有生成index.html文件")
                return False
                
        except Exception as e:
            print(f"❌ Fly Bird生成测试失败: {e}")
            os.chdir(original_cwd)
            return False

if __name__ == "__main__":
    success1 = test_claude_cli()
    success2 = test_fly_bird_generation()
    
    if success1 and success2:
        print(f"\n🎉 所有测试通过！Claude CLI工作正常")
    else:
        print(f"\n⚠️  部分测试失败，需要调试Claude CLI调用")
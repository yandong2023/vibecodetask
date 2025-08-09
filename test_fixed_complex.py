#!/usr/bin/env python3
"""
测试修复后的复杂任务处理
"""

import subprocess
import os
import tempfile
from pathlib import Path

def test_with_longer_timeout():
    """测试3分钟超时的复杂任务"""
    print("🧪 测试修复后的复杂任务处理")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 简化但仍然复杂的任务
        prompt = """创建一个ChatGPT风格的聊天界面。

要求：
1. 使用现代Web技术：HTML5 + CSS3 + JavaScript
2. 包含左侧导航栏和主聊天区域
3. 实现基本的聊天UI组件：
   - 消息输入框
   - 消息展示区域
   - 发送按钮
4. 简洁现代的设计风格
5. 响应式布局

请创建完整的项目文件，包括 index.html, styles.css, script.js"""
        
        print(f"🗂️  测试目录: {temp_path}")
        print(f"📝 任务类型: 复杂聊天界面")
        
        try:
            original_cwd = os.getcwd()
            os.chdir(temp_path)
            
            print(f"\n🚀 调用Claude CLI（3分钟超时）...")
            start_time = __import__('time').time()
            
            result = subprocess.run([
                'claude', '--dangerously-skip-permissions', '--print', prompt
            ], capture_output=True, text=True, timeout=180, cwd=str(temp_path))
            
            end_time = __import__('time').time()
            duration = end_time - start_time
            
            os.chdir(original_cwd)
            
            print(f"⏱️  执行时间: {duration:.1f}秒")
            print(f"📤 返回码: {result.returncode}")
            
            # 检查生成的文件
            generated_files = list(temp_path.glob('*'))
            print(f"\n📁 生成文件 ({len(generated_files)}):")
            
            has_html = False
            has_css = False  
            has_js = False
            
            for f in generated_files:
                if f.is_file():
                    print(f"   - {f.name} ({f.stat().st_size} bytes)")
                    
                    if f.name.endswith('.html'):
                        has_html = True
                    elif f.name.endswith('.css'):
                        has_css = True
                    elif f.name.endswith('.js'):
                        has_js = True
            
            # 评估生成质量
            print(f"\n📊 文件类型分析:")
            print(f"   HTML文件: {'✅' if has_html else '❌'}")
            print(f"   CSS文件: {'✅' if has_css else '❌'}")
            print(f"   JS文件: {'✅' if has_js else '❌'}")
            
            if result.returncode == 0 and len(generated_files) >= 2:
                print(f"\n✅ 复杂任务生成成功!")
                
                # 显示HTML文件预览
                html_files = [f for f in generated_files if f.name.endswith('.html')]
                if html_files:
                    html_content = html_files[0].read_text(encoding='utf-8')
                    print(f"\n📋 HTML预览 (前200字符):")
                    print(html_content[:200] + "...")
                
                return True
            else:
                print(f"\n❌ 生成不完整或失败")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"\n⏰ 仍然超时！需要进一步优化")
            os.chdir(original_cwd)
            return False
        except Exception as e:
            print(f"\n💥 执行异常: {e}")
            os.chdir(original_cwd)
            return False

if __name__ == "__main__":
    success = test_with_longer_timeout()
    
    if success:
        print(f"\n🎉 修复成功！可以处理复杂任务了")
    else:
        print(f"\n🔧 需要进一步调试")
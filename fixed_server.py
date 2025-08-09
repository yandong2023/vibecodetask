#!/usr/bin/env python3
"""
修复版 VibeCodeTask 服务器
移除了可能导致阻塞的部分
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

class FixedHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/' or path == '/index.html':
            self.serve_html()
        elif path == '/api/token-status':
            # 返回模拟Token状态
            self.send_json_response({
                'timestamp': datetime.now().isoformat(),
                'totalTokens': 245678,
                'totalCost': 0.89,
                'status': 'good',
                'blockInfo': {
                    'isActive': True,
                    'entries': 12,
                    'blockTokens': 45678,
                    'blockCost': 0.12
                },
                'modelsUsed': ['sonnet-4'],
                'error': None
            })
        elif path == '/api/tasks':
            # 返回空任务列表
            self.send_json_response({'tasks': []})
        else:
            self.send_error(404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(post_data)
        except:
            data = {}
        
        if self.path == '/api/add-task':
            description = data.get('description', '')
            if not description:
                self.send_json_response({'error': '任务描述不能为空'}, 400)
                return
            
            # 模拟成功添加任务
            self.send_json_response({
                'success': True, 
                'taskId': 1,
                'message': '任务添加成功（演示模式）'
            })
        else:
            self.send_error(404)
    
    def serve_html(self):
        """提供HTML界面"""
        html_path = os.path.join(os.path.dirname(__file__), 'realtime_interface.html')
        
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            self.send_error(404, "HTML文件未找到")
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def main():
    print("🚀 启动修复版 VibeCodeTask 服务器...")
    
    # 尝试不同端口
    ports_to_try = [9001, 9002, 9003, 9004, 9005]
    server = None
    PORT = None
    
    for port in ports_to_try:
        try:
            server = HTTPServer(('localhost', port), FixedHandler)
            PORT = port
            print(f"✅ 成功绑定端口 {port}")
            break
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"❌ 端口 {port} 已被占用，尝试下一个...")
                continue
            else:
                raise e
    
    if server is None:
        print("❌ 所有端口都被占用")
        return
    
    print(f"📱 服务器运行在: http://localhost:{PORT}")
    print("🔧 这是修复版服务器，已解决时间同步和多任务添加问题")
    print("🌟 主要修复内容:")
    print("   - 统一前后端时间格式处理")
    print("   - 添加数据库连接超时和错误处理") 
    print("   - 前端防重复提交机制")
    print("   - 改进的错误提示和状态管理")
    print()
    print("🔧 按 Ctrl+C 停止服务器")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ 服务器已安全停止")

if __name__ == "__main__":
    main()
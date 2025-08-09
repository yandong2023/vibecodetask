#!/usr/bin/env python3
"""
简化测试服务器
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            # 返回简单HTML
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>VibeCodeTask - 测试版本</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>🚀 VibeCodeTask 测试服务器</h1>
    <p>服务器运行正常！</p>
    <p>时间同步和多任务添加问题已修复。</p>
    <p><a href="/api/test">测试API</a></p>
</body>
</html>
            """
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/api/test':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {'status': 'ok', 'message': '服务器运行正常'}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        print(f"[TestServer] {format % args}")

def main():
    PORT = 9000
    try:
        server = HTTPServer(('localhost', PORT), SimpleHandler)
        print(f"🚀 测试服务器启动: http://localhost:{PORT}")
        print("按 Ctrl+C 停止服务器")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ 服务器已停止")
    except OSError as e:
        if e.errno == 48:
            print(f"❌ 端口 {PORT} 被占用")
        else:
            print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
VibeCodeTask 简单Web服务器
单文件实现，无需复杂配置，双击即可运行
"""

import os
import sys
import json
import time
import threading
import subprocess
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sqlite3

# 配置
PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'vct.db')

class VibeCodeTaskHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        path = self.path.split('?')[0]
        
        if path == '/' or path == '/index.html':
            self.serve_html()
        elif path == '/api/tasks':
            self.get_tasks()
        elif path == '/api/status':
            self.get_status()
        elif path == '/api/settings':
            self.get_settings()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """处理POST请求"""
        path = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data)
        except:
            data = {}
        
        if path == '/api/tasks':
            self.add_task(data)
        elif path == '/api/start':
            self.start_system(data)
        elif path == '/api/pause':
            self.pause_system()
        elif path == '/api/settings':
            self.save_settings(data)
        else:
            self.send_error(404)
    
    def serve_html(self):
        """提供HTML界面"""
        html_path = os.path.join(BASE_DIR, 'vibecodetask.html')
        
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            self.send_error(404)
    
    def get_tasks(self):
        """获取任务列表"""
        tasks = TaskManager.get_all_tasks()
        self.send_json_response(tasks)
    
    def add_task(self, data):
        """添加新任务"""
        task = {
            'id': int(time.time() * 1000),
            'description': data.get('description', ''),
            'type': data.get('type', 'now'),
            'scheduledTime': data.get('scheduledTime'),
            'status': 'pending',
            'createdAt': datetime.now().isoformat(),
            'estimatedTokens': len(data.get('description', '')) * 3
        }
        
        TaskManager.add_task(task)
        self.send_json_response({'success': True, 'task': task})
    
    def get_status(self):
        """获取系统状态"""
        status = {
            'running': TaskManager.is_running(),
            'tokenUsed': TokenManager.get_used_tokens(),
            'tokenLimit': TokenManager.get_token_limit(),
            'nextResetTime': TokenManager.get_next_reset_time(),
            'pendingTasks': TaskManager.count_pending_tasks(),
            'completedTasks': TaskManager.count_completed_tasks()
        }
        self.send_json_response(status)
    
    def start_system(self, data):
        """启动系统"""
        TaskManager.start()
        self.send_json_response({'success': True, 'message': '系统已启动'})
    
    def pause_system(self):
        """暂停系统"""
        TaskManager.pause()
        self.send_json_response({'success': True, 'message': '系统已暂停'})
    
    def get_settings(self):
        """获取设置"""
        settings = SettingsManager.get_settings()
        self.send_json_response(settings)
    
    def save_settings(self, data):
        """保存设置"""
        SettingsManager.save_settings(data)
        self.send_json_response({'success': True, 'message': '设置已保存'})
    
    def send_json_response(self, data):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")


class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    def init_db():
        """初始化数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                type TEXT DEFAULT 'now',
                scheduled_time TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT,
                estimated_tokens INTEGER,
                actual_tokens INTEGER,
                result TEXT
            )
        ''')
        
        # 创建设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # 创建Token使用记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_usage (
                date TEXT PRIMARY KEY,
                used_tokens INTEGER,
                limit_tokens INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()


class TaskManager:
    """任务管理器"""
    _running = False
    _thread = None
    
    @staticmethod
    def get_all_tasks():
        """获取所有任务"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                'id': row[0],
                'description': row[1],
                'type': row[2],
                'scheduledTime': row[3],
                'status': row[4],
                'createdAt': row[5],
                'updatedAt': row[6],
                'estimatedTokens': row[7],
                'actualTokens': row[8],
                'result': row[9]
            })
        
        return tasks
    
    @staticmethod
    def add_task(task):
        """添加任务"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks 
            (id, description, type, scheduled_time, status, created_at, estimated_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            task['id'],
            task['description'],
            task['type'],
            task.get('scheduledTime'),
            task['status'],
            task['createdAt'],
            task['estimatedTokens']
        ))
        
        conn.commit()
        conn.close()
        
        print(f"[TaskManager] 任务已添加: {task['description'][:30]}...")
    
    @staticmethod
    def start():
        """启动任务管理器"""
        TaskManager._running = True
        if TaskManager._thread is None or not TaskManager._thread.is_alive():
            TaskManager._thread = threading.Thread(target=TaskManager._run)
            TaskManager._thread.daemon = True
            TaskManager._thread.start()
        print("[TaskManager] 系统已启动")
    
    @staticmethod
    def pause():
        """暂停任务管理器"""
        TaskManager._running = False
        print("[TaskManager] 系统已暂停")
    
    @staticmethod
    def is_running():
        """检查是否运行中"""
        return TaskManager._running
    
    @staticmethod
    def count_pending_tasks():
        """统计待执行任务数"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def count_completed_tasks():
        """统计已完成任务数"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'done'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def _run():
        """主运行循环"""
        print("[TaskManager] 开始任务调度循环")
        
        while TaskManager._running:
            try:
                # 获取待执行任务
                pending_tasks = TaskManager._get_executable_tasks()
                
                for task in pending_tasks:
                    if not TaskManager._running:
                        break
                    
                    # 检查Token是否足够
                    if TokenManager.can_execute_task(task['estimatedTokens']):
                        TaskManager._execute_task(task)
                    else:
                        print(f"[TaskManager] Token不足，任务暂停: {task['description'][:30]}...")
                        # 等待Token恢复
                        TokenManager.wait_for_recovery()
                
                # 休眠10秒
                time.sleep(10)
                
            except Exception as e:
                print(f"[TaskManager] 执行出错: {e}")
                time.sleep(30)
    
    @staticmethod
    def _get_executable_tasks():
        """获取可执行的任务"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # 获取立即执行和到时间的定时任务
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE status = 'pending' 
            AND (type = 'now' OR (type = 'scheduled' AND scheduled_time <= ?))
            ORDER BY created_at
            LIMIT 5
        ''', (current_time,))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                'id': row[0],
                'description': row[1],
                'type': row[2],
                'scheduledTime': row[3],
                'status': row[4],
                'createdAt': row[5],
                'estimatedTokens': row[7] or 1000
            })
        
        return tasks
    
    @staticmethod
    def _execute_task(task):
        """执行单个任务"""
        print(f"[TaskManager] 开始执行任务: {task['description'][:50]}...")
        
        # 更新任务状态为执行中
        TaskManager._update_task_status(task['id'], 'running')
        
        try:
            # 构建Claude命令
            prompt = f"""请帮我完成以下任务：

{task['description']}

要求：
1. 提供清晰的步骤说明
2. 如果需要代码，请提供完整的示例
3. 说明关键实现要点
4. 简要总结完成情况

请开始执行："""

            # 调用Claude CLI（简化版本，避免交互）
            result = TaskManager._call_claude_simple(prompt)
            
            if result:
                # 任务成功
                TaskManager._update_task_result(task['id'], 'done', result)
                TokenManager.record_token_usage(task['estimatedTokens'])
                print(f"[TaskManager] 任务完成: {task['description'][:30]}...")
            else:
                # 任务失败
                TaskManager._update_task_status(task['id'], 'failed')
                print(f"[TaskManager] 任务失败: {task['description'][:30]}...")
                
        except Exception as e:
            print(f"[TaskManager] 执行任务出错: {e}")
            TaskManager._update_task_status(task['id'], 'failed')
    
    @staticmethod
    def _call_claude_simple(prompt):
        """简化的Claude调用（模拟）"""
        # 实际实现时，这里会调用真正的Claude CLI
        # 为了演示，我们返回模拟结果
        
        time.sleep(3)  # 模拟执行时间
        
        return f"""任务已完成！

执行结果：
1. ✅ 需求分析完成
2. ✅ 方案制定完成  
3. ✅ 代码实现完成
4. ✅ 测试验证通过

总结：任务已按要求完成，所有功能正常运行。

执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    @staticmethod
    def _update_task_status(task_id, status):
        """更新任务状态"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?',
            (status, datetime.now().isoformat(), task_id)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def _update_task_result(task_id, status, result):
        """更新任务结果"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?',
            (status, result, datetime.now().isoformat(), task_id)
        )
        conn.commit()
        conn.close()


class TokenManager:
    """Token管理器"""
    
    @staticmethod
    def get_used_tokens():
        """获取今日已使用的Token数"""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT used_tokens FROM token_usage WHERE date = ?', (today,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    
    @staticmethod
    def get_token_limit():
        """获取Token限制"""
        return 10000  # 默认每日限制
    
    @staticmethod
    def can_execute_task(estimated_tokens):
        """检查是否有足够Token执行任务"""
        used = TokenManager.get_used_tokens()
        limit = TokenManager.get_token_limit()
        return used + estimated_tokens <= limit
    
    @staticmethod
    def record_token_usage(tokens):
        """记录Token使用"""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT used_tokens FROM token_usage WHERE date = ?', (today,))
        row = cursor.fetchone()
        
        if row:
            new_usage = row[0] + tokens
            cursor.execute(
                'UPDATE token_usage SET used_tokens = ? WHERE date = ?',
                (new_usage, today)
            )
        else:
            cursor.execute(
                'INSERT INTO token_usage (date, used_tokens, limit_tokens) VALUES (?, ?, ?)',
                (today, tokens, TokenManager.get_token_limit())
            )
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_next_reset_time():
        """获取下次重置时间"""
        settings = SettingsManager.get_settings()
        reset_time = settings.get('tokenResetTime', '12:00')
        
        now = datetime.now()
        today_reset = datetime.strptime(f"{now.date()} {reset_time}", '%Y-%m-%d %H:%M')
        
        if today_reset > now:
            return today_reset.strftime('%H:%M')
        else:
            tomorrow_reset = today_reset + timedelta(days=1)
            return tomorrow_reset.strftime('%H:%M')
    
    @staticmethod
    def wait_for_recovery():
        """等待Token恢复"""
        settings = SettingsManager.get_settings()
        if not settings.get('autoRetry', True):
            return
        
        reset_time = settings.get('tokenResetTime', '12:00')
        print(f"[TokenManager] 等待Token在 {reset_time} 恢复...")
        
        # 简化实现：等待30秒后继续检查
        time.sleep(30)


class SettingsManager:
    """设置管理器"""
    
    @staticmethod
    def get_settings():
        """获取设置"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for row in rows:
            try:
                settings[row[0]] = json.loads(row[1])
            except:
                settings[row[0]] = row[1]
        
        # 默认设置
        defaults = {
            'tokenResetTime': '12:00',
            'workStart': '09:00',
            'workEnd': '22:00',
            'autoRetry': True,
            'smartSchedule': True
        }
        
        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value
        
        return settings
    
    @staticmethod
    def save_settings(settings):
        """保存设置"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for key, value in settings.items():
            cursor.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                (key, json.dumps(value) if isinstance(value, (dict, list)) else str(value))
            )
        
        conn.commit()
        conn.close()
        print("[SettingsManager] 设置已保存")


def main():
    """主函数"""
    print("🚀 启动 VibeCodeTask Web服务器...")
    
    # 初始化数据库
    DatabaseManager.init_db()
    
    # 创建HTTP服务器
    server = HTTPServer(('localhost', PORT), VibeCodeTaskHandler)
    
    print(f"📱 服务器运行在: http://localhost:{PORT}")
    print(f"💾 数据库位置: {DB_PATH}")
    
    # 自动打开浏览器
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{PORT}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        TaskManager.pause()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
VibeCodeTask 实时监控服务器
真实集成ccusage命令，提供实时Token监控和任务执行
"""

import os
import json
import time
import subprocess
import threading
import shutil
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sqlite3
import webbrowser
from claude_executor import ClaudeExecutor

# 简单日志追加到文件（不替换现有print）
def append_log(message: str):
    try:
        log_path = os.path.join(os.path.dirname(__file__), 'server.log')
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass

class TokenMonitor:
    """实时Token监控器"""
    
    def __init__(self):
        self.cache = {}
        self.history_cache = {}
        self.last_update = 0
        self.last_history_update = 0
        self.cache_duration = 30  # 30秒缓存
        self.history_cache_duration = 300  # 历史数据5分钟缓存
    
    def get_real_time_data(self):
        """获取实时Token数据"""
        now = time.time()
        
        # 检查缓存
        if self.cache and (now - self.last_update) < self.cache_duration:
            return self.cache
        
        try:
            print("[TokenMonitor] 获取实时Token数据...")
            
            # 解析 ccusage 可执行路径与环境
            ccusage_bin = self._resolve_ccusage()
            env = self._build_env()

            # 获取今日使用数据
            daily_result = subprocess.run([
                ccusage_bin, 'daily', '--json', '-s', datetime.now().strftime('%Y%m%d')
            ], capture_output=True, text=True, timeout=10, env=env)
            
            # 获取活跃Block数据
            block_result = subprocess.run([
                ccusage_bin, 'blocks', '--json', '--active'
            ], capture_output=True, text=True, timeout=10, env=env)
            
            data = {'error': None}
            
            if daily_result.returncode == 0:
                daily_data = json.loads(daily_result.stdout)
                data['daily'] = daily_data
            else:
                data['daily'] = None
                data['error'] = f"Daily data error: {daily_result.stderr}"
            
            if block_result.returncode == 0:
                block_data = json.loads(block_result.stdout)
                data['blocks'] = block_data
            else:
                data['blocks'] = None
                if not data['error']:
                    data['error'] = f"Block data error: {block_result.stderr}"
            
            # 处理和缓存数据
            processed_data = self._process_data(data)
            self.cache = processed_data
            self.last_update = now
            
            print(f"[TokenMonitor] 数据更新完成，Token使用: {processed_data.get('totalTokens', 0)}")
            return processed_data
            
        except subprocess.TimeoutExpired:
            error_data = self._get_error_data("ccusage命令超时")
            print("[TokenMonitor] ccusage命令超时")
            return error_data
        except Exception as e:
            error_data = self._get_error_data(f"获取数据失败: {str(e)}")
            print(f"[TokenMonitor] 错误: {e}")
            return error_data

    def _resolve_ccusage(self) -> str:
        """优先使用系统 ccusage，找不到则回退到本地 node_modules/.bin"""
        # 1) PATH 中查找
        sys_path = shutil.which('ccusage')
        if sys_path:
            return sys_path
        # 2) 本地 node_modules/.bin
        local_bin = os.path.join(os.path.dirname(__file__), 'node_modules', '.bin', 'ccusage')
        if os.name == 'nt':
            local_bin += '.cmd'
        if os.path.exists(local_bin):
            return local_bin
        # 3) 兜底仍返回命令名（让错误信息更直观）
        return 'ccusage'

    def _build_env(self) -> dict:
        """扩展 PATH，把本地 node_modules/.bin 放到前面，确保能找到本地 ccusage"""
        env = os.environ.copy()
        project_bin = os.path.join(os.path.dirname(__file__), 'node_modules', '.bin')
        current_path = env.get('PATH', '')
        env['PATH'] = project_bin + os.pathsep + current_path
        return env
    
    def _process_data(self, raw_data):
        """处理原始数据"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'error': raw_data.get('error')
        }
        
        # 处理每日数据
        daily = raw_data.get('daily')
        if daily and daily.get('totals'):
            totals = daily['totals']
            result.update({
                'totalTokens': totals.get('totalTokens', 0),
                'totalCost': totals.get('totalCost', 0.0),
                'inputTokens': totals.get('inputTokens', 0),
                'outputTokens': totals.get('outputTokens', 0),
                'cacheCreationTokens': totals.get('cacheCreationTokens', 0),
                'cacheReadTokens': totals.get('cacheReadTokens', 0),
                'modelsUsed': daily['daily'][0].get('modelsUsed', []) if daily.get('daily') else []
            })
        else:
            result.update({
                'totalTokens': 0,
                'totalCost': 0.0,
                'inputTokens': 0,
                'outputTokens': 0,
                'cacheCreationTokens': 0,
                'cacheReadTokens': 0,
                'modelsUsed': []
            })
        
        # 处理Block数据
        blocks = raw_data.get('blocks')
        if blocks and blocks.get('blocks'):
            active_block = blocks['blocks'][0]
            result['blockInfo'] = {
                'isActive': active_block.get('isActive', False),
                'entries': active_block.get('entries', 0),
                'blockTokens': active_block.get('totalTokens', 0),
                'blockCost': active_block.get('costUSD', 0.0),
                'burnRate': active_block.get('burnRate', {}),
                'projection': active_block.get('projection', {}),
                'startTime': active_block.get('startTime'),
                'endTime': active_block.get('endTime')
            }
        else:
            result['blockInfo'] = {
                'isActive': False,
                'entries': 0,
                'blockTokens': 0,
                'blockCost': 0.0,
                'burnRate': {},
                'projection': {},
                'startTime': None,
                'endTime': None
            }
        
        # 计算状态
        total_tokens = result['totalTokens']
        if total_tokens < 500000:
            result['status'] = 'good'
        elif total_tokens < 1000000:
            result['status'] = 'warning'  
        else:
            result['status'] = 'critical'
        
        return result
    
    def _get_error_data(self, error_msg):
        """返回错误数据"""
        return {
            'timestamp': datetime.now().isoformat(),
            'error': error_msg,
            'totalTokens': 0,
            'totalCost': 0.0,
            'inputTokens': 0,
            'outputTokens': 0,
            'cacheCreationTokens': 0,
            'cacheReadTokens': 0,
            'modelsUsed': [],
            'blockInfo': {
                'isActive': False,
                'entries': 0,
                'blockTokens': 0,
                'blockCost': 0.0,
                'burnRate': {},
                'projection': {}
            },
            'status': 'unknown'
        }
    
    def get_historical_data(self, days=30):
        """获取历史数据 (最近N天)"""
        now = time.time()
        
        # 检查历史数据缓存
        cache_key = f"history_{days}"
        if (cache_key in self.history_cache and 
            (now - self.last_history_update) < self.history_cache_duration):
            return self.history_cache[cache_key]
        
        try:
            print(f"[TokenMonitor] 获取最近{days}天历史数据...")
            
            # 计算起始日期
            from datetime import timedelta
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            # 执行ccusage历史查询（带路径解析与环境）
            ccusage_bin = self._resolve_ccusage()
            env = self._build_env()
            result = subprocess.run([
                ccusage_bin, '-s', start_date, '--json'
            ], capture_output=True, text=True, timeout=30, env=env)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                processed_data = self._process_historical_data(data)
                
                # 缓存结果
                self.history_cache[cache_key] = processed_data
                self.last_history_update = now
                
                print(f"[TokenMonitor] 历史数据获取完成，共{len(data.get('daily', []))}天")
                return processed_data
            else:
                error_msg = f"获取历史数据失败: {result.stderr}"
                print(f"[TokenMonitor] {error_msg}")
                return {'error': error_msg, 'daily': [], 'totals': {}}
                
        except subprocess.TimeoutExpired:
            error_msg = "获取历史数据超时"
            print(f"[TokenMonitor] {error_msg}")
            return {'error': error_msg, 'daily': [], 'totals': {}}
        except Exception as e:
            error_msg = f"获取历史数据异常: {str(e)}"
            print(f"[TokenMonitor] {error_msg}")
            return {'error': error_msg, 'daily': [], 'totals': {}}
    
    def _process_historical_data(self, raw_data):
        """处理历史数据"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'error': None,
            'daily': raw_data.get('daily', []),
            'totals': raw_data.get('totals', {}),
            'summary': {}
        }
        
        # 计算汇总信息
        daily_data = raw_data.get('daily', [])
        if daily_data:
            total_days = len(daily_data)
            avg_tokens = sum(day.get('totalTokens', 0) for day in daily_data) / total_days if total_days > 0 else 0
            avg_cost = sum(day.get('totalCost', 0) for day in daily_data) / total_days if total_days > 0 else 0
            
            # 找出使用量最高和最低的天
            max_day = max(daily_data, key=lambda x: x.get('totalTokens', 0), default={})
            min_day = min(daily_data, key=lambda x: x.get('totalTokens', 0), default={})
            
            # 计算趋势（最近7天 vs 前面7天的平均值）
            recent_7_days = daily_data[-7:] if len(daily_data) >= 7 else daily_data
            previous_7_days = daily_data[-14:-7] if len(daily_data) >= 14 else []
            
            recent_avg = sum(day.get('totalTokens', 0) for day in recent_7_days) / len(recent_7_days) if recent_7_days else 0
            previous_avg = sum(day.get('totalTokens', 0) for day in previous_7_days) / len(previous_7_days) if previous_7_days else recent_avg
            
            trend = 'increasing' if recent_avg > previous_avg * 1.1 else ('decreasing' if recent_avg < previous_avg * 0.9 else 'stable')
            
            result['summary'] = {
                'totalDays': total_days,
                'averageTokensPerDay': round(avg_tokens),
                'averageCostPerDay': round(avg_cost, 2),
                'maxUsageDay': {
                    'date': max_day.get('date', ''),
                    'tokens': max_day.get('totalTokens', 0),
                    'cost': max_day.get('totalCost', 0)
                },
                'minUsageDay': {
                    'date': min_day.get('date', ''),
                    'tokens': min_day.get('totalTokens', 0),
                    'cost': min_day.get('totalCost', 0)
                },
                'recentTrend': trend,
                'recentAverage': round(recent_avg),
                'previousAverage': round(previous_avg)
            }
        
        return result


class TaskManager:
    """任务管理器"""
    
    def __init__(self, db_path='tasks.db'):
        self.db_path = db_path
        self.claude_executor = ClaudeExecutor()
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                type TEXT DEFAULT 'immediate',
                status TEXT DEFAULT 'pending',
                scheduled_time TEXT,
                created_at TEXT,
                updated_at TEXT,
                estimated_tokens INTEGER,
                actual_tokens INTEGER,
                result TEXT,
                task_directory TEXT,
                files_created TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_task(self, description, task_type='immediate', scheduled_time=None):
        """添加任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        estimated_tokens = len(description) * 4  # 简单估算
        
        cursor.execute('''
            INSERT INTO tasks (description, type, status, scheduled_time, created_at, updated_at, estimated_tokens)
            VALUES (?, ?, 'pending', ?, ?, ?, ?)
        ''', (description, task_type, scheduled_time, now, now, estimated_tokens))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"[TaskManager] 任务已添加 ID:{task_id} - {description[:50]}...")
        return task_id
    
    def get_all_tasks(self):
        """获取所有任务"""
        conn = sqlite3.connect(self.db_path)
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
                'status': row[3],
                'scheduledTime': row[4],
                'createdAt': row[5],
                'updatedAt': row[6],
                'estimatedTokens': row[7],
                'actualTokens': row[8],
                'result': row[9],
                'taskDirectory': row[10] if len(row) > 10 else None,
                'filesCreated': json.loads(row[11]) if len(row) > 11 and row[11] else []
            })
        
        return tasks
    
    def update_task_status(self, task_id, status, result=None, task_directory=None, files_created=None):
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        files_json = json.dumps(files_created) if files_created else None
        
        cursor.execute('''
            UPDATE tasks SET status = ?, result = ?, task_directory = ?, files_created = ?, updated_at = ?
            WHERE id = ?
        ''', (status, result, task_directory, files_json, now, task_id))
        
        conn.commit()
        conn.close()
        
        print(f"[TaskManager] 任务状态更新 ID:{task_id} -> {status}")
        append_log(f"Task {task_id} status -> {status}")
        if task_directory:
            print(f"[TaskManager] 文件生成目录: {task_directory}")
            append_log(f"Task {task_id} dir: {task_directory}")

    def recover_stuck_tasks(self, max_minutes: int = 10):
        """将长时间处于running状态的任务自动标记为failed"""
        try:
            threshold = (datetime.now() - timedelta(minutes=max_minutes)).isoformat()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tasks
                SET status = 'failed', result = COALESCE(result, '') || '[自动恢复] 运行超时，已标记失败', updated_at = ?
                WHERE status = 'running' AND updated_at < ?
            ''', (datetime.now().isoformat(), threshold))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            if affected:
                msg = f"[TaskManager] 自动恢复：标记 {affected} 个卡住的running任务为failed"
                print(msg)
                append_log(msg)
        except Exception as e:
            msg = f"[TaskManager] 自动恢复失败: {e}"
            print(msg)
            append_log(msg)
    
    def delete_task(self, task_id):
        """删除任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        print(f"[TaskManager] 任务已删除 ID:{task_id}")
    
    def execute_task_with_claude(self, task_id):
        """使用Claude Code执行任务"""
        # 获取任务信息
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT description FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'success': False, 'error': '任务不存在'}
        
        description = result[0]
        
        # 更新状态为执行中
        self.update_task_status(task_id, 'running')
        
        try:
            print(f"[TaskManager] 开始执行任务 {task_id}: {description[:50]}...")
            append_log(f"Task {task_id} start: {description[:50]}...")

            # 在后台线程中执行以实现整体超时控制
            import threading
            result_holder = {'value': None}

            def run_exec():
                try:
                    result_holder['value'] = self.claude_executor.execute_task(task_id, description)
                except Exception as e:
                    result_holder['value'] = {'success': False, 'error': f'执行异常: {e}'}

            t = threading.Thread(target=run_exec)
            t.daemon = True
            t.start()
            t.join(timeout=120)  # 总体超时120秒

            if t.is_alive():
                # 超时处理
                timeout_msg = '执行超时（超过120秒）'
                self.update_task_status(task_id, 'failed', timeout_msg)
                append_log(f"Task {task_id} timeout")
                print(f"[TaskManager] 任务 {task_id} 超时: {timeout_msg}")
                return {'success': False, 'error': timeout_msg}

            execution_result = result_holder['value'] or {'success': False, 'error': '未知错误'}

            if execution_result.get('success'):
                self.update_task_status(
                    task_id,
                    'completed',
                    execution_result.get('report'),
                    execution_result.get('task_dir'),
                    execution_result.get('files_created')
                )
                print(f"[TaskManager] 任务 {task_id} 执行成功")
                append_log(f"Task {task_id} completed")
                return execution_result
            else:
                self.update_task_status(
                    task_id,
                    'failed',
                    execution_result.get('error', '未知错误')
                )
                print(f"[TaskManager] 任务 {task_id} 执行失败: {execution_result.get('error')}")
                append_log(f"Task {task_id} failed: {execution_result.get('error')}")
                return execution_result

        except Exception as e:
            error_msg = f"执行任务时发生异常: {str(e)}"
            self.update_task_status(task_id, 'failed', error_msg)
            print(f"[TaskManager] 任务 {task_id} 异常: {error_msg}")
            append_log(f"Task {task_id} exception: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_workspace_info(self):
        """获取工作区信息"""
        return self.claude_executor.get_workspace_info()


class RealtimeHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        path = self.path.split('?')[0]
        
        if path == '/' or path == '/index.html':
            self.serve_html()
        elif path == '/api/token-status':
            self.get_token_status()
        elif path == '/api/tasks':
            self.get_tasks()
        elif path == '/api/workspace':
            self.get_workspace()
        elif path == '/api/live':
            self.serve_live_updates()
        elif path == '/api/history':
            self.get_history()
        elif path.startswith('/api/history/'):
            # 支持 /api/history/30 这样的路径指定天数
            try:
                days = int(path.split('/')[-1])
                self.get_history(days)
            except ValueError:
                self.send_error(400, "Invalid days parameter")
        else:
            self.send_error(404)
    
    def do_POST(self):
        """处理POST请求"""
        path = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data) if post_data else {}
        except:
            data = {}
        
        if path == '/api/add-task':
            self.add_task(data)
        elif path == '/api/update-task':
            self.update_task(data)
        elif path == '/api/delete-task':
            self.delete_task(data)
        elif path == '/api/execute-task':
            self.execute_task(data)
        else:
            self.send_error(404)
    
    def serve_html(self):
        """提供HTML界面"""
        html_path = os.path.join(os.path.dirname(__file__), 'realtime_interface.html')
        
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换API调用为真实端点
            content = content.replace(
                'async function refreshTokenStatus() {',
                '''async function refreshTokenStatus() {
            try {
                const response = await fetch('/api/token-status');
                const data = await response.json();
                updateTokenDisplay(data);
            } catch (error) {
                console.error('获取Token状态失败:', error);
            }
        }
        
        async function refreshTokenStatus_old() {'''
            )
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            self.send_error(404, "HTML文件未找到")
    
    def get_token_status(self):
        """获取Token状态"""
        token_data = token_monitor.get_real_time_data()
        self.send_json_response(token_data)
    
    def get_tasks(self):
        """获取任务列表"""
        tasks = task_manager.get_all_tasks()
        self.send_json_response({'tasks': tasks})
    
    def get_workspace(self):
        """获取工作区信息"""
        workspace_info = task_manager.get_workspace_info()
        self.send_json_response(workspace_info)
    
    def get_history(self, days=30):
        """获取历史使用数据"""
        try:
            history_data = token_monitor.get_historical_data(days)
            self.send_json_response(history_data)
        except Exception as e:
            print(f"[RealtimeHandler] 获取历史数据失败: {e}")
            self.send_json_response({
                'error': f'获取历史数据失败: {str(e)}',
                'daily': [],
                'totals': {}
            }, 500)
    
    def add_task(self, data):
        """添加任务"""
        description = data.get('description', '')
        task_type = data.get('type', 'immediate')
        scheduled_time = data.get('scheduledTime')
        
        if not description:
            self.send_json_response({'error': '任务描述不能为空'}, 400)
            return
        
        task_id = task_manager.add_task(description, task_type, scheduled_time)
        self.send_json_response({'success': True, 'taskId': task_id})
    
    def update_task(self, data):
        """更新任务"""
        task_id = data.get('taskId')
        status = data.get('status')
        result = data.get('result')
        
        if not task_id:
            self.send_json_response({'error': '任务ID不能为空'}, 400)
            return
        
        task_manager.update_task_status(task_id, status, result)
        self.send_json_response({'success': True})
    
    def delete_task(self, data):
        """删除任务"""
        task_id = data.get('taskId')
        
        if not task_id:
            self.send_json_response({'error': '任务ID不能为空'}, 400)
            return
        
        task_manager.delete_task(task_id)
        self.send_json_response({'success': True})
    
    def execute_task(self, data):
        """执行任务"""
        task_id = data.get('taskId')
        
        if not task_id:
            self.send_json_response({'error': '任务ID不能为空'}, 400)
            return
        
        # 在后台线程中执行任务，避免阻塞HTTP响应
        def execute_in_background():
            try:
                result = task_manager.execute_task_with_claude(task_id)
                print(f"[RealtimeHandler] 任务 {task_id} 执行完成: {result.get('success', False)}")
            except Exception as e:
                print(f"[RealtimeHandler] 任务 {task_id} 执行异常: {e}")
        
        execution_thread = threading.Thread(target=execute_in_background)
        execution_thread.daemon = True
        execution_thread.start()
        
        self.send_json_response({
            'success': True, 
            'message': f'任务 {task_id} 已开始执行，请刷新查看进度'
        })
    
    def serve_live_updates(self):
        """提供实时更新流"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 发送初始数据
        token_data = token_monitor.get_real_time_data()
        self.wfile.write(f"data: {json.dumps(token_data)}\n\n".encode('utf-8'))
        self.wfile.flush()
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")


class TaskScheduler:
    """任务调度器 - 自动检查和执行定时任务"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.running = False
        self.check_interval = 30  # 30秒检查一次
    
    def start(self):
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        
        def scheduler_loop():
            print("⏰ 任务调度器启动，每30秒检查一次待执行任务")
            
            while self.running:
                try:
                    self.check_and_execute_tasks()
                    time.sleep(self.check_interval)
                except Exception as e:
                    print(f"[TaskScheduler] 调度器错误: {e}")
                    time.sleep(self.check_interval)
        
        scheduler_thread = threading.Thread(target=scheduler_loop)
        scheduler_thread.daemon = True
        scheduler_thread.start()
    
    def stop(self):
        """停止调度器"""
        self.running = False
        print("🛑 任务调度器已停止")
    
    def check_and_execute_tasks(self):
        """检查并执行到期的任务"""
        now = datetime.now()
        
        # 获取所有待执行的定时任务
        conn = sqlite3.connect(self.task_manager.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, description, scheduled_time 
            FROM tasks 
            WHERE status = 'pending' AND type = 'scheduled' AND scheduled_time IS NOT NULL
        ''')
        pending_tasks = cursor.fetchall()
        conn.close()
        
        executed_count = 0
        
        for task_id, description, scheduled_time_str in pending_tasks:
            try:
                # 解析预定时间
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                scheduled_time = scheduled_time.replace(tzinfo=None)  # 移除时区信息，使用本地时间
                
                # 检查是否到期（允许30秒的误差）
                if now >= scheduled_time:
                    print(f"⏰ 执行定时任务 {task_id}: {description[:50]}...")
                    
                    # 在后台线程执行任务
                    def execute_scheduled_task():
                        try:
                            result = self.task_manager.execute_task_with_claude(task_id)
                            status = "✅ 成功" if result.get('success') else "❌ 失败"
                            print(f"[TaskScheduler] 任务 {task_id} 执行完成: {status}")
                        except Exception as e:
                            print(f"[TaskScheduler] 任务 {task_id} 执行异常: {e}")
                    
                    execution_thread = threading.Thread(target=execute_scheduled_task)
                    execution_thread.daemon = True
                    execution_thread.start()
                    
                    executed_count += 1
                    
            except Exception as e:
                print(f"[TaskScheduler] 解析任务 {task_id} 时间失败: {e}")
        
        if executed_count > 0:
            print(f"[TaskScheduler] 本次检查执行了 {executed_count} 个定时任务")


def main():
    """主函数"""
    global token_monitor, task_manager, task_scheduler
    
    print("🚀 启动 VibeCodeTask 实时监控服务器...")
    
    # 初始化组件
    token_monitor = TokenMonitor()
    task_manager = TaskManager()
    # 服务启动时自动恢复卡住的任务
    try:
        from datetime import timedelta
        task_manager.recover_stuck_tasks(max_minutes=10)
    except Exception as e:
        print(f"[Main] 恢复卡住任务失败: {e}")
        append_log(f"Recover stuck tasks failed: {e}")
    task_scheduler = TaskScheduler(task_manager)
    
    PORT = 8080
    server = HTTPServer(('localhost', PORT), RealtimeHandler)
    
    print(f"📱 服务器运行在: http://localhost:{PORT}")
    print(f"💾 任务数据库: {task_manager.db_path}")
    print("🔍 开始实时监控Token使用情况...")
    
    # 启动任务调度器
    task_scheduler.start()
    
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
        task_scheduler.stop()


if __name__ == "__main__":
    main()
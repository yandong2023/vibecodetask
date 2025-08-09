#!/usr/bin/env python3
"""
真实Token管理器 - 集成ccusage命令
"""

import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class RealTokenManager:
    """真实Token管理器 - 使用ccusage获取实时数据"""
    
    def __init__(self):
        self.cache_expire_time = 60  # 缓存60秒
        self.last_update = 0
        self.cached_data = None
    
    def get_current_usage(self) -> Dict:
        """获取当前使用情况"""
        now = time.time()
        
        # 如果缓存未过期，返回缓存数据
        if self.cached_data and (now - self.last_update) < self.cache_expire_time:
            return self.cached_data
        
        try:
            # 获取今天的使用数据
            today = datetime.now().strftime('%Y%m%d')
            result = subprocess.run(
                ['ccusage', 'daily', '--json', '-s', today],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # 解析数据
                usage_info = self._parse_usage_data(data)
                
                # 更新缓存
                self.cached_data = usage_info
                self.last_update = now
                
                return usage_info
            else:
                print(f"[TokenManager] ccusage命令失败: {result.stderr}")
                return self._get_fallback_data()
                
        except subprocess.TimeoutExpired:
            print("[TokenManager] ccusage命令超时")
            return self._get_fallback_data()
        except Exception as e:
            print(f"[TokenManager] 获取使用数据失败: {e}")
            return self._get_fallback_data()
    
    def get_active_block_info(self) -> Dict:
        """获取当前活动block信息"""
        try:
            result = subprocess.run(
                ['ccusage', 'blocks', '--json', '--active'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return self._parse_block_data(data)
            else:
                return {}
                
        except Exception as e:
            print(f"[TokenManager] 获取block信息失败: {e}")
            return {}
    
    def _parse_usage_data(self, data: Dict) -> Dict:
        """解析使用数据"""
        if not data.get('daily'):
            return self._get_fallback_data()
        
        today_data = data['daily'][0] if data['daily'] else {}
        totals = data.get('totals', {})
        
        # 计算总使用token (包括缓存)
        total_tokens = totals.get('totalTokens', 0)
        total_cost = totals.get('totalCost', 0.0)
        
        # 分别统计输入和输出token
        input_tokens = totals.get('inputTokens', 0)
        output_tokens = totals.get('outputTokens', 0)
        cache_creation = totals.get('cacheCreationTokens', 0)
        cache_read = totals.get('cacheReadTokens', 0)
        
        # 估算剩余可用token（基于成本）
        # Claude Code通常有每日成本限制，我们可以根据使用模式估算
        estimated_daily_limit = self._estimate_daily_limit(today_data)
        remaining_tokens = max(0, estimated_daily_limit - total_tokens)
        
        return {
            'totalTokens': total_tokens,
            'totalCost': total_cost,
            'inputTokens': input_tokens,
            'outputTokens': output_tokens,
            'cacheCreationTokens': cache_creation,
            'cacheReadTokens': cache_read,
            'estimatedDailyLimit': estimated_daily_limit,
            'remainingTokens': remaining_tokens,
            'usagePercentage': (total_tokens / estimated_daily_limit * 100) if estimated_daily_limit > 0 else 0,
            'modelsUsed': today_data.get('modelsUsed', []),
            'lastUpdated': datetime.now().isoformat()
        }
    
    def _parse_block_data(self, data: Dict) -> Dict:
        """解析block数据"""
        blocks = data.get('blocks', [])
        if not blocks:
            return {}
        
        active_block = blocks[0]  # 活动block
        
        return {
            'blockId': active_block.get('id', ''),
            'startTime': active_block.get('startTime', ''),
            'isActive': active_block.get('isActive', False),
            'entries': active_block.get('entries', 0),
            'totalTokens': active_block.get('totalTokens', 0),
            'costUSD': active_block.get('costUSD', 0.0),
            'burnRate': active_block.get('burnRate', {}),
            'projection': active_block.get('projection', {}),
            'models': active_block.get('models', [])
        }
    
    def _estimate_daily_limit(self, today_data: Dict) -> int:
        """估算每日token限制"""
        # 这里可以根据用户的订阅计划来估算
        # 默认估算值，实际需要根据Claude Code的具体限制调整
        
        models_used = today_data.get('modelsUsed', [])
        
        # 如果使用Opus模型，限制通常较低
        if any('opus' in model.lower() for model in models_used):
            return 1000000  # 1M tokens for Opus users
        else:
            return 5000000  # 5M tokens for Sonnet users
    
    def _get_fallback_data(self) -> Dict:
        """获取备用数据"""
        return {
            'totalTokens': 0,
            'totalCost': 0.0,
            'inputTokens': 0,
            'outputTokens': 0,
            'cacheCreationTokens': 0,
            'cacheReadTokens': 0,
            'estimatedDailyLimit': 1000000,
            'remainingTokens': 1000000,
            'usagePercentage': 0,
            'modelsUsed': [],
            'lastUpdated': datetime.now().isoformat(),
            'error': 'Unable to fetch real usage data'
        }
    
    def can_execute_task(self, estimated_tokens: int) -> bool:
        """检查是否有足够token执行任务"""
        usage = self.get_current_usage()
        remaining = usage.get('remainingTokens', 0)
        
        # 保留5%的安全边距
        safe_remaining = remaining * 0.95
        
        return estimated_tokens <= safe_remaining
    
    def get_token_status(self) -> Dict:
        """获取token状态信息"""
        usage = self.get_current_usage()
        block_info = self.get_active_block_info()
        
        # 计算状态
        percentage = usage.get('usagePercentage', 0)
        if percentage < 50:
            status = 'good'
        elif percentage < 80:
            status = 'warning'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'percentage': percentage,
            'totalTokens': usage.get('totalTokens', 0),
            'remainingTokens': usage.get('remainingTokens', 0),
            'totalCost': usage.get('totalCost', 0),
            'estimatedDailyLimit': usage.get('estimatedDailyLimit', 0),
            'modelsUsed': usage.get('modelsUsed', []),
            'blockInfo': block_info,
            'lastUpdated': usage.get('lastUpdated'),
            'hasError': 'error' in usage
        }
    
    def wait_for_recovery(self) -> None:
        """等待token恢复"""
        print("[TokenManager] Token不足，等待恢复...")
        
        # 检查当前block的投影信息
        block_info = self.get_active_block_info()
        projection = block_info.get('projection', {})
        
        if projection:
            remaining_minutes = projection.get('remainingMinutes', 60)
            print(f"[TokenManager] 预计 {remaining_minutes} 分钟后当前block结束")
            
            # 等待到block结束
            wait_time = min(remaining_minutes * 60, 3600)  # 最多等待1小时
            time.sleep(wait_time)
        else:
            # 默认等待1小时
            print("[TokenManager] 等待1小时后重试")
            time.sleep(3600)
    
    def get_live_monitoring_command(self) -> str:
        """获取实时监控命令"""
        return "ccusage blocks --live --refresh-interval 5"

# 使用示例
if __name__ == "__main__":
    token_manager = RealTokenManager()
    
    print("🔍 获取当前Token使用情况...")
    usage = token_manager.get_current_usage()
    print(json.dumps(usage, indent=2, ensure_ascii=False))
    
    print("\n📊 获取Token状态...")
    status = token_manager.get_token_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    print("\n🔄 获取活动Block信息...")
    block_info = token_manager.get_active_block_info()
    print(json.dumps(block_info, indent=2, ensure_ascii=False))
    
    print(f"\n📺 实时监控命令: {token_manager.get_live_monitoring_command()}")
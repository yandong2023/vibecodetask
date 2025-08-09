#!/usr/bin/env node

// 模拟API返回的实际数据
const apiResponse = {
  "tasks": [
    {
      "id": 6,
      "scheduledTime": "2025-08-09T14:22:00",
      "createdAt": "2025-08-09T22:21:51.324625"
    },
    {
      "id": 5,
      "scheduledTime": "2025-08-09T14:15:00",
      "createdAt": "2025-08-09T22:14:19.534048"
    },
    {
      "id": 4,
      "scheduledTime": "2025-08-09T15:17:28",
      "createdAt": "2025-08-09T15:16:28.213443"
    },
    {
      "id": 3,
      "scheduledTime": null,
      "createdAt": "2025-08-09T14:49:04.408948"
    },
    {
      "id": 2,
      "scheduledTime": "13:13",  // 问题在这里！
      "createdAt": "2025-08-09T13:12:06.236006"
    }
  ]
};

// 复制修复后的函数
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '--';
    try {
        const date = new Date(dateTimeStr);
        if (isNaN(date.getTime())) {
            return dateTimeStr;
        }
        return date.toLocaleString();
    } catch (e) {
        console.warn('Date parsing error:', e, dateTimeStr);
        return dateTimeStr;
    }
}

function getTaskTypeText(task) {
    switch (task.type) {
        case 'immediate': return '⚡ 立即执行';
        case 'scheduled': {
            if (task.scheduledTime) {
                try {
                    const scheduledDate = new Date(task.scheduledTime);
                    if (isNaN(scheduledDate.getTime())) {
                        return `⏰ ${task.scheduledTime}`;
                    }
                    return `⏰ ${scheduledDate.toLocaleString()}`;
                } catch (e) {
                    return `⏰ ${task.scheduledTime}`;
                }
            }
            return '⏰ 定时执行';
        }
        case 'smart': return '🤖 智能调度';
        default: return '❓ 未知';
    }
}

console.log('🔍 分析API数据中的问题时间格式');
console.log('=' * 50);
console.log();

apiResponse.tasks.forEach(task => {
    console.log(`📋 任务 ${task.id}:`);
    console.log(`   scheduledTime: "${task.scheduledTime}"`);
    console.log(`   createdAt: "${task.createdAt}"`);
    
    // 测试scheduledTime解析
    try {
        if (task.scheduledTime) {
            const date = new Date(task.scheduledTime);
            if (isNaN(date.getTime())) {
                console.log(`   ❌ scheduledTime 解析失败: "${task.scheduledTime}"`);
            } else {
                console.log(`   ✅ scheduledTime 解析成功: ${date.toLocaleString()}`);
            }
        } else {
            console.log(`   ✅ scheduledTime 为空，正常`);
        }
    } catch (e) {
        console.log(`   ❌ scheduledTime 异常: ${e.message}`);
    }
    
    // 测试createdAt解析
    try {
        const date = new Date(task.createdAt);
        if (isNaN(date.getTime())) {
            console.log(`   ❌ createdAt 解析失败`);
        } else {
            console.log(`   ✅ createdAt 解析成功: ${date.toLocaleString()}`);
        }
    } catch (e) {
        console.log(`   ❌ createdAt 异常: ${e.message}`);
    }
    
    console.log();
});

console.log('🎯 发现的问题:');
console.log('   任务ID 2 的 scheduledTime 格式异常: "13:13"');
console.log('   这种格式无法被 new Date() 正确解析');
console.log('   需要在后端数据库层面修复这个问题');
console.log();

console.log('💡 建议的解决方案:');
console.log('   1. 修复数据库中异常的时间格式');
console.log('   2. 加强前端的时间格式兼容性');
console.log('   3. 后端在返回数据前进行格式验证');
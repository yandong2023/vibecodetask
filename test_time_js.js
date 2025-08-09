#!/usr/bin/env node

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

// 用户提供的实际任务数据
const testTask = {
    "id": 5,
    "description": "用html+js 生成fly bird游戏",
    "type": "scheduled",
    "status": "completed",
    "scheduledTime": "2025-08-09T14:15:00",
    "createdAt": "2025-08-09T22:14:19.534048",
    "updatedAt": "2025-08-09T22:15:33.784604",
    "estimatedTokens": 84
};

console.log('🕐 时间格式处理测试结果');
console.log('=' * 50);
console.log('');

console.log('📋 用户实际任务数据测试:');
console.log('');

console.log('⏰ scheduledTime:');
console.log(`   输入: "${testTask.scheduledTime}"`);
console.log(`   输出: "${formatDateTime(testTask.scheduledTime)}"`);
console.log('');

console.log('📅 createdAt:');
console.log(`   输入: "${testTask.createdAt}"`);
console.log(`   输出: "${formatDateTime(testTask.createdAt)}"`);
console.log('');

console.log('🔄 updatedAt:');
console.log(`   输入: "${testTask.updatedAt}"`);
console.log(`   输出: "${formatDateTime(testTask.updatedAt)}"`);
console.log('');

console.log('📝 任务类型显示:');
console.log(`   输入: ${JSON.stringify({ type: testTask.type, scheduledTime: testTask.scheduledTime })}`);
console.log(`   输出: "${getTaskTypeText(testTask)}"`);
console.log('');

console.log('🧪 额外测试案例:');
console.log('');

const extraTests = [
    "2025-08-10T14:30:00",
    "2025-08-10T14:30:00.123456", 
    "2025-08-10T14:30:00Z",
    null,
    undefined,
    "invalid-date",
    ""
];

extraTests.forEach((testInput, index) => {
    console.log(`   测试 ${index + 1}:`);
    console.log(`     输入: ${JSON.stringify(testInput)}`);
    console.log(`     输出: "${formatDateTime(testInput)}"`);
});

console.log('');
console.log('✅ 测试完成！如果所有输出都正常显示，说明时间格式修复成功。');

// 模拟任务列表渲染测试
console.log('');
console.log('📋 模拟任务列表渲染:');
console.log('');

const taskListItem = `
任务: ${testTask.description}
类型: ${getTaskTypeText(testTask)}
创建时间: ${formatDateTime(testTask.createdAt)}
预计Token: ${testTask.estimatedTokens}
状态: ${testTask.status}
`;

console.log(taskListItem);
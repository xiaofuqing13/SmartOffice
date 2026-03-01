/**
 * 日期格式化工具函数
 */

/**
 * 格式化日期
 * @param {Date|String|Number} date - 日期对象或可转为日期的字符串/时间戳
 * @param {String} format - 格式化模板，如 'YYYY-MM-DD HH:mm:ss'
 * @returns {String} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return '';
  
  // 确保date是Date对象
  if (!(date instanceof Date)) {
    date = new Date(date);
    if (isNaN(date.getTime())) return '无效日期';
  }
  
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hour = date.getHours();
  const minute = date.getMinutes();
  const second = date.getSeconds();
  
  // 填充函数，确保数字为两位
  const pad = num => (num < 10 ? '0' + num : num);
  
  return format
    .replace(/YYYY/g, year)
    .replace(/YY/g, String(year).slice(2))
    .replace(/MM/g, pad(month))
    .replace(/M/g, month)
    .replace(/DD/g, pad(day))
    .replace(/D/g, day)
    .replace(/HH/g, pad(hour))
    .replace(/H/g, hour)
    .replace(/hh/g, pad(hour % 12 || 12))
    .replace(/h/g, hour % 12 || 12)
    .replace(/mm/g, pad(minute))
    .replace(/m/g, minute)
    .replace(/ss/g, pad(second))
    .replace(/s/g, second);
}

/**
 * 格式化相对时间，如"几分钟前"、"几小时前"等
 * @param {Date|String|Number} date - 日期对象或可转为日期的字符串/时间戳
 * @returns {String} 相对时间字符串
 */
export function formatRelativeTime(date) {
  if (!date) return '';
  
  // 确保date是Date对象
  if (!(date instanceof Date)) {
    date = new Date(date);
    if (isNaN(date.getTime())) return '无效日期';
  }
  
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const months = Math.floor(days / 30);
  const years = Math.floor(months / 12);
  
  if (seconds < 60) {
    return '刚刚';
  } else if (minutes < 60) {
    return `${minutes}分钟前`;
  } else if (hours < 24) {
    return `${hours}小时前`;
  } else if (days < 30) {
    return `${days}天前`;
  } else if (months < 12) {
    return `${months}个月前`;
  } else {
    return `${years}年前`;
  }
}

/**
 * 格式化时间范围
 * @param {Date|String|Number} startDate - 开始日期
 * @param {Date|String|Number} endDate - 结束日期
 * @param {String} format - 日期格式
 * @returns {String} 格式化后的时间范围
 */
export function formatDateRange(startDate, endDate, format = 'YYYY-MM-DD') {
  if (!startDate) return '';
  
  // 格式化开始日期
  const start = formatDate(startDate, format);
  
  // 如果没有结束日期，只返回开始日期
  if (!endDate) return start;
  
  // 格式化结束日期
  const end = formatDate(endDate, format);
  
  // 返回日期范围
  return `${start} 至 ${end}`;
} 
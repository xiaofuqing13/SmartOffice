import request from '@/utils/request'

/**
 * 获取月度日历事件
 * @param {Number} year - 年份
 * @param {Number} month - 月份(1-12)
 * @returns {Promise} - 返回月度事件列表
 */
export function getMonthlyEvents(year, month) {
  return request({
    url: '/api/calendar/events/monthly/',
    method: 'get',
    params: { year, month }
  })
}

/**
 * 获取周视图日历事件
 * @param {String} date - 日期字符串，格式为YYYY-MM-DD
 * @returns {Promise} - 返回周视图事件列表
 */
export function getWeeklyEvents(date) {
  return request({
    url: '/api/calendar/events/weekly/',
    method: 'get',
    params: { date }
  })
}

/**
 * 获取日视图日历事件
 * @param {String} date - 日期字符串，格式为YYYY-MM-DD
 * @returns {Promise} - 返回日视图事件列表
 */
export function getDailyEvents(date) {
  return request({
    url: '/api/calendar/events/daily/',
    method: 'get',
    params: { date }
  })
}

/**
 * 创建日历事件
 * @param {Object} data - 事件数据
 * @returns {Promise} - 返回创建的事件
 */
export function createEvent(data) {
  const { title, start, end, location, description, type, reminder, participants } = data
  
  return request({
    url: '/api/calendar/events/',
    method: 'post',
    data: { title, start, end, location, description, type, reminder, participants }
  })
}

/**
 * 更新日历事件
 * @param {Number} id - 事件ID
 * @param {Object} data - 事件数据
 * @returns {Promise} - 返回更新后的事件
 */
export function updateEvent(id, data) {
  const { title, start, end, location, description, type, reminder, participants } = data
  
  return request({
    url: `/api/calendar/events/${id}/`,
    method: 'put',
    data: { title, start, end, location, description, type, reminder, participants }
  })
}

/**
 * 删除日历事件
 * @param {number} id - 事件ID
 * @returns {Promise}
 */
export function deleteCalendarEvent(id) {
  return request({
    url: `/api/calendar/events/${id}/`,
    method: 'delete'
  })
}

/**
 * 获取日历事件详情
 * @param {number} id - 事件ID
 * @returns {Promise}
 */
export function getCalendarEvent(id) {
    return request({
        url: `/api/calendar/events/${id}/`,
        method: 'get'
    })
} 
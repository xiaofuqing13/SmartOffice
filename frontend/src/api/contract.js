import request from '@/utils/request'
import userApi from './user'

/**
 * 合同管理API
 */

/**
 * 获取合同列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getContractList(params) {
  return request({
    url: '/api/contract/contracts/',
    method: 'get',
    params
  })
}

/**
 * 获取合同详情
 * @param {string|number} id - 合同ID或编号
 * @returns {Promise}
 */
export function getContractDetail(id) {
  return request({
    url: `/api/contract/contracts/${id}/`,
    method: 'get'
  })
}

/**
 * 创建新合同
 * @param {Object} data - 合同数据
 * @returns {Promise}
 */
export function createContract(data) {
  return request({
    url: '/api/contract/contracts/',
    method: 'post',
    data
  })
}

/**
 * 更新合同
 * @param {string|number} id - 合同ID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export function updateContract(id, data) {
  return request({
    url: `/api/contract/contracts/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除合同
 * @param {string|number} id - 合同ID
 * @returns {Promise}
 */
export function deleteContract(id) {
  return request({
    url: `/api/contract/contracts/${id}/`,
    method: 'delete'
  })
}

/**
 * 获取合同模板列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getContractTemplates(params) {
  return request({
    url: '/api/contract/templates/',
    method: 'get',
    params
  })
}

/**
 * 获取推荐的合同模板列表
 * @param {Object} params - 筛选参数
 * @returns {Promise}
 */
export function getRecommendedTemplates(params) {
  return request({
    url: '/api/contract/contracts/template_suggestions/',
    method: 'get',
    params
  })
}

/**
 * 获取合同模板详情
 * @param {string|number} id - 模板ID
 * @returns {Promise}
 */
export function getContractTemplateDetail(id) {
  return request({
    url: `/api/contract/templates/${id}/`,
    method: 'get'
  })
}

/**
 * 使用模板创建合同
 * @param {string|number} templateId - 模板ID
 * @param {Object} data - 合同数据（标题、公司等）
 * @returns {Promise}
 */
export function createContractFromTemplate(templateId, data) {
  return request({
    url: `/api/contract/templates/${templateId}/use_template/`,
    method: 'post',
    data
  })
}

/**
 * 添加合同附件
 * @param {string|number} id - 合同ID
 * @param {Object} data - 附件数据
 * @returns {Promise}
 */
export function addContractAttachment(id, data) {
  return request({
    url: `/api/contract/contracts/${id}/add_attachment/`,
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 检查合同(AI分析)
 * @param {string|number} id - 合同ID
 * @param {Object} data - 合同文本数据，包含content属性
 * @returns {Promise}
 */
export function checkContract(id, data) {
  // 确保ID有效
  if (!id || isNaN(Number(id))) {
    console.error('无效的合同ID:', id);
    return Promise.reject(new Error('无效的合同ID'));
  }
  
  // 确保数据包含content
  if (!data || !data.content) {
    console.error('无效的合同内容:', data);
    return Promise.reject(new Error('合同内容不能为空'));
  }
  
  // 记录调用信息
  const contentLength = data && data.content ? data.content.length : 0;
  console.log(`调用checkContract API - ID: ${id}, 内容长度: ${contentLength}`);
  
  return request({
    url: `/api/contract/contracts/${id}/check_contract/`,
    method: 'post',
    data,
    timeout: 180000 // 3分钟超时，检查可能需要更长时间
  }).catch(error => {
    console.error('合同检查API错误:', error);
    throw error;
  });
}

/**
 * 合同AI润色
 * @param {string|number} id - 合同ID
 * @param {Object} data - 合同文本数据，包含content属性
 * @param {AbortSignal} [signal] - 用于取消请求的AbortSignal对象
 * @returns {Promise}
 */
export function aiPolishContract(id, data, signal) {
  // 确保数据包含content
  if (!data || !data.content) {
    console.error('无效的合同内容:', data);
    return Promise.reject(new Error('合同内容不能为空'));
  }
  
  const contentLength = data && data.content ? data.content.length : 0;
  console.log(`调用aiPolishContract API - ID: ${id}, 内容长度: ${contentLength}`);
  
  return request({
    url: `/api/contract/contracts/${id}/ai_polish/`,
    method: 'post',
    data,
    signal
  }).then(response => {
    console.log('AI润色返回数据:', response);
    return response;
  }).catch(error => {
    console.error('AI润色API错误:', error);
    throw error;
  });
}

/**
 * 创建日历事件
 * @param {Object} data - 事件数据
 * @returns {Promise}
 */
export function createCalendarEvent(data) {
  return request({
    url: '/api/contract/events/',
    method: 'post',
    data
  })
}

/**
 * 更新日历事件
 * @param {Number} id - 事件ID
 * @param {Object} data - 事件数据
 * @returns {Promise}
 */
export function updateCalendarEvent(id, data) {
  return request({
    url: `/api/contract/events/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除日历事件
 * @param {Number} id - 事件ID
 * @returns {Promise}
 */
export function deleteCalendarEvent(id) {
  return request({
    url: `/api/contract/events/${id}/`,
    method: 'delete'
  })
}

export const { getCompanyUsers } = userApi; 
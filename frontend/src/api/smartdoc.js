import request from '@/utils/request'

/**
 * 获取所有文档列表
 * @param {Object} params - 查询参数
 * @returns {Promise} Promise对象
 */
export function getDocuments(params) {
  console.log('调用getDocuments API, 参数:', params);
  // 确保参数中包含分页信息，使用与Django REST Framework兼容的参数名
  const queryParams = {
    ...params,
    page: params.page || 1,
    page_size: params.limit || params.page_size || 10, // 默认使用后端配置的PAGE_SIZE=10
  };
  
  // 如果同时存在limit和page_size，移除limit避免冲突
  if (queryParams.limit && queryParams.page_size) {
    delete queryParams.limit;
  }
  
  console.log('处理后的参数:', queryParams);
  
  return request({
    url: '/api/smartdoc/documents/',
    method: 'get',
    params: queryParams,
    timeout: 60000 // 增加超时时间到60秒
  }).then(response => {
    console.log('getDocuments API响应:', response);
    
    // 检查是否有警告信息
    if (response && response.warning) {
      console.warn('API响应包含警告:', response.warning);
    }
    
    // 标准化响应格式，确保总是返回一致的结构
    if (response.results && Array.isArray(response.results)) {
      // DRF标准分页格式
      console.log(`DRF分页格式: 共${response.count || 0}条记录，当前页${queryParams.page}`);
      return {
        data: response.results,
        count: response.count || 0,
        total: response.count || 0,
        next: response.next,
        previous: response.previous,
        warning: response.warning
      };
    } else if (response.data && Array.isArray(response.data)) {
      // 已经处理过的数组格式
      console.log(`数组格式: 共${response.data.length}条记录`);
      return response;
    } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
      // 嵌套的DRF分页格式
      console.log(`嵌套DRF格式: 共${response.data.count || 0}条记录，当前页${queryParams.page}`);
      return {
        data: response.data.results,
        count: response.data.count || 0,
        total: response.data.count || 0,
        next: response.data.next,
        previous: response.data.previous,
        warning: response.data.warning
      };
    } else {
      // 未知格式，返回原始响应
      console.warn('未知响应格式:', response);
      return response;
    }
  }).catch(error => {
    console.error('getDocuments API错误:', error);
    
    // 检查是否是404分页错误
    if (error.response && error.response.status === 404 && queryParams.page > 1) {
      console.warn(`页码${queryParams.page}不存在，自动尝试获取第1页`);
      
      // 如果是第一次自动重试，防止无限循环
      if (!params._retry) {
        // 修改为第1页重新请求
        const fallbackParams = {
          ...params,
          page: 1,
          _retry: true // 标记为重试请求
        };
        
        return getDocuments(fallbackParams).then(response => {
          // 添加警告信息
          if (response) {
            response.warning = `请求的页码 ${queryParams.page} 不存在，已返回第1页数据`;
          }
          return response;
        });
      } else {
        // 防止多次重试导致循环
        console.error('已经重试过一次，避免多次重试');
        throw error;
      }
    }
    
    // 检查是否是网络错误或服务器错误
    if (error.response && error.response.status >= 500) {
      console.warn('服务器错误，可能需要重试');
    } else if (!error.response) {
      console.warn('网络错误，请检查网络连接');
    }
    
    throw error;
  });
}

/**
 * 获取最近编辑的文档
 * @param {Object} params - 查询参数
 * @returns {Promise} Promise对象
 */
export function getRecentDocuments(params) {
  console.log('调用getRecentDocuments API, 参数:', params);
  return request({
    url: '/api/smartdoc/documents/recent/',
    method: 'get',
    params
  }).then(response => {
    console.log('getRecentDocuments API响应:', response);
    return response;
  }).catch(error => {
    console.error('getRecentDocuments API错误:', error);
    throw error;
  });
}

/**
 * 获取共享文档
 * @param {Object} params - 查询参数
 * @returns {Promise} Promise对象
 */
export function getSharedDocuments(params) {
  return request({
    url: '/api/smartdoc/documents/shared/',
    method: 'get',
    params
  })
}

/**
 * 获取单个文档详情
 * @param {number} id - 文档ID
 * @returns {Promise} Promise对象
 */
export function getDocumentDetail(id) {
  return request({
    url: `/api/smartdoc/documents/${id}/`,
    method: 'get',
    timeout: 60000 // 增加超时时间到60秒，确保大文档可以完整加载
  })
}

/**
 * 创建新文档
 * @param {Object} data - 文档数据
 * @returns {Promise} Promise对象
 */
export function createDocument(data) {
  return request({
    url: '/api/smartdoc/documents/',
    method: 'post',
    data
  })
}

/**
 * 更新文档
 * @param {number} id - 文档ID
 * @param {Object} data - 更新数据
 * @returns {Promise} Promise对象
 */
export function updateDocument(id, data) {
  return request({
    url: `/api/smartdoc/documents/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除文档
 * @param {number} id - 文档ID
 * @returns {Promise} Promise对象
 */
export function deleteDocument(id) {
  return request({
    url: `/api/smartdoc/documents/${id}/`,
    method: 'delete'
  })
}

/**
 * 分享文档
 * @param {number} id - 文档ID
 * @param {Array} sharedUsers - 用户信息数组，每个对象包含 user_id 和 permission
 * @returns {Promise} Promise对象
 */
export function shareDocument(id, sharedUsers) {
  return request({
    url: `/api/smartdoc/documents/${id}/share/`,
    method: 'post',
    data: {
      shared_users: sharedUsers
    }
  })
}

/**
 * 获取所有可分享用户列表
 * @returns {Promise} Promise对象
 */
export function getUsers() {
  return request({
    url: '/api/smartdoc/documents/users/',
    method: 'get'
  })
}

/**
 * 获取文档分类列表
 * @param {Object} params - 查询参数
 * @returns {Promise} Promise对象
 */
export function getDocumentCategories(params) {
  console.log('调用getDocumentCategories API, 参数:', params);
  return request({
    url: '/api/smartdoc/categories/',
    method: 'get',
    params
  }).then(response => {
    console.log('getDocumentCategories API响应:', response);
    return response;
  }).catch(error => {
    console.error('getDocumentCategories API错误:', error);
    throw error;
  });
}

/**
 * 创建文档分类
 * @param {Object} data - 分类数据
 * @returns {Promise} Promise对象
 */
export function createDocumentCategory(data) {
  return request({
    url: '/api/smartdoc/categories/',
    method: 'post',
    data
  })
}

/**
 * 更新文档分类
 * @param {number} id - 分类ID
 * @param {Object} data - 更新数据
 * @returns {Promise} Promise对象
 */
export function updateDocumentCategory(id, data) {
  return request({
    url: `/api/smartdoc/categories/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除文档分类
 * @param {number} id - 分类ID
 * @returns {Promise} Promise对象
 */
export function deleteDocumentCategory(id) {
  return request({
    url: `/api/smartdoc/categories/${id}/`,
    method: 'delete'
  })
}

/**
 * 获取文档相关文档（上下文感知）
 * @param {number} id - 文档ID
 * @returns {Promise} Promise对象
 */
export function getRelatedDocuments(id) {
  return request({
    url: `/api/smartdoc/documents/${id}/related_documents/`,
    method: 'get'
  })
}

/**
 * 生成文档相关文档（上下文感知）
 * @param {number} id - 文档ID
 * @returns {Promise} Promise对象
 */
export function generateRelatedDocuments(id) {
  return request({
    url: `/api/smartdoc/documents/${id}/generate_related/`,
    method: 'post'
  })
} 

/**
 * AI生成文档
 * @param {Object} data - {title, requirement, category_id, doc_type}
 * @returns {Promise} Promise对象，返回{id, title}
 */
export function aiGenerateDocument(data) {
  return request({
    url: '/api/smartdoc/ai_generate/',
    method: 'post',
    data,
    timeout: 180000 // 3分钟，防止AI生成超时
  })
} 

/**
 * AI内容扩写
 * @param {number} id - 文档ID
 * @param {Object} data - 扩写参数，如{selection, length}
 * @returns {Promise} Promise对象
 */
export function expandContent(id, data) {
  return request({
    url: `/api/smartdoc/documents/${id}/expand_content/`,
    method: 'post',
    data,
    timeout: 120000 // 2分钟，防止AI生成超时
  })
}

/**
 * AI文本润色
 * @param {number} id - 文档ID
 * @param {Object} data - 润色参数，如{selection, style}
 * @returns {Promise} Promise对象
 */
export function polishText(id, data) {
  return request({
    url: `/api/smartdoc/documents/${id}/polish_text/`,
    method: 'post',
    data,
    timeout: 120000 // 2分钟，防止AI生成超时
  })
}

/**
 * AI语法纠错
 * @param {number} id - 文档ID
 * @param {Object} data - 纠错参数，如{selection}
 * @returns {Promise} Promise对象
 */
export function grammarCheck(id, data) {
  return request({
    url: `/api/smartdoc/documents/${id}/grammar_check/`,
    method: 'post',
    data,
    timeout: 120000 // 2分钟，防止AI生成超时
  }).then(res => res.data)
}

/**
 * AI多语言翻译
 * @param {number} id - 文档ID
 * @param {Object} data - { selection, target_lang }
 * @returns {Promise} Promise对象
 */
export function translateText(id, data) {
  return request({
    url: `/api/smartdoc/documents/${id}/translate/`,
    method: 'post',
    data,
    timeout: 120000
  }).then(res => res.data)
}

/**
 * 文档智能问答
 * @param {number} id - 文档ID
 * @param {Object} data - { question, context }
 * @returns {Promise} Promise对象
 */
export function docQa(id, data) {
  return request({
    url: `/api/smartdoc/documents/${id}/qa/`,
    method: 'post',
    data,
    timeout: 120000
  }).then(res => res.data)
}

/**
 * 导出文档为PDF文件
 * @param {number} id - 文档ID
 * @returns {Promise} Promise对象，返回Blob
 */
export function exportDocumentAsPdf(id) {
  return request({
    url: `/api/smartdoc/documents/${id}/export/pdf/`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 导出文档为Word文件
 * @param {number} id - 文档ID
 * @returns {Promise} Promise对象，返回Blob
 */
export function exportDocumentAsWord(id) {
  return request({
    url: `/api/smartdoc/documents/${id}/export/word/`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 导入Word文档
 * @param {FormData} formData - 包含Word文件的FormData对象
 * @returns {Promise} Promise对象
 */
export function importWordDocument(formData) {
  return request({
    url: '/api/smartdoc/documents/import/word/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 60000 // 60秒超时
  })
} 
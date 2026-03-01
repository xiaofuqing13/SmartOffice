/**
 * 知识库API服务
 */
import request from '@/utils/request'

const baseURL = '/api/knowledge'  // 确保这个路径与后端实际部署的路径一致

// 分类相关API
export function getCategories() {
  console.log('调用getCategories API函数')
  return request({
    url: `${baseURL}/categories/`,
    method: 'get'
  }).then(response => {
    console.log('getCategories API响应成功:', response)
    
    // 确保返回有效的数据，即使后端返回空或格式不一致
    if (!response) {
      console.warn('getCategories响应为空，返回空数组')
      return []
    }
    
    // 根据不同的数据格式返回正确的结果
    if (Array.isArray(response)) {
      return response
    } else if (response.results && Array.isArray(response.results)) {
      return response.results
    } else if (response.data && Array.isArray(response.data)) {
      return response.data
    } else if (typeof response === 'object') {
      // 尝试查找可能的数组字段
      for (const key of ['items', 'categories', 'list']) {
        if (response[key] && Array.isArray(response[key])) {
          return response[key]
        }
      }
    }
    
    // 所有尝试都失败时，返回空数组而不是错误
    console.warn('无法从响应中提取分类数据，返回空数组:', response)
    return []
  }).catch(error => {
    console.error('getCategories API请求失败:', error)
    if (error.response) {
      console.error('错误状态码:', error.response.status)
      console.error('错误数据:', error.response.data)
    }
    // 返回空数组而不是抛出错误，使调用代码更健壮
    return []
  })
}

export function addCategory(data) {
  return request({
    url: `${baseURL}/categories/`,
    method: 'post',
    data
  })
}

export function updateCategory(id, data) {
  return request({
    url: `${baseURL}/categories/${id}/`,
    method: 'put',
    data
  })
}

export function deleteCategory(id) {
  return request({
    url: `${baseURL}/categories/${id}/`,
    method: 'delete'
  })
}

// 知识库文档相关API
export function getDocuments(params) {
  console.log('调用getDocuments API:', `${baseURL}/documents/`, '参数:', params)
  return request({
    url: `${baseURL}/documents/`,
    method: 'get',
    params
  }).then(response => {
    console.log('getDocuments API响应成功:', response)
    return response
  }).catch(error => {
    console.error('getDocuments API请求失败:', error)
    if (error.response) {
      console.error('错误状态码:', error.response.status)
      console.error('错误数据:', error.response.data)
    }
    throw error
  })
}

export function getDocument(id) {
  return request({
    url: `${baseURL}/documents/${id}/`,
    method: 'get'
  })
}

export function uploadDocument(data) {
  console.log('开始上传文件...', data);
  
  // 检查FormData中是否包含文件及其大小
  if (data instanceof FormData) {
    const file = data.get('file');
    if (file) {
      console.log('FormData中的文件信息:', {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
      });
      
      // 验证文件有效性
      if (!file.size || file.size === 0) {
        return Promise.reject(new Error('文件大小为0，无法上传'));
      }
    } else {
      console.warn('FormData中未找到文件!');
      return Promise.reject(new Error('未找到有效文件'));
    }
  }
  
  return request({
    url: `${baseURL}/documents/`,
    method: 'post',
    data,
    timeout: 120000, // 增加超时时间到120秒，大文件上传需要更长时间
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: progressEvent => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      console.log(`上传进度: ${percentCompleted}%`);
    }
  }).then(response => {
    console.log('文件上传成功响应:', response);
    return response;
  }).catch(error => {
    console.error('文件上传失败:', error);
    
    // 处理不同的错误情况
    if (error.response) {
      console.error('上传错误状态码:', error.response.status);
      console.error('上传错误数据:', error.response.data);
      
      // 处理特定的错误代码
      if (error.response.status === 413) {
        error.message = '文件太大，超出服务器允许的上传限制';
      } else if (error.response.status === 400) {
        error.message = `上传参数错误: ${JSON.stringify(error.response.data)}`;
      } else if (error.response.status === 401) {
        error.message = '未授权，请重新登录后再尝试上传';
      } else if (error.response.status === 500) {
        error.message = '服务器处理上传时发生错误';
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('没有收到上传响应:', error.request);
      if (error.code === 'ECONNABORTED') {
        error.message = '上传超时，请检查网络或尝试上传较小的文件';
      } else {
        error.message = '网络错误，未收到服务器响应';
      }
    }
    
    throw error;
  });
}

export function updateDocument(id, data) {
  return request({
    url: `${baseURL}/documents/${id}/`,
    method: 'put',
    data
  })
}

export function deleteDocument(id) {
  console.log('>>> deleteDocument function entered for ID:', id);
  const requestConfig = {
    url: `${baseURL}/documents/${id}/`,
    method: 'delete'
  };
  console.log('>>> deleteDocument - Request config prepared:', requestConfig);
  return request(requestConfig).then(response => {
    console.log('deleteDocument API响应成功:', response);
    return response;
  }).catch(error => {
    console.error('deleteDocument API请求失败:', error);
    if (error.response) {
      console.error('错误状态码:', error.response.status);
      console.error('错误数据:', error.response.data);
    }
    throw error;
  });
}

export function downloadDocumentFile(id) {
  return request({
    url: `${baseURL}/documents/${id}/`,
    method: 'get',
    responseType: 'blob'
  })
}

export function reprocessDocument(id) {
  return request({
    url: `${baseURL}/documents/${id}/reprocess/`,
    method: 'post'
  })
}

// 文档块相关API
export function getDocumentChunks(documentId) {
  return request({
    url: `${baseURL}/documents/${documentId}/chunks/`,
    method: 'get'
  })
}

export function searchKnowledge(query) {
  return request({
    url: `${baseURL}/search/`,
    method: 'get',
    params: { query }
  })
}

export function getDocumentStatistics() {
  return request({
    url: `${baseURL}/statistics/`,
    method: 'get'
  })
}

// 知识库构建相关API
export function buildKnowledgeBase() {
  console.log('调用buildKnowledgeBase API')
  return request({
    url: `${baseURL}/build/`,
    method: 'post'
  }).then(response => {
    console.log('buildKnowledgeBase API响应成功:', response)
    return response
  }).catch(error => {
    console.error('buildKnowledgeBase API请求失败:', error)
    if (error.response) {
      console.error('错误状态码:', error.response.status)
      console.error('错误数据:', error.response.data)
    }
    throw error
  })
}

export function getKnowledgeBaseStatus() {
  return request({
    url: `${baseURL}/build/status/`,
    method: 'get'
  })
} 

// 知识库列表API
export function getKnowledgeList() {
  return request({
    url: `${baseURL}/list/`,
    method: 'get'
  })
}

// 知识图谱相关API
export function getKnowledgeGraphData(params) {
  console.log('调用getKnowledgeGraphData API:', `${baseURL}/graph-data/`, '参数:', params)
  return request({
    url: `${baseURL}/graph-data/`,
    method: 'get',
    params
  }).then(response => {
    console.log('getKnowledgeGraphData API响应成功:', response)
    return response
  }).catch(error => {
    console.error('getKnowledgeGraphData API请求失败:', error)
    if (error.response) {
      console.error('错误状态码:', error.response.status)
      console.error('错误数据:', error.response.data)
    }
    throw error
  })
}

export function getEntityDetail(entityId) {
  console.log('调用getEntityDetail API:', `${baseURL}/entities/${entityId}/`)
  return request({
    url: `${baseURL}/entities/${entityId}/`,
    method: 'get'
  }).then(response => {
    console.log('getEntityDetail API响应成功:', response)
    return response
  }).catch(error => {
    console.error('getEntityDetail API请求失败:', error)
    if (error.response) {
      console.error('错误状态码:', error.response.status)
      console.error('错误数据:', error.response.data)
    }
    throw error
  })
}
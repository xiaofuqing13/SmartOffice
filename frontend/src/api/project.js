import request from '@/utils/request'

// 获取项目文档列表
export function fetchProjectDocuments(projectId) {
  return request({
    url: '/api/project-documents/',
    method: 'get',
    params: { project: projectId }
  })
}

// 上传项目文档
export function uploadProjectDocument(data) {
  return request({
    url: '/api/project-documents/',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 删除项目文档
export function deleteProjectDocument(id) {
  return request({
    url: `/api/project-documents/${id}/`,
    method: 'delete'
  })
}

// 编辑项目文档
export function updateProjectDocument(id, data) {
  return request({
    url: `/api/project-documents/${id}/`,
    method: 'patch',
    data,
    headers: { 'Content-Type': 'application/json' }
  })
}

// 获取项目需求列表
export function fetchRequirements(projectId) {
  return request({
    url: '/api/requirements/',
    method: 'get',
    params: { project: projectId }
  })
}

// 创建需求
export function createRequirement(data) {
  return request({
    url: '/api/requirements/',
    method: 'post',
    data
  })
}

// 更新需求
export function updateRequirement(id, data) {
  return request({
    url: `/api/requirements/${id}/`,
    method: 'patch',
    data
  })
}

// 删除需求
export function deleteRequirement(id) {
  return request({
    url: `/api/requirements/${id}/`,
    method: 'delete'
  })
}

// 获取需求AI分析
export function getRequirementAiAnalysis(projectId) {
  return request({
    url: '/api/requirements/ai_analysis/',
    method: 'get',
    params: { project: projectId }
  })
}

// 获取文档AI聚合分析
export function getDocumentAiDashboard(projectId) {
  return request({
    url: '/api/project-documents/ai_dashboard/',
    method: 'get',
    params: { project: projectId }
  })
}

// 获取单条需求AI分析
export function getSingleRequirementAiAnalysis(requirementId) {
  return request({
    url: `/api/requirements/${requirementId}/ai_analysis/`,
    method: 'get'
  })
}

// 导出项目AI分析报告（支持POST图片）
export function exportProjectAiReport(projectId, data) {
  return request({
    url: `/api/projects/${projectId}/export_ai_report/`,
    method: 'post',
    data,
    responseType: 'blob', // 重要：下载文件
    timeout: 120000, // 增加超时时间到120秒
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/pdf, application/json;q=0.9'
    },
    validateStatus: function (status) {
      return status >= 200 && status < 500 // 默认只接受2xx响应状态码
    }
  })
}

// 获取项目报表中每个图表的AI分析
export function getProjectChartAnalysis(projectId) {
  return request({
    url: `/api/projects/${projectId}/chart_analysis/`,
    method: 'get'
  })
} 
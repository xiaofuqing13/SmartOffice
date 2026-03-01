import request from '@/utils/request'

/**
 * 公司相关API服务
 */

// 获取所有公司列表
export function getCompanyList() {
  return request({
    url: '/api/auth/companies/',
    method: 'get'
  })
}

// 获取简化的公司列表(id和名称)
export function getSimpleCompanyList() {
  return request({
    url: '/api/auth/companies/simple_list/',
    method: 'get',
    auth: false
  })
}

// 获取公司详情
export function getCompanyDetails(id) {
  return request({
    url: `/api/auth/companies/${id}/company_details/`,
    method: 'get'
  })
}

// 创建公司
export function createCompany(data) {
  return request({
    url: '/api/auth/companies/',
    method: 'post',
    data
  })
}

// 更新公司信息
export function updateCompany(id, data) {
  return request({
    url: `/api/auth/companies/${id}/`,
    method: 'put',
    data
  })
}

// 删除公司
export function deleteCompany(id) {
  return request({
    url: `/api/auth/companies/${id}/`,
    method: 'delete'
  })
}

/**
 * 部门相关API服务
 */

// 获取部门列表
export function getDepartmentList(params) {
  return request({
    url: '/api/auth/departments/',
    method: 'get',
    params
  })
}

// 获取公司的部门列表
export function getCompanyDepartments(companyId) {
  return request({
    url: '/api/auth/departments/company_departments/',
    method: 'get',
    params: {
      company_id: companyId
    }
  })
}

// 创建部门
export function createDepartment(data) {
  return request({
    url: '/api/auth/departments/',
    method: 'post',
    data
  })
}

// 更新部门信息
export function updateDepartment(id, data) {
  return request({
    url: `/api/auth/departments/${id}/`,
    method: 'put',
    data
  })
}

// 删除部门
export function deleteDepartment(id) {
  return request({
    url: `/api/auth/departments/${id}/`,
    method: 'delete'
  })
}

// 获取当前登录用户所属公司信息
export function getCurrentUserCompany() {
  return request({
    url: '/api/auth/companies/current_user_company/',
    method: 'get'
  })
} 
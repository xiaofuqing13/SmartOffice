import axios from 'axios';

// 确保使用与 auth.js 中相同的 axios 实例或配置
const api = axios.create({
  baseURL: 'http://localhost:8000/api/admin',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器以附加JWT令牌
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 管理员相关API
export default {
  // 获取仪表盘所有数据
  getDashboardData() {
    return api.get('/dashboard/');
  },

  // 获取仪表盘图表的AI分析
  getDashboardAnalysis(chartTitle, chartData) {
    return api.post('/dashboard/analysis/', {
      chart_title: chartTitle,
      chart_data: chartData,
    });
  },

  // 获取用户列表 (支持分页和搜索)
  getUsers(params) {
    return api.get('/users/', { params });
  },

  // 创建新用户
  createUser(data) {
    return api.post('/users/', data);
  },

  // 更新用户信息
  updateUser(id, data) {
    return api.patch(`/users/${id}/`, data);
  },

  // 删除用户
  deleteUser(id) {
    return api.delete(`/users/${id}/`);
  },

  // 公司管理
  getCompanies(params) {
    return api.get('/companies/', { params });
  },
  createCompany(data) {
    return api.post('/companies/', data);
  },
  updateCompany(id, data) {
    return api.patch(`/companies/${id}/`, data);
  },
  deleteCompany(id) {
    return api.delete(`/companies/${id}/`);
  },

  // 部门管理
  getDepartments(params) {
    return api.get('/departments/', { params });
  },
  createDepartment(data) {
    return api.post('/departments/', data);
  },
  updateDepartment(id, data) {
    return api.patch(`/departments/${id}/`, data);
  },
  deleteDepartment(id) {
    return api.delete(`/departments/${id}/`);
  },

  // 获取智能文档
  getSmartDocs(params) {
    return api.get('/smart-docs/', { params });
  },

  // 获取智能文档详情
  getSmartDocDetail(id) {
    return api.get(`/smart-docs/${id}/`);
  },

  // 删除智能文档
  deleteSmartDoc(id) {
    return api.delete(`/smart-docs/${id}/`);
  },

  // 获取合同列表
  getContracts(params) {
    return api.get('/contracts/', { params });
  },

  // 获取合同详情
  getContractDetail(id) {
    return api.get(`/contracts/${id}/`);
  },

  // 删除合同
  deleteContract(id) {
    return api.delete(`/contracts/${id}/`);
  },

  // Contract Templates
  getContractTemplates() {
    return api.get('/contract-templates/');
  },
  getContractTemplate(id) {
    return api.get(`/contract-templates/${id}/`);
  },
  createContractTemplate(data) {
    return api.post('/contract-templates/', data);
  },
  updateContractTemplate(id, data) {
    return api.patch(`/contract-templates/${id}/`, data);
  },
  deleteContractTemplate(id) {
    return api.delete(`/contract-templates/${id}/`);
  },

  // Knowledge Base Categories
  getKnowledgeCategories(params) {
    return api.get('/knowledge-categories/', { params });
  },
  createKnowledgeCategory(data) {
    return api.post('/knowledge-categories/', data);
  },
  updateKnowledgeCategory(id, data) {
    return api.patch(`/knowledge-categories/${id}/`, data);
  },
  deleteKnowledgeCategory(id) {
    return api.delete(`/knowledge-categories/${id}/`);
  },

  // Knowledge Base Articles
  getKnowledgeBases(params) {
    return api.get('/knowledge-bases/', { params });
  },
  getKnowledgeBaseDetail(id) {
    return api.get(`/knowledge-bases/${id}/`);
  },
  createKnowledgeBase(data) {
    const formData = new FormData();
    for (const key in data) {
      if (data[key] !== null && data[key] !== undefined) {
        formData.append(key, data[key]);
      }
    }
    return api.post('/knowledge-bases/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  updateKnowledgeBase(id, data) {
    const formData = new FormData();
    for (const key in data) {
      // 避免将文件对象作为普通字段附加
      if (key !== 'original_file' && data[key] !== null && data[key] !== undefined) {
        formData.append(key, data[key]);
      }
    }
    // 仅当存在新文件时才附加文件
    if (data.original_file instanceof File) {
      formData.append('original_file', data.original_file);
    }
    return api.patch(`/knowledge-bases/${id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  deleteKnowledgeBase(id) {
    return api.delete(`/knowledge-bases/${id}/`);
  },
  
  // Knowledge Base Building
  getKnowledgeBuildStatus() {
    return api.get('/knowledge/build/');
  },
  buildKnowledgeForCompanies(companyIds) {
    return api.post('/knowledge/build/', { company_ids: companyIds });
  },
};
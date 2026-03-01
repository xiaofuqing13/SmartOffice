import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加认证token
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

// 响应拦截器 - 处理常见错误
api.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    // 错误详细日志
    console.error('API错误:', error.response || error);
    
    if (error.response && error.response.status === 401) {
      // 清除本地token信息
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // 不要在这里进行重定向，而是通过store中的action来处理
      // 由于axios拦截器不应该直接访问router，所以让组件处理重定向
      // 或在捕获错误的地方进行处理
    }
    return Promise.reject(error);
  }
);

// 认证相关API
export default {
  // 用户登录
  login(data) {
    return api.post('/api/auth/login/', data);
  },
  
  // 管理员登录
  adminLogin(data) {
    return api.post('/api/auth/admin/login/', data);
  },
  
  // 用户注册
  register(data) {
    console.log('发送注册请求:', data);
    return api.post('/api/auth/register/', data, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      }
    });
  },
  
  // 用户登出
  logout() {
    return api.post('/api/auth/logout/');
  },
  
  // 请求重置密码
  requestPasswordReset(data) {
    return api.post('/api/auth/password/request-reset/', data);
  },
  
  // 重置密码
  resetPassword(data) {
    return api.post('/api/auth/password/reset/', data);
  }
}; 
import axios from 'axios';
import { ElMessage } from 'element-plus';

// 创建axios实例
const service = axios.create({
  baseURL: 'http://localhost:8000',  // 明确指定后端地址
  timeout: 180000,  // 将超时时间从60秒增加到180秒，适应AI生成等慢接口
  headers: {
    'Content-Type': 'application/json'
  }
});

// 智能超时设置函数 - 根据请求类型和数据量调整超时时间
const getSmartTimeout = (config) => {
  const url = config.url || '';
  const method = config.method || '';
  const data = config.data;
  
  // 默认3分钟
  let timeout = 180000;
  
  // AI生成文档接口单独设置
  if (url.includes('ai_generate_document')) {
    timeout = 180000;
  }
  // 其他AI相关接口
  else if (url.includes('ai_polish') || url.includes('check_contract')) {
    if ((method === 'post' || method === 'put') && data) {
      const contentSize = typeof data === 'string' ? 
                          data.length : 
                          (data.content ? data.content.length : 0);
      if (contentSize > 50000) {
        timeout = 180000;
      } else if (contentSize > 20000) {
        timeout = 120000;
      } else if (contentSize > 5000) {
        timeout = 90000;
      }
      console.log(`智能超时: 内容大小 ${contentSize} 字符, 设置超时 ${timeout/1000} 秒`);
    } else {
      timeout = 120000;
    }
  } else if (url.includes('contract') && method === 'post' && data && data.use_ai_agent) {
    console.log('检测到AI合同生成请求，设置较长超时时间');
    timeout = 180000;
  }
  
  return timeout;
};

// 请求拦截器 - 添加认证token
service.interceptors.request.use(
  config => {
    console.log('发送请求至:', config.url, '方法:', config.method);
    
    // 应用智能超时设置
    config.timeout = getSmartTimeout(config);
    
    // 对于文件上传请求增加超时时间
    if (config.data instanceof FormData) {
      const hasFile = Array.from(config.data.entries()).some(entry => entry[1] instanceof File);
      if (hasFile) {
        console.log('检测到文件上传请求，增加超时时间');
        config.timeout = Math.max(config.timeout, 180000); // 至少3分钟
      }
    }
    
    // 传递AbortSignal，用于请求取消
    if (config.signal) {
      console.log('请求可取消 (AbortSignal已设置)');
    }
    
    // 检查数据对象中的signal属性
    if (config.data && config.data.signal) {
      config.signal = config.data.signal;
      // 从数据对象中移除signal属性，防止序列化错误
      delete config.data.signal;
      console.log('从数据中提取并设置AbortSignal');
    }
    
    const requireAuth = config.auth !== false; // 检查请求是否需要认证
    const token = localStorage.getItem('token'); // 从 localStorage 获取 token
    console.log('Token from localStorage:', token ? '有效令牌' : '无令牌');
    
    if (token && requireAuth) {
      // 修正：使用Bearer认证格式，而不是Token格式
      config.headers.Authorization = `Bearer ${token}`; 
      console.log('已添加认证token (格式: Bearer ...) 对请求:', config.url);
      
      // 调试信息
      if (config.url.includes('export') || config.url.includes('export-direct')) {
        console.log('导出请求的认证头:', config.headers.Authorization ? '已设置' : '未设置');
      }
    } else if (!requireAuth) {
      console.log('此请求不需要认证:', config.url, '方法:', config.method);
    } else {
      console.warn('未找到认证token，Authorization头部未设置:', config.url);
      
      // 对于导出请求特别提示
      if (config.url.includes('export') || config.url.includes('export-direct')) {
        console.warn('导出文档需要认证，但未找到认证令牌！');
      }
    }
    
    // 如果是FormData，移除Content-Type，让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
      // 添加特别的日志用于调试文件上传
      if (config.url.includes('/api/chat/messages/')) {
        console.log('检测到聊天消息上传请求，FormData内容:');
        for (let [key, value] of config.data.entries()) {
          if (value instanceof File) {
            console.log(`- ${key}: [文件] ${value.name}, 类型: ${value.type}, 大小: ${value.size} 字节`);
          } else {
            console.log(`- ${key}: ${value}`);
          }
        }
      }
    } else if (config.method === 'post' || config.method === 'put') {
      if (!config.headers['Content-Type']) {
        config.headers['Content-Type'] = 'application/json';
      }
    }
    
    return config;
  },
  error => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一处理响应和错误
service.interceptors.response.use(
  response => {
    console.log('收到响应:', response.config.url, response.status)
    
    // 优先处理 204 No Content 响应
    if (response.status === 204) {
      // 对于204，没有响应体，直接返回一个包含状态码的对象，以便上层判断
      return { status: 204 };
    }
    
    // 记录文档详情API的响应大小
    if (response.config.url.includes('/api/smartdoc/documents/') && 
        response.config.url.endsWith('/') &&
        !response.config.url.includes('list')) {
      // 这可能是文档详情请求
      const contentLength = response.headers['content-length'] || '未知';
      console.log('文档详情响应大小:', contentLength, '字节');
      
      // 如果内容很大，记录更详细的信息
      if (contentLength && parseInt(contentLength) > 100000) {
        console.log('检测到大型文档响应:', {
          url: response.config.url,
          size: contentLength + ' 字节',
          status: response.status,
          headers: response.headers,
          time: new Date().toISOString()
        });
      }
    }
    
    // 记录关键API的更详细日志
    if (response.config.url.includes('check_contract') || 
        response.config.url.includes('ai_polish') ||
        (response.config.url.includes('contracts') && response.config.method === 'post')) {
      console.log('重要API响应:', {
        url: response.config.url,
        status: response.status,
        headers: response.headers,
        dataType: typeof response.data,
        dataHasKeys: typeof response.data === 'object' ? Object.keys(response.data).join(',') : 'not-an-object',
        responseTime: new Date().toISOString()
      });
    }
    
    const res = response.data;
    
    // 详细记录响应数据类型和结构
    if (res) {
      const type = typeof res;
      const isArray = Array.isArray(res);
      console.log('响应数据类型:', isArray ? 'Array' : type, 
                  isArray ? `(长度:${res.length})` : 
                  (type === 'object' ? `(键:${Object.keys(res).join(',')})` : ''));
                  
      // 检查文档详情响应是否包含内容字段
      if (response.config.url.includes('/api/smartdoc/documents/') && 
          response.config.url.endsWith('/') &&
          type === 'object' && 
          res.content === undefined && 
          res.id) {
        console.warn('警告: 文档详情响应缺少content字段');
      }
    }
    
    // 如果是下载文件直接返回
    if (response.config.responseType === 'blob') {
      console.log('检测到blob响应类型，文件大小:', response.data.size, '字节');
      // 检查blob是否有效
      if (response.data.size < 100) {
        console.warn('警告：blob响应数据过小，可能无效:', response.data.size, '字节');
      }
      return response;
    }
    
    // 检查是否是DRF分页格式
    const isDRFPagination = res && !Array.isArray(res) && res.results && Array.isArray(res.results);
    if (isDRFPagination) {
      console.log('检测到DRF分页响应格式:', 
                  'count=', res.count, 
                  'next=', Boolean(res.next), 
                  'previous=', Boolean(res.previous),
                  '结果数量=', res.results.length);
      // 保留完整的分页信息，但添加data字段指向results
      return {
        count: res.count,
        total: res.count, // 添加total别名，统一接口
        next: res.next,
        previous: res.previous,
        results: res.results,
        data: res.results
      };
    }
    
    // 将后端数据统一为 { data: [...] } 格式
    // 这样便于前端处理不同类型的响应
    if (response.data) {
      // 普通数组响应 [...]
      if (Array.isArray(response.data)) {
        console.log('处理数组响应数据');
        return {
          data: response.data,
          count: response.data.length, // 添加计数字段
          total: response.data.length   // 添加总数字段
        };
      }
      // 单个对象响应 {...}
      else if (typeof response.data === 'object') {
        console.log('处理对象响应数据');
        // 如果对象中已有data字段，直接保留，否则将整个对象作为data
        if ('data' in response.data) {
          return response.data;
        } else {
          return {
            data: response.data
          };
        }
      }
    }
    
    // 默认返回空对象
    return { data: {} };
  },
  error => {
    // 检查是否是取消请求的错误
    if (axios.isCancel(error)) {
      console.log('请求被取消:', error.message);
      // 自定义错误对象，标记为请求取消
      return Promise.reject({
        isCancelled: true,
        message: '请求被取消，可能是超时或用户中断'
      });
    }
    
    // 首先检查是否为密码修改页面的旧密码错误 - 这是预期的验证结果而非错误
    if (error.response && error.response.status === 400) {
      const data = error.response.data;
      const isPasswordChangeEndpoint = error.config.url.includes('/api/auth/users/change_password/');
      const isOldPasswordIncorrect = data && 
        data.old_password && 
        Array.isArray(data.old_password) && 
        data.old_password.includes("Incorrect password.");
      
      // 如果是密码更改且旧密码错误，作为特殊情况处理
      if (isPasswordChangeEndpoint && isOldPasswordIncorrect) {
        console.log('密码验证：当前密码不正确 - 这是预期的验证结果');
        // 包装为验证结果而非错误
        return Promise.reject({
          isValidationResult: true,
          status: 400,
          data: error.response.data,
          message: '',
          fieldErrors: {
            old_password: ['Incorrect password.']
          }
        });
      }
    }

    // 正常错误日志记录和处理
    console.error('响应错误:', error);
    
    // 检查是否是超时错误
    if (error.code === 'ECONNABORTED' || (error.message && error.message.includes('timeout'))) {
      console.error('请求超时:', error.config.url);
      ElMessage.error('请求超时，服务器响应时间过长，请稍后重试');
      return Promise.reject({
        isTimeout: true,
        message: '请求超时，服务器响应时间过长'
      });
    }
    
    // 处理HTTP错误
    if (error.response) {
      const status = error.response.status;
      
      // 特殊处理blob响应错误
      if (error.config && error.config.responseType === 'blob') {
        console.error('Blob响应错误:', status, error.config.url);
        
        // 尝试读取blob错误内容
        if (error.response.data instanceof Blob) {
          const blob = error.response.data;
          // 如果是JSON格式的错误信息
          if (blob.type === 'application/json') {
            const reader = new FileReader();
            reader.onload = () => {
              try {
                const errorData = JSON.parse(reader.result);
                console.error('Blob错误详情:', errorData);
                ElMessage.error(errorData.error || errorData.message || '导出失败，请稍后重试');
              } catch (e) {
                console.error('解析Blob错误失败:', e);
                ElMessage.error('导出失败，请稍后重试');
              }
            };
            reader.readAsText(blob);
          } else {
            ElMessage.error('导出失败，请稍后重试');
          }
          
          return Promise.reject({
            isBlobError: true,
            status,
            message: '导出文件失败'
          });
        }
      }
      
      // 认证错误
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // 只有当前不在登录页面时才重定向
        const currentPath = window.location.pathname;
        if (currentPath !== '/login' && currentPath !== '/') {
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
        }
      } 
      // 权限错误
      else if (status === 403) {
        ElMessage.error('登录已过期，请重新登录');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // 只有当前不在登录页面时才重定向
        const currentPath = window.location.pathname;
        if (currentPath !== '/login' && currentPath !== '/') {
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
        }
      } 
      // 请求错误
      else if (status === 400) {
        const data = error.response.data;
        console.error('400错误详细数据:', data);
        console.error('400错误完整内容:', JSON.stringify(data, null, 2));
        
        // 处理400错误
        // 尝试提取错误信息
        let message = '请求参数错误';
        if (data && data.message) {
          message = data.message;
        } else if (data && data.error) {
          message = data.error;
        } else if (typeof data === 'string') {
          message = data;
        } else if (data && typeof data === 'object') {
          // 如果是对象，尝试从字段错误中提取信息
          message = Object.entries(data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
        }
        ElMessage.error(message);
      } 
      // 服务器错误
      else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后再试');
      } 
      // 其他错误
      else {
        try {
          ElMessage.error(error.response.data && error.response.data.message ? error.response.data.message : '请求失败');
        } catch (e) {
          ElMessage.error('请求失败');
        }
      }
    } else if (error.request) {
      // 请求发送但没有响应
      ElMessage.error('网络连接失败，请检查网络设置');
    } else {
      // 请求设置错误
      ElMessage.error('请求配置错误');
    }
    
    return Promise.reject(error);
  }
);

export default service; 
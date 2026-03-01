import axios from 'axios'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * 封装API请求钩子函数
 * @returns {Object} 包含request方法和loading状态的对象
 */
export function useRequest() {
  const loading = ref(false)
  
  // 创建axios实例
  const instance = axios.create({
    timeout: 10000, // 请求超时时间
    headers: {
      'Content-Type': 'application/json'
    }
  })
  
  // 请求拦截器
  instance.interceptors.request.use(
    config => {
      // 从localStorage获取token
      const token = localStorage.getItem('token')
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
      return config
    },
    error => {
      console.error('请求错误:', error)
      return Promise.reject(error)
    }
  )
  
  // 响应拦截器
  instance.interceptors.response.use(
    response => {
      // 如果响应成功但业务状态码表示失败
      if (response.data && response.data.code >= 400) {
        ElMessage.error(response.data.message || '请求失败')
        return Promise.reject(response.data)
      }
      return response.data
    },
    error => {
      // 处理响应错误
      if (error.response) {
        const status = error.response.status
        
        if (status === 401) {
          // 未授权，可能是token过期
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          // 跳转到登录页
          window.location.href = '/login'
        } else if (status === 403) {
          ElMessage.error('没有权限执行此操作')
        } else if (status === 404) {
          ElMessage.error('请求的资源不存在')
        } else if (status === 500) {
          ElMessage.error('服务器内部错误')
        } else {
          ElMessage.error(error.response.data?.message || '请求失败')
        }
      } else if (error.request) {
        // 请求已发送但没有收到响应
        ElMessage.error('服务器无响应，请稍后重试')
      } else {
        // 请求配置出错
        ElMessage.error('请求配置错误')
      }
      
      return Promise.reject(error)
    }
  )
  
  /**
   * 通用请求方法
   * @param {string} url - 请求地址
   * @param {Object} options - 请求配置
   * @returns {Promise} 请求结果
   */
  const request = async (url, options = {}) => {
    loading.value = true
    
    try {
      const { method = 'GET', params, data, ...rest } = options
      
      const config = {
        url,
        method,
        params,
        data,
        ...rest
      }
      
      const response = await instance(config)
      return response
    } catch (error) {
      console.error('请求出错:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  return {
    loading,
    request
  }
} 
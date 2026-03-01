import authApi from '@/api/auth';
import userApi from '@/api/user';

const state = {
  token: localStorage.getItem('token') || '',
  user: JSON.parse(localStorage.getItem('user')) || null,
  loading: false,
  error: null
};

const mutations = {
  AUTH_REQUEST(state, loading = true) {
    state.loading = loading;
    if (loading) {
      state.error = null;
    }
  },
  AUTH_SUCCESS(state, { token, user }) {
    state.loading = false;
    state.token = token;
    state.user = user;
    state.error = null;
  },
  AUTH_ERROR(state, error) {
    state.loading = false;
    state.error = error;
  },
  LOGOUT(state) {
    state.token = '';
    state.user = null;
  },
  CLEAR_ERROR(state) {
    state.error = null;
  },
  UPDATE_USER_PROFILE(state, userData) {
    state.user = { ...state.user, ...userData };
    localStorage.setItem('user', JSON.stringify(state.user));
  },
  SET_USER_PROFILE(state, profile) {
    state.user = { ...state.user, ...profile };
    localStorage.setItem('user', JSON.stringify(state.user));
  }
};

const actions = {
  // 登录
  async login({ commit, dispatch }, credentials) {
    commit('AUTH_REQUEST');
    try {
      const response = await authApi.login(credentials);
      
      if (response.success) {
        const { token, userId, username } = response.data;
        
        // 保存认证信息
        localStorage.setItem('token', token);
        
        // 创建简单用户对象
        const user = {
          id: userId,
          username: username
        };
        
        // 保存用户信息
        localStorage.setItem('user', JSON.stringify(user));
        
        commit('AUTH_SUCCESS', { token, user });
        
        // 登录成功后获取完整用户信息
        dispatch('getUserProfile');
        
        return Promise.resolve(response);
      } else {
        commit('AUTH_ERROR', response.message || '登录失败');
        return Promise.reject(response);
      }
    } catch (error) {
      let errorMsg = '登录失败，请稍后重试';
      
      // 尝试从不同位置获取错误信息
      if (error.response) {
        if (error.response.data) {
          if (error.response.data.message) {
            errorMsg = error.response.data.message;
          } else if (error.response.data.detail) {
            errorMsg = error.response.data.detail;
          } else if (typeof error.response.data === 'string') {
            errorMsg = error.response.data;
          }
        } else if (error.response.statusText) {
          errorMsg = `服务器错误 (${error.response.status}): ${error.response.statusText}`;
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      commit('AUTH_ERROR', errorMsg);
      return Promise.reject({ ...error, message: errorMsg });
    }
  },
  
  // 管理员登录
  async adminLogin({ commit, dispatch }, credentials) {
    commit('AUTH_REQUEST');
    try {
      const response = await authApi.adminLogin(credentials);
      
      if (response.success) {
        const { token, userId, username } = response.data;
        
        localStorage.setItem('token', token);
        
        const user = {
          id: userId,
          username: username,
          isAdmin: true 
        };
        
        localStorage.setItem('user', JSON.stringify(user));
        
        commit('AUTH_SUCCESS', { token, user });
        
        dispatch('getUserProfile');
        
        return Promise.resolve(response);
      } else {
        commit('AUTH_ERROR', response.message || '登录失败');
        return Promise.reject(response);
      }
    } catch (error) {
      let errorMsg = '登录失败，请稍后重试';
      
      if (error.response && error.response.data && error.response.data.message) {
        errorMsg = error.response.data.message;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      commit('AUTH_ERROR', errorMsg);
      return Promise.reject({ ...error, message: errorMsg });
    }
  },
  
  // 注册
  async register({ commit }, userData) {
    commit('AUTH_REQUEST');
    try {
      const response = await authApi.register(userData);
      
      if (response.success) {
        return Promise.resolve(response);
      } else {
        commit('AUTH_ERROR', response.message);
        return Promise.reject(response);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || '注册失败，请稍后重试';
      commit('AUTH_ERROR', errorMsg);
      return Promise.reject(error);
    }
  },
  
  // 登出
  async logout({ commit }) {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('登出请求失败，但会继续清除本地会话', error);
    }
    
    // 清除本地存储
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // 切换为浅色模式
    localStorage.setItem('theme', 'light');
    document.documentElement.setAttribute('data-theme', 'light');
    
    // 更新meta主题色
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', '#ffffff');
    }
    
    // 更新状态
    commit('LOGOUT');
    
    return Promise.resolve();
  },
  
  // 请求重置密码
  async requestPasswordReset({ commit }, { email }) {
    commit('AUTH_REQUEST');
    try {
      const response = await authApi.requestPasswordReset({ email });
      
      if (response.success) {
        commit('AUTH_SUCCESS', { token: '', user: null });
        return Promise.resolve(response);
      } else {
        commit('AUTH_ERROR', response.message);
        return Promise.reject(response);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || '请求重置密码失败，请稍后重试';
      commit('AUTH_ERROR', errorMsg);
      return Promise.reject(error);
    }
  },
  
  // 重置密码
  async resetPassword({ commit }, resetData) {
    commit('AUTH_REQUEST');
    try {
      const response = await authApi.resetPassword(resetData);
      
      if (response.success) {
        commit('AUTH_SUCCESS', { token: '', user: null });
        return Promise.resolve(response);
      } else {
        commit('AUTH_ERROR', response.message);
        return Promise.reject(response);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || '重置密码失败，请稍后重试';
      commit('AUTH_ERROR', errorMsg);
      return Promise.reject(error);
    }
  },
  
  // 获取用户个人信息
  async getUserProfile({ commit }) {
    commit('AUTH_REQUEST');
    try {
      console.log('开始获取用户个人信息');
      const response = await userApi.getUserProfile();
      console.log('获取用户个人信息响应:', response);
      
      // 检查不同响应格式
      let userData = null;
      
      if (response && response.success && response.data) {
        // 标准格式 {success: true, data: {...}}
        console.log('检测到标准响应格式');
        userData = response.data;
      } else if (response && response.code === 200 && response.data) {
        // 格式 {code: 200, data: {...}}
        console.log('检测到code=200响应格式');
        userData = response.data;
      } else if (response && typeof response === 'object' && response.id) {
        // 直接返回数据对象 {id: ..., username: ...}
        console.log('检测到直接返回数据对象格式');
        userData = response;
      } else {
        console.error('无法解析用户信息响应:', response);
        commit('AUTH_ERROR', '获取用户信息失败：响应格式错误');
        return Promise.reject({message: '响应格式错误'});
      }
      
      // 检查公司ID
      if (!userData.company) {
        console.warn('用户数据中未包含公司ID:', userData);
      }
      
      commit('SET_USER_PROFILE', userData);
      console.log('用户信息已更新到Vuex和localStorage');
      return Promise.resolve({success: true, data: userData});
    } catch (error) {
      console.error('获取用户信息失败, 详细错误:', error);
      let errorMsg = '获取用户信息失败，请稍后重试';
      
      if (error.response) {
        console.error('错误状态码:', error.response.status);
        console.error('错误响应数据:', error.response.data);
        
        if (error.response.status === 403) {
          errorMsg = '您没有权限获取用户信息，请重新登录';
        } else if (error.response.data && typeof error.response.data === 'object') {
          if (error.response.data.message) {
            errorMsg = error.response.data.message;
          } else if (error.response.data.detail) {
            errorMsg = error.response.data.detail;
          }
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      commit('AUTH_ERROR', errorMsg);
      return Promise.reject({...error, message: errorMsg});
    }
  },
  
  // 更新用户个人信息
  async updateUserProfile({ commit }, profileData) {
    commit('AUTH_REQUEST');
    try {
      // 记录发送到API的数据
      console.log('发送到API的数据:', profileData);
      
      const response = await userApi.updateUserProfile(profileData);
      
      if (response.success) {
        commit('UPDATE_USER_PROFILE', response.data);
        return Promise.resolve(response);
      } else {
        const errorMsg = response.message || '更新用户信息失败';
        commit('AUTH_ERROR', errorMsg);
        return Promise.reject(errorMsg);
      }
    } catch (error) {
      // 更详细的错误处理
      console.error('用户信息更新错误:', error);
      
      let errorMsg = '更新用户信息失败，请稍后重试';
      
      // 尝试从错误对象获取更详细的信息
      if (typeof error === 'string') {
        errorMsg = error;
      } else if (error.message) {
        errorMsg = error.message;
      } else if (error.response && error.response.data) {
        if (typeof error.response.data === 'string') {
          errorMsg = error.response.data;
        } else if (error.response.data.message) {
          errorMsg = error.response.data.message;
        } else if (error.response.data.detail) {
          errorMsg = error.response.data.detail;
        } else if (error.response.data.error) {
          errorMsg = error.response.data.error;
        } else {
          // 尝试提取字段错误
          const errorFields = [];
          for (const field in error.response.data) {
            if (Array.isArray(error.response.data[field])) {
              errorFields.push(`${field}: ${error.response.data[field].join(', ')}`);
            }
          }
          if (errorFields.length > 0) {
            errorMsg = errorFields.join('; ');
          }
        }
      }
      
      commit('AUTH_ERROR', errorMsg);
      
      // 返回字符串错误，而不是复杂对象
      return Promise.reject(errorMsg);
    }
  },
  
  // 更新用户头像
  async updateUserAvatar({ commit }, formData) {
    commit('AUTH_REQUEST');
    try {
      const response = await userApi.updateUserAvatar(formData);
      
      if (response.success) {
        commit('UPDATE_USER_PROFILE', { avatar: response.data.avatar });
        return Promise.resolve(response);
      } else {
        commit('AUTH_ERROR', response.message || '更新头像失败');
        return Promise.reject(response);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || '更新头像失败，请稍后重试';
      commit('AUTH_ERROR', errorMsg);
      return Promise.reject(error);
    }
  },
  
  // 修改密码
  async changePassword({ commit }, passwordData) {
    commit('AUTH_REQUEST');
    try {
      const response = await userApi.changePassword(passwordData);
      
      if (response.success) {
        commit('CLEAR_ERROR');
        return Promise.resolve(response);
      } else {
        // 检查是否是当前密码不正确的错误
        const isOldPasswordError = response.fieldErrors && 
          response.fieldErrors.old_password && 
          Array.isArray(response.fieldErrors.old_password) && 
          response.fieldErrors.old_password.includes("Incorrect password.");
          
        // 只有在不是当前密码错误的情况下才设置全局错误状态
        if (!isOldPasswordError) {
          commit('AUTH_ERROR', response.message || '修改密码失败');
        } else {
          // 清除可能存在的错误
          commit('CLEAR_ERROR');
        }
        
        return response; // 对于验证结果不使用Promise.reject，而是直接返回
      }
    } catch (error) {
      // 检查是否是预期的密码验证结果
      if (error.isValidationResult) {
        // 清除错误状态
        commit('CLEAR_ERROR');
        // 直接返回验证结果
        return error;
      }
      
      // 检查是否是当前密码不正确的错误
      const isOldPasswordError = error.fieldErrors && 
        error.fieldErrors.old_password && 
        Array.isArray(error.fieldErrors.old_password) && 
        error.fieldErrors.old_password.includes("Incorrect password.");
        
      // 只有在不是当前密码错误的情况下才设置全局错误状态
      if (!isOldPasswordError) {
        const errorMsg = error.response?.data?.message || '修改密码失败，请稍后重试';
        commit('AUTH_ERROR', errorMsg);
      } else {
        // 清除可能存在的错误
        commit('CLEAR_ERROR');
      }
      
      return Promise.reject(error);
    } finally {
      // 结束loading状态
      commit('AUTH_REQUEST', false);
    }
  },
  
  // 清除错误
  clearError({ commit }) {
    commit('CLEAR_ERROR');
  }
};

const getters = {
  isAuthenticated: state => !!state.token,
  currentUser: state => state.user,
  loading: state => state.loading,
  error: state => state.error
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}; 
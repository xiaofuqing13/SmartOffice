import request from '@/utils/request';

/**
 * 用户API - 提供与用户相关的接口调用
 */
const userApi = {
  /**
   * 获取当前用户信息
   */
  async getUserProfile() {
    console.log('调用getUserProfile API');
    try {
    const response = await request.get('/api/auth/users/me/');
      console.log('getUserProfile API响应:', response);
      
      // 检查响应数据结构
      if (response && response.success && response.data) {
        // 标准格式：{success: true, data: {...}}
    return response;
      } else if (response && response.code === 200 && response.data) {
        // 另一种格式：{code: 200, data: {...}}
        return {
          success: true,
          data: response.data
        };
      } else if (response && typeof response === 'object' && response.id) {
        // 后端直接返回用户对象，需要包装成统一格式
        return {
          success: true,
          data: response
        };
      } else {
        console.error('getUserProfile API响应格式未识别:', response);
        return {
          success: false,
          message: '用户信息响应格式错误',
          error: response
        };
      }
    } catch (error) {
      console.error('getUserProfile API错误:', error);
      return {
        success: false,
        message: error.message || '获取用户信息失败',
        error: error
      };
    }
  },

  /**
   * 更新用户个人资料
   * @param {Object} profileData - 用户个人资料数据
   */
  async updateUserProfile(profileData) {
    let userId = profileData.id;
    if (!userId) {
      const userJson = localStorage.getItem('user');
      if (userJson) {
        const user = JSON.parse(userJson);
        userId = user.id;
      }
    }
    
    if (!userId) {
      return {
        success: false,
        message: '用户ID不存在，无法更新个人信息'
      };
    }
    
    const cleanedData = {
      username: profileData.username || '',
      name: profileData.name || '',
      email: profileData.email || '',
      phone: profileData.phone || '',
      position: profileData.position || '',
      department: profileData.department || '',
      office: profileData.office || '',
      employee_id: profileData.employee_id || '',
      manager: profileData.manager || '',
      bio: profileData.bio || ''
    };
    
    if (!cleanedData.username) {
      const userJson = localStorage.getItem('user');
      if (userJson) {
        const user = JSON.parse(userJson);
        if (user.username) {
          cleanedData.username = user.username;
        }
      }
    }
    
    console.log(`正在发送PUT请求到: /api/auth/users/${userId}/`);
    console.log('发送的数据:', JSON.stringify(cleanedData));
    
    try {
      const response = await request.put(`/api/auth/users/${userId}/`, cleanedData);
      
      return {
        success: true,
        message: '个人信息更新成功',
        data: response.data || response
      };
    } catch (error) {
      console.error('API请求失败:', error);
      
      let errorMessage = '更新用户信息失败，请稍后重试';
      let errorFields = null;
      
      if (error.response) {
        console.error('状态码:', error.response.status);
        console.error('响应数据:', error.response.data);
        
        if (error.response.data) {
          if (typeof error.response.data === 'string') {
            errorMessage = error.response.data;
          } else if (error.response.data.message) {
            errorMessage = error.response.data.message;
          } else if (error.response.data.detail) {
            errorMessage = error.response.data.detail;
          } else if (error.response.data.error) {
            errorMessage = error.response.data.error;
          } else {
            errorFields = {};
            let hasFields = false;
            
            Object.entries(error.response.data).forEach(([field, messages]) => {
              if (Array.isArray(messages) && messages.length > 0) {
                errorFields[field] = messages;
                hasFields = true;
                
                if (field === 'username' && messages.includes('用户名已存在')) {
                  errorMessage = '该用户名已被使用，请选择其他用户名';
                } else if (field === 'email' && messages.includes('邮箱已存在')) {
                  errorMessage = '该邮箱已被注册，请使用其他邮箱';
                }
              }
            });
            
            if (hasFields) {
              const fieldErrors = Object.entries(errorFields)
                .map(([field, msgs]) => `${field}: ${msgs.join(', ')}`)
                .join('; ');
              
              if (fieldErrors) {
                errorMessage = fieldErrors;
              }
            }
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      return {
        success: false,
        message: errorMessage,
        fields: errorFields,
        error: error
      };
    }
  },

  /**
   * 更新用户头像
   * @param {FormData} formData - 包含头像文件的表单数据
   */
  async updateUserAvatar(formData) {
    const userId = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).id : null;
    if (!userId) {
      throw new Error('用户未登录');
    }
    const response = await request.post(`/api/auth/users/${userId}/avatar/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response;
  },

  /**
   * 修改用户密码
   * @param {Object} passwordData - 包含旧密码和新密码的对象
   */
  async changePassword(passwordData) {
    const { old_password, new_password, confirm_password } = passwordData;
    
    // 使用后端实际期望的字段名
    const requestData = {
      old_password,
      new_password,
      confirm_password  // 确认密码需与新密码相同
    };
    
    console.log('发送密码修改请求');
    
    try {
      const response = await request.put('/api/auth/users/change_password/', requestData);
      console.log('密码修改成功');
      return {
        success: true,
        message: '密码修改成功',
        data: response
      };
    } catch (error) {
      // 检查是否是预期的密码验证结果
      if (error.isValidationResult) {
        console.log('密码验证：当前密码不正确');
        return {
          success: false,
          message: '',
          fieldErrors: error.fieldErrors || error.data
        };
      }
      
      // 正常错误处理
      console.error('密码修改失败');
      
      // 详细记录错误信息
      if (error.response) {
        console.error('错误状态码:', error.response.status);
        
        const data = error.response.data;
        
        // 检查是否包含成功消息
        if (data && data.message && (
            data.message.toLowerCase().includes('success') || 
            data.message.toLowerCase().includes('successfully')
          )) {
          console.log('实际上密码修改成功了，返回成功消息');
          return {
            success: true,
            message: '密码修改成功',
            data: data
          };
        }
        
        // 检查是否是当前密码不正确的错误
        const isOldPasswordError = data && 
          data.old_password && 
          Array.isArray(data.old_password) && 
          data.old_password.includes("Incorrect password.");
        
        // 提取详细错误信息
        let errorMessage = '密码修改失败，请检查您输入的当前密码是否正确';
        
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data) {
          if (data.message) {
            errorMessage = data.message;
          } else if (data.detail) {
            errorMessage = data.detail;
          } else if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
            errorMessage = data.non_field_errors.join(', ');
          } else if (data.old_password && Array.isArray(data.old_password)) {
            // 翻译常见的密码错误消息
            if (data.old_password.includes("Incorrect password.")) {
              errorMessage = "当前密码不正确，请重新输入";
            } else {
              errorMessage = `当前密码: ${data.old_password.join(', ')}`;
            }
          } else if (data.new_password && Array.isArray(data.new_password)) {
            // 翻译常见的新密码错误消息
            const newPasswordErrors = data.new_password.map(err => {
              if (err.includes("too short")) return "新密码太短";
              if (err.includes("too common")) return "新密码太简单";
              if (err.includes("entirely numeric")) return "新密码不能全为数字";
              if (err.includes("similar to")) return "新密码与用户信息过于相似";
              return err;
            });
            errorMessage = `新密码问题: ${newPasswordErrors.join(', ')}`;
          } else {
            // 尝试提取错误字段信息
            const errorDetails = [];
            try {
              Object.entries(data).forEach(([field, messages]) => {
                // 字段名称翻译
                let fieldName = field;
                if (field === 'old_password') fieldName = '当前密码';
                if (field === 'new_password') fieldName = '新密码';
                if (field === 'confirm_password') fieldName = '确认密码';
                
                if (Array.isArray(messages) && messages.length > 0) {
                  errorDetails.push(`${fieldName}: ${messages.join(', ')}`);
                } else if (typeof messages === 'string') {
                  errorDetails.push(`${fieldName}: ${messages}`);
                } else if (messages !== null && typeof messages === 'object') {
                  errorDetails.push(`${fieldName}: ${JSON.stringify(messages)}`);
                }
              });
            } catch (e) {
              console.error('解析错误字段时出错:', e);
            }
            
            if (errorDetails.length > 0) {
              errorMessage = errorDetails.join('; ');
            }
          }
        }
        
        return {
          success: false,
          message: isOldPasswordError ? '' : errorMessage, // 当密码错误时不设置通用错误消息
          fieldErrors: data  // 返回原始字段错误，便于界面处理
        };
      }
      
      return {
        success: false,
        message: error.message || '密码修改失败，请重试'
      };
    }
  },

  /**
   * 获取公司的所有用户列表
   * @param {number} companyId - 公司ID
   * @returns {Promise} 包含用户列表的Promise
   */
  async getCompanyUsers(companyId) {
    try {
      if (!companyId) {
        // 如果没有传入公司ID，尝试从用户信息中获取
        const userJson = localStorage.getItem('user');
        if (userJson) {
          const user = JSON.parse(userJson);
          companyId = user.company;
        }
        
        // 如果仍然没有公司ID，返回错误
        if (!companyId) {
          return {
            success: false,
            message: '缺少公司ID，无法获取用户列表'
          };
        }
      }
      
      const response = await request.get(`/api/auth/companies/${companyId}/users/`);
      
      let users = [];
      if (Array.isArray(response.data)) {
        users = response.data;
      } else if (response.data && Array.isArray(response.data.data)) {
        users = response.data.data;
      } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
        users = response.data.results;
      }
      
      return {
        success: true,
        data: users
      };
    } catch (error) {
      console.error('获取公司用户列表失败:', error);
      return {
        success: false,
        message: error.message || '获取用户列表失败',
        error: error
      };
    }
  }
};

export default userApi; 
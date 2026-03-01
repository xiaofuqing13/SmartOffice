<template>
  <div class="profile-container">
    <el-alert
      v-if="alert.show"
      :type="alert.type"
      :title="alert.message"
      :closable="true"
      show-icon
      @close="closeAlert"
      class="profile-alert"
    />
    
    <div class="profile-content">
      <!-- 移动标签页到上方 -->
      <div class="profile-tabs-container">
        <el-tabs v-model="activeTab" class="profile-tabs">
          <el-tab-pane label="基本信息" name="basic"></el-tab-pane>
          <el-tab-pane label="账户安全" name="security"></el-tab-pane>
        </el-tabs>
      </div>
      
      <!-- 左侧个人信息区域 -->
      <div class="profile-left">
        <div class="avatar-container">
          <div class="avatar-wrapper" @click="triggerFileInput">
            <el-avatar :size="120" :src="avatarUrl" class="user-avatar">
              <span>{{ userInitial }}</span>
            </el-avatar>
            <div class="avatar-edit-overlay">
              <el-icon><Edit /></el-icon>
            </div>
          </div>
          <input 
            type="file" 
            ref="avatarInput" 
            accept="image/*" 
            style="display: none;"
            @change="handleAvatarChange"
          />
        </div>
        <h3 class="user-name">{{ userData.name || userData.username }}</h3>
        <p class="user-title">{{ userTitle }}</p>
      </div>
      
      <!-- 右侧内容区域 -->
      <div class="profile-right">
        <!-- 根据当前标签页显示对应内容 -->
        <div v-if="activeTab === 'basic'">
          <el-form 
            ref="profileForm" 
            :model="userData" 
            :rules="rules" 
            label-width="100px"
            v-loading="loading"
            class="profile-form"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="姓名" prop="name">
                  <el-input v-model="userData.name" placeholder="请输入姓名">
                    <template #prefix>
                      <el-icon><User /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="工号" prop="employee_id">
                  <el-input v-model="userData.employee_id" placeholder="公司内员工序号" :disabled="true">
                    <template #prefix>
                      <el-icon><Ticket /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
            
            <!-- 添加隐藏的用户名字段，确保表单提交时包含 -->
            <input type="hidden" v-model="userData.username" />
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="部门" prop="department">
                  <el-input v-model="userData.department_name" placeholder="用户所在部门" :disabled="true">
                    <template #prefix>
                      <el-icon><OfficeBuilding /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="职位" prop="position">
                  <el-input v-model="userData.position" placeholder="用户当前职位" :disabled="true">
                    <template #prefix>
                      <el-icon><Briefcase /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="电子邮箱" prop="email">
                  <el-input v-model="userData.email" placeholder="请输入电子邮箱">
                    <template #prefix>
                      <el-icon><Message /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="手机号码" prop="phone">
                  <el-input v-model="userData.phone" placeholder="请输入手机号码">
                    <template #prefix>
                      <el-icon><Phone /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="办公地点" prop="office">
                  <el-input v-model="userData.company_address" placeholder="公司地址" :disabled="true">
                    <template #prefix>
                      <el-icon><Location /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="直系领导" prop="manager">
                  <el-input v-model="userData.department_manager_name" placeholder="部门主管" :disabled="true">
                    <template #prefix>
                      <el-icon><UserFilled /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="个人简介" prop="bio">
              <el-input
                v-model="userData.bio"
                type="textarea"
                :rows="3"
                placeholder="请输入您的个人简介"
              />
            </el-form-item>
            
            <el-form-item class="form-actions">
              <el-button type="primary" @click="submitForm">
                <el-icon><Check /></el-icon>
                <span>保存更改</span>
              </el-button>
              <el-button @click="resetForm">
                <el-icon><Refresh /></el-icon>
                <span>重置</span>
              </el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <div v-if="activeTab === 'security'">
          <div class="security-section">
            <div class="security-header">
              <h4><el-icon><Lock /></el-icon> 密码管理</h4>
              <p class="security-tip">定期更改密码可以提高账户安全性</p>
            </div>
            <el-divider />
            
            <el-form 
              ref="passwordForm" 
              :model="passwordData" 
              :rules="passwordRules" 
              label-width="120px"
              v-loading="passwordLoading"
              :status-icon="true"
              class="password-form"
            >
              <el-form-item 
                label="当前密码" 
                prop="old_password"
                :error="fieldErrors.old_password"
                :class="{'has-error': fieldErrors.old_password}"
              >
                <el-input 
                  v-model="passwordData.old_password" 
                  type="password" 
                  placeholder="请输入当前密码"
                  show-password
                  @focus="clearFieldError('old_password')"
                >
                  <template #prefix>
                    <el-icon><Key /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item 
                label="新密码" 
                prop="new_password"
                :error="fieldErrors.new_password"
                :class="{'has-error': fieldErrors.new_password}"
              >
                <el-input 
                  v-model="passwordData.new_password" 
                  type="password" 
                  placeholder="请输入新密码"
                  show-password
                  @focus="clearFieldError('new_password')"
                >
                  <template #prefix>
                    <el-icon><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item 
                label="确认新密码" 
                prop="confirm_password"
                :error="fieldErrors.confirm_password"
                :class="{'has-error': fieldErrors.confirm_password}"
              >
                <el-input 
                  v-model="passwordData.confirm_password" 
                  type="password" 
                  placeholder="请再次输入新密码"
                  show-password
                  @focus="clearFieldError('confirm_password')"
                >
                  <template #prefix>
                    <el-icon><Check /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item class="form-actions">
                <el-button type="primary" @click="changePassword">
                  <el-icon><Key /></el-icon>
                  <span>修改密码</span>
                </el-button>
                <el-button @click="resetPasswordForm">
                  <el-icon><Refresh /></el-icon>
                  <span>重置</span>
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, reactive, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { 
  Edit, 
  User, 
  Ticket, 
  OfficeBuilding, 
  Briefcase, 
  Message, 
  Phone, 
  Location, 
  UserFilled, 
  Lock, 
  Key, 
  Check, 
  Refresh
} from '@element-plus/icons-vue'

export default {
  name: 'ProfileCard',
  components: {
    Edit,
    User,
    Ticket,
    OfficeBuilding,
    Briefcase,
    Message,
    Phone,
    Location,
    UserFilled,
    Lock,
    Key,
    Check,
    Refresh
  },
  setup() {
    const store = useStore()
    const profileForm = ref(null)
    const passwordForm = ref(null)
    const avatarInput = ref(null)
    const loading = ref(false)
    const passwordLoading = ref(false)
    const activeTab = ref('basic')
    
    const alert = reactive({
      show: false,
      type: 'success',
      message: ''
    })
    
    // 用户数据
    const userData = reactive({
      id: '',
      username: '',
      name: '',
      email: '',
      phone: '',
      avatar: '',
      position: '',
      department: '',
      company_name: '',
      department_manager_name: '',
      office: '',
      employee_id: '',
      manager: '',
      bio: '',
      join_date: '', // 添加入职日期字段
      department_name: '', // 添加部门名称字段
      company_address: '' // 添加公司地址字段
    })
    
    // 密码相关数据
    const passwordData = reactive({
      old_password: '',
      new_password: '',
      confirm_password: ''
    })
    
    // 字段错误信息
    const fieldErrors = reactive({
      old_password: '',
      new_password: '',
      confirm_password: ''
    })
    
    // 清除指定字段的错误信息
    const clearFieldError = (field) => {
      if (fieldErrors[field]) {
        fieldErrors[field] = ''
      }
    }
    
    // 清除所有字段错误
    const clearAllFieldErrors = () => {
      Object.keys(fieldErrors).forEach(key => {
        fieldErrors[key] = ''
      })
    }
    
    // 表单验证规则
    const rules = {
      username: [
        { required: true, message: '用户名不能为空', trigger: 'blur' },
        { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
      ],
      name: [
        { required: true, message: '请输入姓名', trigger: 'blur' },
        { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入电子邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的电子邮箱格式', trigger: 'blur' }
      ],
      phone: [
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
      ]
    }
    
    // 密码验证规则
    const passwordRules = {
      old_password: [
        { required: true, message: '请输入当前密码', trigger: 'blur' }
      ],
      new_password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
      ],
      confirm_password: [
        { required: true, message: '请再次输入新密码', trigger: 'blur' },
        { 
          validator: (rule, value, callback) => {
            if (value !== passwordData.new_password) {
              callback(new Error('两次输入密码不一致'))
            } else {
              callback()
            }
          }, 
          trigger: 'blur' 
        }
      ]
    }
    
    // 计算属性：用户头像
    const avatarUrl = computed(() => {
      return userData.avatar || ''
    })
    
    // 计算属性：用户名首字母（用于没有头像时显示）
    const userInitial = computed(() => {
      if (userData.name) {
        return userData.name.charAt(0)
      } else if (userData.username) {
        return userData.username.charAt(0)
      }
      return '用'
    })
    
    // 计算属性：用户职位和部门
    const userTitle = computed(() => {
      const parts = []
      if (userData.department_name) parts.push(userData.department_name)
      if (userData.position) parts.push(userData.position)
      return parts.join(' / ') || '暂无职位信息'
    })
    
    // 获取用户数据
    const getUserData = async () => {
      loading.value = true
      try {
        // 首先从本地存储获取基本信息
        const storedUser = store.getters['user/currentUser']
        console.log('本地存储的用户数据:', storedUser)
        
        if (storedUser) {
          // 确保username字段被设置
          if (storedUser.username) {
            userData.username = storedUser.username
          }
          
          Object.keys(userData).forEach(key => {
            if (storedUser[key]) {
              userData[key] = storedUser[key]
            }
          })
        }
        
        // 如果没有用户名，尝试从localStorage获取
        if (!userData.username) {
          const userJson = localStorage.getItem('user')
          if (userJson) {
            try {
              const localUser = JSON.parse(userJson)
              if (localUser && localUser.username) {
                userData.username = localUser.username
              }
            } catch (e) {
              console.error('解析本地存储的用户数据失败:', e)
            }
          }
        }
        
        // 然后从服务器获取完整信息
        console.log('正在从服务器请求用户数据...')
        await store.dispatch('user/getUserProfile')
        const fullUser = store.getters['user/currentUser']
        console.log('从服务器获取的用户数据:', fullUser)
        
        if (fullUser) {
          // 确保username字段被保留
          const currentUsername = userData.username
          
          Object.keys(userData).forEach(key => {
            if (fullUser[key] !== undefined) {
              userData[key] = fullUser[key]
            }
          })
          
          // 如果服务器返回的数据中没有username，但我们已经有了username，则保留它
          if (!userData.username && currentUsername) {
            userData.username = currentUsername
          }
          
          // 如果没有入职日期，设置为当前日期
          if (!userData.join_date) {
            userData.join_date = new Date().toISOString().split('T')[0]
          }
        }
        
        console.log('最终用户数据:', userData)
      } catch (error) {
        showAlert('获取用户信息失败，请刷新重试', 'error')
        console.error('获取用户信息失败:', error)
        // 记录更详细的错误信息
        if (error.response) {
          console.error('响应状态:', error.response.status)
          console.error('响应数据:', error.response.data)
        }
      } finally {
        loading.value = false
      }
    }
    
    // 提交表单
    const submitForm = async () => {
      if (!profileForm.value) return
      
      await profileForm.value.validate(async (valid) => {
        if (valid) {
          loading.value = true
          try {
            // 确保用户ID存在
            if (!userData.id) {
              const storedUser = store.getters['user/currentUser'];
              if (storedUser && storedUser.id) {
                userData.id = storedUser.id;
              }
            }
            
            // 记录发送的数据以便调试
            console.log('正在发送用户数据:', JSON.stringify(userData));
            
            const response = await store.dispatch('user/updateUserProfile', userData)
            if (response.success) {
              showAlert('个人信息更新成功', 'success')
            } else {
              showAlert(response.message || '更新失败，请重试', 'error')
            }
          } catch (error) {
            // 改进错误处理，确保显示具体错误信息
            console.error('更新用户信息失败:', error);
            let errorMessage = '更新失败，请重试';
            
            // 检查不同的错误对象格式
            if (typeof error === 'string') {
              errorMessage = error;
            } else if (error && typeof error === 'object') {
              if (error.message) {
                errorMessage = error.message;
              }
              
              // 检查是否是Vuex返回的自定义错误对象格式
              if (error.response && typeof error.response === 'object') {
                console.log('自定义错误响应对象:', error.response);
                
                if (error.response.message) {
                  errorMessage = error.response.message;
                } else if (error.response.data) {
                  if (typeof error.response.data === 'string') {
                    errorMessage = error.response.data;
                  } else if (error.response.data.message) {
                    errorMessage = error.response.data.message;
                  } else if (error.response.data.error) {
                    errorMessage = error.response.data.error;
                  } else if (error.response.data.detail) {
                    errorMessage = error.response.data.detail;
                  }
                }
              } 
              // 标准Axios错误对象
              else if (error.response && error.response.status) {
                console.error('响应状态:', error.response.status);
                
                if (error.response.data) {
                  console.error('响应数据:', error.response.data);
                  
                  if (typeof error.response.data === 'string') {
                    errorMessage = error.response.data;
                  } else if (error.response.data.message) {
                    errorMessage = error.response.data.message;
                  } else if (error.response.data.error) {
                    errorMessage = error.response.data.error;
                  } else if (error.response.data.detail) {
                    errorMessage = error.response.data.detail;
                  } else {
                    // 尝试提取错误字段
                    const errorFields = Object.entries(error.response.data || {})
                      .filter(([, value]) => Array.isArray(value) && value.length > 0)
                      .map(([field, messages]) => `${field}: ${messages.join(', ')}`);
                    
                    if (errorFields.length > 0) {
                      errorMessage = errorFields.join('; ');
                    }
                  }
                }
              }
            }
            
            showAlert(errorMessage, 'error');
          } finally {
            loading.value = false
          }
        } else {
          return false
        }
      })
    }
    
    // 重置表单
    const resetForm = () => {
      profileForm.value?.clearValidate();
      getUserData();
    }
    
    // 修改密码
    const changePassword = async () => {
      if (!passwordForm.value) return
      
      // 清除之前的字段错误
      clearAllFieldErrors()
      
      await passwordForm.value.validate(async (valid) => {
        if (valid) {
          passwordLoading.value = true
          try {
            const { old_password, new_password, confirm_password } = passwordData
            console.log('发送密码修改请求')
            
            const response = await store.dispatch('user/changePassword', { 
              old_password, 
              new_password,
              confirm_password
            })
            
            if (response.success) {
              showAlert('密码修改成功', 'success')
              resetPasswordForm()
            } else {
              // 简化错误日志记录
              if (response.isValidationResult) {
                console.log('验证结果：当前密码不正确')
              } else {
                console.log('密码修改失败')
              }

              // 检查是否为当前密码不正确的错误
              let isOldPasswordError = false;
              
              if (response && response.fieldErrors && 
                  response.fieldErrors.old_password && 
                  Array.isArray(response.fieldErrors.old_password) && 
                  response.fieldErrors.old_password.includes('Incorrect password.')) {
                isOldPasswordError = true;
              }

              let alertMessage = '密码修改失败，请重试';
              if (response && response.message) {
                alertMessage = response.message; // response.message 来自 userApi.js，已经是友好的中文提示
              }

              // 使用从 userApi.js 传递过来的 fieldErrors 更新组件的响应式 fieldErrors
              if (response && response.fieldErrors) {
                Object.entries(response.fieldErrors).forEach(([fieldKey, errorsArray]) => {
                  if (Object.prototype.hasOwnProperty.call(fieldErrors, fieldKey) && Array.isArray(errorsArray) && errorsArray.length > 0) {
                    let specificMessage = errorsArray.join(', '); // 默认错误信息

                    // 特别处理旧密码不正确的错误
                    if (fieldKey === 'old_password' && errorsArray.includes('Incorrect password.')) {
                      specificMessage = '当前密码不正确，请重新输入';
                      isOldPasswordError = true;
                      
                      // 添加抖动动画
                      const inputEl = document.querySelector(`.password-form .el-form-item[prop="${fieldKey}"] .el-input__wrapper`);
                      if (inputEl) {
                        inputEl.classList.add('shake-error');
                        setTimeout(() => { inputEl.classList.remove('shake-error'); }, 600);
                      }
                    }
                    // (可以为其他字段添加类似的特定错误处理和翻译)

                    fieldErrors[fieldKey] = specificMessage; // 更新响应式 fieldErrors，触发UI更新
                  }
                });
              }
              
              // 仅当错误不是"当前密码不正确"时才显示通用错误提示
              if (!isOldPasswordError) {
                showAlert(alertMessage, 'error', 5000)
              }
            }
          } catch (error) {
            // 简化错误日志记录
            if (error.isValidationResult) {
              console.log('验证结果：当前密码不正确')
            } else {
              console.log('密码修改失败')
            }

            // 检查是否为当前密码不正确的错误
            let isOldPasswordError = false;
            
            if (error && error.fieldErrors && 
                error.fieldErrors.old_password && 
                Array.isArray(error.fieldErrors.old_password) && 
                error.fieldErrors.old_password.includes('Incorrect password.')) {
              isOldPasswordError = true;
            }

            let alertMessage = '密码修改失败，请重试';
            if (error && error.message) {
              alertMessage = error.message; // error.message 来自 userApi.js，已经是友好的中文提示
            }

            // 使用从 userApi.js 传递过来的 fieldErrors 更新组件的响应式 fieldErrors
            if (error && error.fieldErrors) {
              Object.entries(error.fieldErrors).forEach(([fieldKey, errorsArray]) => {
                if (Object.prototype.hasOwnProperty.call(fieldErrors, fieldKey) && Array.isArray(errorsArray) && errorsArray.length > 0) {
                  let specificMessage = errorsArray.join(', '); // 默认错误信息

                  // 特别处理旧密码不正确的错误
                  if (fieldKey === 'old_password' && errorsArray.includes('Incorrect password.')) {
                    specificMessage = '当前密码不正确，请重新输入';
                    isOldPasswordError = true;
                    
                    // 添加抖动动画
                    const inputEl = document.querySelector(`.password-form .el-form-item[prop="${fieldKey}"] .el-input__wrapper`);
                    if (inputEl) {
                      inputEl.classList.add('shake-error');
                      setTimeout(() => { inputEl.classList.remove('shake-error'); }, 600);
                    }
                  }
                  // (可以为其他字段添加类似的特定错误处理和翻译)

                  fieldErrors[fieldKey] = specificMessage; // 更新响应式 fieldErrors，触发UI更新
                }
              });
            }
            
            // 仅当错误不是"当前密码不正确"时才显示通用错误提示
            if (!isOldPasswordError) {
              showAlert(alertMessage, 'error', 5000);
            }
          } finally {
            passwordLoading.value = false;
          }
        } else {
          // 表单验证失败，Element Plus 会自动显示验证错误
          console.log('密码表单验证未通过');
          return false;
        }
      });
    }
    
    // 重置密码表单
    const resetPasswordForm = () => {
      passwordForm.value?.resetFields()
      clearAllFieldErrors()
    }
    
    // 触发文件上传
    const triggerFileInput = () => {
      avatarInput.value.click()
    }
    
    // 处理头像变更
    const handleAvatarChange = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        ElMessage.error('请选择图片文件')
        return
      }
      
      // 验证文件大小（最大3MB）
      if (file.size > 3 * 1024 * 1024) {
        ElMessage.error('图片大小不能超过3MB')
        return
      }
      
      // 创建FormData对象
      const formData = new FormData()
      formData.append('avatar', file)
      
      loading.value = true
      try {
        const response = await store.dispatch('user/updateUserAvatar', formData)
        if (response.success) {
          showAlert('头像更新成功', 'success')
          userData.avatar = response.data.avatar
        } else {
          showAlert(response.message || '头像更新失败，请重试', 'error')
        }
      } catch (error) {
        showAlert(error.message || '头像更新失败，请重试', 'error')
        console.error('更新头像失败:', error)
      } finally {
        loading.value = false
        // 重置文件输入，允许重新选择同一个文件
        event.target.value = ''
      }
    }
    
    // 显示提示信息
    const showAlert = (message, type = 'success', duration = 3000) => {
      alert.show = true
      alert.type = type
      alert.message = message
      
      // 3秒后自动关闭
      setTimeout(() => {
        closeAlert()
      }, duration)
    }
    
    // 关闭提示信息
    const closeAlert = () => {
      alert.show = false
    }
    
    // 组件挂载时获取用户数据
    onMounted(() => {
      getUserData()
    })
    
    return {
      profileForm,
      passwordForm,
      avatarInput,
      userData,
      passwordData,
      loading,
      passwordLoading,
      activeTab,
      alert,
      rules,
      passwordRules,
      avatarUrl,
      userInitial,
      userTitle,
      submitForm,
      resetForm,
      changePassword,
      resetPasswordForm,
      triggerFileInput,
      handleAvatarChange,
      showAlert,
      closeAlert,
      fieldErrors,
      clearFieldError,
      clearAllFieldErrors
    }
  }
}
</script>

<style lang="scss" scoped>
.profile-container {
  padding: 10px;
}

.profile-alert {
  margin-bottom: 20px;
}

/* 添加标签页容器样式 */
.profile-tabs-container {
  width: 100%;
  margin-bottom: 20px;
}

.profile-content {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  margin-top: 20px;
}

.profile-left {
  flex: 0 0 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: var(--bg-color-secondary) !important;
  border-radius: 8px;
  padding: 30px 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.profile-right {
  flex: 1;
}

.avatar-container {
  margin-bottom: 20px;
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  display: inline-block;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
  
  &:hover {
    transform: scale(1.03);
    
    .avatar-edit-overlay {
      opacity: 1;
    }
  }
}

.user-avatar {
  background-color: var(--el-color-primary);
  color: white;
  font-size: 48px;
  font-weight: bold;
}

.avatar-edit-overlay {
  position: absolute;
  bottom: 0;
  right: 0;
  background-color: var(--el-color-primary);
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  opacity: 0.8;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  margin: 15px 0 5px;
  color: var(--el-text-color-primary);
}

.user-title {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0 0 20px 0;
  text-align: center;
}

.profile-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 25px;
  }
  
  :deep(.el-tabs__item) {
    font-size: 16px;
    padding: 0 20px;
    height: 50px;
    line-height: 50px;
    
    &.is-active {
      font-weight: 600;
    }
  }
}

.profile-form {
  padding: 10px;
  
  :deep(.el-form-item__label) {
    font-weight: 500;
  }
  
  :deep(.el-input__wrapper) {
    transition: all 0.3s;
    
    &:hover {
      box-shadow: 0 0 0 1px var(--el-color-primary-light-5) inset;
    }
    
    &:focus-within {
      box-shadow: 0 0 0 1px var(--el-color-primary) inset;
    }
  }
  
  :deep(.el-input__prefix) {
    color: var(--el-text-color-secondary);
  }
}

.form-actions {
  margin-top: 30px;
  display: flex;
  justify-content: flex-start;
  gap: 15px;
}

.security-section {
  padding: 10px;
  
  .security-header {
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
    
    h4 {
      font-size: 18px;
      font-weight: 500;
      margin: 0 0 5px 0;
      display: flex;
      align-items: center;
      
      .el-icon {
        margin-right: 10px;
        color: var(--el-color-primary);
      }
    }
  }
  
  .security-tip {
    color: var(--el-text-color-secondary);
    font-size: 14px;
    margin: 0 0 0 30px;
  }
}

.password-form {
  max-width: 600px;
  margin-top: 20px;
}

/* 高亮错误字段 */
.has-error :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-color-danger) inset !important;
  background-color: rgba(245, 108, 108, 0.05);
}

/* 密码错误抖动动画 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

:deep(.shake-error) {
  animation: shake 0.6s ease-in-out;
  box-shadow: 0 0 0 1px var(--el-color-danger) inset !important;
  background-color: rgba(245, 108, 108, 0.1) !important;
}

/* 响应式布局 */
@media (max-width: 992px) {
  .profile-content {
    flex-direction: column;
  }
  
  .profile-left {
    flex: none;
    margin-bottom: 30px;
    width: 100%;
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .profile-form {
    :deep(.el-form-item__label) {
      float: none;
      display: block;
      text-align: left;
      padding: 0 0 10px;
    }
  }
}
</style> 
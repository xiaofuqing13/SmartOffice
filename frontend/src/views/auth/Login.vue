<template>
  <div class="login-container">
    <div class="main-container">
      <!-- 左侧区域 -->
      <div class="left-section">
        <div class="animation-container" id="lottieAnimation"></div>
        <div class="left-content">
          <h2>欢迎回来</h2>
          <p>登录智行舟系统，开始您的高效工作</p>
        </div>
      </div>
      
      <!-- 右侧登录表单 -->
      <div class="login-box">
        <div class="login-header">
          <i class="bi bi-briefcase"></i>
          <h4>智行舟系统</h4>
          <p>专业高效的一站式企业办公解决方案</p>
        </div>

        <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
          <el-form-item prop="username">
            <el-input 
              v-model="loginForm.username" 
              placeholder="请输入账号或邮箱" 
              autocomplete="off"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password" 
              type="password" 
              placeholder="请输入密码" 
              show-password
              autocomplete="off"
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <div class="login-options">
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
            <div>
              <a href="/admin/login/" class="admin-link">进入管理员端</a>
            </div>
          </div>
          
          <el-button type="primary" class="login-button" :loading="loading" @click="handleLogin">
            登录
          </el-button>
        </el-form>

        <div class="login-footer">
          <p>还没有账号？<router-link to="/register">立即注册</router-link></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const store = useStore()
    const loginFormRef = ref(null)
    
    // 从Vuex获取加载状态和错误信息
    const loading = computed(() => store.getters['user/loading'])
    const error = computed(() => store.getters['user/error'])
    
    // 登录表单数据
    const loginForm = reactive({
      username: '',
      password: '',
      remember: false
    })
    
    // 登录表单验证规则
    const loginRules = {
      username: [
        { required: true, message: '请输入账号或邮箱', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }
    
    // 处理登录
    const handleLogin = async () => {
      if (!loginFormRef.value) return;
      
      // 清除之前的错误
      store.dispatch('user/clearError');
      
      try {
        // 表单验证
        await loginFormRef.value.validate();
      } catch (error) {
        ElMessage.warning('请填写完整的登录信息');
        return;
      }
      
      try {
        // 登录数据
        const loginData = {
          username: loginForm.username,
          password: loginForm.password,
          remember: loginForm.remember ? 'true' : 'false'  // API要求是字符串
        };
        
        // 调用登录API
        const response = await store.dispatch('user/login', loginData);
        ElMessage.success(response.message || '登录成功');
        router.push('/dashboard'); // 登录成功后跳转到工作台
      } catch (err) {
        // 使用Vuex中的错误信息或从错误对象获取信息
        if (error.value) {
          ElMessage.error(error.value);
        } else if (err.response && err.response.data && err.response.data.message) {
          ElMessage.error(err.response.data.message);
        } else {
          ElMessage.error(err.message || '登录失败，请稍后重试');
        }
      }
    }
    
    // 组件挂载后加载动画
    onMounted(() => {
      // 确保重置loading状态
      store.commit('user/AUTH_REQUEST', false);
      
      const animContainer = document.getElementById('lottieAnimation');
      if (animContainer && window.lottie) {
        window.lottie.loadAnimation({
          container: animContainer,
          renderer: 'svg',
          loop: true,
          autoplay: true,
          path: 'https://assets10.lottiefiles.com/packages/lf20_iorpbol0.json' // 登录主题动画
        });
      }
    });
    
    return {
      loginFormRef,
      loginForm,
      loginRules,
      loading,
      handleLogin,
      User,
      Lock
    }
  }
}
</script>

<style scoped>
.login-container {
  font-family: 'Microsoft YaHei', sans-serif;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #88a0f8 0%, #7089f7 100%);
  margin: 0;
  padding: 0;
  
  /* 覆盖深色模式变量，强制使用浅色模式 */
  --bg-color: #ffffff;
  --bg-color-secondary: #f9fafb;
  --bg-color-tertiary: #f3f4f6;
  --text-color: #1f2937;
  --text-color-secondary: #4b5563;
  --text-color-tertiary: #6b7280;
  --border-color: #e5e7eb;
  --border-color-light: #f3f4f6;
  --shadow-color: rgba(0, 0, 0, 0.1);
  --hover-color: #f3f4f6;
  --active-color: #e5e7eb;
  
  /* 字体和内容密度相关设置 */
  --font-size-base: 16px;
  --font-size-sm: 14px;
  --font-size-lg: 18px;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 600;
  --line-height-base: 1.5;
  --spacing-base: 16px;
  --spacing-sm: 8px;
  --spacing-lg: 24px;
  --content-max-width: 1200px;
  --form-element-height: 40px;
  --border-radius: 8px;
}

.main-container {
  display: flex;
  width: 90%;
  max-width: 1200px;
  min-height: 600px;
  background: rgba(255, 255, 255, 0.20);
  border-radius: 24px;
  box-shadow: none;
  overflow: hidden;
  backdrop-filter: blur(16px) saturate(160%);
  border: none;
  position: relative;
  z-index: 1;
}

.left-section {
  flex: 1;
  background: linear-gradient(45deg, #4299e1 60%, #667eea 100%);
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.animation-container {
  width: 100%;
  height: 300px;
  margin-bottom: 30px;
}

.left-content {
  text-align: center;
  z-index: 1;
}

.left-content h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 20px;
  background: linear-gradient(90deg, #fff 20%, #a6c1ee 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.left-content p {
  font-size: 1.1rem;
  line-height: 1.6;
  opacity: 0.92;
  text-shadow: 0 2px 8px rgba(80,80,160,0.08);
}

.login-box {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 0;
  box-shadow: none;
  border: none;
  color: #333;
}

.login-header {
  margin-bottom: 2rem;
  text-align: center;
}

.login-header i {
  font-size: 2.5rem;
  background: linear-gradient(45deg, #007bff, #6610f2);
  -webkit-background-clip: text;
  color: transparent;
  margin-bottom: 20px;
  display: inline-block;
}

.login-header h4 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  margin: 0.5rem 0;
  color: #333;
}

.login-header p {
  font-size: var(--font-size-base);
  color: #666;
  margin-bottom: 0;
}

.login-form {
  margin-bottom: 20px;
}

.login-form :deep(.el-input__wrapper) {
  background-color: white; 
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

.login-form :deep(.el-input__inner) {
  color: #333;
}

.login-form :deep(.el-checkbox__label) {
  color: #606266;
}

.login-form :deep(.el-button--primary) {
  background-color: #409EFF;
  color: white;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  font-size: 14px;
}

.forgot-link, .admin-link {
  color: var(--el-color-primary);
  text-decoration: none;
  transition: color 0.3s;
}

.admin-link {
  margin-right: 16px;
}

.forgot-link:hover, .admin-link:hover {
  color: #a0cfff;
  text-decoration: underline;
}

.login-button {
  height: var(--form-element-height);
  border-radius: var(--border-radius);
  background: linear-gradient(90deg, #667eea 0%, #4361ee 100%);
  border: none;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.5px;
  margin-top: var(--spacing-sm);
  transition: all 0.2s cubic-bezier(.4,0,.2,1);
  position: relative;
  overflow: hidden;
}

.login-button:hover, .login-button:focus {
  transform: translateY(-2px) scale(1.03);
  background: linear-gradient(90deg, #4361ee 0%, #667eea 100%);
}

.login-button:active {
  transform: scale(0.97);
}

.login-footer {
  text-align: center;
  margin-top: var(--spacing-lg);
  font-size: var(--font-size-sm);
  color: #4a5568;
}

.login-footer a {
  color: #409EFF;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.login-footer a:hover {
  color: #2d3a8c;
}

@media (max-width: 992px) {
  .main-container {
    flex-direction: column;
    width: 95%;
    margin: 20px 0;
  }
  .left-section {
    padding: 30px;
    min-height: 300px;
  }
  .login-box {
    padding: 30px;
  }
  .left-content h2 {
    font-size: 2rem;
  }
}
</style> 
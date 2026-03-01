<template>
  <div class="register-page">
    <!-- 背景动画元素 -->
    <div class="bg-animation">
      <div class="bg-particle"></div>
      <div class="bg-particle"></div>
      <div class="bg-particle"></div>
      <div class="bg-particle"></div>
      <div class="bg-particle"></div>
    </div>
    
    <div class="main-container">
      <div class="left-section">
        <!-- 装饰元素 -->
        <div class="decoration">
          <div class="decoration-circle"></div>
          <div class="decoration-circle"></div>
          <div class="decoration-circle"></div>
        </div>
        
        <div class="animation-container" id="lottieAnimation"></div>
        <div class="left-content">
          <h2>欢迎加入我们</h2>
          <p>加入智行舟系统，提升工作效率，实现智能协作</p>
        </div>
      </div>
      
      <div class="register-container">
        <div class="register-header">
          <i class="bi bi-briefcase"></i>
          <h4>创建您的账户</h4>
          <p>开始您的智能办公之旅</p>
        </div>

        <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" class="register-form">
          <div class="mb-3">
            <label for="username" class="form-label">账号</label>
            <el-form-item prop="username">
              <el-input 
                v-model="registerForm.username" 
                placeholder="请输入您的账号 (例如：user123)"
                id="username"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>
          
          <div class="mb-3">
            <label for="email" class="form-label">邮箱</label>
            <el-form-item prop="email">
              <el-input 
                v-model="registerForm.email" 
                placeholder="请输入您的邮箱地址"
                id="email"
              >
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
              <div id="emailHelp" class="form-text">我们将发送验证邮件到此邮箱，也可用于密码找回。</div>
            </el-form-item>
          </div>

          <div class="mb-3">
            <label for="company" class="form-label">企业名称</label>
            <el-form-item prop="company">
              <el-select 
                v-model="registerForm.company" 
                placeholder="请选择您的企业"
                style="width: 100%"
                id="company"
              >
                <template #prefix>
                  <el-icon><OfficeBuilding /></el-icon>
                </template>
                <el-option
                  v-for="item in companies"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
              <div id="companyHelp" class="form-text">您所属的企业或组织名称，有助于系统为您提供更精准的服务。</div>
            </el-form-item>
          </div>

          <div class="mb-3">
            <label for="password" class="form-label">密码</label>
            <el-form-item prop="password">
              <el-input 
                v-model="registerForm.password" 
                type="password" 
                placeholder="请输入密码 (至少6位)"
                show-password
                id="password"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <div class="mb-3">
            <label for="confirmPassword" class="form-label">确认密码</label>
            <el-form-item prop="confirmPassword">
              <el-input 
                v-model="registerForm.confirmPassword" 
                type="password" 
                placeholder="请再次输入密码"
                show-password
                id="confirmPassword"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <el-button type="primary" class="btn btn-primary w-100" @click="handleRegister" :loading="loading">
            注册
          </el-button>
        </el-form>

        <div class="login-link">
          <p>已有账号? <router-link to="/login">立即登录</router-link></p>
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
import { User, Lock, Message, OfficeBuilding } from '@element-plus/icons-vue'
import { getSimpleCompanyList } from '@/api/company'

export default {
  name: 'Register',
  setup() {
    const router = useRouter();
    const store = useStore();
    const registerFormRef = ref(null);
    const loading = computed(() => store.getters['user/loading']);
    const error = computed(() => store.getters['user/error']);
    const companies = ref([]);

    // 注册表单数据
    const registerForm = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      company: null
    });

    // 注册表单验证规则
    const registerRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 4, message: '用户名长度至少4个字符', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      company: [
        { required: true, message: '请选择企业', trigger: 'change' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请确认密码', trigger: 'blur' },
        { 
          validator: (rule, value, callback) => {
            if (value !== registerForm.password) {
              callback(new Error('两次输入密码不一致'));
            } else {
              callback();
            }
          }, 
          trigger: 'blur' 
        }
      ]
    };

    // 获取企业列表
    const fetchCompanies = async () => {
      try {
        const response = await getSimpleCompanyList();
        console.log('获取企业列表响应:', response);
        
        if (response && response.data) {
          companies.value = response.data;
        } else if (response && response.success && Array.isArray(response)) {
          // 处理返回数据直接是数组的情况
          companies.value = response;
        } else {
          console.error('获取企业列表失败:', response);
          // 设置一个默认企业选项，防止注册页面出错
          companies.value = [
            { id: 1, name: '默认企业' }
          ];
          ElMessage.warning('获取企业列表失败，已设置默认选项');
        }
      } catch (error) {
        console.error('获取企业列表失败:', error);
        // 设置一个默认企业选项，防止注册页面出错
        companies.value = [
          { id: 1, name: '默认企业' }
        ];
        ElMessage.warning('获取企业列表失败，已设置默认选项');
      }
    };

    // 处理注册
    const handleRegister = async () => {
      if (!registerFormRef.value) return;
      
      // 清除之前的错误
      store.dispatch('user/clearError');
      
      try {
        // 表单验证
        await registerFormRef.value.validate();
      } catch (error) {
        ElMessage.warning('请填写所有必填项');
        return;
      }
      
      try {
        // 创建注册数据对象，添加必要的可选字段
        const registerData = {
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
          confirmPassword: registerForm.confirmPassword,
          company: registerForm.company,
          // 添加空值的可选字段，避免后端验证问题
          first_name: '',
          last_name: '',
          phone: ''
        };
        
        // 调用注册API
        const response = await store.dispatch('user/register', registerData);
        ElMessage.success(response.message || '注册成功！');
        
        // 注册成功后自动登录
        const loginData = {
          username: registerForm.username,
          password: registerForm.password
        };
        
        try {
          // 调用登录API
          await store.dispatch('user/login', loginData);
          ElMessage.success('自动登录成功！');
          
          // 登录成功后跳转到仪表板
          router.push('/dashboard');
        } catch (loginError) {
          console.error('自动登录失败:', loginError);
          ElMessage.warning('自动登录失败，请手动登录');
          router.push('/login');
        }
      } catch (err) {
        // 错误已在store中处理，这里可以显示额外提示
        if (error.value) {
          ElMessage.error(error.value);
        } else {
          console.error('注册失败:', err);
          ElMessage.error('注册失败，请稍后重试');
        }
      }
    };

    onMounted(() => {
      fetchCompanies();
      
      // 添加Lottie动画
      const animContainer = document.getElementById('lottieAnimation');
      if (animContainer && window.lottie) {
        window.lottie.loadAnimation({
          container: animContainer,
          renderer: 'svg',
          loop: true,
          autoplay: true,
          path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' // 办公主题动画
        });
      }
    });

    return {
      registerFormRef,
      registerForm,
      registerRules,
      loading,
      companies,
      handleRegister,
      User,
      Lock,
      Message,
      OfficeBuilding
    };
  }
}
</script>

<style scoped>
.register-page {
  font-family: 'Microsoft YaHei', sans-serif;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #8bc6ec 0%, #9599e2 100%);
  position: relative;
  overflow: hidden;
  
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
  min-height: 480px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  overflow: hidden;
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  box-shadow: 0 25px 45px rgba(0, 17, 51, 0.12);
  position: relative;
  z-index: 10;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.left-section {
  flex: 1;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  padding: 25px 30px;
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
  height: 180px;
  margin-bottom: 15px;
  position: relative;
  z-index: 1;
}

.left-content {
  text-align: center;
  z-index: 1;
  position: relative;
}

.left-content h2 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 10px;
  background: linear-gradient(90deg, #fff 10%, #e0e7ff 90%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.left-content p {
  font-size: 0.9rem;
  line-height: 1.4;
  opacity: 0.92;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  max-width: 85%;
  margin: 0 auto;
}

.register-container {
  flex: 1;
  max-width: 640px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 0 24px 24px 0;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.12);
  color: #333;
}

.register-header {
  margin-bottom: 2rem;
  text-align: center;
}

.register-header i {
  font-size: 2rem;
  background: linear-gradient(45deg, #2563eb, #3b82f6);
  -webkit-background-clip: text;
  color: transparent;
  margin-bottom: 10px;
  display: inline-block;
}

.register-header h4 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  margin: 0.5rem 0;
  color: #333;
}

.register-header p {
  font-size: var(--font-size-base);
  color: #666;
}

.mb-3 {
  margin-bottom: var(--spacing-base);
}

.form-label {
  color: #333;
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--spacing-sm);
}

.form-text {
  color: #666;
  font-size: var(--font-size-sm);
}

/* 修改注册表单组件样式 */
.register-form :deep(.el-input__wrapper) {
  background-color: white;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

.register-form :deep(.el-input__inner) {
  color: #333;
}

.register-form :deep(.el-select .el-input__wrapper) {
  background-color: white;
}

.register-form :deep(.el-select-dropdown) {
  background-color: white;
  border-color: #dcdfe6;
}

.register-form :deep(.el-select-dropdown__item) {
  color: #606266;
}

.register-form :deep(.el-select-dropdown__item.hover),
.register-form :deep(.el-select-dropdown__item:hover) {
  background-color: #f5f7fa;
}

.register-form :deep(.el-button--primary) {
  background-color: #409EFF;
  color: white;
}

.btn-primary {
  height: var(--form-element-height);
  border-radius: var(--border-radius);
  background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
  border: none;
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.5px;
  margin-top: var(--spacing-sm);
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(37, 99, 235, 0.2);
  position: relative;
  overflow: hidden;
}

.btn-primary:hover, .btn-primary:focus {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(37, 99, 235, 0.3);
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
}

.btn-primary:active {
  transform: translateY(0) scale(0.98);
}

.w-100 {
  width: 100% !important;
}

.login-link {
  text-align: center;
  margin-top: var(--spacing-base);
  font-size: var(--font-size-sm);
  color: #64748b;
}

.login-link a {
  color: #409EFF;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
  position: relative;
}

.login-link a:hover {
  color: #3b82f6;
}

.login-link a::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 2px;
  bottom: -2px;
  left: 0;
  background: linear-gradient(90deg, #2563eb, #3b82f6);
  transform: scaleX(0);
  transform-origin: bottom right;
  transition: transform 0.3s ease;
}

.login-link a:hover::after {
  transform: scaleX(1);
  transform-origin: bottom left;
}

/* 装饰元素 */
.decoration {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  pointer-events: none;
  opacity: 0.6;
  z-index: 0;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(3px);
}

.decoration-circle:nth-child(1) {
  width: 140px;
  height: 140px;
  top: 10%;
  left: 10%;
  animation: float-slow 8s ease-in-out infinite;
}

.decoration-circle:nth-child(2) {
  width: 80px;
  height: 80px;
  bottom: 15%;
  left: 20%;
  animation: float-slow 6s ease-in-out infinite 1s;
}

.decoration-circle:nth-child(3) {
  width: 110px;
  height: 110px;
  top: 60%;
  left: 40%;
  animation: float-slow 10s ease-in-out infinite 2s;
}

@keyframes float-slow {
  0% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(5deg); }
  100% { transform: translateY(0) rotate(0deg); }
}

@media (max-width: 992px) {
  .main-container {
    flex-direction: column;
    width: 95%;
    margin: 15px 0;
    min-height: auto;
  }
  
  .left-section {
    padding: 20px;
    min-height: 240px;
  }
  
  .register-container {
    padding: 20px;
  }
  
  .left-content h2 {
    font-size: 1.6rem;
  }
  
  .animation-container {
    height: 150px;
  }
}

/* 背景动画元素 */
.bg-animation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.bg-particle {
  position: absolute;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
  border-radius: 50%;
  animation: float-particle 15s infinite linear;
  backdrop-filter: blur(1px);
}

.bg-particle:nth-child(1) { width: 100px; height: 100px; left: 10%; top: 20%; animation-duration: 25s; }
.bg-particle:nth-child(2) { width: 180px; height: 180px; right: 10%; top: 60%; animation-duration: 35s; }
.bg-particle:nth-child(3) { width: 80px; height: 80px; left: 30%; bottom: 10%; animation-duration: 22s; }
.bg-particle:nth-child(4) { width: 120px; height: 120px; right: 20%; top: 10%; animation-duration: 28s; }
.bg-particle:nth-child(5) { width: 150px; height: 150px; left: 60%; bottom: 20%; animation-duration: 33s; }

@keyframes float-particle {
  0% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(10px, 10px) rotate(90deg); }
  50% { transform: translate(0, 20px) rotate(180deg); }
  75% { transform: translate(-10px, 10px) rotate(270deg); }
  100% { transform: translate(0, 0) rotate(360deg); }
}
</style> 
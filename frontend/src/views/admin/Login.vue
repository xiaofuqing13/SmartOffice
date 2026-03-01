<template>
  <div class="login-container">
    <div id="particles-js"></div>
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">智行舟平台管理后台</h1>
        <p class="login-subtitle">高效、智能、便捷</p>
      </div>
      <el-form
        ref="loginForm"
        :model="loginData"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginData.username"
            placeholder="请输入管理员账号"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginData.password"
            type="password"
            placeholder="请输入密码"
            show-password
            :prefix-icon="Lock"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            @click="handleLogin"
            :loading="loading"
            size="large"
          >
            {{ loading ? '登录中...' : '立即登录' }}
          </el-button>
        </el-form-item>
        <el-form-item class="extra-links">
          <el-button
            type="primary"
            link
            @click="goToUserLogin"
            class="back-button"
          >
            返回用户端
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import 'particles.js';

export default {
  name: 'AdminLogin',
  setup() {
    const router = useRouter();
    const store = useStore();
    const loginForm = ref(null);
    const loading = ref(false);

    const loginData = ref({
      username: '',
      password: '',
    });

    const loginRules = {
      username: [{ required: true, message: '管理员账号不能为空', trigger: 'blur' }],
      password: [{ required: true, message: '密码不能为空', trigger: 'blur' }],
    };

    const initParticles = () => {
      window.particlesJS('particles-js', {
        particles: {
          number: { value: 80, density: { enable: true, value_area: 800 } },
          color: { value: '#ffffff' },
          shape: {
            type: 'circle',
            stroke: { width: 0, color: '#000000' },
            polygon: { nb_sides: 5 },
          },
          opacity: {
            value: 0.5,
            random: false,
            anim: { enable: false, speed: 1, opacity_min: 0.1, sync: false },
          },
          size: {
            value: 3,
            random: true,
            anim: { enable: false, speed: 40, size_min: 0.1, sync: false },
          },
          line_linked: {
            enable: true,
            distance: 150,
            color: '#ffffff',
            opacity: 0.4,
            width: 1,
          },
          move: {
            enable: true,
            speed: 2,
            direction: 'none',
            random: false,
            straight: false,
            out_mode: 'out',
            bounce: false,
            attract: { enable: false, rotateX: 600, rotateY: 1200 },
          },
        },
        interactivity: {
          detect_on: 'canvas',
          events: {
            onhover: { enable: true, mode: 'repulse' },
            onclick: { enable: true, mode: 'push' },
            resize: true,
          },
          modes: {
            grab: { distance: 400, line_linked: { opacity: 1 } },
            bubble: { distance: 400, size: 40, duration: 2, opacity: 8, speed: 3 },
            repulse: { distance: 200, duration: 0.4 },
            push: { particles_nb: 4 },
            remove: { particles_nb: 2 },
          },
        },
        retina_detect: true,
      });
    };

    const handleLogin = () => {
      loginForm.value.validate(async (valid) => {
        if (valid) {
          loading.value = true;
          try {
            await store.dispatch('user/adminLogin', loginData.value);
            ElMessage.success('登录成功，正在跳转...');
            await router.push('/admin/dashboard');
          } catch (error) {
            ElMessage.error(error.message || '登录失败，请检查账号或密码');
          } finally {
            loading.value = false;
          }
        }
      });
    };
    
    const goToUserLogin = () => {
      router.push('/');
    };

    onMounted(() => {
      initParticles();
    });

    return {
      loginForm,
      loginData,
      loginRules,
      loading,
      handleLogin,
      goToUserLogin,
      User,
      Lock,
    };
  },
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2c3e50, #3498db);
}

#particles-js {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.login-card {
  position: relative;
  z-index: 2;
  width: 400px;
  padding: 40px;
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  text-align: center;
  color: white;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.login-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 16px 40px 0 rgba(0, 0, 0, 0.4);
}

.login-header {
  margin-bottom: 30px;
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 10px;
}

.login-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 25px;
}

.login-form :deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.2) !important;
  border-radius: 8px;
  border: none;
  box-shadow: none !important;
}

.login-form :deep(.el-input__inner) {
  color: white;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.7);
}

.login-form :deep(.el-input__prefix-inner),
.login-form :deep(.el-input__suffix-inner) {
  color: rgba(255, 255, 255, 0.9);
}

.login-button {
  width: 100%;
  border: none;
  background: linear-gradient(135deg, #3498db, #8e44ad);
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.extra-links {
  text-align: center;
  margin-top: -10px;
}

.back-button {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  transition: all 0.3s ease;
}

.back-button:hover {
  color: #fff;
  transform: scale(1.05);
}
</style> 
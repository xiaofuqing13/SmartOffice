<template>
  <div class="admin-layout">
    <div class="sidebar">
      <div class="logo">
        <span>智行舟-企业后台</span>
      </div>
      <nav class="navigation">
        <ul>
          <li>
            <router-link to="/admin/dashboard">
              <i class="bi bi-grid-1x2-fill"></i>
              <span>仪表盘</span>
            </router-link>
          </li>
          <li>
            <router-link to="/admin/users">
              <i class="bi bi-people-fill"></i>
              <span>用户管理</span>
            </router-link>
          </li>
          <li>
            <router-link to="/admin/companies">
              <i class="bi bi-building"></i>
              <span>公司管理</span>
            </router-link>
          </li>
          <li>
            <router-link to="/admin/departments">
              <i class="bi bi-diagram-3-fill"></i>
              <span>部门管理</span>
            </router-link>
          </li>
          <li>
            <router-link to="/admin/smart-docs">
              <i class="bi bi-file-earmark-text-fill"></i>
              <span>智能文档</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/contracts" class="nav-link" active-class="active">
              <i class="bi bi-file-earmark-text"></i> 合同管理
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/contract-templates" class="nav-link" active-class="active">
              <i class="bi bi-file-richtext"></i> 合同模板
            </router-link>
          </li>
          <li>
            <router-link to="/admin/knowledge">
              <i class="bi bi-book-fill"></i>
              <span>知识库管理</span>
            </router-link>
          </li>
        </ul>
      </nav>
      <div class="sidebar-footer">
        <button @click="logout" class="logout-btn">
          <i class="bi bi-box-arrow-right"></i>
          <span>安全退出</span>
        </button>
      </div>
    </div>
    <div class="main-content">
      <header class="top-bar">
        <h3>欢迎您，企业管理员！</h3>
      </header>
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';

export default {
  name: 'AdminLayout',
  setup() {
    const router = useRouter();
    const store = useStore();

    const logout = async () => {
      await store.dispatch('user/logout');
      router.push('/admin/login');
    };

    return {
      logout,
    };
  },
};
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  background-color: #f0f2f5;
}

.sidebar {
  width: 250px;
  background-image: linear-gradient(180deg, #3a506b 0%, #1c2b3a 100%);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.logo span {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #ffffff;
  text-align: center;
}

.navigation {
  flex-grow: 1;
  margin-top: 16px;
}

.navigation ul {
  list-style: none;
  padding: 0 16px;
  margin: 0;
}

.navigation a {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  color: #ffffff;
  text-decoration: none;
  transition: all 0.3s ease;
  font-size: 15px;
  border-radius: 6px;
  margin-bottom: 8px;
  position: relative;
}

.navigation a:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.navigation .router-link-active {
  background-color: #3498db;
  color: white;
  box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3);
}

.navigation .router-link-active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    height: 60%;
    width: 4px;
    background-color: #ffffff;
    border-radius: 0 2px 2px 0;
}

.navigation a span {
  color: #ffffff;
}

.navigation i {
  margin-right: 12px;
  font-size: 20px;
  width: 24px;
  text-align: center;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.logout-btn {
  width: 100%;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-size: 15px;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.3);
}

.logout-btn span {
  color: #ffffff;
}

.logout-btn i {
  margin-right: 8px;
}

.main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.top-bar {
  background-color: white;
  padding: 16px 24px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  z-index: 1;
}

.content-area {
  padding: 24px;
  flex-grow: 1;
}
</style> 
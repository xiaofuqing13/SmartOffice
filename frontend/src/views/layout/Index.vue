<template>
  <div class="app-wrapper" :class="{ 'mobile': device === 'mobile' }">
    <!-- 侧边栏 -->
    <Sidebar class="sidebar-container" />
    
    <!-- 主要内容区域 -->
    <div class="main-container" :style="mainContainerStyle">
      <!-- 顶部导航栏 -->
      <Navbar />
      
      <!-- 内容区域 -->
      <div class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in" @before-leave="beforeRouteLeave">
            <keep-alive :include="cachedRoutes">
              <component :is="Component" :key="$route.fullPath + refreshKey" />
          </keep-alive>
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, onBeforeUnmount, watch, ref } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/layout/Sidebar.vue'
import Navbar from '@/components/layout/Navbar.vue'

export default {
  name: 'Layout',
  components: {
    Sidebar,
    Navbar
  },
  setup() {
    const store = useStore()
    const route = useRoute()
    
    // 设备类型
    const device = computed(() => store.getters.device)
    
    // 侧边栏状态
    const sidebarOpened = computed(() => store.getters.sidebar.opened)
    
    // 刷新页面时使用的key
    const refreshKey = ref(0)
    
    // 需要缓存的路由，缓存小组件页面提高切换性能
    const cachedRoutes = ref([
      'Dashboard',
      'Calendar',
      'Chat',
      'Contact',
      'Company',
      'Project',
      'Profile',
      'Knowledge'
    ])
    
    // 动态计算主容器样式
    const mainContainerStyle = computed(() => {
      // 侧边栏展开宽度为160px，收起宽度为64px
      const sidebarWidth = sidebarOpened.value ? '160px' : '64px'
      return {
        marginLeft: sidebarWidth,
        width: `calc(100% - ${sidebarWidth})`
      }
    })
    
    // 路由离开前的清理工作
    const beforeRouteLeave = () => {
      // 清理可能存在的DOM副作用
      cleanupDOMElements();
    }
    
    // 清理DOM元素的集中处理函数
    const cleanupDOMElements = () => {
      try {
        // 移除可能的事件拦截器和遮罩
        document.querySelectorAll('.el-overlay, .el-popup-parent--hidden, .el-message, .el-message-box').forEach(el => {
            if (el && el.parentNode) {
              try {
                el.parentNode.removeChild(el);
              } catch (e) {
                console.error('清理DOM元素失败:', e);
              }
            }
          });
          
          // 恢复body样式
          if (document && document.body && document.body.style) {
          document.body.style.overflow = '';
          document.body.classList.remove('el-popup-parent--hidden');
          }
          
          // 确保导航菜单可点击
          document.querySelectorAll('.el-menu-item, .el-submenu').forEach(el => {
            if (el && el.style) {
            el.style.pointerEvents = 'auto';
            }
          });
        
        // 如果当前是智能文档页面，额外清理相关资源
        if (route.path === '/smartdoc' || route.path.startsWith('/smartdoc/')) {
          document.querySelectorAll('.ql-container, .ql-toolbar, .ql-editor').forEach(el => {
            if (el && el.parentNode) {
              el.parentNode.removeChild(el);
            }
          });
        }
      } catch (error) {
        console.error('清理DOM资源失败:', error);
      }
    }
    
    // 监视路由变化，刷新页面时更新key值
    watch(() => route.fullPath, (newPath, oldPath) => {
      if (newPath === oldPath && oldPath !== undefined) {
        // 相同路径刷新页面时，更新key值触发组件重新渲染
        refreshKey.value = Date.now();
      }
    });
    
    // 响应式布局 - 窗口尺寸变化监听
    const handleResize = () => {
      if (document && document.body) {
        if (document.body.clientWidth < 992) {
          store.dispatch('setDevice', 'mobile')
          store.dispatch('toggleSidebar', false)
        } else {
          store.dispatch('setDevice', 'desktop')
        }
      }
    }
    
    onMounted(() => {
      handleResize()
      window.addEventListener('resize', handleResize)
    })
    
    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
    })
    
    return {
      device,
      mainContainerStyle,
      cachedRoutes,
      refreshKey,
      beforeRouteLeave
    }
  }
}
</script>

<style lang="scss" scoped>
.app-wrapper {
  position: relative;
  height: 100%;
  width: 100%;
  display: flex;
  background-color: var(--el-bg-color-page);
  color: var(--text-color);
}

.sidebar-container {
  transition: width 0.28s;
  height: 100%;
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 1001;
}

.main-container {
  min-height: 100%;
  transition: margin-left 0.28s;
  position: relative;
  padding-top: 60px; /* 为固定导航栏腾出空间 */
  overflow: auto; /* 允许主内容区出现滚动条 */
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
  color: var(--text-color);
}

.app-main {
  flex: 1;
  width: 100%;
  position: relative;
  overflow: auto;
  padding: 0;
  height: 100%;
  background-color: var(--el-bg-color-page);
}

/* 增强过渡动画效果 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* 备用过渡动画，确保动画效果一定生效 */
.v-enter-active,
.v-leave-active {
  transition: opacity 0.3s ease;
}

.v-enter-from,
.v-leave-to {
  opacity: 0;
}

.app-wrapper.mobile .sidebar-container {
  transition: transform .28s;
  width: 180px !important;
}

.app-wrapper.mobile .main-container {
  margin-left: 0 !important;
  width: 100% !important;
}

.app-wrapper.mobile .sidebar-container.is-collapsed {
  transform: translateX(-200px);
}
</style> 
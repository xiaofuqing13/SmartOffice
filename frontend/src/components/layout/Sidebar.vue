<template>
  <div class="sidebar" :class="{ 'is-collapsed': !sidebarOpened }">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <img src="https://cdn-icons-png.flaticon.com/512/2891/2891491.png" alt="Logo">
      <h5 v-if="sidebarOpened">智能办公系统</h5>
    </div>

    <!-- 侧边栏菜单 -->
    <el-scrollbar class="sidebar-menu-container">
      <el-menu
        :default-active="activeMenu"
        :collapse="!sidebarOpened"
        :background-color="menuBackgroundColor"
        :text-color="menuTextColor"
        :active-text-color="menuActiveTextColor"
        :unique-opened="true"
        router
      >
        <el-menu-item 
          v-for="route in routes" 
          :key="route.absPath" 
          :index="route.absPath"
          @click="handleMenuClick(route.absPath)"
        >
          <el-icon>
            <component :is="iconComponent(route.meta.icon)"></component>
          </el-icon>
          <template #title>
            <span>{{ route.meta.title }}</span>
          </template>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script>
import { computed, watch, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'

export default {
  name: 'Sidebar',
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()
    
    // 跟踪上一个路由
    const lastPath = ref('');

    // 从Vuex中获取侧边栏状态
    const sidebarOpened = computed(() => store.getters.sidebar.opened)

    // 菜单路由
    const routes = computed(() => {
      // 首先获取所有非隐藏的路由
      const allRoutes = router.options.routes.find(r => r.path === '/').children
        .filter(route => !route.hidden)
        .map(route => ({
          ...route,
          absPath: route.path.startsWith('/') ? route.path : '/' + route.path
        }));
      
      // 定义期望的路由顺序
      const routeOrder = [
        'dashboard',     // 工作中心
        'smartdoc',      // 文档处理
        'project',       // 项目协作
        'calendar',      // 日程安排
        'chat',          // 即时沟通
        'contract',      // 智能合同
        'knowledge',     // 企业知识库
        'contact',       // 企业通讯录
        'company',       // 企业信息
        'profile'        // 个人中心
      ];
      
      // 按照定义的顺序对路由进行排序
      return allRoutes.sort((a, b) => {
        const indexA = routeOrder.indexOf(a.path);
        const indexB = routeOrder.indexOf(b.path);
        // 如果两者都在排序列表中，按列表顺序排序
        if (indexA >= 0 && indexB >= 0) {
          return indexA - indexB;
        }
        // 如果只有一个在列表中，将其排在前面
        if (indexA >= 0) return -1;
        if (indexB >= 0) return 1;
        // 如果都不在列表中，保持原顺序
        return 0;
      });
    })

    // 当前激活的菜单
    const activeMenu = computed(() => {
      const path = route.path;
      
      // 如果当前路径是文档详情页，激活的菜单应该是smartdoc
      if (path.startsWith('/smartdoc/')) {
        return '/smartdoc';
      }
      
      return path;
    })
    
    // 获取主题相关的颜色
    const currentTheme = computed(() => {
      const theme = localStorage.getItem('theme') || 'light';
      return theme;
    });
    
    // 根据主题计算菜单颜色
    const menuBackgroundColor = computed(() => {
      return currentTheme.value === 'dark' ? 'var(--bg-color-secondary)' : 'var(--bg-color)';
    });
    
    const menuTextColor = computed(() => {
      return 'var(--text-color)';
    });
    
    const menuActiveTextColor = computed(() => {
      return 'var(--primary-color)';
    });
    
    // 处理菜单点击
    const handleMenuClick = (path) => {
      // 确保path为绝对路径
      if (!path.startsWith('/')) path = '/' + path;
      
      console.log('菜单点击:', path, '当前路径:', route.path);
      
      // 如果是从smartdoc详情页点击到智能文档首页，使用路由导航
      if (route.path.startsWith('/smartdoc/') && path === '/smartdoc') {
        try {
          // 清理可能存在的遮罩
          document.querySelectorAll('.el-overlay').forEach(el => {
            if (el && el.parentNode) el.parentNode.removeChild(el);
          });
          
          // 使用路由导航而不是强制刷新
          router.push(path);
          return;
        } catch (e) {
          console.error('导航处理错误:', e);
        }
      }
      
      // 如果是从smartdoc页面点击其他页面，也使用路由导航
      if ((route.path === '/smartdoc' || route.path.startsWith('/smartdoc/')) && path !== '/smartdoc') {
        try {
          // 清理可能存在的遮罩
          document.querySelectorAll('.el-overlay').forEach(el => {
            if (el && el.parentNode) el.parentNode.removeChild(el);
          });
          
          // 清理编辑器实例以避免内存泄漏，但不中断导航流程
          setTimeout(() => {
            cleanupQuillEditor();
          }, 100);
          
          // 使用路由导航代替硬刷新
          router.push(path);
        } catch (e) {
          console.error('导航处理错误:', e);
          // 如果发生错误，尝试使用硬刷新作为后备方案
          window.location.href = path;
        }
      } else if (path === '/smartdoc' && !route.path.startsWith('/smartdoc')) {
        // 从其他页面点击智能文档菜单，使用常规导航
        router.push(path);
      } else {
        // 其他情况使用常规导航
        router.push(path);
      }
    }
    
    // 清理Quill编辑器，避免内存泄漏
    const cleanupQuillEditor = () => {
      try {
        // 移除编辑器相关DOM元素
        const quillElements = document.querySelectorAll('.ql-container, .ql-toolbar, .ql-editor');
        quillElements.forEach(el => {
          if (el && el.parentNode) {
            // 创建克隆以移除事件监听器
            const clone = el.cloneNode(false);
            if (el.parentNode) {
              el.parentNode.replaceChild(clone, el);
            }
          }
        });
      } catch (error) {
        console.error('清理编辑器资源失败:', error);
      }
    }
    
    // 监视路由变化，确保导航菜单正常工作
    watch(() => route.path, () => {
      // 记录上一个路径
      lastPath.value = route.path;
      
      // 在路由变化时确保导航菜单可点击
      setTimeout(() => {
        document.querySelectorAll('.el-menu-item, .el-submenu').forEach(el => {
          el.style.pointerEvents = 'auto';
        });
      }, 50);
    });

    // 将Bootstrap图标类名转换为Element Plus图标组件
    const iconComponent = (icon) => {
      // 如果是bootstrap图标类，转换为Element Plus图标
      if (icon && icon.includes('bi-')) {
        // 移除bi-前缀
        const iconName = icon.replace('bi-', '');
        
        // 图标映射表 - Bootstrap图标到Element Plus图标的映射
        const iconMap = {
          'grid-1x2': 'Menu',
          'calendar-week': 'Calendar',
          'book': 'Collection',
          'chat-dots': 'ChatDotRound',
          'camera-video': 'VideoCamera',
          'file-earmark-text': 'Document',
          'file-earmark-ruled': 'Tickets',
          'envelope': 'Message',
          'check2-square': 'CheckboxButton',
          'box-seam': 'Box',
          'person-lines-fill': 'User',
          'kanban': 'Opportunity',
          'list-check': 'Finished',
          'people': 'UserFilled',
          'building': 'OfficeBuilding',
          'gear': 'Setting',
          'house': 'HomeFilled',
          'grid': 'Grid',
          'person': 'User'
        };
        
        // 如果在映射表中找到对应的图标，则返回它，否则返回默认图标
        return iconMap[iconName] || 'Document';
      }
      
      // 如果不是bi-前缀，则原样返回
      return icon || 'Document';
    }

    return {
      sidebarOpened,
      routes,
      activeMenu,
      iconComponent,
      handleMenuClick,
      menuBackgroundColor,
      menuTextColor,
      menuActiveTextColor
    }
  }
}
</script>

<style lang="scss" scoped>
.sidebar {
  width: 160px;
  height: 100%;
  background-color: var(--bg-color);
  border-right: 1px solid var(--border-color);
  box-shadow: 0 0 10px var(--shadow-color);
  z-index: 1000;
  transition: width 0.3s;
}

.sidebar.is-collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-color);
  height: 60px;
  background-color: var(--bg-color);
}

.sidebar-header img {
  width: 24px;
  height: 24px;
}

.sidebar-header h5 {
  margin: 0 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  white-space: nowrap;
}

.sidebar-menu-container {
  height: calc(100% - 60px);
}

.el-menu {
  border-right: none;
}

.el-menu-item {
  height: 50px;
  line-height: 50px;
  position: relative;
  overflow: hidden;
  
  /* 添加过渡效果 */
  transition: background-color 0.25s ease, color 0.25s ease;
  
  /* 添加悬停效果 */
  &:hover {
    background-color: var(--hover-color) !important;
  }
  
  /* 增强激活状态的样式 */
  &.is-active {
    background-color: rgba(var(--primary-color-rgb, 59, 130, 246), 0.1) !important;
    color: var(--primary-color) !important;
    font-weight: 500;
    
    /* 添加左侧指示条 */
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      height: 100%;
      width: 4px;
      background-color: var(--primary-color);
    }
  }
  
  /* 点击反馈效果 */
  &:active {
    background-color: var(--active-color) !important;
    transform: scale(0.98);
    transition: transform 0.1s;
  }
}

.el-menu-item .el-icon {
  margin-right: 10px;
  width: 24px;
  text-align: center;
  font-size: 18px;
}
</style> 
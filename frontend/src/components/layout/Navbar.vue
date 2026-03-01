<template>
  <div class="navbar">
    <!-- 左侧菜单按钮 -->
    <div class="hamburger-container" @click="toggleSidebar">
      <el-icon size="20">
        <Menu />
      </el-icon>
    </div>

    <!-- 面包屑导航 -->
    <div class="breadcrumb-container">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ currentRoute }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 右侧菜单 -->
    <div class="right-menu">
      <!-- 全局搜索 -->
      <div class="search-container">
        <global-search ref="globalSearchRef" />
      </div>

      <!-- 通知菜单 -->
      <el-dropdown class="notification-container" trigger="click" :teleported="true" @visible-change="handleDropdownChange">
        <div class="notification-icon-container">
          <el-badge :value="reminders.length" class="item" :hidden="reminders.length === 0">
            <el-icon size="18"><Bell /></el-icon>
          </el-badge>
        </div>
        <template #dropdown>
          <el-dropdown-menu style="min-width:260px;max-width:350px;">
            <el-dropdown-item v-if="reminders.length === 0">
              <span style="color:#888;">暂无日程提醒</span>
            </el-dropdown-item>
            <el-dropdown-item v-for="item in reminders" :key="item.recommendation_id || item.event_id" style="white-space:normal;line-height:1.5;position:relative;padding-right:32px;">
              <div style="flex:1;">
                <b>{{ item.title }}</b>
                <div style="font-size:12px;color:#888;">提醒时间：{{ formatReminderTime(item.reminder) }}</div>
                <div style="margin-top:2px;">{{ item.ai_content }}</div>
              </div>
              <el-tooltip content="标记为已读" placement="left">
                <el-icon
                  class="read-icon"
                  style="position:absolute;top:12px;right:8px;cursor:pointer;"
                  @click="markAsRead(item)"
                >
                  <Check />
                </el-icon>
              </el-tooltip>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 用户头像菜单 -->
      <el-dropdown class="avatar-container" trigger="click" :teleported="true" @visible-change="handleDropdownChange">
        <div class="avatar-wrapper">
          <img :src="userAvatar" class="user-avatar">
          <span v-if="username" class="username">{{ username }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>
              <router-link to="/profile" class="dropdown-link">
                <el-icon><User /></el-icon> 个人中心
              </router-link>
            </el-dropdown-item>
            <el-dropdown-item>
              <span @click="(e) => openSettings(e)" style="display: block;">
                <el-icon><Setting /></el-icon> 系统设置
              </span>
            </el-dropdown-item>
            <el-dropdown-item divided>
              <span @click="logout" style="display: block;">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import { computed, ref, inject, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Menu, 
  Bell, 
  User, 
  Setting, 
  SwitchButton, 
  ArrowDown,
  Check
} from '@element-plus/icons-vue'
import { getMonthlyEvents } from '@/api/calendar'
import { getScheduleReminders, markScheduleReminderAsRead } from '@/api/ai' // 导入AI API及已读接口
import GlobalSearch from '@/components/GlobalSearch.vue' // 导入全局搜索组件

export default {
  name: 'Navbar',
  components: {
    GlobalSearch, // 注册全局搜索组件
    Menu, 
    Bell, 
    User, 
    Setting, 
    SwitchButton, 
    ArrowDown,
    Check
  },
  setup() {
    const store = useStore()
    const route = useRoute()
    const router = useRouter()

    const searchInput = ref('')
    const globalSearchRef = ref(null)
    
    // 从Vuex获取侧边栏状态
    const isActive = computed(() => store.getters.sidebar.opened)
    
    // 从Vuex获取用户信息和未读消息
    const userAvatar = computed(() => {
      const avatar = store.getters.user && store.getters.user.avatar;
      if (!avatar) {
        return '/img/default-avatar.svg'; // 更新默认头像路径
      }
      // 检查是否是完整URL
      if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
        return avatar;
      }
      // 添加服务器地址前缀，确保不会重复添加前缀
      if (avatar.startsWith('/')) {
        return `http://localhost:8000${avatar}`;
      } else {
        return `http://localhost:8000/${avatar}`;
      }
    });
    const username = computed(() => {
      // 从store中获取用户信息
      const user = store.getters.user;
      // 优先获取name，如果没有则尝试获取username
      if (user) {
        return user.name || user.username || '';
      }
      return '';
    });
    const reminders = ref([])
    
    // 获取AI日程提醒
    const fetchReminders = async () => {
      try {
        const response = await getScheduleReminders()
        if (response && response.data) {
          let data = []
          if (Array.isArray(response.data)) {
            data = response.data
          } else if (response.data.data && Array.isArray(response.data.data)) {
            data = response.data.data
          } else if (response.success && Array.isArray(response.data)) {
            data = response.data
          }
          // 只保留未读提醒
          reminders.value = data.filter(r => r.is_read === false || r.is_read === undefined)
        } else {
          reminders.value = []
        }
      } catch (e) {
        reminders.value = []
      }
    }

    // 记录已提醒的eventId+提醒时间，避免重复请求
    const remindedSet = ref(new Set())
    // 定时检测日程提醒
    let reminderTimer = null
    const checkReminders = async () => {
      const now = new Date()
      const year = now.getFullYear()
      const month = now.getMonth() + 1
      try {
        // 获取本月所有日程
        const res = await getMonthlyEvents(year, month)
        const events = (res.data || []).filter(e => e.reminder && e.reminder !== 'none')
        for (const event of events) {
          let remindTime = null
          const start = new Date(event.start)
          switch (event.reminder) {
            case '10min': remindTime = new Date(start.getTime() - 10 * 60 * 1000); break
            case '30min': remindTime = new Date(start.getTime() - 30 * 60 * 1000); break
            case '1hour': remindTime = new Date(start.getTime() - 60 * 60 * 1000); break
            case '1day': remindTime = new Date(start.getTime() - 24 * 60 * 60 * 1000); break
            default: remindTime = null
          }
          if (remindTime) {
            const key = `${event.id}_${remindTime.toISOString().slice(0,16)}`
            // 到达提醒点且未提醒过（允许1分钟误差）
            if (Math.abs(now - remindTime) < 60 * 1000 && !remindedSet.value.has(key)) {
              console.log('触发AI提醒检测，事件ID:', event.id, '提醒时间:', remindTime)
              await fetchReminders()
              remindedSet.value.add(key)
            }
          }
        }
      } catch (e) { console.warn('日程检测异常', e) }
    }
    onMounted(() => {
      fetchReminders()
      reminderTimer = setInterval(checkReminders, 60 * 1000)
    })
    // 页面卸载时清理定时器
    onUnmounted(() => { if (reminderTimer) clearInterval(reminderTimer) })

    // 获取当前路由标题
    const currentRoute = computed(() => {
      return route.meta.title || '工作台'
    })

    // 切换侧边栏
    const toggleSidebar = () => {
      store.dispatch('toggleSidebar')
    }

    // 退出登录
    const logout = async () => {
      try {
        await store.dispatch('user/logout')
        // 成功退出后，明确重置loading状态
        store.commit('user/AUTH_REQUEST', false)
        ElMessage.success('退出登录成功')
        router.push('/login')
      } catch (error) {
        ElMessage.error('退出登录失败，请重试')
        console.error('登出失败:', error)
        // 失败时也确保重置loading状态
        store.commit('user/AUTH_REQUEST', false)
      }
    }
    
    // 处理下拉菜单变化，防止事件冒泡
    const handleDropdownChange = (visible) => {
      if (visible) {
        // 阻止可能的事件冒泡
        setTimeout(() => {
          fetchReminders()
        }, 0)
      }
    }

    // 格式化提醒时间
    const formatReminderTime = (reminder) => {
      const reminderMap = {
        '10min': '10分钟前',
        '30min': '30分钟前',
        '1hour': '1小时前',
        '1day': '1天前',
        'none': '不提醒'
      }
      return reminderMap[reminder] || reminder
    }

    // 打开系统设置
    const openSettings = (event) => {
      // 阻止事件冒泡，避免点击事件传播导致设置框立即关闭
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      
      // 使用store的action来打开设置
      store.dispatch('openSettings');
    }

    // 从父组件获取设置对话框可见状态
    const settingsVisible = inject('settingsVisible', computed({
      get: () => store.state.settingsVisible || false,
      set: (value) => store.commit('SET_SETTINGS_VISIBLE', value)
    }));

    // 标记提醒为已读并隐藏
    const markAsRead = async (item) => {
      if (!item.recommendation_id) return
      try {
        await markScheduleReminderAsRead(item.recommendation_id)
        // 隐藏该提醒
        reminders.value = reminders.value.filter(r => r.recommendation_id !== item.recommendation_id)
      } catch (e) {
        ElMessage.error('标记已读失败')
      }
    }

    // 监听路由变化，刷新导航栏状态
    watch(() => route.path, (newPath, oldPath) => {
      if (newPath !== oldPath) {
        // 重新获取日程提醒
        fetchReminders();
        
        // 清空全局搜索组件状态
        if (globalSearchRef.value && typeof globalSearchRef.value.clearSearch === 'function') {
          globalSearchRef.value.clearSearch();
        }
      }
    });

    return {
      // 图标组件
      Menu,
      Bell,
      User,
      Setting,
      SwitchButton,
      ArrowDown,
      Check,
      // 其他数据
      searchInput,
      globalSearchRef,
      isActive,
      userAvatar,
      username,
      currentRoute,
      toggleSidebar,
      logout,
      handleDropdownChange,
      openSettings,
      settingsVisible,
      reminders,
      markAsRead,
      formatReminderTime
    }
  }
}
</script>

<style scoped>
.navbar {
  height: 60px;
  background-color: var(--bg-color);
  box-shadow: 0 1px 4px var(--shadow-color);
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 20000; /* 提高z-index确保不被其他元素覆盖 */
  width: 100%;
}

.hamburger-container {
  cursor: pointer;
  font-size: 20px;
  line-height: 60px;
  padding: 0 15px;
  transition: color 0.3s;
  
  &:hover {
    color: var(--primary-color);
  }
  
  &:active {
    transform: scale(0.95);
  }
}

.breadcrumb-container {
  margin-left: 15px;
  flex: 1;
}

.right-menu {
  display: flex;
  align-items: center;
}

.search-container {
  margin-right: 20px;
}

.search-input {
  width: 210px;
  margin-left: 10px;
  transition: width 0.3s;
}

.search-input:focus {
  width: 240px;
}

.notification-container, 
.avatar-container {
  margin-left: 15px;
  cursor: pointer;
  position: relative;
  z-index: 20001; /* 确保下拉菜单按钮高于其他元素 */
  
  /* 添加悬停效果 */
  &:hover {
    color: var(--primary-color);
  }
  
  /* 添加点击效果 */
  &:active {
    transform: scale(0.95);
  }
}

.notification-icon-container {
  font-size: 18px;
  padding: 5px;
  border-radius: 50%;
  transition: background-color 0.3s, color 0.3s, transform 0.2s;
  min-width: 30px; /* 确保点击区域足够大 */
  min-height: 30px; /* 确保点击区域足够大 */
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* 悬停时显示背景 */
  &:hover {
    background-color: var(--hover-color);
  }
}

.avatar-wrapper {
  display: flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 20px;
  transition: background-color 0.3s, transform 0.2s;
  min-height: 40px; /* 确保点击区域足够大 */
  
  /* 悬停时显示背景 */
  &:hover {
    background-color: var(--hover-color);
  }
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 8px;
}

.username {
  font-size: 14px;
  color: var(--text-color);
  margin-right: 5px;
}

.dropdown-link {
  display: block;
  width: 100%;
  height: 100%;
  text-decoration: none;
  color: inherit;
}

a {
  text-decoration: none;
  color: inherit;
}

/* 修复下拉菜单项样式 */
:deep(.el-dropdown-menu) {
  z-index: 20002 !important; /* 确保下拉菜单显示在最上层 */
}

:deep(.el-dropdown-menu__item) {
  line-height: 30px;
  padding: 6px 16px;
  pointer-events: auto !important; /* 确保点击事件能够被捕获 */
  
  &:hover {
    background-color: var(--hover-color);
    color: var(--primary-color);
  }
  
  &:active {
    background-color: var(--active-color);
  }
  
  .el-icon {
    margin-right: 8px;
    font-size: 16px;
    vertical-align: middle;
  }
}

.read-icon {
  color: #52c41a;
  font-size: 20px;
  border-radius: 50%;
  transition: box-shadow 0.2s, background 0.2s, transform 0.1s;
}
.read-icon:hover {
  background: #e6f7ec;
  box-shadow: 0 2px 8px rgba(82,196,26,0.15);
  color: #389e0d;
  transform: scale(1.15);
}
.read-icon:active {
  background: #b7eb8f;
  transform: scale(0.95);
}
</style> 
import { createStore } from 'vuex'
import user from './modules/user'

export default createStore({
  state: {
    // 系统信息
    app: {
      sidebar: {
        opened: true
      },
      device: 'desktop'
    },
    // 未读消息数量
    unread: {
      messages: 5,
      notifications: 8,
      tasks: 3,
      approvals: 2
    },
    // 设置对话框可见性
    settingsVisible: false,
    // 记录最后一个打开设置的路由路径
    settingsOpenedOnPath: null
  },
  mutations: {
    // 切换侧边栏
    TOGGLE_SIDEBAR(state) {
      state.app.sidebar.opened = !state.app.sidebar.opened
    },
    // 设置设备类型
    SET_DEVICE(state, device) {
      state.app.device = device
    },
    // 更新未读消息
    SET_UNREAD(state, unread) {
      state.unread = {
        ...state.unread,
        ...unread
      }
    },
    // 设置设置对话框可见性
    SET_SETTINGS_VISIBLE(state, visible) {
      state.settingsVisible = visible
      // 当打开设置时，记录当前路径，用于判断路由变化
      if (visible) {
        state.settingsOpenedOnPath = window.location.pathname
      } else {
        state.settingsOpenedOnPath = null
      }
    }
  },
  actions: {
    // 切换侧边栏
    toggleSidebar({ commit }) {
      commit('TOGGLE_SIDEBAR')
    },
    // 设置设备类型
    setDevice({ commit }, device) {
      commit('SET_DEVICE', device)
    },
    // 打开设置弹窗
    openSettings({ commit }) {
      // 先清理可能存在的遮罩
      document.querySelectorAll('.el-overlay').forEach(el => {
        if (el && el.parentNode) {
          el.parentNode.removeChild(el);
        }
      });
      
      // 恢复body样式
      document.body.style.overflow = '';
      document.body.classList.remove('el-popup-parent--hidden');
      
      setTimeout(() => {
        commit('SET_SETTINGS_VISIBLE', true)
      }, 100)
    }
  },
  getters: {
    // 获取侧边栏状态
    sidebar: state => state.app.sidebar,
    // 获取设备类型
    device: state => state.app.device,
    // 获取未读消息 - 通过dashboard模块获取
    unread: state => state.dashboard.unread,
    // 获取用户信息
    user: state => state.user.user,
    // 获取设置对话框可见性
    settingsVisible: state => state.settingsVisible,
    // 获取设置打开的路径
    settingsOpenedOnPath: state => state.settingsOpenedOnPath
  },
  modules: {
    user
    // dashboard
  }
}) 
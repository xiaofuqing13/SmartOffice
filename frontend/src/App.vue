<template>
  <div id="app">
    <router-view />
    <settings-dialog v-model:visible="settingsVisible" />
  </div>
</template>

<script>
import { computed, provide } from 'vue';
import { useStore } from 'vuex';
import SettingsDialog from '@/components/settings/SettingsDialog.vue';

export default {
  name: 'App',
  components: {
    SettingsDialog
  },
  setup() {
    const store = useStore();
    
    // 从Vuex获取设置对话框可见状态
    const settingsVisible = computed({
      get: () => store.state.settingsVisible || false,
      set: (value) => store.commit('SET_SETTINGS_VISIBLE', value)
    });
    
    // 提供给子组件，允许任何子组件访问此状态
    provide('settingsVisible', settingsVisible);
    
    return {
      settingsVisible
    };
  }
};
</script>

<style>
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css");

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  font-family: 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  background-color: var(--el-bg-color-page, #f5f7fa);
  color: var(--text-color, #333);
  height: 100%;
  width: 100%;
  overflow-x: hidden;
  position: relative;
  transition: background-color 0.3s ease, color 0.3s ease;
}

#app {
  position: relative;
  height: 100%;
  width: 100%;
  background-color: var(--el-bg-color-page);
}

.el-button {
  font-weight: 500;
}

.app-container {
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

/* 修复导航栏重叠问题 */
.el-menu-item-group__title,
.el-menu.el-menu--horizontal {
  z-index: auto !important;
}

/* 增强导航交互样式 */
.el-menu-item {
  transition: background-color 0.3s, color 0.3s !important;
}

.el-menu-item:hover {
  background-color: var(--hover-color) !important;
}

.el-menu-item.is-active {
  color: var(--primary-color) !important;
  background-color: rgba(var(--primary-color-rgb, 59, 130, 246), 0.1) !important;
}

/* 增强下拉菜单交互 */
.el-dropdown-menu__item {
  transition: background-color 0.2s, color 0.2s !important;
  font-size: 14px;
  padding: 8px 16px !important;
  line-height: 1.5 !important;
}

.el-dropdown-menu__item:hover {
  background-color: var(--hover-color) !important;
  color: var(--primary-color) !important;
}

.el-dropdown-menu__item:active {
  transform: scale(0.98);
}

/* 深色模式下元素背景色强制覆盖 */
body[data-theme="dark"],
:root[data-theme="dark"] {
  --bg-color: #1a1a1a;
  --el-bg-color-page: #141414;
  --el-bg-color: #1d1d1d;
  --el-bg-color-overlay: #1d1d1d;
  --el-border-color: #424242;
  --el-border-color-light: #424242;
  --el-border-color-lighter: #333333;
  --el-text-color-primary: #e0e0e0;
  --el-text-color-regular: #a6a6a6;
  --el-text-color-secondary: #8c8c8c;
  --el-fill-color: #262626;
  --el-fill-color-light: #2c2c2c;
  --el-fill-color-lighter: #333333;
  --el-fill-color-blank: #1a1a1a;
  
  /* 强制所有容器使用深色背景 */
  html, body, #app, .app-wrapper, .main-container, .app-main, .knowledge-container, 
  .el-container, .el-main, .el-aside, .el-header, .el-footer,
  .container, .content, .wrapper, .page-container, .page-wrapper,
  .layout-container, .layout-wrapper, .view-container, .view-wrapper,
  .section, .panel, .box, .block {
    background-color: var(--el-bg-color-page) !important;
  }
  
  /* 强制对话框和弹出层使用深色背景 */
  .el-dialog, .el-dialog__body, .el-dialog__header, .el-dialog__footer,
  .el-popover, .el-popconfirm, .el-tooltip__popper,
  .el-drawer, .el-drawer__body, .el-drawer__header, .el-drawer__footer {
    background-color: var(--el-bg-color) !important;
    color: var(--el-text-color-primary) !important;
    border-color: var(--el-border-color) !important;
  }
  
  /* 强制所有背景为白色的元素使用深色背景 */
  [style*="background-color: white"],
  [style*="background-color: #fff"],
  [style*="background-color: #ffffff"],
  [style*="background: white"],
  [style*="background: #fff"],
  [style*="background: #ffffff"] {
    background-color: var(--el-bg-color-page) !important;
    background: var(--el-bg-color-page) !important;
  }
  
  /* 卡片组件强制背景色 */
  .el-card, 
  .project-card, 
  .department-card,
  .info-card,
  .user-info,
  .profile-card {
    background-color: var(--bg-color-secondary) !important;
  }
  
  /* 列表项强制背景色 */
  .list-item,
  .item,
  .task-item,
  .project-item,
  .notification-item,
  .message-item,
  .contact-item {
    background-color: var(--bg-color-secondary) !important;
  }
  
  /* 表格强制背景色和文字颜色 */
  .el-table,
  .el-table__header,
  .el-table__body,
  .el-table--enable-row-hover .el-table__body tr:hover>td {
    background-color: var(--bg-color-secondary) !important;
    color: var(--text-color) !important;
  }
  
  .el-table th,
  .el-table tr,
  .el-table td {
    background-color: inherit !important;
    color: var(--text-color) !important;
    border-bottom-color: var(--border-color) !important;
  }
  
  /* 输入框强制背景色和文字颜色 */
  .el-input__wrapper,
  .el-textarea__wrapper {
    background-color: var(--bg-color-tertiary) !important;
    box-shadow: 0 0 0 1px var(--border-color) inset !important;
  }
  
  .el-input__inner,
  .el-textarea__inner {
    background-color: transparent !important;
    color: var(--text-color) !important;
  }
  
  /* 下拉菜单强制背景色和文字颜色 */
  .el-select-dropdown,
  .el-select__popper,
  .el-dropdown-menu,
  .el-popper,
  .el-picker-panel,
  .el-date-picker,
  .el-date-range-picker,
  .el-time-panel {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
  }
  
  .el-select-dropdown__item,
  .el-dropdown-menu__item {
    color: var(--text-color) !important;
  }
  
  .el-select-dropdown__item.hover,
  .el-select-dropdown__item:hover,
  .el-dropdown-menu__item:hover,
  .el-dropdown-menu__item:focus {
    background-color: var(--hover-color) !important;
  }
  
  /* 箭头指示器 */
  .el-popper .el-popper__arrow::before {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
  }
  
  /* Element Plus全局变量覆盖 */
  --el-color-white: var(--bg-color) !important;
  --el-bg-color: var(--bg-color-secondary) !important;
  --el-bg-color-overlay: var(--bg-color-secondary) !important;
  --el-fill-color-blank: var(--bg-color) !important;
  --el-border-color: var(--border-color) !important;
  --el-border-color-light: var(--border-color) !important;
  --el-text-color-primary: var(--text-color) !important;
  --el-text-color-regular: var(--text-color-secondary) !important;
  --el-text-color-secondary: var(--text-color-tertiary) !important;
  
  /* 特别是这些属性对下拉框影响最大 */
  --el-fill-color-lighter: var(--bg-color-tertiary) !important;
  --el-select-option-selected-hover-bg-color: var(--hover-color) !important;
  --el-select-option-hover-bg-color: var(--hover-color) !important;
  
  /* 为特定页面添加特例 - 保持按钮原始样式 */
  .smartdoc-detail .ai-feature-card:nth-child(4) .ai-feature-btn,
  .smartdoc-detail .ai-feature-card:nth-child(5) .ai-feature-btn {
    /* 清除可能会影响按钮的继承属性 */
    background-color: initial;
    border-color: initial;
    color: initial;
    box-shadow: initial;
  }
}

/* 全局tooltip样式，灰色背景和白色字体 */
:root {
  --el-tooltip-bg-color: rgba(70, 70, 70, 0.9) !important;
  --el-tooltip-text-color: #ffffff !important;
  --el-tooltip-border-color: rgba(70, 70, 70, 0.9) !important;
  --el-tooltip-padding: 8px 12px !important;
  --el-tooltip-arrow-size: 6px !important;
  --el-tooltip-border-radius: 4px !important;
}

/* 确保所有tooltip的箭头颜色一致 */
.el-popper.is-dark .el-popper__arrow::before,
.el-tooltip__popper .el-popper__arrow::before {
  background-color: rgba(70, 70, 70, 0.9) !important;
  border-color: rgba(70, 70, 70, 0.9) !important;
}

/* 确保所有tooltip的背景和文字颜色一致 */
.el-tooltip__popper,
.el-tooltip__popper.is-dark, 
.el-popper.is-dark,
.el-popper.is-customized,
.el-popper.el-tooltip__popper {
  background-color: rgba(70, 70, 70, 0.9) !important;
  color: #ffffff !important;
  border-color: rgba(70, 70, 70, 0.9) !important;
}

/* 确保tooltip内的所有文本都是白色 */
.el-tooltip__popper span,
.el-popper.is-dark span,
.el-popper.el-tooltip__popper span {
  color: #ffffff !important;
}
</style> 
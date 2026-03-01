<template>
  <div v-if="renderDialog" class="settings-dialog-wrapper">
    <teleport to="body">
      <transition name="settings-fade">
        <div v-if="visible" class="settings-dialog-container">
          <div class="settings-dialog-overlay" @click="handleOverlayClick"></div>
          <div class="settings-dialog">
            <div class="settings-content">
              <theme-settings @close="handleClose"></theme-settings>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import ThemeSettings from './ThemeSettings.vue';

export default {
  name: 'SettingsDialog',
  components: {
    ThemeSettings
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:visible'],
  setup(props, { emit }) {
    const store = useStore();
    const router = useRouter();
    const renderDialog = ref(true);
    
    // 监听路由变化
    watch(() => router.currentRoute.value.path, (newPath, oldPath) => {
      if (props.visible && oldPath !== newPath) {
        // 路由已变化，关闭弹窗
        handleClose();
      }
    });
    
    // 监听可见性变化
    watch(() => props.visible, async (isVisible) => {
      if (isVisible) {
        // 弹窗打开
        document.body.classList.add('settings-dialog-open');
        
        // 当弹窗打开时，等待下一个DOM循环，确保弹窗已渲染
        await nextTick();
        focusTrap();
      } else {
        // 弹窗关闭
        document.body.classList.remove('settings-dialog-open');
      }
    });
    
    // 键盘事件处理
    const handleKeyDown = (e) => {
      if (props.visible && e.key === 'Escape') {
        handleClose();
      }
    };
    
    // 点击遮罩关闭
    const handleOverlayClick = () => {
      handleClose();
    };
    
    // 关闭弹窗
    const handleClose = () => {
      emit('update:visible', false);
      
      // 使用Vuex同步状态
      setTimeout(() => {
        store.commit('SET_SETTINGS_VISIBLE', false);
        
        // 清理DOM
        cleanup();
      }, 100);
    };
    
    // 将焦点限制在弹窗内
    const focusTrap = () => {
      const dialog = document.querySelector('.settings-dialog');
      if (dialog) {
        dialog.focus();
      }
    };
    
    // 清理函数
    const cleanup = () => {
      // 清理可能存在的遮罩层
      document.querySelectorAll('.el-overlay, .el-popup-parent--hidden, .v-modal').forEach(el => {
        if (el && el.parentNode) {
          el.parentNode.removeChild(el);
        }
      });
      
      // 恢复body样式
      document.body.style.overflow = '';
      document.body.classList.remove('el-popup-parent--hidden');
      document.body.classList.remove('settings-dialog-open');
    };
    
    // 组件挂载
    onMounted(() => {
      window.addEventListener('keydown', handleKeyDown);
      
      // 清理现有遮罩层
      cleanup();
    });
    
    // 组件卸载
    onUnmounted(() => {
      window.removeEventListener('keydown', handleKeyDown);
      cleanup();
    });
    
    return {
      renderDialog,
      handleClose,
      handleOverlayClick
    };
  }
};
</script>

<style lang="scss">
// 全局样式，确保不被scoped限制
body.settings-dialog-open {
  overflow: hidden;
}

.settings-dialog-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

.settings-dialog-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.settings-dialog-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(1px);
  z-index: 10001;
  cursor: pointer;
}

.settings-dialog {
  position: relative;
  width: 800px;
  max-width: 90vw;
  max-height: 90vh;
  background-color: var(--bg-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px var(--shadow-color);
  z-index: 10002;
  overflow: hidden;
}

.settings-content {
  width: 100%;
  height: 100%;
  overflow: auto;
}

// 淡入淡出动画
.settings-fade-enter-active,
.settings-fade-leave-active {
  transition: all 0.3s ease;
}

.settings-fade-enter-from,
.settings-fade-leave-to {
  opacity: 0;
}

.settings-fade-enter-from .settings-dialog {
  transform: scale(0.9);
}

.settings-fade-leave-to .settings-dialog {
  transform: scale(0.9);
}
</style> 
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import store from './store'
// 导入全局样式文件
import './styles/index.scss'

// 导入Lottie动画库
import lottie from 'lottie-web'
// 添加到全局window对象
window.lottie = lottie

// 导入Bootstrap和Bootstrap图标
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'

// 导入Element Plus图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 导入自定义图标组件
import { registerCustomIcons } from './components/icons'

// 导入错误处理工具
import { setupErrorHandlers } from './utils/errorHandler'

// 导入mitt
import mitt from 'mitt'

// 设置全局错误处理，修复"v[w] is not a function"错误
setupErrorHandlers()

// 初始化主题设置
const initTheme = () => {
  // 从localStorage获取主题设置
  const savedTheme = localStorage.getItem('theme');
  const savedDensity = localStorage.getItem('density');
  const savedFontSize = localStorage.getItem('fontSize');
  
  // 应用主题
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  } else {
    // 检测系统主题
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    localStorage.setItem('theme', prefersDark ? 'dark' : 'light');
  }
  
  // 应用密度设置
  if (savedDensity) {
    document.body.setAttribute('data-density', savedDensity);
  } else {
    document.body.setAttribute('data-density', 'standard');
    localStorage.setItem('density', 'standard');
  }
  
  // 应用字体大小
  if (savedFontSize) {
    document.documentElement.style.setProperty('--font-size-base', `${savedFontSize}px`);
  } else {
    document.documentElement.style.setProperty('--font-size-base', '14px');
    localStorage.setItem('fontSize', '14');
  }
  
  // 监听系统主题变化
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    // 仅当用户未手动设置主题时才跟随系统
    if (!localStorage.getItem('theme')) {
      const newTheme = e.matches ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    }
  });
}

// 初始化主题
initTheme();

// 创建Vue应用实例
const app = createApp(App)

// 创建全局事件总线
const emitter = mitt()
app.config.globalProperties.emitter = emitter

// 注册自定义指令，用于处理点击事件冒泡
app.directive('stop-propagation', {
  mounted(el) {
    // 处理所有可能的交互事件，但跳过导航相关操作
    const events = ['click', 'mousedown', 'mouseup', 'touchstart', 'touchend'];
    
    el._eventHandlers = {};
    
    events.forEach(event => {
      el._eventHandlers[event] = function(e) {
        // 检查目标元素是否为导航链接或包含在导航链接中
        const isNavLink = e.target.closest('a') || e.target.closest('.el-menu-item');
        
        // 如果不是导航元素，才阻止冒泡
        if (!isNavLink && e && typeof e.stopPropagation === 'function') {
          e.stopPropagation();
        }
      };
      el.addEventListener(event, el._eventHandlers[event]);
    });
  },
  beforeUnmount(el) {
    // 移除所有事件监听器
    if (el._eventHandlers) {
      Object.keys(el._eventHandlers).forEach(event => {
        el.removeEventListener(event, el._eventHandlers[event]);
      });
      delete el._eventHandlers;
    }
  }
})

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册自定义图标组件
registerCustomIcons(app)

// 使用插件
app.use(store)
app.use(router)
app.use(ElementPlus, { 
  size: 'default', 
  zIndex: 3000,
  dropdown: {
    teleported: true,
    placement: 'bottom-end',
    popperOptions: {
      modifiers: [
        {
          name: 'preventOverflow',
          options: {
            boundariesElement: 'viewport'
          }
        }
      ]
    }
  }
})

// 挂载应用
app.mount('#app') 
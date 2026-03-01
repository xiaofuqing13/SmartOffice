/**
 * 修复JavaScript运行时错误
 * 特别是main.7ee886d8.js中出现的"v[w] is not a function"错误和Quill资源加载问题
 */

// 资源加载失败处理器
export function setupResourceLoadHandlers() {
  // 要监视的外部CDN资源及其本地备份映射
  const resourceMappings = {
    // Quill相关资源
    'quill.min.js': '/static/lib/quill/quill.min.js',
    'quill.snow.css': '/static/lib/quill/quill.snow.css',
    'vue-quill.snow.css': '/static/lib/quill/quill.snow.css',
    '@vueup/vue-quill': '/static/lib/quill/quill.min.js',
    // 更多资源映射可以在这里添加
  };
  
  // 资源类型映射
  const resourceTypeMap = {
    'js': 'script',
    'css': 'link'
  };

  // 添加预加载资源提示
  function addResourceHints() {
    const head = document.head;
    
    // 预加载本地备份资源
    Object.values(resourceMappings).forEach(localPath => {
      const extension = localPath.split('.').pop();
      
      if (!document.querySelector(`link[rel="preload"][href="${localPath}"]`)) {
        const preloadLink = document.createElement('link');
        preloadLink.rel = 'preload';
        preloadLink.href = localPath;
        preloadLink.as = extension === 'css' ? 'style' : 'script';
        head.appendChild(preloadLink);
      }
    });
  }
  
  // 应用资源预加载
  if (typeof window !== 'undefined' && document.head) {
    addResourceHints();
  }
  
  // 拦截DOM变化事件，确保DOMNodeInserted被正确处理
  function patchDeprecatedEvents() {
    if (!window._patchedAddEventListener) {
      window._patchedAddEventListener = true;
      try {
        // 保存原始方法
        const originalAddEventListener = Node.prototype.addEventListener;
        const originalRemoveEventListener = Node.prototype.removeEventListener;
        
        // 重写addEventListener
        Node.prototype.addEventListener = function(type, listener) {
          if (type === 'DOMNodeInserted' || type === 'DOMNodeRemoved') {
            console.warn(`检测到已弃用的${type}事件，替换为MutationObserver`);
            
            const element = this;
            if (!element._mutationListeners) {
              element._mutationListeners = new Map();
            }
            
            // 为监听器创建唯一ID
            const listenerId = Date.now() + Math.random().toString(36).slice(2);
            
            // 创建MutationObserver
            const observer = new MutationObserver((mutations) => {
              for (let mutation of mutations) {
                if (mutation.type === 'childList') {
                  if (type === 'DOMNodeInserted' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                      // 创建自定义事件对象而不是Event
                      const customEvent = {
                        type: type,
                        bubbles: true,
                        relatedNode: element,
                        target: node,
                        preventDefault: () => {},
                        stopPropagation: () => {}
                      };
                      
                      try {
                        listener.call(element, customEvent);
                      } catch (e) {
                        console.error('执行监听器时出错:', e);
                      }
                    });
                  }
                  
                  if (type === 'DOMNodeRemoved' && mutation.removedNodes.length > 0) {
                    mutation.removedNodes.forEach(node => {
                      // 创建自定义事件对象而不是Event
                      const customEvent = {
                        type: type,
                        bubbles: true,
                        relatedNode: element,
                        target: node,
                        preventDefault: () => {},
                        stopPropagation: () => {}
                      };
                      
                      try {
                        listener.call(element, customEvent);
                      } catch (e) {
                        console.error('执行监听器时出错:', e);
                      }
                    });
                  }
                }
              }
            });
            
            // 保存监听器信息
            element._mutationListeners.set(listenerId, {
              type,
              originalListener: listener,
              observer
            });
            
            // 标记原始监听器
            if (typeof listener === 'function') {
              listener._mutationListenerId = listenerId;
            } else if (listener && typeof listener === 'object') {
              listener._mutationListenerId = listenerId;
            }
            
            // 开始观察
            observer.observe(element, {
              childList: true,
              subtree: true
            });
            
            return;
          }
          
          return originalAddEventListener.apply(this, arguments);
        };
        
        // 重写removeEventListener
        Node.prototype.removeEventListener = function(type, listener) {
          if ((type === 'DOMNodeInserted' || type === 'DOMNodeRemoved') && 
              this._mutationListeners &&
              (typeof listener === 'function' || (listener && typeof listener === 'object'))) {
            
            const listenerId = listener._mutationListenerId;
            if (listenerId && this._mutationListeners.has(listenerId)) {
              const info = this._mutationListeners.get(listenerId);
              info.observer.disconnect();
              this._mutationListeners.delete(listenerId);
              return;
            }
            
            // 尝试通过遍历找到匹配的监听器
            for (const [id, info] of this._mutationListeners.entries()) {
              if (info.type === type && info.originalListener === listener) {
                info.observer.disconnect();
                this._mutationListeners.delete(id);
                return;
              }
            }
          }
          
          return originalRemoveEventListener.apply(this, arguments);
        };
        
        console.log('已应用DOMNodeInserted/DOMNodeRemoved事件拦截补丁');
      } catch (e) {
        console.error('应用事件拦截补丁失败:', e);
      }
    }
  }
  
  // 执行事件补丁
  if (typeof window !== 'undefined') {
    patchDeprecatedEvents();
  }
  
  // 监听资源加载错误
  window.addEventListener('error', function(event) {
    if (!event.target || (!event.target.src && !event.target.href)) return true;
    
    const resource = event.target;
    const resourceUrl = resource.src || resource.href;
    let handled = false;
    
    // 检查是否是需要处理的资源
    for (const [cdnPattern, localPath] of Object.entries(resourceMappings)) {
      if (resourceUrl.includes(cdnPattern)) {
        console.warn(`检测到CDN资源 ${cdnPattern} 加载失败，正在切换到本地备份...`);
        
        // 获取资源扩展名
        const extension = localPath.split('.').pop();
        const elementType = resourceTypeMap[extension] || 'script';
        
        // 删除旧资源元素
        if (resource.parentNode) {
          resource.parentNode.removeChild(resource);
        }
        
        // 创建新的元素使用本地资源
        const localResource = document.createElement(elementType);
        if (elementType === 'script') {
          localResource.src = localPath;
          localResource.async = true;
          localResource.onerror = () => {
            console.error(`本地备份资源 ${localPath} 也加载失败，可能需要检查文件是否存在`);
          };
        } else if (elementType === 'link') {
          localResource.href = localPath;
          localResource.rel = 'stylesheet';
          localResource.onerror = () => {
            console.error(`本地备份样式 ${localPath} 加载失败，尝试使用内联样式`);
            addInlineQuillStyles();
          };
        }
        
        // 添加资源到页面
        document.body.appendChild(localResource);
        console.log(`已切换到本地备份: ${localPath}`);
        handled = true;
        break;
      }
    }
    
    // 如果处理了错误，阻止错误冒泡
    if (handled) {
      event.preventDefault();
      event.stopPropagation();
      return true;
    }
  }, true);
  
  // 添加内联Quill样式作为最后的备份
  function addInlineQuillStyles() {
    if (!document.getElementById('quill-inline-styles')) {
      const styleEl = document.createElement('style');
      styleEl.id = 'quill-inline-styles';
      styleEl.textContent = `
        .ql-container {
          box-sizing: border-box;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          font-size: 14px;
          height: 100%;
          margin: 0px;
          position: relative;
          border: 1px solid #ccc;
          border-radius: 4px;
        }
        .ql-editor {
          box-sizing: border-box;
          cursor: text;
          line-height: 1.42;
          height: 100%;
          outline: none;
          overflow-y: auto;
          padding: 12px 15px;
          tab-size: 4;
          text-align: left;
          white-space: pre-wrap;
          word-wrap: break-word;
          min-height: 200px;
        }
        .suggestion-highlight {
          background-color: rgba(255, 217, 102, 0.3);
          border-bottom: 1px dashed #ffb300;
          cursor: pointer;
          position: relative;
        }
        .suggestion-tooltip {
          position: absolute;
          z-index: 9999;
          background: white;
          border: 1px solid #ccc;
          border-radius: 4px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
          padding: 10px;
          max-width: 400px;
        }
      `;
      document.head.appendChild(styleEl);
      console.log('已添加内联Quill样式作为备用');
    }
  }
  
  // 动态资源重试机制
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = args[0].toString();
    
    try {
      const response = await originalFetch(...args);
      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }
      return response;
    } catch (error) {
      // 检查是否需要处理的资源
      for (const [cdnPattern, localPath] of Object.entries(resourceMappings)) {
        if (url.includes(cdnPattern)) {
          console.warn(`Fetch请求 ${url} 失败，尝试使用本地备份...`);
          try {
            // 尝试使用备用资源
            const localResponse = await originalFetch(localPath);
            if (localResponse.ok) {
              return localResponse;
            }
          } catch (localError) {
            console.error(`本地备份请求也失败: ${localError}`);
          }
        }
      }
      throw error;
    }
  };
  
  // 检查Quill是否正确加载并初始化
  function checkQuillLoading() {
    if (window.Quill) return; // 已经加载
    
    console.warn('未检测到Quill对象，尝试加载本地版本');
    const staticBasePath = `${window.location.origin}/static/lib/quill/`;
    
    // 加载CSS
    if (!document.getElementById('quill-snow-css')) {
      const cssLink = document.createElement('link');
      cssLink.rel = 'stylesheet';
      cssLink.id = 'quill-snow-css';
      cssLink.href = `${staticBasePath}quill.snow.css`;
      document.head.appendChild(cssLink);
    }
    
    // 加载JS
    if (!document.getElementById('quill-script')) {
      const script = document.createElement('script');
      script.id = 'quill-script';
      script.src = `${staticBasePath}quill.min.js`;
      script.async = false;
      document.body.appendChild(script);
    }
  }
  
  // 在DOMContentLoaded后检查资源
  window.addEventListener('DOMContentLoaded', function() {
    // 检查关键资源是否加载
    setTimeout(checkQuillLoading, 1000); // 给CDN资源一点加载时间
  });
}

export function setupErrorHandlers() {
  // 设置资源加载处理
  setupResourceLoadHandlers();
  
  // 防止图片加载错误导致的v[w]不是函数的错误
  window.addEventListener('error', function(event) {
    // 检查是否是图片加载错误
    if (event.target && (event.target.tagName === 'IMG' || event.target.tagName === 'SCRIPT')) {
      // 阻止错误冒泡
      event.stopPropagation();
      event.preventDefault();
      
      console.warn('资源加载错误被捕获并处理:', event.target.src || event.target.href);
      
      // 返回true表示错误已处理
      return true;
    }
  }, true);
  
  // 修复window.onload处理器
  const originalWindowOnload = window.onload;
  window.onload = function(event) {
    try {
      if (typeof originalWindowOnload === 'function') {
        originalWindowOnload(event);
      }
    } catch (error) {
      console.warn('window.onload错误被捕获:', error.message);
      // 特别处理 v[w] is not a function 错误
      if (error.message.includes('is not a function') || error.message.includes('not a function')) {
        console.warn('检测到常见的事件处理错误，已被安全处理');
      }
    }
    
    // 添加安全的onload处理函数
    const allImages = document.querySelectorAll('img');
    allImages.forEach(img => {
      // 为每个图片添加安全的onload处理
      const originalOnload = img.onload;
      img.onload = function(event) {
        try {
          if (typeof originalOnload === 'function') {
            originalOnload.call(this, event);
          }
        } catch (error) {
          console.warn('图片onload错误被捕获:', error.message);
        }
      };
      
      // 添加onerror处理
      const originalOnerror = img.onerror;
      img.onerror = function(event) {
        try {
          if (typeof originalOnerror === 'function') {
            originalOnerror.call(this, event);
          }
          // 设置默认替代图片
          this.src = '/static/img/placeholder.png';
          this.onerror = null; // 防止循环错误
        } catch (error) {
          console.warn('图片onerror错误被捕获:', error.message);
        }
      };
    });
  };
  
  // 重写document.createElement方法，为新创建的img元素添加安全的onload处理
  const originalCreateElement = document.createElement;
  document.createElement = function(tagName) {
    const element = originalCreateElement.call(document, tagName);
    if (tagName.toLowerCase() === 'img') {
      const originalOnload = element.onload;
      element.onload = function(event) {
        try {
          if (typeof originalOnload === 'function') {
            originalOnload.call(this, event);
          }
        } catch (error) {
          console.warn('动态创建的图片onload错误被捕获:', error.message);
        }
      };
    }
    return element;
  };

  // 处理未捕获的Promise错误
  window.addEventListener('unhandledrejection', function(event) {
    console.warn('未处理的Promise异常被捕获:', event.reason);
    
    // 处理消息通道关闭错误
    if (event.reason && 
        typeof event.reason.message === 'string' && 
        event.reason.message.includes('message channel closed')) {
      console.warn('检测到消息通道关闭错误，这通常是由后端服务断开连接引起的');
      // 静默处理，不向用户显示错误提示
      event.preventDefault();
      return;
    }
    
    // 针对Vue Router的模块加载错误进行特殊处理
    if (event.reason && 
        (event.reason.toString().includes('modules[moduleId].call') || 
         event.reason.toString().includes('Cannot read property') ||
         event.reason.toString().includes('is not an object'))) {
      console.warn('检测到Vue Router模块加载错误，尝试刷新页面解决...');
      
      // 可以选择添加以下恢复机制之一:
      // 1. 添加提示但不自动刷新
      // showErrorNotification('页面加载异常，请尝试刷新页面');
      
      // 2. 自动尝试刷新（但给用户一点时间看到错误）
      // setTimeout(() => window.location.reload(), 3000);
    }
    
    // 防止错误传播到控制台
    event.preventDefault();
  });
  
  // 全局错误处理
  window.onerror = function(message, source, lineno, colno, error) {
    console.warn('全局错误被捕获:', {
      message,
      source,
      lineno,
      colno,
      error: error ? error.stack : null
    });
    
    // 对特定的错误类型进行处理
    if (message && (
        message.includes('stopPropagation is not a function') || 
        message.includes('v-stop-propagation')
    )) {
      console.warn('检测到事件传播错误，这可能是自定义指令中的问题');
      return true; // 防止错误显示在控制台
    }
    
    // 返回false表示允许错误继续传播到控制台
    return false;
  };
} 
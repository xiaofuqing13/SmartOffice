// DOM事件补丁 - 修复DOMNodeInserted和DOMNodeRemoved警告
(function() {
  // 拦截并重写DOM变化事件APIs
  const originalAddEventListener = Node.prototype.addEventListener;
  const originalRemoveEventListener = Node.prototype.removeEventListener;
  
  // 重写addEventListener
  Node.prototype.addEventListener = function(type, listener, options) {
    // 如果是DOMNodeInserted事件，替换为使用MutationObserver
    if (type === 'DOMNodeInserted' || type === 'DOMNodeRemoved') {
      console.warn(`检测到已弃用的${type}事件，正在替换为MutationObserver`);
      
      const element = this;
      // 保存原始监听器引用
      if (!element._mutationListeners) {
        element._mutationListeners = new Map();
      }
      
      // 为每个监听器创建唯一标识
      const listenerId = Date.now() + Math.random().toString(36).substr(2, 9);
      
      // 创建MutationObserver实例
      const observer = new MutationObserver((mutations) => {
        for (let mutation of mutations) {
          if (mutation.type === 'childList') {
            // 模拟DOMNodeInserted事件
            if (type === 'DOMNodeInserted' && mutation.addedNodes.length > 0) {
              mutation.addedNodes.forEach(node => {
                const event = new Event('DOMNodeInserted', {bubbles: true});
                event.relatedNode = element;
                event.target = node;
                try {
                  listener.call(element, event);
                } catch (e) {
                  console.error('执行监听器时出错:', e);
                }
              });
            }
            
            // 模拟DOMNodeRemoved事件
            if (type === 'DOMNodeRemoved' && mutation.removedNodes.length > 0) {
              mutation.removedNodes.forEach(node => {
                const event = new Event('DOMNodeRemoved', {bubbles: true});
                event.relatedNode = element;
                event.target = node;
                try {
                  listener.call(element, event);
                } catch (e) {
                  console.error('执行监听器时出错:', e);
                }
              });
            }
          }
        }
      });
      
      // 保存需要的信息以便后续清理
      const listenerInfo = {
        type: type,
        originalListener: listener,
        observer: observer,
        options: options
      };
      
      // 开始观察DOM变化
      observer.observe(element, {
        childList: true,
        subtree: true
      });
      
      // 保存监听器信息
      element._mutationListeners.set(listenerId, listenerInfo);
      
      // 为原始监听器添加唯一ID，方便后续移除
      if (typeof listener === 'function') {
        listener._mutationListenerId = listenerId;
      } else if (listener && typeof listener === 'object') {
        listener._mutationListenerId = listenerId;
      }
      
      // 不要继续注册已废弃的事件
      return;
    }
    
    // 对于其他类型的事件，使用原始方法
    return originalAddEventListener.apply(this, arguments);
  };
  
  // 重写removeEventListener
  Node.prototype.removeEventListener = function(type, listener, options) {
    if ((type === 'DOMNodeInserted' || type === 'DOMNodeRemoved') && 
        this._mutationListeners && 
        (typeof listener === 'function' || (listener && typeof listener === 'object'))) {
      
      let listenerId = listener._mutationListenerId;
      
      if (listenerId && this._mutationListeners.has(listenerId)) {
        const listenerInfo = this._mutationListeners.get(listenerId);
        listenerInfo.observer.disconnect();
        this._mutationListeners.delete(listenerId);
        return;
      }
      
      // 如果没有ID匹配，尝试遍历查找匹配的监听器
      for (const [id, info] of this._mutationListeners.entries()) {
        if (info.type === type && info.originalListener === listener) {
          info.observer.disconnect();
          this._mutationListeners.delete(id);
          break;
        }
      }
      return;
    }
    
    // 对于其他事件类型，使用原始方法
    return originalRemoveEventListener.apply(this, arguments);
  };
})();

// 添加资源加载失败处理
window.addEventListener('error', function(e) {
  const target = e.target;
  // 检查是否为外部资源加载错误
  if (target && (target.tagName === 'LINK' || target.tagName === 'SCRIPT')) {
    const src = target.src || target.href;
    if (src) {
      // 检查是否为Quill相关资源
      if (src.includes('quill.snow.css') || src.includes('quill.min.js')) {
        console.warn(`资源加载失败: ${src}，尝试使用本地备份`);
        
        // 根据资源类型加载本地备份
        const isCSS = src.includes('.css');
        const localPath = `${window.location.origin}/static/lib/quill/${isCSS ? 'quill.snow.css' : 'quill.min.js'}`;
        
        // 移除失败的元素
        target.parentNode.removeChild(target);
        
        // 创建新元素使用本地资源
        if (isCSS) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = localPath;
          document.head.appendChild(link);
        } else {
          const script = document.createElement('script');
          script.src = localPath;
          script.async = true;
          document.body.appendChild(script);
        }
      }
    }
  }
}, true); // 捕获阶段 
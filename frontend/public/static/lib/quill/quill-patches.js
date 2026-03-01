/**
 * Quill编辑器补丁 - 修复DOMNodeInserted警告、资源加载和建议显示问题
 */
(function() {
  // 全局拦截addEventListener早期补丁
  if (!window._patchedAddEventListener && !window._appliedGlobalPatch) {
    window._appliedGlobalPatch = true;
    try {
      // 这里是双保险，确保即使页面中的补丁代码没有正确执行，
      // 这个补丁仍然会拦截DOMNodeInserted事件
      const originalAddEventListener = Node.prototype.addEventListener;
      if (!Node.prototype._originalAddEventListener) {
        Node.prototype._originalAddEventListener = originalAddEventListener;
      
        Node.prototype.addEventListener = function(type, listener, options) {
          if (type === 'DOMNodeInserted' || type === 'DOMNodeRemoved') {
            console.warn(`由Quill补丁拦截已弃用的${type}事件，使用MutationObserver替代`);
            
            const element = this;
            // 使用MutationObserver
            const observer = new MutationObserver((mutations) => {
              for (let mutation of mutations) {
                if (mutation.type === 'childList') {
                  if (type === 'DOMNodeInserted' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                      // 创建合成事件
                      const event = new CustomEvent(type, {
                        bubbles: true,
                        cancelable: true
                      });
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
            
            // 开始观察变化
            observer.observe(element, {
              childList: true,
              subtree: true
            });
            
            // 保存observer供后续清理
            if (!element._domObservers) element._domObservers = new Map();
            element._domObservers.set(listener, observer);
            
            return;
          }
          
          // 使用原始方法处理其他事件类型
          return originalAddEventListener.apply(this, arguments);
        };
      }
    } catch (e) {
      console.warn('应用全局事件拦截补丁失败:', e);
    }
  }

  // 等待Quill库加载完成
  function waitForQuill(callback, maxAttempts = 20) {
    let attempts = 0;
    function checkQuill() {
      attempts++;
      if (window.Quill) {
        callback(window.Quill);
      } else if (attempts < maxAttempts) {
        setTimeout(checkQuill, 100);
      } else {
        console.warn('Quill加载超时，尝试使用备用资源');
        loadBackupResources();
      }
    }
    checkQuill();
  }
  
  // 加载备用资源
  function loadBackupResources() {
    const staticBasePath = `${window.location.origin}/static/lib/quill/`;
    
    // 检查是否已加载CSS
    if (!document.getElementById('quill-snow-css')) {
      const cssLink = document.createElement('link');
      cssLink.rel = 'stylesheet';
      cssLink.id = 'quill-snow-css';
      cssLink.href = `${staticBasePath}quill.snow.css`;
      document.head.appendChild(cssLink);
    }
    
    // 检查是否已加载脚本
    if (!window.Quill) {
      const script = document.createElement('script');
      script.id = 'quill-script';
      script.src = `${staticBasePath}quill.min.js`;
      script.async = false;
      script.onload = function() {
        console.log('本地备份Quill脚本加载成功');
        applyQuillPatches(window.Quill);
      };
      document.body.appendChild(script);
    }
  }
  
  // 增强差异比较功能
  function enhancedDiffDisplay(original, suggested) {
    if (!original || !suggested) return '';
    
    // 简单的差异比较算法
    const tokens1 = original.split(/\s+/);
    const tokens2 = suggested.split(/\s+/);
    
    const result = [];
    let i = 0, j = 0;
    
    while (i < tokens1.length && j < tokens2.length) {
      if (tokens1[i] === tokens2[j]) {
        result.push(`<span class="unchanged">${tokens2[j]}</span>`);
        i++; j++;
      } else {
        // 查找最佳匹配
        let found = false;
        for (let lookahead = 1; lookahead < 3 && i + lookahead < tokens1.length; lookahead++) {
          if (tokens1[i + lookahead] === tokens2[j]) {
            // 发现删除
            for (let k = i; k < i + lookahead; k++) {
              result.push(`<span class="deleted">${tokens1[k]}</span>`);
            }
            i += lookahead;
            found = true;
            break;
          }
        }
        
        if (!found) {
          for (let lookahead = 1; lookahead < 3 && j + lookahead < tokens2.length; lookahead++) {
            if (tokens1[i] === tokens2[j + lookahead]) {
              // 发现添加
              for (let k = j; k < j + lookahead; k++) {
                result.push(`<span class="added">${tokens2[k]}</span>`);
              }
              j += lookahead;
              found = true;
              break;
            }
          }
        }
        
        if (!found) {
          // 替换
          result.push(`<span class="replaced" title="替换: ${tokens1[i]} => ${tokens2[j]}">${tokens2[j]}</span>`);
          i++; j++;
        }
      }
    }
    
    // 处理剩余标记
    while (i < tokens1.length) {
      result.push(`<span class="deleted">${tokens1[i]}</span>`);
      i++;
    }
    
    while (j < tokens2.length) {
      result.push(`<span class="added">${tokens2[j]}</span>`);
      j++;
    }
    
    return result.join(' ');
  }

  // 添加补丁到Quill
  function applyQuillPatches(Quill) {
    console.log('应用Quill补丁...');
    
    // 添加增强差异显示功能到全局作用域
    window.enhancedDiffDisplay = enhancedDiffDisplay;
    
    // 修复DOMNodeInserted警告
    try {
      const originalMutationClass = Quill.imports['modules/mutation'];
      if (originalMutationClass) {
        console.log('正在修复Quill的Mutation模块...');
        
        // 保存原来的构造函数
        const originalInitialize = originalMutationClass.prototype.initialize;
        
        // 覆盖构造函数
        originalMutationClass.prototype.initialize = function() {
          const result = originalInitialize.apply(this, arguments);
          
          // 如果它使用了DOMNodeInserted，我们替换为MutationObserver
          if (this.observer) {
            console.log('替换为MutationObserver');
            return result;
          }
          
          // 创建一个MutationObserver来替换DOMNodeInserted事件
          this.observer = new MutationObserver((mutations) => {
            for (let mutation of mutations) {
              if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (let node of Array.from(mutation.addedNodes)) {
                  // 触发与DOMNodeInserted相同的逻辑
                  if ((this.domNode && this.domNode.contains(node)) || 
                      node === this.domNode) {
                    // 调用DOM变化的处理函数，模拟DOMNodeInserted
                    this.onNodeAddedCallback && this.onNodeAddedCallback(node);
                  }
                }
              }
            }
          });
          
          // 开始观察
          if (this.domNode) {
            this.observer.observe(this.domNode, {
              childList: true,
              subtree: true
            });
          }
          
          return result;
        };
        
        // 保存原来的闭包函数
        const originalClose = originalMutationClass.prototype.close || function() {};
        
        // 覆盖闭包函数以断开MutationObserver
        originalMutationClass.prototype.close = function() {
          if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
          }
          return originalClose.apply(this, arguments);
        };
      }
    } catch (e) {
      console.warn('修复Quill的Mutation模块失败:', e);
    }
    
    // 增强SuggestionBlot以确保前后对比正常工作
    try {
      // 注册自定义格式处理器
      const Inline = Quill.import('blots/inline');
      
      // 使用window全局变量避免重复注册和命名冲突
      if (!window.SuggestionBlotClass) {
        class SuggestionBlot extends Inline {
          static create(value) {
            const node = super.create();
            
            // 确保所有必要的属性都被正确设置
            if (typeof value === 'object') {
              for (const key in value) {
                node.setAttribute(`data-${key}`, typeof value[key] === 'object' ? 
                  JSON.stringify(value[key]) : String(value[key]));
              }
            }
            
            // 添加明显的视觉提示
            node.style.backgroundColor = 'rgba(255, 217, 102, 0.3)';
            node.style.borderBottom = '1px dashed #ffb300';
            node.style.cursor = 'pointer';
            node.style.padding = '0 2px';
            node.title = '点击查看建议';
            
            return node;
          }
          
          static formats(node) {
            const result = {};
            const attributes = node.attributes;
            
            for (let i = 0; i < attributes.length; i++) {
              const attr = attributes[i];
              if (attr.name.startsWith('data-')) {
                const name = attr.name.slice(5); // 去除'data-'前缀
                result[name] = attr.value;
              }
            }
            
            return result;
          }
        }
        
        SuggestionBlot.blotName = 'suggestion';
        SuggestionBlot.tagName = 'SPAN';
        SuggestionBlot.className = 'suggestion-highlight';
        
        // 存储到window上，以便其他地方可以检查是否已定义
        window.SuggestionBlotClass = SuggestionBlot;
        
        // 注册到Quill
        Quill.register(SuggestionBlot);
      } else {
        console.log('SuggestionBlot已被注册，跳过重复注册');
      }
      
      // 添加自定义CSS
      if (!document.getElementById('suggestion-styles')) {
        const styleElem = document.createElement('style');
        styleElem.id = 'suggestion-styles';
        styleElem.textContent = `
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
          .suggestion-tooltip-header {
            font-weight: bold;
            margin-bottom: 5px;
            padding-bottom: 5px;
            border-bottom: 1px solid #eee;
          }
          .suggestion-diff .deleted {
            background-color: #ffd0d0;
            text-decoration: line-through;
            color: #c00;
          }
          .suggestion-diff .added {
            background-color: #d0ffd0;
            color: #0a0;
          }
          .suggestion-diff .replaced {
            background-color: #ffffd0;
            border-bottom: 1px dotted #999;
          }
          .suggestion-actions {
            margin-top: 10px;
            text-align: right;
          }
          .suggestion-actions button {
            margin-left: 5px;
            padding: 3px 8px;
            cursor: pointer;
          }
          .btn-adopt {
            background: #4caf50;
            color: white;
            border: none;
            border-radius: 3px;
          }
          .btn-ignore {
            background: #f5f5f5;
            color: #333;
            border: 1px solid #ccc;
            border-radius: 3px;
          }
        `;
        document.head.appendChild(styleElem);
      }
    } catch (e) {
      console.warn('增强SuggestionBlot失败:', e);
    }
    
    console.log('Quill补丁应用完成');
  }
  
  // 检测资源加载失败并切换到本地资源
  function setupResourceFailover() {
    window.addEventListener('error', function(e) {
      const target = e.target;
      // 检查是否为外部资源加载错误
      if (target && (target.tagName === 'LINK' || target.tagName === 'SCRIPT')) {
        const src = target.src || target.href;
        if (src) {
          // 检查是否为Quill相关资源
          if (src.includes('quill') && !src.includes('/static/lib/quill/')) {
            console.warn(`资源加载失败: ${src}，尝试使用本地备份`);
            loadBackupResources();
          }
        }
      }
    }, true); // 捕获阶段
  }

  // 执行启动程序
  setupResourceFailover();
  waitForQuill(applyQuillPatches);
})(); 
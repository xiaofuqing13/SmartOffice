<template>
  <div class="settings-panel">
    <div class="settings-header">
      <h2>系统设置</h2>
      <div class="settings-actions">
        <el-button @click="restoreDefaults" type="link">
          <el-icon><Refresh /></el-icon> 恢复默认
        </el-button>
        <el-button @click="saveSettings" type="primary">
          <el-icon><Check /></el-icon> 保存设置
        </el-button>
      </div>
    </div>

    <div class="settings-content">
      <el-menu class="settings-sidebar" :default-active="activeSection">
        <el-menu-item index="ai" @click="activeSection = 'ai'">
          <el-icon><Setting /></el-icon>
          <span>个性化AI设置</span>
        </el-menu-item>
        <el-menu-item index="ui" @click="activeSection = 'ui'">
          <el-icon><Brush /></el-icon>
          <span>界面偏好</span>
        </el-menu-item>
      </el-menu>

      <div class="settings-main">
        <!-- 主题设置 -->
        <div v-if="activeSection === 'ui'" class="settings-section">
          <h3>主题设置</h3>
          
          <div class="setting-item">
            <span class="setting-label">主题模式</span>
            <el-radio-group v-model="settings.theme" size="large">
              <el-radio-button label="light">
                <el-icon><Sunny /></el-icon> 浅色
              </el-radio-button>
              <el-radio-button label="dark">
                <el-icon><Moon /></el-icon> 深色
              </el-radio-button>
            </el-radio-group>
          </div>

          <h3>布局设置</h3>
          
          <div class="setting-item">
            <span class="setting-label">内容密度</span>
            <el-radio-group v-model="settings.density" size="large">
              <el-radio-button label="compact">紧凑</el-radio-button>
              <el-radio-button label="standard">标准</el-radio-button>
              <el-radio-button label="comfortable">宽松</el-radio-button>
            </el-radio-group>
          </div>

          <div class="setting-item">
            <span class="setting-label">字体大小</span>
            <div class="font-size-slider">
              <el-slider 
                v-model="settings.fontSize" 
                :min="12" 
                :max="20" 
                :step="1" 
                show-input
                :format-tooltip="value => `${value}px`"
              ></el-slider>
            </div>
          </div>
        </div>

        <!-- AI设置部分 -->
        <div v-if="activeSection === 'ai'" class="settings-section">
          <h3>个性化AI设置</h3>
          <el-form label-position="top" :model="aiSettings">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item>
                  <template #label>
                    <span class="label-with-icon">
                      AI如何称呼您
                      <el-tooltip
                        effect="light"
                        content="您希望AI助手如何称呼您，例如您的姓名或昵称。"
                        placement="top"
                      >
                        <template #trigger>
                          <span class="info-icon-wrapper">
                            <el-icon class="info-icon"><info-filled /></el-icon>
                          </span>
                        </template>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-input 
                    v-model="aiSettings.nickname" 
                    placeholder="例如：李经理"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item>
                  <template #label>
                    <span class="label-with-icon">
                      您的职位
                      <el-tooltip
                        effect="light"
                        content="您的职位信息有助于AI在生成内容时更贴合您的专业领域。"
                        placement="top"
                      >
                        <template #trigger>
                          <span class="info-icon-wrapper">
                            <el-icon class="info-icon"><info-filled /></el-icon>
                          </span>
                        </template>
                      </el-tooltip>
                    </span>
                  </template>
                  <el-input 
                    v-model="aiSettings.job" 
                    placeholder="例如：软件工程师"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item>
              <template #label>
                <span class="label-with-icon">
                  AI沟通风格
                  <el-tooltip
                    effect="light"
                    content="选择您偏好的AI沟通风格，或在下方文本框中自定义。"
                    placement="top"
                  >
                    <template #trigger>
                      <span class="info-icon-wrapper">
                        <el-icon class="info-icon"><info-filled /></el-icon>
                      </span>
                    </template>
                  </el-tooltip>
                </span>
              </template>
              <el-radio-group v-model="aiSettings.tone">
                <el-radio-button label="professional">专业严谨</el-radio-button>
                <el-radio-button label="friendly">亲切友好</el-radio-button>
                <el-radio-button label="concise">简洁直接</el-radio-button>
                <el-radio-button label="custom">自定义</el-radio-button>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item v-if="aiSettings.tone === 'custom'">
              <template #label>
                <span class="label-with-icon">
                  自定义AI风格
                  <el-tooltip
                    effect="light"
                    content='在这里输入您希望AI具备的其它沟通风格或特征，例如"幽默"、"详细"等，多个词语请用逗号隔开。'
                    placement="top"
                  >
                    <template #trigger>
                      <span class="info-icon-wrapper">
                        <el-icon class="info-icon"><info-filled /></el-icon>
                      </span>
                    </template>
                  </el-tooltip>
                </span>
              </template>
              <el-input 
                type="textarea" 
                v-model="aiSettings.traitsText" 
                placeholder="例如：富有创造力, 善于总结" 
                :rows="3"
                class="textarea-input"
              />
            </el-form-item>
            
            <el-form-item>
              <template #label>
                <span class="label-with-icon">
                  其它自定义信息
                  <el-tooltip
                    effect="light"
                    content="您可以在此提供更多关于您的工作内容、兴趣偏好或特定要求的信息，以便AI为您提供更个性化的服务。"
                    placement="top"
                  >
                    <template #trigger>
                      <span class="info-icon-wrapper">
                        <el-icon class="info-icon"><info-filled /></el-icon>
                      </span>
                    </template>
                  </el-tooltip>
                </span>
              </template>
              <el-input 
                type="textarea" 
                v-model="aiSettings.otherInfo" 
                placeholder="例如：我主要负责XX项目的管理，请在总结时突出项目进度和风险点。" 
                :rows="4"
                class="textarea-input"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Refresh, Check, Setting, Brush, Sunny, Moon, InfoFilled } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { ElMessage } from 'element-plus';

export default {
  name: 'ThemeSettings',
  components: {
    Refresh, 
    Check, 
    Setting, 
    Brush, 
    Sunny, 
    Moon,
    InfoFilled
  },
  data() {
    return {
      activeSection: 'ui',
      settings: {
        theme: localStorage.getItem('theme') || 'light',
        density: localStorage.getItem('density') || 'standard',
        fontSize: parseInt(localStorage.getItem('fontSize')) || 14
      },
      aiSettings: {
        nickname: '',
        job: '',
        tone: 'professional',
        traitsText: '',
        otherInfo: ''
      },
      defaultSettings: {
        theme: 'light',
        density: 'standard',
        fontSize: 14
      },
      defaultAiSettings: {
        nickname: '',
        job: '',
        tone: 'professional',
        traitsText: '',
        otherInfo: ''
      }
    }
  },
  created() {
    this.loadAiSettings();
  },
  watch: {
    'settings.theme': {
      handler(newVal) {
        this.applyTheme(newVal);
      },
      immediate: true
    },
    'settings.fontSize': {
      handler(newVal) {
        document.documentElement.style.setProperty('--font-size-base', `${newVal}px`);
        localStorage.setItem('fontSize', newVal);
      },
      immediate: true
    },
    'settings.density': {
      handler(newVal) {
        document.body.setAttribute('data-density', newVal);
        localStorage.setItem('density', newVal);
      },
      immediate: true
    }
  },
  methods: {
    async loadAiSettings() {
      try {
        const response = await request({
          url: '/api/settings/ai-settings',
          method: 'get'
        });
        if (response && response.success) {
          this.aiSettings = {
            nickname: response.data.nickname || '',
            job: response.data.job || '',
            tone: response.data.tone || 'professional',
            traitsText: response.data.traits_text || '',
            otherInfo: response.data.other_info || ''
          };
        }
      } catch (error) {
        console.error('获取AI设置失败:', error);
      }
    },
    async saveAiSettings() {
      try {
        const payload = {
          nickname: this.aiSettings.nickname,
          job: this.aiSettings.job,
          tone: this.aiSettings.tone,
          traits_text: this.aiSettings.traitsText,
          other_info: this.aiSettings.otherInfo,
        };
        await request({
          url: '/api/settings/ai-settings',
          method: 'post',
          data: payload
        });
        // 保存成功后不显示消息，由 saveSettings 统一处理
      } catch (error) {
        console.error('保存AI设置失败:', error);
        throw new Error('保存AI设置失败');
      }
    },
    applyTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
      
      // 更新meta主题色
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#ffffff');
      }
    },
    async saveSettings() {
      try {
        // 保存UI设置到localStorage
        localStorage.setItem('theme', this.settings.theme);
        localStorage.setItem('density', this.settings.density);
        localStorage.setItem('fontSize', this.settings.fontSize);
        
        // 保存AI设置到数据库
        if (this.activeSection === 'ai') {
          await this.saveAiSettings();
        }
        
        // 应用UI设置
        this.applyTheme(this.settings.theme);
        document.body.setAttribute('data-density', this.settings.density);
        document.documentElement.style.setProperty('--font-size-base', `${this.settings.fontSize}px`);
        
        // 统一通知用户
        ElMessage({
          message: '设置已保存',
          type: 'success'
        });
        
        // 关闭设置面板
        this.$emit('close');
      } catch (error) {
        ElMessage({
          message: error.message || '保存失败',
          type: 'error'
        });
      }
    },
    restoreDefaults() {
      // 根据当前活动的设置部分重置相应设置
      if (this.activeSection === 'ui') {
        this.settings = JSON.parse(JSON.stringify(this.defaultSettings));
      } else if (this.activeSection === 'ai') {
        this.aiSettings = JSON.parse(JSON.stringify(this.defaultAiSettings));
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.settings-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  color: var(--text-color);
  
  .settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    
    h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
    }
    
    .settings-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .settings-content {
    display: flex;
    flex: 1;
    overflow: hidden;
    
    .settings-sidebar {
      width: 200px;
      border-right: 1px solid var(--border-color);
    }
    
    .settings-main {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      
      .settings-section {
        margin-bottom: 24px;
        
        h3 {
          font-size: 16px;
          font-weight: 500;
          margin-top: 0;
          margin-bottom: 16px;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--border-color);
        }
      }
      
      .setting-item {
        margin-bottom: 20px;
        
        .setting-label {
          display: block;
          font-size: 14px;
          margin-bottom: 8px;
        }
        
        .font-size-slider {
          margin-top: 10px;
        }
      }
    }
  }
}

:deep(.el-menu) {
  background-color: transparent;
  border-right: none;
}

:deep(.el-menu-item) {
  color: var(--text-color);
  
  &:hover {
    background-color: var(--hover-color);
  }
  
  &.is-active {
    background-color: var(--hover-color);
    color: var(--primary-color);
  }
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  box-shadow: -1px 0 0 0 var(--primary-color);
}

:deep(.el-slider__runway) {
  background-color: var(--slider-bg);
}

:deep(.el-slider__bar) {
  background-color: var(--primary-color);
}

:deep(.el-slider__button) {
  border-color: var(--primary-color);
}

/* 添加信息图标和提示文本的样式 */
.label-with-icon {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-icon {
  font-size: 16px;
  color: #909399;
  cursor: help;
  transition: all 0.3s;
}

.info-icon:hover {
  color: var(--primary-color);
}

/* 表单项样式 */
:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-tooltip__trigger) {
  display: inline-flex;
}

:deep(.el-tooltip__popper) {
  max-width: 300px;
  z-index: 9999;
}

.info-icon-wrapper {
  display: inline-flex;
  align-items: center;
}

/* 文本区域样式 */
.textarea-input {
  width: 100%;
}

:deep(.el-textarea__inner) {
  font-family: var(--font-family);
}

/* 单选按钮组样式 */
:deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style> 
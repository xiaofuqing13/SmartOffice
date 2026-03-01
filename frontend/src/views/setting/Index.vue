<template>
  <div>
    <!-- 右上角设置按钮 -->
    <el-popover
      placement="bottom"
      :width="120"
      trigger="click"
    >
      <template #reference>
        <div class="settings-button">
          <i class="el-icon-setting"></i>
        </div>
      </template>
      <div class="settings-menu">
        <div class="menu-item" @click="openSettings">系统设置</div>
        <div class="menu-item">帮助中心</div>
        <div class="menu-divider"></div>
        <div class="menu-item">退出登录</div>
      </div>
    </el-popover>
    
    <!-- 设置弹窗 -->
    <el-dialog
      title="系统设置"
      v-model="dialogVisible"
      width="800px"
      :before-close="handleClose"
      :close-on-click-modal="false"
      custom-class="settings-dialog"
      destroy-on-close
    >
      <div class="settings-container">
        <!-- 左侧导航 -->
        <div class="settings-nav">
          <div 
            class="nav-item" 
            :class="{ active: activeTab === 'ai' }" 
            @click="activeTab = 'ai'"
          >
            <i class="el-icon-cpu"></i>
            <span>个性化AI设置</span>
          </div>
          <div 
            class="nav-item" 
            :class="{ active: activeTab === 'ui' }" 
            @click="activeTab = 'ui'"
          >
            <i class="el-icon-brush"></i>
            <span>界面偏好</span>
          </div>
        </div>
        
        <!-- 右侧内容 -->
        <div class="settings-content">
          <!-- 统一的操作按钮区 -->
          <div class="global-action-bar">
            <el-popconfirm
              :title="`确定要恢复${activeTab === 'ai' ? '个性化AI设置' : '界面偏好'}的默认设置吗？`"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="resetCurrentSettings"
            >
              <template #reference>
                <el-button>
                  <el-icon><refresh-left /></el-icon>
                  恢复默认
                </el-button>
              </template>
            </el-popconfirm>
            <el-button type="primary" @click="saveCurrentSettings">
              <el-icon><check /></el-icon>
              保存设置
            </el-button>
          </div>
          
          <!-- 个性化AI设置 -->
          <div v-if="activeTab === 'ai'" class="setting-section">
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
                          <el-icon class="info-icon"><info-filled /></el-icon>
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
                          <el-icon class="info-icon"><info-filled /></el-icon>
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
                      <el-icon class="info-icon"><info-filled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-radio-group v-model="aiSettings.tone" class="tone-radios">
                  <el-radio-button label="professional">专业严谨</el-radio-button>
                  <el-radio-button label="friendly">亲切友好</el-radio-button>
                  <el-radio-button label="concise">简洁直接</el-radio-button>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item>
                <template #label>
                  <span class="label-with-icon">
                    自定义AI风格
                    <el-tooltip
                      effect="light"
                      content='在这里输入您希望AI具备的其它沟通风格或特征，例如"幽默"、"详细"等，多个词语请用逗号隔开。'
                      placement="top"
                    >
                      <el-icon class="info-icon"><info-filled /></el-icon>
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
                      <el-icon class="info-icon"><info-filled /></el-icon>
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
          
          <!-- 界面偏好设置 -->
          <div v-if="activeTab === 'ui'" class="setting-section">
            <h3>主题设置</h3>
            <el-form label-position="left" label-width="120px">
              <el-form-item label="主题模式">
                <el-radio-group v-model="uiSettings.theme">
                  <el-radio label="light">浅色</el-radio>
                  <el-radio label="dark">深色</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
            
            <h3>布局设置</h3>
            <el-form label-position="left" label-width="120px">
              <el-form-item label="内容密度">
                <el-radio-group v-model="uiSettings.contentDensity">
                  <el-radio label="compact">紧凑</el-radio>
                  <el-radio label="normal">标准</el-radio>
                  <el-radio label="comfortable">宽松</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="字体大小">
                <el-slider v-model="uiSettings.fontSize" :min="12" :max="20" :step="1" show-stops></el-slider>
                <span class="description">{{ uiSettings.fontSize }}px</span>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { InfoFilled, RefreshLeft as RefreshLeftIcon, Check as CheckIcon } from '@element-plus/icons-vue'

export default {
  name: 'Setting',
  components: {
    InfoFilled,
    'refresh-left': RefreshLeftIcon,
    'check': CheckIcon
  },
  data() {
    return {
      dialogVisible: false,
      activeTab: 'ai',
      aiSettings: {
        nickname: '',
        job: '',
        tone: 'professional',
        traitsText: '',
        otherInfo: ''
      },
      uiSettings: {
        theme: 'light',
        contentDensity: 'normal',
        fontSize: 14
      }
    }
  },
  mounted() {
    // 只在需要时获取设置
    if (this.dialogVisible) {
      this.fetchUiSettings()
      this.fetchAiSettings()
    }
    // 添加处理弹窗显示的事件监听
    document.addEventListener('keydown', this.handleKeyDown)
  },
  beforeUnmount() {
    // 组件销毁前清理事件监听
    document.removeEventListener('keydown', this.handleKeyDown)
  },
  methods: {
    // 消息提示封装，避免直接依赖this.$message
    showMessage(type, message) {
      try {
        // 尝试使用Element Plus的消息组件
        ElMessage({
          type,
          message
        })
      } catch (error) {
        // 备用方案：使用console记录消息
        console.log(`[${type}] ${message}`)
      }
    },
    // 暴露给父组件的方法，用于打开设置弹窗
    openSettings() {
      try {
        console.log('设置弹窗被打开')
        this.dialogVisible = true
        // 打开弹窗时获取设置
        this.fetchUiSettings()
        this.fetchAiSettings()
      } catch (error) {
        console.error('打开设置弹窗失败:', error)
        // 确保即使出错也不会阻塞用户界面
      }
    },
    handleKeyDown(e) {
      // ESC键关闭弹窗
      if (e.key === 'Escape' && this.dialogVisible) {
        this.dialogVisible = false
      }
    },
    handleClose() {
      this.dialogVisible = false
    },
    async fetchUiSettings() {
      try {
        // 使用request实用程序自动携带认证
        const response = await request({
          url: '/api/settings/ui-preferences',
          method: 'get'
        })
        
        if (response && response.success) {
          this.uiSettings = { ...this.uiSettings, ...response.data }
        }
      } catch (error) {
        console.error('获取界面偏好失败:', error)
        // 更友好的错误消息，不要暴露403错误
        this.showMessage('info', '首次使用系统，暂无偏好设置')
      }
    },
    async fetchAiSettings() {
      try {
        // 获取个性化AI设置
        const response = await request({
          url: '/api/settings/ai-settings',
          method: 'get'
        })
        
        if (response && response.success) {
          // 将API返回的字段映射到本地状态
          this.aiSettings = {
            nickname: response.data.nickname || '',
            job: response.data.job || '',
            tone: response.data.tone || 'professional',
            traitsText: response.data.traits_text || '',
            otherInfo: response.data.other_info || ''
          }
        }
      } catch (error) {
        console.error('获取个性化AI设置失败:', error)
        this.showMessage('info', '首次使用系统，暂无个性化AI设置')
      }
    },
    async saveAiSettings() {
      try {
        // 构建请求数据，将本地字段映射为API所需格式
        const requestData = {
          nickname: this.aiSettings.nickname,
          job: this.aiSettings.job,
          tone: this.aiSettings.tone,
          traits_text: this.aiSettings.traitsText,
          other_info: this.aiSettings.otherInfo
        }
        
        // 保存个性化AI设置
        const response = await request({
          url: '/api/settings/ai-settings',
          method: 'post',
          data: requestData
        })
        
        if (response && response.success) {
          this.showMessage('success', '个性化AI设置已保存')
          this.dialogVisible = false
        } else {
          const errorMsg = (response && response.message) || '保存失败'
          this.showMessage('error', errorMsg)
        }
      } catch (error) {
        console.error('保存个性化AI设置失败:', error)
        this.showMessage('error', '保存设置信息失败')
      }
    },
    resetAiSettings() {
      this.aiSettings = {
        nickname: '',
        job: '',
        tone: 'professional',
        traitsText: '',
        otherInfo: ''
      }
      this.showMessage('info', '已重置个性化AI设置')
    },
    async saveUiSettings() {
      try {
        // 使用request实用程序自动携带认证
        const response = await request({
          url: '/api/settings/ui-preferences',
          method: 'post',
          data: this.uiSettings
        })
        
        if (response && response.success) {
          this.showMessage('success', '界面偏好设置已保存')
          // 应用新的主题设置
          this.applyTheme()
          this.dialogVisible = false
        } else {
          const errorMsg = (response && response.message) || '保存失败'
          this.showMessage('error', errorMsg)
        }
      } catch (error) {
        console.error('保存界面偏好失败:', error)
        this.showMessage('error', '保存设置信息失败')
      }
    },
    resetUiSettings() {
      this.uiSettings = {
        theme: 'light',
        contentDensity: 'normal',
        fontSize: 14
      }
      this.showMessage('info', '已恢复默认设置，请点击保存生效')
    },
    applyTheme() {
      // 实际应用主题的逻辑，可以通过修改CSS变量来实现
      if (document && document.documentElement && document.documentElement.style) {
      document.documentElement.setAttribute('data-theme', this.uiSettings.theme)
      document.documentElement.style.setProperty('--font-size-base', `${this.uiSettings.fontSize}px`)
      }
    },
    // 根据当前激活的标签页重置设置
    resetCurrentSettings() {
      if (this.activeTab === 'ai') {
        this.resetAiSettings();
      } else if (this.activeTab === 'ui') {
        this.resetUiSettings();
      }
    },
    
    // 根据当前激活的标签页保存设置
    saveCurrentSettings() {
      if (this.activeTab === 'ai') {
        this.saveAiSettings();
      } else if (this.activeTab === 'ui') {
        this.saveUiSettings();
      }
    }
  }
}
</script>

<style scoped>
.settings-button {
  position: fixed;
  top: 15px;
  right: 20px;
  z-index: 999;
  cursor: pointer;
  color: #409EFF;
  font-size: 20px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s;
}

.settings-button:hover {
  background-color: rgba(64, 158, 255, 0.1);
}

.settings-menu {
  padding: 5px 0;
}

.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.menu-item:hover {
  background-color: #f5f7fa;
  color: #409EFF;
}

.menu-divider {
  height: 1px;
  background-color: #eee;
  margin: 5px 0;
}

.settings-container {
  display: flex;
  height: 500px;
}

.settings-nav {
  width: 200px;
  border-right: 1px solid #eee;
  padding: 20px 0;
}

.nav-item {
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
}

.nav-item i {
  margin-right: 10px;
  font-size: 18px;
}

.nav-item.active {
  background-color: #ecf5ff;
  color: #409EFF;
  border-right: 2px solid #409EFF;
}

.nav-item:hover:not(.active) {
  background-color: #f5f7fa;
}

.settings-content {
  flex: 1;
  padding: 20px 30px;
  overflow-y: auto;
}

.settings-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.setting-section {
  margin-bottom: 30px;
}

.setting-section h3 {
  font-size: 16px;
  font-weight: 500;
  margin: 20px 0;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.description {
  color: #909399;
  font-size: 13px;
  margin-left: 10px;
}

.setting-action {
  display: none; /* 隐藏原有的按钮区 */
}

.global-action-bar {
  display: flex;
  justify-content: flex-end;
  padding: 0 0 15px 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.global-action-bar :deep(.el-button) {
  margin-left: 10px;
  display: inline-flex;
  align-items: center;
}

.global-action-bar :deep(.el-button .el-icon) {
  margin-right: 5px;
}

.custom-input-aligned {
  width: 400px;
  max-width: 100%;
  border-radius: 4px;
}

.input-label {
  font-size: 16px;
  margin-bottom: 10px;
  color: #333;
}

.input-wrapper {
  display: flex;
}

.textarea-input :deep(.el-textarea__inner) {
  font-size: 14px;
  line-height: 1.5;
  padding: 10px 12px;
}

.label-with-icon {
  display: flex;
  align-items: center;
  gap: 5px;
}

.info-icon {
  font-size: 16px;
  color: #909399;
  cursor: pointer;
}

.info-icon:hover {
  color: #409EFF;
}
</style> 
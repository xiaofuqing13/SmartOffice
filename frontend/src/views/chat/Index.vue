<template>
  <div class="chat-container">
        <el-card class="chat-card" :body-style="{backgroundColor: 'transparent', padding: 0}">
          <div class="chat-header-actions" v-if="sessionsLoading">
            <el-alert
              title="正在加载数据..."
              type="info"
              :closable="false"
              show-icon
            />
          </div>
          <div class="chat-layout">
            <!-- 左侧联系人列表 -->
            <div class="chat-sidebar">
              <!-- 搜索框 -->
              <div class="search-box">
                <div class="search-header">
                  <el-input 
                    v-model="searchQuery" 
                    placeholder="搜索联系人..."
                    clearable
                    :prefix-icon="Search"
                  ></el-input>
                  <el-button circle size="small" @click="refreshChatSessions" title="刷新列表">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                </div>
              </div>
              
              <!-- 聊天标签页 -->
              <div class="chat-tabs">
                <div 
                  v-for="(tab, index) in tabs" 
                  :key="index"
                  class="chat-tab"
                  :class="{'active': activeTab === index}"
                  @click="activeTab = index"
                >
                  {{ tab }}
                </div>
              </div>
              
              <!-- 联系人列表 -->
              <div class="contacts-list">
                <!-- 部门分组显示 (仅在同事标签页显示) -->
                <template v-if="activeTab === 1">
                  <div v-if="!sessionsLoading && Object.keys(groupedUsersByDepartment).length > 0">
                    <div v-for="(departmentUsers, deptName) in groupedUsersByDepartment" :key="deptName" class="department-group">
                      <div class="department-header">{{ deptName }}</div>
                      <div 
                        v-for="contact in departmentUsers" 
                        :key="contact.id"
                        class="contact-item"
                        :class="{'active': selectedContact === contact.id}"
                        @click="selectContact(contact)"
                      >
                        <div class="contact-avatar">
                          <div 
                            v-if="!contact.avatar && !contact.avatar_url" 
                            class="avatar" 
                            :style="{backgroundColor: contact.color}"
                          >
                            <span class="avatar-initial">{{ contact.initial }}</span>
                          </div>
                          <img v-else :src="contact.avatar_url || contact.avatar" alt="avatar" class="avatar" />
                          <div 
                            class="contact-status" 
                            :class="'status-' + contact.status"
                          ></div>
                        </div>
                        <div class="contact-info">
                          <div class="contact-name">
                            <span>{{ contact.name }}</span>
                            <span class="time">{{ contact.lastTime }}</span>
                          </div>
                          <div class="contact-message">
                            <span>{{ contact.lastMessage }}</span>
                            <el-badge 
                              v-if="contact.unread" 
                              :value="contact.unread" 
                              class="message-badge"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div v-else-if="!sessionsLoading" class="loading-container">
                    <el-skeleton :rows="5" animated />
                  </div>
                </template>
                
                <!-- 最近聊天标签页 -->
                <template v-else>
                  <div 
                    v-for="contact in filteredContacts" 
                    :key="contact.id"
                    class="contact-item"
                    :class="{'active': selectedContact === contact.id}"
                    @click="selectContact(contact)"
                  >
                    <div class="contact-avatar">
                      <div 
                        v-if="!contact.avatar && !contact.avatar_url" 
                        class="avatar" 
                        :style="{backgroundColor: contact.color}"
                      >
                        <span class="avatar-initial">{{ contact.initial }}</span>
                      </div>
                      <img v-else :src="contact.avatar_url || contact.avatar" alt="avatar" class="avatar" />
                      <div 
                        class="contact-status" 
                        :class="'status-' + contact.status"
                      ></div>
                    </div>
                    <div class="contact-info">
                      <div class="contact-name">
                        <span>{{ contact.name }}</span>
                        <span class="time">{{ contact.lastTime }}</span>
                      </div>
                      <div class="contact-message">
                        <span>{{ contact.lastMessage }}</span>
                        <el-badge 
                          v-if="contact.unread" 
                          :value="contact.unread" 
                          class="message-badge"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <!-- 在最近聊天标签页，如果没有聊天记录，显示提示 -->
                  <div v-if="!sessionsLoading && filteredContacts.length === 0" class="empty-contacts">
                    <el-empty 
                      description="暂无联系人" 
                      :image-size="100"
                    >
                      <template #image>
                        <el-icon :size="64" class="empty-icon"><UserFilled /></el-icon>
                      </template>
                    </el-empty>
                  </div>
                </template>

                <!-- 无联系人提示 -->
                <div v-if="sessionsLoading" class="loading-container">
                  <el-skeleton :rows="5" animated />
                </div>
              </div>
            </div>
            
            <!-- 右侧聊天内容 -->
            <div class="chat-content">
              <!-- 聊天头部 -->
              <div class="chat-header" v-if="selectedContact !== null">
                <div class="contact-avatar">
                  <div 
                    v-if="!currentContact.avatar && !currentContact.avatar_url" 
                    class="avatar" 
                    :style="{backgroundColor: currentContact.color}"
                  >
                    <span class="avatar-initial">{{ currentContact.initial || '?' }}</span>
                  </div>
                  <img 
                    v-else 
                    :src="currentContact.avatar_url || currentContact.avatar" 
                    alt="avatar" 
                    class="avatar" 
                  />
                  <div 
                    class="contact-status" 
                    :class="'status-' + (currentContact.status || 'online')"
                  ></div>
                </div>
                <div class="contact-info">
              <h6>{{ currentContact.name || '未命名联系人' }}</h6>
              <p>{{ getStatusText(currentContact.status || 'online') }}</p>
                </div>
                <div class="chat-actions">
                  <el-tooltip content="AI总结" placement="bottom">
                    <el-button @click="openSummaryDialog" circle>
                      <el-icon><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-robot" viewBox="0 0 16 16">
                        <path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.22z"/>
                        <path d="M4 1.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5M12 1a2 2 0 0 1 2 2v10.5a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2zM4 0a1 1 0 0 0-1 1v10.5a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1z"/>
                      </svg></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </div>
              
              <!-- 聊天消息区域 -->
              <div class="chat-messages" v-if="selectedContact !== null" ref="messageContainer">
                <!-- 有消息时显示消息列表 -->
                <template v-if="messages.length > 0">
                  <div 
                    v-for="(message, index) in messages" 
                    :key="message.id || index"
                    class="message"
                    :class="message.sender.id === userId ? 'message-sent' : 'message-received'"
                  >
                    <div class="message-container">
                      <div v-if="message.sender.id !== userId" class="message-avatar">
                        <div 
                          v-if="!message.sender.avatar && !message.sender.avatar_url" 
                          class="avatar small" 
                          :style="{backgroundColor: getSenderColor(message.sender)}"
                        >
                          <span class="avatar-initial">{{ getSenderInitial(message.sender) }}</span>
                        </div>
                        <img 
                          v-else 
                          :src="message.sender.avatar_url || message.sender.avatar" 
                          alt="avatar" 
                          class="avatar small" 
                        />
                      </div>
                      <div class="message-content-wrapper" @contextmenu.prevent="openContextMenu($event, message)">
                        <div 
                          class="message-content"
                          :class="message.sender.id === userId ? 'sent' : 'received'"
                        >
                          <div v-if="message.message_type === 'text'" class="text-card">
                            <div class="text-card-inner">
                              {{ message.content }}
                            </div>
                          </div>
                      
                          <div v-else-if="message.message_type === 'image'" class="image-card">
                            <div class="image-card-inner">
                              <div class="image-preview" @click="toggleImageExpand(message.file)">
                                <img :src="message.file" alt="image" />
                              </div>
                            </div>
                          </div>
                      
                          <div v-else-if="message.message_type === 'file'" class="file-card" @click="downloadFile(message)">
                            <div class="file-card-inner">
                              <div class="file-icon">
                                <el-icon><Document /></el-icon>
                              </div>
                              <div class="file-info">
                                <div class="file-name">
                                  <span class="file-name-main">{{ getFileName(message.file_name) }}</span><!--
                                --><span class="file-name-ext">{{ getFileExtension(message.file_name) }}</span>
                                </div>
                                <div class="file-meta">
                                  <span class="file-size">{{ formatFileSize(message.file_size) }}</span>
                                  <span class="file-download-hint">点击下载</span>
                                </div>
                              </div>
                            </div>
                          </div>
                      
                          <div v-else-if="message.message_type === 'knowledge'" class="knowledge-card" @click="viewKnowledge(message)">
                            <div class="knowledge-card-inner">
                              <div class="knowledge-icon">
                                <el-icon><Reading /></el-icon>
                              </div>
                              <div class="knowledge-content">
                                <div class="knowledge-title">{{ message.knowledge_detail.title }}</div>
                                <div class="knowledge-desc">{{ message.knowledge_detail.description }}</div>
                                <div class="knowledge-footer">
                                  <span class="knowledge-type">{{ message.knowledge_detail.file_type }}</span>
                                  <span class="knowledge-view">查看详情</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div class="message-time">{{ formatMessageTime(message.created_at) }}</div>
                      </div>
                    </div>
                  </div>
                </template>
                
                <!-- 没有消息时显示空提示 -->
                <template v-else-if="!messagesLoading">
                  <div class="empty-messages">
                    <el-empty description="暂无消息记录">
                      <template #image>
                        <el-icon :size="64" class="empty-icon"><ChatLineSquare /></el-icon>
                      </template>
                      <p>发送第一条消息开始对话吧</p>
                    </el-empty>
                  </div>
                </template>
                
                <!-- 加载中显示骨架屏 -->
                <template v-else>
                  <div class="loading-messages">
                    <el-skeleton :rows="3" animated />
                    <el-skeleton style="margin-top: 20px" :rows="2" animated />
                    <div style="text-align: right; margin-top: 20px">
                      <el-skeleton :rows="2" animated />
                    </div>
                  </div>
                </template>
              </div>
              
              <!-- 聊天输入框 -->
              <div class="chat-input" v-if="selectedContact !== null">
                <div class="chat-tools">
                  <el-tooltip content="发送图片" placement="top">
                    <el-button circle @click="openImageUpload" :loading="imageUploading">
                      <el-icon><PictureFilled /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="发送文件" placement="top">
                    <el-button circle @click="openFileUpload" :loading="fileUploading">
                      <el-icon><FolderOpened /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <!-- <el-tooltip content="分享知识库文件" placement="top">
                    <el-button circle @click="openKnowledgeDialog">
                      <el-icon><Reading /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="语音消息" placement="top">
                    <el-button circle>
                      <el-icon><Microphone /></el-icon>
                    </el-button>
                  </el-tooltip> -->
                </div>
                <div class="input-area">
                  <el-input
                    v-model="messageInput"
                    type="textarea"
                    :rows="3"
                    placeholder="输入消息..."
                    resize="none"
                    @keyup.enter.prevent="sendMessage"
                  ></el-input>
                </div>
                <div class="send-button">
                  <el-button type="primary" @click="sendMessage">
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </div>
              </div>
              
              <!-- 无选中联系人提示 -->
              <div class="empty-chat" v-if="selectedContact === null">
                <div class="empty-illustration">
                  <el-icon :size="64"><ChatDotSquare /></el-icon>
                </div>
                <h4>选择一个联系人开始聊天</h4>
                <p>从左侧列表选择联系人开始对话</p>
              </div>
            </div>
          </div>
        </el-card>
  
  <!-- 隐藏的文件上传输入 -->
  <input 
    type="file" 
    ref="fileInput" 
    style="display: none" 
    @change="handleFileUpload" 
  />
  
  <!-- 隐藏的图片上传输入 -->
  <input 
    type="file" 
    ref="imageInput" 
    style="display: none" 
    accept="image/*" 
    @change="handleImageUpload" 
  />
  
  <!-- 知识库选择对话框 -->
  <el-dialog
    v-model="knowledgeDialogVisible"
    title="选择知识库文件"
    width="50%"
  >
    <el-table
      v-loading="knowledgeLoading"
      :data="knowledgeList"
      style="width: 100%"
      @row-click="selectKnowledge"
    >
      <el-table-column prop="title" label="标题"></el-table-column>
      <el-table-column prop="file_type" label="类型">
        <template #default="scope">
          <el-tag>{{ scope.row.file_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="primary" size="small" @click.stop="shareKnowledge(scope.row)">
            分享
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="knowledgeDialogVisible = false">取消</el-button>
      </span>
    </template>
  </el-dialog>

  <!-- AI总结对话框 -->
  <el-dialog
    v-model="summaryDialogVisible"
    title="AI 聊天总结"
    width="50%"
    @close="handleCloseSummaryDialog"
    top="5vh"
  >
    <div v-loading="summaryLoading" element-loading-text="正在生成摘要，请稍候...">
      <el-form label-position="top" style="margin-bottom: 20px;">
        <el-form-item label="选择要总结的消息时间范围">
          <el-date-picker
            v-model="summaryDateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :picker-options="pickerOptions"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <div v-if="summaryContent" class="summary-content-wrapper">
        <el-alert title="AI 总结要点" type="info" :closable="false" show-icon class="summary-title"></el-alert>
        <div class="summary-content">
          <p style="white-space: pre-wrap;">{{ summaryContent }}</p>
        </div>
      </div>
       <el-empty v-if="!summaryContent && !summaryLoading" description="暂无摘要，请选择时间范围后点击" />
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCloseSummaryDialog">关闭</el-button>
        <el-button type="primary" @click="handleSummarize" :disabled="summaryLoading">
          {{ summaryLoading ? '生成中...' : '生成摘要' }}
        </el-button>
      </span>
    </template>
  </el-dialog>

  <!-- 替换图片预览对话框为内联展示 -->
  <div class="fullscreen-image-preview" v-if="expandedImage" @click="expandedImage = null">
    <img :src="expandedImage" alt="预览图片" class="fullscreen-preview-image" />
  </div>
  
  <!-- 移除原有的图片预览对话框 -->
  <!-- <el-dialog
    v-model="imagePreviewVisible"
    :title="false"
    width="80%"
    center
    append-to-body
    :show-close="true"
    class="image-preview-dialog"
  >
    <img :src="previewImageUrl" alt="预览图片" class="preview-image" />
  </el-dialog> -->

  <!-- 聊天右键菜单 -->
  <div class="chat-context-menu" v-show="contextMenuVisible" :style="contextMenuStyle">
    <div class="context-menu-item" @click="addToCalendarFromMessage">
      <el-icon><Calendar /></el-icon>
      <span>添加到日程</span>
    </div>
    <div class="context-menu-item" @click="copyMessageContent">
      <el-icon><DocumentCopy /></el-icon>
      <span>复制内容</span>
    </div>
  </div>

  <!-- 添加日程对话框 -->
  <el-dialog
    v-model="calendarDialogVisible"
    title="添加日程"
    width="500px"
  >
    <div v-loading="isAnalyzing" element-loading-text="AI分析中...">
      <el-form :model="calendarEvent" :rules="calendarRules" ref="calendarFormRef" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="calendarEvent.title" placeholder="请输入日程标题"></el-input>
        </el-form-item>
        <el-form-item label="开始时间" prop="start">
          <el-date-picker
            v-model="calendarEvent.start"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="结束时间" prop="end">
          <el-date-picker
            v-model="calendarEvent.end"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="地点" prop="location">
          <el-input v-model="calendarEvent.location" placeholder="请输入地点"></el-input>
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="calendarEvent.type" placeholder="请选择日程类型">
            <el-option label="会议" value="blue"></el-option>
            <el-option label="出差" value="orange"></el-option>
            <el-option label="假期" value="green"></el-option>
            <el-option label="截止日期" value="red"></el-option>
            <el-option label="其他" value="purple"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提醒" prop="reminder">
          <el-select v-model="calendarEvent.reminder" placeholder="请选择提醒时间">
            <el-option label="不提醒" value="none"></el-option>
            <el-option label="10分钟前" value="10min"></el-option>
            <el-option label="30分钟前" value="30min"></el-option>
            <el-option label="1小时前" value="1hour"></el-option>
            <el-option label="1天前" value="1day"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="calendarEvent.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入描述信息"
          ></el-input>
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="calendarDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCalendarEvent" :loading="isSubmitting">确认添加</el-button>
      </div>
    </template>
  </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, 
  Refresh, 
  ChatDotSquare, 
  UserFilled, 
  ChatLineSquare,
  PictureFilled,
  FolderOpened,
  Reading,
  Microphone,
  Position,
  Document,
  Calendar,
  DocumentCopy
} from '@element-plus/icons-vue'
import { 
  getChatSessions, 
  getChatSession, 
  sendTextMessage, 
  sendImageMessage,
  sendKnowledgeMessage,
  downloadMessageFile,
  sendFileMessage,
  summarizeChat,
  analyzeForCalendar,
  createCalendarEvent
} from '@/api/chat'
import { getKnowledgeList } from '@/api/knowledge'
// eslint-disable-next-line no-unused-vars
import { formatDate } from '@/utils/date'
import request from '@/utils/request'
import { aiChatWithDocuments } from '@/api/ai'

export default {
  name: 'Chat',
  components: {
    Calendar,
    DocumentCopy
  },
  
  setup() {
    const store = useStore()
    const currentUser = computed(() => store.getters.user)
    
    // 添加本地用户数据存储
    const userInfo = ref(null)
    
    const searchQuery = ref('')
    const activeTab = ref(0)
    const selectedContact = ref(null)
    const messageInput = ref('')
    const messageContainer = ref(null)
    const fileInput = ref(null)
    const imageInput = ref(null)
    const messages = ref([])
    const sessionsLoading = ref(false)
    const messagesLoading = ref(false)
    const chatSessions = ref([])
    const currentChatId = ref(null)
    
    // 知识库相关
    const knowledgeDialogVisible = ref(false)
    const knowledgeLoading = ref(false)
    const knowledgeList = ref([])
    const selectedKnowledge = ref(null)
    
    // 标签页
    const tabs = ref(['最近聊天', '同事'])
    
    // 联系人列表
    const contacts = ref([])
    // 所有同事用户列表
    const allColleagues = ref([])
    
    // 部门列表
    const departments = ref([])
    
    // 当前选中的联系人
    const currentContact = computed(() => {
      if (selectedContact.value === null) return {}
      return contacts.value.find(c => c.id === selectedContact.value) || {}
    })
    
    // 安全地获取用户ID，避免模板中的null错误
    const userId = computed(() => {
      return userInfo.value?.id || null
    })
    
    // 根据搜索过滤联系人
    const filteredContacts = computed(() => {
      if (!searchQuery.value) return contacts.value
      return contacts.value.filter(contact =>
        contact.name.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })
    
    // 根据当前激活的标签页获取要显示的联系人
    const getActiveContacts = computed(() => {
      if (activeTab.value === 0) {
        return filteredContacts.value
      } else if (activeTab.value === 1) {
        return filteredContacts.value.filter(contact => !contact.isGroup)
      }
      return filteredContacts.value
    })
    
    
    // 按部门分组的用户
    const groupedUsersByDepartment = computed(() => {
      // 合并聊天联系人和所有同事
      const usersMap = new Map();
      
      // 先添加聊天联系人（非群组）
      filteredContacts.value
        .filter(contact => !contact.isGroup)
        .forEach(contact => {
          // 跳过自己
          if (userInfo.value && contact.userId === userInfo.value.id) {
            return;
          }
          // 使用ID作为唯一键
          usersMap.set(contact.userId || contact.id, contact);
        });
      
      // 再添加所有同事，但避免重复
      allColleagues.value.forEach(colleague => {
        // 跳过自己
        if (userInfo.value && colleague.id === userInfo.value.id) {
          return;
        }
        
        // 只有在不存在时才添加（避免覆盖现有联系人）
        if (!usersMap.has(colleague.id)) {
          // 构造兼容格式的用户对象
          const contact = {
            id: 'user_' + colleague.id, // 添加前缀以避免与现有会话ID冲突
            userId: colleague.id,
            name: (colleague.name || colleague.username || '未命名联系人').trim(),
            initial: ((colleague.name || colleague.username || '未命名联系人')[0]),
            avatar: colleague.avatar || '',
            color: getRandomColor(colleague.id),
            status: 'online',
            lastMessage: '',
            lastTime: '',
            unread: 0,
            isGroup: false,
            department: colleague.department || '其它'
          };
          usersMap.set(colleague.id, contact);
        }
      });
      
      // 创建一个部门ID到名称的映射
      const departmentMap = new Map(departments.value.map(dept => [dept.id, dept.name]))
      
      // 按部门分组
      const groupedUsers = {};
      
      // 将Map转为Array后分组
      Array.from(usersMap.values()).forEach(user => {
        const departmentName = departmentMap.get(user.department) || '其他';
        if (!groupedUsers[departmentName]) {
          groupedUsers[departmentName] = [];
        }
        groupedUsers[departmentName].push(user);
      });
      
      return groupedUsers;
    })
    
    // 路由
    const route = useRoute()
    
    // 定义一个refreshInterval的引用，以便在组件卸载时清除
    let refreshInterval = null
    
    // 组件卸载时清除定时器
    onBeforeUnmount(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })
    
    // 路由相关操作
    onMounted(async () => {
      try {
        // 先加载用户数据
        const userData = await fetchCurrentUser()
        
        // 如果获取用户信息失败，显示错误并返回
        if (!userData) {
          ElMessage.error('无法加载用户信息，请刷新页面重试')
          return
        }
        
        console.log('组件挂载时获取的用户信息:', userData)
        
        // 确保用户数据已经更新
        if (!userInfo.value || !userInfo.value.id) {
          console.error('用户数据未正确加载:', userInfo.value)
          ElMessage.error('用户数据加载异常，请刷新页面重试')
          return
        } else {
          console.log('当前用户数据已正确加载:', userInfo.value)
        }
        
        // 加载所有用户列表
        await loadAllUsers()
        
        // 加载部门列表
        await loadDepartments()
        
        // 再加载聊天会话列表
        await loadChatSessions()
        
        // 检查URL参数中是否有会话ID
        const sessionId = route.query.session || route.query.id
        if (sessionId) {
          // 查找对应的联系人
          const foundContact = contacts.value.find(c => c.id === parseInt(sessionId))
          if (foundContact) {
            // 选中该联系人
            selectedContact.value = foundContact.id
            // 加载聊天记录
            await loadChatMessages(sessionId)
          } else {
            // 如果未找到对应联系人，尝试直接加载会话
            console.log('通过ID直接加载聊天会话:', sessionId)
            await loadChatMessages(sessionId)
          }
        }
      
        // 设置定时刷新
        refreshInterval = setInterval(async () => {
          if (selectedContact.value) {
            await loadChatMessages(selectedContact.value, true)
          }
          await loadChatSessions(true)
        }, 30000)
        
        // 初始滚动到底部
        await nextTick()
        scrollToBottom()
      } catch (error) {
        console.error('初始化聊天组件失败:', error)
        ElMessage.error('初始化聊天组件失败: ' + error.message)
      }
    })
    
    // 获取当前用户信息
    const fetchCurrentUser = async () => {
      try {
        console.log('开始获取当前用户信息...')
        
        // 检查localStorage中是否有token
        const token = localStorage.getItem('token')
        if (!token) {
          console.warn('本地存储中没有找到认证token')
          ElMessage.warning('未登录或登录已过期，请重新登录')
          return null
        }
        
        const response = await request({
          url: '/api/auth/users/me/',
          method: 'get'
        })
        
        console.log('获取用户信息响应:', response)
        
        // 检查响应格式并获取用户数据
        let userData = null
        if (response.data && response.data.id) {
          // 直接从data字段获取用户数据
          userData = response.data
          console.log('从data字段获取用户数据:', userData)
        } else if (response.data && response.data.data && response.data.data.id) {
          // 从嵌套data字段获取用户数据
          userData = response.data.data
          console.log('从嵌套data字段获取用户数据:', userData)
        } else if (response.id) {
          // 直接响应就是用户数据
          userData = response
          console.log('直接获取用户数据:', userData)
        } else {
          console.error('获取用户信息响应格式异常:', response)
          throw new Error('用户信息格式异常')
        }
        
        if (!userData || !userData.id) {
          console.error('获取的用户数据无效:', userData)
          throw new Error('无效的用户数据')
        }
        
        // 不使用未定义的mutation，而是直接更新本地状态
        userInfo.value = userData
        
        // 保存到localStorage以便持久化
        localStorage.setItem('user', JSON.stringify(userData))
        
        console.log('用户数据已更新:', userInfo.value)
        return userData
      } catch (error) {
        console.error('获取当前用户信息失败:', error)
        ElMessage.error('获取用户信息失败: ' + (error.message || '未知错误'))
        return null
      }
    }
    
    // 加载聊天会话列表
    const loadChatSessions = async (isBackgroundRefresh = false) => {
      try {
        if (!isBackgroundRefresh) {
          sessionsLoading.value = true
        }
        console.log('正在加载聊天会话列表...')
        
        const response = await getChatSessions()
        console.log('获取聊天会话响应:', response)
        
        // 确保我们有响应数据
        if (!response) {
          console.error('获取聊天会话返回空响应')
          contacts.value = []
          return
        }
        
        let data
        if (response.success && response.data) {
          data = response.data
          console.log('使用包装格式的聊天数据:', data)
        } else {
          data = response
          console.log('使用直接返回的聊天数据:', data)
        }
        
        // 转换数据格式
        chatSessions.value = data
        
        // 构建联系人列表
        if (data && Array.isArray(data.results)) {
          console.log('处理分页数据结构, 共有会话数:', data.results.length)
          // 处理分页数据结构
          contacts.value = data.results.map(session => {
            // 找到对方用户（非当前用户）
            let otherParticipant = null
            if (session.participants && Array.isArray(session.participants)) {
              if (userInfo.value && userInfo.value.id) {
                otherParticipant = session.participants.find(
                  p => p.user && p.user.id !== userInfo.value.id
                )
              } else {
                // 如果没有当前用户信息，使用第一个参与者
                otherParticipant = session.participants[0]
              }
            }
            
            // 如果是群聊，使用群聊信息
            if (session.is_group) {
              return {
                id: session.id,
                name: session.title || '群聊',
                initial: (session.title || '群聊')[0],
                avatar: '',
                avatar_url: '',
                color: getRandomColor(session.id),
                status: 'online',
                lastMessage: session.last_message ? session.last_message.content : '',
                lastTime: session.last_message ? formatMessageTime(session.last_message.created_at) : formatMessageTime(session.updated_at),
                unread: session.unread_count,
                isGroup: true
              }
            }
            
            // 单聊，使用对方信息
            if (otherParticipant) {
              const user = otherParticipant.user
              // 处理头像路径
              let avatar_url = '';
              if (user.avatar) {
                const avatar = user.avatar;
                if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
                  avatar_url = avatar;
                } else if (avatar.startsWith('/')) {
                  avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}${avatar}`;
                } else {
                  avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}/${avatar}`;
                }
              }
              
              return {
                id: session.id,
                userId: user.id, // 添加用户ID，用于检查是否是自己
                name: (user.name || (((user.first_name || '') + ' ' + (user.last_name || '')).trim() || user.username) || '未命名联系人').trim(),
                initial: ((user.name || user.first_name || user.username || '未命名联系人')[0]),
                avatar: user.avatar || '',
                avatar_url: avatar_url,
                color: getRandomColor(user.id),
                status: 'online',
                lastMessage: session.last_message ? session.last_message.content : '',
                lastTime: session.last_message ? formatMessageTime(session.last_message.created_at) : formatMessageTime(session.updated_at),
                unread: session.unread_count,
                isGroup: false,
                department: user.department || '其他' // 确保有默认部门
              }
            }
            
            // 如果没有其他参与者（理论上不应该发生）
            return {
              id: session.id,
              name: session.title || '聊天',
              initial: (session.title || '聊天')[0],
              avatar: '',
              avatar_url: '',
              color: getRandomColor(session.id),
              status: 'online',
              lastMessage: session.last_message ? session.last_message.content : '',
              lastTime: session.last_message ? formatMessageTime(session.last_message.created_at) : formatMessageTime(session.updated_at),
              unread: session.unread_count,
              isGroup: session.is_group,
              department: '其他'
            }
          })
        } else if (data && Array.isArray(data)) {
          console.log('处理非分页数据结构, 共有会话数:', data.length)
          // 处理非分页数据结构
          contacts.value = data.map(session => {
            // 找到对方用户（非当前用户）
            let otherParticipant = null
            if (session.participants && Array.isArray(session.participants)) {
              if (userInfo.value && userInfo.value.id) {
                otherParticipant = session.participants.find(
                  p => p.user && p.user.id !== userInfo.value.id
                )
              } else {
                // 如果没有当前用户信息，使用第一个参与者
                otherParticipant = session.participants[0]
              }
            }
            
            // 如果是群聊，使用群聊信息
            if (session.is_group) {
              return {
                id: session.id,
                name: session.title || '群聊',
                initial: (session.title || '群聊')[0],
                avatar: '',
                avatar_url: '',
                color: getRandomColor(session.id),
                status: 'online',
                lastMessage: session.last_message ? session.last_message.content : '',
                lastTime: session.last_message ? formatMessageTime(session.last_message.created_at) : formatMessageTime(session.updated_at),
                unread: session.unread_count,
                isGroup: true
              }
            }
            
            // 单聊，使用对方信息
            if (otherParticipant) {
              const user = otherParticipant.user
              // 处理头像路径
              let avatar_url = '';
              if (user.avatar) {
                const avatar = user.avatar;
                if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
                  avatar_url = avatar;
                } else if (avatar.startsWith('/')) {
                  avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}${avatar}`;
                } else {
                  avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}/${avatar}`;
                }
              }
              
              return {
                id: session.id,
                name: (user.name || (((user.first_name || '') + ' ' + (user.last_name || '')).trim() || user.username) || '未命名联系人').trim(),
                initial: ((user.name || user.first_name || user.username || '未命名联系人')[0]),
                avatar: user.avatar || '',
                avatar_url: avatar_url,
                color: getRandomColor(user.id),
                status: 'online',
                lastMessage: session.last_message ? session.last_message.content : '',
                lastTime: session.last_message ? formatMessageTime(session.last_message.created_at) : formatMessageTime(session.updated_at),
                unread: session.unread_count,
                isGroup: false,
                department: user.department || '其他'
              }
            }
            
            // 如果没有其他参与者（理论上不应该发生）
            return {
              id: session.id,
              name: session.title || '聊天',
              initial: (session.title || '聊天')[0],
              avatar: '',
              avatar_url: '',
              color: getRandomColor(session.id),
              status: 'online',
              lastMessage: session.last_message ? session.last_message.content : '',
              lastTime: session.last_message ? formatMessageTime(session.last_message.created_at) : formatMessageTime(session.updated_at),
              unread: session.unread_count,
              isGroup: session.is_group,
              department: '其他'
            }
          })
        } else {
          // 如果没有有效数据
          console.error('获取聊天会话格式异常或为空:', data)
          contacts.value = []
        }
        
        console.log('处理后的联系人列表:', contacts.value)
        
        // 如果有未读消息，按未读数量排序
        if (contacts.value.length > 0) {
          contacts.value.sort((a, b) => b.unread - a.unread)
        }
      } catch (error) {
        console.error('加载聊天会话失败:', error)
        ElMessage.error('加载聊天会话失败: ' + (error.message || '未知错误'))
        contacts.value = []
      } finally {
        if (!isBackgroundRefresh) {
          sessionsLoading.value = false
        }
      }
    }
    
    // 加载聊天消息
    const loadChatMessages = async (chatId, isBackgroundRefresh = false) => {
      if (!chatId) {
        console.error('无法加载消息: chatId为空')
        return
      }
      
      try {
        if (!isBackgroundRefresh) {
          messagesLoading.value = true
        }
        console.log(`正在加载聊天会话 ${chatId} 的消息...`)
        
        const response = await getChatSession(chatId)
        console.log('聊天会话详情响应:', response)
        
        if (!response) {
          console.error('获取聊天会话详情返回空响应')
          messages.value = []
          return
        }
        
        // 处理不同的响应格式
        let messageData = []
        let sessionData = null
        
        if (response.data && response.data.messages) {
          // 标准格式：响应直接包含messages字段
          messageData = response.data.messages
          sessionData = response.data
          console.log('标准格式消息数据，消息数量:', messageData.length)
        } else if (response.data && response.data.data && response.data.data.messages) {
          // 包装格式：{success: true, data: {messages: [...]}}
          messageData = response.data.data.messages
          sessionData = response.data.data
          console.log('包装格式消息数据，消息数量:', messageData.length)
        } else if (response.messages) {
          // 直接返回格式: {messages: [...]}
          messageData = response.messages
          sessionData = response
          console.log('直接返回格式消息数据，消息数量:', messageData.length)
        } else {
          console.warn('无法识别的消息数据格式:', response)
          console.log('尝试检查是否有其他可能的消息字段...')
          
          // 尝试查找其他可能的消息字段
          const possibleMessageFields = ['message', 'chat_messages', 'chats', 'content']
          for (const field of possibleMessageFields) {
            if (response[field] && Array.isArray(response[field])) {
              console.log(`找到可能的消息字段 ${field}，使用此字段数据`)
              messageData = response[field]
              sessionData = response
              break
            } else if (response.data && response.data[field] && Array.isArray(response.data[field])) {
              console.log(`在data字段中找到可能的消息字段 ${field}，使用此字段数据`)
              messageData = response.data[field]
              sessionData = response.data
              break
            }
          }
          
          if (messageData.length === 0) {
            console.warn('未找到任何消息数据，使用空数组')
          }
        }
        
        // 处理消息发送者的头像
        messageData.forEach(message => {
          if (message.sender && message.sender.avatar) {
            const avatar = message.sender.avatar;
            if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
              message.sender.avatar_url = avatar;
            } else if (avatar.startsWith('/')) {
              message.sender.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}${avatar}`;
            } else {
              message.sender.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}/${avatar}`;
            }
          }
        });
        
        // 记录会话和消息数据
        console.log('处理后的会话数据:', sessionData)
        console.log('处理后的消息数据:', messageData)
        
        // 如果会话不在联系人列表中，添加它
        if (sessionData && !contacts.value.some(c => c.id === parseInt(chatId))) {
          console.log('会话不在联系人列表中，添加它:', sessionData)
          
          // 创建临时联系人对象
          const session = sessionData
          // 找到对方用户（非当前用户）
          let otherParticipant = null
          
          // 确保 session.participants 存在且是数组
          if (session.participants && Array.isArray(session.participants) && session.participants.length > 0 && userInfo.value) {
            otherParticipant = session.participants.find(p => p.user && p.user.id !== userInfo.value.id)
          }
          
          let tempContact = null
          
          // 如果是群聊，使用群聊信息
          if (session.is_group) {
            tempContact = {
              id: parseInt(chatId),
              name: session.title || '群聊',
              initial: (session.title || '群聊')[0],
              avatar: '',
              avatar_url: '',
              color: getRandomColor(parseInt(chatId)),
              status: 'online',
              lastMessage: session.last_message ? session.last_message.content : '',
              lastTime: formatMessageTime(session.updated_at),
              unread: 0,
              isGroup: true
            }
          // 单聊，使用对方信息
          } else if (otherParticipant && otherParticipant.user) {
            const user = otherParticipant.user
            // 处理头像路径
            let avatar_url = '';
            if (user.avatar) {
              const avatar = user.avatar;
              if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
                avatar_url = avatar;
              } else if (avatar.startsWith('/')) {
                avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}${avatar}`;
              } else {
                avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}/${avatar}`;
              }
            }
            
            tempContact = {
              id: parseInt(chatId),
              name: (user.name || (((user.first_name || '') + ' ' + (user.last_name || '')).trim() || user.username) || '未命名联系人').trim(),
              initial: ((user.name || user.first_name || user.username || '未命名联系人')[0]),
              avatar: user.avatar || '',
              avatar_url: avatar_url,
              color: getRandomColor(user.id),
              status: 'online',
              lastMessage: session.last_message ? session.last_message.content : '',
              lastTime: formatMessageTime(session.updated_at),
              unread: 0,
              isGroup: false
            }
          } else {
            // 如果无法找到对方信息，使用默认值
            tempContact = {
              id: parseInt(chatId),
              name: session.title || '聊天',
              initial: (session.title || '聊天')[0],
              avatar: '',
              avatar_url: '',
              color: getRandomColor(parseInt(chatId)),
              status: 'online',
              lastMessage: '',
              lastTime: formatMessageTime(session.updated_at),
              unread: 0,
              isGroup: session.is_group
            }
          }
          
          // 添加临时联系人到列表
          if (tempContact) {
            contacts.value.unshift(tempContact)
            console.log('添加临时联系人:', tempContact)
          }
        }
        
        // 更新组件数据
        messages.value = messageData || []
        currentChatId.value = parseInt(chatId)
        selectedContact.value = parseInt(chatId)
        
        // 加载当前会话已上传的文档ID
        try {
          const res = await request({
            url: '/api/ai/documents/',
            method: 'get',
            params: { chat: chatId }
          })
          if (res && res.data && Array.isArray(res.data.results)) {
            selectedDocumentIds.value = res.data.results.map(doc => doc.id)
            console.log('当前会话文档ID:', selectedDocumentIds.value)
          }
        } catch (e) {
          selectedDocumentIds.value = []
        }
        
        // 滚动到底部
        nextTick(() => {
          scrollToBottom()
        })
      } catch (error) {
        console.error('加载会话详情失败:', error)
        
        let errorMessage = '加载聊天消息失败'
        if (error.response) {
          const status = error.response.status
          if (status === 404) {
            errorMessage = '聊天会话不存在或已被删除'
          } else if (status === 403) {
            errorMessage = '无权访问此聊天会话'
          } else if (error.response.data && error.response.data.message) {
            errorMessage = error.response.data.message
          }
        } else if (error.message) {
          errorMessage = error.message
        }
        
        ElMessage.error(errorMessage)
        messages.value = []
      } finally {
        if (!isBackgroundRefresh) {
          messagesLoading.value = false
        }
      }
    }
    
    // 刷新聊天会话列表
    const refreshChatSessions = async () => {
      // 更新用户列表
      await loadAllUsers()
      
      // 更新部门列表
      await loadDepartments()
      
      // 更新聊天会话
      await loadChatSessions()
      
      // 如果有当前聊天ID，确保选中正确的联系人
      if (currentChatId.value) {
        const contact = contacts.value.find(c => c.id === currentChatId.value)
        if (contact) {
          selectedContact.value = contact.id
        }
      }
    }
    
    // 确保消息容器滚动到底部
    const scrollToBottom = () => {
      if (messageContainer.value) {
        messageContainer.value.scrollTop = messageContainer.value.scrollHeight
      }
    }
    
    // 在选择联系人后，滚动到底部
    const selectContact = async (contact) => {
      // 检查是否尝试与自己聊天
      if (!contact.isGroup && userInfo.value && contact.userId === userInfo.value.id) {
        ElMessage.warning('不能与自己聊天')
        return
      }
      
      console.log('选择联系人:', contact)
      
      // 处理两种类型的ID：现有对话ID和用户ID前缀的情况
      let contactId = contact.id
      
      // 检查是否已有该联系人的对话
      if (typeof contactId === 'string' && contactId.startsWith('user_')) {
        // 这是直接选择了用户，而不是现有的聊天会话
        let userId = contact.userId || contact.id.replace('user_', '')
        console.log('尝试查找与用户的现有对话:', userId)
        
        // 尝试在现有会话中查找与该用户的对话
        const existingChat = contacts.value.find(c => 
          !c.isGroup && 
          ((c.userId && c.userId == userId) || 
          (c.user && c.user.id == userId))
        )
        
        if (existingChat) {
          console.log('找到与用户的现有对话:', existingChat)
          contactId = existingChat.id
        } else {
          console.log('未找到与用户的现有对话，创建新对话')
          
          // 创建新的聊天会话
          try {
            const response = await request({
              url: '/api/chat/sessions/',
              method: 'post',
              data: {
                participant_ids: [userId],
                is_group: false
              }
            })
            
            console.log('创建会话响应:', response)
            
            // 处理API响应
            let newSession = null
            
            if (response && response.data) {
              newSession = response.data
            } else if (response && response.id) {
              newSession = response
            }
            
            if (newSession && newSession.id) {
              // 创建临时联系人对象
              const tempContact = {
                id: newSession.id,
                userId: userId,
                name: contact.name,
                initial: contact.initial,
                avatar: contact.avatar,
                avatar_url: contact.avatar_url || '',
                color: contact.color || getRandomColor(userId),
                status: 'online',
                lastMessage: '',
                lastTime: formatMessageTime(new Date()),
                unread: 0,
                isGroup: false,
                department: contact.department
              }
              
              // 添加到联系人列表
              contacts.value.unshift(tempContact)
              
              // 更新选中的联系人
              contactId = newSession.id
              ElMessage.success('已创建新的对话')
            } else {
              throw new Error('创建会话返回无效数据')
            }
          } catch (error) {
            console.error('创建新会话失败:', error)
            ElMessage.error('无法创建新对话: ' + (error.message || '未知错误'))
            return
          }
        }
      }
      
      // 加载选中的联系人
      selectedContact.value = contactId
      messageInput.value = ''
      messages.value = []
      
      // 加载消息
      try {
        await loadChatMessages(contactId)
        
        // 滚动到底部
        nextTick(() => {
          scrollToBottom()
        })
      } catch (error) {
        console.error('加载聊天消息失败:', error)
        ElMessage.error('无法加载对话内容：' + (error.message || '未知错误'))
      }
    }
    
    // 在消息列表更新后，滚动到底部
    watch(messages, () => {
      nextTick(() => {
        scrollToBottom()
      })
    })
    
    // 发送消息
    const sendMessage = async () => {
      if (!messageInput.value.trim() || !currentChatId.value) return

      try {
        console.log('发送消息时文档IDs:', selectedDocumentIds.value)
        if (!userInfo.value || !userInfo.value.id) {
          const userData = await fetchCurrentUser()
          if (!userData || !userData.id) {
            throw new Error('无法获取当前用户信息，请刷新页面重试')
          }
        }

        const tempMessage = {
          id: 'temp-' + Date.now(),
          content: messageInput.value.trim(),
          sender: {
            id: userInfo.value.id,
            username: userInfo.value.username || '用户',
            first_name: userInfo.value.first_name || '',
            last_name: userInfo.value.last_name || ''
          },
          message_type: 'text',
          created_at: new Date().toISOString(),
          is_temp: true
        }

        messages.value.push(tempMessage)
        const messageCopy = messageInput.value
        messageInput.value = ''
        await nextTick()
        scrollToBottom()

        let response, aiMsg
        if (selectedDocumentIds.value && selectedDocumentIds.value.length > 0) {
          // 文档增强AI对话
          response = await aiChatWithDocuments({
            message: messageCopy,
            chat_id: currentChatId.value,
            document_ids: selectedDocumentIds.value
          })
          // 兼容流式文本响应
          let aiContent = ''
          if (response && typeof response.data === 'string') {
            aiContent = response.data
          } else if (response && response.data && response.data.message) {
            aiContent = response.data.message
          }
          if (aiContent) {
            aiMsg = {
              id: 'ai-' + Date.now(),
              content: aiContent,
              sender: { id: 0, username: 'AI助手' },
              message_type: 'text',
              created_at: new Date().toISOString()
            }
            // 用AI回复替换临时消息
            const tempIndex = messages.value.findIndex(m => m.id === tempMessage.id)
            if (tempIndex !== -1) {
              messages.value.splice(tempIndex, 1, aiMsg)
            } else {
              messages.value.push(aiMsg)
            }
          }
        } else {
          // 原有普通消息
          response = await sendTextMessage({
            chat: currentChatId.value,
            content: messageCopy
          })
          let messageData = null
          if (response && response.success && response.data) {
            messageData = response.data
          } else if (response && response.id) {
            messageData = response
          } else if (response && response.chat) {
            messageData = {
              id: response.id || 'msg-' + Date.now(),
              content: response.content,
              message_type: response.message_type,
              file: response.file,
              created_at: response.created_at || new Date().toISOString(),
              sender: {
                id: userInfo.value.id,
                username: userInfo.value.username || '用户',
                first_name: userInfo.value.first_name || '',
                last_name: userInfo.value.last_name || ''
              }
            }
          }
          const tempIndex = messages.value.findIndex(m => m.id === tempMessage.id)
          if (tempIndex !== -1 && messageData) {
            messages.value.splice(tempIndex, 1, messageData)
          } else if (messageData) {
            messages.value.push(messageData)
          }
        }
        await nextTick()
        scrollToBottom()
      } catch (error) {
        console.error('发送消息失败:', error)
        messages.value = messages.value.filter(m => !m.is_temp)
        messageInput.value = error.savedMessage || messageInput.value
        ElMessage.error('发送消息失败，请重试')
      }
    }
    
    // 打开文件上传
    const openFileUpload = () => {
      fileInput.value.click()
    }
    
    // 打开图片上传
    const openImageUpload = () => {
      imageInput.value.click()
    }
    
    // 添加文件和图片上传加载状态
    const fileUploading = ref(false)
    const imageUploading = ref(false)
    
    // 处理文件上传
    const handleFileUpload = async (event) => {
      const file = event.target.files[0]
      if (!file || !currentChatId.value) return
      try {
        // 显示加载动画
        fileUploading.value = true
        
        // 直接使用sendFileMessage发送文件消息
        await sendFileMessage(
          currentChatId.value,
          `发送文件: ${file.name}`,
          file
        )
        
        // 同时上传到AI文档系统（如果需要）
        const formData = new FormData()
        formData.append('file', file)
        formData.append('chat', currentChatId.value)
        await request({
          url: '/api/ai/documents/upload/',
          method: 'post',
          data: formData,
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        // 上传后强制刷新文档ID列表
        const docRes = await request({
          url: '/api/ai/documents/',
          method: 'get',
          params: { chat: currentChatId.value }
        })
        if (docRes && docRes.data && Array.isArray(docRes.data.results)) {
          selectedDocumentIds.value = docRes.data.results.map(doc => doc.id)
          console.log('上传后刷新文档IDs:', selectedDocumentIds.value)
        }
        
        ElMessage.success('文件发送成功')
        
        // 重新加载消息
        loadChatMessages(currentChatId.value, true)
        event.target.value = ''
      } catch (error) {
        console.error('发送文件失败:', error)
        ElMessage.error('发送文件失败')
      } finally {
        // 无论成功失败，都关闭加载动画
        fileUploading.value = false
      }
    }
    
    // 处理图片上传
    const handleImageUpload = async (event) => {
      const file = event.target.files[0]
      if (!file || !currentChatId.value) return
      
      try {
        // 检查文件类型
        if (!file.type.startsWith('image/')) {
          ElMessage.error('只能上传图片文件')
          event.target.value = ''
          return
        }
        
        // 检查文件大小（最大10MB）
        const maxSize = 10 * 1024 * 1024 // 10MB
        if (file.size > maxSize) {
          ElMessage.error('图片大小不能超过10MB')
          event.target.value = ''
          return
        }
        
        // 显示加载动画
        imageUploading.value = true
        
        console.log('准备发送图片，聊天ID:', currentChatId.value, '文件:', file.name, '大小:', file.size)
        
        // 使用修改后的API参数
        await sendImageMessage(
          currentChatId.value, 
          `发送图片`, 
          file
        )
        
        // 重新加载消息
        loadChatMessages(currentChatId.value, true)
        
        // 清空文件输入
        event.target.value = ''
      } catch (error) {
        console.error('发送图片失败:', error)
        
        // 更详细的错误信息
        let errorMessage = '发送图片失败'
        if (error.response) {
          console.error('错误状态码:', error.response.status)
          console.error('错误详情:', error.response.data)
          
          if (error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error
          } else if (error.response.data && typeof error.response.data === 'string') {
            errorMessage = error.response.data
          } else if (error.response.status === 413) {
            errorMessage = '图片太大，服务器拒绝接收'
          }
        }
        
        ElMessage.error(errorMessage)
        event.target.value = ''
      } finally {
        // 无论成功失败，都关闭加载动画
        imageUploading.value = false
      }
    }
    
    // 打开知识库对话框
    const openKnowledgeDialog = async () => {
      knowledgeDialogVisible.value = true
      await loadKnowledgeList()
    }
    
    // 加载知识库列表
    const loadKnowledgeList = async () => {
      try {
        knowledgeLoading.value = true
        const { data } = await getKnowledgeList()
        knowledgeList.value = data
      } catch (error) {
        console.error('加载知识库列表失败:', error)
        ElMessage.error('加载知识库列表失败')
      } finally {
        knowledgeLoading.value = false
      }
    }
    
    // 选择知识库文件
    const selectKnowledge = (row) => {
      selectedKnowledge.value = row
    }
    
    // 分享知识库文件
    const shareKnowledge = async (knowledge) => {
      if (!currentChatId.value) return
      
      try {
        await sendKnowledgeMessage(
          currentChatId.value,
          `分享知识库文件: ${knowledge.title}`,
          knowledge.id
        )
        
        // 关闭对话框
        knowledgeDialogVisible.value = false
        
        // 重新加载消息
        loadChatMessages(currentChatId.value, true)
      } catch (error) {
        console.error('分享知识库文件失败:', error)
        ElMessage.error('分享知识库文件失败')
      }
    }
    
    // 下载文件
    const downloadFile = async (message) => {
      try {
        const response = await downloadMessageFile(message.id)
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', message.file_name || 'download')
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (error) {
        console.error('下载文件失败:', error)
        ElMessage.error('下载文件失败')
      }
    }
    
    // 查看知识库文件
    const viewKnowledge = (message) => {
      if (message.knowledge_detail) {
        // 可以跳转到知识库详情页面
        ElMessageBox.alert(
          `标题: ${message.knowledge_detail.title}<br>描述: ${message.knowledge_detail.description || '无'}`, 
          '知识库文件', 
          {
            dangerouslyUseHTMLString: true,
            confirmButtonText: '确定'
          }
        )
      }
    }
    
    // 获取发送者颜色
    const getSenderColor = (sender) => {
      return getRandomColor(sender.id)
    }
    
    // 获取发送者首字母
    const getSenderInitial = (sender) => {
      return (sender.first_name || sender.username)[0]
    }
    
    // 根据ID生成随机颜色
    const getRandomColor = (id) => {
      const colors = [
        '#007bff', '#28a745', '#dc3545', '#fd7e14', 
        '#6f42c1', '#20c997', '#17a2b8', '#6c757d'
      ]
      
      // 使用ID作为索引，确保同一用户颜色一致
      const index = typeof id === 'number' ? id % colors.length : 0
      return colors[index]
    }
    
    // 格式化消息时间
    const formatMessageTime = (timestamp) => {
      if (!timestamp) return ''
      
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      // 今天内的消息显示时间
      if (diff < 24 * 60 * 60 * 1000) {
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      return `${hours}:${minutes}`
      }
      
      // 一周内的消息显示星期几
      if (diff < 7 * 24 * 60 * 60 * 1000) {
        const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
        return days[date.getDay()]
      }
      
      // 更早的消息显示日期
      return `${date.getMonth() + 1}月${date.getDate()}日`
    }
    
    // 格式化日期
    const formatDate = (timestamp) => {
      if (!timestamp) return ''
      
      const date = new Date(timestamp)
      return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
    }
    
    // 格式化文件大小
    const formatFileSize = (sizeInKB) => {
      if (sizeInKB < 1024) {
        return `${sizeInKB} KB`
      } else {
        return `${(sizeInKB / 1024).toFixed(2)} MB`
      }
    }
    
    // 获取状态文字
    const getStatusText = (status) => {
      const statusMap = {
        'online': '在线',
        'offline': '离线',
        'busy': '忙碌',
        'away': '离开'
      }
      return statusMap[status] || status
    }
    
    // 添加强制刷新方法
    const forceRefresh = async () => {
      try {
        ElMessage.info('正在强制刷新数据...')
        
        // 重新获取用户信息
        const userData = await fetchCurrentUser()
        
        if (!userData) {
          ElMessage.error('无法获取用户信息，请尝试重新登录')
          return
        }
        
        // 重新加载聊天会话
        await loadChatSessions()
        
        if (contacts.value.length === 0) {
          ElMessage.warning('未找到任何聊天会话，您可能还没有开始任何对话')
        } else {
          ElMessage.success('刷新成功！找到 ' + contacts.value.length + ' 个聊天会话')
        }
      } catch (error) {
        console.error('强制刷新失败:', error)
        ElMessage.error('刷新失败: ' + (error.message || '未知错误'))
      }
    }
    
    // 加载所有用户
    const loadAllUsers = async () => {
      try {
        console.log('正在加载所有用户列表...')
        
        // 确保已获取当前用户信息及其公司ID
        if (!userInfo.value || !userInfo.value.company) {
          console.error('无法加载同事列表：缺少用户或公司信息。')
          // 尝试重新获取用户信息
          const userData = await fetchCurrentUser();
          if (!userData || !userData.company) {
            ElMessage.error('无法获取您的公司信息，无法加载同事列表。');
            allColleagues.value = []; // 清空列表
            return;
          }
        }
        
        const companyId = userInfo.value.company;
        console.log('开始获取公司同事列表，公司ID:', companyId);

        // 使用/api/auth/contacts/并传入公司ID来获取同事列表
        const response = await request({
          url: '/api/auth/contacts/',
          method: 'get',
          params: { company: companyId }
        });

        console.log('公司同事列表API响应:', response);

        let users = [];
        // 根据通讯录页面的经验，响应可能在 response.data 中
        if (response && response.success && Array.isArray(response.data)) {
          users = response.data;
        } else if (response && Array.isArray(response.data)) {
           users = response.data;
        } else if (response && Array.isArray(response)) {
           users = response;
        } else {
          console.warn('获取同事列表的响应格式未知或数据为空:', response);
        }

        if (users.length > 0) {
          console.log(`成功获取到 ${users.length} 个同事`);
          // 后端返回的contacts可能需要格式化以匹配allColleagues的期望结构
          allColleagues.value = users.map(u => ({
            id: u.id,
            username: u.username,
            name: u.name, // 直接使用通讯录接口提供的name字段
            department: u.department,
            avatar: u.avatar_url || u.avatar
          }));
        } else {
          allColleagues.value = []; // 如果没有用户，则清空
        }

      } catch (error) {
        console.error('加载公司同事列表过程中出错:', error);
        ElMessage.error('加载同事列表失败，请稍后重试。');
        allColleagues.value = []; // 出错时清空列表
      }
    }
    
    // 获取部门列表
    const loadDepartments = async () => {
      try {
        console.log('正在加载部门列表...')
        const response = await request({
          url: '/api/auth/departments/',
          method: 'get'
        })
        
        console.log('获取部门响应:', response)
        
        // 处理响应数据
        let depts = []
        if (response && response.results) {
          depts = response.results
        } else if (Array.isArray(response)) {
          depts = response
        } else if (response && response.data) {
          if (Array.isArray(response.data)) {
            depts = response.data
          } else if (response.data.results) {
            depts = response.data.results
          }
        }
        
        if (depts && depts.length > 0) {
          console.log(`成功获取到${depts.length}个部门`)
          departments.value = depts
        }
      } catch (error) {
        console.error('获取部门列表失败:', error)
      }
    }
    
    const selectedDocumentIds = ref([]) // 当前会话关联文档ID
    
    // AI总结相关
    const summaryDialogVisible = ref(false)
    const summaryDateRange = ref([new Date(new Date().setDate(new Date().getDate() - 7)), new Date()])
    const summaryContent = ref('')
    const summaryLoading = ref(false)
    const pickerOptions = ref({
      shortcuts: [{
        text: '最近一周',
        onClick(picker) {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
          picker.$emit('pick', [start, end]);
        }
      }, {
        text: '最近一个月',
        onClick(picker) {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
          picker.$emit('pick', [start, end]);
        }
      }, {
        text: '最近三个月',
        onClick(picker) {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
          picker.$emit('pick', [start, end]);
        }
      }]
    })
    
    const openSummaryDialog = () => {
      // 重置内容，但保留日期范围
      summaryContent.value = ''
      summaryDialogVisible.value = true
    }
    
    const handleCloseSummaryDialog = () => {
      summaryDialogVisible.value = false
    }
    
    const handleSummarize = async () => {
      if (!selectedContact.value) {
        ElMessage.warning('请先选择一个聊天');
        return;
      }
      if (!summaryDateRange.value || summaryDateRange.value.length !== 2) {
        ElMessage.warning('请选择一个有效的时间范围');
        return;
      }

      summaryLoading.value = true;
      summaryContent.value = ''; // Reset before fetching

      const [startDate, endDate] = summaryDateRange.value;

      try {
        // 'summarizeChat' returns the full axios response
        const response = await summarizeChat(selectedContact.value, startDate.toISOString(), endDate.toISOString());
        
        // The actual data from the backend is in response.data
        const summary = response.data.summary;

        if (summary) {
          // If we have a summary, display it
          summaryContent.value = summary;
        } else {
          // If the summary is empty or not present, display a clear message
          summaryContent.value = '在选定时间范围内没有可总结的消息，或AI未能生成摘要。';
        }
      } catch (error) {
        console.error('Summarization error:', error);
        summaryContent.value = '生成摘要时遇到错误，请检查后台日志或稍后再试。';
        ElMessage.error('生成摘要失败，请稍后再试');
      } finally {
        summaryLoading.value = false;
      }
    };
    
    // 替换图片预览方法
    const expandedImage = ref(null)

    // 切换图片放大显示
    const toggleImageExpand = (imageUrl) => {
      expandedImage.value = imageUrl
    }
    
    const getFileName = (fullName) => {
      if (!fullName) return '';
      const lastDot = fullName.lastIndexOf('.');
      if (lastDot === -1 || lastDot === 0) {
        return fullName;
      }
      return fullName.substring(0, lastDot);
    };

    const getFileExtension = (fullName) => {
      if (!fullName) return '';
      const lastDot = fullName.lastIndexOf('.');
      if (lastDot === -1 || lastDot === 0 || lastDot >= fullName.length - 1) {
        return '';
      }
      return fullName.substring(lastDot); // includes the dot
    };
    
    // 右键菜单相关
    const contextMenuVisible = ref(false)
    const contextMenuStyle = ref({
      top: '0px',
      left: '0px'
    })
    const selectedMessage = ref(null)
    
    // 处理右键菜单打开
    const openContextMenu = (event, message) => {
      event.preventDefault()
      // 保存点击位置
      contextMenuStyle.value = {
        top: `${event.clientY}px`,
        left: `${event.clientX}px`
      }
      // 保存选中的消息
      selectedMessage.value = message
      // 显示菜单
      contextMenuVisible.value = true
      
      // 添加全局点击事件监听器关闭菜单
      document.addEventListener('click', closeContextMenu, { once: true })
    }
    
    // 关闭右键菜单
    const closeContextMenu = () => {
      contextMenuVisible.value = false
    }
    
    // 复制消息内容
    const copyMessageContent = () => {
      if (!selectedMessage.value) return
      
      const content = selectedMessage.value.content || ''
      navigator.clipboard.writeText(content)
        .then(() => {
          ElMessage.success('内容已复制到剪贴板')
          closeContextMenu()
        })
        .catch(err => {
          ElMessage.error('复制失败: ' + err)
        })
    }
    
    // 日程对话框相关
    const calendarDialogVisible = ref(false);
    const isAnalyzing = ref(false);
    const isSubmitting = ref(false);
    const calendarFormRef = ref(null); // Ref for the form
    const calendarEvent = reactive({
      title: '',
      start: '',
      end: '',
      location: '',
      type: 'blue',
      reminder: '30min',
      description: '',
    });
    
    // Validation rules for the calendar form
    const calendarRules = reactive({
      title: [{ required: true, message: '请输入日程标题', trigger: 'blur' }],
      start: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
      end: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
      location: [{ required: true, message: '请输入地点', trigger: 'blur' }],
      type: [{ required: true, message: '请选择日程类型', trigger: 'change' }],
      reminder: [{ required: true, message: '请选择提醒时间', trigger: 'change' }],
      description: [{ required: true, message: '请输入描述信息', trigger: 'blur' }],
    });
    
    // 自定义验证规则
    const validateEndTime = (rule, value, callback) => {
      if (!value) {
        // 'required' rule will handle this
        callback();
      } else if (calendarEvent.start) {
        const startDate = new Date(calendarEvent.start);
        const endDate = new Date(value);
        if (endDate <= startDate) {
          callback(new Error('结束时间必须晚于开始时间'));
        } else if (startDate.toDateString() !== endDate.toDateString()) {
          callback(new Error('开始和结束时间必须是同一天'));
        } else {
          callback();
        }
      } else {
        callback();
      }
    };

    // 监听开始时间变化，以触发结束时间的验证
    watch(() => calendarEvent.start, (newValue) => {
      if (newValue && calendarFormRef.value) {
        calendarFormRef.value.validateField('end');
      }
    });

    // 更新验证规则
    calendarRules.end = [
      { required: true, message: '请选择结束时间', trigger: 'change' },
      { validator: validateEndTime, trigger: 'change' }
    ];
    
    // 从消息添加到日程
    const addToCalendarFromMessage = async () => {
      if (!selectedMessage.value) {
        ElMessage.warning('无法识别消息');
        return;
      }
      
      isAnalyzing.value = true;
      calendarDialogVisible.value = true;
      
      try {
        const messageContent = selectedMessage.value.content;
        const response = await analyzeForCalendar(messageContent);
        
        console.log('AI日程分析响应:', response);
        
        // 修复数据结构处理方式
        const eventData = response?.data?.data || response?.data;
        
        if (!eventData || typeof eventData !== 'object') {
            console.error("AI分析未能返回有效的日程数据。", response);
            ElMessage.warning('AI未能自动识别日程，请手动填写。');
            // Populate with default values for manual entry
            calendarEvent.title = '';
            calendarEvent.start = formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss');
            calendarEvent.end = formatDate(new Date(Date.now() + 60*60*1000), 'YYYY-MM-DD HH:mm:ss');
            calendarEvent.location = '';
            calendarEvent.type = 'blue';
            calendarEvent.reminder = '30min';
            calendarEvent.description = messageContent || '';
            calendarEvent.is_all_day = false;
        } else {
            console.log('AI成功识别日程数据:', eventData);
            // Populate with data from AI
            calendarEvent.title = eventData.title || '';
            calendarEvent.start = eventData.start || formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss');
            calendarEvent.end = eventData.end || formatDate(new Date(Date.now() + 60*60*1000), 'YYYY-MM-DD HH:mm:ss');
            calendarEvent.location = eventData.location || '';
            calendarEvent.type = eventData.type || 'blue';
            calendarEvent.reminder = eventData.reminder || '30min';
            calendarEvent.description = eventData.description || messageContent || '';
            calendarEvent.is_all_day = eventData.is_all_day || false;
            
            // 添加参与者处理
            if (eventData.participants && Array.isArray(eventData.participants)) {
                calendarEvent.participants = eventData.participants;
            } else {
                calendarEvent.participants = userId.value ? [userId.value] : [];
            }
        }
      } catch (error) {
        console.error('获取日程信息失败:', error);
        ElMessage.error('AI分析失败，请手动填写日程。');
        // Populate with default values on API error
        calendarEvent.title = '';
        calendarEvent.start = formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss');
        calendarEvent.end = formatDate(new Date(Date.now() + 60*60*1000), 'YYYY-MM-DD HH:mm:ss');
        calendarEvent.location = '';
        calendarEvent.type = 'blue';
        calendarEvent.reminder = '30min';
        calendarEvent.description = selectedMessage.value?.content || '';
        calendarEvent.is_all_day = false;
      } finally {
        isAnalyzing.value = false;
        closeContextMenu();
      }
    };
    
    // 添加日程
    const submitCalendarEvent = async () => {
      if (!calendarFormRef.value) return;
      await calendarFormRef.value.validate(async (valid) => {
        if (valid) {
          isSubmitting.value = true;
          try {
            const eventData = { ...calendarEvent };
            if (!eventData.participants) {
                eventData.participants = [];
            }
            if (userId.value && !eventData.participants.includes(userId.value)) {
                eventData.participants.push(userId.value);
            }

            await createCalendarEvent(eventData);
            
            ElMessage.success('日程添加成功');
            calendarDialogVisible.value = false;
          } catch (error) {
            ElMessage.error('添加日程失败: ' + (error.response?.data?.error || error.message));
          } finally {
            isSubmitting.value = false;
          }
        } else {
          ElMessage.error('请填写所有必填项');
          return false;
        }
      });
    };
    
    // 全局点击事件监听 - 用于处理组件外部点击关闭右键菜单
    onMounted(() => {
      document.addEventListener('click', (event) => {
        // 如果点击位置不在右键菜单内，关闭菜单
        if (contextMenuVisible.value) {
          const menuEl = document.querySelector('.chat-context-menu')
          if (menuEl && !menuEl.contains(event.target)) {
            contextMenuVisible.value = false
          }
        }
      })
    })
    
    return {
      searchQuery,
      activeTab,
      selectedContact,
      tabs,
      contacts,
      currentContact,
      filteredContacts,
      messages,
      messageInput,
      messageContainer,
      fileInput,
      imageInput,
      currentUser,
      userInfo,
      userId,
      knowledgeDialogVisible,
      knowledgeLoading,
      knowledgeList,
      sessionsLoading,
      messagesLoading,
      // 图标
      Search,
      Document,
      PictureFilled,
      FolderOpened,
      Microphone,
      Position,
      ChatDotSquare,
      Reading,
      UserFilled,
      ChatLineSquare,
      Refresh,
      // 方法
      sendMessage,
      getStatusText,
      selectContact,
      openFileUpload,
      openImageUpload,
      handleFileUpload,
      handleImageUpload,
      openKnowledgeDialog,
      selectKnowledge,
      shareKnowledge,
      downloadFile,
      viewKnowledge,
      getSenderColor,
      getSenderInitial,
      formatMessageTime,
      formatDate,
      formatFileSize,
      refreshChatSessions,
      forceRefresh,
      groupedUsersByDepartment,
      getActiveContacts,
      loadAllUsers,
      loadDepartments,
      selectedDocumentIds,
      fileUploading,
      imageUploading,
      summaryDialogVisible,
      summaryDateRange,
      summaryContent,
      summaryLoading,
      pickerOptions,
      openSummaryDialog,
      handleCloseSummaryDialog,
      handleSummarize,
      expandedImage,
      toggleImageExpand,
      getFileName,
      getFileExtension,
      contextMenuVisible,
      contextMenuStyle,
      openContextMenu,
      copyMessageContent,
      addToCalendarFromMessage,
      calendarDialogVisible,
      calendarEvent,
      isAnalyzing,
      isSubmitting,
      submitCalendarEvent,
      calendarFormRef,
      calendarRules
    }
  }
}
</script>

<style scoped>
.chat-container {
  height: calc(100vh - 64px); /* 减去顶部导航栏的高度 */
  width: 100%;
  padding: 20px;
  overflow: hidden;
  box-sizing: border-box;
  background-color: transparent;
}

.chat-card {
  height: 100%;
  width: 100%;
  border-radius: 8px;
  margin: 0;
  overflow: hidden;
  box-shadow: 0 2px 12px var(--shadow-color) !important;
  background-color: transparent;
}

.chat-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
  background-color: transparent;
}

.chat-layout {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: transparent;
}

/* 侧边栏样式 */
.chat-sidebar {
  width: 280px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  height: 100%;
  overflow: hidden;
}

.search-box {
  padding: 15px;
  border-bottom: 1px solid var(--border-color);
}

.chat-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.chat-tab {
  flex: 1;
  text-align: center;
  padding: 12px;
  cursor: pointer;
  font-weight: 500;
  color: var(--text-color-secondary);
  transition: all 0.3s ease;
}

.chat-tab.active {
  color: var(--el-color-primary);
  border-bottom: 2px solid var(--el-color-primary);
}

.contacts-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.contact-item {
  display: flex;
  padding: 15px;
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: all 0.2s ease;
  border-color: var(--border-color);
}

.contact-item:hover {
  background-color: var(--hover-color);
}

.contact-item.active {
  background-color: var(--primary-color-light, #f0f7ff);
}

.contact-avatar {
  position: relative;
  margin-right: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.avatar.small {
  width: 32px;
  height: 32px;
  font-size: 12px;
}

.avatar-initial {
  font-size: 16px;
}

.contact-status {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--bg-color);
}

.status-online {
  background-color: #28a745;
}

.status-offline {
  background-color: #6c757d;
}

.status-busy {
  background-color: #dc3545;
}

.status-away {
  background-color: #fd7e14;
}

.contact-info {
  flex: 1;
  overflow: hidden;
}

.contact-name {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.contact-name span {
  font-weight: 500;
}

.time {
  font-size: 12px;
  color: var(--text-color-tertiary);
}

.contact-message {
  display: flex;
  justify-content: space-between;
  color: var(--text-color-secondary);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
  padding-right: 30px; 
}

.message-badge {
  position: absolute;
  right: 5px;
  top: 0;
  height: 100%;
  display: flex;
  align-items: center;
}

.message-badge :deep(.el-badge__content) {
  position: static !important;
  transform: none !important;
}

/* 聊天内容样式 */
.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background-color: transparent;
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-color);
}

.chat-header .contact-info {
  margin-right: auto;
}

.chat-header h6 {
  margin: 0;
  font-size: 16px;
  color: var(--text-color);
}

.chat-header p {
  margin: 0;
  font-size: 12px;
  color: var(--text-color-tertiary);
}

.chat-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-left: auto;
  padding-right: 15px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-height: calc(100% - 150px); 
  display: flex;
  flex-direction: column;
  background-color: transparent;
}

.message {
  margin-bottom: 15px;
  width: 100%;
  display: flex;
  flex-direction: column;
  background-color: transparent;
}

.message-container {
  width: 100%;
  display: flex;
  background-color: transparent;
}

.message-sent .message-container {
  flex-direction: row-reverse;
}

.message-avatar {
  margin-right: 10px;
  flex-shrink: 0;
}

.message-sent .message-avatar {
  margin-right: 0;
  margin-left: 10px;
}

.message-content-wrapper {
  max-width: 100%;
  width: auto;
}

.message-content {
  padding: 0;
  border-radius: 0;
  background-color: transparent;
  max-width: 280px;
  width: 100%;
}

.message-content.received {
  background-color: transparent;
  border: none;
}

.message-content.sent {
  background-color: transparent;
  border: none;
}

.message-time {
  font-size: 12px;
  color: var(--text-color-tertiary);
  margin-top: 5px;
  text-align: right;
}

.message-sent .message-time {
  text-align: right;
}

.message-received .message-time {
  text-align: left;
}

.image-card {
  width: 100%;
  max-width: 280px;
  background-color: transparent;
  border-radius: 8px;
  margin: 5px 0;
  overflow: hidden;
}

.message-sent .image-card {
  margin-left: auto;
}

.image-card-inner {
  display: flex;
  flex-direction: column;
}

.image-preview {
  width: 100%;
  height: 180px;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.image-preview img:hover {
  transform: scale(1.03);
}

.file-card {
  width: 100%;
  max-width: 280px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 5px 0;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.message-sent .file-card {
  margin-left: auto;
}

.file-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.file-card-inner {
  display: flex;
  align-items: center;
  padding: 15px;
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-color: var(--el-color-primary-light-9);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.file-icon .el-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

/* 增强深色模式下的文件图标可见性 */
:root[data-theme="dark"] .file-icon .el-icon,
body[data-theme="dark"] .file-icon .el-icon {
  color: #4db8ff !important;
  font-size: 26px !important;
  filter: drop-shadow(0 0 2px rgba(77, 184, 255, 0.5)) !important;
}

.file-info {
  flex: 1;
  overflow: hidden;
}

.file-name {
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 4px;
  display: flex;
  align-items: baseline;
  overflow: hidden;
}

.file-name-main {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
}

.file-name-ext {
  white-space: nowrap;
  flex-shrink: 0;
}

.file-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.file-size {
  color: var(--text-color-secondary);
}

.file-download-hint {
  color: var(--el-color-primary);
}

.knowledge-card {
  width: 100%;
  max-width: 280px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 5px 0;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.message-sent .knowledge-card {
  margin-left: auto;
}

.knowledge-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.knowledge-card-inner {
  display: flex;
  padding: 15px;
}

.knowledge-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-color: var(--el-color-success-light-9);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.knowledge-icon .el-icon {
  font-size: 24px;
  color: var(--el-color-success);
}

.knowledge-content {
  flex: 1;
  overflow: hidden;
}

.knowledge-title {
  font-weight: 500;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.knowledge-desc {
  color: var(--text-color-secondary);
  font-size: 12px;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.knowledge-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.knowledge-type {
  color: var(--text-color-tertiary);
  background-color: var(--bg-color-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
}

.knowledge-view {
  color: var(--el-color-primary);
}

.chat-input {
  padding: 15px;
  background-color: var(--bg-color);
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  min-height: 150px; /* 确保输入框有足够高度 */
}

.chat-tools {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.input-area {
  margin-bottom: 10px;
  flex: 1;
}

.send-button {
  display: flex;
  justify-content: flex-end;
}

.empty-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.empty-illustration {
  margin-bottom: 20px;
  color: #ddd;
}

.empty-chat h4 {
  margin: 0 0 10px;
}

.empty-chat p {
  margin: 0;
  font-size: 14px;
}

.empty-contacts {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.empty-icon {
  margin-bottom: 20px;
  color: #ddd;
}

.empty-contacts h4 {
  margin: 0 0 10px;
}

.empty-contacts p {
  margin: 0;
  font-size: 14px;
}

.loading-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.empty-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.loading-messages {
  flex: 1;
  padding: 20px;
}

.mt-3 {
  margin-top: 15px;
}

.search-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-header .el-input {
  flex: 1;
}

.chat-header-actions {
  margin-bottom: 10px;
}

.refresh-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 5px;
}

.department-group {
  margin-bottom: 10px;
  border-color: var(--border-color);
}

.department-header {
  padding: 5px 15px;
  font-size: 13px;
  color: var(--text-color-secondary);
  background-color: var(--bg-color-tertiary);
  border-radius: 4px;
  margin-bottom: 5px;
  font-weight: 500;
  background-color: var(--bg-color-tertiary) !important;
}

.group-actions {
  display: flex;
  align-items: center;
  margin-left: auto;
  margin-right: 5px;
}

.group-action-btn {
  padding: 6px;
  color: #909399;
}

.group-action-btn:hover {
  color: #409EFF;
}

/* 添加对话框全局样式以适配深色模式 */
:deep(.el-dialog) {
  background-color: var(--bg-color);
  color: var(--text-color);
}

:deep(.el-dialog__title) {
  color: var(--text-color);
}

:deep(.el-dialog__body) {
  color: var(--text-color);
}

/* 表格样式适配深色模式 */
:deep(.el-table) {
  background-color: var(--bg-color);
  color: var(--text-color);
}

:deep(.el-table th.el-table__cell) {
  background-color: var(--bg-color-tertiary);
}

:deep(.el-table tr) {
  background-color: var(--bg-color);
}

:deep(.el-table td.el-table__cell) {
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
}

/* 修复输入框和下拉菜单 */
:deep(.el-select .el-input__wrapper) {
  background-color: var(--bg-color-secondary);
}

:deep(.el-select-dropdown) {
  background-color: var(--bg-color-secondary);
  border-color: var(--border-color);
}

:deep(.el-select-dropdown__item) {
  color: var(--text-color);
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
  background-color: var(--hover-color);
}

:deep(.el-input__wrapper) {
  background-color: var(--bg-color-secondary) !important;
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

:deep(.el-input__inner) {
  color: var(--text-color);
}

:deep(.el-select__input) {
  color: var(--text-color) !important;
}

:deep(.el-textarea__inner) {
  background-color: var(--bg-color-secondary);
  color: var(--text-color);
  border-color: var(--border-color);
}

/* 修复空白提示和图标颜色 */
.empty-icon {
  color: var(--text-color-tertiary);
}

:deep(.el-icon) {
  color: inherit;
}

:deep(.el-button--primary) {
  color: white;
}

.chat-header h6 {
  color: var(--text-color);
}

/* 修复badge和标签 */
:deep(.el-badge__content) {
  background-color: var(--error-color, #ef4444);
}

:deep(.el-tag) {
  background-color: var(--primary-color-light);
  border-color: var(--primary-color-light);
  color: var(--primary-color);
}

/* 修复下拉菜单的样式 */
:deep(.el-popper.is-light) {
  background-color: var(--bg-color-tertiary);
  border-color: var(--border-color);
}

:deep(.el-popper__arrow::before) {
  background-color: var(--bg-color-tertiary);
  border-color: var(--border-color);
}

/* 修复搜索框内图标颜色 */
.search-box :deep(.el-input__prefix-inner) {
  color: var(--text-color-tertiary);
}

/* 修复表单组件 */
:deep(.el-input),
:deep(.el-select) {
  --el-fill-color-blank: var(--bg-color-tertiary);
  --el-text-color-regular: var(--text-color);
  --el-border-color: var(--border-color);
  --el-border-color-hover: var(--primary-color);
  --el-fill-color-light: var(--bg-color-tertiary);
}

/* 修复部门组标题 */
.department-header {
  background-color: var(--bg-color-tertiary) !important;
}

/* 修复El-Card组件样式 */
:deep(.el-card) {
  --el-card-bg-color: var(--bg-color);
  background-color: var(--bg-color);
  color: var(--text-color);
  border-color: var(--border-color);
}

/* 修复El-Alert样式 */
:deep(.el-alert) {
  --el-alert-bg-color: var(--bg-color-tertiary);
  color: var(--text-color);
}

:deep(.el-alert--info) {
  --el-alert-bg-color: var(--bg-color-tertiary);
}

:deep(.el-empty__image svg) {
  fill: var(--text-color-tertiary);
}

/* 修复下拉菜单 */
:deep(.el-dropdown-menu) {
  background-color: var(--bg-color-tertiary);
  border-color: var(--border-color);
}

:deep(.el-dropdown-menu__item) {
  color: var(--text-color);
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: var(--hover-color);
}

:deep(.el-dropdown-menu__item--divided:before) {
  background-color: var(--border-color);
}

:deep(.el-dropdown-menu__item.is-disabled) {
  color: var(--text-color-tertiary);
}

:deep(.el-divider) {
  background-color: var(--border-color);
}

/* 修复消息框 */
:deep(.el-message-box) {
  background-color: var(--bg-color);
  border-color: var(--border-color);
}

:deep(.el-message-box__title) {
  color: var(--text-color);
}

:deep(.el-message-box__message) {
  color: var(--text-color);
}

:deep(.el-message) {
  background-color: var(--bg-color);
  border-color: var(--border-color);
}

:deep(.el-message__content) {
  color: var(--text-color);
}

/* 修复输入区域的阴影 */
.el-textarea__wrapper {
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

.summary-content-wrapper {
  margin-top: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.summary-title {
  border-radius: 0;
  border-bottom: 1px solid #e4e7ed;
}

.summary-content {
  padding: 15px;
  background-color: #fafafa;
  min-height: 150px;
  max-height: 40vh;
  overflow-y: auto;
}

/* 全屏图片预览样式 */
.fullscreen-image-preview {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.9);
  z-index: 20003; /* 确保在导航栏之上 */
  overflow: auto;
  text-align: center;
  padding: 0;
  font-size: 0; /* 消除因行高导致的垂直间隙 */
  cursor: pointer;
}

.fullscreen-preview-image {
  margin: 0; /* 确保图片没有外边距 */
  /* 图片将使用其自然尺寸 */
}

/* 文本卡片样式 */
.text-card {
  max-width: 280px;
  margin: 5px 0;
  overflow: hidden;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-sent .text-card {
  margin-left: auto;
}

.text-card-inner {
  padding: 12px 15px;
  word-break: break-word;
}

.received .text-card {
  background-color: #fff;
}

.sent .text-card {
  background-color: var(--el-color-primary);
  color: white;
}

/* 消息内容样式 */
.message-content {
  padding: 0;
  border-radius: 0;
  background-color: transparent;
  max-width: 280px;
  width: 100%;
}

.message-content-wrapper {
  max-width: 100%;
  width: auto;
}

/* 统一所有卡片样式 */
.image-card, .file-card, .knowledge-card, .text-card {
  width: 100%;
  max-width: 280px;
  margin: 5px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.message-sent .image-card,
.message-sent .file-card,
.message-sent .knowledge-card,
.message-sent .text-card {
  margin-left: auto;
}

/* 文件卡片深色模式样式增强 */
.file-card {
  width: 100%;
  max-width: 280px;
  background-color: #fff;
  color: #333;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 5px 0;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

/* 深色模式下的文件卡片样式 */
:root[data-theme="dark"] .file-card,
body[data-theme="dark"] .file-card {
  background-color: #2a2a2a !important;
  border: 1px solid #3a3a3a !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
}

:root[data-theme="dark"] .file-name,
body[data-theme="dark"] .file-name {
  color: #e0e0e0 !important;
}

:root[data-theme="dark"] .file-size,
body[data-theme="dark"] .file-size {
  color: #aaa !important;
}

:root[data-theme="dark"] .file-download-hint,
body[data-theme="dark"] .file-download-hint {
  color: #4db8ff !important;
  font-weight: 500 !important;
}

:root[data-theme="dark"] .file-icon,
body[data-theme="dark"] .file-icon {
  background-color: #3a3a3a !important;
}

:root[data-theme="dark"] .file-card:hover,
body[data-theme="dark"] .file-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
  background-color: #323232 !important;
}

/* 确保文件名称在深色模式下高对比度 */
:root[data-theme="dark"] .file-name-main,
:root[data-theme="dark"] .file-name-ext,
body[data-theme="dark"] .file-name-main,
body[data-theme="dark"] .file-name-ext {
  color: #fff !important;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.5) !important;
}

/* 移除旧的文本消息样式 */
.message-content span {
  padding: 0;
  border-radius: 0;
  display: inline;
  background-color: transparent;
  color: inherit;
}

.file-name-ext {
  white-space: nowrap;
  flex-shrink: 0;
}

.file-card,
.knowledge-card {
  min-height: 80px;
  display: flex;
  align-items: center;
}

.file-card-inner,
.knowledge-card-inner {
  width: 100%;
}

/* 右键菜单样式 */
.chat-context-menu {
  position: fixed;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  min-width: 150px;
  z-index: 9999;
  padding: 5px 0;
}

.context-menu-item {
  padding: 8px 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.context-menu-item:hover {
  background-color: #f5f7fa;
}

.context-menu-item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}
</style> 
<template>
  <div class="openwebui-chat-root">
    <div class="openwebui-chat-window">
      <div class="openwebui-chat-header">
        <span class="openwebui-title">智慧AI办公助手</span>
        <el-button type="link" size="small" @click="clearChat" class="clear-chat-btn">
          <el-icon><Delete /></el-icon> 新对话
        </el-button>
      </div>
      
      <div class="openwebui-chat-container">
        <div class="openwebui-chat-body" ref="chatBody">
          <div v-for="(msg, idx) in messages" :key="idx" :class="['openwebui-msg', msg.role]">
            <template v-if="msg.role==='assistant'">
              <div class="openwebui-avatar ai-avatar left-avatar">
                <svg viewBox="0 0 40 40" width="36" height="36"><circle cx="20" cy="20" r="20" fill="#2f54eb"/><text x="50%" y="55%" text-anchor="middle" fill="#fff" font-size="20" font-family="Arial" dy=".3em">🤖</text></svg>
              </div>
            </template>
            <template v-if="msg.role==='user'">
              <div class="openwebui-avatar user-avatar right-avatar">
                <img v-if="userAvatarUrl" :src="userAvatarUrl" class="user-avatar-img" alt="用户头像" @error="handleAvatarError" />
                <svg v-else viewBox="0 0 40 40" width="36" height="36"><circle cx="20" cy="20" r="20" fill="#bbb"/><text x="50%" y="55%" text-anchor="middle" fill="#fff" font-size="20" font-family="Arial" dy=".3em">🧑</text></svg>
              </div>
            </template>
            <div class="openwebui-msg-bubble">
              <template v-if="msg.type === 'text'">
                <span v-if="msg.role==='user'">{{ msg.content }}</span>
                <span v-else v-html="msg.content"></span>
                <span v-if="msg.streaming" class="openwebui-cursor"></span>
                <div v-if="msg.source === 'knowledge_base' && msg.role === 'assistant'" class="source-tag knowledge-base-tag">
                  <el-icon><DataAnalysis /></el-icon> 知识库
                </div>
                <div v-if="msg.source === 'general_ai' && msg.role === 'assistant'" class="source-tag general-ai-tag">
                  <el-icon><Cpu /></el-icon> AI大模型
                </div>
              </template>
              <!-- 卡片类型消息渲染（已修改） -->
              <template v-else-if="msg.type === 'card'">
                <div class="openwebui-card-message" :class="getCardClass(msg.status)" :data-event-id="msg.event_id">
                  <div class="card-icon-wrapper">
                    <el-icon><component :is="getCardIcon(msg.status)" /></el-icon>
                  </div>
                  <div class="card-content-wrapper">
                    <div class="card-title">{{ getCardTitle(msg.status) }}</div>
                    <div class="card-body" v-html="msg.content"></div>
                    <!-- 新增：卡片操作按钮 -->
                    <div v-if="msg.status === 'success' && msg.event_id" class="card-actions">
                        <el-button size="small" @click="editEvent(msg)" round>
                          <el-icon><EditPen /></el-icon> 编辑
                        </el-button>
                        <el-button type="danger" size="small" @click="deleteEventFromCard(msg.event_id)" round>
                          <el-icon><Delete /></el-icon> 删除
                        </el-button>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else-if="msg.type === 'file'">
                <div class="file-bubble-nest file-bubble-vertical">
                  <div v-for="file in msg.files" :key="file.name + file.size" class="file-message-card">
                    <div class="file-icon-area">
                      <img v-if="file.ext==='csv'" src="https://cdn.jsdelivr.net/gh/file-icons/icons/svg/csv.svg" class="file-icon-img" />
                      <el-icon v-else><Document /></el-icon>
                    </div>
                    <div class="file-info-area">
                      <div class="file-name">{{ file.name }}</div>
                      <div class="file-meta">{{ file.ext.toUpperCase() }} · {{ file.size }}</div>
                    </div>
                  </div>
                  <div class="file-desc-text" v-if="msg.content">{{ msg.content }}</div>
                </div>
              </template>
            </div>
          </div>
        </div>
        
        <!-- 右侧面板 - 包含模式切换和历史记录 -->
        <div class="openwebui-right-panel" :class="{'collapsed': rightPanelCollapsed}">
          <div class="right-panel-header">
            <!-- 模式切换按钮 -->
            <div class="right-panel-mode-controls">
              <el-radio-group v-model="chatMode" size="default">
                <el-radio-button label="agent">
                  <el-icon><MagicStick /></el-icon> AI助手
                </el-radio-button>
                <el-radio-button label="knowledge_base">
                  <el-icon><DataAnalysis /></el-icon> 知识库
                </el-radio-button>
              </el-radio-group>
            </div>
            
            <!-- 展开/收起按钮 -->
            <el-button 
              circle
              @click="rightPanelCollapsed = !rightPanelCollapsed"
              :title="rightPanelCollapsed ? '展开' : '收起'"
              class="collapse-button"
            >
              <el-icon :size="16">
                <Expand v-if="!rightPanelCollapsed" />
                <Fold v-else />
              </el-icon>
            </el-button>
          </div>
          
          <!-- 历史记录内容 -->
          <div class="history-container">
            <div class="history-header">
              <h3 class="history-title">历史记录</h3>
              <el-button 
                v-if="chatSessions.length > 0"
                text
                size="small" 
                class="clear-all-btn"
                @click="confirmClearAllHistory"
              >
                清空
              </el-button>
            </div>
            
            <div class="history-list">
              <div 
                v-for="(session, index) in chatSessions" 
                :key="session.id"
                class="history-item"
                :class="{'active': session.id === chatId}"
              >
                <div class="history-item-content" @click="switchChatSession(session.id)">
                  <div class="history-item-icon">
                    <el-icon><ChatLineSquare /></el-icon>
                  </div>
                  <div class="history-item-info">
                    <div class="history-item-title">{{ session.title || `对话 ${index + 1}` }}</div>
                    <div class="history-item-time">{{ formatTime(session.created_at) }}</div>
                  </div>
                </div>
                <div class="history-item-actions">
                  <div class="delete-btn-wrapper" @click.stop="deleteSession(session.id)">
                    <el-icon class="delete-icon"><Delete /></el-icon>
                  </div>
                </div>
              </div>
              <div v-if="chatSessions.length === 0" class="history-empty">
                暂无历史记录
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="openwebui-chat-footer">
        <!-- 预览区放在footer顶部 -->
        <div v-if="selectedFiles.length" class="openwebui-file-preview-bar">
          <div v-for="(file, idx) in selectedFiles" :key="file.id" class="openwebui-file-card">
            <div class="openwebui-file-thumb">
              <img v-if="file.type.startsWith('image/')" :src="file.url" class="openwebui-file-img" />
              <div v-else class="openwebui-file-icon" :style="{background: file.bg}">
                <el-icon v-if="file.ext==='pdf'"><Document /></el-icon>
                <el-icon v-else-if="file.ext==='csv' || file.ext==='xls' || file.ext==='xlsx'"><Document /></el-icon>
                <el-icon v-else><Document /></el-icon>
              </div>
            </div>
            <div class="openwebui-file-info">
              <div class="openwebui-file-name" :title="file.name">{{ file.name }}</div>
              <div class="openwebui-file-meta">{{ file.label }} · {{ file.size }}</div>
              <!-- 添加进度条显示 -->
              <el-progress 
                v-if="file.status !== 'completed'" 
                :percentage="file.progress" 
                :status="file.status === 'failed' ? 'exception' : ''" 
                :stroke-width="4"
                class="openwebui-file-progress" />
              <div v-else class="openwebui-file-status completed">
                <el-icon><Check /></el-icon> 处理完成
              </div>
            </div>
            <el-icon class="openwebui-file-remove" @click="removeFile(idx)"><Close /></el-icon>
          </div>
        </div>
        <!-- 输入区 -->
        <div class="openwebui-input-area">
          <input type="file" ref="fileInput" style="display:none" @change="handleFileUpload" multiple 
               accept=".txt,.pdf,.doc,.docx,.md,.xls,.xlsx,.csv,.jpg,.jpeg,.png,.gif,.bmp,.webp,.svg,.tiff" />
          <el-tooltip
            content="文档: txt, pdf, doc, docx, md&#10;表格: xls, xlsx, csv&#10;图片: jpg, jpeg, png, gif, bmp, webp, svg, tiff"
            placement="top"
            popper-class="openwebui-upload-tooltip"
            :open-delay="200"
            v-if="chatMode === 'agent'"
          >
            <el-button class="openwebui-upload-btn" @click="triggerFileInput" title="上传文件/图片" :disabled="loading">
              <el-icon><UploadFilled /></el-icon>
            </el-button>
          </el-tooltip>
          <el-input
            v-model="input"
            placeholder="请输入您的问题..."
            @keyup.enter="sendMsg"
            class="openwebui-input"
            :disabled="loading || processingFiles"
          />
          <el-button type="primary" @click="sendMsg" class="openwebui-send-btn" :loading="loading" :disabled="processingFiles">
            {{ loading ? '生成中' : (processingFiles ? '处理中' : '发送') }}
          </el-button>
        </div>
        <div class="openwebui-options-area" v-if="chatMode === 'knowledge_base'">
            <el-radio-group v-model="searchMethod" size="small">
              <el-radio-button label="basic">基础检索</el-radio-button>
              <el-radio-button label="local">复杂检索</el-radio-button>
            </el-radio-group>
        </div>
        <div class="openwebui-footer-hint" v-if="chatMode === 'agent'">
          支持文档、表格、图片等多种格式文件
        </div>
      </div>
    </div>

    <!-- 新增：编辑日程对话框 -->
    <el-dialog
      v-model="editEventDialogVisible"
      title="编辑日程"
      width="500px"
      class="calendar-dialog"
      :append-to-body="true"
      :destroy-on-close="true"
      :close-on-click-modal="false"
    >
      <el-form :model="editingEvent" label-width="80px" v-if="editingEvent">
        <el-form-item label="标题">
          <el-input v-model="editingEvent.title" placeholder="请输入日程标题"></el-input>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="editingEvent.start"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="editingEvent.end"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="editingEvent.location" placeholder="请输入地点"></el-input>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="editingEvent.type" placeholder="请选择日程类型">
            <el-option label="会议" value="blue"></el-option>
            <el-option label="出差" value="orange"></el-option>
            <el-option label="假期" value="green"></el-option>
            <el-option label="截止日期" value="red"></el-option>
            <el-option label="其他" value="purple"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提醒">
          <el-select v-model="editingEvent.reminder" placeholder="请选择提醒时间">
            <el-option label="不提醒" value="none"></el-option>
            <el-option label="10分钟前" value="10min"></el-option>
            <el-option label="30分钟前" value="30min"></el-option>
            <el-option label="1小时前" value="1hour"></el-option>
            <el-option label="1天前" value="1day"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input 
            v-model="editingEvent.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editEventDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveEditEvent">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, nextTick, computed, onMounted, watch } from 'vue'
import { UploadFilled, Document, Close, Check, Delete, DataAnalysis, Cpu, MagicStick, ChatLineSquare, Fold, Expand, 
  Calendar, ChatDotRound, Collection, DocumentCopy, Grid, Connection, CircleCheckFilled, InfoFilled, CircleCloseFilled, WarningFilled, EditPen } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { marked } from 'marked'
import { ElMessage, ElMessageBox } from 'element-plus'
import { aiChatWithDocumentsStream, getAIChatSessions, getAIChatSession, deleteAIChatSession } from '@/api/ai'
import { deleteCalendarEvent } from '@/api/calendar' // 新增导入
import { getCurrentInstance } from 'vue';
import { getCalendarEvent, updateEvent } from '@/api/calendar' // 新增导入

function formatSize(size) {
  if (size < 1024) return size + 'B';
  if (size < 1024*1024) return (size/1024).toFixed(1) + 'KB';
  return (size/1024/1024).toFixed(1) + 'MB';
}
function getExt(name) {
  const arr = name.split('.');
  return arr.length > 1 ? arr[arr.length-1].toLowerCase() : '';
}
function getFileLabel(type, ext) {
  const ext_lower = ext.toLowerCase();
  if (type.startsWith('image/')) return '图片';
  if (ext_lower === 'pdf') return 'PDF';
  if (['csv','xls','xlsx'].includes(ext_lower)) return '表格';
  if (['doc','docx'].includes(ext_lower)) return '文档';
  if (ext_lower === 'md') return 'Markdown';
  if (ext_lower === 'txt') return '文本';
  return ext_lower.toUpperCase();
}
function getFileBg(ext) {
  const ext_lower = ext.toLowerCase();
  if (ext_lower === 'pdf') return '#f87171'; // 红色
  if (['csv','xls','xlsx'].includes(ext_lower)) return '#34d399'; // 绿色
  if (['doc','docx'].includes(ext_lower)) return '#60a5fa'; // 蓝色
  if (ext_lower === 'md') return '#a78bfa'; // 紫色
  if (ext_lower === 'txt') return '#fbbf24'; // 黄色
  return '#a5b4fc'; // 默认淡紫色
}
function escapeHtml(html) {
  return html.replace(/[&<>"']/g, function(m) {
    return ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[m];
  });
}

// 格式化日期时间
function formatTime(dateTimeStr) {
  if (!dateTimeStr) return '';
  const date = new Date(dateTimeStr);
  return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
}

// ISO日期格式化为可读格式
function formatISODate(isoDateStr) {
  if (!isoDateStr) return '';
  try {
    const date = new Date(isoDateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.error('日期格式化错误:', error);
    return isoDateStr; // 返回原始值
  }
}

export default {
  name: 'Dashboard',
  components: {
    UploadFilled, Document, Close, Check, Delete, DataAnalysis, Cpu, MagicStick, ChatLineSquare, Fold, Expand,
    Calendar, ChatDotRound, Collection, DocumentCopy, Grid, Connection, CircleCheckFilled, InfoFilled, CircleCloseFilled, WarningFilled, EditPen
  },
  setup() {
    const { proxy } = getCurrentInstance();
    const userAvatarUrl = ref(proxy.$store.state.user.avatar)
    const handleAvatarError = () => {
      userAvatarUrl.value = ''; // 加载失败时清空，会显示默认SVG
    };
    
    const input = ref('')
    const messages = ref([
      { 
        role: 'assistant', 
        content: `<div class="welcome-message">
          <h3>欢迎来到智行舟平台</h3>
          <div class="platform-intro">
            <p>智行舟平台是您的智能协作中心，融合了项目管理、即时通讯、智能文档和AI助手等。我们致力于通过前沿AI技术赋能您的团队，优化业务流程，为您打造无缝连接的未来办公新范式，核心优势如下：</p>
            
            <ul class="platform-features">
              <li><span class="feature-highlight">AI智能引擎</span> - 我们的AI助手能够理解自然语言，处理复杂文档，创建日程，成为您24小时的智能工作伙伴。</li>
              <li><span class="feature-highlight">一体化协作</span> - 无缝整合项目、日程与沟通工具，打破信息孤岛，让团队协作如行云流水般顺畅，显著提升效率。</li>
              <li><span class="feature-highlight">智慧文档处理</span> - 从智能合同生成到知识库管理，自动化处理繁杂的文档工作流，让您的团队聚焦于核心创新。</li>
              <li><span class="feature-highlight">安全可靠保障</span> - 采用企业级数据加密与精细化权限管理，全方位守护您的核心数据资产安全。</li>
            </ul>
            
            <p>借助智行舟平台，您的企业将迈入更敏捷、高效、智能的协作新纪元，激发团队潜力，提升整体竞争力。</p>
          </div>
          <p>选择以下功能模块，或直接向我提问，我将为您提供智能助手服务。</p>
          <div class="quick-nav-cards">
            <div class="nav-card" onclick="window.location.href='/project'">
              <div class="nav-card-icon">
                <i class="bi bi-kanban"></i>
              </div>
              <div class="nav-card-content">
                <div class="nav-card-title">项目协作</div>
                <div class="nav-card-desc">任务分配、进度跟踪、团队协作</div>
              </div>
              <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
            </div>
            <div class="nav-card" onclick="window.location.href='/calendar'">
              <div class="nav-card-icon">
                <i class="bi bi-calendar-week"></i>
              </div>
              <div class="nav-card-content">
                <div class="nav-card-title">日程安排</div>
                <div class="nav-card-desc">会议预约、日程提醒、时间管理</div>
              </div>
              <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
            </div>
            <div class="nav-card" onclick="window.location.href='/chat'">
              <div class="nav-card-icon">
                <i class="bi bi-chat-dots"></i>
              </div>
              <div class="nav-card-content">
                <div class="nav-card-title">即时沟通</div>
                <div class="nav-card-desc">团队聊天、文件共享、消息通知</div>
              </div>
              <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
            </div>
            <div class="nav-card" onclick="window.location.href='/smartdoc'">
              <div class="nav-card-icon">
                <i class="bi bi-file-earmark-text"></i>
              </div>
              <div class="nav-card-content">
                <div class="nav-card-title">智能文档</div>
                <div class="nav-card-desc">内容创作、智能问答、文档共享</div>
              </div>
              <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
            </div>
            <div class="nav-card" onclick="window.location.href='/knowledge'">
              <div class="nav-card-icon">
                <i class="bi bi-book"></i>
              </div>
              <div class="nav-card-content">
                <div class="nav-card-title">知识库</div>
                <div class="nav-card-desc">团队知识共享、检索、存储平台</div>
              </div>
              <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
            </div>
            <div class="nav-card" onclick="window.location.href='/contract'">
              <div class="nav-card-icon">
                <i class="bi bi-file-earmark-ruled"></i>
              </div>
              <div class="nav-card-content">
                <div class="nav-card-title">智能合同</div>
                <div class="nav-card-desc">合同模板、AI审查、智能生成</div>
              </div>
              <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
            </div>
          </div>
        </div>`, 
        rawContent: '您好，我是您的AI助手，有什么可以帮您？',
        type: 'text' 
      }
    ])
    const chatBody = ref(null)
    const fileInput = ref(null)
    const selectedFiles = ref([])
    const loading = ref(false)
    const processingFiles = computed(() => {
      return selectedFiles.value.some(file => file.status !== 'completed' && file.status !== 'failed');
    })
    const chatId = ref(null) // 存储当前聊天ID，用于维持对话上下文
    const showContextBar = computed(() => chatId.value !== null)
    const searchMethod = ref('basic') // 新增：搜索方法, 默认为basic
    const chatMode = ref('agent') // agent 或 knowledge_base
    const retrievalScope = ref('local') // 'local' 或 'basic'
    
    // 添加变量来存储当前请求的控制器
    const currentRequestController = ref(null);
    
    // 右侧面板相关状态
    const rightPanelCollapsed = ref(false);
    const chatSessions = ref([]);
    
    // 编辑对话框相关状态
    const editEventDialogVisible = ref(false);
    const editingEvent = ref(null);
    const currentEditingMessage = ref(null);
    
    // 获取 emitter 实例
    const emitter = proxy.emitter;
    
    // 获取聊天会话列表
    const fetchChatSessions = async () => {
      try {
        const res = await getAIChatSessions();
        if (res.data && Array.isArray(res.data)) {
          chatSessions.value = res.data;
        } else if (res.data && res.data.results && Array.isArray(res.data.results)) {
          chatSessions.value = res.data.results;
        }
        return chatSessions.value;
      } catch (error) {
        console.error('获取聊天会话列表失败:', error);
        chatSessions.value = [];
        return [];
      }
    };
    
    // 切换聊天会话
    const switchChatSession = async (sessionId) => {
      if (sessionId === chatId.value) return;
      
      try {
        loading.value = true;
        const res = await getAIChatSession(sessionId);
        if (res.data) {
          chatId.value = sessionId;
          // 加载聊天历史
          if (res.data.messages && Array.isArray(res.data.messages)) {
            messages.value = res.data.messages.map(msg => {
              return {
                role: msg.role,
                content: msg.content,
                rawContent: msg.content,
                type: msg.type || 'text',
                source: msg.role === 'user' ? '' : (msg.source || (msg.role === 'assistant' ? 'general_ai' : '')) // 确保用户消息没有source属性
              }
            });
          }
        }
      } catch (error) {
        console.error('获取聊天会话详情失败:', error);
        ElMessage.error('切换聊天会话失败');
        
        // 如果切换失败，检查当前会话列表中是否还有这个会话
        const sessionExists = chatSessions.value.some(session => session.id === sessionId);
        if (!sessionExists) {
          // 如果会话已不存在，尝试切换到第一个可用会话或创建新会话
          if (chatSessions.value.length > 0) {
            await switchChatSession(chatSessions.value[0].id);
          } else {
            clearChat();
          }
        }
      } finally {
        loading.value = false;
      }
    };

    // 监听聊天ID变化，更新会话列表
    watch(chatId, (newChatId) => {
      if (newChatId) {
        fetchChatSessions();
      }
    });

    // 获取用户信息
    const getUserInfo = async () => {
      try {
        const res = await request({
          url: '/api/auth/users/me/',
          method: 'get'
        })
        console.log('用户信息完整响应:', res)

        // 尝试从响应的不同位置获取头像URL
        let avatarUrl = null
        if (res.data && res.data.data && res.data.data.avatar) {
          avatarUrl = res.data.data.avatar
        } else if (res.data && res.data.avatar) {
          avatarUrl = res.data.avatar
        } else if (res.data) {
          // 遍历res.data查找avatar字段
          const findAvatar = (obj) => {
            if (!obj || typeof obj !== 'object') return null
            
            if ('avatar' in obj) return obj.avatar
            
            // 递归搜索所有子对象
            for (const key in obj) {
              if (typeof obj[key] === 'object') {
                const result = findAvatar(obj[key])
                if (result) return result
              }
            }
            return null
          }
          
          avatarUrl = findAvatar(res.data)
        }

        console.log('找到的头像URL:', avatarUrl)
        
        if (avatarUrl) {
          // 如果是相对路径，添加基础URL
          if (!avatarUrl.startsWith('http') && !avatarUrl.startsWith('data:')) {
            // 确保媒体URL正确拼接
            const baseUrl = window.location.origin
            if (avatarUrl.startsWith('/')) {
              userAvatarUrl.value = `${baseUrl}${avatarUrl}`
            } else {
              userAvatarUrl.value = `${baseUrl}/${avatarUrl}`
            }
          } else {
            userAvatarUrl.value = avatarUrl
          }
          console.log('处理后的用户头像URL:', userAvatarUrl.value)
        } else {
          console.log('用户信息中没有找到头像:', res.data)
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    }
    
    const scrollToBottom = () => {
      nextTick(() => {
        if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
      })
    }
    
    const uploadFileAndGetId = async (file) => {
      const formData = new FormData()
      formData.append('file', file.rawFile)
      try {
        // 标记文件为上传中
        file.progress = 0;
        file.status = 'pending';
        let smoothTimer = null;
        let lastProgress = 0;
        let uploadFinished = false;
        const res = await request({
          url: '/api/ai/documents/upload/',
          method: 'post',
          data: formData,
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            if (percentCompleted < 100) {
              file.progress = percentCompleted;
              lastProgress = percentCompleted;
            } else {
              // 上传瞬间完成，平滑递增到95%
              if (!uploadFinished) {
                uploadFinished = true;
                let fakeProgress = lastProgress;
                smoothTimer = setInterval(() => {
                  fakeProgress += 3;
                  if (fakeProgress >= 95) {
                    fakeProgress = 95;
                    clearInterval(smoothTimer);
                  }
                  file.progress = fakeProgress;
                }, 20);
              }
            }
          }
        })
        // 上传完成后，状态改为处理中，不重置进度条
        if (smoothTimer) clearInterval(smoothTimer);
        if (file.progress < 95) file.progress = 95;
        file.status = 'processing';
        file.documentId = res.data.id;
        pollDocumentStatus(file);
        return res.data.id;
      } catch (error) {
        file.status = 'failed';
        console.error('文件上传失败:', error);
        throw new Error(`上传文件 ${file.name} 失败: ${error.message || '服务器错误'}`);
      }
    }
    
    // 轮询文档处理状态
    const pollDocumentStatus = async (file, interval = 1000) => {
      if (!file.documentId) return;
      
      try {
        const res = await request({
          url: `/api/ai/documents/${file.documentId}/`,
          method: 'get'
        });
        
        if (res.data.status === 'completed') {
          file.progress = 100;
          file.status = 'completed';
          return;
        } else if (res.data.status === 'failed') {
          file.status = 'failed';
          file.progress = 0;
          return;
        } else if (res.data.status === 'processing') {
          // 处理中，增加进度（仅在小于95时递增）
          if (file.progress < 95) {
            file.progress = Math.min(file.progress + 5, 95);
          }
        }
        
        // 继续轮询
        setTimeout(() => pollDocumentStatus(file, interval), interval);
      } catch (e) {
        // 出错时，继续轮询，但不更新进度
        setTimeout(() => pollDocumentStatus(file, interval), interval);
      }
    }
    
    const clearChat = () => {
      // 清空对话历史，开始新的对话
      chatId.value = null;
      
      // 重置消息列表，只保留欢迎消息
      messages.value = [
        { 
          role: 'assistant', 
          content: `<div class="welcome-message">
            <h3>欢迎来到智行舟平台</h3>
            <div class="platform-intro">
              <p>智行舟平台是您的智能协作中心，融合了项目管理、即时通讯、智能文档和AI助手。我们致力于通过前沿AI技术赋能您的团队，优化业务流程，为您打造无缝连接的未来办公新范式，核心优势如下：</p>
              
              <ul class="platform-features">
                <li><span class="feature-highlight">AI智能引擎</span> - 我们的AI助手能够理解自然语言，处理复杂文档，自动创建日程，成为您24小时的智能工作伙伴。</li>
                <li><span class="feature-highlight">一体化协作</span> - 无缝整合项目、日程与沟通工具，打破信息孤岛，让团队协作如行云流水般顺畅，显著提升效率。</li>
                <li><span class="feature-highlight">智慧文档处理</span> - 从智能合同生成到知识库管理，自动化处理繁杂的文档工作流，让您的团队聚焦于核心创新。</li>
                <li><span class="feature-highlight">安全可靠保障</span> - 采用企业级数据加密与精细化权限管理，全方位守护您的核心数据资产安全。</li>
              </ul>
              
              <p>借助智行舟平台，您的企业将迈入更敏捷、高效、智能的协作新纪元，激发团队潜力，提升整体竞争力。</p>
            </div>
            <p>选择以下功能模块，或直接向我提问，我将为您提供智能助手服务。</p>
            <div class="quick-nav-cards">
              <div class="nav-card" onclick="window.location.href='/project'">
                <div class="nav-card-icon">
                  <i class="bi bi-kanban"></i>
                </div>
                <div class="nav-card-content">
                  <div class="nav-card-title">项目协作</div>
                  <div class="nav-card-desc">任务分配、进度跟踪、团队协作</div>
                </div>
                <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
              </div>
              <div class="nav-card" onclick="window.location.href='/calendar'">
                <div class="nav-card-icon">
                  <i class="bi bi-calendar-week"></i>
                </div>
                <div class="nav-card-content">
                  <div class="nav-card-title">日程安排</div>
                  <div class="nav-card-desc">会议预约、日程提醒、时间管理</div>
                </div>
                <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
              </div>
              <div class="nav-card" onclick="window.location.href='/chat'">
                <div class="nav-card-icon">
                  <i class="bi bi-chat-dots"></i>
                </div>
                <div class="nav-card-content">
                  <div class="nav-card-title">即时沟通</div>
                  <div class="nav-card-desc">团队聊天、文件共享、消息通知</div>
                </div>
                <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
              </div>
              <div class="nav-card" onclick="window.location.href='/smartdoc'">
                <div class="nav-card-icon">
                  <i class="bi bi-file-earmark-text"></i>
                </div>
                <div class="nav-card-content">
                  <div class="nav-card-title">AI文档</div>
                  <div class="nav-card-desc">文档摘要、智能问答、内容创作</div>
                </div>
                <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
              </div>
              <div class="nav-card" onclick="window.location.href='/knowledge'">
                <div class="nav-card-icon">
                  <i class="bi bi-book"></i>
                </div>
                <div class="nav-card-content">
                  <div class="nav-card-title">知识库</div>
                  <div class="nav-card-desc">团队知识共享、检索、存储平台</div>
                </div>
                <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
              </div>
              <div class="nav-card" onclick="window.location.href='/contract'">
                <div class="nav-card-icon">
                  <i class="bi bi-file-earmark-ruled"></i>
                </div>
                <div class="nav-card-content">
                  <div class="nav-card-title">智能合同</div>
                  <div class="nav-card-desc">合同模板、AI审查、智能生成</div>
                </div>
                <div class="nav-card-arrow"><i class="nav-arrow-icon">→</i></div>
              </div>
            </div>
          </div>`, 
          rawContent: '您好，我是您的AI助手，有什么可以帮您？',
          type: 'text' 
        }
      ];
      
      // 清空选择的文件
      selectedFiles.value = [];
      
      // 清空输入框
      input.value = '';
      
      // 如果有正在进行的请求，取消它
      if (currentRequestController.value) {
        currentRequestController.value.abort();
        currentRequestController.value = null;
      }
      
      // 重置加载状态
      loading.value = false;
      
      // 滚动到顶部
      nextTick(() => {
        if (chatBody.value) {
          chatBody.value.scrollTop = 0;
        }
      });
      
      // 刷新历史记录列表
      fetchChatSessions();
    }
    
    const processBuffer = (data) => {
        let lastMessage = messages.value[messages.value.length - 1];
        if (!lastMessage || lastMessage.role !== 'assistant') {
            lastMessage = { 
                role: 'assistant', 
                content: '', 
                rawContent: '', 
                type: 'text', 
                streaming: true,
                source: chatMode.value === 'knowledge_base' ? 'knowledge_base' : 'general_ai' // 根据当前模式设置默认source
            };
            messages.value.push(lastMessage);
        }

        if (data.type === 'processing_start') {
            lastMessage.type = 'text';
            lastMessage.content = data.content;
            lastMessage.rawContent = data.content;
            lastMessage.streaming = true;
        } else if (data.type === 'text_chunk') {
            lastMessage.type = 'text';
            lastMessage.streaming = true;
            if (!lastMessage.rawContent || lastMessage.rawContent === "正在为您处理日程...") {
              lastMessage.rawContent = '';
            }
            // 在将内容添加到rawContent之前进行过滤
            const filteredContent = data.content.replace(/\[Data: Sources \(\d+\)\]\.?/g, '');
            lastMessage.rawContent += filteredContent;
            // 流式传输时，实时进行markdown转换
            lastMessage.content = marked.parse(lastMessage.rawContent);
        } else if (data.type === 'final_card') {
            // 仅当是日程相关且有event_id时才显示为卡片
            if (data.event_id && data.is_schedule === true) {
                lastMessage.type = 'card';
                lastMessage.streaming = false;
                lastMessage.content = marked.parse(data.content || '');
                lastMessage.status = data.status || 'clarification';
                lastMessage.event_id = data.event_id || null;
                
                // 如果是成功创建日程，触发日历刷新
                if (data.status === 'success') {
                    emitter.emit('refreshCalendar');
                }
            } else {
                // 非日程相关或无event_id时以文本形式展示
                lastMessage.type = 'text';
                lastMessage.streaming = false;
                lastMessage.rawContent = data.content || '';
                lastMessage.content = marked.parse(lastMessage.rawContent);
            }
        } else if (data.type === 'error') {
            // 如果是日程相关错误且明确指定了is_schedule，才显示为卡片
            if (data.is_schedule === true) {
                lastMessage.type = 'card';
                lastMessage.streaming = false;
                lastMessage.content = data.content || '发生未知错误。';
                lastMessage.status = 'error';
            } else {
                // 非日程错误以文本形式展示
                lastMessage.type = 'text';
                lastMessage.streaming = false;
                lastMessage.rawContent = data.content || '发生未知错误。';
                lastMessage.content = marked.parse(lastMessage.rawContent);
            }
        } else if (data.type === 'update_card') {
            // 仅更新日程卡片
            if (data.is_schedule === true && data.event_id) {
                // 处理卡片更新
                const targetCard = messages.value.find(msg => 
                    msg.type === 'card' && msg.event_id === data.event_id
                );
                
                if (targetCard) {
                    targetCard.content = marked.parse(data.content || '');
                    targetCard.status = data.status || targetCard.status;
                }
            }
        } else if (data.type === 'session_id') {
            // 处理会话ID消息，更新当前聊天ID
            if (data.chat_id && !chatId.value) {
                chatId.value = data.chat_id;
                fetchChatSessions(); // 创建新会话后刷新列表
            }
        }
        scrollToBottom();
    };

    const sendMsg = async () => {
      if (!input.value.trim() && selectedFiles.value.length === 0) {
        ElMessage.warning('请输入内容或上传文件');
        return;
      }
      
      if (processingFiles.value) {
        ElMessage.warning('文件正在处理中，请稍候再试');
        return;
      }
      
      if (currentRequestController.value) {
        currentRequestController.value.abort();
      }
      
      const userMsg = { role: 'user', content: input.value, type: 'text' };
      messages.value.push(userMsg);
      
      if (selectedFiles.value.length > 0) {
        messages.value.push({
          role: 'user',
          content: `上传了${selectedFiles.value.length}个文件`,
          type: 'file',
          files: selectedFiles.value.map(f => ({ name: f.name, size: f.size, ext: f.ext }))
        });
      }
      
      const assistantMsg = { role: 'assistant', content: '', type: 'text', streaming: true, source: chatMode.value === 'knowledge_base' ? 'knowledge_base' : 'general_ai' };
      messages.value.push(assistantMsg);
      
      const currentInput = input.value;
      input.value = '';
      
      const currentDocumentIds = selectedFiles.value.map(f => f.documentId).filter(Boolean);
      selectedFiles.value = [];
      
      scrollToBottom();
      loading.value = true;
      
      // 获取用户的AI个性化设置
      let aiSettings = null;
      try {
        const aiSettingsResponse = await request({
          url: '/api/settings/ai-settings',
          method: 'get'
        });
        
        if (aiSettingsResponse && aiSettingsResponse.success) {
          aiSettings = aiSettingsResponse.data;
        }
      } catch (error) {
        console.error('获取AI个性化设置失败:', error);
        // 即使获取失败也继续聊天
      }
      
      const requestData = {
        message: currentInput,
        chat_id: chatId.value,
        document_ids: currentDocumentIds,
        chatMode: chatMode.value,
        method: searchMethod.value // For knowledge base
      };

      // 添加AI个性化设置
      if (aiSettings) {
        requestData.ai_settings = aiSettings;
      }

      // 统一使用流式请求处理所有模式
      currentRequestController.value = aiChatWithDocumentsStream(
        requestData,
        // onChunk callback
        (payload, newChatId) => {
          if (newChatId && !chatId.value) {
            chatId.value = newChatId;
          }
          processBuffer(payload);
        },
        // onComplete callback
        (newChatId) => {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.streaming = false;
          }
          if (newChatId && !chatId.value) {
            chatId.value = newChatId;
            fetchChatSessions(); // 创建新会话后刷新列表
          }
          loading.value = false;
          currentRequestController.value = null;
        },
        // onError callback
        (error) => {
          console.error('流式请求出错:', error);
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content = '抱歉，响应生成过程中出现错误，请稍后重试。';
            lastMsg.streaming = false;
          }
          loading.value = false;
          currentRequestController.value = null;
          ElMessage.error('请求出错: ' + (error.message || '未知错误'));
        }
      );
    }
    
    const triggerFileInput = () => {
      if (fileInput.value) fileInput.value.value = '';
      fileInput.value && fileInput.value.click()
    }
    
    const handleFileUpload = (e) => {
      const files = e.target.files
      if (!files || !files.length) return
      
      // 支持的文件类型配置
      const allowedTypes = {
        // 文档类型
        'text/plain': 'txt',                          // txt文件
        'application/pdf': 'pdf',                     // pdf文件
        'application/msword': 'doc',                  // doc文件
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx', // docx文件
        'text/markdown': 'md',                        // markdown文件
        'text/x-markdown': 'md',                      // markdown文件变体
        
        // 表格类型
        'text/csv': 'csv',                            // csv文件
        'application/csv': 'csv',                     // csv文件另一种MIME
        'application/vnd.ms-excel': 'xls',            // xls文件
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx', // xlsx文件
        
        // 图片类型
        'image/jpeg': 'jpg',                          // jpg/jpeg图片
        'image/png': 'png',                           // png图片
        'image/gif': 'gif',                           // gif图片
        'image/bmp': 'bmp',                           // bmp图片
        'image/webp': 'webp',                         // webp图片
        'image/svg+xml': 'svg',                       // svg矢量图
        'image/tiff': 'tiff'                          // tiff图片
      };
      
      // 显示支持的文件格式提示
      const supportedFormats = '支持的文件格式: txt, pdf, doc, docx, md, xls, xlsx, csv 和常见图片格式';
      
      // 检查每个文件
      const validFiles = [];
      let hasInvalidFile = false;
      
      // 有效的文件扩展名列表（不区分大小写）
      const validExtensions = ['txt', 'pdf', 'doc', 'docx', 'md', 'xls', 'xlsx', 'csv', 
                              'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff'];
      
      Array.from(files).forEach(file => {
        const ext = getExt(file.name).toLowerCase();
        const isValidExtension = validExtensions.includes(ext);
        
        // 检查MIME类型或扩展名是否有效
        if (allowedTypes[file.type] || isValidExtension) {
          const id = file.name + '_' + file.size + '_' + Date.now() + Math.random()
          if (file.type.startsWith('image/')) {
            const reader = new FileReader()
            reader.onload = (ev) => {
              selectedFiles.value.push({
                id,
                name: file.name,
                type: file.type,
                url: ev.target.result,
                size: formatSize(file.size),
                ext,
                label: getFileLabel(file.type, ext),
                bg: getFileBg(ext),
                rawFile: file,
                progress: 0,
                status: 'ready'
              })
              // 自动上传
              uploadFileAndGetId(selectedFiles.value[selectedFiles.value.length - 1])
            }
            reader.readAsDataURL(file)
          } else {
            selectedFiles.value.push({
              id,
              name: file.name,
              type: file.type,
              url: URL.createObjectURL(file),
              size: formatSize(file.size),
              ext,
              label: getFileLabel(file.type, ext),
              bg: getFileBg(ext),
              rawFile: file, // 直接使用原始file对象
              progress: 0,
              status: 'ready'
            })
            // 自动上传
            uploadFileAndGetId(selectedFiles.value[selectedFiles.value.length - 1])
          }
          validFiles.push(selectedFiles.value[selectedFiles.value.length - 1])
        } else {
          hasInvalidFile = true;
          ElMessage.error(`不支持的文件类型: ${file.name}`);
          console.warn(`文件类型拒绝: ${file.name}, MIME: ${file.type}, 扩展名: ${ext}`);
        }
      })
      
      // 在有不支持文件类型时显示支持的格式信息
      if (hasInvalidFile) {
        ElMessage.info(supportedFormats);
      }
      
      // 如果全部文件都是有效的，显示成功上传提示
      if (validFiles.length > 0 && validFiles.length === files.length) {
        ElMessage.success(`已添加${validFiles.length}个文件`);
      }
    }
    
    const removeFile = (idx) => {
      selectedFiles.value.splice(idx, 1)
    }

    // marked配置：表格带边框+代码块美化+复制按钮
    const renderer = new marked.Renderer();
    renderer.table = function(header, body) {
      return `<table class="openwebui-md-table"><thead>${header}</thead><tbody>${body}</tbody></table>`;
    };
    renderer.code = function(code, infostring, escaped) {
      const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
      let lang = (infostring || '').split(/\s+/)[0];
      let langLabel = lang ? lang : 'code';
      let langClass = lang ? `language-${lang}` : '';
      return `
        <div class="openwebui-md-code-block-beauty">
          <div class="openwebui-md-code-toolbar">
            <span class="openwebui-md-code-lang">${langLabel}</span>
            <button class="openwebui-copy-btn" data-clipboard-target="#${codeId}" title="复制代码">复制</button>
          </div>
          <pre class="openwebui-md-pre"><code id="${codeId}" class="${langClass}">${escaped ? code : escapeHtml(code)}</code></pre>
        </div>
      `;
    };
    
    // 新增：自定义扩展，禁用删除线功能
    const disableStrikethrough = {
      walkTokens(token) {
        if (token.type === 'del') {
          // 将删除线（del）类型的token改写为普通文本（text）类型
          token.type = 'text';
          token.text = token.raw; // 使用原始文本，保留'~~'
          delete token.tokens;
        }
      },
    };

    marked.use(disableStrikethrough);
    
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: false,
      mangle: false,
      renderer
    })

    // --- 卡片样式辅助函数 (新增) ---
    const getCardClass = (status) => {
      switch (status) {
        case 'success':
          return 'success-card';
        case 'error':
          return 'error-card';
        case 'clarification':
          return 'clarification-card';
        case 'deleted':
          return 'deleted-card';
        default:
          return '';
      }
    };
    const getCardIcon = (status) => {
      switch (status) {
        case 'success':
          return 'CircleCheckFilled';
        case 'error':
          return 'CircleCloseFilled';
        case 'clarification':
          return 'InfoFilled';
        case 'deleted':
          return 'WarningFilled';
        default:
          return 'InfoFilled';
      }
    };
    const getCardTitle = (status) => {
      switch (status) {
        case 'success':
          return '日程操作成功';
        case 'error':
          return '操作失败';
        case 'clarification':
          return '需要确认';
        case 'deleted':
          return '日程已删除';
        default:
          return '提示信息';
      }
    };
    // ------------------------------------
    
    // 导航到其他模块
    const navigateTo = (path) => {
      // 获取当前路由路径
      const currentPath = window.location.pathname;
      // 如果已经在指定路径，不进行跳转
      if (currentPath.includes(path)) return;
      
      // 在同一tab中导航
      window.location.href = `/${path}`;
    }

    // 这个方法在welcome-message中使用
    const navigateToModule = (path) => {
      navigateTo(path);
    }

    // 删除单个聊天会话
    const deleteSession = async (sessionId) => {
      try {
        await ElMessageBox.confirm(
          '确认要删除这条对话记录吗？',
          '提示',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'info',
          }
        );
        
        await deleteAIChatSession(sessionId);
        
        // 刷新会话列表
        await fetchChatSessions();
        
        // 无论删除的是不是当前会话，都直接创建新会话
        clearChat(); // 清空当前会话，创建新对话
        ElMessage.success('对话已删除，已创建新对话');
      } catch (error) {
        if (error !== 'cancel' && error !== 'close') {
          console.error('删除聊天会话失败:', error);
          ElMessage.error('删除失败，请稍后重试');
        }
      }
    }

    // 确认清空所有历史记录
    const confirmClearAllHistory = () => {
      ElMessageBox.confirm(
        '确认要清空所有历史记录吗？此操作不可恢复。',
        '警告',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
        .then(() => {
          clearAllHistory();
        })
        .catch(() => {
          // 用户取消，不做任何操作
        });
    }

    // 清空所有历史记录
    const clearAllHistory = async () => {
      try {
        // 显示加载状态
        loading.value = true;
        
        for (const session of chatSessions.value) {
          await deleteAIChatSession(session.id);
        }
        
        // 清空会话列表
        chatSessions.value = [];
        
        // 清空当前会话，创建新对话
        clearChat();
        
        ElMessage.success('所有历史记录已清空，已创建新对话');
      } catch (error) {
        console.error('清空历史记录失败:', error);
        ElMessage.error('操作失败，请稍后重试');
      } finally {
        // 关闭加载状态
        loading.value = false;
      }
    }

    onMounted(() => {
      document.body.addEventListener('click', function(e) {
        if (e.target.classList && e.target.classList.contains('openwebui-copy-btn')) {
          const codeId = e.target.getAttribute('data-clipboard-target').replace('#', '');
          const codeElem = document.getElementById(codeId);
          if (codeElem) {
            navigator.clipboard.writeText(codeElem.innerText).then(() => {
              e.target.innerText = '已复制';
              setTimeout(() => { e.target.innerText = '复制'; }, 1200);
            });
          }
        }
      });
      
      // 获取用户头像
      getUserInfo();
      
      // 获取聊天会话列表并初始化界面
      fetchChatSessions().then(() => {
        // 如果没有历史会话，确保显示新对话界面
        if (chatSessions.value.length === 0) {
          clearChat();
        }
      });
      
      // 添加页面卸载时的清理
      window.addEventListener('beforeunload', () => {
        if (currentRequestController.value) {
          currentRequestController.value.abort();
        }
      });
    });

    // 监控日历刷新事件
    emitter.on('refreshCalendar', () => {
      // 假设日历有自己的刷新方法，这里我们调用它
      // 如果日历组件有ref, 可以是 this.$refs.calendar.fetchEvents();
      // 或者如果刷新逻辑在当前组件内，直接调用
      console.log('收到日历刷新事件，正在重新加载数据...');
      // 示例: findCalendarComponentAndRefresh();
    });

    // --- 新增：卡片操作函数 ---
    const editEvent = async (msg) => {
      if (!msg || !msg.event_id || msg.is_schedule !== true) {
        ElMessage.error('无效的日程信息，无法编辑');
        return;
      }
      
      try {
        // 获取事件详情
        const response = await getCalendarEvent(msg.event_id);
        
        if (!response || !response.data) {
          ElMessage.error('无法获取日程详情，请稍后重试');
          return;
        }
        
        // 设置编辑事件数据
        editingEvent.value = {...response.data};
        currentEditingMessage.value = msg;
        
        // 显示编辑对话框
        editEventDialogVisible.value = true;
      } catch (error) {
        console.error('获取日程详情出错:', error);
        ElMessage.error('获取日程信息失败: ' + (error.response?.data?.message || error.message || '未知错误'));
      }
    };

    // 保存编辑后的事件
    const saveEditEvent = async () => {
      if (!editingEvent.value || !currentEditingMessage.value) {
        ElMessage.error('编辑数据无效');
        return;
      }
      
      // 简单验证
      if (!editingEvent.value.title) {
        ElMessage.warning('请输入日程标题');
        return;
      }
      
      // 组装更新数据
      const updateData = {
        title: editingEvent.value.title,
        start: editingEvent.value.start,
        end: editingEvent.value.end,
        location: editingEvent.value.location || '',
        description: editingEvent.value.description || '',
        type: editingEvent.value.type,
        reminder: editingEvent.value.reminder || 'none'
      };
      
      try {
        // 调用更新API
        await updateEvent(editingEvent.value.id, updateData);
        
        // 更新消息卡片内容
        if (currentEditingMessage.value) {
          const title = editingEvent.value.title;
          const start = formatISODate(editingEvent.value.start);
          const end = formatISODate(editingEvent.value.end);
          const location = editingEvent.value.location;
          
          let content = `已成功更新日程：**${title}**\n\n`;
          content += `- **时间**: ${start} - ${end}\n`;
          if (location) content += `- **地点**: ${location}\n`;
          
          currentEditingMessage.value.content = marked.parse(content);
          currentEditingMessage.value.status = 'success';
        }
        
        // 触发日历刷新事件
        emitter.emit('refreshCalendar');
        
        ElMessage.success('日程已成功更新！');
        
        // 关闭对话框
        editEventDialogVisible.value = false;
      } catch (error) {
        console.error('更新日程失败:', error);
        ElMessage.error('更新失败: ' + (error.response?.data?.message || error.message || '未知错误'));
      }
    };

    // 从卡片中删除日程
    const deleteEventFromCard = async (eventId) => {
      if (!eventId) {
        ElMessage.error('无法删除：缺少事件ID');
        return;
      }
      
      try {
        await ElMessageBox.confirm(
          '您确定要删除这个日程吗？',
          '提示',
          {
            confirmButtonText: '确认删除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        );
        
        // 调用删除API
        await deleteCalendarEvent(eventId);
        
        // 找到包含这个事件ID的卡片消息
        const eventMsg = messages.value.find(msg => 
          msg.type === 'card' && msg.event_id === eventId && msg.is_schedule === true
        );
        
        if (eventMsg) {
          // 获取事件标题
          const titleMatch = eventMsg.content.match(/\*\*([^*]+)\*\*/);
          const eventTitle = titleMatch ? titleMatch[1] : '开会';
          
          // 更新卡片显示为已删除，但使用简洁的确认消息
          eventMsg.status = 'deleted';
          eventMsg.content = `好的，名为"${eventTitle}"的事件已成功删除。`;
        }
        
        // 触发日历刷新事件
        emitter.emit('refreshCalendar');
        
        ElMessage.success('日程已删除');
      } catch (error) {
        if (error === 'cancel') return;
        
        if (error.response?.status === 404) {
          ElMessage.error('操作失败：该日程已被删除或不存在。');
        } else {
          console.error("从卡片删除日程时出错:", error);
          ElMessage.error('删除失败：' + (error.response?.data?.message || error.message || '未知错误'));
        }
      }
    };
    
    // 更新卡片显示
    const updateCardDisplay = (msg, title, description) => {
      // 构建新的卡片内容
      const eventDate = new Date();
      const dateStr = `${eventDate.getFullYear()}年${eventDate.getMonth() + 1}月${eventDate.getDate()}日`;
      let content = `已成功更新日程：**${title}**\n\n`;
      content += `日期：${dateStr}\n\n`;
      if (description) {
        content += `描述：${description}\n\n`;
      }
      content += `您可以在日历中查看完整详情。`;
      
      // 更新卡片内容
      msg.content = marked.parse(content);
      
      // 确保卡片状态为成功
      msg.status = 'success';
      
      // 强制重新渲染卡片
      nextTick(() => {
        const cardElement = document.querySelector(`.openwebui-card-message[data-event-id="${msg.event_id}"]`);
        if (cardElement) {
          cardElement.classList.remove('clarification-card', 'error-card', 'deleted-card');
          cardElement.classList.add('success-card');
        }
      });
    };
    
    // 为日期选择器格式化日期 (保留此函数以兼容其他地方的调用)
    const formatDateForPicker = (date) => {
      if (!date) return '';
      
      try {
        // 确保使用有效的Date对象
        let dateObj;
        if (date instanceof Date) {
          if (isNaN(date.getTime())) {
            console.error('无效日期对象', date);
            dateObj = new Date(); // 使用当前时间作为回退
          } else {
            dateObj = date;
          }
        } else {
          // 尝试解析字符串日期
          dateObj = new Date(date);
          if (isNaN(dateObj.getTime())) {
            console.error('无效日期字符串', date);
            dateObj = new Date(); // 使用当前时间作为回退
          }
        }
      
        // 使用直接获取年月日时分的方式，不涉及时区转换
        const year = dateObj.getFullYear();
        const month = (dateObj.getMonth() + 1).toString().padStart(2, '0');
        const day = dateObj.getDate().toString().padStart(2, '0');
        const hours = dateObj.getHours().toString().padStart(2, '0');
        const minutes = dateObj.getMinutes().toString().padStart(2, '0');
        
        const formatted = `${year}-${month}-${day} ${hours}:${minutes}`;
        return formatted;
      } catch (error) {
        console.error('日期格式化错误:', error);
        // 返回当前时间作为回退选项
        const now = new Date();
        return `${now.getFullYear()}-${(now.getMonth() + 1).toString().padStart(2, '0')}-${now.getDate().toString().padStart(2, '0')} ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      }
    };

    return {
      input, 
      messages, 
      sendMsg, 
      chatBody, 
      fileInput,
      triggerFileInput, 
      handleFileUpload, 
      selectedFiles, 
      removeFile, 
      UploadFilled, 
      Document, 
      Close, 
      Check,
      loading, 
      processingFiles,
      clearChat,
      showContextBar,
      chatId,
      userAvatarUrl,
      handleAvatarError,
      searchMethod,
      chatMode,
      retrievalScope,
      // 右侧面板相关
      rightPanelCollapsed,
      chatSessions,
      switchChatSession,
      formatTime,
      navigateTo,
      navigateToModule,
      // 图标组件
      Calendar, 
      ChatDotRound, 
      Collection, 
      DocumentCopy,
      Grid,
      Connection,
      deleteSession,
      confirmClearAllHistory,
      clearAllHistory,
      getCardClass,
      getCardIcon,
      getCardTitle,
      editEvent,
      deleteEventFromCard,
      editEventDialogVisible,
      editingEvent,
      saveEditEvent,
      // 添加这两个函数以解决ESLint警告
      updateCardDisplay,
      formatDateForPicker,
    }
  }
}
</script>

<style scoped lang="scss">
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.openwebui-chat-root {
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  background: var(--bg-color);
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.openwebui-chat-window {
  width: 100%;
  height: 100%;
  min-height: 0;
  background: var(--bg-color);
  border-radius: 0;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 0;
}

.openwebui-chat-header {
  height: 56px;
  background: var(--bg-color-secondary);
  display: flex;
  align-items: center;
  padding: 0 24px;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  justify-content: space-between;
  color: var(--text-color);
}

.header-center-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.openwebui-title {
  color: var(--primary-color);
}

.clear-chat-btn {
  color: var(--text-color-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: normal;
}

.clear-chat-btn:hover {
  color: var(--primary-color);
}

.openwebui-file-preview-bar {
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0 8px 0;
  background: transparent;
  border-bottom: none;
  overflow-x: auto;
  min-height: 64px;
  z-index: 3;
}

.openwebui-file-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  background: var(--bg-color-secondary);
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(var(--primary-color-rgb),0.04);
  padding: 8px 16px 8px 8px;
  min-width: 160px;
  max-width: 240px;
  position: relative;
  color: var(--text-color);
}

.openwebui-file-thumb {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--bg-color-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-right: 10px;
}

.openwebui-file-img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 8px;
}

.openwebui-file-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
}

.openwebui-file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.openwebui-file-name {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.openwebui-file-meta {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-top: 2px;
}

.openwebui-file-progress {
  margin-top: 4px;
  width: 100%;
}

.openwebui-file-status.completed {
  color: var(--success-color);
}

.openwebui-file-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  color: var(--text-color-tertiary);
  font-size: 16px;
  cursor: pointer;
  transition: color 0.2s;
}

.openwebui-file-remove:hover {
  color: var(--error-color);
}

.openwebui-chat-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.openwebui-chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 12px 16px;
  background: var(--bg-color);
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-height: calc(100vh - 200px);
  height: calc(100vh - 200px);
  flex-shrink: 1;
  scrollbar-width: thin;
  width: auto;
  transition: all 0.3s ease;
}

.openwebui-msg {
  display: flex;
  align-items: flex-end;
  margin-bottom: 16px;
  flex-direction: row;
  justify-content: flex-start;
}

.openwebui-msg.user {
  flex-direction: row-reverse;
  justify-content: flex-end;
  align-items: flex-end;
  margin-left: auto;
  margin-right: 0;
}

.openwebui-msg.assistant {
  flex-direction: row;
  justify-content: flex-start;
  align-items: flex-end;
  margin-right: auto;
  margin-left: 0;
}

.openwebui-msg-bubble {
  position: relative;
  max-width: 90%;
  padding: 12px 18px;
  border-radius: 20px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  line-height: 1.6;
}

.openwebui-msg.user .openwebui-msg-bubble {
  background: var(--primary-color);
  color: #fff;
  border-bottom-right-radius: 4px;
  margin-right: 8px;
  margin-left: auto;
}

.openwebui-msg.assistant .openwebui-msg-bubble {
  background: var(--bg-color-secondary);
  color: var(--text-color);
  border-bottom-left-radius: 4px;
  margin-left: 8px;
  margin-right: auto;
}

.openwebui-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-bottom: auto;
}

.left-avatar {
  margin-right: 8px;
}

.right-avatar {
  margin-left: 8px;
}

.user-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  overflow: hidden;
  display: block;
  background-color: #f0f2f5;
}

.openwebui-user-label {
  font-weight: bold;
  margin-right: 4px;
}

.openwebui-ai-label {
  font-weight: bold;
  color: #2f54eb;
  margin-right: 4px;
}

.openwebui-chat-footer {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: 0 16px 12px 16px;
  background: var(--bg-color);
  border-top: 1px solid var(--border-color);
  margin: 0;
  flex-shrink: 0;
  box-shadow: 0 -2px 16px 0 rgba(var(--primary-color-rgb),0.03);
  z-index: 2;
}

.openwebui-input-area {
  display: flex;
  align-items: center;
  width: 100%;
}

.openwebui-input {
  flex: 1;
  margin-right: 12px;
  height: 40px;
  display: flex;
  align-items: center;
}

.openwebui-send-btn {
  min-width: 72px;
  height: 40px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
}

.openwebui-upload-btn {
  margin-right: 8px;
  font-size: 20px;
  background: var(--bg-color-tertiary);
  border: 1px solid var(--border-color);
  color: var(--primary-color);
  cursor: pointer;
  border-radius: 8px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border 0.2s, box-shadow 0.2s;
}

.openwebui-upload-btn:hover {
  border: 1.5px solid var(--primary-color);
  box-shadow: 0 2px 8px rgba(var(--primary-color-rgb),0.08);
}

.openwebui-img-preview {
  max-width: 180px;
  max-height: 120px;
  border-radius: 8px;
  display: block;
  margin: 4px 0;
  box-shadow: 0 2px 8px rgba(47,84,235,0.08);
}

.openwebui-file-link {
  color: var(--primary-color);
  text-decoration: underline;
  word-break: break-all;
}

.openwebui-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: var(--primary-color);
  margin-left: 2px;
  vertical-align: middle;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0% { opacity: 1; }
  50% { opacity: 0; }
  100% { opacity: 1; }
}

.file-bubble-nest {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.file-bubble-vertical {
  justify-content: flex-start;
  align-items: flex-start;
}

.file-message-card {
  display: flex;
  align-items: center;
  background: var(--bg-color-secondary);
  border-radius: 12px;
  padding: 8px 16px;
  margin-bottom: 0;
  min-width: 180px;
  max-width: 320px;
  box-shadow: 0 2px 8px rgba(var(--primary-color-rgb),0.04);
  color: var(--text-color);
}

.file-icon-area {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.file-icon-img {
  width: 32px;
  height: 32px;
}

.file-info-area {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.file-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 2px;
  word-break: break-all;
}

.file-meta {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.file-desc-text {
  margin-top: 8px;
  font-size: 15px;
  color: var(--text-color);
  background: transparent;
  border-radius: 8px;
  padding: 0 2px;
  display: inline-block;
  word-break: break-all;
}

.openwebui-context-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 24px;
  background-color: var(--bg-color-tertiary);
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--text-color-secondary);
}

.context-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.context-icon {
  color: var(--primary-color);
  font-size: 16px;
}

.source-tag {
  font-size: 10px;
  color: #888;
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 4px;
  .el-icon {
    margin-right: 4px;
  }
}

.knowledge-base-tag {
  background-color: #e8f5e9; /* Light green */
  color: #2e7d32;
}

.general-ai-tag {
  background-color: #e3f2fd; /* Light blue */
  color: #1565c0;
}

/* 右侧面板样式 */
.openwebui-right-panel {
  width: 320px;
  height: 100%;
  background: var(--el-bg-color-page);
  border-left: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}

.openwebui-right-panel.collapsed {
  width: 50px;
}

.right-panel-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color);
  background-color: var(--el-bg-color);
}

.right-panel-mode-controls {
  flex: 1;
  display: flex;
  justify-content: center;
  overflow: hidden;
  transition: opacity 0.3s;
}

.collapsed .right-panel-mode-controls {
  opacity: 0;
  width: 0;
  pointer-events: none;
}

.collapse-button {
  margin-left: 8px;
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  color: var(--text-color);
  transition: all 0.2s ease;
}

.collapse-button:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: scale(1.1);
  box-shadow: 0 0 8px rgba(var(--primary-color-rgb), 0.2);
}

.collapsed .collapse-button {
  margin-left: 0;
}

.history-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background-color: var(--el-bg-color-page);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 16px 0 8px;
  border-bottom: none;
}

.history-title {
  font-size: 15px;
  margin: 0;
  color: var(--el-text-color-regular);
  transition: opacity 0.2s;
  line-height: 1.2;
  font-weight: 500;
}

.clear-all-btn {
  padding: 4px 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 4px;
}

.clear-all-btn:hover {
  background-color: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 4px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 18px;
  background: var(--el-bg-color);
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  margin-bottom: 8px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: none;
}

.history-item:hover {
  background: var(--el-bg-color-page);
  border-color: var(--el-border-color);
  box-shadow: var(--el-box-shadow-light);
}

.history-item.active {
  background: var(--el-color-primary);
  color: white;
  border-color: var(--el-color-primary);
}

.history-item-content {
  display: flex;
  align-items: center;
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.history-item-icon {
  min-width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--el-color-primary-light-9);
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  font-size: 14px;
}

.history-item.active .history-item-icon {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.history-item-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.history-item-title {
  font-size: 14.5px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
}

.history-item-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.history-item.active .history-item-time {
  color: rgba(255, 255, 255, 0.8);
}

.history-item-actions {
  opacity: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
}

.delete-btn-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(245, 108, 108, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
}

.delete-btn-wrapper:hover {
  background-color: rgba(245, 108, 108, 0.15);
}

.delete-icon {
  font-size: 17px;
  color: var(--el-color-danger);
  transition: all 0.2s ease;
}

.history-empty {
  text-align: center;
  padding: 30px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  font-style: normal;
}

.collapsed .history-item {
  justify-content: center;
  padding: 10px 0;
}

.collapsed .history-item-icon {
  margin-right: 0;
}

.collapsed .history-item-info,
.collapsed .history-item-actions {
  display: none;
}

.collapsed .history-title {
  opacity: 0;
  height: 0;
  margin: 0;
  padding: 0;
}

.collapsed .history-container {
  display: none;
}

.collapsed .right-panel-header {
  justify-content: center;
  padding-left: 0;
  padding-right: 0;
  border-bottom-color: transparent;
}

/* 新增卡片消息样式 */
.openwebui-card-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px; /* 减小内边距，让卡片更紧凑 */
  width: 100%; /* 确保卡片填满气泡 */
}

.card-icon-wrapper {
  font-size: 24px;
  margin-top: 2px;
}

.card-content-wrapper {
  flex: 1;
  text-align: left;
}

.card-title {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 4px;
}

.card-body {
  font-size: 14px;
  line-height: 1.5;
  // 确保换行符生效
  white-space: pre-wrap;
  :deep(p) {
    margin: 0;
  }
}

/* 新增：卡片操作区域样式 */
.card-actions {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 根据状态设置不同颜色 */
.success-card .card-icon-wrapper {
  color: #67c23a; /* Element Plus 成功色 */
}
.success-card .card-title {
  color: #67c23a;
}
.openwebui-msg.assistant .openwebui-msg-bubble .success-card {
  border-left: 4px solid #67c23a;
}

.clarification-card .card-icon-wrapper {
  color: #e6a23c; /* Element Plus 警告色 */
}
.clarification-card .card-title {
  color: #e6a23c;
}
.openwebui-msg.assistant .openwebui-msg-bubble .clarification-card {
  border-left: 4px solid #e6a23c;
}

.error-card .card-icon-wrapper {
  color: #f56c6c; /* Element Plus 危险色 */
}
.error-card .card-title {
  color: #f56c6c;
}
.openwebui-msg.assistant .openwebui-msg-bubble .error-card {
  border-left: 4px solid #f56c6c;
}

.deleted-card .card-icon-wrapper {
  color: #909399; /* Element Plus 灰色 */
}
.deleted-card .card-title {
  color: #909399;
}
.openwebui-msg.assistant .openwebui-msg-bubble .deleted-card {
  border-left: 4px solid #909399;
}
</style>

<style>
.openwebui-md-table {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  background: var(--bg-color-secondary);
  font-size: 15px;
}
.openwebui-md-table th, .openwebui-md-table td {
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  text-align: left;
  color: var(--text-color);
  background: var(--bg-color-secondary);
}
.openwebui-md-table th {
  background: var(--bg-color-tertiary);
  font-weight: 600;
  color: var(--text-color-secondary);
}
/* 代码块美化和复制按钮 */
.openwebui-md-code-block-beauty {
  position: relative;
  background: var(--bg-color-tertiary);
  border-radius: 12px;
  margin: 18px 0;
  box-shadow: 0 4px 16px var(--shadow-color);
  overflow: hidden;
  border: 1px solid var(--border-color);
}
.openwebui-md-code-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-color-secondary);
  border-bottom: 1px solid var(--border-color);
  height: 36px;
  padding: 0 14px;
}
.openwebui-md-code-lang {
  font-size: 13px;
  color: var(--text-color-tertiary);
  font-family: 'JetBrains Mono', 'Fira Mono', 'Consolas', monospace;
  user-select: none;
}
.openwebui-copy-btn {
  background: var(--bg-color-tertiary);
  border: 1px solid var(--border-color);
  color: var(--primary-color);
  border-radius: 6px;
  font-size: 13px;
  padding: 2px 12px;
  cursor: pointer;
  z-index: 2;
  transition: background 0.2s, border 0.2s, color 0.2s;
  outline: none;
  margin-left: 8px;
}
.openwebui-copy-btn:hover {
  background: var(--primary-color);
  color: #fff;
  border: 1px solid var(--primary-color);
}
.openwebui-md-pre {
  margin: 0;
  padding: 16px 18px;
  background: var(--bg-color-tertiary);
  border-radius: 0 0 12px 12px;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Mono', 'Consolas', monospace;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-color);
  min-height: 40px;
}
@media (max-width: 600px) {
  .openwebui-md-pre {
    font-size: 13px;
    padding: 12px 6px;
  }
  .openwebui-md-code-block-beauty {
    margin: 12px 0;
  }
}
</style>

<style>
.openwebui-footer-hint {
  font-size: 12px;
  color: var(--text-color-secondary);
  text-align: center;
  padding-top: 8px;
  user-select: none;
  width: 100%;
}
</style>

<style>
.openwebui-upload-tooltip {
  max-width: 300px !important;
  background: var(--bg-color-secondary) !important;
  color: var(--text-color) !important;
  border: 1px solid var(--primary-color) !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.2) !important;
  padding: 10px 14px !important;
  font-size: 13px !important;
  line-height: 1.6 !important;
  white-space: pre-wrap; /* For newline in content */
}

.openwebui-upload-tooltip .el-popper__arrow::before {
  border-color: var(--primary-color) !important;
  background: var(--bg-color-secondary) !important;
}
</style>

<style lang="scss" scoped>
.openwebui-options-area {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}
</style>

<style>
/* 导航卡片样式 */
.welcome-message {
  margin-bottom: 24px;
  padding: 8px;
  border-radius: 12px;
  background-color: var(--el-bg-color);
}

.welcome-message h3 {
  margin-bottom: 12px;
  font-size: 22px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  text-align: center;
}

.platform-intro {
  background-color: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 18px;
  border-left: 4px solid var(--el-color-primary);
}

.platform-intro p {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14.5px;
  line-height: 1.6;
  text-align: left;
}

.welcome-message p {
  margin-bottom: 22px;
  color: var(--el-text-color-regular);
  font-size: 15px;
  text-align: center;
}

.quick-nav-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 15px;
}

.nav-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 16px;
  background-color: var(--el-bg-color-overlay);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: var(--el-box-shadow-lighter);
  position: relative;
  overflow: hidden;
}

.nav-card:hover {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
  transform: translateY(-3px);
  box-shadow: var(--el-box-shadow-light);
}

body[data-theme="dark"] .nav-card:hover {
  background-color: var(--el-color-primary-dark-2);
}

.nav-card:hover .nav-card-arrow {
  opacity: 1;
  transform: translateX(0);
}

.nav-card-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 46px;
  height: 46px;
  font-size: 22px;
  margin-right: 12px;
  color: #ffffff;
  background-color: var(--el-color-primary);
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.25);
  transition: all 0.3s ease;
}

.nav-card:hover .nav-card-icon {
  transform: scale(1.1);
}

.nav-card-icon .el-icon,
.nav-card-icon .bi {
  font-size: 22px;
}

.nav-card:nth-child(2) .nav-card-icon {
  background-color: #67C23A;
  box-shadow: 0 2px 6px rgba(103, 194, 58, 0.25);
}

.nav-card:nth-child(3) .nav-card-icon {
  background-color: #E6A23C;
  box-shadow: 0 2px 6px rgba(230, 162, 60, 0.25);
}

.nav-card:nth-child(4) .nav-card-icon {
  background-color: #F56C6C;
  box-shadow: 0 2px 6px rgba(245, 108, 108, 0.25);
}

.nav-card:nth-child(5) .nav-card-icon {
  background-color: #909399;
  box-shadow: 0 2px 6px rgba(144, 147, 153, 0.25);
}

.nav-card:nth-child(6) .nav-card-icon {
  background-color: #9c27b0;
  box-shadow: 0 2px 6px rgba(156, 39, 176, 0.25);
}

.nav-card-content {
  flex: 1;
}

.nav-card-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
}

.nav-card-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.nav-card-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateX(10px);
  transition: all 0.3s ease;
  color: var(--el-color-primary);
  font-weight: bold;
  font-size: 18px;
  margin-left: 5px;
}

.nav-arrow-icon {
  font-style: normal;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .quick-nav-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .nav-card {
    padding: 12px;
    flex-direction: column;
    text-align: center;
  }
  
  .nav-card-icon {
    margin-right: 0;
    margin-bottom: 10px;
    width: 42px;
    height: 42px;
  }
  
  .nav-card-title {
    margin-bottom: 4px;
  }
  
  .nav-card-arrow {
    position: absolute;
    top: 8px;
    right: 8px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .welcome-message h3 {
    font-size: 18px;
  }
  
  .welcome-message p {
    font-size: 14px;
    margin-bottom: 16px;
  }
  
  .quick-nav-cards {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .nav-card {
    flex-direction: row;
    text-align: left;
    padding: 12px;
  }
  
  .nav-card-icon {
    margin-right: 12px;
    margin-bottom: 0;
  }
}

/* 更新平台介绍样式 */
.platform-intro {
  background-color: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 22px;
  border-left: 4px solid var(--el-color-primary);
  box-shadow: var(--el-box-shadow-lighter);
}

.platform-intro p {
  margin: 0 0 12px;
  color: var(--el-text-color-regular);
  font-size: 14.5px;
  line-height: 1.6;
}

.platform-intro p:last-child {
  margin-bottom: 0;
  font-style: italic;
  color: #606266;
}

.platform-features {
  padding-left: 18px;
  margin: 12px 0 14px;
  list-style-type: none;
}

.platform-features li {
  position: relative;
  padding-left: 8px;
  margin-bottom: 10px;
  font-size: 14px;
  color: #454b54;
  line-height: 1.5;
}

.platform-features li::before {
  content: "•";
  position: absolute;
  left: -12px;
  color: #409EFF;
  font-weight: bold;
}

.feature-highlight {
  font-weight: 600;
  color: #303133;
}

/* 修改一下welcome-message样式 */
.welcome-message h3 {
  margin-bottom: 16px;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  text-align: center;
}

.welcome-message > p {
  margin-bottom: 22px;
  color: #606266;
  font-size: 15px;
  text-align: center;
}
</style> 

<!-- 添加事件编辑表单样式 -->
<style>
.event-edit-dialog .el-message-box__input {
  padding: 0;
}

.event-edit-dialog .el-message-box__input input {
  display: none;
}

.event-edit-form {
  padding: 10px 0;
}

.event-edit-form .form-group {
  margin-bottom: 15px;
}

.event-edit-form label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: var(--text-color);
}

.event-edit-form .form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-size: 14px;
  transition: border-color 0.2s;
}

.event-edit-form .form-control:focus {
  border-color: var(--primary-color);
  outline: none;
}

.event-edit-form textarea.form-control {
  min-height: 80px;
  resize: vertical;
}

.event-edit-form select.form-control {
  appearance: auto;
  height: 38px;
  background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
  padding-right: 2.5rem;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* 增加对话框宽度 */
.event-edit-dialog .el-message-box {
  width: 400px;
  max-width: 95vw;
}

/* 暗色主题适配 */
body[data-theme="dark"] .event-edit-form .form-control {
  background-color: var(--bg-color-secondary);
  border-color: var(--border-color);
  color: var(--text-color);
}

body[data-theme="dark"] .event-edit-form label {
  color: var(--text-color-secondary);
}

/* 修复datetime-local输入框样式 */
.event-edit-form input[type="datetime-local"] {
  padding-right: 0.75rem;
}

/* 确保表单在不同浏览器中正常显示 */
@supports (-moz-appearance: none) {
  .event-edit-form select.form-control {
    padding-right: 2rem;
    background-image: none;
  }
}
</style>

<style lang="scss" scoped>
// ... existing code ...

/* 卡片消息样式 */
.openwebui-card-message {
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bg-color-secondary);
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.openwebui-card-message:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.card-icon-wrapper {
  margin-right: 12px;
  font-size: 20px;
  padding-top: 2px;
}

.card-content-wrapper {
  flex: 1;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.card-body {
  font-size: 14px;
  color: var(--text-color);
  line-height: 1.5;
}

.card-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

/* 根据状态设置不同颜色 */
.success-card .card-icon-wrapper {
  color: #67c23a; /* Element Plus 成功色 */
}
.success-card .card-title {
  color: #67c23a;
}
.openwebui-msg.assistant .openwebui-msg-bubble .success-card {
  border-left: 4px solid #67c23a;
}

.clarification-card .card-icon-wrapper {
  color: #e6a23c; /* Element Plus 警告色 */
}
.clarification-card .card-title {
  color: #e6a23c;
}
.openwebui-msg.assistant .openwebui-msg-bubble .clarification-card {
  border-left: 4px solid #e6a23c;
}

.error-card .card-icon-wrapper {
  color: #f56c6c; /* Element Plus 危险色 */
}
.error-card .card-title {
  color: #f56c6c;
}
.openwebui-msg.assistant .openwebui-msg-bubble .error-card {
  border-left: 4px solid #f56c6c;
}

.deleted-card .card-icon-wrapper {
  color: #909399; /* Element Plus 灰色 */
}
.deleted-card .card-title {
  color: #909399;
}
.openwebui-msg.assistant .openwebui-msg-bubble .deleted-card {
  border-left: 4px solid #909399;
}
</style>

<!-- 添加事件编辑表单样式 -->
<style>
.event-edit-dialog .el-message-box__input {
  padding: 0;
}

.event-edit-dialog .el-message-box__input input {
  display: none;
}

.event-edit-form {
  padding: 10px 0;
}

.event-edit-form .form-group {
  margin-bottom: 15px;
}

.event-edit-form label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: var(--text-color);
}

.event-edit-form .form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-size: 14px;
  transition: border-color 0.2s;
}

.event-edit-form .form-control:focus {
  border-color: var(--primary-color);
  outline: none;
}

.event-edit-form textarea.form-control {
  min-height: 80px;
  resize: vertical;
}

.event-edit-form select.form-control {
  appearance: auto;
}
</style>

<style>
/* 确保 el-dialog 在暗黑模式下样式正确 */
.calendar-dialog .el-dialog {
  background-color: var(--bg-color);
}
.calendar-dialog .el-dialog__title {
  color: var(--text-color);
}
.calendar-dialog .el-dialog__header {
  border-bottom: 1px solid var(--border-color);
}
.calendar-dialog .el-dialog__body {
  background-color: var(--bg-color);
  color: var(--text-color);
}
.calendar-dialog .el-dialog__footer {
  border-top: 1px solid var(--border-color);
}
.calendar-dialog .el-form-item__label {
  color: var(--text-color);
}
.calendar-dialog .el-input__wrapper,
.calendar-dialog .el-textarea__inner {
  background-color: var(--bg-color-secondary) !important;
  box-shadow: none !important;
  border: 1px solid var(--border-color);
  color: var(--text-color);
}
.calendar-dialog .el-input__inner {
  color: var(--text-color) !important;
}

/* 移除旧的、不再需要的CSS */
.event-edit-dialog .el-message-box__input {
  display: none;
}
.event-edit-form {
  display: none;
}
</style>
<template>
  <div class="smart-doc-container">
    <!-- 文档列表侧边栏 -->
    <div class="sidebar" :class="{ 'collapsed': isDocListCollapsed }">
      <!-- 侧边栏头部 -->
      <div class="sidebar-header">
        <h4 v-if="!isDocListCollapsed">我的文档</h4>
        <div class="toggle-btn" @click="toggleDocList">
          <el-icon><ArrowLeft v-if="!isDocListCollapsed" /><ArrowRight v-else /></el-icon>
        </div>
      </div>

      <!-- 展开状态的文档列表 -->
      <div class="sidebar-content" v-show="!isDocListCollapsed">
        <!-- 搜索和筛选区域 -->
        <div class="search-area">
          <el-input
            placeholder="搜索文档..."
            v-model="searchQuery"
            clearable
            @input="debouncedSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <div class="filter-options">
            <el-input v-model="docTypeFilter" placeholder="文档类型" size="small" clearable />
            <el-select v-model="sortOption" placeholder="排序" size="small">
              <el-option label="最近更新" value="update" />
              <el-option label="最近创建" value="create" />
              <el-option label="名称升序" value="name-asc" />
            </el-select>
          </div>
        </div>

        <!-- 文档列表区域 -->
        <el-scrollbar class="document-list-scrollbar">
          <div v-if="documentsLoading" class="loading-state">
            <el-skeleton :rows="10" animated />
          </div>
          <div v-else class="document-list">
            <div 
              v-for="doc in filteredDocuments" 
              :key="doc.id" 
              class="doc-item"
              :class="{ 'active': currentDoc?.id === doc.id }"
              @click="selectDocument(doc.id)"
            >
              <div class="doc-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="doc-info">
                <h5>{{ doc.title }}</h5>
                <div class="doc-meta">
                  <span>{{ doc.type }}</span>
                  <span>{{ formatDate(doc.update_time) }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="filteredDocuments.length === 0" class="empty-state">
              <el-empty description="暂无文档" :image-size="60">
                <el-button size="small" @click="fetchDocuments(1, [])">重新加载</el-button>
              </el-empty>
            </div>
            
            <div v-if="filteredDocuments.length > 0" class="document-count">
              共 {{ filteredDocuments.length }} 个文档
            </div>
          </div>
        </el-scrollbar>

        <!-- 创建按钮区域 -->
        <div class="action-buttons">
          <el-button type="primary" @click="openNewDocumentDialog">
            <el-icon><Plus /></el-icon> 新建文档
          </el-button>
        </div>
      </div>

      <!-- 折叠状态的文档图标列表 -->
      <div class="collapsed-sidebar" v-if="isDocListCollapsed">
        <el-tooltip content="新建文档" placement="right">
          <div class="icon-btn create-btn" @click="openNewDocumentDialog">
            <el-icon><Plus /></el-icon>
          </div>
        </el-tooltip>
        
        <div class="recent-docs">
          <el-tooltip 
            v-for="doc in filteredDocuments.slice(0, 5)" 
            :key="doc.id" 
            :content="doc.title"
            placement="right"
          >
            <div 
              class="icon-btn doc-btn"
              :class="{ 'active': currentDoc?.id === doc.id }"
              @click="selectDocument(doc.id)"
            >
              <el-icon><Document /></el-icon>
            </div>
          </el-tooltip>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 文档内容显示区域 -->
      <div class="document-content">
        <el-skeleton v-if="loading" :rows="6" animated style="margin:40px" />
        <template v-else-if="currentDoc">
          <!-- 文档标题和操作栏 -->
          <div class="document-header">
            <div class="header-left-actions">
              <el-tooltip content="返回列表" placement="bottom">
                <el-button @click="goBack" circle>
                  <el-icon><ArrowLeftBold /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
            <div class="doc-info-area">
              <div class="doc-title-label">标题：</div>
              <div class="doc-title">
                <el-input 
                  v-model="currentDoc.title"
                  placeholder="文档标题"
                  size="large"
                  @change="onTitleChange"
                />
              </div>
              <div class="doc-type-label">类型：</div>
              <div class="doc-type-selector">
                <el-input 
                  v-model="currentDoc.type" 
                  placeholder="输入文档类型"
                  size="default"
                  @change="onTypeChange"
                />
              </div>
            </div>
            <div class="doc-actions">
              <el-tooltip content="保存文档" placement="bottom">
                <el-button 
                  circle
                  :disabled="!documentChanged" 
                  :loading="saveLoading"
                  @click="saveDocument"
                >
                  <el-icon><CircleCheck /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="导出文档" placement="bottom">
                <el-button circle @click="exportDocument"><el-icon><Download /></el-icon></el-button>
              </el-tooltip>
              <el-tooltip content="更多操作" placement="bottom">
                <el-dropdown trigger="click">
                  <el-button circle><el-icon><More /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="deleteDocument" class="text-red-500">删除文档</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </el-tooltip>
            </div>
          </div>
          
          <!-- 编辑器区域 -->
          <div class="editor-area">
            <QuillEditor
              v-model:content="currentDoc.content"
              :options="editorOptions"
              contentType="html"
              theme="snow"
              class="quill-editor"
              @textChange="onContentChange"
              @ready="onEditorReady"
              placeholder=" "
            />
          </div>
        </template>
        
        <!-- 无文档时的提示 -->
        <div v-else class="empty-doc-state">
          <el-empty description="请选择或创建一个文档">
            <el-button type="primary" @click="openNewDocumentDialog">新建文档</el-button>
          </el-empty>
        </div>
      </div>
    </div>
    
    <!-- 智能助手面板 -->
    <div class="assistant-panel" :class="{ 'collapsed': isAssistantCollapsed }">
      <div class="assistant-header">
        <h5 v-if="!isAssistantCollapsed">AI功能</h5>
        <div class="toggle-btn" @click="toggleAssistant">
          <el-icon><ArrowRight v-if="!isAssistantCollapsed" /><ArrowLeft v-else /></el-icon>
        </div>
      </div>
      
      <div class="assistant-body" v-show="!isAssistantCollapsed">
        <div class="ai-features-beauty">
          <div class="ai-feature-card">
            <el-tooltip content="请先在编辑器中选择文本后再使用此功能" :disabled="hasValidSelection" placement="top" effect="dark">
              <el-button type="primary" class="ai-feature-btn" @click="expandContent" :loading="expandLoading" :disabled="!hasValidSelection">
                <el-icon class="ai-icon"><Edit /></el-icon>
                内容扩写
              </el-button>
            </el-tooltip>
            <div class="ai-feature-desc">将选中文本智能扩展为更丰富内容，适合写作、报告等场景。</div>
          </div>
          <div class="ai-feature-card">
            <el-tooltip content="请先在编辑器中选择文本后再使用此功能" :disabled="hasValidSelection" placement="top" effect="dark">
              <el-button type="success" class="ai-feature-btn" @click="polishText" :loading="polishLoading" :disabled="!hasValidSelection">
                <el-icon class="ai-icon"><StarFilled /></el-icon>
                文本润色
              </el-button>
            </el-tooltip>
            <div class="ai-feature-desc">让表达更专业、流畅，提升文档整体质量。</div>
          </div>
          <div class="ai-feature-card">
            <el-tooltip content="请先在编辑器中选择文本后再使用此功能" :disabled="hasValidSelection" placement="top" effect="dark">
              <el-button type="warning" class="ai-feature-btn" @click="grammarCheckText" :loading="grammarCheckLoading" :disabled="!hasValidSelection">
                <el-icon class="ai-icon"><Edit /></el-icon>
                智能纠错
              </el-button>
            </el-tooltip>
            <div class="ai-feature-desc">AI自动检查语法、错别字、表达不通顺并给出优化建议。</div>
          </div>
          <div class="ai-feature-card">
            <el-button type="info" class="ai-feature-btn" @click="openTranslateDialog">
              <el-icon class="ai-icon"><ChatDotRound /></el-icon>
              多语言翻译
            </el-button>
            <div class="ai-feature-desc">支持多语种精准互译，助力国际化办公。</div>
          </div>
          <div class="ai-feature-card">
            <el-button type="success" class="ai-feature-btn" @click="openQaDialog">
              <el-icon class="ai-icon"><QuestionFilled /></el-icon>
              智能问答
            </el-button>
            <div class="ai-feature-desc">基于文档内容，AI即时解答你的问题。</div>
          </div>
        </div>
      </div>
      
      <!-- 折叠状态的AI功能图标列表 -->
      <div class="collapsed-assistant" v-if="isAssistantCollapsed">
        <el-tooltip :content="hasValidSelection ? '内容扩写' : '请先在编辑器中选择文本'" placement="left">
          <div class="icon-btn" @click="expandContent" :class="{ 'disabled': !hasValidSelection || expandLoading }">
            <el-icon v-if="expandLoading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Edit /></el-icon>
          </div>
        </el-tooltip>
        <el-tooltip :content="hasValidSelection ? '文本润色' : '请先在编辑器中选择文本'" placement="left">
          <div class="icon-btn" @click="polishText" :class="{ 'disabled': !hasValidSelection || polishLoading }">
            <el-icon v-if="polishLoading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><StarFilled /></el-icon>
          </div>
        </el-tooltip>
        <el-tooltip :content="hasValidSelection ? '智能纠错' : '请先在编辑器中选择文本'" placement="left">
          <div class="icon-btn" @click="grammarCheckText" :class="{ 'disabled': !hasValidSelection || grammarCheckLoading }">
            <el-icon v-if="grammarCheckLoading" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Edit /></el-icon>
          </div>
        </el-tooltip>
        <el-tooltip content="多语言翻译" placement="left">
          <div class="icon-btn" @click="openTranslateDialog">
            <el-icon><ChatDotRound /></el-icon>
          </div>
        </el-tooltip>
        <el-tooltip content="智能问答" placement="left">
          <div class="icon-btn" @click="openQaDialog">
            <el-icon><QuestionFilled /></el-icon>
          </div>
        </el-tooltip>
      </div>
    </div>

    <!-- 创建新文档对话框 -->
    <el-dialog
      v-model="newDocumentDialogVisible"
      title="新建智能文档"
      width="35%"
    >
      <el-form 
        :model="newDocumentForm" 
        label-width="80px" 
        :rules="documentFormRules"
        ref="documentFormRef"
      >
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="newDocumentForm.title" placeholder="请输入文档标题" />
        </el-form-item>
        <el-form-item label="文档类型">
          <el-input v-model="newDocumentForm.type" placeholder="请输入文档类型" />
          <div class="form-tip">如果未填写，默认为通用类型</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="newDocumentDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createNewDocument" :loading="createLoading">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除文档"
      width="30%"
    >
      <div v-if="currentDoc">
        <p>您确定要删除文档 <strong>{{ currentDoc.title }}</strong> 吗?</p>
        <p class="warning-text">此操作不可撤销!</p>
        </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmDelete" :loading="deleteLoading">
            删除
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 比较弹窗 -->
    <el-dialog
      v-model="compareDialogVisible"
      :title="compareDialogData.title"
      width="90%"
      class="compare-dialog large-dialog"
      :fullscreen="false"
      :append-to-body="true"
      :destroy-on-close="false"
      :close-on-click-modal="false"
      :show-close="true"
    >
      <div v-if="compareDialogData" class="dialog-container">
        <div class="compare-content">
          <div class="original-content">
            <h6>原始内容</h6>
            <QuillEditor
              v-model:content="compareDialogData.original"
              contentType="text"
              theme="snow"
              :readOnly="true"
              class="quill-editor-in-dialog"
              style="background:#f9f9f9;"
            />
          </div>
          <div class="modified-content">
            <h6>优化建议内容（可编辑）</h6>
            <QuillEditor
              v-model:content="compareDialogData.modifiedContent"
              contentType="text"
              theme="snow"
              class="quill-editor-in-dialog"
            />
          </div>
        </div>
        <div v-if="compareDialogData.suggestions" class="ai-suggestions" style="margin-top:16px;">
          <el-alert
            title="AI纠错建议"
            type="info"
            :closable="false"
            show-icon
            style="font-size:15px;line-height:1.8;"
          >
            <div v-html="compareDialogData.suggestions"></div>
          </el-alert>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeCompareDialog">取消</el-button>
          <el-button type="primary" @click="applyCompareChanges">应用更改</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 多语言翻译弹窗（对比模式） -->
    <el-dialog v-model="translateDialogVisible" title="多语言智能翻译" width="900px" destroy-on-close>
      <div style="margin-bottom:12px; display:flex; align-items:center; gap:12px;">
        <el-select v-model="targetLang" placeholder="选择目标语言" style="width:180px;">
          <el-option label="英文" value="en" />
          <el-option label="中文" value="zh" />
          <el-option label="日文" value="ja" />
          <el-option label="法文" value="fr" />
          <el-option label="德文" value="de" />
          <el-option label="西班牙文" value="es" />
          <el-option label="俄文" value="ru" />
          <el-option label="韩文" value="ko" />
        </el-select>
        <el-button type="primary" :loading="translateLoading" @click="doTranslate">翻译</el-button>
      </div>
      <div class="compare-content">
        <div class="original-content">
          <h6>原文内容</h6>
          <QuillEditor
            v-model:content="translateInput"
            contentType="text"
            theme="snow"
            :readOnly="true"
            class="quill-editor-in-dialog"
            style="background:#f9f9f9;"
          />
        </div>
        <div class="modified-content">
          <h6>翻译内容（可编辑）</h6>
          <QuillEditor
            v-model:content="translateModifiedContent"
            contentType="text"
            theme="snow"
            class="quill-editor-in-dialog"
          />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="translateDialogVisible = false">取消</el-button>
          <el-button v-if="translateModifiedContent" type="success" @click="replaceSelectionWithTranslation">应用翻译</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 智能问答弹窗 -->
    <el-dialog v-model="qaDialogVisible" title="文档智能问答" width="500px">
      <el-input
        v-model="qaQuestion"
        placeholder="请输入您的问题"
        style="margin-bottom:12px;"
        @keyup.enter="doQa"
      />
      <el-button type="primary" :loading="qaLoading" @click="doQa">提问</el-button>
      <div v-if="qaAnswer" style="margin-top:16px;">
        <el-alert title="AI答案" type="info" :closable="false" show-icon>
          <div v-html="qaAnswerHtml"></div>
        </el-alert>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import _ from 'lodash'
import { 
  getDocuments, 
  getDocumentDetail, 
  createDocument, 
  updateDocument,
  deleteDocument as apiDeleteDocument,
  expandContent as apiExpandContent,
  polishText as apiPolishText,
  grammarCheck,
  translateText,
  docQa
} from '@/api/smartdoc'
import { Document, Plus, CircleCheck, Download, More, Search, ArrowLeft, ArrowRight, Edit, StarFilled, ChatDotRound, QuestionFilled, ArrowLeftBold, Loading } from '@element-plus/icons-vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css' // 导入代码高亮样式表

// 配置marked
marked.use(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, { language }).value;
    }
  })
);

// 设置安全选项
marked.use({
  gfm: true,
  breaks: true,
  pedantic: false,
  sanitize: false, // marked v4.3.0不再支持sanitize选项
  smartLists: true,
  smartypants: false
});

export default {
  name: 'SmartDocDetail',
  components: {
    Document, Plus, CircleCheck, Download, More, 
    Search, ArrowLeft, ArrowRight, QuillEditor, Edit, StarFilled, ChatDotRound, QuestionFilled, ArrowLeftBold, Loading
  },
  setup() {
    const router = useRouter();
    const route = useRoute();
    
    const goBack = () => {
      router.push('/smartdoc');
    };
    
    // 状态数据
    const documents = ref([])
    const currentDoc = ref(null)
    const documentChanged = ref(false)
    const isDocListCollapsed = ref(false)
    const isAssistantCollapsed = ref(false)
    const searchQuery = ref('')
    const docTypeFilter = ref('')
    const sortOption = ref('update')
    const newDocumentDialogVisible = ref(false)
    const deleteDialogVisible = ref(false)
    const documentsLoading = ref(true) // 文档加载状态
    
    // 加载状态
    const saveLoading = ref(false)
    const createLoading = ref(false)
    const deleteLoading = ref(false)
    const expandLoading = ref(false)
    const polishLoading = ref(false)
    const grammarCheckLoading = ref(false)
    
    // 表单数据
    const newDocumentForm = ref({
        title: '',
      type: ''
    })
    
    // 表单验证规则
    const documentFormRules = {
      title: [
        { required: true, message: '请输入文档标题', trigger: 'blur' },
        { min: 2, max: 50, message: '标题长度须在2到50个字符之间', trigger: 'blur' }
      ]
    }
    
    const documentFormRef = ref(null)
      
    const uploadImage = async (file) => {
      try {
        // 使用FileReader将文件转换为base64
        const reader = new FileReader()
        return new Promise((resolve, reject) => {
          reader.onload = (e) => {
            const base64Data = e.target.result
            // 直接返回base64数据作为图片URL
            resolve({ url: base64Data })
          }
          reader.onerror = () => {
            reject(new Error('文件读取失败'))
          }
          reader.readAsDataURL(file)
        })
      } catch (error) {
        console.error('图片处理失败:', error)
        throw error
      }
    }
    
      // 编辑器配置
    const editorOptions = {
      placeholder: ' ',
        modules: {
        toolbar: {
          container: [
            ['bold', 'italic', 'underline', 'strike'],
            ['blockquote', 'code-block'],
          [{ 'header': 1 }, { 'header': 2 }],
          [{ 'list': 'ordered' }, { 'list': 'bullet' }],
          [{ 'script': 'sub' }, { 'script': 'super' }],
          [{ 'indent': '-1' }, { 'indent': '+1' }],
          [{ 'direction': 'rtl' }],
          [{ 'size': ['small', false, 'large', 'huge'] }],
          [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
          [{ 'color': [] }, { 'background': [] }],
          [{ 'font': [] }],
          [{ 'align': [] }],
            ['clean'],
          ['link', 'image']
          ],
          handlers: {
            image: function () {
              const input = document.createElement('input')
              input.setAttribute('type', 'file')
              input.setAttribute('accept', 'image/*')
              input.click()
              input.onchange = async () => {
                const file = input.files[0]
                if (!file) return
                
                // 检查文件大小和类型
                if (file.size > 5 * 1024 * 1024) { // 5MB限制
                  ElMessage.error('图片不能超过5MB')
                  return
                }
                
                // 支持的图片类型
                const supportedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if (!supportedTypes.includes(file.type)) {
                  ElMessage.error('只支持JPG、PNG、GIF和WEBP格式图片')
                  return
                }
                
                ElMessage.info('正在处理图片...')
                
                try {
                  // 直接传递文件对象而不是FormData
                  const res = await uploadImage(file)
                  const url = res.url
                  if (!url) throw new Error('无效的图片URL')
                  
                  // 获取编辑器实例并插入图片
                  const quill = quillInstance.value
                  const range = quill.getSelection(true)
                  quill.insertEmbed(range.index, 'image', url)
                  
                  // 标记文档已修改
                  documentChanged.value = true
                  
                  ElMessage.success('图片插入成功')
                } catch (e) {
                  console.error('图片处理失败:', e)
                  ElMessage.error('图片处理失败: ' + e.message)
                }
              }
            }
          }
        }
      }
    }
    
    // 计算属性
    const filteredDocuments = computed(() => {
      let result = [...documents.value]
      
      // 搜索筛选
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(doc => 
          doc.title.toLowerCase().includes(query) || 
          doc.type.toLowerCase().includes(query)
        )
      }
      
      // 类型筛选
      if (docTypeFilter.value) {
        const typeFilter = docTypeFilter.value.toLowerCase()
        result = result.filter(doc => 
          doc.type.toLowerCase().includes(typeFilter)
        )
      }
      
      // 排序
      if (sortOption.value === 'update') {
        result.sort((a, b) => new Date(b.update_time) - new Date(a.update_time))
      } else if (sortOption.value === 'create') {
        result.sort((a, b) => new Date(b.create_time) - new Date(a.create_time))
      } else if (sortOption.value === 'name-asc') {
        result.sort((a, b) => a.title.localeCompare(b.title))
      }
      
      return result
    })
    
    // 添加未定义的变量
    const filteredCount = computed(() => {
      return filteredDocuments.value.length;
    });
    
    // 方法
    const fetchDocuments = async (page = 1, allDocs = []) => {
      if (page === 1) {
        documentsLoading.value = true
      }
      
      try {
        console.log(`开始获取文档列表 第${page}页...`)
        const params = {
          page: page,
          limit: 100,  // 尝试请求更多，尽管后端可能只会返回10条（默认PAGE_SIZE）
          _t: new Date().getTime() // 添加时间戳，确保不使用缓存
        }
        
        const response = await getDocuments(params)
        console.log(`文档列表响应(第${page}页):`, response)
        
        // 处理获取到的数据
        let docsList = [...allDocs]
        let totalCount = 0
        let currentPageDocs = []
        let hasMore = false
        
        // 处理不同格式的响应
        if (response.data && Array.isArray(response.data)) {
          currentPageDocs = response.data
          totalCount = response.count || response.total || 0
          hasMore = docsList.length + currentPageDocs.length < totalCount
        } else if (response.results && Array.isArray(response.results)) {
          currentPageDocs = response.results
          totalCount = response.count || 0
          hasMore = !!response.next
        } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
          currentPageDocs = response.data.results
          totalCount = response.data.count || 0
          hasMore = !!response.data.next
        }
        
        // 确保不添加重复的文档
        const existingIds = new Set(docsList.map(doc => doc.id))
        const newDocs = currentPageDocs.filter(doc => !existingIds.has(doc.id))
        
        if (newDocs.length > 0) {
          docsList = [...docsList, ...newDocs]
          console.log(`第${page}页添加了${newDocs.length}个新文档，当前共有${docsList.length}个文档`)
        } else {
          console.log(`第${page}页没有新文档，可能是达到了末尾或出现了重复数据`)
        }
        
        // 更新文档列表
        documents.value = docsList
        
        // 如果没有更多数据或已经加载了足够多的文档，则停止递归
        if (!hasMore || currentPageDocs.length === 0 || page >= 50) {
          console.log(`文档加载完成，共${docsList.length}个文档${hasMore ? '（但还有更多）' : ''}`)
          documentsLoading.value = false
          return docsList
        }
        
        // 如果文档数量太少（比如小于50），并且有更多数据，继续加载下一页
        if (docsList.length < 200 && hasMore) {
          console.log(`已获取 ${docsList.length}/${totalCount || '未知'} 个文档，加载下一页...`)
          // 延迟100ms避免请求过于频繁
          await new Promise(resolve => setTimeout(resolve, 100))
          // 递归加载下一页
          return fetchDocuments(page + 1, docsList)
        } else {
          console.log(`已加载足够的文档(${docsList.length}个)或达到限制，停止加载更多`)
          documentsLoading.value = false
          return docsList
        }
      } catch (error) {
        console.error('获取文档列表失败', error)
        ElMessage.error('获取文档列表失败，已加载部分数据')
        documentsLoading.value = false
        documents.value = allDocs // 保留已加载的文档
        return allDocs
      }
    }
    
    const loading = ref(false)
    
    // 添加一个文档缓存对象
    const documentCache = ref(new Map());
    
    const selectDocument = async (id) => {
      console.log(`选择文档: ${id}, 当前文档: ${currentDoc.value?.id}`);
      
      // 如果点击的是当前文档，不执行任何操作
      if (currentDoc.value && currentDoc.value.id === id) {
        console.log('已经选中该文档，不执行任何操作');
        return;
      }
      
      // 如果当前文档已修改，提示保存
      if (documentChanged.value && currentDoc.value) {
        try {
          await ElMessageBox.confirm(
            '当前文档已修改但未保存，是否保存更改？',
            '保存提示',
            {
              confirmButtonText: '保存',
              cancelButtonText: '不保存',
              type: 'warning',
              distinguishCancelAndClose: true // 允许区分取消和关闭
            }
          )
          await saveDocument()
        } catch (error) {
          // 用户选择不保存或点×，撤销本地更改，恢复原内容
          if (error === 'cancel' || error === 'close') {
            if (currentDoc.value && originalDoc.value) {
              currentDoc.value.title = originalDoc.value.title
              currentDoc.value.type = originalDoc.value.type
              currentDoc.value.content = originalDoc.value.content
              documentChanged.value = false
            }
          }
          // 用户选择不保存，继续切换文档
        }
      }
      
      // 快速显示缓存中的文档（如果有）
      if (documentCache.value.has(id)) {
        console.log(`使用缓存的文档数据: ${id}`);
        const cachedDoc = documentCache.value.get(id);
        
        // 先设置当前文档为缓存数据，提高用户体验
        currentDoc.value = cachedDoc;
        originalDoc.value = {
          title: cachedDoc.title || '',
          type: cachedDoc.type || '通用',
          content: cachedDoc.content || ''
        };
        documentChanged.value = false;
      }
      
      // 更新路由以反映新选中的文档
      router.push({ name: 'SmartDocDetail', params: { id }, replace: true })
    }
    
    // 记录初始内容用于对比
    const originalDoc = ref({ title: '', type: '', content: '' })
    
    const fetchDocumentDetail = async (id, retry = 0) => {
      // 如果是同一个文档，且已加载，不重复加载
      if (currentDoc.value && currentDoc.value.id === id && !loading.value) {
        console.log(`文档 ${id} 已加载，不重复获取`);
        return;
      }
      
      loading.value = true
      try {
        console.log(`正在获取文档详情，ID: ${id}`)
        const response = await getDocumentDetail(id)
        console.log('文档详情响应:', response)
        
        if (response && response.data) {
          // 确保文档数据完整
          if (!response.data.content) {
            console.warn('文档内容为空，设置为默认空字符串')
            response.data.content = ''
          }
          
          // 保存文档数据
          currentDoc.value = response.data
          
          // 更新缓存
          documentCache.value.set(id, { ...response.data });
          
          // 如果缓存过大，清理旧缓存
          if (documentCache.value.size > 20) {
            // 转换为数组，保留最近的10个
            const entries = Array.from(documentCache.value.entries());
            const recentEntries = entries.slice(-10);
            documentCache.value = new Map(recentEntries);
          }
          
          // 记录初始内容
          originalDoc.value = {
            title: response.data.title || '',
            type: response.data.type || '通用',
            content: response.data.content || ''
          }
          
          documentChanged.value = false
          loading.value = false
          
          // 检查数据完整性
          if (!currentDoc.value.content) {
            console.warn('文档内容可能缺失，尝试重新获取')
            // 设置一个定时器，在编辑器加载完成后检查内容
            setTimeout(() => {
              if (quillInstance.value && (!currentDoc.value.content || currentDoc.value.content.trim() === '')) {
                ElMessage.warning('文档内容可能不完整，请尝试刷新页面')
              }
            }, 2000)
          }
        } else {
          throw new Error('文档不存在或数据无效')
        }
      } catch (error) {
        console.error('获取文档详情失败', error)
        
        if (retry < 3) {
          console.log(`获取文档详情失败，${retry + 1}秒后重试...`)
          setTimeout(() => fetchDocumentDetail(id, retry + 1), 1000 * (retry + 1))
        } else {
          loading.value = false
          console.error('多次重试后获取文档详情仍然失败', error)
          const errorMsg = error.response && error.response.status === 404 
            ? '文档不存在' 
            : error.response && error.response.data && error.response.data.detail 
              ? error.response.data.detail 
              : '获取文档详情失败'
          
          ElMessage.error(errorMsg)
          // 如果是404，导航回文档列表页
          if (error.response && error.response.status === 404) {
            router.push('/smartdoc')
          }
        }
      }
    }
    
    const saveDocument = async () => {
      if (!currentDoc.value || !documentChanged.value) return
      
      saveLoading.value = true
      try {
        await updateDocument(currentDoc.value.id, {
          title: currentDoc.value.title,
          type: currentDoc.value.type,
          content: currentDoc.value.content
        })
        
        // 保存成功后，更新原始文档记录
        originalDoc.value = {
          title: currentDoc.value.title,
          type: currentDoc.value.type,
          content: currentDoc.value.content
        }
        documentChanged.value = false
        ElMessage.success('文档保存成功')
      } catch (error) {
        console.error('保存文档失败', error)
        ElMessage.error('保存文档失败')
      } finally {
        saveLoading.value = false
      }
    }
    
    const toggleDocList = () => {
      isDocListCollapsed.value = !isDocListCollapsed.value
    }
    
    const toggleAssistant = () => {
      isAssistantCollapsed.value = !isAssistantCollapsed.value
    }
    
    const onEditorChange = () => {
      documentChanged.value = true
    }
    
    const openNewDocumentDialog = () => {
      newDocumentForm.value = { title: '', type: '' }
      newDocumentDialogVisible.value = true
    }
    
    const createNewDocument = async () => {
      if (!documentFormRef.value) return
      
      await documentFormRef.value.validate(async (valid) => {
        if (valid) {
          createLoading.value = true
          try {
            const response = await createDocument({
              title: newDocumentForm.value.title,
              type: newDocumentForm.value.type || '通用',
              content: ''
            })
            
            ElMessage.success('文档创建成功')
            newDocumentDialogVisible.value = false
            
            // 刷新文档列表并打开新文档
            await fetchDocuments()
            router.push({ name: 'SmartDocDetail', params: { id: response.data.id } })
      } catch (error) {
            console.error('创建文档失败', error)
            ElMessage.error('创建文档失败')
          } finally {
            createLoading.value = false
          }
        }
      })
    }
    
    const deleteDocument = () => {
      if (!currentDoc.value) return
      
      deleteDialogVisible.value = true
    }
    
    const confirmDelete = async () => {
      if (!currentDoc.value) return
      
      deleteLoading.value = true
      try {
        // 记录将要删除的文档ID，便于调试
        const deletedDocId = currentDoc.value.id
        
        // 执行删除API调用
        await apiDeleteDocument(deletedDocId)
        ElMessage.success('文档删除成功')
        deleteDialogVisible.value = false
        
        console.log(`文档已删除，ID: ${deletedDocId}，准备返回列表页面并刷新`)
        
        // 清除可能的缓存数据
        if (window.localStorage) {
          try {
            // 移除可能存在的相关缓存
            localStorage.removeItem(`doc_cache_${deletedDocId}`);
            // 移除文档列表缓存，确保再次加载时获取最新数据
            localStorage.removeItem(`doc_list_cache`);
          } catch (e) {
            console.error('清除本地缓存失败:', e);
          }
        }
        
        // 清除当前文档状态，避免可能的内存泄漏
        currentDoc.value = null;
        
        // 使用window.location.href而不是router.replace，强制整个页面刷新
        // 添加时间戳参数，确保不走缓存
        window.location.href = '/smartdoc?_refresh=' + new Date().getTime();
      } catch (error) {
        console.error('删除文档失败', error)
        ElMessage.error('删除文档失败')
      } finally {
        deleteLoading.value = false
      }
    }
    
    const exportDocument = () => {
      ElMessageBox({
        title: '导出文档',
        message: '请选择导出格式',
        showCancelButton: true,
        confirmButtonText: '导出为PDF',
        cancelButtonText: '导出为Word',
        closeOnClickModal: true,
        callback: (action) => {
          if (action === 'confirm') {
            exportToPdf()
          } else if (action === 'cancel') {
            exportToWord()
          }
        }
      })
    }
    
    // 导出为PDF
    const exportToPdf = () => {
      if (!currentDoc.value || !currentDoc.value.content) {
        ElMessage.error('没有可导出的文档')
        return
      }
      const docTitle = currentDoc.value.title || '未命名文档'
      const filename = `${docTitle}.pdf`
      // 直接克隆quill编辑器内容
      const editorDom = document.querySelector('.ql-editor')
      if (!editorDom) {
        ElMessage.error('未找到编辑器内容')
        return
      }
      const contentElement = editorDom.cloneNode(true)
      const options = {
        margin: [15, 15, 15, 15],
        filename: filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      }
      const loading = ElLoading.service({
        lock: true,
        text: '正在生成PDF...',
        background: 'rgba(255, 255, 255, 0.7)'
      })
      import('html2pdf.js').then(html2pdfModule => {
        const html2pdf = html2pdfModule.default
        html2pdf().from(contentElement).set(options).save().then(() => {
          loading.close()
          ElMessage.success('PDF导出成功')
        }).catch(error => {
          console.error('PDF导出失败:', error)
          loading.close()
          ElMessage.error('PDF导出失败')
        })
      }).catch(error => {
        console.error('加载html2pdf.js失败:', error)
        loading.close()
        ElMessage.error('PDF导出功能加载失败')
      })
    }
    
    // 导出为Word（保留图片）
    const exportToWord = async () => {
      if (!currentDoc.value || !currentDoc.value.content) {
        ElMessage.error('没有可导出的文档')
        return
      }
      
      const docTitle = currentDoc.value.title || '未命名文档'
      const filename = `${docTitle}.doc`
      
      const loading = ElLoading.service({
        lock: true,
        text: '正在生成Word文档...',
        background: 'rgba(255, 255, 255, 0.7)'
      })
      
      try {
        // 创建一个临时文档容器处理内容
        const contentContainer = document.createElement('div')
        contentContainer.innerHTML = currentDoc.value.content
        // 不再替换图片为占位符，直接保留<img>标签
        // 创建微软Word兼容的HTML文档
        const msWordHtml = `
          <html xmlns:o="urn:schemas-microsoft-com:office:office" 
                xmlns:w="urn:schemas-microsoft-com:office:word" 
                xmlns="http://www.w3.org/TR/REC-html40">
          <head>
            <meta charset="utf-8">
            <title>${docTitle}</title>
            <style>
              body { font-family: SimSun, Arial, sans-serif; margin: 1cm; }
              img { max-width: 100%; height: auto; }
              p { margin: 0; padding: 0; }
              h1 { font-size: 18pt; }
              h2 { font-size: 16pt; }
              h3 { font-size: 14pt; }
              table { border-collapse: collapse; width: 100%; }
              td, th { border: 1px solid #000; padding: 5px; }
            </style>
          </head>
          <body>
            <h1>${docTitle}</h1>
            ${contentContainer.innerHTML}
          </body>
          </html>
        `
        // 使用file-saver保存文件
        const FileSaver = await import('file-saver')
        const saveAs = FileSaver.saveAs || FileSaver.default
        const blob = new Blob([msWordHtml], { type: 'application/msword' })
        saveAs(blob, filename)
        loading.close()
        ElMessage.success('Word文档导出成功')
      } catch (error) {
        console.error('Word导出失败:', error)
        loading.close()
        ElMessage.error(`Word导出失败: ${error.message || '未知错误'}`)
      }
    }
    
    const printDocument = () => {
      ElMessage.info('打印文档功能暂未实现')
    }
    
    const addCollaborator = () => {
      ElMessage.info('添加协作者功能暂未实现')
    }
    
    const viewHistory = () => {
      ElMessage.info('查看历史版本功能暂未实现')
    }
    
    // 1. 在setup里加缓存变量
    const quillSelection = ref(null);
    const quillSelectedText = ref('');

    // 计算属性：判断是否有有效的选择文本（去除空白字符后不为空）
    const hasValidSelection = computed(() => {
      return quillSelectedText.value && quillSelectedText.value.trim().length > 0;
    });

    // 2. 监听Quill的selection-change事件
    const onSelectionChange = (range, oldRange, source) => {
      console.log('=== Quill Selection Change ===');
      console.log('Range:', range);
      console.log('Old Range:', oldRange);
      console.log('Source:', source);

      if (!quillInstance.value) {
        console.log('Quill实例不存在');
        return;
      }

      // 防止在程序化操作时清除选择状态
      if (source === 'api' && !range) {
        console.log('API操作导致的空选择，忽略');
        return;
      }

      if (range && range.length > 0) {
        const text = quillInstance.value.getText(range.index, range.length);
        console.log('选中文本长度:', text.length);
        console.log('选中文本内容:', JSON.stringify(text));
        console.log('选中文本(显示):', text);

        // 保存原始文本，不进行trim处理，确保与实际选择一致
        quillSelectedText.value = text;
        quillSelection.value = { ...range }; // 深拷贝避免引用问题

        console.log('已保存选择状态');
      } else {
        console.log('清除选择状态');
        quillSelectedText.value = '';
        quillSelection.value = null;
      }
      console.log('=== End Selection Change ===');
    };

    // 1. 最大长度常量
    const MAX_AI_TEXT_LENGTH = 2000;

    // 辅助函数：获取当前有效的选择和对应文本
    const getCurrentSelectionWithText = () => {
      if (!quillInstance.value) return { selection: null, text: '' };

      let selection = quillInstance.value.getSelection();
      let text = '';

      // 如果当前有选择，直接使用
      if (selection && selection.length > 0) {
        text = quillInstance.value.getText(selection.index, selection.length);
        console.log('使用当前选择:', { selection, text: JSON.stringify(text) });
        return { selection, text };
      }

      // 如果当前没有选择，尝试使用缓存的选择和文本
      if (quillSelection.value && quillSelection.value.length > 0 && quillSelectedText.value) {
        // 验证缓存的选择是否仍然有效
        const textLength = quillInstance.value.getLength();
        if (quillSelection.value.index + quillSelection.value.length <= textLength) {
          // 直接使用缓存的文本，而不是重新获取，确保一致性
          selection = quillSelection.value;
          text = quillSelectedText.value;
          console.log('使用缓存的选择和文本:', { selection, text: JSON.stringify(text) });
          return { selection, text };
        }
      }

      console.log('没有有效的选择');
      return { selection: null, text: '' };
    };

    // 保持向后兼容的getCurrentSelection函数
    const getCurrentSelection = () => {
      const result = getCurrentSelectionWithText();
      return result.selection;
    };

    // 辅助函数：安全地设置选择状态
    const safeSetSelection = (index, length = 0, source = 'api') => {
      if (!quillInstance.value) return;

      try {
        const textLength = quillInstance.value.getLength();
        const safeIndex = Math.max(0, Math.min(index, textLength - 1));
        const safeLength = Math.max(0, Math.min(length, textLength - safeIndex));

        quillInstance.value.setSelection(safeIndex, safeLength, source);
      } catch (error) {
        console.warn('设置选择状态失败:', error);
      }
    };

    // 刷新编辑器实例的函数
    const refreshQuillEditor = () => {
      if (quillInstance.value) {
        try {
          // 清除选择状态
          quillSelectedText.value = '';
          quillSelection.value = null;

          // 重新获取焦点
          nextTick(() => {
            if (quillInstance.value) {
              quillInstance.value.focus();
              console.log('Quill编辑器已刷新');
            }
          });
        } catch (error) {
          console.warn('刷新Quill编辑器失败:', error);
        }
      }
    };

    // 2. expandContent方法加截断
    const expandContent = async () => {
      if (!currentDoc.value || expandLoading.value) return;
      try {
        expandLoading.value = true;
        if (!quillInstance.value) {
          ElMessage.error('编辑器未就绪，请稍后再试');
          expandLoading.value = false;
          return;
        }

        // 使用新的辅助函数获取选择和文本
        const { selection, text } = getCurrentSelectionWithText();

        console.log('=== 扩写内容 - 获取选择 ===');
        console.log('Selection:', selection);
        console.log('原始文本:', JSON.stringify(text));
        console.log('缓存的选择文本:', JSON.stringify(quillSelectedText.value));

        let selectedText = text.trim();
        let range = null;
        if (selection && selection.length > 0 && selectedText) {
          range = { ...selection };
        }

        console.log('处理后的文本:', JSON.stringify(selectedText));
        console.log('=== End 扩写内容获取 ===');

        if (!selectedText) {
          ElMessage.warning('请先选择要扩写的文本内容');
          expandLoading.value = false;
          return;
        }
        if (selectedText.length > MAX_AI_TEXT_LENGTH) {
          ElMessage.warning(`选中文本过长，已自动截断为前${MAX_AI_TEXT_LENGTH}字`);
          selectedText = selectedText.slice(0, MAX_AI_TEXT_LENGTH);
        }
        ElMessage.info('正在扩写内容，请稍候...');
        const response = await apiExpandContent(currentDoc.value.id, {
          selection: selectedText,
          length: 'medium'
        });
        showCompareDialog({
          title: '内容扩写结果',
          original: selectedText,
          modified: response.data.content,
          onApply: (finalContent) => {
            if (
              range &&
              typeof range.index === 'number' &&
              typeof range.length === 'number' &&
              range.index >= 0 &&
              range.length > 0
            ) {
              const quillLen = quillInstance.value.getLength();
              let insertPos = range.index;
              if (insertPos > quillLen) insertPos = quillLen - 1;

              // 使用 API 源标记，避免触发不必要的选择变化事件
              quillInstance.value.deleteText(insertPos, range.length, 'api');
              quillInstance.value.insertText(insertPos, finalContent, 'api');

              // 设置新的选择位置
              let selPos = insertPos + finalContent.length;
              selPos = Math.max(0, Math.min(selPos, quillInstance.value.getLength()));

              // 延迟设置选择，确保文本插入完成
              nextTick(() => {
                safeSetSelection(selPos, 0, 'api');
                documentChanged.value = true;
                ElMessage.success('内容扩写已应用');
                // 刷新编辑器实例
                setTimeout(() => {
                  refreshQuillEditor();
                }, 100);
              });
            } else {
              ElMessage.error('选区无效，无法插入内容');
            }
          }
        });
      } catch (error) {
        console.error('[内容扩写] 异常:', error);
        if (error && error.response) {
          ElMessage.error('内容扩写失败: ' + (error.response.data.detail || error.message));
        } else {
          ElMessage.error('内容扩写失败，请稍后再试');
        }
      } finally {
        expandLoading.value = false;
      }
    };

    // 3. polishText同理
    const polishText = async () => {
      if (!currentDoc.value || polishLoading.value) return;
      try {
        polishLoading.value = true;
        if (!quillInstance.value) {
          ElMessage.error('编辑器未就绪，请稍后再试');
          polishLoading.value = false;
          return;
        }

        // 使用新的辅助函数获取选择和文本
        const { selection, text } = getCurrentSelectionWithText();

        let selectedText = text.trim();
        let range = null;
        if (selection && selection.length > 0 && selectedText) {
          range = { ...selection };
        }
        if (!selectedText) {
          ElMessage.warning('请先选择要润色的文本内容');
          polishLoading.value = false;
          return;
        }
        if (selectedText.length > MAX_AI_TEXT_LENGTH) {
          ElMessage.warning(`选中文本过长，已自动截断为前${MAX_AI_TEXT_LENGTH}字`);
          selectedText = selectedText.slice(0, MAX_AI_TEXT_LENGTH);
        }
        ElMessage.info('正在润色文本，请稍候...');
        const response = await apiPolishText(currentDoc.value.id, {
          selection: selectedText,
          style: 'professional'
        });
        showCompareDialog({
          title: '文本润色结果',
          original: selectedText,
          modified: response.data.content,
          onApply: (finalContent) => {
            if (
              range &&
              typeof range.index === 'number' &&
              typeof range.length === 'number' &&
              range.index >= 0 &&
              range.length > 0
            ) {
              const quillLen = quillInstance.value.getLength();
              let insertPos = range.index;
              if (insertPos > quillLen) insertPos = quillLen - 1;

              // 使用 API 源标记，避免触发不必要的选择变化事件
              quillInstance.value.deleteText(insertPos, range.length, 'api');
              quillInstance.value.insertText(insertPos, finalContent, 'api');

              // 设置新的选择位置
              let selPos = insertPos + finalContent.length;
              selPos = Math.max(0, Math.min(selPos, quillInstance.value.getLength()));

              // 延迟设置选择，确保文本插入完成
              nextTick(() => {
                safeSetSelection(selPos, 0, 'api');
                documentChanged.value = true;
                ElMessage.success('文本润色已应用');
                // 刷新编辑器实例
                setTimeout(() => {
                  refreshQuillEditor();
                }, 100);
              });
            } else {
              ElMessage.error('选区无效，无法插入内容');
            }
          }
        });
      } catch (error) {
        console.error('[文本润色] 异常:', error);
        if (error && error.response) {
          ElMessage.error('文本润色失败: ' + (error.response.data.detail || error.message));
        } else {
          ElMessage.error('文本润色失败，请稍后再试');
        }
      } finally {
        polishLoading.value = false;
      }
    };
    
    // 添加比较弹窗的状态变量和方法
    const compareDialogVisible = ref(false)
    const compareDialogData = ref({
      title: '',
      original: '',
      modified: '',
      modifiedContent: '',
      onApply: () => {}
    })
    
    // 显示比较弹窗
    const showCompareDialog = (data) => {
      compareDialogData.value = {
        ...data,
        modifiedContent: data.modified
      };
      compareDialogVisible.value = true;
    }
    
    // 应用比较弹窗的更改
    const applyCompareChanges = () => {
      compareDialogData.value.onApply(compareDialogData.value.modifiedContent);
      compareDialogVisible.value = false;
    }
    
    // 关闭比较弹窗
    const closeCompareDialog = () => {
      compareDialogVisible.value = false
    }
    
    // 防抖搜索
    const debouncedSearch = _.debounce(() => {
      // 搜索逻辑已通过计算属性处理
    }, 300)
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      
      // 同一天显示时间
      if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      
      // 昨天
      const yesterday = new Date(now)
      yesterday.setDate(now.getDate() - 1)
      if (date.toDateString() === yesterday.toDateString()) {
        return '昨天'
      }
      
      // 一周内显示星期
      const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
      const diffDays = Math.round((now - date) / (1000 * 60 * 60 * 24))
      if (diffDays < 7) {
        return weekDays[date.getDay()]
      }
      
      // 其他情况显示日期
      return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
    }
    
    // 监听路由变化
    watch(() => route.params.id, (newId, oldId) => {
      console.log(`路由参数ID变化: ${oldId} -> ${newId}`)
      if (newId) {
        // 检查ID是否为有效正整数
        const idNum = Number(newId)
        if (isNaN(idNum) || idNum <= 0 || !Number.isInteger(idNum)) {
          ElMessage.error('无效的文档ID')
          router.push('/smartdoc')
          return
        }
        
        // 如果ID发生了变化，重新获取文档
        if (newId !== oldId) {
          console.log(`文档ID变化，获取文档详情: ${newId}`)
          // 检查是否已有缓存
          if (documentCache.value.has(newId)) {
            console.log(`使用缓存的文档数据: ${newId}`);
            currentDoc.value = documentCache.value.get(newId);
            originalDoc.value = {
              title: currentDoc.value.title || '',
              type: currentDoc.value.type || '通用',
              content: currentDoc.value.content || ''
            };
            documentChanged.value = false;
            
            // 在后台异步刷新数据
            setTimeout(() => {
              fetchDocumentDetail(newId);
            }, 500);
          } else {
            // 没有缓存，直接获取
            fetchDocumentDetail(newId);
          }
        }
      } else {
        currentDoc.value = null
      }
    }, { immediate: false }) // 设为false避免重复加载
    
    // 监听query参数变化，处理强制刷新
    watch(() => route.query._refresh, (newVal) => {
      if (newVal) {
        console.log('检测到强制刷新参数:', newVal)
        const docId = route.params.id
        if (docId) {
          console.log('强制刷新文档详情:', docId)
          fetchDocumentDetail(docId)
        }
        // 同时刷新文档列表
        fetchDocuments()
      }
    })
    
    // 自动保存功能
    setInterval(() => {
      if (documentChanged.value && currentDoc.value && !saveLoading.value) {
        saveDocument()
      }
    }, 60000) // 每分钟自动保存一次
    
    // 生命周期钩子
    onMounted(() => {
      fetchInitialData();
      
      // 监听路由参数变化，当ID变化时刷新页面数据
      watch(() => route.params.id, (newId, oldId) => {
        if (newId && newId !== oldId) {
          refreshDocumentData(newId);
        }
      });
    })
    
    // 滚动到当前选中的文档
    const scrollToActiveDocument = () => {
      try {
        if (!currentDoc.value) return;
        
        // 查找当前激活的文档元素
        const activeDoc = document.querySelector('.doc-item.active');
        if (activeDoc) {
          // 使用scrollIntoView滚动到该元素
          activeDoc.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      } catch (error) {
        console.error('滚动到活动文档失败:', error);
      }
    }
    
    // 只有内容实际变化才标记为已修改
    const onTitleChange = (val) => {
      documentChanged.value = val !== originalDoc.value.title
    }
    const onTypeChange = (val) => {
      documentChanged.value = val !== originalDoc.value.type
    }
    const onContentChange = () => {
      // 修复：正确比较编辑器内容
      if (currentDoc.value && originalDoc.value) {
        // 比较当前内容与原始内容是否真的不同
        const currentContent = currentDoc.value.content
        const originalContent = originalDoc.value.content
        documentChanged.value = currentContent !== originalContent
      }
      scrollQuillToBottom();
    }
    
    // 编辑器实例
    const quillInstance = ref(null);

    // 2. 编辑器ready时赋值
    const onEditorReady = (quill) => {
      console.log('编辑器就绪');
      quillInstance.value = quill;
      quill.on('selection-change', onSelectionChange);

      // 延迟执行，确保工具栏DOM已完全渲染
      setTimeout(() => {
        // 为工具栏按钮添加提示
        const toolbarTooltips = {
          '.ql-bold': '加粗 (Ctrl+B)',
          '.ql-italic': '斜体 (Ctrl+I)',
          '.ql-underline': '下划线 (Ctrl+U)',
          '.ql-strike': '删除线',
          '.ql-blockquote': '块级引用',
          '.ql-code-block': '代码块',
          '.ql-header[value="1"]': '标题1',
          '.ql-header[value="2"]': '标题2',
          '.ql-list[value="ordered"]': '有序列表',
          '.ql-list[value="bullet"]': '无序列表',
          '.ql-script[value="sub"]': '下标',
          '.ql-script[value="super"]': '上标',
          '.ql-indent[value="-1"]': '减少缩进',
          '.ql-indent[value="+1"]': '增加缩进',
          '.ql-direction': '文本方向',
          '.ql-clean': '清除格式',
          '.ql-link': '超链接',
          '.ql-image': '图片',
          // Pickers (less specific selectors)
          '.ql-size': '字号',
          '.ql-header': '段落格式',
          '.ql-color': '字体颜色',
          '.ql-background': '背景颜色',
          '.ql-font': '字体',
          '.ql-align': '对齐方式',
        };

        try {
          const toolbar = quill.getModule('toolbar').container;
          if (!toolbar) {
            console.error("未能获取编辑器工具栏容器。");
            return;
          }
          for (const selector in toolbarTooltips) {
            const elements = toolbar.querySelectorAll(selector);
            elements.forEach(el => {
              // 避免覆盖更具体选择器的提示
              if (!el.hasAttribute('title')) {
                 el.title = toolbarTooltips[selector];
              }
            });
          }
        } catch (error) {
          console.error("为编辑器工具栏添加提示时出错:", error);
        }
      }, 200); // 延迟200毫秒
    };
    
    // 智能滚动函数 - 避免干扰文本选择
    function scrollQuillToBottom() {
      if (quillInstance.value) {
        // 保存当前选择状态
        const currentSelection = quillInstance.value.getSelection();

        const container = quillInstance.value.root;
        container.scrollTop = container.scrollHeight;

        // 恢复选择状态（如果存在）
        if (currentSelection && currentSelection.length > 0) {
          // 使用 nextTick 确保滚动完成后再恢复选择
          nextTick(() => {
            try {
              quillInstance.value.setSelection(currentSelection.index, currentSelection.length);
            } catch (error) {
              console.warn('恢复选择状态失败:', error);
            }
          });
        }
      }
    }
    
    const grammarCheckText = async () => {
      if (!currentDoc.value || grammarCheckLoading.value) return;
      try {
        grammarCheckLoading.value = true;
        if (!quillInstance.value) {
          ElMessage.error('编辑器未就绪，请稍后再试');
          grammarCheckLoading.value = false;
          return;
        }

        // 使用新的辅助函数获取选择和文本
        const { selection, text } = getCurrentSelectionWithText();

        let selectedText = text.trim();
        let range = null;
        if (selection && selection.length > 0 && selectedText) {
          range = { ...selection };
        }
        if (!selectedText) {
          ElMessage.warning('请先选择要纠错的文本内容');
          grammarCheckLoading.value = false;
          return;
        }
        if (selectedText.length > MAX_AI_TEXT_LENGTH) {
          ElMessage.warning(`选中文本过长，已自动截断为前${MAX_AI_TEXT_LENGTH}字`);
          selectedText = selectedText.slice(0, MAX_AI_TEXT_LENGTH);
        }
        ElMessage.info('正在智能纠错，请稍候...');
        const response = await grammarCheck(currentDoc.value.id, { selection: selectedText });
        // 只保留建议部分，去除"优化后的文本"字样，并将md转为html
        let suggestions = response.suggestions || '';
        suggestions = suggestions.replace(/\*\*优化后的文本\*\*[:：]?([\s\S]*)$/, '').trim();
        const suggestionsHtml = marked.parse(suggestions);

        // 从修正文本中只提取优化后的文本
        let correctedText = response.corrected || '';
        const optimizedTextMatch = correctedText.match(/优化后的文本[:：]([\s\S]*)/);
        const finalCorrectedText = optimizedTextMatch ? optimizedTextMatch[1].trim() : correctedText;

        showCompareDialog({
          title: '智能纠错建议',
          original: selectedText,
          modified: finalCorrectedText, // 右侧编辑器直接填优化后文本
          suggestions: suggestionsHtml, // AI建议区只显示建议，且为html
          onApply: (finalContent) => {
            if (
              range &&
              typeof range.index === 'number' &&
              typeof range.length === 'number' &&
              range.index >= 0 &&
              range.length > 0
            ) {
              const quillLen = quillInstance.value.getLength();
              let insertPos = range.index;
              if (insertPos > quillLen) insertPos = quillLen - 1;

              // 使用 API 源标记，避免触发不必要的选择变化事件
              quillInstance.value.deleteText(insertPos, range.length, 'api');
              quillInstance.value.insertText(insertPos, finalContent, 'api');

              // 设置新的选择位置
              let selPos = insertPos + finalContent.length;
              selPos = Math.max(0, Math.min(selPos, quillInstance.value.getLength()));

              // 延迟设置选择，确保文本插入完成
              nextTick(() => {
                safeSetSelection(selPos, 0, 'api');
                documentChanged.value = true;
                ElMessage.success('智能纠错已应用');
                // 刷新编辑器实例
                setTimeout(() => {
                  refreshQuillEditor();
                }, 100);
              });
            } else {
              ElMessage.error('选区无效，无法插入内容');
            }
          }
        });
      } catch (error) {
        console.error('[智能纠错] 异常:', error);
        if (error && error.response) {
          ElMessage.error('智能纠错失败: ' + (error.response.data.detail || error.message));
        } else {
          ElMessage.error('智能纠错失败，请稍后再试');
        }
      } finally {
        grammarCheckLoading.value = false;
      }
    }
    
    // 多语言翻译
    const translateDialogVisible = ref(false)
    const translateInput = ref('')
    const translateResult = ref('')
    const translateLoading = ref(false)
    const targetLang = ref('en')
    const translateModifiedContent = ref('')
    const openTranslateDialog = () => {
      if (!quillInstance.value) {
        ElMessage.error('编辑器未就绪，请稍后重试');
        return;
      }

      // 使用新的辅助函数获取选择和文本
      const { selection, text } = getCurrentSelectionWithText();

      // 清空旧数据
      translateResult.value = '';
      translateModifiedContent.value = '';

      if (selection && selection.length > 0) {
        translateInput.value = text.trim();
      } else {
        translateInput.value = '';
      }

      // 显示对话框
      translateDialogVisible.value = true;
    }
    const useSelectedTextForTranslate = () => {
      if (!quillInstance.value) return
      const selection = quillInstance.value.getSelection()
      if (selection && selection.length > 0) {
        translateInput.value = quillInstance.value.getText(selection.index, selection.length)
      }
    }
    const doTranslate = async () => {
      if (!currentDoc.value || !translateInput.value) return
      translateLoading.value = true
      try {
        const res = await translateText(currentDoc.value.id, { selection: translateInput.value, target_lang: targetLang.value })
        translateResult.value = res.translated
        translateModifiedContent.value = res.translated
      } catch (e) {
        ElMessage.error('翻译失败')
      } finally {
        translateLoading.value = false
      }
    }
    const replaceSelectionWithTranslation = () => {
      if (!quillInstance.value || !translateModifiedContent.value) return

      // 使用辅助函数获取当前有效选择
      const selection = getCurrentSelection();

      if (selection && selection.length > 0) {
        const quillLen = quillInstance.value.getLength()
        let insertPos = selection.index
        if (insertPos > quillLen) insertPos = quillLen - 1

        // 使用 API 源标记，避免触发不必要的选择变化事件
        quillInstance.value.deleteText(insertPos, selection.length, 'api')
        quillInstance.value.clipboard.dangerouslyPasteHTML(insertPos, translateModifiedContent.value, 'api')

        let selPos = insertPos + translateModifiedContent.value.replace(/<[^>]+>/g, '').length
        if (selPos > quillInstance.value.getLength() - 1) selPos = quillInstance.value.getLength() - 1

        // 延迟设置选择，确保文本插入完成
        nextTick(() => {
          safeSetSelection(selPos, 0, 'api')
          documentChanged.value = true
          ElMessage.success('已替换为翻译内容')
          translateDialogVisible.value = false
          // 刷新编辑器实例
          setTimeout(() => {
            refreshQuillEditor();
          }, 100);
        });
      } else {
        // 未选中内容时插入到光标处
        const cursor = quillInstance.value.getSelection(true)
        let insertPos = cursor ? cursor.index : quillInstance.value.getLength() - 1
        quillInstance.value.insertEmbed(insertPos, 'text', translateModifiedContent.value, 'api')

        nextTick(() => {
          safeSetSelection(insertPos + translateModifiedContent.value.replace(/<[^>]+>/g, '').length, 0, 'api')
          documentChanged.value = true
          ElMessage.success('已插入翻译内容')
          translateDialogVisible.value = false
          // 刷新编辑器实例
          setTimeout(() => {
            refreshQuillEditor();
          }, 100);
        });
      }
    }

    // 智能问答
    const qaDialogVisible = ref(false)
    const qaQuestion = ref('')
    const qaAnswer = ref('')
    const qaLoading = ref(false)
    
    // 计算属性：将Markdown格式的回答转换为HTML
    const qaAnswerHtml = computed(() => {
      return qaAnswer.value ? marked.parse(qaAnswer.value) : ''
    })
    
    const openQaDialog = () => {
      qaDialogVisible.value = true
      qaQuestion.value = ''
      qaAnswer.value = ''
    }
    const doQa = async () => {
      if (!currentDoc.value || !qaQuestion.value) return
      qaLoading.value = true
      try {
        const res = await docQa(currentDoc.value.id, { question: qaQuestion.value, context: currentDoc.value.content })
        qaAnswer.value = res.answer
      } catch (e) {
        ElMessage.error('问答失败')
      } finally {
        qaLoading.value = false
      }
    }
    
    // 刷新文档数据
    const refreshDocumentData = async (docId) => {
      loading.value = true;
      try {
        if (docId) {
          await fetchDocumentDetail(docId);
        }
      } catch (error) {
        console.error('刷新文档数据失败:', error);
        ElMessage.error('刷新文档数据失败');
      } finally {
        loading.value = false;
      }
    };
    
    // 初始化数据加载
    const fetchInitialData = () => {
      console.log('组件挂载，开始加载数据');
      
      // 获取当前文档ID
      const docId = route.params.id;
      
      // 如果有文档ID，优先加载文档详情
      if (docId) {
        console.log('有文档ID，优先加载文档详情:', docId);
        fetchDocumentDetail(docId).then(() => {
          // 文档详情加载完成后，异步加载文档列表
          console.log('文档详情加载完成，开始加载文档列表');
          fetchDocuments().then(() => {
            // 文档列表加载完成后，滚动到当前文档
            console.log('文档列表加载完成');
            nextTick(() => {
              scrollToActiveDocument();
            });
          });
        });
      } else {
        // 没有文档ID，只加载文档列表
        console.log('没有文档ID，只加载文档列表');
        fetchDocuments();
      }
    };
    
    return {
      route,
      router,
      goBack,
      documents,
      currentDoc,
      documentChanged,
      filteredDocuments,
      filteredCount,
      searchQuery,
      docTypeFilter,
      sortOption,
      isDocListCollapsed,
      isAssistantCollapsed,
      documentFormRules,
      documentFormRef,
      newDocumentForm,
      newDocumentDialogVisible,
      deleteDialogVisible,
      saveLoading,
      createLoading,
      deleteLoading,
      expandLoading,
      polishLoading,
      grammarCheckLoading,
      compareDialogVisible,
      compareDialogData,
      translateDialogVisible,
      translateLoading,
      targetLang,
      translateInput,
      translateModifiedContent,
      qaDialogVisible,
      qaQuestion,
      qaAnswer,
      qaAnswerHtml,
      qaLoading,
      saveDocument,
      toggleDocList,
      toggleAssistant,
      onEditorChange,
      openNewDocumentDialog,
      createNewDocument,
      deleteDocument,
      confirmDelete,
      exportDocument,
      exportToPdf,
      exportToWord,
      printDocument,
      addCollaborator,
      viewHistory,
      expandContent,
      polishText,
      debouncedSearch,
      formatDate,
      loading,
      onTitleChange,
      onTypeChange,
      onContentChange,
      onEditorReady,
      showCompareDialog,
      applyCompareChanges,
      closeCompareDialog,
      quillSelection,
      quillSelectedText,
      hasValidSelection,
      onSelectionChange,
      quillInstance,
      grammarCheckText,
      openTranslateDialog,
      useSelectedTextForTranslate,
      doTranslate,
      openQaDialog,
      doQa,
      replaceSelectionWithTranslation,
      documentsLoading,
      documentCache,
      scrollToActiveDocument,
      selectDocument,
      editorOptions
    }
  }
}
</script>

<style lang="scss" scoped>
/* 修改整体布局，调整侧边栏和主内容区域的宽度比例 */
.smart-doc-container {
  display: flex;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-color);
}

.sidebar {
  width: 240px;
  height: 100%;
  border-right: 1px solid var(--border-color);
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  /* 仅保留宽度变化的过渡，其他动画全部去除 */
  transition: width 0.3s;
}

.sidebar.collapsed {
  width: 50px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  height: 48px;
  box-sizing: border-box;
}

.sidebar-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.toggle-btn {
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.toggle-btn:hover {
  background-color: var(--hover-color);
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  height: calc(100% - 48px);
  overflow: hidden;
}

.search-area {
  padding: 12px;
  border-bottom: 1px solid var(--border-color-light);
}

.filter-options {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.document-list-scrollbar {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth; /* 添加平滑滚动效果 */
}

.document-list-scrollbar :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
  scrollbar-width: thin; /* Firefox */
}

.document-list-scrollbar :deep(.el-scrollbar__thumb) {
  background-color: rgba(144, 147, 153, 0.3);
  border-radius: 6px;
}

.document-list-scrollbar :deep(.el-scrollbar__thumb:hover) {
  background-color: rgba(144, 147, 153, 0.5);
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px; /* 为滚动条留出空间 */
}

.doc-item {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease; /* 加快过渡速度 */
}

.doc-item:hover {
  background-color: var(--hover-color);
}

.doc-item.active {
  background-color: var(--active-color);
}

.doc-icon {
  margin-right: 12px;
  color: var(--primary-color);
}

.doc-info {
  flex: 1;
  overflow: hidden;
}

.doc-info h5 {
  margin: 0 0 4px 0;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-color);
}

.doc-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-color-tertiary);
}

.action-buttons {
  padding: 12px;
  border-top: 1px solid var(--border-color-light);
}

.action-buttons .el-button {
  width: 100%;
  height: 36px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background-color: var(--hover-color);
}

.icon-btn.doc-btn.active {
  background-color: var(--active-color);
  color: var(--primary-color);
}

.create-btn {
  background-color: var(--active-color);
  color: var(--primary-color);
}

.collapsed-sidebar {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  gap: 12px;
  height: calc(100% - 48px);
  overflow-y: auto;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background-color: var(--hover-color);
}

.icon-btn.doc-btn.active {
  background-color: var(--active-color);
  color: var(--primary-color);
}

.create-btn {
  background-color: var(--active-color);
  color: var(--primary-color);
}

.recent-docs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  align-items: center;
  min-width: 0;
  height: 100%;
  background-color: var(--bg-color-tertiary);
  position: relative;
  /* 去除外部滚动 */
  overflow: hidden;
}

/* 主内容区域样式 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  background-color: #f6f6f6;
  position: relative;
  /* 去除外部滚动 */
  overflow: hidden;
}

.document-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  height: 100%;
  overflow: hidden;
}

/* 文档标题和类型标签样式 */
.doc-title-label, .doc-type-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color-secondary);
  white-space: nowrap;
}

.document-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-color-secondary);
  height: 68px;
  box-sizing: border-box;
  width: 100%;
  z-index: 5;
}

.header-left-actions {
  margin-right: 15px;
}

.doc-info-area {
  flex-grow: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-title {
  width: 300px;
}

.doc-type-selector {
  width: 150px;
}

.doc-actions {
  display: flex;
  gap: 8px;
  z-index: 6; /* 确保操作按钮在最上层 */
}

.editor-area {
  flex: 1;
  background-color: var(--bg-color);
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  padding: 0; /* 取消padding，避免高度累加 */
}

.quill-editor {
  flex: 1;
  height: 100%;
  background: var(--bg-color);
  min-height: 0;
  box-sizing: border-box;
}

.quill-editor :deep(.ql-container) {
  flex: 1;
  height: 100% !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  background: #fff !important;
  box-sizing: border-box;
}

.quill-editor :deep(.ql-editor) {
  flex: 1;
  min-height: 0 !important;
  height: 100% !important;
  overflow-y: auto !important;
  background: #fff !important;
  padding: 15px;
  box-sizing: border-box;
}

.empty-doc-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-color);
}

/* 智能助手面板样式 */
.assistant-panel {
  width: 280px;
  height: 100%;
  border-left: 1px solid var(--border-color);
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.assistant-panel.collapsed {
  width: 50px;
}

.assistant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  height: 48px;
  box-sizing: border-box;
}

.assistant-header h5 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.assistant-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 16px;
}

.ai-features-beauty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
  margin-top: 30px;
}

.ai-feature-card {
  width: 100%;
  max-width: 320px;
  background: var(--bg-color-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(80,120,200,0.06);
  padding: 18px 20px 10px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: box-shadow 0.2s;
}

.ai-feature-card:hover {
  box-shadow: 0 4px 16px rgba(80,120,200,0.13);
}

.ai-feature-btn {
  width: 100%;
  height: 48px;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  margin-bottom: 6px;
  transition: background 0.2s, color 0.2s;
}

.ai-feature-desc {
  font-size: 13px;
  color: var(--text-color-tertiary);
  text-align: center;
  margin-top: 2px;
  margin-bottom: 2px;
  line-height: 1.6;
}

.context-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.warning-text {
  color: #f56c6c;
  font-weight: 500;
}

.compare-content {
  flex: 1;
  display: flex;
  gap: 20px;
  overflow: hidden;
}

.original-content, .modified-content {
  flex: 1;
  min-width: 350px;
  max-width: 50%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}

.original-content h6, .modified-content h6 {
  margin: 0;
  padding: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  background-color: var(--bg-color-tertiary);
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  border-bottom: 1px solid var(--border-color);
}

.content-box {
  padding: 15px;
  overflow-y: auto;
  white-space: pre-wrap;
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  max-height: 50vh;
  border: 1px solid var(--border-color);
  background-color: var(--bg-color);
}

.compare-dialog :deep(.el-dialog__body) {
  padding: 20px;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  height: 60vh;
  overflow: hidden;
}

.compare-dialog :deep(.el-dialog__header) {
  padding: 15px 20px;
}

.compare-dialog :deep(.el-dialog__footer) {
  padding: 10px 20px;
}

.compare-dialog :deep(.el-dialog) {
  max-height: 85vh; /* 限制整个对话框的最大高度 */
  display: flex;
  flex-direction: column;
  margin: 0 auto !important;
  overflow: hidden; /* 弹窗本身不应该滚动 */
}

/* 确保弹窗内容能够撑满但不溢出弹窗 */
.compare-dialog :deep(.el-dialog__body) {
  padding: 20px;
  flex: 1;
  overflow: auto;
  max-height: calc(85vh - 110px); /* 减去头部和底部的高度 */
  height: auto;
  display: flex;
  flex-direction: column;
}

.dialog-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.quill-editor-in-dialog {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.quill-editor-in-dialog :deep(.ql-toolbar) {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg-color);
}

.quill-editor-in-dialog :deep(.ql-container) {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100% !important;
  overflow-y: auto !important;
  background: var(--bg-color) !important;
}

.quill-editor-in-dialog :deep(.ql-editor) {
  flex: 1;
  min-height: 0 !important;
  height: 100% !important;
  overflow-y: auto !important;
  background: var(--bg-color) !important;
  padding: 15px;
}

.document-count {
  text-align: center;
  padding: 12px;
  color: var(--text-color-tertiary);
  font-size: 13px;
  border-top: 1px dashed var(--border-color);
  margin-top: 10px;
}

.loading-state {
  padding: 10px;
  min-height: 200px;
  text-align: center;
  color: var(--text-color-tertiary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 20px;
  text-align: center;
  color: var(--text-color-tertiary);
}

.collapsed-assistant {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  gap: 12px;
  height: calc(100% - 48px);
  overflow-y: auto;
}

.icon-btn.disabled {
  color: var(--el-disabled-text-color);
  cursor: not-allowed;
}

.icon-btn.disabled:hover {
  background-color: transparent;
}

.collapsed-assistant .icon-btn {
  border-radius: 50%;
  color: var(--text-color-secondary);
  background-color: var(--bg-color-secondary);
  border: 1px solid var(--border-color);
  transition: all 0.2s ease-in-out;
}

.collapsed-assistant .icon-btn:hover {
  background-color: #409eff;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.collapsed-assistant .icon-btn.disabled {
  color: var(--el-disabled-text-color);
  background-color: var(--bg-color-tertiary);
  border-color: var(--border-color-light);
}

.collapsed-assistant .icon-btn.disabled:hover {
  background-color: var(--bg-color-tertiary);
  color: var(--el-disabled-text-color);
  transform: none;
  box-shadow: none;
  border-color: var(--border-color-light);
  cursor: not-allowed;
}

.user-permissions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  margin-top: 8px;
}

.user-permission-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--bg-color-secondary);
  padding: 10px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
}

.user-name {
  min-width: 60px;
  margin-right: 12px;
  font-weight: 500;
  color: var(--text-color);
}
</style>
<style>
/* Quill editor dark theme overrides */
[data-theme="dark"] .quill-editor .ql-snow,
[data-theme="dark"] .ql-snow .ql-tooltip { /* For tooltips like links */
  background-color: var(--bg-color-secondary);
  border-color: var(--border-color);
  color: var(--text-color);
  box-shadow: none;
}

[data-theme="dark"] .ql-snow .ql-tooltip a {
  color: var(--primary-color);
}

[data-theme="dark"] .ql-snow .ql-tooltip input {
    background-color: var(--bg-color-tertiary);
    color: var(--text-color);
    border: 1px solid var(--border-color);
}

[data-theme="dark"] .quill-editor .ql-toolbar {
  background-color: var(--bg-color-tertiary);
  border-color: var(--border-color) !important;
}

[data-theme="dark"] .ql-snow.ql-toolbar .ql-stroke {
  stroke: var(--text-color-tertiary);
}

[data-theme="dark"] .ql-snow.ql-toolbar .ql-fill {
  fill: var(--text-color-tertiary);
}

/* Picker (dropdown) styles */
[data-theme="dark"] .ql-snow.ql-toolbar .ql-picker-label {
  color: var(--text-color-tertiary);
}

[data-theme="dark"] .ql-snow .ql-picker-options {
  background-color: var(--bg-color-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-color);
}

[data-theme="dark"] .ql-snow .ql-picker-item {
  color: var(--text-color-secondary);
}

[data-theme="dark"] .ql-snow .ql-picker-item:hover {
  background-color: var(--hover-color);
  color: var(--text-color);
}

[data-theme="dark"] .ql-snow .ql-picker-item.ql-selected {
  background-color: var(--active-color);
  color: var(--text-color);
}

[data-theme="dark"] .quill-editor .ql-container.ql-snow {
  border-color: var(--border-color);
}

[data-theme="dark"] .ql-editor {
  background-color: var(--bg-color-secondary);
  color: var(--text-color);
}

[data-theme="dark"] .ql-editor.ql-blank::before {
    color: var(--text-color-tertiary);
    font-style: normal;
}

/* Hover/active states for toolbar buttons */
[data-theme="dark"] .ql-snow.ql-toolbar button:hover,
[data-theme="dark"] .ql-snow.ql-toolbar .ql-picker-label:hover {
    background-color: var(--active-color);
    color: var(--primary-color);
}

[data-theme="dark"] .ql-snow.ql-toolbar button.ql-active,
[data-theme="dark"] .ql-snow.ql-toolbar .ql-picker-label.ql-active {
    background-color: var(--active-color);
    color: var(--primary-color);
}

[data-theme="dark"] .ql-snow.ql-toolbar button:hover .ql-stroke,
[data-theme="dark"] .ql-snow.ql-toolbar .ql-picker-label:hover .ql-stroke,
[data-theme="dark"] .ql-snow.ql-toolbar button.ql-active .ql-stroke,
[data-theme="dark"] .ql-snow.ql-toolbar .ql-picker-label.ql-active .ql-stroke {
    stroke: var(--primary-color);
}

[data-theme="dark"] .ai-feature-card {
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

[data-theme="dark"] .ai-feature-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}

[data-theme="dark"] .ai-feature-btn.el-button--info {
    background-color: var(--el-color-info-dark-2);
    border-color: var(--el-color-info-dark-2);
    color: #fff;
}

[data-theme="dark"] .ai-feature-btn.el-button--info:hover {
    background-color: var(--el-color-info-light-3);
    border-color: var(--el-color-info-light-3);
}

[data-theme="dark"] .ai-feature-btn.el-button--success {
    background-color: var(--el-color-success-dark-2);
    border-color: var(--el-color-success-dark-2);
    color: #fff;
}

[data-theme="dark"] .ai-feature-btn.el-button--success:hover {
    background-color: var(--el-color-success-light-3);
    border-color: var(--el-color-success-light-3);
}

.ai-feature-card:hover {
  box-shadow: 0 4px 16px rgba(80,120,200,0.13);
}
</style> 
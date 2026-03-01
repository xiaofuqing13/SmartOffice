<template>
  <div class="knowledge-container" :key="internalRefreshKey">
    <el-alert
      title="知识库使用说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px;"
    >
      <template #default>
        <div>
          知识库的<b>【上传文档】</b>、<b>【构建知识库】</b>及<b>【分类管理】</b>等核心功能，主要由企业所有者（老板角色）在后台进行统一管理和构建。
          <br>
          普通员工此页面进行已有知识的<b>查阅和检索</b>。
        </div>
      </template>
    </el-alert>
    
    <!-- 标签页导航 -->
    <el-tabs v-model="activeTab" class="knowledge-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="文档管理" name="documents">
        <template #label>
          <span class="tab-label">
            <el-icon><Document /></el-icon>
            文档管理
          </span>
        </template>
        <DocumentManagement ref="documentManagementRef" />
      </el-tab-pane>
      
      <el-tab-pane label="知识图谱" name="graph">
        <template #label>
          <span class="tab-label">
            <el-icon><DataAnalysis /></el-icon>
            知识图谱
          </span>
        </template>
        <KnowledgeGraph ref="knowledgeGraphRef" />
      </el-tab-pane>
    </el-tabs>
    
    <!-- 原有的文档管理内容，现在作为组件 -->
    <div v-show="false" class="row">
      <!-- 左侧导航 -->
      <div class="col-lg-3">
        <el-card class="category-card">
          <div class="search-box">
            <el-input 
              v-model="searchQuery" 
              placeholder="搜索文档..."
              clearable
              :prefix-icon="Search"
              @input="handleSearch"
            ></el-input>
          </div>
          
          <div class="category-list">
            <div v-for="(category, index) in categories" :key="category.id || index" 
                 class="category-item" 
                 :class="{'active': selectedCategory === (category.id || index)}"
                 @click="selectCategory(category.id || index)">
              <div class="category-icon" :style="{'background-color': category.color}">
                <el-icon :size="20" color="white">
                  <component :is="category.icon"></component>
                </el-icon>
              </div>
              <span class="category-name">{{ category.name }}</span>
              <span class="category-count">{{ category.document_count || 0 }}</span>
            </div>
            
            <!-- <el-button 
              v-if="isAdmin"
              type="primary" 
              size="small" 
              class="add-category-btn"
              @click="showCategoryDialog = true">
              <el-icon><Plus /></el-icon> 添加分类
            </el-button> -->
          </div>
          
          <div class="filter-section">
            <h6>筛选条件</h6>
            <div class="filter-group">
              <h6>文件类型</h6>
              <div class="filter-options">
                <el-checkbox v-model="filters.types.pdf" @change="applyFilters">PDF文档</el-checkbox>
                <el-checkbox v-model="filters.types.doc" @change="applyFilters">Word文档</el-checkbox>
                <el-checkbox v-model="filters.types.xls" @change="applyFilters">Excel表格</el-checkbox>
                <el-checkbox v-model="filters.types.ppt" @change="applyFilters">PPT演示文稿</el-checkbox>
                <el-checkbox v-model="filters.types.img" @change="applyFilters">图片</el-checkbox>
                <el-checkbox v-model="filters.types.txt" @change="applyFilters">文本文件</el-checkbox>
                <el-checkbox v-model="filters.types.md" @change="applyFilters">Markdown文件</el-checkbox>
              </div>
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 右侧内容区 -->
      <div class="col-lg-9">
        <div class="page-header">
          <h2 class="page-title">{{ currentCategoryName }}</h2>
            <div class="header-actions">
            <!-- <el-button type="primary" size="large" @click="openUploadDialog">
              <el-icon class="el-icon--left"><Upload /></el-icon> 上传文档
              </el-button>
            <el-button type="success" plain size="large" @click="buildingVisible = true">
              <el-icon class="el-icon--left"><Files /></el-icon> 构建知识库
              </el-button>
            <el-button v-if="isAdmin" text bg size="large" @click="showCategoryDialog = true">
              <el-icon class="el-icon--left"><FolderAdd /></el-icon> 管理分类
              </el-button> -->
            <el-button text bg size="large" @click="forceRefresh">
              <el-icon class="el-icon--left"><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>
          
        <el-card class="document-container-card" shadow="never">
          <div v-if="documents.length === 0" class="empty-state">
            <div class="empty-icon">
              <el-icon><InfoFilled /></el-icon>
            </div>
            <h3 class="empty-title">当前分类下暂无文档</h3>
          </div>
          
          <div v-else class="document-grid">
            <el-card 
              v-for="doc in documents" 
              :key="doc.id" 
              class="document-item-card" 
              shadow="hover"
              body-style="padding: 0; height: 100%; display: flex; flex-direction: column;"
            >
              <div class="card-header">
                <div class="file-icon" :class="'file-icon-' + doc.file_type">
                  <component :is="getFileIcon(doc.file_type)" />
              </div>
                <div class="document-title-block">
                  <h5 class="document-title" :title="doc.title">
                    {{ doc.title }}
                    <span v-if="doc.file_type" class="file-extension">.{{ doc.file_type }}</span>
                  </h5>
                  </div>
                </div>
              <div class="card-body">
                <p class="document-description">
                  {{ doc.description || '暂无描述信息' }}
                </p>
              </div>
              <div class="card-footer">
                <div class="document-meta">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatDate(doc.date) }}</span>
                </div>
                <div class="card-actions">
                  <el-button type="primary" text bg :icon="Download" @click.stop="downloadDocument(doc)">下载</el-button>
                   <!-- <el-dropdown trigger="click" @click.stop>
                    <el-button text bg class="more-button">
                      <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                        <el-dropdown-item @click="editDocument(doc)" :icon="Edit">编辑</el-dropdown-item>
                        <el-dropdown-item @click="deleteDocument(doc)" :icon="Delete" class="delete-item">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown> -->
              </div>
            </div>
            </el-card>
          </div>
          
          <div v-if="documents.length > 0" class="pagination-wrapper">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :total="totalDocs"
              :page-size="pageSize"
              :page-sizes="[12, 24, 48, 96]"
              :current-page="currentPage"
              @current-change="handlePageChange"
              @size-change="handleSizeChange"
            />
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="uploadVisible"
      title="上传文档"
      width="500px"
      :before-close="handleCloseUploadDialog"
    >
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules">
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入文档标题"></el-input>
        </el-form-item>
        <el-form-item label="文档描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="请输入文档描述"></el-input>
        </el-form-item>
        <el-form-item label="选择分类">
          <el-select v-model="uploadForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option
              v-for="(cat, idx) in categories.filter(c => c.id !== 'all')"
              :key="idx"
              :label="cat.name"
              :value="cat.id"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="文档文件" prop="file">
          <el-upload
            class="upload-demo"
            drag
            action="javascript:void(0);"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleRemove"
            :limit="1"
            :before-upload="beforeUpload"
            :on-error="handleUploadError"
            ref="uploadRef"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                <strong>仅支持</strong>上传 txt, pdf, doc, docx, md, ppt, pptx, xls, xlsx 格式文件，单个文件不超过10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCancelUpload">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分类管理对话框 -->
    <el-dialog
      v-model="showCategoryDialog"
      title="分类管理"
      width="850px"
    >
      <div class="category-dialog-content">
        <div class="category-list-section">
          <div class="section-header">
            <h5>已有分类</h5>
            <!-- <el-button 
              type="primary" 
              size="small" 
              @click="resetCategoryForm">
              <el-icon><Plus /></el-icon> 新增分类
            </el-button> -->
          </div>
          
          <div v-if="categoryLoading" class="text-center p-4">
            <el-icon class="is-loading"><Loading /></el-icon> 加载中...
          </div>
          
          <div v-else-if="categories.length <= 1" class="empty-categories">
            <el-empty description="" />
          </div>
          
          <div v-else class="category-items">
            <div v-for="(category, index) in categories.filter(c => c.id !== 'all')" :key="index" class="category-list-item">
              <div class="category-info">
                <div class="category-color" :style="{ backgroundColor: category.color }"></div>
                <div class="category-name-section">
                  <div class="category-name" :title="category.name">{{ category.name }}</div>
                  <div class="category-desc" :title="category.description">{{ category.description || '无描述' }}</div>
                </div>
              </div>
              
              <div class="category-details">
                <span class="category-count">{{ category.document_count || 0 }}个文档</span>
                <div class="category-actions">
                    <el-button type="primary" size="small" plain @click="editCategory(category)">
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button type="danger" size="small" plain @click="handleDeleteCategory(category)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="showAddCategoryForm" class="category-form-section">
          <div class="section-header">
            <h5>{{ editingCategory ? '编辑分类' : '新增分类' }}</h5>
            <el-button size="small" @click="cancelCategoryForm">
              取消
            </el-button>
          </div>
          
          <el-form :model="categoryForm" label-width="80px">
            <el-form-item label="分类名称" required>
              <el-input v-model="categoryForm.name" placeholder="请输入分类名称"></el-input>
            </el-form-item>
            
            <el-form-item label="分类描述">
              <el-input type="textarea" v-model="categoryForm.description" :rows="2" placeholder="请输入分类描述"></el-input>
            </el-form-item>
            
            <el-form-item label="图标">
              <el-select v-model="categoryForm.icon" placeholder="选择图标" style="width: 100%">
                <el-option value="Document" label="文档">
                  <div class="d-flex align-items-center">
                    <el-icon><Document /></el-icon> <span class="ml-2">文档</span>
                  </div>
                </el-option>
                <el-option value="Files" label="文件夹">
                  <div class="d-flex align-items-center">
                    <el-icon><Files /></el-icon> <span class="ml-2">文件夹</span>
                  </div>
                </el-option>
                <el-option value="Tickets" label="票据">
                  <div class="d-flex align-items-center">
                    <el-icon><Tickets /></el-icon> <span class="ml-2">票据</span>
                  </div>
                </el-option>
                <el-option value="DataAnalysis" label="数据分析">
                  <div class="d-flex align-items-center">
                    <el-icon><DataAnalysis /></el-icon> <span class="ml-2">数据分析</span>
                  </div>
                </el-option>
                <el-option value="PictureFilled" label="图片">
                  <div class="d-flex align-items-center">
                    <el-icon><PictureFilled /></el-icon> <span class="ml-2">图片</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="颜色">
              <el-color-picker v-model="categoryForm.color" show-alpha @change="formatColorValue"></el-color-picker>
              <span class="ml-2">{{ categoryForm.color }}</span>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveCategoryForm">保存</el-button>
              <el-button @click="cancelCategoryForm">取消</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-dialog>

    <!-- 知识库构建对话框组件 -->
    <KnowledgeBuilder 
      v-model="buildingVisible"
      @build-completed="handleBuildCompleted"
      @build-failed="handleBuildFailed"
    />

    <!-- 编辑文档对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑文档"
      width="500px"
      :before-close="handleCloseEditDialog"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="文档标题">
          <el-input v-model="editForm.title" placeholder="请输入文档标题"></el-input>
        </el-form-item>
        <el-form-item label="文档描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入文档描述"></el-input>
        </el-form-item>
        <el-form-item label="选择分类">
          <el-select v-model="editForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option
              v-for="(cat, idx) in categories.filter(c => c.id !== 'all')"
              :key="idx"
              :label="cat.name"
              :value="cat.id"
            ></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCancelEditDialog">取消</el-button>
          <el-button type="primary" @click="handleUpdateDocument">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount, onActivated, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Upload, FolderAdd, View, Download, More, Share, 
  Edit, EditPen, FolderOpened, Star, Delete, Document, 
  Files, Tickets, DataAnalysis, PictureFilled, UploadFilled,
  Loading, List, Grid, Crop, Plus, InfoFilled, Clock, User,
  Refresh
} from '@element-plus/icons-vue'
import { getCategories, getDocuments, getDocumentChunks, uploadDocument, updateDocument, deleteDocument as apiDeleteDocument, deleteCategory, updateCategory, addCategory, downloadDocumentFile } from '@/api/knowledge'
import KnowledgeBuilder from '@/components/KnowledgeBuilder.vue'
import KnowledgeGraph from './components/KnowledgeGraph.vue'
import DocumentManagement from './components/DocumentManagement.vue'

export default {
  name: 'Knowledge',
  components: {
    KnowledgeBuilder,
    KnowledgeGraph,
    DocumentManagement
  },
  setup() {
    // 路由相关
    const route = useRoute();
    
    // 内部刷新标识
    const internalRefreshKey = ref(Date.now());
    
    // 状态变量
    const activeTab = ref('documents')
    const searchQuery = ref('')
    const selectedCategory = ref('all')
    const currentPage = ref(1)
    const pageSize = ref(10)
    const uploadVisible = ref(false)
    const editDialogVisible = ref(false)
    const showCategoryDialog = ref(false)
    const showAddCategoryForm = ref(false)
    const showChunksDialog = ref(false)
    const editingCategory = ref(null)
    const viewMode = ref('list')
    const sortOrder = ref('-created_at')
    const categoryLoading = ref(false)
    const loading = ref(false)
    const uploading = ref(false)
    const chunksLoading = ref(false)
    const isAdmin = ref(true) // 实际应用中从用户会话获取
    const selectedDocument = ref(null)
    const documentChunks = ref([])
    const uploadFormRef = ref(null)
    const uploadRef = ref(null)
    const totalDocs = ref(0)
    const documentManagementRef = ref(null)
    const knowledgeGraphRef = ref(null)
    
    // 编辑表单
    const editForm = reactive({
      id: null,
      title: '',
      description: '',
      category: null,
      creator: null,
    })
    
    // 上传表单
    const uploadForm = reactive({
      title: '',
      description: '',
      file: null,
      category: null,
      tags: '',
      chunk_size: 500,
      chunk_overlap: 50,
      is_public: true
    })
    
    // 上传表单验证规则
    const uploadRules = {
      title: [
        { required: true, message: '请输入文档标题', trigger: 'blur' }
      ],
      file: [
        { required: true, message: '请上传文件', trigger: 'change' }
      ]
    }
    
    // 分类表单
    const categoryForm = reactive({
      id: null,
      name: '',
      description: '',
      icon: 'Document',
      color: '#409EFF'
    })
    
    // 筛选条件
    const filters = ref({
      types: {
        pdf: false,
        doc: false,
        xls: false,
        ppt: false,
        img: false,
        txt: false,
        md: false,
      },
    })
    
    // 知识分类
    const categories = ref([
      { id: 'all', name: '全部文档', icon: 'Files', color: '#007bff', document_count: 0 }
    ])
    
    // 文档列表
    const documents = ref([])
    
    // 计算属性
    const currentCategoryName = computed(() => {
      const category = categories.value.find(cat => cat.id === selectedCategory.value)
      return category ? category.name : '全部文档'
    })
    
    const processingCount = computed(() => {
      return documents.value.filter(doc => doc.status === 'processing').length
    })
    
    // 知识库构建相关状态
    const buildingVisible = ref(false)
    
    // 方法
    const fetchCategories = async () => {
      categoryLoading.value = true
      console.log('开始获取知识库分类...')
      try {
        // console.log('请求URL:', `${API_URL}/categories/`) // 已被实际API调用取代
        const response = await getCategories() // API call for specific categories
        console.log('获取分类响应:', response)
        
        let categoryList = []
        
        // 处理不同格式的响应 (for specific categories)
        if (response) {
          if (response.results && Array.isArray(response.results)) {
            categoryList = response.results
          } 
          else if (Array.isArray(response)) {
            categoryList = response
          } 
          else if (typeof response === 'object') {
            const possibleArrayFields = ['data', 'categories', 'items'];
            for (const field of possibleArrayFields) {
              if (response[field] && Array.isArray(response[field])) {
                categoryList = response[field];
                break;
              }
            }
          }
        }

        // Fetch the grand total of all documents
        let grandTotalAllDocuments = 0;
        try {
          // Lightweight request to get the total count of all documents
          const allDocsResponse = await getDocuments({ page: 1, page_size: 1 }); 
          if (allDocsResponse && Object.prototype.hasOwnProperty.call(allDocsResponse, 'count')) {
            grandTotalAllDocuments = allDocsResponse.count;
            console.log('获取到全部文档总数:', grandTotalAllDocuments);
          } else {
            console.warn('未能从 getDocuments 响应中获取总数 count:', allDocsResponse);
          }
        } catch (docError) {
          console.error('获取全部文档总数失败:', docError);
          // 保留 grandTotalAllDocuments = 0 或根据需要处理错误
        }
        
        // 创建 "全部文档" 分类
        const allCategory = { 
          id: 'all', 
          name: '全部文档', 
          icon: 'Files', 
          color: '#007bff', 
          document_count: grandTotalAllDocuments // 使用获取到的真实总数
        }
        
        if (categoryList && categoryList.length > 0) {
          console.log('找到分类数据，数量:', categoryList.length);
          // 不再通过累加其他分类来计算 allCategory.document_count
          categories.value = [allCategory, ...categoryList]
        } else {
          console.warn('未找到有效的分类数据');
          if (response && response.message) {
            ElMessage.warning(response.message);
          } else if (!response && !categoryList.length) { // Only show if response was truly empty and no list was parsed
             // 删除警告消息
          }
          categories.value = [allCategory]; // 至少显示"全部文档"分类
        }
      } catch (error) {
        console.error('获取分类失败:', error)
        if (error.response) {
          console.error('错误响应状态:', error.response.status)
          console.error('错误响应数据:', error.response.data)
        } else if (error.message && error.message.includes('message channel closed')) {
          console.warn('通信通道关闭：', error.message);
          // 静默处理此类错误，不向用户显示
        } else {
          ElMessage.error('无法加载知识库分类，请检查网络连接或联系管理员')
        }
        // 确保至少有"全部"分类可显示
        categories.value = [{ 
          id: 'all', 
          name: '全部文档', 
          icon: 'Files', 
          color: '#007bff', 
          document_count: 0 
        }];
      } finally {
        categoryLoading.value = false
      }
    }
    
    const fetchDocuments = async () => {
      loading.value = true
      try {
        // 构建参数对象
        const params = {
          page: currentPage.value,
          page_size: pageSize.value,
          ordering: sortOrder.value
        }
        
        // 添加筛选条件
        if (selectedCategory.value && selectedCategory.value !== 'all') {
          params.category = selectedCategory.value
        }
        
        // 添加搜索查询
        if (searchQuery.value) {
          params.search = searchQuery.value
        }
        
        // 添加文件类型筛选
        const selectedTypes = []
        const typeMapping = {
          doc: ['doc', 'docx'],
          xls: ['xls', 'xlsx'],
          ppt: ['ppt', 'pptx'],
        };

        for (const [type, selected] of Object.entries(filters.value.types)) {
          if (selected) {
            if (typeMapping[type]) {
              selectedTypes.push(...typeMapping[type]);
            } else {
              selectedTypes.push(type);
            }
          }
        }
        
        // 使用Set去重，以防将来可能的逻辑重叠
        const uniqueSelectedTypes = [...new Set(selectedTypes)];

        if (uniqueSelectedTypes.length > 0) {
          params.file_type = uniqueSelectedTypes.join(',')
        }
        
        const response = await getDocuments(params)
        if (response) {
          console.log('获取文档响应:', response)
          
          // 处理不同格式的响应
          if (response.results && Array.isArray(response.results)) {
            // 分页格式的响应
            documents.value = response.results
            totalDocs.value = response.count || response.total || documents.value.length
          } else if (Array.isArray(response)) {
            // 数组格式的响应
            documents.value = response
            totalDocs.value = response.length
          } else if (response.data && Array.isArray(response.data)) {
            // 另一种常见的对象包装格式
            documents.value = response.data
            totalDocs.value = response.total || response.count || documents.value.length
          } else if (typeof response === 'object') {
            // 尝试提取可能的文档列表
            const possibleDocuments = Object.values(response).filter(item => 
              item && typeof item === 'object' && ('title' in item || 'file' in item)
            )
            if (possibleDocuments.length > 0) {
              documents.value = possibleDocuments
              totalDocs.value = possibleDocuments.length
            } else {
              console.error('无法从响应中提取文档列表:', response)
              documents.value = []
              totalDocs.value = 0
              ElMessage.warning('获取文档列表格式异常')
            }
          } else {
            console.error('文档响应格式不支持:', typeof response, response)
            documents.value = []
            totalDocs.value = 0
            ElMessage.warning('获取文档列表格式不支持')
          }
        } else {
          documents.value = []
          totalDocs.value = 0
        }
      } catch (error) {
        console.error('获取文档失败:', error)
        ElMessage.error('无法加载知识库文档')
      } finally {
        loading.value = false
      }
    }
    
    const fetchDocumentChunks = async (documentId) => {
      chunksLoading.value = true
      try {
        const response = await getDocumentChunks(documentId)
        documentChunks.value = response
      } catch (error) {
        console.error('获取文档分块失败:', error)
        ElMessage.error('无法加载文档分块数据')
      } finally {
        chunksLoading.value = false
      }
    }
    
    const handlePageChange = (page) => {
      currentPage.value = page
      fetchDocuments()
    }
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      fetchDocuments()
    }
    
    const selectCategory = (categoryId) => {
      selectedCategory.value = categoryId
      currentPage.value = 1
      fetchDocuments()
    }
    
    const handleSearch = () => {
      currentPage.value = 1
      fetchDocuments()
    }
    
    const applyFilters = () => {
      currentPage.value = 1
      fetchDocuments()
    }
    
    const handleFileChange = (file) => {
      console.log(">>> handleFileChange: Received file object from el-upload:", file);
      if (file && file.raw) {
        console.log(">>> handleFileChange: file.raw (the actual File object):", file.raw);
        
        // 检查文件大小是否为0，这会导致上传失败
        if (file.raw.size === 0) {
          ElMessage.error('文件大小为0，请选择有效文件');
          return false;
        }
        
        // 检查文件是否过大（例如超过10MB）
        const maxSizeInBytes = 10 * 1024 * 1024; // 10MB
        if (file.raw.size > maxSizeInBytes) {
          ElMessage.error(`文件过大，最大支持${maxSizeInBytes / (1024 * 1024)}MB`);
          return false;
        }
        
        // 严格检查文件扩展名是否支持
        const fileName = file.raw.name;
        const ext = fileName.slice(fileName.lastIndexOf('.') + 1).toLowerCase();
        const allowedFileTypes = ['txt', 'pdf', 'doc', 'docx', 'md', 'ppt', 'pptx', 'xls', 'xlsx'];
        
        if (!allowedFileTypes.includes(ext)) {
          ElMessage.error(`不支持的文件类型: ${ext}。仅支持 ${allowedFileTypes.join(', ')} 格式。`);
          // 不支持的文件类型不应该更新uploadForm.file
          uploadForm.file = null;
          // 清除上传组件中显示的文件
          if (uploadRef.value) {
            uploadRef.value.clearFiles();
          }
          return false;
        }
        
        // 仅在验证通过后设置文件
        uploadForm.file = file.raw
        console.log(">>> handleFileChange: uploadForm.file after assignment:", uploadForm.file, uploadForm.file ? `Name: ${uploadForm.file.name}, Size: ${uploadForm.file.size} bytes, Type: ${uploadForm.file.type}` : 'No file');
        uploadForm.title = uploadForm.title || file.name.split('.')[0];
        
        // 返回true表示验证通过
        return true;
      } else {
        console.warn(">>> handleFileChange: file.raw is not available. File:", file);
        return false;
      }
    }
    
    const handleRemove = () => {
      console.log(">>> handleRemove: File removed by user. Setting uploadForm.file to null.");
      uploadForm.file = null;
      
      // 如果标题是自动从文件名生成的，也清除标题
      if (uploadForm.title && uploadForm.title.includes('.')) {
        const fileNameWithoutExt = uploadForm.file?.name?.split('.')[0];
        if (uploadForm.title === fileNameWithoutExt) {
          uploadForm.title = '';
        }
      }
    }
    
    const beforeUpload = (file) => {
      // 获取文件扩展名
      const fileName = file.name;
      const ext = fileName.slice(fileName.lastIndexOf('.') + 1).toLowerCase();
      
      // 允许的文件类型列表
      const allowedFileTypes = ['txt', 'pdf', 'doc', 'docx', 'md', 'ppt', 'pptx', 'xls', 'xlsx'];
      
      // 严格检查文件类型
      if (!allowedFileTypes.includes(ext)) {
        ElMessage.error(`不支持的文件类型: ${ext}。仅支持 ${allowedFileTypes.join(', ')} 格式。`);
        return false;
      }
      
      // 检查文件大小
      const maxSizeInBytes = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSizeInBytes) {
        ElMessage.error(`文件大小超过限制，最大支持 ${maxSizeInBytes / (1024 * 1024)}MB`);
        return false;
      }
      
      // 检查文件是否为空
      if (file.size === 0) {
        ElMessage.error('文件为空，请选择有效文件');
        return false;
      }
      
      return true;
    }
    
    const handleUploadError = (error) => {
      console.error('上传错误:', error);
      ElMessage.error('上传错误，请检查文件格式或网络连接');
      // 移除错误文件
      uploadForm.file = null;
    }
    
    const submitUpload = async () => {
      if (!uploadFormRef.value) return
      
      await uploadFormRef.value.validate(async (valid) => {
        if (valid) {
          uploading.value = true
          
          console.log(">>> submitUpload: Current uploadForm.file before appending to FormData:", uploadForm.file);
          if (!uploadForm.file) {
            console.warn(">>> submitUpload: uploadForm.file is null or undefined before appending.");
            uploading.value = false;
            ElMessage.warning("请先选择文件再上传");
            return;
          }
          
          // 再次检查文件大小，确保不是空文件或损坏文件
          if (uploadForm.file.size === 0) {
            console.error(">>> submitUpload: 文件大小为0，无法上传");
            uploading.value = false;
            ElMessage.error("文件大小为0，请选择有效文件");
            return;
          }
          
          console.log(`>>> submitUpload: uploadForm.file details - Name: ${uploadForm.file.name}, Size: ${uploadForm.file.size} bytes, Type: ${uploadForm.file.type}`);
          
          // 创建formData对象，并添加文件和其他参数
          const formData = new FormData()
          formData.append('title', uploadForm.title)
          formData.append('description', uploadForm.description)
          formData.append('file', uploadForm.file) // Appending the file
          
          if (uploadForm.category) {
            formData.append('category', uploadForm.category)
            console.log(`>>> submitUpload: Attaching category to FormData: ${uploadForm.category}`)
          } else {
            console.log(">>> submitUpload: No category selected (uploadForm.category is null/empty). Not attaching to FormData.")
          }
          
          formData.append('tags', JSON.stringify(uploadForm.tags))
          formData.append('chunk_size', uploadForm.chunk_size.toString())
          formData.append('chunk_overlap', uploadForm.chunk_overlap.toString())
          formData.append('is_public', uploadForm.is_public.toString())
          
          // 再次检查formData中的文件是否正确
          const fileInFormData = formData.get('file');
          if (!fileInFormData || fileInFormData.size === 0) {
            console.error(">>> submitUpload: FormData中的文件无效或大小为0");
            uploading.value = false;
            ElMessage.error("FormData处理文件失败，请重试");
            return;
          }

          try {
            const response = await uploadDocument(formData) // Assuming uploadDocument returns the new document object or its ID
            console.log(">>> submitUpload: API Response from uploadDocument:", response);

            ElMessage.success('文档上传请求已发送，后台正在处理...')
            uploading.value = false // 确保上传状态被重置
            uploadVisible.value = false
            const uploadedFileTitle = uploadForm.title; // Store title for polling check
            resetUploadForm()

            // Start polling for document status if response contains an ID or enough info
            // For simplicity, we'll poll fetchDocuments and look for the title, assuming titles are reasonably unique for recent uploads.
            // A more robust way is if backend returns the new document ID, and we poll a getDocumentById(id) endpoint.
            // Or if the document object in fetchDocuments has a clear 'status' field (e.g., 'processing', 'completed').
            
            let attempts = 0;
            const maxAttempts = 10; // Poll for max 30 seconds (10 attempts * 3s interval)
            const pollInterval = 3000; // 3 seconds

            const poll = setInterval(async () => {
              attempts++;
              console.log(`>>> Polling for document status (attempt ${attempts}/${maxAttempts})...`);
              try {
                // Fetch the list of documents, usually sorted by creation date descending
                const documentsResponse = await getDocuments({ 
                  page: 1, 
                  page_size: 10, // Check recent documents
                  ordering: '-created_at', 
                  category: selectedCategory.value || undefined, // Use current category or all if 'all'
                  // search: uploadedFileTitle // Optionally, if backend supports search by title for recent items
                });

                let foundDoc = null;
                if (documentsResponse && documentsResponse.results && documentsResponse.results.length > 0) {
                  // Attempt to find the document by title. This is a simplification.
                  // Ideally, backend returns ID and we poll for that ID, or a status field directly.
                  foundDoc = documentsResponse.results.find(doc => doc.title === uploadedFileTitle);
                  
                  // MORE ROBUST CHECK: Assume doc object has a 'status' field from backend
                  // Example: if (doc.status === 'completed') { ... }
                  // For now, if we find it by title recently, we assume it might be processed or soon.
                }

                if (foundDoc) {
                  // Let's assume if found by title, it's processed enough for a refresh.
                  // Replace this with actual status check if backend provides 'status' field.
                  console.log(`>>> Polling: Document "${uploadedFileTitle}" found (or assumed processed). Refreshing lists.`);
                  clearInterval(poll);
                  fetchDocuments();
                  fetchCategories();
                  ElMessage.success(`文档 "${uploadedFileTitle}" 处理完毕并已刷新列表!`);
                  // 确保所有状态正确重置
                  uploading.value = false;
                } else if (attempts >= maxAttempts) {
                  console.log(">>> Polling: Max attempts reached. Refreshing lists anyway.");
                  clearInterval(poll);
                  fetchDocuments();
                  fetchCategories();
                  ElMessage.info(`文档 "${uploadedFileTitle}" 可能仍在后台处理中，列表已刷新。`);
                  // 确保所有状态正确重置
                  uploading.value = false;
                }
              } catch (pollError) {
                console.error(">>> Polling error:", pollError);
                clearInterval(poll);
                // Still refresh, as the document might be there despite polling error
                fetchDocuments();
                fetchCategories();
                ElMessage.error('检查文档状态时出错，列表已刷新。');
                // 确保所有状态正确重置
                uploading.value = false;
              }
            }, pollInterval);

          } catch (error) {
            console.error('上传文档失败:', error)
            uploading.value = false;
            // 在上传失败时清除文件选择状态
            if (uploadRef.value) {
              uploadRef.value.clearFiles();
            }
            let errorMsg = '文档上传失败'
            if (error.response && error.response.data) {
              const data = error.response.data;
              if (typeof data === 'string') errorMsg += ': ' + data;
              else if (data.detail) errorMsg += ': ' + data.detail;
              else if (data.message) errorMsg += ': ' + data.message;
              else if (data.file && Array.isArray(data.file)) errorMsg += ': ' + data.file.join(', ');
              // 处理特定的文件类型错误
              else if (data.status === 'error' && data.message && data.message.includes('不支持的文件类型')) {
                errorMsg = data.message; // 直接使用后端的错误消息
              }
              else if (typeof data === 'object') errorMsg += ': ' + JSON.stringify(data).substring(0, 100);
            }
            ElMessage.error(errorMsg);
          }
        } else {
          console.log('error submit!! Form validation failed.');
          uploading.value = false; // Ensure uploading is reset if validation fails
          return false;
        }
      })
    }
    
    const showDocumentChunks = async (doc) => {
      selectedDocument.value = doc
      showChunksDialog.value = true
      await fetchDocumentChunks(doc.id)
    }
    
    const editCategory = (category) => {
      editingCategory.value = category
      categoryForm.id = category.id
      categoryForm.name = category.name
      categoryForm.description = category.description || ''
      categoryForm.icon = category.icon || 'Document'
      
      // 确保颜色值不超过20个字符
      if (category.color && category.color.length > 20) {
        categoryForm.color = category.color.substring(0, 20);
        console.log(`编辑分类时截断颜色值: ${category.color} -> ${categoryForm.color}`);
      } else {
        categoryForm.color = category.color || '#409EFF'
      }
      
      showAddCategoryForm.value = true // 显示编辑表单
    }
    
    const handleDeleteCategory = async (category) => {
      try {
        await ElMessageBox.confirm(`确定要删除分类 "${category.name}" 吗？`, '删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await deleteCategory(category.id)
        ElMessage.success('分类删除成功')
        fetchCategories()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除分类失败:', error)
          ElMessage.error('删除分类失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
        }
      }
    }
    
    const saveCategoryForm = async () => {
      console.log('保存分类表单被调用，模式:', editingCategory.value ? 'edit' : 'add')
      
      // 确保颜色值不超过20个字符
      formatColorValue(categoryForm.color);
      
      showAddCategoryForm.value = false
      if (editingCategory.value) {
        console.log('尝试更新分类:', categoryForm)
        if (!editingCategory.value.id) {
            ElMessage.error('无法更新分类，未找到当前编辑的分类ID');
            return;
        }
        try {
          const response = await updateCategory(editingCategory.value.id, categoryForm)
          console.log('更新分类响应:', response)
          if (response && (response.id || (response.data && response.data.id))) {
            ElMessage.success('分类更新成功')
            await fetchCategories() // 刷新分类列表
            // 如果当前编辑的分类就是选中的分类，可能需要刷新文档列表
            if (selectedCategory.value === (response.id || response.data.id)) {
              await fetchDocuments();
            }
          } else if (response && response.error) {
            ElMessage.error(`更新分类失败: ${response.error.message || '未知错误'}`)
          } else if (response && response.detail) {
             ElMessage.error(`更新分类失败: ${response.detail}`)
          }
          else {
            ElMessage.error('更新分类失败，响应格式不符合预期或无ID返回')
          }
        } catch (error) {
          console.error('更新分类失败:', error)
          ElMessage.error('更新分类失败，请检查网络或联系管理员')
        }
      } else {
        console.log('尝试添加新分类:', categoryForm)
        try {
          const response = await addCategory(categoryForm)
          console.log('添加分类响应:', response)
          if (response && (response.id || (response.data && response.data.id))) {
            ElMessage.success('分类添加成功')
            await fetchCategories() // 刷新分类列表
            // 自动选中新创建的分类并刷新文档列表
            const newCategoryId = response.id || response.data.id;
            if (newCategoryId) {
              selectedCategory.value = newCategoryId;
              console.log(`新分类创建成功，自动选中新分类 ID: ${newCategoryId}`);
              await fetchDocuments(); // 刷新文档列表以显示新选中的分类（初始为空）
            } else {
              console.warn("新创建的分类ID未找到，无法自动选中。");
            }
          } else if (response && response.error) {
            ElMessage.error(`添加分类失败: ${response.error.message || '未知错误'}`)
          } else if (response && response.detail) {
             ElMessage.error(`添加分类失败: ${response.detail}`)
          }
           else {
            ElMessage.error('添加分类失败，响应格式不符合预期或无ID返回')
            console.error("添加分类失败，响应:", response);
          }
        } catch (error) {
          console.error('添加分类失败:', error)
          ElMessage.error('添加分类失败，请检查网络或联系管理员')
        }
      }
      resetCategoryForm()
    }
    
    const cancelCategoryForm = () => {
      showAddCategoryForm.value = false
      editingCategory.value = null
      categoryForm.id = null
      categoryForm.name = ''
      categoryForm.description = ''
      categoryForm.icon = 'Document'
      categoryForm.color = '#409EFF' // 确保默认颜色值不超过20个字符
    }
    
    const resetCategoryForm = () => {
      editingCategory.value = null
      categoryForm.id = null
      categoryForm.name = ''
      categoryForm.description = ''
      categoryForm.icon = 'Document'
      categoryForm.color = '#409EFF' // 确保默认颜色值不超过20个字符
      showAddCategoryForm.value = true
    }
    
    const resetUploadForm = () => {
      if (uploadFormRef.value) {
        // 使用el-form的resetFields方法重置表单
        uploadFormRef.value.resetFields(); 
      }
      
      // 手动重置所有uploadForm字段，确保全部清空
      uploadForm.title = ''
      uploadForm.description = ''
      uploadForm.file = null
      uploadForm.category = null // Explicitly reset category
      uploadForm.tags = ''
      uploadForm.is_public = true
      uploadForm.chunk_size = 500 // 重置为初始默认值
      uploadForm.chunk_overlap = 50 // 重置为初始默认值
      
      // 清除上传组件中的文件
      if (uploadRef.value) {
        uploadRef.value.clearFiles();
      }
      
      console.log(">>> resetUploadForm: uploadForm和上传组件已完全重置");
    }
    
    const handleCancelUpload = () => {
      // 如果正在上传，不允许关闭
      if (uploading.value) {
        ElMessage.warning('文件正在上传中，请等待上传完成');
        return;
      }
      resetUploadForm();
      uploadVisible.value = false;
    }
    
    const handleCloseUploadDialog = (done) => {
      handleCancelUpload();
      done(); // 允许关闭对话框
    }
    
    const openUploadDialog = () => {
      resetUploadForm(); // Reset form first for a clean state
      if (selectedCategory.value && selectedCategory.value !== 'all') {
        uploadForm.category = selectedCategory.value;
        console.log(`>>> openUploadDialog: Auto-selecting current category: ${selectedCategory.value}`);
      } else {
        uploadForm.category = null; // If 'all' or no category is selected, let user choose in dialog
        console.log(">>> openUploadDialog: No category auto-selected (current is 'all' or none).");
      }
      uploadVisible.value = true;
    };
    
    // 文件操作函数
    const previewDocument = async (doc) => {
      try {
        // 记录文档对象，便于调试
        console.log('预览文档对象:', doc);
        
        // 检查是否有 original_file 字段
        if (doc.original_file) {
          try {
            const response = await fetch(doc.original_file);
            if (response.ok) {
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              window.open(url, '_blank');
              setTimeout(() => window.URL.revokeObjectURL(url), 100);
              return;
            }
          } catch (error) {
            console.warn('通过 original_file 访问失败，尝试其他方式:', error);
          }
        }
        
        // 首先尝试通过API获取文件
        try {
          const response = await downloadDocumentFile(doc.id);
        const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/octet-stream' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        setTimeout(() => window.URL.revokeObjectURL(url), 100);
          return;
        } catch (apiError) {
          console.warn('通过API获取文件失败，尝试直接访问文件URL:', apiError);
        }
        
        // 如果API调用失败，尝试直接访问文件URL
        if (doc.file_url) {
          // 尝试直接访问原始URL
          try {
            const response = await fetch(doc.file_url);
            if (response.ok) {
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              window.open(url, '_blank');
              setTimeout(() => window.URL.revokeObjectURL(url), 100);
              return;
            }
          } catch (urlError) {
            console.warn('直接访问文件URL失败:', urlError);
          }
          
          // 尝试修正的URL路径
          // 从file_url中提取文件名
          const fileUrlParts = doc.file_url.split('/');
          const originalFilename = fileUrlParts[fileUrlParts.length - 1];
          
          // 尝试从file_url中提取可能的UUID
          let uuid = null;
          const uuidMatch = doc.file_url.match(/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/);
          if (uuidMatch && uuidMatch[1]) {
            uuid = uuidMatch[1];
            console.log('从URL中提取的UUID:', uuid);
          }
          
          // 构造可能的替代路径
          const possiblePaths = [
            `/media/original_files/${originalFilename}`,
            `/media/original_files/company_1/${originalFilename}`,
            `/backend/media/original_files/${originalFilename}`,
            `/backend/media/original_files/company_1/${originalFilename}`,
            `/media/documents/1/${originalFilename}`,
            `/backend/media/documents/1/${originalFilename}`
          ];
          
          // 如果文件名不是UUID格式，尝试在documents目录下查找可能匹配的文件
          if (!originalFilename.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[a-z]+$/)) {
            // 尝试使用文档ID作为文件名的一部分
            if (doc.id) {
              possiblePaths.push(`/media/documents/1/${doc.id}.${doc.file_type}`);
              possiblePaths.push(`/backend/media/documents/1/${doc.id}.${doc.file_type}`);
            }
          }
          
          // 如果从URL中提取到了UUID，尝试使用UUID构造路径
          if (uuid) {
            possiblePaths.push(`/media/documents/1/${uuid}.${doc.file_type}`);
            possiblePaths.push(`/backend/media/documents/1/${uuid}.${doc.file_type}`);
          }
          
          // 尝试所有可能的路径
          for (const path of possiblePaths) {
            try {
              const response = await fetch(path);
              if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                window.open(url, '_blank');
                setTimeout(() => window.URL.revokeObjectURL(url), 100);
                return;
              }
            } catch (pathError) {
              console.warn(`尝试路径 ${path} 失败:`, pathError);
            }
          }
        }
        
        // 所有尝试都失败，显示错误消息
        throw new Error('无法找到有效的文件路径');
      } catch (error) {
        console.error('预览文档失败:', error);
        ElMessage.error('预览文档失败: 无法找到或访问文件。请联系管理员检查文件路径配置。');
      }
    }
    
    const downloadDocument = async (doc) => {
      try {
        // 记录文档对象，便于调试
        console.log('下载文档对象:', doc);
        
        // 检查是否有 original_file 字段
        if (doc.original_file) {
          try {
            const response = await fetch(doc.original_file);
            if (response.ok) {
              const blob = await response.blob();
              const filename = doc.original_filename || doc.title + '.' + doc.file_type;
              
              const url = window.URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', filename);
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              window.URL.revokeObjectURL(url);
              
              ElMessage.success(`文档 "${filename}" 下载成功`);
              return;
            }
          } catch (error) {
            console.warn('通过 original_file 下载失败，尝试其他方式:', error);
          }
        }
        
        // 首先尝试通过API获取文件
        try {
          const response = await downloadDocumentFile(doc.id);
          const filename = doc.title ? `${doc.title}.${doc.file_type}` : 
                          (doc.file_url ? doc.file_url.split('/').pop() : `document.${doc.file_type}`);
          
          const url = window.URL.createObjectURL(new Blob([response.data], { type: response.headers['content-type'] || 'application/octet-stream' }));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', filename);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          ElMessage.success(`文档 "${filename}" 下载成功`);
          return;
        } catch (apiError) {
          console.warn('通过API获取文件失败，尝试直接访问文件URL:', apiError);
        }
        
        // 如果API调用失败，尝试直接访问文件URL
        if (doc.file_url) {
          // 尝试直接访问原始URL
          try {
            const response = await fetch(doc.file_url);
            if (response.ok) {
              const blob = await response.blob();
              const filename = doc.title ? `${doc.title}.${doc.file_type}` : doc.file_url.split('/').pop();
              
              const url = window.URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', filename);
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              window.URL.revokeObjectURL(url);
              
              ElMessage.success(`文档 "${filename}" 下载成功`);
              return;
            }
          } catch (urlError) {
            console.warn('直接访问文件URL失败:', urlError);
          }
          
          // 尝试修正的URL路径
          const fileUrlParts = doc.file_url.split('/');
          const originalFilename = fileUrlParts[fileUrlParts.length - 1];
          
          // 尝试从file_url中提取可能的UUID
          let uuid = null;
          const uuidMatch = doc.file_url.match(/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/);
          if (uuidMatch && uuidMatch[1]) {
            uuid = uuidMatch[1];
            console.log('从URL中提取的UUID:', uuid);
          }
          
          // 构造可能的替代路径
          const possiblePaths = [
            `/media/original_files/${originalFilename}`,
            `/media/original_files/company_1/${originalFilename}`,
            `/backend/media/original_files/${originalFilename}`,
            `/backend/media/original_files/company_1/${originalFilename}`,
            `/media/documents/1/${originalFilename}`,
            `/backend/media/documents/1/${originalFilename}`
          ];
          
          // 如果文件名不是UUID格式，尝试在documents目录下查找可能匹配的文件
          if (!originalFilename.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[a-z]+$/)) {
            // 尝试使用文档ID作为文件名的一部分
            if (doc.id) {
              possiblePaths.push(`/media/documents/1/${doc.id}.${doc.file_type}`);
              possiblePaths.push(`/backend/media/documents/1/${doc.id}.${doc.file_type}`);
            }
          }
          
          // 如果从URL中提取到了UUID，尝试使用UUID构造路径
          if (uuid) {
            possiblePaths.push(`/media/documents/1/${uuid}.${doc.file_type}`);
            possiblePaths.push(`/backend/media/documents/1/${uuid}.${doc.file_type}`);
          }
          
          // 尝试所有可能的路径
          for (const path of possiblePaths) {
            try {
              const response = await fetch(path);
              if (response.ok) {
                const blob = await response.blob();
                const filename = doc.title ? `${doc.title}.${doc.file_type}` : originalFilename;
                
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', filename);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
                
                ElMessage.success(`文档 "${filename}" 下载成功`);
                return;
              }
            } catch (pathError) {
              console.warn(`尝试路径 ${path} 失败:`, pathError);
            }
          }
        }
        
        // 所有尝试都失败，显示错误消息
        throw new Error('无法找到有效的文件路径');
      } catch (error) {
        console.error('下载文档失败:', error);
        ElMessage.error('下载文档失败: 无法找到或访问文件。请联系管理员检查文件路径配置。');
      }
    }
    
    const shareDocument = (doc) => {
      // 实现文档分享功能
      console.log('准备分享文档:', doc.title)
      ElMessage.info(`文档"${doc.title}"的分享功能即将上线`)
    }
    
    const editDocument = (doc) => {
      editForm.id = doc.id;
      editForm.title = doc.title;
      editForm.description = doc.description;
      editForm.category = doc.category;
      editForm.creator = doc.creator;
      editDialogVisible.value = true;
    }

    const handleUpdateDocument = async () => {
      if (!editForm.id) return;
      try {
        await updateDocument(editForm.id, {
          title: editForm.title,
          description: editForm.description,
          category: editForm.category,
          creator: editForm.creator,
        });
        ElMessage.success('文档更新成功');
        editDialogVisible.value = false;
        fetchDocuments(); // 刷新列表
      } catch (error) {
        console.error('更新文档失败:', error);
        let errorMsg = '更新文档失败';
        if (error.response && error.response.data) {
          const data = error.response.data;
          if (typeof data === 'object' && data !== null) {
            const messages = Object.entries(data).map(([field, errors]) => {
              return `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`;
            }).join('; ');

            if (messages) {
              errorMsg += `: ${messages}`;
            } else {
              errorMsg += `: 请求失败，无详细信息。`;
            }
          } else {
            errorMsg += `: ${data}`;
          }
        } else if (error.message) {
          errorMsg += `: ${error.message}`;
        } else {
          errorMsg += ': 未知错误';
        }
        ElMessage.error(errorMsg);
      }
    };
    
    const handleCloseEditDialog = (done) => {
      editDialogVisible.value = false;
      done();
    }

    const handleCancelEditDialog = () => {
      editDialogVisible.value = false;
    }

    const deleteDocument = async (doc) => {
      console.log('>>> Vue component: Attempting to delete document (local method):', doc); // Log entry
      try {
        await ElMessageBox.confirm(`确定要删除文档 "${doc.title}" 吗？此操作不可撤销。`, '删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        console.log('>>> Vue component: Calling apiDeleteDocument for ID:', doc.id); // Log before API call
        await apiDeleteDocument(doc.id) // MODIFIED: Use imported and renamed apiDeleteDocument
        
        ElMessage.success('文档删除成功')
        fetchDocuments()
        fetchCategories() // 更新分类文档计数
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除文档失败:', error)
          // 使用更安全的错误消息提取
          const errorMessage = error?.response?.data?.detail || error?.message || '未知错误';
          ElMessage.error('删除文档失败: ' + errorMessage);
        }
      }
    }
    
    // 获取文件图标
    const getFileIcon = (fileType) => {
      const extension = fileType ? fileType.toLowerCase() : '';
      const iconMap = {
        pdf: Document,
        doc: Document,
        docx: Document,
        xls: DataAnalysis,
        xlsx: DataAnalysis,
        ppt: Tickets,
        pptx: Tickets,
        png: PictureFilled,
        jpg: PictureFilled,
        jpeg: PictureFilled,
        gif: PictureFilled,
        svg: PictureFilled,
        img: PictureFilled,
        txt: Files,
        md: Files,
        other: Files
      };
      return iconMap[extension] || Files;
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    }
    
    // 格式化文件大小
    const formatFileSize = (sizeInKB) => {
      if (!sizeInKB) return '0 KB'
      
      if (sizeInKB < 1024) {
        return `${sizeInKB} KB`
      } else {
        return `${(sizeInKB / 1024).toFixed(2)} MB`
      }
    }
    
    // 获取标签列表
    const getTagsList = (tags) => {
      if (!tags) return []
      if (Array.isArray(tags)) return tags
      return tags.split(',').map(tag => tag.trim()).filter(tag => tag)
    }
    
    // 处理构建完成
    const handleBuildCompleted = () => {
      // 刷新文档列表
      fetchDocuments()
      fetchCategories()
      ElMessage.success('知识库构建完成，现在可以使用智能问答功能了！')
    }

    // 处理构建失败
    const handleBuildFailed = (error) => {
      console.error('知识库构建失败:', error)
      ElMessage.error('知识库构建失败，请检查日志或联系管理员')
    }
    
    // 格式化颜色值，确保不超过20个字符
    const formatColorValue = (color) => {
      if (color && color.length > 20) {
        // 如果是带透明度的颜色值(rgba)，则去除透明度，转为hex格式
        if (color.startsWith('rgba')) {
          const hexColor = color.replace(/rgba\((\d+),\s*(\d+),\s*(\d+),[^)]+\)/, (match, r, g, b) => {
            const toHex = (c) => {
              const hex = parseInt(c).toString(16);
              return hex.length === 1 ? '0' + hex : hex;
            };
            return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
          });
          categoryForm.color = hexColor.substring(0, 20);
        } else {
          // 如果是其他格式，直接截断
          categoryForm.color = color.substring(0, 20);
        }
        console.log(`颜色值已格式化: ${color} -> ${categoryForm.color}`);
      }
    };
    
    // 添加一个强制刷新函数
    const forceRefresh = async () => {
      console.log('强制刷新知识库组件');
      
      // 更新内部刷新标识，触发视图更新
      internalRefreshKey.value = Date.now();
      
      // 重置所有状态
      currentPage.value = 1;
      
      // 第一步：清除所有可能的DOM副作用
      try {
        // 清除所有浮层和遮罩
        const overlays = document.querySelectorAll('.el-overlay, .el-overlay-dialog, .el-overlay-message-box, .el-popup-parent--hidden');
        overlays.forEach(el => {
          if (el && el.parentNode) {
            try {
              el.parentNode.removeChild(el);
            } catch (e) {
              console.error('清理浮层元素失败:', e);
            }
          }
        });
        
        // 恢复body样式
        if (document && document.body) {
          document.body.style.overflow = '';
          document.body.classList.remove('el-popup-parent--hidden');
          document.body.style.pointerEvents = 'auto';
        }
        
        // 处理所有可能的下拉菜单
        const dropdowns = document.querySelectorAll('.el-dropdown-menu, .el-select-dropdown');
        dropdowns.forEach(el => {
          if (el && el.parentNode) {
            try {
              el.parentNode.removeChild(el);
            } catch (e) {
              console.error('清理下拉菜单失败:', e);
            }
          }
        });
      } catch (error) {
        console.error('清理DOM元素失败:', error);
      }
      
      // 第二步：重新绑定所有事件
      await nextTick();
      try {
        // 确保所有按钮和交互元素可点击
        const interactiveElements = document.querySelectorAll(
          '.knowledge-container button, ' +
          '.el-dropdown-menu__item, ' +
          '.document-item-card, ' +
          '.card-actions button, ' +
          '.card-footer button, ' +
          '.el-dropdown, ' +
          '.category-item'
        );
        
        interactiveElements.forEach(el => {
          if (el) {
            // 恢复所有交互元素的点击能力
            el.style.pointerEvents = 'auto';
            if (el.hasAttribute('disabled') && !el.classList.contains('is-disabled')) {
              el.removeAttribute('disabled');
            }
            
            // 为了确保事件能正确触发，我们尝试复制并替换元素
            // 这会清除旧的事件监听器并保持Vue的绑定
            try {
              const parent = el.parentNode;
              if (parent) {
                // 使用克隆节点的方式可能会丢失Vue的绑定，所以我们只重置样式
                el.style.opacity = '1';
                el.style.visibility = 'visible';
                el.style.display = '';
              }
            } catch (e) {
              console.error('重置元素样式失败:', e);
            }
          }
        });
        
        // 重置上传组件
        if (uploadRef.value) {
          uploadRef.value.clearFiles();
          uploadForm.file = null;
          uploadForm.title = '';
          uploadForm.description = '';
        }
        
        // 确保文档卡片可点击
        document.querySelectorAll('.document-item-card').forEach(card => {
          if (card) {
            card.style.pointerEvents = 'auto';
            card.style.cursor = 'pointer';
            // 重置z-index确保没有被覆盖
            card.style.zIndex = '1';
            card.style.position = 'relative';
          }
        });
        
        // 特别处理下拉菜单
        document.querySelectorAll('.el-dropdown').forEach(dropdown => {
          if (dropdown) {
            dropdown.style.pointerEvents = 'auto';
          }
        });
      } catch (error) {
        console.error('重置交互元素失败:', error);
      }
      
      // 第三步：强制重新获取数据
      try {
        console.log('重新加载所有数据...');
        loading.value = true;
        
        // 先获取分类数据
        await fetchCategories().catch(err => {
          console.error('强制刷新分类失败:', err);
          return [];
        });
        
        // 然后获取文档数据
        await fetchDocuments().catch(err => {
          console.error('强制刷新文档失败:', err);
          return [];
        });
        
        console.log('数据刷新完成');
      } catch (error) {
        console.error('强制刷新数据失败:', error);
      } finally {
        loading.value = false;
      }
      
      // 第四步：再次确保DOM更新完成后的交互性
      await nextTick();
      setTimeout(() => {
        try {
          // 最后一次确保所有元素可交互
          document.querySelectorAll('.knowledge-container button, .el-dropdown, .document-item-card').forEach(el => {
            if (el) {
              el.style.pointerEvents = 'auto';
            }
          });
        } catch (error) {
          console.error('最终DOM修复失败:', error);
        }
      }, 300);
    };
    
    // 监听路由变化，确保每次进入页面都刷新
    watch(() => route.fullPath, (newPath) => {
      if (newPath === '/knowledge') {
        console.log('检测到路由变化到知识库页面，强制刷新');
        // 延迟执行，确保DOM已经渲染
        setTimeout(() => {
          forceRefresh();
        }, 100);
      }
    });
    
    // 生命周期钩子
    onMounted(() => {
      console.log('Knowledge组件挂载');
      // 组件挂载时强制刷新
      forceRefresh();
      });
    
    // 添加keep-alive激活事件处理
    onActivated(() => {
      console.log('Knowledge组件被激活');
      // 组件激活时强制刷新
      forceRefresh();
    });
    
    onBeforeUnmount(() => {
      // 无需清除，因为没有设置轮询
      // if (pollingInterval) {
      //   clearInterval(pollingInterval)
      // }
    })
    
    // 标签页切换处理
    const handleTabChange = (tabName) => {
      activeTab.value = tabName
      if (tabName === 'documents' && documentManagementRef.value) {
        // 切换到文档管理时刷新数据
        nextTick(() => {
          if (documentManagementRef.value && documentManagementRef.value.refresh) {
            documentManagementRef.value.refresh()
          }
        })
      } else if (tabName === 'graph' && knowledgeGraphRef.value) {
        // 切换到知识图谱时刷新数据
        nextTick(() => {
          if (knowledgeGraphRef.value && knowledgeGraphRef.value.refresh) {
            knowledgeGraphRef.value.refresh()
          }
        })
      }
    }

    return {
      activeTab,
      documentManagementRef,
      knowledgeGraphRef,
      searchQuery,
      selectedCategory,
      categories,
      documents,
      filters,
      currentPage,
      pageSize,
      totalDocs,
      uploadVisible,
      uploadForm,
      uploadFormRef,
      uploadRef,
      uploadRules,
      uploading,
      loading,
      viewMode,
      sortOrder,
      showCategoryDialog,
      showAddCategoryForm,
      editingCategory,
      categoryForm,
      categoryLoading,
      showChunksDialog,
      selectedDocument,
      documentChunks,
      chunksLoading,
      isAdmin,
      currentCategoryName,
      processingCount,
      forceRefresh,
      internalRefreshKey,
      
      // 图标
      Search,
      Upload,
      FolderAdd,
      View,
      Download,
      More,
      Share,
      Edit,
      EditPen,
      FolderOpened,
      Star,
      Delete,
      Document,
      Files,
      Tickets,
      DataAnalysis,
      PictureFilled,
      UploadFilled,
      Loading,
      List,
      Grid,
      Crop,
      Plus,
      InfoFilled,
      Clock,
      User,
      Refresh,
      
      // 方法
      handleTabChange,
      selectCategory,
      handleSearch,
      applyFilters,
      getFileIcon,
      formatDate,
      formatFileSize,
      getTagsList,
      previewDocument,
      downloadDocument,
      shareDocument,
      editDocument,
      handleUpdateDocument,
      handleCloseEditDialog,
      handleCancelEditDialog,
      deleteDocument,
      handleFileChange,
      handleRemove,
      beforeUpload,
      handleUploadError,
      submitUpload,
      handlePageChange,
      handleSizeChange,
      showDocumentChunks,
      editCategory,
      handleDeleteCategory,
      saveCategoryForm,
      cancelCategoryForm,
      resetCategoryForm,
      buildingVisible,
      handleBuildCompleted,
      handleBuildFailed,
      resetUploadForm,
      handleCloseUploadDialog,
      openUploadDialog,
      handleCancelUpload,
      formatColorValue,
      editDialogVisible,
      editForm
    }
  }
}
</script>

<style lang="scss" scoped>
.knowledge-container {
  padding: 20px;
  height: 100%;
  width: 100%;
  background-color: var(--el-bg-color-page) !important;
}

.knowledge-tabs {
  margin-bottom: 20px;
  
  .tab-label {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      font-size: 16px;
    }
  }
  
  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }
  
  :deep(.el-tabs__nav-wrap::after) {
    background-color: var(--el-border-color-light);
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: var(--el-color-primary);
  }
  
  :deep(.el-tabs__item) {
    color: var(--el-text-color-regular);
    font-weight: 500;
    
    &.is-active {
      color: var(--el-color-primary);
      font-weight: 600;
    }
    
    &:hover {
      color: var(--el-color-primary);
    }
  }
}

/* 确保所有交互元素可点击 */
.knowledge-container button,
.knowledge-container .el-dropdown,
.knowledge-container .document-item-card,
.knowledge-container .category-item {
  pointer-events: auto !important;
  cursor: pointer !important;
}

/* 强制知识库页面的所有元素使用深色背景 */
.knowledge-container .row,
.knowledge-container .col-lg-3,
.knowledge-container .col-lg-9,
.knowledge-container .page-header,
.knowledge-container .document-grid {
  background-color: var(--el-bg-color-page) !important;
}

/* 确保下拉菜单项可点击 */
:deep(.el-dropdown-menu__item) {
  pointer-events: auto !important;
  cursor: pointer !important;
}

.row {
  display: flex;
  gap: 20px;
}

.col-lg-3 {
  flex: 0 0 280px;
  width: 280px;
}

.col-lg-9 {
  flex: 1;
  min-width: 0;
}

.category-card {
  border: none;
  border-radius: 8px;
  padding: 16px;
  background-color: var(--el-bg-color);
  height: 100%;
}

.search-box {
  margin-bottom: 20px;
}

.category-list .category-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  border-radius: 6px;
  margin-bottom: 5px;
  transition: background-color 0.2s ease-in-out;
  
  &.active {
    background-color: var(--el-color-primary-light-9);
    .category-name {
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }
  
  &:hover {
    background-color: var(--el-fill-color-light);
  }
  
  .category-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    .el-icon {
      color: white !important;
    }
  }

  .category-name {
    flex-grow: 1;
    font-weight: 500;
  }

  .category-count {
    font-size: 12px;
    color: #909399;
    background-color: #e9e9eb;
    padding: 2px 6px;
    border-radius: 10px;
  }
}

.add-category-btn {
  width: 100%;
  margin-top: 10px;
}

.filter-section {
  margin-top: 20px;
  h6 {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-bottom: 10px;
  }
  .filter-group {
    margin-bottom: 15px;
  }
  .filter-options {
    display: flex;
    flex-direction: column;
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  .page-title {
    font-size: 28px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  .header-actions {
  display: flex;
    gap: 12px;
  }
}

.document-container-card {
  border: none;
  border-radius: 8px;
  background-color: var(--el-bg-color-overlay);
  padding: 24px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  .empty-icon {
    font-size: 64px;
    color: var(--el-text-color-placeholder);
    margin-bottom: 20px;
}
  .empty-title {
    font-size: 20px;
    color: var(--el-text-color-primary);
  margin-bottom: 10px;
}
  .empty-description {
  color: var(--el-text-color-secondary);
  margin-bottom: 20px;
}
}

.document-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.document-item-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.3s ease;
  background-color: var(--el-bg-color-overlay);

  &:hover {
    transform: translateY(-5px);
    box-shadow: var(--el-box-shadow-light);
}

  .card-header {
  display: flex;
  align-items: center;
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
}

  .file-icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
    font-size: 20px;
    color: #fff;

    &.file-icon-pdf { background-color: #f56c6c; }
    &.file-icon-doc, &.file-icon-docx { background-color: #409eff; }
    &.file-icon-xls, &.file-icon-xlsx { background-color: #67c23a; }
    &.file-icon-ppt, &.file-icon-pptx { background-color: #e6a23c; }
    &.file-icon-img, &.file-icon-jpg, &.file-icon-jpeg, &.file-icon-png, &.file-icon-gif, &.file-icon-svg { background-color: #909399; }
    &.file-icon-txt, &.file-icon-md { background-color: #b1b3b8; }
}

  .document-title-block {
    flex-grow: 1;
    overflow: hidden;
}

  .document-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;  
  overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
}

  .file-extension {
    font-weight: 400;
    color: var(--el-text-color-placeholder);
    font-size: 14px;
    margin-left: 2px;
}

  .card-body {
    padding: 16px;
    flex-grow: 1;
    min-height: 85px;
  }
  
  .document-description {
    font-size: 14px;
    color: var(--el-text-color-regular);
  line-height: 1.6;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;  
    overflow: hidden;
    text-overflow: ellipsis;
}

  .card-footer {
    margin-top: auto;
    border-top: 1px solid var(--el-border-color-lighter);
    padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
    background-color: var(--el-fill-color-lighter);
}

  .document-meta {
    font-size: 13px;
    color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
    gap: 6px;
}

  .card-actions {
  display: flex;
  align-items: center;
    gap: 4px;
  }
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  :deep(.el-pagination.is-background .el-pager li) {
    background-color: var(--el-fill-color);
  }
   :deep(.el-pagination.is-background .el-pager li:not(.is-disabled):hover) {
    color: var(--el-color-primary);
  }
  :deep(.el-pagination.is-background .btn-next),
  :deep(.el-pagination.is-background .btn-prev) {
    background-color: var(--el-fill-color);
  }
}

.category-dialog-content {
  display: flex;
  gap: 24px;

  .category-list-section {
    flex: 2;
    border-right: 1px solid var(--el-border-color-light);
    padding-right: 24px;
    min-width: 0;
  }

  .category-form-section {
    flex: 3;
    min-width: 0;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h5 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
  }

  .category-items {
    max-height: 400px;
    overflow-y: auto;
    padding-right: 8px; /* for scrollbar */
  }

  .category-list-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 8px;
    border-radius: 6px;
    margin-bottom: 8px;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    .category-info {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-grow: 1;
      min-width: 0;

      .category-color {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
      }

      .category-name-section {
        flex-grow: 1;
        min-width: 0;

        .category-name {
          font-weight: 500;
          color: var(--el-text-color-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          display: block; // Ensures it takes its own line
        }

        .category-desc {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          display: block; // Ensures it takes its own line
        }
      }
    }
    
    .category-details {
        display: flex;
        align-items: center;
        gap: 16px;
        flex-shrink: 0;
        margin-left: 16px;
    }

    .category-count {
      font-size: 13px;
      color: var(--el-text-color-regular);
      white-space: nowrap;
      flex-shrink: 0;
    }

    .category-actions {
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
  }

  .empty-categories {
    text-align: center;
    padding: 20px;
  }
}

.category-form-section .el-form {
  margin-top: 10px;
}

/* 分页容器样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color);
}

// ===========================================
// 深色模式
// ===========================================
:deep(.dark .knowledge-container) {
  background-color: #141414;
}
:deep(.dark .page-header .page-title) {
  color: #ffffff;
}
:deep(.dark .document-container-card) {
  background-color: #1d1d1d;
  border-color: #424242;
}
:deep(.dark .document-item-card) {
  background-color: #262626;
  border-color: #424242;
  &:hover {
    border-color: #589ef8;
  }
}
:deep(.dark .document-title) {
  color: #e0e0e0;
}
:deep(.dark .file-extension) {
  color: #8c8c8c;
}
:deep(.dark .document-description) {
  color: #a6a6a6;
}
:deep(.dark .card-footer) {
  background-color: #2c2c2c;
  border-top-color: #424242;
}
:deep(.dark .document-meta) {
  color: #8c8c8c;
}
:deep(.dark .category-card) {
  background-color: #1d1d1d;
  border-color: #424242;
}
:deep(.dark .category-name) {
  color: #e0e0e0;
}
:deep(.dark .category-count) {
  color: #8c8c8c;
}
:deep(.dark .filter-section h6) {
  color: #e0e0e0;
}
:deep(.dark .el-checkbox__label) {
  color: #a6a6a6;
}
:deep(.dark .el-checkbox__input .el-checkbox__inner) {
  background-color: #333;
  border-color: #555;
}
:deep(.dark .category-item.active) {
  background-color: #2c2c2c;
}
:deep(.dark .category-item:hover) {
  background-color: #262626;
}
</style>
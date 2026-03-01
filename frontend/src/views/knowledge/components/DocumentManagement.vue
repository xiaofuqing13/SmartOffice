<template>
  <div class="document-management">
    <div class="row">
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { 
  Search, 
  Refresh, 
  InfoFilled, 
  Clock, 
  Download,
  Document as DocumentIcon,
  Folder,
  FolderOpened,
  Files,
  Picture,
  VideoPlay,
  Reading
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getCategories, getDocuments, downloadDocumentFile } from '@/api/knowledge'

// 响应式数据
const searchQuery = ref('')
const selectedCategory = ref('all')
const documents = ref([])
const categories = ref([])
const totalDocs = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const loading = ref(false)

// 筛选条件
const filters = reactive({
  types: {
    pdf: false,
    doc: false,
    xls: false,
    ppt: false,
    img: false,
    txt: false,
    md: false
  }
})

// 计算属性
const currentCategoryName = computed(() => {
  const category = categories.value.find(cat => cat.id === selectedCategory.value)
  return category ? category.name : '全部文档'
})

// 方法
const handleSearch = () => {
  currentPage.value = 1
  loadDocuments()
}

const selectCategory = (categoryId) => {
  selectedCategory.value = categoryId
  currentPage.value = 1
  loadDocuments()
}

const applyFilters = () => {
  currentPage.value = 1
  loadDocuments()
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadDocuments()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadDocuments()
}

const forceRefresh = () => {
  loadCategories()
  loadDocuments()
}

const getFileIcon = (fileType) => {
  const iconMap = {
    pdf: Reading,
    doc: DocumentIcon,
    docx: DocumentIcon,
    xls: Files,
    xlsx: Files,
    ppt: VideoPlay,
    pptx: VideoPlay,
    jpg: Picture,
    jpeg: Picture,
    png: Picture,
    gif: Picture,
    txt: DocumentIcon,
    md: DocumentIcon
  }
  return iconMap[fileType] || DocumentIcon
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const downloadDocument = async (doc) => {
  try {
    const response = await downloadDocumentFile(doc.id)
    
    // 根据文件类型设置正确的MIME类型
    const getMimeType = (fileType) => {
      const mimeTypes = {
        pdf: 'application/pdf',
        doc: 'application/msword',
        docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        xls: 'application/vnd.ms-excel',
        xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ppt: 'application/vnd.ms-powerpoint',
        pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        png: 'image/png',
        gif: 'image/gif',
        txt: 'text/plain',
        md: 'text/markdown'
      }
      return mimeTypes[fileType] || 'application/octet-stream'
    }
    
    // 确保文件名包含正确的扩展名
    const getFileName = (doc) => {
      let fileName = doc.filename || doc.title || 'document'
      
      // 如果文件名已经包含扩展名，直接使用
      if (fileName.includes('.')) {
        return fileName
      }
      
      // 如果没有扩展名，添加文件类型作为扩展名
      if (doc.file_type) {
        return `${fileName}.${doc.file_type}`
      }
      
      return fileName
    }
    
    const mimeType = getMimeType(doc.file_type)
    const fileName = getFileName(doc)
    
    const url = window.URL.createObjectURL(new Blob([response], { type: mimeType }))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(`文档 "${fileName}" 下载成功`)
  } catch (error) {
    console.error('下载文档失败:', error)
    ElMessage.error('下载文档失败')
  }
}

const loadCategories = async () => {
  try {
    const response = await getCategories()
    categories.value = [
      {
        id: 'all',
        name: '全部文档',
        icon: Folder,
        color: '#409EFF',
        document_count: response.reduce((sum, cat) => sum + (cat.document_count || 0), 0)
      },
      ...response.map(cat => ({
        ...cat,
        icon: FolderOpened,
        color: cat.color || '#67C23A'
      }))
    ]
  } catch (error) {
    console.error('加载分类失败:', error)
    ElMessage.error('加载分类失败')
  }
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value
    }
    
    if (selectedCategory.value !== 'all') {
      params.category = selectedCategory.value
    }
    
    // 添加文件类型筛选
    const selectedTypes = Object.keys(filters.types).filter(type => filters.types[type])
    if (selectedTypes.length > 0) {
      params.file_types = selectedTypes.join(',')
    }
    
    const response = await getDocuments(params)
    documents.value = response.results
    totalDocs.value = response.count
  } catch (error) {
    console.error('加载文档失败:', error)
    ElMessage.error('加载文档失败')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  // 检查用户登录状态
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')
  console.log('当前token状态:', token ? '已存在' : '不存在')
  console.log('当前用户状态:', user ? JSON.parse(user) : '未登录')
  
  if (!token) {
    ElMessage.error('请先登录后再访问知识库')
    return
  }
  
  loadCategories()
  loadDocuments()
})

// 暴露方法给父组件
defineExpose({
  refresh: forceRefresh
})
</script>

<style scoped>
.document-management {
  width: 100%;
}

.category-card {
  height: fit-content;
  margin-bottom: 20px;
}

.search-box {
  margin-bottom: 20px;
}

.category-list {
  margin-bottom: 20px;
}

.category-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.category-item:hover {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
}

.category-item.active {
  background-color: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.category-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.category-name {
  flex: 1;
  font-weight: 500;
}

.category-count {
  background-color: #f0f2f5;
  color: #606266;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.filter-section {
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.filter-section h6 {
  margin: 0 0 12px 0;
  font-weight: 600;
  color: #303133;
}

.filter-group {
  margin-bottom: 16px;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.document-container-card {
  min-height: 500px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-title {
  margin: 0;
  font-weight: 500;
}

.document-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.document-item-card {
  height: 200px;
  transition: all 0.3s ease;
}

.document-item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f2f5;
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 20px;
  color: white;
}

.file-icon-pdf { background-color: #f56565; }
.file-icon-doc, .file-icon-docx { background-color: #4299e1; }
.file-icon-xls, .file-icon-xlsx { background-color: #48bb78; }
.file-icon-ppt, .file-icon-pptx { background-color: #ed8936; }
.file-icon-jpg, .file-icon-jpeg, .file-icon-png, .file-icon-gif { background-color: #9f7aea; }
.file-icon-txt, .file-icon-md { background-color: #718096; }

.document-title-block {
  flex: 1;
  min-width: 0;
}

.document-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-extension {
  color: #909399;
  font-weight: 400;
}

.card-body {
  padding: 16px;
  flex: 1;
  display: flex;
  align-items: center;
}

.document-description {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  padding: 12px 16px;
  border-top: 1px solid #f0f2f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.document-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}
</style>
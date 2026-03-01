<template>
  <div class="module-card">
    <div class="module-header">
      <h5 class="module-title">文档管理</h5>
      <div class="btn-group">
        <el-button type="primary" size="default" round @click="uploadDialogVisible = true">上传文档</el-button>
        <el-dialog v-model="uploadDialogVisible" title="上传文档" width="400px">
          <el-form :model="uploadForm" label-width="80px" :rules="formRules" ref="uploadFormRef">
            <el-form-item label="文档名称" prop="name" required>
              <el-input v-model="uploadForm.name" placeholder="请输入文档名称" />
            </el-form-item>
            <el-form-item label="描述" prop="desc" required>
              <el-input v-model="uploadForm.desc" placeholder="请输入文档描述" />
            </el-form-item>
            <el-form-item label="标签" prop="tags" required>
              <el-input v-model="uploadForm.tags" placeholder="多个标签用逗号分隔" />
            </el-form-item>
            <el-form-item label="文件" prop="file" required>
              <el-upload
                :auto-upload="false"
                :show-file-list="true"
                :on-change="handleFileChange"
                :file-list="fileList"
              >
                <el-button>选择文件</el-button>
              </el-upload>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="uploadDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
          </template>
        </el-dialog>
      </div>
    </div>
    <!-- AI文档分析 -->
    <div class="ai-document-analysis mb-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h6 class="mb-0">AI文档分析</h6>
        <div class="btn-group">
          <el-button size="small" @click="fetchAiDocDashboard" :loading="aiDocLoading">
            <el-icon><Refresh /></el-icon>刷新分析
          </el-button>
        </div>
      </div>
      <div class="row">
        <div class="col-md-4">
          <div class="ai-analysis-card">
            <h6 class="text-primary">文档健康度</h6>
            <el-progress :percentage="aiDocDashboard.health_score" :status="aiDocDashboard.health_score>=80?'success':(aiDocDashboard.health_score>=60?'warning':'exception')" style="margin-bottom:8px;" />
            <p class="text-muted small">{{ aiDocDashboard.health_desc }}</p>
          </div>
        </div>
        <div class="col-md-4">
          <div class="ai-analysis-card">
            <h6 class="text-primary">文档关联性</h6>
            <div class="document-relations">
              <div class="relation-item">
                <el-icon><Link /></el-icon>
                发现{{ aiDocDashboard.related_count }}个相关文档
              </div>
              <div class="relation-item">
                <el-icon><CircleCloseFilled /></el-icon>
                {{ aiDocDashboard.conflict_count }}个文档存在版本冲突
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="ai-analysis-card">
            <h6 class="text-primary">智能建议</h6>
            <div class="ai-suggestions">
              <div v-if="!aiDocDashboard.suggestions.length" class="text-center py-2">
                <span class="text-muted">暂无建议</span>
              </div>
              <div class="suggestion-item" v-for="(suggestion, i) in aiDocDashboard.suggestions" :key="i" v-html="formatMarkdown(suggestion)">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 筛选区 -->
    <div class="filter-bar" style="display:flex;gap:12px;margin-bottom:16px;">
      <el-input v-model="filterKeyword" placeholder="文档名/描述" clearable style="width:180px;" />
      <el-select v-model="filterTag" placeholder="标签" clearable style="width:120px;">
        <el-option label="全部" value="" />
        <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
      </el-select>
    </div>
    <!-- 文档列表 -->
    <div class="document-list">
      <div class="list-group">
        <div class="list-group-item list-group-item-action" v-for="doc in filteredDocs" :key="doc.name">
          <div class="d-flex w-100 justify-content-between">
            <div>
              <h6 class="mb-1">{{ doc.name }}</h6>
              <div class="ai-document-tags">
                <el-tag v-for="tag in doc.tags" :key="tag.text" :type="tag.type" size="small">{{ tag.text }}</el-tag>
              </div>
            </div>
            <div class="text-end">
              <small>{{ doc.time }}</small>
              <el-button v-if="doc.file" type="success" size="small" @click="downloadFile(doc.file, doc.name)" style="margin-left:8px;">下载</el-button>
              <el-button type="primary" size="small" @click="openEditDialog(doc)" style="margin-left:8px;">编辑</el-button>
              <el-button type="info" size="small" @click="analyzeDocument(doc)" style="margin-left:8px;" :loading="doc.analyzing">AI分析</el-button>
              <el-button type="danger" size="small" @click="confirmDelete(doc)" style="margin-left:8px;">删除</el-button>
            </div>
          </div>
          <p class="mb-1">{{ doc.desc }}</p>
          <div class="ai-document-analysis" v-if="doc.analysis">
            <div class="d-flex justify-content-between">
              <small class="text-muted">AI分析：</small>
              <el-button type="link" size="small" @click="doc.showFullAnalysis = !doc.showFullAnalysis">
                {{ doc.showFullAnalysis ? '收起' : '展开' }}
              </el-button>
            </div>
            <div v-if="doc.showFullAnalysis" v-html="formatMarkdown(doc.analysis)"></div>
            <div v-else v-html="formatMarkdown(doc.analysis.substring(0, 100) + (doc.analysis.length > 100 ? '...' : ''))"></div>
          </div>
          <div class="ai-document-analysis" v-else>
            <small class="text-muted">暂无AI分析</small>
          </div>
        </div>
      </div>
    </div>
    <el-dialog v-model="editDialogVisible" title="编辑文档信息" width="400px">
      <el-form :model="editForm" label-width="80px" :rules="formRules" ref="editFormRef">
        <el-form-item label="文档名称" prop="name" required>
          <el-input v-model="editForm.name" placeholder="请输入文档名称" />
        </el-form-item>
        <el-form-item label="描述" prop="desc" required>
          <el-input v-model="editForm.desc" placeholder="请输入文档描述" />
        </el-form-item>
        <el-form-item label="标签" prop="tags" required>
          <el-input v-model="editForm.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { Link, CircleCloseFilled, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchProjectDocuments, uploadProjectDocument, updateProjectDocument, deleteProjectDocument, getDocumentAiDashboard } from '@/api/project'
import axios from 'axios'
import request from '@/utils/request'
import { marked } from 'marked'

const props = defineProps({
  project: { type: Object, required: true }
})

const docs = ref([])
const loading = ref(false)
const uploadDialogVisible = ref(false)
const uploadForm = ref({
  name: '',
  desc: '',
  tags: '',
  file: null
})
const fileList = ref([])
const uploading = ref(false)
const editDialogVisible = ref(false)
const editForm = ref({ id: '', name: '', desc: '', tags: '' })
const editLoading = ref(false)
const aiDocDashboard = ref({
  health_score: 0,
  health_desc: '',
  related_count: 0,
  conflict_count: 0,
  suggestions: []
})
const aiDocLoading = ref(false)
const filterKeyword = ref('')
const filterTag = ref('')
const allTags = computed(() => {
  // 汇总所有文档的标签
  const tagsSet = new Set()
  docs.value.forEach(doc => {
    (doc.tags || []).forEach(t => tagsSet.add(t.text))
  })
  return Array.from(tagsSet)
})
const filteredDocs = computed(() => {
  return docs.value.filter(doc => {
    const matchKeyword = !filterKeyword.value || doc.name.includes(filterKeyword.value) || (doc.desc && doc.desc.includes(filterKeyword.value))
    const matchTag = !filterTag.value || (doc.tags && doc.tags.some(t => t.text === filterTag.value))
    return matchKeyword && matchTag
  })
})

const formatMarkdown = (text) => {
  if (!text) return '';
  return marked(text);
}

// 获取后端baseURL
const BASE_URL = 'http://localhost:8000'

function loadDocuments() {
  if (!props.project?.id) return
  loading.value = true
  fetchProjectDocuments(props.project.id).then(res => {
    docs.value = (res.data || []).map(doc => ({
      id: doc.id,
      name: doc.name,
      tags: (doc.tags || '').split(',').filter(Boolean).map(t => ({ text: t, type: 'info' })),
      time: doc.uploaded_at ? doc.uploaded_at.slice(0, 10) : '',
      desc: doc.desc,
      analysis: doc.analysis,
      file: doc.file,
      analyzing: false,
      showFullAnalysis: false
    }))
    // 自动AI分析
    docs.value.forEach(doc => {
      if (!doc.analysis) {
        analyzeDocument(doc)
      }
    })
  }).finally(() => loading.value = false)
}

function fetchAiDocDashboard() {
  if (!props.project?.id) return
  aiDocLoading.value = true
  getDocumentAiDashboard(props.project.id).then(res => {
    aiDocDashboard.value = res.data || {
      health_score: 0,
      health_desc: '',
      related_count: 0,
      conflict_count: 0,
      suggestions: []
    }
  }).finally(() => aiDocLoading.value = false)
}

onMounted(() => {
  loadDocuments()
  fetchAiDocDashboard()
})

watch(() => props.project?.id, (val) => {
  if (val) {
    loadDocuments()
    fetchAiDocDashboard()
  }
})

// 监听文档列表变化，重新获取AI分析
watch(docs, () => {
  fetchAiDocDashboard()
}, { deep: true })

// 上传成功回调
function handleUploadSuccess() {
  ElMessage.success('文档上传成功！')
  loadDocuments()
}

// 上传失败回调
function handleUploadError() {
  ElMessage.error('文档上传失败，请重试')
}

function handleFileChange(file) {
  uploadForm.value.file = file.raw
  fileList.value = [file]
}

function submitUpload() {
  if (!uploadFormRef.value) {
    console.error('表单引用不存在')
    return
  }
  
  uploadFormRef.value.validate(valid => {
    if (!valid) {
      ElMessage.error('请填写所有必填项')
      return
    }
    
    if (!uploadForm.value.file) {
      ElMessage.warning('请先选择文件')
      return
    }
    
    uploading.value = true
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('project', props.project.id)
    formData.append('name', uploadForm.value.name || uploadForm.value.file.name)
    formData.append('desc', uploadForm.value.desc)
    formData.append('tags', uploadForm.value.tags)
    
    uploadProjectDocument(formData).then(() => {
      handleUploadSuccess()
      uploadDialogVisible.value = false
      uploadForm.value = { name: '', desc: '', tags: '', file: null }
      fileList.value = []
    }).catch(() => {
      handleUploadError()
    }).finally(() => {
      uploading.value = false
    })
  })
}

function downloadFile(url, name) {
  let downloadUrl = url
  if (!/^https?:\/\//.test(url)) {
    downloadUrl = BASE_URL + url
  }
  axios({
    url: downloadUrl,
    method: 'get',
    responseType: 'blob',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token') || ''}`
    }
  }).then(res => {
    const blob = new Blob([res.data])
    // 优先用文档名称+原文件后缀
    let ext = ''
    const urlFilename = url.split('/').pop() || ''
    const idx = urlFilename.lastIndexOf('.')
    if (idx !== -1) ext = urlFilename.slice(idx)
    let filename = (name || 'download') + ext
    // 兼容Content-Disposition
    const disposition = res.headers['content-disposition']
    if (disposition) {
      const match = disposition.match(/filename="?([^"]+)"?/)
      if (match) filename = decodeURIComponent(match[1])
    }
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href)
  }).catch(() => {
    ElMessage.error('下载失败，请检查网络或权限')
  })
}

function openEditDialog(doc) {
  editForm.value = {
    id: doc.id,
    name: doc.name,
    desc: doc.desc,
    tags: (doc.tags || []).map(t => t.text).join(',')
  }
  editDialogVisible.value = true
}

function submitEdit() {
  if (!editFormRef.value) {
    console.error('表单引用不存在')
    return
  }
  
  editFormRef.value.validate(valid => {
    if (!valid) {
      ElMessage.error('请填写所有必填项')
      return
    }
    
    editLoading.value = true
    updateProjectDocument(editForm.value.id, {
      name: editForm.value.name,
      desc: editForm.value.desc,
      tags: editForm.value.tags
    }).then(() => {
      ElMessage.success('文档信息已更新')
      editDialogVisible.value = false
      loadDocuments()
    }).catch(() => {
      ElMessage.error('更新失败')
    }).finally(() => {
      editLoading.value = false
    })
  })
}

function confirmDelete(doc) {
  ElMessageBox.confirm('确定要删除该文档吗？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    deleteProjectDocument(doc.id).then(() => {
      ElMessage.success('文档已删除')
      loadDocuments()
    }).catch(() => {
      ElMessage.error('删除失败')
    })
  }).catch(() => {})
}

// 添加分析文档的功能
function analyzeDocument(doc) {
  // 检查文档ID
  const idNum = Number(doc.id)
  if (!idNum || isNaN(idNum) || idNum <= 0 || !Number.isInteger(idNum)) {
    ElMessage.warning('无效的文档ID')
    return
  }
  
  // 设置分析状态
  doc.analyzing = true
  
  // 调用AI分析接口
  request
    .post(`/api/project-documents/${doc.id}/ai_analyze/`)
    .then(response => {
      const analysis = response.data.analysis
      // 更新文档分析结果
      doc.analysis = analysis
      doc.showFullAnalysis = false
      ElMessage.success('AI分析完成')
    })
    .catch(error => {
      console.error('文档AI分析失败:', error)
      ElMessage.error('文档AI分析失败')
    })
    .finally(() => {
      doc.analyzing = false
    })
}

// 表单引用
const uploadFormRef = ref(null)
const editFormRef = ref(null)

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入文档名称', trigger: 'blur' }],
  desc: [{ required: true, message: '请输入文档描述', trigger: 'blur' }],
  tags: [{ required: true, message: '请输入标签', trigger: 'blur' }],
  file: [{ required: true, message: '请选择文件', trigger: 'change' }]
}
</script>
<style scoped>
.module-card { background: var(--bg-color-secondary); border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; padding: 20px; }
.module-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.module-title { font-size: 1.1rem; font-weight: 600; color: var(--text-color) !important; margin: 0; }
.btn-group { display: flex; gap: 10px; }
.row { display: flex; flex-wrap: wrap; margin: 0 -10px; }
.col-md-4 { padding: 0 10px; width: 33.3333%; }
.mb-4 { margin-bottom: 24px; }
.list-group { margin: 0; }
.list-group-item { background: var(--bg-color-tertiary); border: none; border-radius: 5px; margin-bottom: 10px; padding: 16px; }
.ai-analysis-card { background: var(--bg-color-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; margin-bottom: 15px; }
.relation-item, .suggestion-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.text-primary { color: var(--primary-color)!important; }
.ai-document-analysis {
  background: var(--bg-color-tertiary);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  color: var(--text-color);
}
.ai-document-analysis .text-muted,
.ai-document-analysis small {
  color: var(--text-color-tertiary) !important;
}

/* 深色模式下 Element Plus 组件适配 */
:deep(.el-tag) {
  background: var(--bg-color-tertiary) !important;
  color: var(--text-color) !important;
  border-color: var(--border-color) !important;
}
:deep(.el-badge__content) {
  background: var(--primary-color) !important;
  color: #fff !important;
}
:deep(.el-empty) {
  background: transparent !important;
  color: var(--text-color-tertiary) !important;
}
:deep(.el-progress-bar__outer) {
  background: var(--bg-color-tertiary) !important;
}
:deep(.el-progress-bar__inner) {
  background: var(--primary-color) !important;
}
.el-dialog,
.el-dialog .el-dialog__body,
.el-dialog .el-dialog__footer {
  background: var(--bg-color-secondary);
  color: var(--text-color);
}
.list-group-item:hover {
  background: var(--hover-color);
  color: var(--primary-color);
}
</style>

<style lang="scss">
[data-theme="dark"] {
  .module-card, .ai-analysis-card, .list-group-item, .el-dialog {
    background-color: var(--el-bg-color-page) !important;
    color: var(--el-text-color-primary) !important;
    border: 1px solid var(--el-border-color-light) !important;
  }

  .module-title, h6, .el-dialog__title {
    color: var(--el-text-color-primary) !important;
  }

  .text-muted, .small, .ai-document-analysis small.text-muted {
    color: var(--el-text-color-secondary) !important;
  }
  
  .el-form-item__label {
    color: var(--el-text-color-secondary) !important;
  }

  .el-input__wrapper {
    background-color: var(--el-fill-color-light) !important;
    border-color: var(--el-border-color) !important;
  }

  .list-group-item-action:hover {
    background-color: var(--el-fill-color-light) !important;
  }
}
</style> 
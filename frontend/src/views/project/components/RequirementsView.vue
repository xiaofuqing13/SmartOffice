<template>
  <div class="module-card">
    <div class="module-header">
      <h5 class="module-title">需求管理</h5>
      <div class="btn-group">
        <el-button type="primary" size="default" round @click="showAddReq=true">新建需求</el-button>
      </div>
    </div>
    <!-- AI需求分析 -->
    <div class="ai-requirement-analysis mb-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h6 class="mb-0">AI需求分析</h6>
        <div class="btn-group">
          <el-button size="small" @click="fetchAiAnalysis" :loading="aiAnalysisLoading">
            <el-icon><Refresh /></el-icon>刷新分析
          </el-button>
        </div>
      </div>
      <div class="row">
        <div class="col-md-4">
          <div class="ai-analysis-card">
            <h6 class="text-primary">需求完整性</h6>
            <el-progress :percentage="aiAnalysis.completeness" :status="getCompletenessStatus(aiAnalysis.completeness)" style="margin-bottom:8px;" />
            <p class="text-muted small">需求描述完整性评分</p>
          </div>
        </div>
        <div class="col-md-4">
          <div class="ai-analysis-card">
            <h6 class="text-primary">需求依赖关系</h6>
            <div class="requirement-dependencies">
              <div class="dependency-item">
                <el-icon><Connection /></el-icon>
                发现{{aiAnalysis.dependencies}}个需求依赖关系
              </div>
              <div class="dependency-item">
                <el-icon><CircleCloseFilled /></el-icon>
                {{aiAnalysis.conflicts}}个需求存在冲突
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="ai-analysis-card">
            <h6 class="text-primary">智能建议</h6>
            <div class="ai-suggestions">
              <div v-if="aiAnalysis.suggestions.length === 0" class="text-center py-2">
                <!-- 不显示任何内容 -->
              </div>
              <div class="suggestion-item" v-for="(suggestion, i) in aiAnalysis.suggestions" :key="i">
                <el-icon><Lightning v-if="i === 0" /><Check v-else /></el-icon>
                {{suggestion}}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 筛选区 -->
    <div class="filter-bar" style="display:flex;gap:12px;margin-bottom:16px;">
      <el-select v-model="filterPriority" placeholder="优先级" clearable style="width:120px;">
        <el-option label="全部" value="" />
        <el-option label="高" value="high" />
        <el-option label="中" value="medium" />
        <el-option label="低" value="low" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px;">
        <el-option label="全部" value="" />
        <el-option label="待处理" value="pending" />
        <el-option label="进行中" value="in-progress" />
        <el-option label="已完成" value="completed" />
      </el-select>
      <el-input v-model="filterKeyword" placeholder="关键词" clearable style="width:180px;" />
    </div>
    <!-- 需求列表 -->
    <div v-loading="loading" class="requirements-list">
      <div class="list-group">
        <div class="list-group-item list-group-item-action" v-for="req in filteredRequirements" :key="req.id">
          <div class="d-flex w-100 justify-content-between">
            <div>
              <h6 class="mb-1">{{ req.name }}</h6>
              <div class="ai-requirement-tags">
                <el-tag v-for="tag in req.tags_list" :key="tag.text" :type="tag.type" size="small">{{ tag.text }}</el-tag>
              </div>
            </div>
            <div class="text-end">
              <el-tag :type="getStatusType(req.status)" size="small">{{ getStatusText(req.status) }}</el-tag>
              <div class="ai-requirement-status">
                <small class="text-muted">{{ formatDate(req.created_at) }}</small>
              </div>
              <div style="margin-top: 8px;">
                <el-button size="small" type="primary" text @click="openEditReq(req)">编辑</el-button>
                <el-button size="small" type="danger" text @click="handleDeleteReq(req)">删除</el-button>
                <el-button size="small" type="info" text @click="analyzeRequirement(req, true)" :loading="req.analyzing">AI分析</el-button>
              </div>
            </div>
          </div>
          <p class="mb-1">{{ req.description || '暂无描述' }}</p>
          <div class="ai-requirement-analysis" v-if="req.ai_analysis">
            <div class="d-flex justify-content-between">
              <small class="text-muted">AI分析：</small>
              <el-button type="link" size="small" @click="req.showFullAnalysis = !req.showFullAnalysis">
                {{ req.showFullAnalysis ? '收起' : '展开' }}
              </el-button>
            </div>
            <div v-if="req.showFullAnalysis">{{ req.ai_analysis }}</div>
            <div v-else>{{ req.ai_analysis.substring(0, 100) }}{{ req.ai_analysis.length > 100 ? '...' : '' }}</div>
          </div>
          <div class="ai-requirement-analysis" v-else>
            <small class="text-muted">暂无AI分析</small>
          </div>
        </div>
      </div>
      <el-empty v-if="requirements.length === 0" description="暂无需求数据" />
    </div>
  </div>
  <!-- 新建/编辑需求弹窗 -->
  <el-dialog v-model="showAddReq" :title="editMode ? '编辑需求' : '新建需求'" width="400px">
    <el-form :model="addReqForm" label-width="80px" :rules="formRules" ref="reqFormRef">
      <el-form-item label="需求名称" prop="name" required>
        <el-input v-model="addReqForm.name" placeholder="请输入需求名称" />
      </el-form-item>
      <el-form-item label="优先级" prop="priority" required>
        <el-select v-model="addReqForm.priority" placeholder="请选择">
          <el-option label="高" value="high" />
          <el-option label="中" value="medium" />
          <el-option label="低" value="low" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签" prop="tags" required>
        <el-input v-model="addReqForm.tags" placeholder="逗号分隔，如：功能,高优先级" />
      </el-form-item>
      <el-form-item label="描述" prop="description" required>
        <el-input v-model="addReqForm.description" type="textarea" placeholder="请输入需求描述" />
      </el-form-item>
      <el-form-item label="状态" prop="status" required>
        <el-select v-model="addReqForm.status" placeholder="请选择">
          <el-option label="待处理" value="pending" />
          <el-option label="进行中" value="in-progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="closeDialog">取消</el-button>
      <el-button type="primary" @click="submitAddReq" :loading="submitting">{{ editMode ? '保存' : '提交' }}</el-button>
    </template>
  </el-dialog>
</template>
<script setup>
import { Connection, CircleCloseFilled, Lightning, Check, Refresh } from '@element-plus/icons-vue'
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchRequirements, createRequirement, updateRequirement, deleteRequirement, getRequirementAiAnalysis, getSingleRequirementAiAnalysis } from '@/api/project'
import { useRoute } from 'vue-router'

const route = useRoute()
const projectId = computed(() => route.params.id)

const requirements = ref([])
const loading = ref(false)
const submitting = ref(false)
const showAddReq = ref(false)
const editMode = ref(false)
const editingReqId = ref(null)
const addReqForm = ref({ name: '', priority: 'medium', tags: '', description: '', status: 'pending' })
const aiAnalysisLoading = ref(false)
const aiAnalysis = ref({
  completeness: 0,
  dependencies: 0,
  conflicts: 0,
  suggestions: []
})
const filterPriority = ref('')
const filterStatus = ref('')
const filterKeyword = ref('')
const filteredRequirements = computed(() => {
  return requirements.value.filter(req => {
    const matchPriority = !filterPriority.value || req.priority === filterPriority.value
    const matchStatus = !filterStatus.value || req.status === filterStatus.value
    const matchKeyword = !filterKeyword.value || req.name.includes(filterKeyword.value) || (req.description && req.description.includes(filterKeyword.value))
    return matchPriority && matchStatus && matchKeyword
  })
})

// 表单引用
const reqFormRef = ref(null)

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入需求名称', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  tags: [{ required: true, message: '请输入标签', trigger: 'blur' }],
  description: [{ required: true, message: '请输入需求描述', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

// 获取需求列表
const fetchRequirementList = async () => {
  try {
    loading.value = true
    const res = await fetchRequirements(projectId.value)
    requirements.value = res.data
    requirements.value.forEach(req => {
      req.analyzing = false
      req.showFullAnalysis = false
      // 自动AI分析
      req.ai_analysis = ''
      analyzeRequirement(req)
    })
  } catch (error) {
    console.error('获取需求列表失败:', error)
    ElMessage.error('获取需求列表失败')
  } finally {
    loading.value = false
  }
}

// 获取需求AI分析
const fetchAiAnalysis = async () => {
  if (!projectId.value) {
    ElMessage.warning('没有有效的项目ID')
    return
  }
  
  try {
    aiAnalysisLoading.value = true
    const res = await getRequirementAiAnalysis(projectId.value)
    
    // 检查响应数据结构
    if (res.data) {
      aiAnalysis.value = {
        completeness: res.data.completeness || 0,
        dependencies: res.data.dependencies || 0,
        conflicts: res.data.conflicts || 0,
        suggestions: Array.isArray(res.data.suggestions) ? res.data.suggestions : []
      }
      
      console.log('AI需求分析结果:', aiAnalysis.value)
    } else {
      console.error('AI分析响应数据格式错误:', res)
      ElMessage.error('AI分析响应数据格式错误')
    }
  } catch (error) {
    console.error('获取AI分析失败:', error)
    ElMessage.error('获取AI分析失败')
  } finally {
    aiAnalysisLoading.value = false
  }
}

// 获取完整性状态
const getCompletenessStatus = (score) => {
  if (score >= 80) return 'success' 
  if (score >= 60) return 'warning'
  return 'exception'
}

// 打开编辑弹窗
const openEditReq = (req) => {
  editMode.value = true
  editingReqId.value = req.id
  addReqForm.value = {
    name: req.name,
    priority: req.priority,
    tags: req.tags,
    description: req.description,
    status: req.status
  }
  showAddReq.value = true
}

// 关闭弹窗
const closeDialog = () => {
  showAddReq.value = false
  editMode.value = false
  editingReqId.value = null
  addReqForm.value = { name: '', priority: 'medium', tags: '', description: '', status: 'pending' }
}

// 提交新建/编辑需求
const submitAddReq = async () => {
  if (!reqFormRef.value) {
    console.error('表单引用不存在')
    return
  }
  
  reqFormRef.value.validate(async valid => {
    if (!valid) {
      ElMessage.error('请填写所有必填项')
      return
    }
    
    try {
      submitting.value = true
      const formData = {
        project: projectId.value,
        name: addReqForm.value.name,
        description: addReqForm.value.description,
        priority: addReqForm.value.priority,
        tags: addReqForm.value.tags,
        status: addReqForm.value.status
      }
      if (editMode.value && editingReqId.value) {
        await updateRequirement(editingReqId.value, formData)
        ElMessage.success('需求更新成功')
      } else {
        await createRequirement(formData)
        ElMessage.success('需求创建成功')
      }
      closeDialog()
      refreshAfterChange()
    } catch (error) {
      console.error('保存需求失败:', error)
      ElMessage.error('保存需求失败')
    } finally {
      submitting.value = false
    }
  })
}

// 删除需求
const handleDeleteReq = async (req) => {
  try {
    await ElMessageBox.confirm('确定删除此需求？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    await deleteRequirement(req.id)
    ElMessage.success('删除成功')
    refreshAfterChange()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除需求失败:', error)
      ElMessage.error('删除需求失败')
    }
  } finally {
    loading.value = false
  }
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    'pending': 'info',
    'in-progress': 'primary',
    'completed': 'success'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    'pending': '待处理',
    'in-progress': '进行中',
    'completed': '已完成'
  }
  return texts[status] || '待处理'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '刚刚'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  // 如果小于1天，显示"x小时前"或"x分钟前"
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours > 0) {
      return `${hours}小时前`
    }
    const minutes = Math.floor(diff / (60 * 1000))
    if (minutes > 0) {
      return `${minutes}分钟前`
    }
    return '刚刚'
  }
  
  // 否则显示日期
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 分析需求
const analyzeRequirement = (req, showMsg = false) => {
  if (!req.id) {
    if (showMsg) ElMessage.warning('无效的需求ID')
    return
  }
  req.analyzing = true
  getSingleRequirementAiAnalysis(req.id)
    .then(res => {
      req.ai_analysis = res.data.ai_analysis || '暂无分析'
      req.showFullAnalysis = false
      if (showMsg) ElMessage.success('AI分析完成')
    })
    .catch(() => {
      req.ai_analysis = 'AI分析失败'
      if (showMsg) ElMessage.error('AI分析失败')
    })
    .finally(() => {
      req.analyzing = false
    })
}

// 在组件挂载时获取需求列表和AI分析
onMounted(() => {
  fetchRequirementList()
  fetchAiAnalysis()
})

// 监听项目ID变化，同时刷新需求列表和AI分析
watch(projectId, () => {
  if (projectId.value) {
    fetchRequirementList()
    fetchAiAnalysis()
  }
})

// 在创建或更新需求后刷新AI分析
const refreshAfterChange = () => {
  fetchRequirementList()
  fetchAiAnalysis()
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
.list-group-item,
.list-group-item-action,
.list-group-item-action:active,
.list-group-item-action:focus,
.list-group-item-action:hover {
  background: var(--bg-color-tertiary) !important;
  color: var(--text-color);
  border: none;
}
.ai-analysis-card { background: var(--bg-color-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; margin-bottom: 15px; }
.dependency-item, .suggestion-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.text-primary { color: var(--primary-color)!important; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.list-group-item:hover {
  background: var(--hover-color);
  color: var(--primary-color);
}
.ai-requirement-analysis {
  background: var(--bg-color-tertiary);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  color: var(--text-color);
}
.ai-requirement-analysis .text-muted,
.ai-requirement-analysis small {
  color: var(--text-color-tertiary) !important;
}

/* 确保 Element Plus 组件在深色模式下正确显示 */
:deep(.el-dialog),
:deep(.el-dialog .el-dialog__body),
:deep(.el-dialog .el-dialog__header),
:deep(.el-dialog .el-dialog__footer) {
  background: var(--bg-color-secondary) !important;
  color: var(--text-color) !important;
}

:deep(.el-button.el-button--text) {
  color: var(--primary-color) !important;
}

:deep(.el-select-dropdown),
:deep(.el-select-dropdown__item),
:deep(.el-select-dropdown__list) {
  background-color: var(--bg-color-secondary) !important;
  color: var(--text-color) !important;
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
  background-color: var(--hover-color) !important;
}

/* 修复 el-tag 标签在深色模式下的显示 */
:deep(.el-tag) {
  background-color: var(--bg-color-tertiary) !important;
  color: var(--text-color) !important;
  border-color: var(--border-color) !important;
}

:deep(.el-tag.el-tag--info) {
  background-color: var(--bg-color-tertiary) !important;
  border-color: var(--border-color) !important;
}

:deep(.el-tag.el-tag--success) {
  background-color: var(--success-color) !important;
  border-color: var(--success-color) !important;
  color: #fff !important;
}

:deep(.el-tag.el-tag--primary) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: #fff !important;
}

:deep(.el-tag.el-tag--warning) {
  background-color: var(--warning-color) !important;
  border-color: var(--warning-color) !important;
  color: #fff !important;
}

:deep(.el-tag.el-tag--danger) {
  background-color: var(--danger-color) !important;
  border-color: var(--danger-color) !important;
  color: #fff !important;
}

/* 修复按钮悬停效果 */
:deep(.el-button:hover),
:deep(.el-button:focus) {
  background-color: var(--hover-color) !important;
  border-color: var(--primary-color) !important;
  color: var(--primary-color) !important;
}

:deep(.el-button--primary:hover),
:deep(.el-button--primary:focus) {
  background-color: var(--primary-color) !important;
  opacity: 0.9;
  color: #fff !important;
}

:deep(.el-button--danger:hover),
:deep(.el-button--danger:focus) {
  background-color: var(--danger-color) !important;
  opacity: 0.9;
  color: #fff !important;
}

:deep(.el-button--info:hover),
:deep(.el-button--info:focus) {
  background-color: var(--info-color) !important;
  opacity: 0.9;
  color: #fff !important;
}

:deep(.el-button--text:hover),
:deep(.el-button--text:focus) {
  background-color: transparent !important;
  color: var(--primary-color) !important;
  opacity: 0.9;
}

/* 确保字体可见 */
.ai-requirement-tags,
.ai-requirement-status {
  color: var(--text-color) !important;
}

/* 修复列表项细节 */
.list-group-item {
  border-radius: 5px !important;
  margin-bottom: 10px !important;
  padding: 16px !important;
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

  .text-muted, .small, .ai-requirement-analysis small.text-muted {
    color: var(--el-text-color-secondary) !important;
  }
  
  .el-form-item__label {
    color: var(--el-text-color-secondary) !important;
  }

  .el-input__wrapper, .el-select .el-input__wrapper {
    background-color: var(--el-fill-color-light) !important;
    border-color: var(--el-border-color) !important;
  }

  .list-group-item-action:hover {
    background-color: var(--el-fill-color-light) !important;
  }

  .dependency-item, .suggestion-item {
    color: var(--el-text-color-secondary) !important;
  }
}
</style> 
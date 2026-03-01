<template>
  <div class="main-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h4>{{ project ? project.name : '项目详情' }}</h4>
          <div class="d-flex align-items-center">
            <span class="badge" :class="project?.statusClass">{{ project?.statusText }}</span>
            <span class="ms-3 text-muted">
              <i class="bi bi-calendar me-1"></i> 
              {{ project?.start ? formatDate(project.start) : '未设置' }} - 
              {{ project?.end ? formatDate(project.end) : '未设置' }}
            </span>
          </div>
        </div>
        <div>
          <el-button type="primary" size="small" plain @click="goBack">
            <i class="bi bi-arrow-left me-1"></i> 返回列表
          </el-button>
          <el-button type="primary" size="small" class="ms-2" @click="showSetting = true">
            <i class="bi bi-gear me-1"></i> 项目设置
          </el-button>
        </div>
      </div>
    </div>
    <!-- 设置弹窗 -->
    <el-dialog v-model="showSetting" title="项目设置" width="500px">
      <el-form :model="editProject" label-width="80px" :rules="formRules" ref="editProjectFormRef">
        <el-form-item label="项目名称" prop="name" required>
          <el-input v-model="editProject.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="desc" required>
          <el-input v-model="editProject.desc" type="textarea" placeholder="请输入项目描述" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start" required>
          <el-date-picker v-model="editProject.start" placeholder="请选择开始日期" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end" required>
          <el-date-picker v-model="editProject.end" placeholder="请选择结束日期" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSetting=false">取消</el-button>
        <el-button type="primary" @click="saveSetting">保存</el-button>
      </template>
    </el-dialog>
    <!-- 导航栏 -->
    <div class="nav-tabs-container">
      <ul class="nav nav-tabs">
        <li class="nav-item" v-for="item in navItems" :key="item.view">
          <a class="nav-link" :class="{active: activeView === item.view}" href="#" @click.prevent="activeView = item.view">
            <el-icon :size="16"><component :is="item.icon" /></el-icon>
            {{ item.label }}
          </a>
        </li>
      </ul>
    </div>
    <!-- 内容区 -->
    <div class="content-area">
      <!-- 内容模块 -->
      <div v-if="activeView === 'dashboard'">
        <DashboardView :project="project" :tasks="tasks" :documents="documents" :requirements="requirements" />
      </div>
      <div v-else-if="activeView === 'tasks'">
        <TasksView :project="project" :members="projectMembers" />
      </div>
      <div v-else-if="activeView === 'documents'">
        <DocumentsView :project="project" />
      </div>
      <div v-else-if="activeView === 'requirements'">
        <RequirementsView :project="project" />
      </div>
      <div v-else-if="activeView === 'reports'">
        <ReportsView :project="project" :tasks="tasks" :documents="documents" :requirements="requirements" />
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Grid, List, Document, Lightning, DataAnalysis } from '@element-plus/icons-vue'
import DashboardView from './components/DashboardView.vue'
import TasksView from './components/TasksView.vue'
import DocumentsView from './components/DocumentsView.vue'
import RequirementsView from './components/RequirementsView.vue'
import ReportsView from './components/ReportsView.vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const activeView = ref('dashboard')
const project = ref(null)
const showSetting = ref(false)
const editProject = ref({ name: '', desc: '', start: '', end: '' })
const projectMembers = ref([])

// 新增：统一管理任务、文档、需求数据
const tasks = ref([])
const documents = ref([])
const requirements = ref([])

// 新增：是否正在加载数据
const isLoading = ref(false)

// 表单引用
const editProjectFormRef = ref(null)

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' }
  ],
  desc: [
    { required: true, message: '请输入项目描述', trigger: 'blur' }
  ],
  start: [
    { required: true, message: '请选择开始日期', trigger: 'change' }
  ],
  end: [
    { required: true, message: '请选择结束日期', trigger: 'change' }
  ]
}

const navItems = [
  { label: '工作台', view: 'dashboard', icon: Grid },
  { label: '任务管理', view: 'tasks', icon: List },
  { label: '文档管理', view: 'documents', icon: Document },
  { label: '需求管理', view: 'requirements', icon: Lightning },
  { label: '项目报表', view: 'reports', icon: DataAnalysis }
]

onMounted(() => {
  loadProject()
})

watch(showSetting, (val) => {
  if (val && project.value) {
    editProject.value = { ...project.value }
  }
})

// 监听视图切换，切换到工作台或报表时刷新数据
watch(activeView, (newView) => {
  if ((newView === 'dashboard' || newView === 'reports') && project.value?.id) {
    refreshData()
  }
})

function loadProject() {
  const id = Number(route.params.id)
  if (isNaN(id)) {
    router.push({ name: 'Project' })
    return
  }
  request.get(`/api/projects/${id}/`).then(res => {
    project.value = res.data
    if (project.value.status === 'doing') {
      project.value.statusText = '进行中'
      project.value.statusClass = 'bg-primary'
    } else if (project.value.status === 'done') {
      project.value.statusText = '已完成'
      project.value.statusClass = 'bg-success'
    } else {
      project.value.statusText = project.value.status || '未知'
      project.value.statusClass = 'bg-secondary'
    }
    
    // 加载项目成员
    loadProjectMembers(id)
    // 新增：加载任务、文档、需求
    loadTasks(id)
    loadDocuments(id)
    loadRequirements(id)
  }).catch(() => {
    router.push({ name: 'Project' })
  })
}

// 新增：加载项目成员
async function loadProjectMembers(projectId) {
  if (!projectId) return

  console.log('ProjectDetail: 加载项目成员，项目ID:', projectId)

  try {
    // 1. 先获取项目详情，确保拿到最新的成员列表
    const projectRes = await request.get(`/api/projects/${projectId}/`);
    const updatedProject = projectRes.data;
    
    // 如果项目中有成员ID列表
    if (updatedProject && updatedProject.members && updatedProject.members.length > 0) {
      const memberIds = updatedProject.members;
      
      // 2. 获取公司所有用户，用于查找成员信息
      const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
      const companyId = userInfo.company_id || userInfo.company;
      if (!companyId) {
        console.error('无法获取公司ID，无法加载成员信息');
        return;
      }
      
      const usersRes = await request.get(`/api/auth/companies/${companyId}/users/`);
      let allCompanyUsers = [];
      if (Array.isArray(usersRes.data)) {
        allCompanyUsers = usersRes.data;
      } else if (usersRes.data && Array.isArray(usersRes.data.data)) {
        allCompanyUsers = usersRes.data.data;
      }
      
      // 3. 从公司所有用户中，筛选出属于本项目的成员
      const memberSet = new Set(memberIds);
      projectMembers.value = allCompanyUsers
        .filter(user => memberSet.has(user.id))
        .map(user => ({
          id: user.id,
          name: user.name || user.username || user.email || `用户${user.id}`
        }));

      console.log('ProjectDetail: 已加载项目成员:', projectMembers.value);
    } else {
      console.log('项目尚无成员');
      projectMembers.value = [];
    }
  } catch (err) {
    console.error('加载项目成员失败', err);
  }
}

// 加载任务数据
function loadTasks(projectId) {
  if (!projectId) return
  request.get(`/api/tasks/?project=${projectId}`).then(res => {
    // 修复：兼容多种后端响应结构
    let tasksData = []
    if (res.data && Array.isArray(res.data.results)) {
      // 分页结构 { results: [...] }
      tasksData = res.data.results
    } else if (Array.isArray(res.data)) {
      // 数组结构 [...]
      tasksData = res.data
    } else if (res.data && Array.isArray(res.data.data)) {
      // 嵌套结构 { data: [...] }
      tasksData = res.data.data
    }
    
    // 标准化任务状态，确保前端统一处理
    tasks.value = tasksData.map(task => ({
      ...task,
      status: task.status === '已完成' ? 'done' : 
              task.status === '进行中' ? 'in-progress' : 
              task.status === '待处理' ? 'todo' : 
              task.status || 'todo',
      due_date: task.due_date || task.dueDate || '' // 确保 due_date 字段存在
    }))
    
    console.log('加载任务数据成功:', tasks.value.length, '条')
  }).catch(err => {
    console.error('加载任务失败:', err)
    tasks.value = []
  })
}

// 加载文档数据
function loadDocuments(projectId) {
  if (!projectId) return
  request.get(`/api/project-documents/?project=${projectId}`).then(res => {
    // 修复：兼容多种后端响应结构
    if (res.data && Array.isArray(res.data.results)) {
      documents.value = res.data.results
    } else if (Array.isArray(res.data)) {
      documents.value = res.data
    } else if (res.data && Array.isArray(res.data.data)) {
      documents.value = res.data.data
    } else {
      documents.value = []
    }
    console.log('加载文档数据成功:', documents.value.length, '条')
  }).catch(err => {
    console.error('加载文档失败:', err)
    documents.value = []
  })
}

// 加载需求数据
function loadRequirements(projectId) {
  if (!projectId) return
  request.get(`/api/requirements/?project=${projectId}`).then(res => {
    // 修复：兼容多种后端响应结构
    if (res.data && Array.isArray(res.data.results)) {
      requirements.value = res.data.results
    } else if (Array.isArray(res.data)) {
      requirements.value = res.data
    } else if (res.data && Array.isArray(res.data.data)) {
      requirements.value = res.data.data
    } else {
      requirements.value = []
    }
    console.log('加载需求数据成功:', requirements.value.length, '条')
  }).catch(err => {
    console.error('加载需求失败:', err)
    requirements.value = []
  })
}

// 新增：刷新所有数据
function refreshData() {
  if (!project.value?.id) return
  
  isLoading.value = true
  console.log('刷新项目数据...')
  
  // 并行加载所有数据
  Promise.all([
    loadTasksAsync(project.value.id),
    loadDocumentsAsync(project.value.id),
    loadRequirementsAsync(project.value.id)
  ]).finally(() => {
    isLoading.value = false
    console.log('数据刷新完成')
  })
}

// 新增：异步加载任务数据
function loadTasksAsync(projectId) {
  return new Promise((resolve) => {
    loadTasks(projectId)
    resolve()
  })
}

// 新增：异步加载文档数据
function loadDocumentsAsync(projectId) {
  return new Promise((resolve) => {
    loadDocuments(projectId)
    resolve()
  })
}

// 新增：异步加载需求数据
function loadRequirementsAsync(projectId) {
  return new Promise((resolve) => {
    loadRequirements(projectId)
    resolve()
  })
}

function formatDate(dateStr) {
  if (!dateStr) return '未设置'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function goBack() {
  router.push({ name: 'Project' })
}

function saveSetting() {
  if (!project.value?.id) return
  
  // 使用表单验证
  if (!editProjectFormRef.value) {
    console.error('表单引用不存在')
    return
  }
  
  editProjectFormRef.value.validate(valid => {
    if (!valid) {
      return
    }

    // 校验开始时间不能大于结束时间
    if (editProject.value.start && editProject.value.end) {
      if (new Date(editProject.value.start) > new Date(editProject.value.end)) {
        ElMessage.error('项目开始时间不能大于结束时间')
        return
      }
    }
  
    // 日期格式化
    function formatDateStr(val) {
      if (!val) return null  // 将空值转为null，避免空字符串验证错误
      if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(val)) return val
      const d = new Date(val)
      if (isNaN(d)) return null  // 无效日期返回null
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    }
    
    const members = projectMembers.value.map(m => m.id)
    
    // 获取用户所在公司ID
    const userInfo = JSON.parse(localStorage.getItem('user') || '{}')
    let companyId = userInfo.company_id || userInfo.company 
    if (typeof companyId === 'string' && !isNaN(companyId)) {
      companyId = Number(companyId)
    }
    
    const payload = { 
      ...editProject.value, 
      members,
      company_id: companyId, // 确保company_id字段存在
      start: formatDateStr(editProject.value.start),
      end: formatDateStr(editProject.value.end)
    }
    
    // 移除不需要的字段，避免后端验证错误
    delete payload.company
    delete payload.companyId
    delete payload.statusText
    delete payload.statusClass
    
    console.log('准备保存的项目数据:', payload)
    
    request.put(`/api/projects/${project.value.id}/`, payload).then(res => {
      Object.assign(project.value, res.data)
      showSetting.value = false
    }).catch(err => {
      console.error('更新项目失败', err?.response?.data || err)
    })
  })
}
</script>
<style scoped>
@import url('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css');
@import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css');
.main-container {
  min-height: 100vh;
  background: var(--bg-color);
  padding-top: 0;
}
.page-header {
  background: var(--bg-color-secondary);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  margin-bottom: 20px;
  margin-top: 0;
  color: var(--text-color);
}
.nav-tabs-container {
  background: var(--bg-color-secondary);
  padding: 0 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  margin-bottom: 20px;
}
.nav-tabs {
  border-bottom: none;
}
.nav-link {
  color: var(--text-color-secondary);
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
}
.nav-link.active {
  color: var(--primary-color);
  border-bottom: 2px solid var(--primary-color);
  background: var(--bg-color);
  border-radius: 10px 10px 0 0;
}
.nav-link:hover {
  background: var(--hover-color);
  color: var(--primary-color);
}
.content-area {
  padding: 20px;
  background: var(--bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  color: var(--text-color);
}
.page-header:hover,
.nav-tabs-container:hover {
  background: var(--hover-color);
}
.bg-primary { background: var(--primary-color)!important; }
.bg-success { background: var(--success-color)!important; }
.bg-warning { background: var(--warning-color)!important; }
.bg-secondary { background: var(--border-color)!important; }
.bg-info { background: var(--info-color)!important; }
.badge {
  font-weight: 500;
  padding: 6px 10px;
  border-radius: 6px;
  color: #fff;
}
/* 如果有全局样式导致空白，可强制覆盖 */
:deep(.el-main) {
  padding-top: 0 !important;
}
.text-muted {
  color: var(--text-color-tertiary) !important;
}
</style>

<style lang="scss">
/* 深色模式下的样式修复 */
[data-theme="dark"] {
  .main-container, .page-header, .nav-tabs-container, .content-area {
    background-color: var(--el-bg-color-page) !important;
    color: var(--el-text-color-primary) !important;
  }
  
  .page-header {
    border-bottom: 1px solid var(--el-border-color);
  }

  .nav-tabs .nav-link {
    color: var(--el-text-color-secondary);
    border-color: transparent;
  }

  .nav-tabs .nav-link:hover {
    background: var(--el-fill-color-light);
    border-color: var(--el-border-color);
  }

  .nav-tabs .nav-link.active {
    background-color: var(--el-color-primary) !important;
    color: #fff !important;
    border-color: var(--el-color-primary) !important;
  }

  /* 修复弹窗样式 */
  .el-dialog {
    background-color: var(--el-bg-color);
  }

  .el-dialog__title {
    color: var(--el-text-color-primary);
  }

  .el-dialog__header {
    border-bottom: 1px solid var(--el-border-color);
  }
  
  .el-form-item__label {
    color: var(--el-text-color-secondary);
  }
}
</style> 
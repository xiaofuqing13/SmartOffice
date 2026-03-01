<template>
  <div class="container-fluid">
    <div class="row">
      <!-- 左侧项目导航 -->
      <div :class="['project-sidebar', isNavCollapsed ? 'collapsed' : '']">
        <div class="card">
          <div class="card-header">
            <span v-if="!isNavCollapsed">我的项目</span>
            <div class="header-actions">
              <button v-if="!isNavCollapsed" class="btn btn-sm btn-primary" @click="showNewProject = true">
                <i class="bi bi-plus"></i> 新建
              </button>
              <button class="btn btn-sm btn-icon" @click="isNavCollapsed = !isNavCollapsed">
                <i :class="['bi', isNavCollapsed ? 'bi-chevron-double-right' : 'bi-chevron-double-left']"></i>
              </button>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="userProjects.length === 0" class="empty-state-nav">
              <el-icon style="font-size:40px;color:#d3d3d3;margin-bottom:10px;"><FolderOpened /></el-icon>
              <div class="empty-title-nav">暂无项目</div>
            </div>
            <div v-else class="project-nav">
              <div v-for="(project, idx) in userProjects" :key="project.id" class="project-item" :class="{active: idx === activeProjectIdx}" @click="selectProject(idx)" :title="project.name">
                <i class="bi bi-kanban"></i>
                <span class="project-name">{{ project.name }}</span>
                <span class="badge" :class="project.statusClass">{{ project.statusText }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 右侧内容区域 -->
      <div :class="['project-main-content', isNavCollapsed ? 'expanded' : '']">
        <div class="card">
          <div class="card-header">
            <span>项目列表</span>
            <div class="search-box">
              <el-input v-model="searchText" placeholder="搜索项目..." prefix-icon="Search" clearable />
            </div>
          </div>
          <div class="card-body">
            <div v-if="filteredProjects.length === 0" class="empty-state">
              <el-icon style="font-size:120px;color:#d3d3d3;margin-bottom:16px;"><FolderOpened /></el-icon>
              <div class="empty-title">暂无项目</div>
              <div class="empty-desc">您还没有任何项目，点击右上角"新建"按钮添加您的第一个项目吧！</div>
            </div>
            <div v-else class="row">
              <div v-for="project in filteredProjects" :key="project.id" class="col-md-6 mb-4">
                <div class="project-card">
                  <div class="project-card-header">
                    <h5>{{ project.name }}</h5>
                    <span class="badge" :class="project.statusClass">{{ project.statusText }}</span>
                  </div>
                  <div class="project-card-body">
                    <p>{{ project.desc || '暂无描述' }}</p>
                    <div class="project-card-stats">
                      <div class="stat-item">
                        <i class="bi bi-calendar"></i>
                        <span>{{ project.start ? formatDate(project.start) : '未设置' }}</span>
                      </div>
                      <div class="stat-item">
                        <i class="bi bi-people"></i>
                        <span>{{ project.members ? project.members.length : 0 }}人</span>
                      </div>
                    </div>
                  </div>
                  <div class="project-card-footer">
                    <el-button type="primary" size="small" @click="goToProjectDetail(project.id)">查看详情</el-button>
                    <el-dropdown @command="handleCommand($event, project.id)" trigger="click">
                      <el-button size="small" plain>
                        <i class="bi bi-three-dots"></i>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="edit">编辑项目</el-dropdown-item>
                          <el-dropdown-item command="delete" divided>删除项目</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 分页组件 -->
            <div class="pagination-container" v-if="total > 0">
              <el-pagination
                background
                layout="prev, pager, next"
                :total="total"
                :page-size="pageSize"
                :current-page="currentPage"
                @current-change="handlePageChange"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 新建/编辑项目弹窗 -->
    <el-dialog v-model="showNewProject" :title="newProject.id ? '编辑项目' : '新建项目'" width="500px">
      <el-form :model="newProject" label-width="80px" :rules="formRules" ref="projectFormRef">
        <el-form-item label="项目名称" prop="name" required>
          <el-input v-model="newProject.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="desc" required>
          <el-input v-model="newProject.desc" type="textarea" placeholder="请输入项目描述" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start" required>
          <el-date-picker v-model="newProject.start" placeholder="请选择开始日期" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end" required>
          <el-date-picker v-model="newProject.end" placeholder="请选择结束日期" />
        </el-form-item>
        <el-form-item label="项目成员" prop="members" required>
          <el-select v-model="newProject.members" multiple placeholder="请选择项目成员">
            <el-option v-for="m in memberOptions" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNewProject=false">取消</el-button>
        <el-button type="primary" @click="addProject">{{ newProject.id ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { FolderOpened } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const store = useStore()
const searchText = ref('')
const projects = ref([])
const activeProjectIdx = ref(0)
const showNewProject = ref(false)
const newProject = ref({ name: '', desc: '', start: '', end: '', members: [] })
const memberOptions = ref([])
const isNavCollapsed = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 表单引用
const projectFormRef = ref(null)

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
  ],
  members: [
    { required: true, message: '请选择项目成员', trigger: 'change' }
  ]
}

function fetchProjects() {
  console.log('fetchProjects: 开始请求项目列表')
  request.get('/api/projects/', {
    params: {
      page: currentPage.value,
      page_size: pageSize.value
    }
  }).then(res => {
    console.log('fetchProjects: 获取成功', res.data)
    
    // 处理后端返回的分页数据
    if (res.data && Array.isArray(res.data.results)) {
      projects.value = res.data.results || []
      total.value = res.data.count || 0
    } else {
      // 兼容不支持分页的旧接口
      projects.value = res.data || []
      total.value = projects.value.length
    }
    
    // 为每个项目添加状态文本和样式
    projects.value.forEach(project => {
      if (project.status === 'doing') {
        project.statusText = '进行中'
        project.statusClass = 'bg-primary text-white'
      } else if (project.status === 'done') {
        project.statusText = '已完成'
        project.statusClass = 'bg-success text-white'
      } else {
        project.statusText = project.status || '未知'
        project.statusClass = 'bg-secondary text-white'
      }
    })
  }).catch(err => {
    console.error('fetchProjects: 请求失败', err?.response?.data || err)
    alert('获取项目列表失败: ' + (err?.response?.data?.detail || '请检查权限或网络连接'))
  })
}

function getCompanyIdFromUser(user) {
  if (!user) return null
  if (typeof user.company_id === 'number') return user.company_id
  if (typeof user.company === 'number') return user.company
  // 兼容后端返回字符串数字
  if (!isNaN(user.company_id)) return Number(user.company_id)
  if (!isNaN(user.company)) return Number(user.company)
  return null
}

function fetchMembers(companyId) {
  companyId = Number(companyId)
  if (!companyId || isNaN(companyId)) {
    console.warn('fetchMembers: companyId无效', companyId)
    return
  }
  const token = localStorage.getItem('token')
  if (!token) {
    alert('未检测到登录凭证，请重新登录！')
    memberOptions.value = []
    return
  }
  console.log('fetchMembers: companyId=', companyId, 'token=', token)
  request.get(`/api/auth/companies/${companyId}/users/`).then(res => {
    let arr = []
    if (Array.isArray(res.data)) {
      arr = res.data
    } else if (res.data && Array.isArray(res.data.data)) {
      arr = res.data.data
    } else {
      console.error('fetchMembers: 返回数据不是数组', res.data)
    }
    memberOptions.value = arr.map(u => ({
      value: u.id,
      label: u.name || u.username
    }))
  }).catch(err => {
    if (err?.response?.status === 403) {
      alert('无权限访问公司成员接口，请重新登录或联系管理员！')
    } else {
      alert('获取公司成员失败，请检查网络或联系管理员！')
    }
    console.error('fetchMembers: 请求出错', err, err?.response?.data)
    memberOptions.value = []
  })
}

/**
 * 确保当前用户关联了公司
 */
function ensureUserCompany() {
  const user = store.getters.user
  
  if (!user) {
    console.warn('未找到用户信息')
    return null
  }
  
  // 检查用户是否有公司信息
  const companyId = getCompanyIdFromUser(user)
  
  if (!companyId) {
    console.warn('用户未关联公司')
    return null
  }
  
  return companyId
}

onMounted(() => {
  console.log('项目页面挂载')
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  
  if (!token) {
    console.warn('未找到token，请确保已登录')
    router.push('/login')
    return
  }
  
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      console.log('当前用户信息:', user)
      console.log('用户公司ID:', getCompanyIdFromUser(user))
      
      // 检查用户公司
      const companyId = ensureUserCompany()
      if (!companyId) {
        alert('您未关联到任何公司，无法访问项目管理页面')
      }
    } catch(e) {
      console.error('解析用户信息失败', e)
    }
  }
  
  // 获取项目列表
  fetchProjects()
})

const userProjects = computed(() => {
  const user = store.getters.user;
  if (!user) {
    return [];
  }
  return projects.value.filter(p => 
    Array.isArray(p.members) && p.members.includes(user.id)
  );
});

const filteredProjects = computed(() => {
  // Then, if there is search text, apply the search filter
  if (!searchText.value) {
    return userProjects.value;
  }

  const keyword = searchText.value.toLowerCase();
  return userProjects.value.filter(p =>
    (p.name && p.name.toLowerCase().includes(keyword)) ||
    (p.desc && p.desc.toLowerCase().includes(keyword))
  );
});

function formatDate(dateStr) {
  if (!dateStr) return '未设置'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function selectProject(idx) {
  activeProjectIdx.value = idx
}

function goToProjectDetail(id) {
  router.push({ name: 'ProjectDetail', params: { id } })
}

function handleCommand(command, projectId) {
  if (command === 'edit') {
    const project = projects.value.find(p => p.id === projectId)
    if (project) {
      newProject.value = { ...project }
      showNewProject.value = true
      fetchMembers(project.company) // 拉取公司成员
    }
  } else if (command === 'delete') {
    ElMessageBox.confirm('确定要删除该项目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      request.delete(`/api/projects/${projectId}/`).then(() => {
        fetchProjects()
      })
    }).catch(() => {})
  }
}

function addProject() {
  // 使用表单验证
  if (!projectFormRef.value) {
    console.error('表单引用不存在')
    return
  }

  projectFormRef.value.validate((valid) => {
    if (!valid) {
      ElMessage.error('请填写所有必填项')
      return
    }

    // 校验开始时间不能大于结束时间
    if (newProject.value.start && newProject.value.end) {
      if (new Date(newProject.value.start) > new Date(newProject.value.end)) {
        ElMessage.error('项目开始时间不能大于结束时间')
        return
      }
    }

    const user = store.getters.user
    const companyId = getCompanyIdFromUser(user)
    if (!companyId) {
      alert('您没有关联到任何公司，无法创建项目')
      return
    }
    // 日期格式化
    function formatDateStr(val) {
      if (!val) return null  // 将空字符串改为null，避免空字符串验证错误
      if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(val)) return val
      const d = new Date(val)
      if (isNaN(d)) return null  // 无效日期返回null而不是空字符串
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    }
    const projectData = {
      ...newProject.value,
      company_id: companyId, // 确保company_id字段存在
      start: formatDateStr(newProject.value.start),
      end: formatDateStr(newProject.value.end)
    }
    delete projectData.company // 防御性删除
    delete projectData.companyId
    console.log('准备保存的项目数据:', projectData)
    if (newProject.value.id) {
      request.put(`/api/projects/${newProject.value.id}/`, projectData)
        .then((res) => {
          console.log('项目更新成功:', res.data)
          showNewProject.value = false
          fetchProjects()
        })
        .catch(err => {
          console.error('编辑项目失败', err?.response?.data || err)
          alert('编辑项目失败: ' + (err?.response?.data?.detail || '请检查权限或网络连接'))
        })
    } else {
      request.post('/api/projects/', projectData)
        .then((res) => {
          console.log('项目创建成功:', res.data)
          showNewProject.value = false
          fetchProjects()
        })
        .catch(err => {
          console.error('创建项目失败', err?.response?.data || err)
          alert('创建项目失败: ' + (err?.response?.data?.detail || '请检查权限或网络连接'))
        })
    }
    newProject.value = { name: '', desc: '', start: '', end: '', members: [] }
  })
}

// 新建项目弹窗打开时自动拉取公司成员，并自动回填已选成员
watch(showNewProject, (val) => {
  if (val) {
    const user = store.getters.user
    const companyId = getCompanyIdFromUser(user)
    if (companyId) fetchMembers(companyId)
    // 编辑时自动回填成员
    if (newProject.value.id && Array.isArray(newProject.value.members)) {
      newProject.value.members = [...newProject.value.members]
    } else {
      newProject.value.members = []
    }
  }
})

// 添加分页处理函数
function handlePageChange(page) {
  currentPage.value = page
  fetchProjects()
}
</script>

<style scoped>
@import url('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css');
@import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css');
.container-fluid { background: var(--bg-color); min-height: 100vh; }
.card { border: none; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); margin-bottom: 20px; background: var(--bg-color-secondary); }
.card-header { background-color: var(--bg-color); border-bottom: 1px solid var(--border-color); padding: 15px 20px; font-weight: 600; font-size: 16px; color: var(--text-color); display: flex; justify-content: space-between; align-items: center; }
.card-body { padding: 20px; }
.btn-primary { background-color: var(--primary-color); border-color: var(--primary-color); }
.project-nav { height: 620px; overflow-y: auto; }
.project-item { display: flex; align-items: center; padding: 12px 15px; color: var(--text-color-secondary); text-decoration: none; transition: all 0.2s; cursor: pointer; border-radius: 5px; margin-bottom: 5px; }
.project-item:hover {
  background: var(--hover-color);
  color: var(--primary-color);
}
.project-item.active { background-color: var(--active-color); color: var(--primary-color); font-weight: 500; }
.project-item i { margin-right: 10px; font-size: 18px; width: 24px; text-align: center; }
.project-item .badge { margin-left: auto; background-color: var(--border-color); font-weight: 500; padding: 4px 8px; border-radius: 10px; color: var(--text-color); }
.bg-primary { background: var(--primary-color)!important; }
.bg-success { background: var(--success-color)!important; }
.bg-warning { background: var(--warning-color)!important; }
.bg-secondary { background: var(--border-color)!important; }
.bg-info { background: var(--info-color)!important; }
.text-white { color: #fff!important; }
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-color-tertiary);
  background: var(--bg-color);
  border-radius: 8px;
}
.empty-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-color-secondary);
}
.empty-desc {
  font-size: 15px;
  color: var(--text-color-tertiary);
}
.empty-state-nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--text-color-tertiary);
  background: var(--bg-color);
  border-radius: 8px;
}
.empty-title-nav {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color-tertiary);
  margin-bottom: 8px;
}

/* 左侧项目导航栏缩放样式 */
.project-sidebar {
  width: 25%; /* 对应 col-md-3 */
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.project-sidebar.collapsed {
  width: 80px;
}

.project-sidebar.collapsed .project-name,
.project-sidebar.collapsed .badge {
  display: none;
}

.project-sidebar.collapsed .project-item {
  justify-content: center;
}

.project-sidebar .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-sidebar .header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-icon {
  background: transparent;
  border: none;
  color: #6c757d;
}

.project-name {
  flex-grow: 1;
  margin-left: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}


/* 右侧内容区域响应式样式 */
.project-main-content {
  width: 75%; /* 对应 col-md-9 */
  transition: width 0.3s ease;
}

.project-main-content.expanded {
  width: calc(100% - 80px);
}

/* 分页容器样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.search-box { width: 250px; }
.project-card { background: var(--bg-color); border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 20px; height: 100%; cursor: pointer; transition: all 0.2s; }
.project-card:hover {
  background: var(--hover-color);
  box-shadow: 0 5px 15px rgba(0,0,0,0.18);
}
.project-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.project-card-header h5 { margin: 0; font-size: 18px; font-weight: 600; color: var(--text-color); }
.project-card-body { margin-bottom: 15px; }
.project-card-body p { color: var(--text-color-secondary); margin-bottom: 15px; }
.project-card-stats { display: flex; gap: 15px; margin-bottom: 15px; }
.stat-item { display: flex; align-items: center; color: var(--text-color-tertiary); font-size: 14px; }
.stat-item i { margin-right: 5px; }
.project-card-footer { display: flex; justify-content: space-between; }
</style> 
<template>
  <div class="dashboard-view">
    <!-- 项目健康度和风险预警 -->
    <div class="row mb-4">
      <div class="col-md-6">
        <div class="module-card">
          <div class="module-header">
            <h5 class="module-title">项目健康度</h5>
          </div>
          <div class="health-content">
            <div v-if="isLoading" class="d-flex justify-content-center py-3">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
              </div>
            </div>
            <template v-else>
              <div class="progress mb-2">
                <div class="progress-bar" :class="healthBarClass" role="progressbar" :style="{ width: `${projectHealth}%` }"></div>
              </div>
              <div class="health-desc">
                <p>{{ projectHealthDesc }}</p>
              </div>
            </template>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="module-card">
          <div class="module-header">
            <h5 class="module-title">风险预警</h5>
          </div>
          <div class="risk-content">
            <div v-if="isLoading" class="d-flex justify-content-center py-3">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
              </div>
            </div>
            <template v-else>
              <div v-for="(risk, index) in projectRisks" :key="index" class="risk-item">
                <div class="risk-icon" :class="getRiskIconClass(index)">
                  <i class="bi" :class="getRiskIconName(index)"></i>
                </div>
                <div class="risk-text">{{ risk }}</div>
              </div>
              <div v-if="projectRisks.length === 0" class="text-center text-muted py-3">
                暂无风险预警
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="row mb-4">
      <div class="col-md-3">
        <div class="stats-card bg-success">
          <div class="stats-content">
            <div class="stats-title">已完成任务</div>
            <div class="stats-number">{{ completedTaskCount }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stats-card bg-warning">
          <div class="stats-content">
            <div class="stats-title">待处理任务</div>
            <div class="stats-number">{{ pendingTaskCount }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stats-card bg-primary">
          <div class="stats-content">
            <div class="stats-title">文档数量</div>
            <div class="stats-number">{{ documentCount }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stats-card bg-info">
          <div class="stats-content">
            <div class="stats-title">需求数量</div>
            <div class="stats-number">{{ requirementCount }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="module-card">
      <div class="module-header">
        <h5 class="module-title">最近活动</h5>
      </div>
      <div class="activity-list">
        <div v-if="isLoading" class="d-flex justify-content-center py-3">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
        </div>
        <template v-else>
          <div v-for="item in recentActivities" :key="item.id" class="activity-item">
            <div class="activity-main">
              <p class="activity-title">{{ item.text }}</p>
              <div v-if="item.ai_analysis" class="activity-desc" v-html="marked(item.ai_analysis)"></div>
            </div>
            <div class="activity-time">
              {{ formatTime(item.time) }}
            </div>
          </div>
          <div v-if="recentActivities.length === 0" class="no-activity">
            暂无最近活动
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { formatRelativeTime as formatTime } from '@/utils/date'
import { marked } from 'marked'
import request from '@/utils/request'

const props = defineProps({
  project: Object,
  tasks: Array,
  documents: Array,
  requirements: Array
})

// 加载状态
const isLoading = ref(false)

// 项目健康度数据
const projectHealth = ref(65)
const projectHealthDesc = ref('项目处于功能阶段，各项工作有序开展，存在一定不确定性。')
const projectRisks = ref([])

// 计算统计数据
const completedTaskCount = computed(() => {
  return props.tasks?.filter(task => task.status === 'done').length || 0
})

const pendingTaskCount = computed(() => {
  return props.tasks?.filter(task => task.status !== 'done').length || 0
})

const documentCount = computed(() => {
  return props.documents?.length || 0
})

const requirementCount = computed(() => {
  return props.requirements?.length || 0
})

// 健康度进度条颜色
const healthBarClass = computed(() => {
  if (projectHealth.value >= 80) return 'bg-success'
  if (projectHealth.value >= 60) return 'bg-warning'
  return 'bg-danger'
})

// 获取风险图标样式
function getRiskIconClass(index) {
  // 第一个风险使用成功样式（绿色），其他使用警告样式（黄色）
  return index === 0 ? 'success' : 'warning'
}

// 获取风险图标名称
function getRiskIconName(index) {
  // 第一个风险使用成功图标，其他使用警告图标
  return index === 0 ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'
}

// 加载项目分析数据
async function loadProjectAnalysis() {
  if (!props.project?.id) return
  
  isLoading.value = true
  
  try {
    const res = await request.get(`/api/projects/${props.project.id}/ai_dashboard/`)
    console.log('项目分析数据:', res.data)
    
    // 更新健康度数据
    projectHealth.value = res.data.health || 0
    projectHealthDesc.value = res.data.health_desc || '无法获取项目健康度数据'
    
    // 更新风险数据
    if (Array.isArray(res.data.risks)) {
      projectRisks.value = res.data.risks
    } else {
      projectRisks.value = []
    }
    
  } catch (err) {
    console.error('加载项目分析数据失败:', err)
    // 设置默认值，但不使用硬编码的数据
    projectHealth.value = 0
    projectHealthDesc.value = '无法获取项目健康度数据'
    projectRisks.value = []
  } finally {
    isLoading.value = false
  }
}

// 生成最近活动列表，基于任务、文档和需求数据
const recentActivities = computed(() => {
  const activities = []

  // 任务活动
  props.tasks?.forEach(task => {
    activities.push({
      id: `task-create-${task.id}`,
      text: `${task.creator_name || '未知用户'} 创建了任务 "${task.title}"`,
      time: task.created_at,
      ai_analysis: `任务已创建，优先级${task.priority || '未定'}`
    })
    if (task.status === 'in-progress' && task.updated_at) {
      activities.push({
        id: `task-update-${task.id}`,
        text: `${task.assignee_name || '负责人'} 正在处理任务 "${task.title}"`,
        time: task.updated_at,
        ai_analysis: '任务正在进行中，请关注进度'
      })
    }
  })

  // 文档活动
  props.documents?.forEach(doc => {
    activities.push({
      id: `doc-${doc.id}`,
      text: `${doc.uploader_name || '未知用户'} 上传了文档 "${doc.name}"`,
      time: doc.uploaded_at,
      ai_analysis: doc.analysis
    })
  })

  // 需求活动
  props.requirements?.forEach(req => {
    activities.push({
      id: `req-${req.id}`,
      text: `${req.creator_name || '未知用户'} 创建了需求 "${req.name}"`,
      time: req.created_at,
      ai_analysis: `需求优先级为${req.priority || '未定'}`
    })
  })
  
  // 按时间倒序排序
  return activities.sort((a, b) => new Date(b.time) - new Date(a.time)).slice(0, 10) // 只显示最近10条
})

// 在组件挂载时加载项目分析数据
onMounted(() => {
  loadProjectAnalysis()
})

// 当项目ID变化时重新加载数据
watch(() => props.project?.id, (newId) => {
  if (newId) {
    loadProjectAnalysis()
  }
})

// 当任务、文档或需求数据变化时，重新加载项目分析
watch([
  () => props.tasks, 
  () => props.documents, 
  () => props.requirements
], () => {
  loadProjectAnalysis()
}, { deep: true })

</script>

<style lang="scss" scoped>
.dashboard-view {
  padding: 10px;
}

.module-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
  height: 100%;
}

.module-header {
  margin-bottom: 20px;
}

.module-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.health-content {
  .progress {
    height: 10px;
    background-color: #e9ecef;
    border-radius: 5px;
  }
  .health-desc {
    margin-top: 10px;
    color: #606266;
    font-size: 14px;
  }
}

.risk-content {
  .risk-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 15px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .risk-icon {
      margin-right: 10px;
      margin-top: 2px;
      
      &.success {
        color: #67C23A;
      }
      
      &.warning {
        color: #E6A23C;
      }
    }
    
    .risk-text {
      flex: 1;
      font-size: 14px;
      color: #606266;
    }
  }
}

.stats-card {
  border-radius: 8px;
  padding: 20px;
  height: 100%;
  color: white;
  
  .stats-content {
    .stats-title {
      font-size: 14px;
      opacity: 0.9;
      margin-bottom: 10px;
    }
    
    .stats-number {
      font-size: 32px;
      font-weight: bold;
    }
  }
}

.activity-list {
  .activity-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 15px 0;
    border-bottom: 1px solid #EBEEF5;

    &:last-child {
      border-bottom: none;
    }
  }

  .activity-main {
    flex: 1;
    .activity-title {
      font-size: 15px;
      color: #303133;
      margin: 0 0 5px 0;
    }
    .activity-desc {
      font-size: 14px;
      color: #888;
      line-height: 1.6;

      :deep(p) {
        margin: 0 0 8px 0;
      }
      :deep(strong) {
        font-weight: bold;
        color: #555;
      }
      :deep(ul) {
        padding-left: 20px;
        margin: 0;
      }
      :deep(li) {
        margin-bottom: 4px;
      }
    }
  }

  .activity-time {
    font-size: 13px;
    color: #909399;
    width: 100px;
    text-align: right;
  }

  .no-activity {
    text-align: center;
    color: #909399;
    padding: 20px;
  }
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin-right: -15px;
  margin-left: -15px;
}

.col-md-3 {
  flex: 0 0 25%;
  max-width: 25%;
  padding-right: 15px;
  padding-left: 15px;
}

.col-md-6 {
  flex: 0 0 50%;
  max-width: 50%;
  padding-right: 15px;
  padding-left: 15px;
}

.mb-4 {
  margin-bottom: 1.5rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.spinner-border {
  display: inline-block;
  width: 2rem;
  height: 2rem;
  border: 0.25em solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spinner-border .75s linear infinite;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@keyframes spinner-border {
  to { transform: rotate(360deg); }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .col-md-3, .col-md-6 {
    flex: 0 0 100%;
    max-width: 100%;
    margin-bottom: 15px;
  }
}
</style>

<style lang="scss" scoped>
[data-theme="dark"] {
  .dashboard-view, .module-card {
    background-color: var(--el-bg-color-page) !important;
    color: var(--el-text-color-primary) !important;
    border: 1px solid var(--el-border-color-light);
  }

  .module-title, .health-desc p {
    color: var(--el-text-color-primary) !important;
  }

  .risk-item, .activity-item {
    border-bottom-color: var(--el-border-color-light) !important;
  }
  
  .risk-text, .activity-main .activity-title, .activity-time {
    color: var(--el-text-color-secondary) !important;
  }
  
  .no-activity {
    color: var(--el-text-color-secondary);
  }

  /* 覆盖统计卡片的背景色 */
  .stats-card {
    &.bg-success { background-color: #28a745 !important; }
    &.bg-warning { background-color: #ffc107 !important; }
    &.bg-primary { background-color: #007bff !important; }
    &.bg-info { background-color: #17a2b8 !important; }
    
    .stats-title, .stats-number {
      color: #fff !important;
    }
  }

  .progress {
    background-color: var(--el-fill-color-light);
  }
}
</style>
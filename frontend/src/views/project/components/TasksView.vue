<template>
  <div class="module-card modern-tasks">
    <div class="module-header">
      <h5 class="module-title">任务管理</h5>
      <div class="btn-group">
        <el-button type="primary" size="default" round @click="handleAddTask">新建任务</el-button>
        <el-button type="info" size="default" round @click="refreshAllTaskAiAnalysis" :loading="refreshingAi">刷新分析</el-button>
      </div>
    </div>
    <!-- 顶部搜索和筛选 -->
    <div class="task-filters modern-filters">
      <el-input v-model="search" placeholder="搜索任务..." clearable class="filter-input" />
      <el-select v-model="filterAssignee" placeholder="负责人" clearable class="filter-select">
        <el-option label="全部" value="" />
        <el-option v-for="member in projectMembers" :key="member.id" :label="member.name" :value="member.name" />
      </el-select>
      <el-select v-model="filterPriority" placeholder="优先级" clearable class="filter-select">
        <el-option label="全部" value="" />
        <el-option label="高" value="高" />
        <el-option label="中" value="中" />
        <el-option label="低" value="低" />
      </el-select>
    </div>
    <!-- 只保留看板视图 -->
    <div class="kanban-view modern-kanban">
      <div class="row">
        <div class="col-md-4" v-for="col in kanban" :key="col.name">
          <div class="card modern-card">
            <div class="card-header modern-card-header kanban-col-header">
              <span class="kanban-col-dot" :class="col.name"></span>
              <h6 class="mb-0">{{ col.name }} <el-badge :value="filteredTasks(col.tasks).length" class="kanban-badge" /></h6>
            </div>
            <div class="card-body task-list">
              <el-empty v-if="filteredTasks(col.tasks).length === 0" description="暂无任务" :image-size="60" />
              <div v-else v-for="task in filteredTasks(col.tasks)" :key="task.title" class="task-card modern-task-card">
                <div class="task-body" @click="openDetail(task)">
                  <div class="task-header">
                    <h6 class="mb-0 task-title-main">{{ task.title }}</h6>
                    <el-tag :type="task.priorityType" size="small">{{ task.priority }}</el-tag>
                  </div>
                  <div class="task-meta-row">
                    <span v-if="task.assignee && task.assignee.user"><el-icon><UserFilled /></el-icon> {{ task.assignee.user.username }}</span>
                    <span v-if="task.dueDate"><el-icon><Calendar /></el-icon> {{ task.dueDate }}</span>
                    <div class="task-progress-row">
                      <el-progress :percentage="getTaskCompletionPercentage(task)" :show-text="false" style="width:60px;height:4px;display:inline-block;margin:0 8px;" />
                      <span class="progress-text">{{ getTaskCompletionText(task) }}</span>
                    </div>
                  </div>
                  <div class="task-tags">
                    <el-tag v-for="tag in task.tags" :key="tag" size="small">{{ tag }}</el-tag>
                  </div>
                  <p class="task-description">{{ task.description }}</p>
                  <div class="ai-analysis-toggle" @click.stop="task._showAI = !task._showAI">
                    <el-icon style="vertical-align:middle;"><ChatDotRound /></el-icon>
                    <span style="font-size:12px;color:#888;cursor:pointer;">AI分析 {{ task._showAI ? '▲' : '▼' }}</span>
                    <el-button size="small" type="link" @click.stop="getTaskAiAnalysis(task.id)" :loading="task._aiLoading">
                      <el-icon><Refresh /></el-icon>
                    </el-button>
                  </div>
                  <div v-if="isCurrentUser(task.assignee?.user?.id)" style="margin-top:6px;">
                    <el-button size="small" @click.stop="openEditTask(task)">编辑</el-button>
                    <el-button size="small" type="danger" @click.stop="confirmDeleteTask(task)">删除</el-button>
                  </div>
                  <transition name="fade">
                    <div v-if="task._showAI" class="ai-analysis modern-ai-analysis">
                      <div v-if="!task.ai || task.ai.length === 0" class="text-center py-2">
                        <span class="text-muted">暂无AI分析</span>
                      </div>
                      <ul class="mb-0" v-else>
                        <li v-for="r in processAIContent(task.ai)" :key="r" v-html="formatMarkdown(r)"></li>
                      </ul>
                    </div>
                  </transition>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 新建/编辑任务弹窗 -->
    <el-dialog v-model="showAddTask" title="新建任务" width="420px" class="modern-dialog">
      <el-form :model="newTask" :rules="formRules" ref="addTaskFormRef" label-width="80px" class="modern-form">
        <el-form-item label="任务名称" prop="title" required>
          <el-input v-model="newTask.title" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="负责人" prop="assignee" required>
          <el-select v-model="newTask.assignee" placeholder="请选择负责人">
            <el-option 
              v-for="member in projectMembers" 
              :key="member.id" 
              :label="member.name" 
              :value="member.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority" required>
          <el-select v-model="newTask.priority" placeholder="请选择优先级">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期" prop="dueDate" required>
          <el-date-picker v-model="newTask.dueDate" value-format="YYYY-MM-DD" placeholder="请选择截止日期" />
        </el-form-item>
        <el-form-item label="描述" prop="description" required>
          <el-input type="textarea" v-model="newTask.description" placeholder="请输入任务描述" />
        </el-form-item>
        <el-form-item label="标签" prop="tags" required>
          <el-input v-model="newTask.tags" placeholder="逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTask = false">取消</el-button>
        <el-button type="primary" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>
    <!-- 任务详情弹窗 -->
    <el-dialog v-model="showDetail" title="任务详情" width="480px" class="modern-dialog">
      <div v-if="currentTask">
        <h5 style="font-weight:600;">{{ currentTask.title }}</h5>
        <div style="margin:10px 0;display:flex;gap:16px;align-items:center;">
          <el-tag :type="currentTask.priorityType" size="small">{{ currentTask.priority }}</el-tag>
          <span>负责人：{{ currentTask.assignee && currentTask.assignee.user ? currentTask.assignee.user.username : '' }}</span>
          <span>截止：{{ currentTask.dueDate }}</span>
        </div>
        <div style="margin-bottom:10px;">描述：{{ currentTask.description }}</div>
        <div style="margin-bottom:10px;">标签：<el-tag v-for="tag in currentTask.tags" :key="tag" size="small">{{ tag }}</el-tag></div>
        <div style="margin-bottom:10px;">进度：<el-progress :percentage="getTaskCompletionPercentage(currentTask)" /></div>
        <div class="ai-analysis modern-ai-analysis">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <small class="text-muted">AI分析：</small>
            <el-button size="small" type="link" @click="getTaskAiAnalysis(currentTask.id)" :loading="currentTask._aiLoading">
              <el-icon><Refresh /></el-icon> 刷新分析
            </el-button>
          </div>
          <div v-if="!currentTask.ai || currentTask.ai.length === 0" class="text-center py-2">
            <span class="text-muted">暂无AI分析</span>
          </div>
          <ul class="mb-0" v-else>
            <li v-for="r in processAIContent(currentTask.ai)" :key="r" v-html="formatMarkdown(r)"></li>
          </ul>
        </div>
        <div class="member-completion-list">
          <div v-if="currentTask.status === 'todo' || currentTask.status === '待处理'">
            <div v-for="member in projectMembers" :key="member.id" class="member-item">
              <span>{{ member.name }}</span>
              <el-tag type="info" size="small">未完成</el-tag>
            </div>
          </div>
          <div v-else-if="!taskCompletions[currentTask?.id]?.members || taskCompletions[currentTask?.id]?.members.length === 0">
            <div v-for="member in projectMembers" :key="member.id" class="member-item">
              <span>{{ member.name }}</span>
              <el-button 
                v-if="isCurrentUser(member.userId)" 
                type="primary" 
                size="small" 
                @click="markCompleteForMember(currentTask.id, member.id)"
              >完成</el-button>
              <el-tag v-else type="info" size="small">未完成</el-tag>
            </div>
          </div>
          <div v-else v-for="m in taskCompletions[currentTask.id]?.members || []" :key="m.id" class="member-item">
            <span>{{ m.name }}</span>
            <el-tag v-if="m.completed" type="success" size="small">已完成</el-tag>
            <el-button 
              v-else-if="isCurrentUser(m.userId)" 
              type="primary" 
              size="small" 
              @click="markComplete(currentTask.id, m.id)"
            >完成</el-button>
            <el-tag v-else type="info" size="small">未完成</el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetail=false">关闭</el-button>
        <el-button v-if="isCurrentUser(currentTask?.assignee?.user?.id)" @click="openEditTask(currentTask)" type="primary">编辑</el-button>
        <el-button v-if="isCurrentUser(currentTask?.assignee?.user?.id)" @click="confirmDeleteTask(currentTask)" type="danger">删除</el-button>
      </template>
    </el-dialog>
    <!-- 编辑任务弹窗 -->
    <el-dialog v-model="showEditTask" title="编辑任务" width="420px" class="modern-dialog">
      <el-form :model="editTask" :rules="formRules" ref="editTaskFormRef" label-width="80px" class="modern-form">
        <el-form-item label="任务名称" prop="title" required>
          <el-input v-model="editTask.title" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority" required>
          <el-select v-model="editTask.priority" placeholder="请选择优先级">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期" prop="dueDate" required>
          <el-date-picker v-model="editTask.dueDate" value-format="YYYY-MM-DD" placeholder="请选择截止日期" />
        </el-form-item>
        <el-form-item label="描述" prop="description" required>
          <el-input type="textarea" v-model="editTask.description" placeholder="请输入任务描述" />
        </el-form-item>
        <el-form-item label="标签" prop="tags" required>
          <el-input v-model="editTask.tags" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="状态" prop="status" required>
          <el-select v-model="editTask.status" placeholder="请选择状态">
            <el-option label="待处理" value="todo" />
            <el-option label="进行中" value="in-progress" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditTask = false">取消</el-button>
        <el-button type="primary" @click="saveEditTask">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { UserFilled, Calendar, ChatDotRound, Refresh } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

// 获取当前登录用户信息
const currentUser = ref(null)
try {
  currentUser.value = JSON.parse(localStorage.getItem('user') || '{}')
  console.log('当前登录用户:', currentUser.value)
} catch (e) {
  console.error('解析用户信息失败:', e)
}

const props = defineProps({
  project: {
    type: Object,
    default: () => ({})
  },
  members: {
    type: Array,
    default: () => []
  }
})

// 直接使用props.members，无需再定义本地的projectMembers
const projectMembers = computed(() => props.members)

const search = ref('')
const filterAssignee = ref('')
const filterPriority = ref('')
const showAddTask = ref(false)
const showDetail = ref(false)
const currentTask = ref(null)
const newTask = ref({
  title: '',
  assignee: '',
  priority: '中',
  dueDate: '',
  description: '',
  tags: '',
  status: 'todo',
  progress: 0,
  completed: 0,
  total: 1
})

// 所有任务数据
const tasks = ref([])

// 新增：任务完成进度数据
const taskCompletions = ref({}) // { [taskId]: { total, completed, members: [{id, name, completed}] } }

const kanban = computed(() => [
  { name: '待处理', tasks: tasks.value.filter(t => t.status === 'todo' || t.status === '待处理') },
  { name: '进行中', tasks: tasks.value.filter(t => t.status === 'in-progress' || t.status === '进行中') },
  { name: '已完成', tasks: tasks.value.filter(t => t.status === 'done' || t.status === '已完成') }
])

const refreshingAi = ref(false)

// 表单引用
const addTaskFormRef = ref(null)
const editTaskFormRef = ref(null)

// 表单验证规则
const formRules = {
  title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  assignee: [{ required: true, message: '请选择负责人', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  dueDate: [{ required: true, message: '请选择截止日期', trigger: 'change' }],
  description: [{ required: true, message: '请输入任务描述', trigger: 'blur' }],
  tags: [{ required: true, message: '请输入标签', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

// 添加过滤条件变化监听
watch([search, filterAssignee, filterPriority], () => {
  // 当过滤条件变化时，刷新任务列表
}, { deep: true });

// 获取任务列表
function fetchTasks() {
  if (!props.project || !props.project.id) return
  request.get(`/api/tasks/?project=${props.project.id}`).then(res => {
    // 统一转换任务字段
    const rawTasks = Array.isArray(res.data) ? res.data : (res.data.data || [])
    tasks.value = rawTasks.map(t => ({
      ...t,
      dueDate: t.due_date || t.dueDate || '',
      priority: t.priority === 'high' ? '高' : t.priority === 'low' ? '低' : t.priority === 'medium' ? '中' : (t.priority || ''),
      priorityType: t.priority === 'high' || t.priority === '高' ? 'danger' : t.priority === 'low' || t.priority === '低' ? 'info' : 'warning',
    }))
    // 自动AI分析
    tasks.value.forEach(task => {
      if (!task.ai || task.ai.length === 0) {
        getTaskAiAnalysis(task.id)
      }
    })
  })
}

// 获取任务完成进度
function fetchTaskCompletions(taskId) {
  if (!taskId) return;
  request.get(`/api/task-completions/?task=${taskId}`).then(res => {
    const completionRecords = Array.isArray(res.data) ? res.data : (res.data.data || []);
    
    // 创建一个以用户ID为键的完成状态映射，方便快速查找
    const completionMap = new Map();
    completionRecords.forEach(record => {
      // 兼容多种可能的后端返回结构
      const userId = record.user?.id || record.member?.user?.id || record.member_id;
      if (userId) {
        completionMap.set(userId, {
          completed: record.completed,
          completionId: record.id
        });
      }
    });

    // 以当前的项目成员列表 (props.members) 为唯一数据源
    const currentProjectMembers = projectMembers.value;

    // 基于当前项目成员构建任务的最终成员列表，并附加其完成状态
    const finalMembersForTask = currentProjectMembers.map(member => {
      const completionData = completionMap.get(member.id);
      return {
        id: member.id,          // 确保ID是用户ID
        name: member.name,
        completed: completionData ? completionData.completed : false,
        completionId: completionData ? completionData.completionId : undefined,
        userId: member.id       // 明确userId字段
      };
    });

    taskCompletions.value[taskId] = {
      total: finalMembersForTask.length,
      completed: finalMembersForTask.filter(m => m.completed).length,
      members: finalMembersForTask
    };
  }).catch(err => {
    console.error(`获取任务[${taskId}]完成进度失败:`, err);
    // 如果API调用失败，则将所有当前项目成员显示为未完成
    taskCompletions.value[taskId] = {
      total: projectMembers.value.length,
      completed: 0,
      members: projectMembers.value.map(m => ({
        id: m.id,
        name: m.name,
        completed: false,
        userId: m.id
      }))
    };
  });
}

// 新增：获取任务完成百分比
function getTaskCompletionPercentage(task) {
  if (!task || !task.id) return 0
  
  // 如果有后端数据，使用后端数据
  if (taskCompletions.value[task.id]?.total) {
    return Math.round(100 * (taskCompletions.value[task.id]?.completed || 0) / taskCompletions.value[task.id]?.total)
  }
  
  // 否则使用默认值
  return 0
}

// 新增：获取任务完成文本
function getTaskCompletionText(task) {
  if (!task || !task.id) {
    // 如果没有任务，显示默认值
    return `0/${projectMembers.value.length || 1}人完成`
  }
  
  // 如果有后端数据，使用后端数据
  if (taskCompletions.value[task.id]) {
    return `${taskCompletions.value[task.id]?.completed || 0}/${taskCompletions.value[task.id]?.total || projectMembers.value.length || 1}人完成`
  }
  
  // 否则使用默认值
  return `0/${projectMembers.value.length || 1}人完成`
}

// 在任务列表加载后，批量获取所有任务的完成进度
watch(tasks, (val) => {
  (val || []).forEach(task => fetchTaskCompletions(task.id))
}, { immediate: true })

// 新增：为没有 TaskCompletion 记录的成员标记完成
function markCompleteForMember(taskId, memberId) {
  if (!taskId || !memberId) return
  
  console.log('为新成员标记任务完成:', taskId, memberId)
  
  // 创建新的 TaskCompletion 记录
  request.post('/api/task-completions/', {
    task: taskId,
    member_id: memberId,
    completed: true,
    completed_at: new Date().toISOString()
  }).then(() => {
    ElMessage.success('已标记为完成')
    // 更新本地状态
    if (!taskCompletions.value[taskId]) {
      // 初始化任务完成状态，使用项目成员总数
      taskCompletions.value[taskId] = {
        total: projectMembers.value.length,
        completed: 1,
        members: projectMembers.value.map(m => ({
          id: m.id,
          name: m.name,
          completed: m.id === memberId,
          completionId: undefined
        }))
      }
    } else {
      // 更新已有的任务完成状态
      taskCompletions.value[taskId].completed++
      // 确保 members 数组包含所有项目成员
      const existingMemberIds = taskCompletions.value[taskId].members.map(m => m.id)
      projectMembers.value.forEach(m => {
        if (!existingMemberIds.includes(m.id)) {
          taskCompletions.value[taskId].members.push({
            id: m.id,
            name: m.name,
            completed: m.id === memberId,
            completionId: undefined
          })
        }
      })
      // 更新当前成员的完成状态
      const member = taskCompletions.value[taskId].members.find(m => m.id === memberId)
      if (member) {
        member.completed = true
      }
      // 确保总数正确
      taskCompletions.value[taskId].total = taskCompletions.value[taskId].members.length
    }
    
    // 重新获取最新数据
    fetchTaskCompletions(taskId)
    // 检查是否所有成员都完成，自动设为已完成
    const tc = taskCompletions.value[taskId]
    if (tc && tc.completed === tc.total && tc.total > 0) {
      updateTaskStatusToDone(taskId)
    }
  }).catch(err => {
    console.error('创建任务完成记录失败:', err)
    ElMessage.error('操作失败，请重试')
  })
}

// 成员点击"完成"按钮
function markComplete(taskId, memberId) {
  const tc = (taskCompletions.value[taskId]?.members || []).find(m => m.id === memberId)
  if (!tc || tc.completed) return
  
  console.log('标记任务完成:', taskId, memberId, tc.completionId)
  
  // 立即更新本地状态，提供即时反馈
  tc.completed = true
  taskCompletions.value[taskId].completed++
  
  // 确保总数正确
  taskCompletions.value[taskId].total = Math.max(
    taskCompletions.value[taskId].total,
    taskCompletions.value[taskId].members.length,
    projectMembers.value.length
  )
  
  // 然后发送请求到后端
  request.patch(`/api/task-completions/${tc.completionId}/`, { 
    completed: true, 
    completed_at: new Date().toISOString() 
  }).then(() => {
    ElMessage.success('已标记为完成')
    // 重新获取最新数据
    fetchTaskCompletions(taskId)
    // 检查是否所有成员都完成，自动设为已完成
    const tcc = taskCompletions.value[taskId]
    if (tcc && tcc.completed === tcc.total && tcc.total > 0) {
      updateTaskStatusToDone(taskId)
    }
  }).catch(err => {
    console.error('标记完成失败:', err)
    ElMessage.error('操作失败，但界面已更新')
    // 失败时不回滚本地状态，保持用户体验
  })
}

// 新增：自动将任务状态设为已完成
function updateTaskStatusToDone(taskId) {
  // 本地更新
  const task = tasks.value.find(t => t.id === taskId)
  if (task) task.status = 'done'
  // 后端更新
  request.patch(`/api/tasks/${taskId}/`, { status: 'done' })
}

// 新建任务
function saveTask() {
  if (!addTaskFormRef.value) {
    console.error('表单引用不存在')
    return
  }

  addTaskFormRef.value.validate(valid => {
    if (!valid) {
      ElMessage.error('请填写所有必填项')
      return
    }

    // 直接用assignee为ProjectMember的id
    const assignee_id = newTask.value.assignee
    if (!assignee_id) {
      ElMessage.error('负责人无效')
      return
    }
    // 确保tags是字符串而不是数组
    const tagsValue = typeof newTask.value.tags === 'string' 
      ? newTask.value.tags 
      : (Array.isArray(newTask.value.tags) ? newTask.value.tags.join(',') : '');
      
    const payload = {
      project: props.project.id,
      title: newTask.value.title,
      description: newTask.value.description,
      assignee_id: assignee_id,
      due_date: newTask.value.dueDate,
      priority: newTask.value.priority === '高' ? 'high' : (newTask.value.priority === 'low' ? 'low' : 'medium'),
      status: 'todo',
      tags: tagsValue
    }
    request.post('/api/tasks/', payload).then(() => {
      ElMessage.success('任务创建成功')
      showAddTask.value = false
      fetchTasks()
    }).catch(() => {
      ElMessage.error('任务创建失败')
    })
  })
}

// 过滤
function filteredTasks(taskArr) {
  return taskArr.filter(t => {
    const matchSearch = !search.value || t.title.includes(search.value) || (t.description && t.description.includes(search.value))
    const matchAssignee = !filterAssignee.value || (t.assignee && t.assignee.user && t.assignee.user.username === filterAssignee.value)
    // 优先级筛选：直接用中文匹配
    const matchPriority = !filterPriority.value || t.priority === filterPriority.value
    return matchSearch && matchAssignee && matchPriority
  })
}

// 详情弹窗
function openDetail(task) {
  // 详情弹窗也需转换 priorityType
  currentTask.value = {
    ...task,
    priorityType: task.priorityType || (task.priority === '高' || task.priority === 'high' ? 'danger' : task.priority === '低' || task.priority === 'low' ? 'info' : 'warning'),
    // 动态获取AI分析结果，而不是使用静态数据
    ai: task.ai || []
  }
  // 显示详情弹窗
  showDetail.value = true
  // 如果没有AI分析数据，自动获取
  if (!task.ai || task.ai.length === 0) {
    getTaskAiAnalysis(task.id)
  }
}

// 新增：获取任务AI分析
function getTaskAiAnalysis(taskId) {
  if (!taskId) return
  
  console.log('获取任务AI分析:', taskId)
  
  // 设置对应任务的加载状态
  const task = tasks.value.find(t => t.id === taskId)
  if (task) {
    task._aiLoading = true
  }
  
  request.get(`/api/tasks/${taskId}/ai_analysis/`).then(res => {
    let suggestions = res.data?.suggestions || []
    
    // 如果后端返回的数据不是数组格式，确保转换为数组
    if (!Array.isArray(suggestions)) {
      suggestions = [suggestions.toString()]
    }
    
    // 确保建议包含"专业分析"和"建议"两个部分
    const formattedSuggestions = formatAiAnalysisData(suggestions)
    
    // 更新当前打开的任务详情
    if (currentTask.value && currentTask.value.id === taskId) {
      currentTask.value.ai = formattedSuggestions
    }
    
    // 更新任务列表中的任务
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.ai = formattedSuggestions
    }
    
    console.log('任务AI分析结果:', formattedSuggestions)
  }).catch(err => {
    console.error('获取任务AI分析失败:', err)
    ElMessage.error('获取任务AI分析失败')
  }).finally(() => {
    // 清除加载状态
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task._aiLoading = false
    }
  })
}

// 新建任务弹窗
function handleAddTask() {
  newTask.value = {
    title: '',
    assignee: '',
    priority: '中',
    dueDate: '',
    description: '',
    tags: '',
    status: 'todo',
    progress: 0,
    completed: 0,
    total: 1
  }
  showAddTask.value = true
}

// 监听项目变化自动拉取任务和成员
watch(() => props.project, (newProject) => {
  if (newProject && newProject.id) {
    // 如果父组件传递了成员数据，优先使用
    if (props.members && props.members.length > 0) {
      projectMembers.value = props.members
      console.log('使用父组件传递的成员数据:', projectMembers.value)
    } else {
      fetchProjectMembers(newProject.id)
    }
    fetchTasks()
  }
}, { immediate: true })

// 监听父组件传递的成员数据变化
watch(() => props.members, (newMembers) => {
  if (newMembers && newMembers.length > 0) {
    projectMembers.value = newMembers
    console.log('成员数据更新:', projectMembers.value)
  }
}, { immediate: true })

onMounted(() => {
  if (props.project && props.project.id) {
    // 如果父组件传递了成员数据，优先使用
    if (props.members && props.members.length > 0) {
      projectMembers.value = props.members
      console.log('使用父组件传递的成员数据:', projectMembers.value)
    } else {
      fetchProjectMembers(props.project.id)
    }
    fetchTasks()
  }
})

// 获取项目成员（ProjectMember 列表，带 user 信息）
function fetchProjectMembers(projectId) {
  if (!projectId) return
  request.get(`/api/project-members/?project=${projectId}`).then(res => {
    // 结构：[{id: ProjectMember.id, user: {id, username, ...}, ...}]
    if (Array.isArray(res.data)) {
      projectMembers.value = res.data.map(pm => ({
        id: pm.id,
        name: pm.user?.username || pm.user?.email || '未命名成员',
        userId: pm.user?.id
      }))
    } else {
      projectMembers.value = []
    }
    console.log('拉取到的项目成员（ProjectMember）:', projectMembers.value)
  }).catch(err => {
    console.error('获取项目成员失败', err)
    projectMembers.value = []
  })
}

// 编辑相关逻辑
const showEditTask = ref(false)
const editTask = ref(null)
function openEditTask(task) {
  editTask.value = { ...task, status: task.status || 'todo' }
  showEditTask.value = true
}
function saveEditTask() {
  if (!editTaskFormRef.value) {
    console.error('表单引用不存在')
    return
  }

  editTaskFormRef.value.validate(valid => {
    if (!valid) {
      ElMessage.error('请填写所有必填项')
      return
    }
    
    // 确保tags是字符串而不是数组
    let tagsValue = '';
    if (typeof editTask.value.tags === 'string') {
      tagsValue = editTask.value.tags;
    } else if (Array.isArray(editTask.value.tags)) {
      tagsValue = editTask.value.tags.join(',');
    }
    
    const payload = {
      id: editTask.value.id,
      title: editTask.value.title,
      description: editTask.value.description || '',
      priority: editTask.value.priority === '高' ? 'high' : (editTask.value.priority === '低' ? 'low' : 'medium'),
      due_date: editTask.value.dueDate || '',
      tags: tagsValue,
      status: editTask.value.status || 'todo',
    }
    request.patch(`/api/tasks/${editTask.value.id}/`, payload).then(() => {
      ElMessage.success('任务更新成功')
      showEditTask.value = false
      fetchTasks()
      showDetail.value = false
    }).catch(() => {
      ElMessage.error('任务更新失败')
    })
  })
}

// 删除相关逻辑
function confirmDeleteTask(task) {
  ElMessageBox.confirm('确定要删除该任务吗？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    request.delete(`/api/tasks/${task.id}/`).then(() => {
      ElMessage.success('任务已删除')
      fetchTasks()
      showDetail.value = false
    })
  })
}

function refreshAllTaskAiAnalysis() {
  if (!tasks.value.length) return
  refreshingAi.value = true
  let finished = 0
  const total = tasks.value.length
  tasks.value.forEach(task => {
    task._aiLoading = true
    request.get(`/api/tasks/${task.id}/ai_analysis/`).then(res => {
      let suggestions = res.data?.suggestions || []
      
      // 如果后端返回的数据不是数组格式，确保转换为数组
      if (!Array.isArray(suggestions)) {
        suggestions = [suggestions.toString()]
      }
      
      // 确保建议包含"专业分析"和"建议"两个部分
      task.ai = formatAiAnalysisData(suggestions)
    }).catch(() => {
      task.ai = []
    }).finally(() => {
      task._aiLoading = false
      finished++
      if (finished === total) {
        refreshingAi.value = false
        ElMessage.success('AI分析完成')
      }
    })
  })
}

// 处理AI内容，确保完整显示，包括建议部分
function processAIContent(aiItems) {
  if (!aiItems || !Array.isArray(aiItems)) return []
  
  // 检查是否有"建议:"但没有跟随内容的情况
  let hasIncompleteData = false
  if (aiItems.length > 0) {
    const lastItem = aiItems[aiItems.length - 1]
    if (typeof lastItem === 'string' && (lastItem.trim() === '建议:' || lastItem.trim() === '建议：')) {
      hasIncompleteData = true
    }
  }
  
  // 如果发现不完整数据，则取消字符限制
  if (hasIncompleteData) {
    return aiItems
  }
  
  // 根据具体情况重组内容，确保分析和建议都能完整显示
  // 尝试将数组重新组合为更有逻辑的结构
  const result = []
  let currentCategory = ''
  let tempItems = []
  
  for (const item of aiItems) {
    if (typeof item !== 'string') {
      result.push(item)
      continue
    }
    
    // 检测新的分类标题
    if (item.includes('专业分析:') || item.includes('专业分析：')) {
      if (currentCategory && tempItems.length) {
        result.push(`${currentCategory}${tempItems.join(' ')}`)
      }
      currentCategory = '专业分析: '
      tempItems = []
    } 
    else if (item.includes('建议:') || item.includes('建议：')) {
      if (currentCategory && tempItems.length) {
        result.push(`${currentCategory}${tempItems.join(' ')}`)
      }
      currentCategory = '建议: '
      tempItems = []
    }
    // 如果是以"-"或"•"开头的列表项，单独保留
    else if (item.trim().startsWith('-') || item.trim().startsWith('•')) {
      result.push(item)
    }
    // 其他情况添加到当前分类
    else {
      tempItems.push(item)
    }
  }
  
  // 添加最后一个分类的内容
  if (currentCategory && tempItems.length) {
    result.push(`${currentCategory}${tempItems.join(' ')}`)
  }
  
  return result.length ? result : aiItems
}

// 将Markdown格式化为HTML显示
function formatMarkdown(text) {
  if (!text) return ''
  try {
    // 简单处理一些markdown语法
    // 加粗
    let result = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // 斜体
    result = result.replace(/\*(.*?)\*/g, '<em>$1</em>')
    // 行内代码
    result = result.replace(/`(.*?)`/g, '<code>$1</code>')
    // 超链接
    result = result.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
    
    // 处理以"-"开头的列表项，确保正确显示
    if (result.trim().startsWith('-') || result.trim().startsWith('•')) {
      result = result.replace(/^[\s-•]+/, '')
      result = `<span class="list-bullet">•</span> ${result}`
    }
    
    // 处理冒号后的内容，如果是分类标题
    if (result.includes('专业分析:') || result.includes('专业分析：')) {
      result = `<strong class="analysis-title">专业分析:</strong> ${result.replace(/专业分析[:：]\s*/, '')}`
    }
    else if (result.includes('建议:') || result.includes('建议：')) {
      result = `<strong class="suggestion-title">建议:</strong> ${result.replace(/建议[:：]\s*/, '')}`
    }
    
    return result
  } catch (e) {
    console.error('Markdown格式化错误:', e)
    return text
  }
}

// 将AI返回的分析内容格式化为标准结构
function formatAiAnalysisData(items) {
  if (!items || !items.length) return []
  
  // 检查原始内容
  const originalText = items.join(' ');
  
  // 检查是否已经包含专业分析和建议两个部分
  const hasAnalysis = items.some(item => 
    typeof item === 'string' && 
    (item.includes('专业分析:') || item.includes('专业分析：'))
  )
  
  const hasSuggestion = items.some(item => 
    typeof item === 'string' && 
    (item.includes('建议:') || item.includes('建议：'))
  )
  
  // 如果最后一项是"建议:"且没有内容，添加默认建议
  if (items.length > 0) {
    const lastItem = items[items.length - 1];
    if (typeof lastItem === 'string' && 
        (lastItem.trim() === '建议:' || lastItem.trim() === '建议：')) {
      // 添加默认建议
      items.push('- 建议进一步明确任务的细节和具体要求')
      items.push('- 考虑提前安排资源，确保任务按时完成')
    }
  }
  
  // 完全没有建议部分，则添加建议部分
  if (!hasSuggestion) {
    items.push('建议:')
    items.push('- 建议进一步明确任务的细节和具体要求')
    items.push('- 考虑提前安排资源，确保任务按时完成')
  }
  
  // 完全没有分析部分，则添加分析部分
  if (!hasAnalysis && !originalText.includes('紧急性') && !originalText.includes('重要性')) {
    // 在最前面添加分析部分
    items.unshift('- 根据任务描述进行初步分析，可能需要更多信息')
    items.unshift('专业分析:')
  }
  
  // 如果有分析和建议标记，但格式不规范，重新组织内容
  if (hasAnalysis || hasSuggestion) {
    // 重组内容为标准格式
    const result = [];
    let currentSection = null;
    let hasAddedAnalysisItems = false;
    let hasAddedSuggestionItems = false;
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (typeof item !== 'string') {
        result.push(item);
        continue;
      }
      
      // 检测章节标题
      if (item.includes('专业分析:') || item.includes('专业分析：')) {
        currentSection = 'analysis';
        result.push(item);
        hasAddedAnalysisItems = false;
        continue;
      } else if (item.includes('建议:') || item.includes('建议：')) {
        currentSection = 'suggestion';
        result.push(item);
        hasAddedSuggestionItems = false;
        continue;
      }
      
      // 添加前缀并分类处理
      if (currentSection === 'analysis') {
        if (!item.trim().startsWith('-') && !item.trim().startsWith('•')) {
          result.push(`- ${item}`);
        } else {
          result.push(item);
        }
        hasAddedAnalysisItems = true;
      } else if (currentSection === 'suggestion') {
        if (!item.trim().startsWith('-') && !item.trim().startsWith('•')) {
          result.push(`- ${item}`);
        } else {
          result.push(item);
        }
        hasAddedSuggestionItems = true;
      } else {
        result.push(item);
      }
    }
    
    // 确保每个部分都有内容
    if (currentSection === 'analysis' && !hasAddedAnalysisItems) {
      result.push('- 根据任务描述进行初步分析，可能需要更多信息');
    } else if (currentSection === 'suggestion' && !hasAddedSuggestionItems) {
      result.push('- 建议进一步明确任务的细节和具体要求');
      result.push('- 考虑提前安排资源，确保任务按时完成');
    }
    
    return result;
  }
  
  // 如果没有特殊特征，就简单分为分析和建议两部分
  const analysisItems = [];
  const suggestionItems = [];
  
  // 分类项目
  items.forEach(item => {
    if (!item || typeof item !== 'string') return;
    
    if (item.includes('紧急性') || item.includes('重要性') || item.includes('可行性')) {
      analysisItems.push(item);
    } else if (!item.includes('专业分析') && !item.includes('建议:') && !item.includes('建议：')) {
      suggestionItems.push(item);
    }
  });
  
  // 如果分类后没有足够的建议，添加默认建议
  if (suggestionItems.length === 0) {
    suggestionItems.push('建议进一步明确任务的细节和具体要求');
    suggestionItems.push('考虑提前安排资源，确保任务按时完成');
  }
  
  // 构造结果
  const result = [];
  
  result.push('专业分析:');
  if (analysisItems.length > 0) {
    result.push(...analysisItems.map(item => item.trim().startsWith('-') ? item : `- ${item}`));
  } else {
    result.push('- 根据任务描述进行初步分析，可能需要更多信息');
  }
  
  result.push('建议:');
  if (suggestionItems.length > 0) {
    result.push(...suggestionItems.map(item => item.trim().startsWith('-') ? item : `- ${item}`));
  } else {
    result.push('- 建议进一步明确任务的细节和具体要求');
    result.push('- 考虑提前安排资源，确保任务按时完成');
  }
  
  return result;
}

// 新增：判断是否为当前登录用户
function isCurrentUser(memberId) {
  if (!currentUser.value || !currentUser.value.id) return false
  return Number(memberId) === Number(currentUser.value.id)
}
</script>
<style scoped>
.module-card.modern-tasks { background: var(--bg-color-secondary); border-radius: 14px; box-shadow: 0 4px 24px rgba(0,0,0,0.07); margin-bottom: 24px; padding: 28px 28px 18px 28px; }
.module-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.module-title { font-size: 1.25rem; font-weight: 700; color: var(--text-color) !important; margin: 0; }
.btn-group { display: flex; gap: 14px; }
.modern-filters { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
.filter-input { width: 200px; }
.filter-select { width: 110px; }
.kanban-view.modern-kanban { margin-top: 18px; }
.card.modern-card { background: var(--bg-color-secondary); border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 18px; border: none; }
.card-header.modern-card-header.kanban-col-header {
  background: var(--bg-color-tertiary) !important; 
  border-radius: 12px 12px 0 0; 
  padding: 12px 18px; 
  font-weight: 700; 
  font-size: 1.1rem;
  color: var(--text-color);
  display: flex; 
  align-items: center; 
  gap: 8px;
}
.task-card.modern-task-card { background: var(--bg-color-secondary); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px 14px; margin-bottom: 12px; cursor: pointer; transition: box-shadow 0.2s, transform 0.2s; box-shadow: 0 1px 4px rgba(0,0,0,0.04); position: relative; padding-right: 32px; }
.task-card.modern-task-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.10); transform: translateY(-2px) scale(1.02); border-color: var(--primary-color-light); }
.task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.task-title-main { font-size: 1.08rem; font-weight: 600; color: var(--text-color); }
.task-meta-row { display: flex; gap: 16px; align-items: center; font-size: 0.95rem; color: var(--text-color-secondary); margin-bottom: 6px; }
.task-tags { display: flex; gap: 6px; margin-bottom: 6px; }
.task-description { color: var(--text-color-secondary); font-size: 0.97rem; margin-bottom: 6px; min-height: 18px; }
.ai-analysis-toggle { margin-top: 4px; margin-bottom: 2px; cursor: pointer; user-select: none; }
.modern-ai-analysis { 
  background: var(--bg-color-tertiary); 
  border-left: 3px solid var(--primary-color); 
  padding: 8px 12px; 
  border-radius: 4px; 
  margin-top: 4px; 
  font-size: 0.97rem; 
}

.modern-ai-analysis ul {
  margin: 0;
  padding-left: 18px;
}

.modern-ai-analysis li {
  margin-bottom: 6px;
  line-height: 1.5;
}

.modern-ai-analysis code {
  background: rgba(0,0,0,0.05);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Consolas', monospace;
}

.modern-ai-analysis strong {
  font-weight: 600;
  color: var(--text-color);
}

.modern-ai-analysis em {
  font-style: italic;
  color: var(--text-color-secondary);
}

.el-dialog.modern-dialog,
.el-dialog.modern-dialog .el-dialog__body,
.el-dialog.modern-dialog .el-dialog__footer {
  background: var(--bg-color-secondary);
  color: var(--text-color);
}
.el-dialog.modern-dialog .el-dialog__body { padding-top: 10px; }
.el-dialog.modern-dialog .el-dialog__footer { padding-bottom: 10px; }
.el-form.modern-form .el-form-item { margin-bottom: 14px; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.kanban-col-dot { 
  width: 10px; 
  height: 10px; 
  border-radius: 50%; 
  display: inline-block; 
  margin-right: 4px; 
}
.kanban-col-dot.待处理 { background: var(--warning-color); }
.kanban-col-dot.进行中 { background: var(--primary-color); }
.kanban-col-dot.已完成 { background: var(--success-color); }
.kanban-badge { margin-left: 4px; vertical-align: middle; }
.modern-gantt .gantt-desc { text-align: center; color: var(--text-color-tertiary); font-size: 15px; margin-top: 12px; }
.modern-chart-view .card { background: var(--bg-color-tertiary); }
.task-progress-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.progress-text { font-size: 12px; color: var(--text-color-tertiary); }
.member-completion-list { margin: 10px 0; }
.member-item { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
/* 深色模式下 Element Plus 组件适配 */
:deep(.el-tag) {
  background: var(--bg-color-tertiary) !important;
  color: var(--text-color) !important;
  border-color: var(--border-color) !important;
}
:deep(.el-badge__content) {
  background-color: var(--primary-color) !important;
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
.modern-ai-analysis .analysis-title {
  display: block;
  margin-bottom: 6px;
  color: var(--primary-color);
  font-weight: 600;
}

.modern-ai-analysis .suggestion-title {
  display: block;
  margin-top: 10px;
  margin-bottom: 6px;
  color: var(--success-color);
  font-weight: 600;
}

.modern-ai-analysis .list-bullet {
  display: inline-block;
  margin-right: 6px;
  color: var(--primary-color);
  font-size: 1.1em;
}

.task-select {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 5;
}

.task-body {
  padding-left: 24px; /* 为复选框留出空间 */
  cursor: pointer;
}

.task-card.modern-task-card {
  position: relative;
  padding: 16px 14px 16px 14px;
}
</style>

<style lang="scss">
/* 深色模式下的样式修复 */
[data-theme="dark"] {
  .module-card, .modern-card, .modern-task-card, .el-dialog {
    background-color: var(--el-bg-color-page) !important;
    color: var(--el-text-color-primary) !important;
    border: 1px solid var(--el-border-color-light) !important;
  }

  .module-title, .task-title-main, .el-dialog__title {
    color: var(--el-text-color-primary) !important;
  }
  
  .filter-input .el-input__wrapper, .filter-select .el-input__wrapper {
    background-color: var(--el-fill-color-light) !important;
    border-color: var(--el-border-color) !important;
  }
  
  .kanban-col-header {
    border-bottom-color: var(--el-border-color-light) !important;
  }
  
  .task-meta-row, .task-description, .progress-text, .ai-analysis-toggle span {
    color: var(--el-text-color-secondary) !important;
  }

  .modern-ai-analysis {
    background-color: var(--el-bg-color) !important;
    border-color: var(--el-border-color) !important;
  }

  .el-form-item__label {
    color: var(--el-text-color-secondary) !important;
  }
}
</style> 
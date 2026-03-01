<template>
  <div class="smartdoc-home-container">
    <!-- 添加隐藏的刷新触发元素，用于强制组件刷新 -->
    <div style="display: none;">{{ refreshTrigger }}</div>
    
    <!-- 页面标题和操作区 -->
    <div class="page-header">
      <div class="left-section">
        <h2 class="page-title">智能文档</h2>
        <p class="page-description">创建、编辑和管理您的智能文档</p>
        </div>
      <div class="right-section">
        <div class="search-controls">
          <el-select 
            v-model="searchCategory" 
            placeholder="选择分类" 
            @change="selectCategory(searchCategory)" 
            class="category-select"
          >
            <el-option label="全部分类" value="all" />
            <el-option 
              v-for="category in documentCategories" 
              :key="category.id" 
              :label="category.name" 
              :value="category.id.toString()"
            />
          </el-select>
          
          <el-input
            placeholder="搜索文档..."
            v-model="searchQuery"
          class="search-input"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <el-button type="success" @click="handleImportWord" style="margin-right: 10px;">
          <el-icon><Upload /></el-icon> 导入Word
        </el-button>
        <el-button type="primary" @click="createNewDocument">
          <el-icon><Plus /></el-icon> 新建文档
        </el-button>
          </div>
        </div>

    <!-- 文档概览统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="hover" @click="selectCategory('all')">
        <div class="stat-content">
          <div class="stat-icon doc-icon">
                <el-icon><Document /></el-icon>
              </div>
          <div class="stat-info">
            <div class="stat-value">{{ totalDocuments }}</div>
            <div class="stat-label">全部文档</div>
                </div>
              </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon edit-icon">
            <el-icon><EditPen /></el-icon>
            </div>
          <div class="stat-info">
            <div class="stat-value">{{ recentEditCount }}</div>
            <div class="stat-label">近期编辑</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon share-icon">
            <el-icon><Share /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ sharedDocuments.length }}</div>
            <div class="stat-label">共享文档</div>
            </div>
        </div>
      </el-card>
    </div>

    <!-- 添加筛选活动状态提示栏 -->
    <div v-if="searchCategory !== 'all'" class="filter-status-bar">
      <div class="filter-bar-content">
        <div class="filter-title">
          <span>当前筛选: </span>
          <span class="filter-category" :style="{ backgroundColor: getSelectedCategoryColor() }">
            {{ getSelectedCategoryName() }}
          </span>
        </div>
        <div class="filter-actions">
          <el-button type="primary" link @click="resetCategoryFilter">
            <el-icon><Close /></el-icon> 清除筛选
          </el-button>
        </div>
      </div>
    </div>

    <!-- 文档分类区域 - 移至文档列表上方 -->
    <div class="section category-section">
      <div class="section-header">
        <h3>文档分类</h3>
        <div class="section-actions">
          <el-button text @click="manageCategories">管理分类</el-button>
        </div>
      </div>
      
      <div class="category-cards">
        <!-- 全部分类选项 -->
        <div 
          class="category-card" 
          :class="{ 'category-active': searchCategory === 'all' }"
          @click="selectCategory('all')"
        >
          <div class="category-icon" :style="{ backgroundColor: '#409EFF' }">
            <el-icon><Document /></el-icon>
          </div>
          <div class="category-info">
            <h4>全部文档</h4>
            <div class="category-count">{{ totalDocuments }} 个文档</div>
          </div>
          <div v-if="searchCategory === 'all'" class="category-selected-indicator"></div>
        </div>
        
        <!-- 分类卡片 -->
        <div 
          v-for="category in documentCategories" 
          :key="category.id" 
          class="category-card" 
          :class="{ 'category-active': searchCategory === category.id.toString() }"
          @click="selectCategory(category)"
        >
          <div class="category-icon" :style="{ backgroundColor: category.color }">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="category-info">
            <h4>{{ category.name }}</h4>
            <div class="category-count">{{ category.document_count }} 个文档</div>
          </div>
          <div v-if="searchCategory === category.id.toString()" class="category-selected-indicator"></div>
        </div>
      </div>
    </div>

    <!-- 添加文档列表区域 -->
    <div class="section">
      <div class="section-header">
        <h3>我的文档</h3>
        <div class="filter-controls">
          <el-button text @click="() => fetchDocuments(true)">刷新</el-button>
        </div>
              </div>
      
      <div class="document-cards">
        <el-card 
          v-for="doc in documents" 
          :key="doc.id" 
          class="doc-card" 
          shadow="hover"
          @click="openDocument(doc)"
        >
          <div class="doc-card-header">
            <div class="doc-info">
              <div class="doc-type-tag">{{ doc.type }}</div>
              <div v-if="doc.category" 
                   class="doc-category-tag" 
                   :style="{ backgroundColor: doc.category.color || '#67C23A' }"
              >
                {{ doc.category.name }}
              </div>
              <!-- 添加共享状态标签 -->
              <div v-if="doc.is_shared" class="doc-shared-tag">
                <el-icon><User /></el-icon>
                <span>已共享</span>
              </div>
            </div>
            <div class="doc-menu btn-container" @click.stop>
              <el-dropdown trigger="click" @click.stop>
                <el-icon><More /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click.stop="openDocument(doc)">打开</el-dropdown-item>
                    <el-dropdown-item @click.stop="editDocument(doc, $event)">编辑</el-dropdown-item>
                    <el-dropdown-item @click.stop="exportDocument(doc)">下载</el-dropdown-item>
                    <el-dropdown-item @click.stop="shareDocument(doc)">分享</el-dropdown-item>
                    <el-dropdown-item divided @click.stop="deleteDocument(doc)" type="danger">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          
          <div class="card-content-area">
            <h4 class="doc-title" :title="doc.title">{{ doc.title }}</h4>
            <div class="doc-preview" v-html="doc.preview || '无预览内容'"></div>
          </div>
          
          <div class="doc-footer">
            <div class="doc-time">
              <el-icon><Clock /></el-icon>
              <span>{{ formatDate(doc.update_time) }}</span>
            </div>
            <div class="doc-actions btn-container">
              <el-tooltip content="编辑" placement="top">
                <el-button link circle size="small" @click.stop="editDocument(doc, $event)">
                  <el-icon><EditPen /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="分享" placement="top">
                <el-button link circle size="small" @click.stop="shareDocument(doc)">
                  <el-icon><Share /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </el-card>
        
        <!-- 创建新文档卡片 -->
        <div class="doc-card new-doc-card" @click="createNewDocument">
          <div class="new-doc-content">
            <el-icon><Plus /></el-icon>
            <span>新建文档</span>
          </div>
        </div>
      </div>
      
      <!-- 分页控制区 -->
      <div v-if="totalCount > 0" class="pagination-container">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :total="totalCount"
          :page-size="pageSize"
          v-model:current-page="page"
          @current-change="onPageChange"
          :pager-count="5"
          :disabled="createLoading"
        />
        <!-- 添加调试信息(仅开发环境显示) -->
        <div v-if="$_isDev" class="pagination-debug">
          <small>当前页: {{ page }} / 总页数: {{ Math.ceil(totalCount / pageSize) || 0 }} (共{{ totalCount }}条记录)</small>
        </div>
      </div>
    </div>

    <!-- 最近编辑文档区域 -->
    <div class="section">
      <div class="section-header">
        <h3>最近编辑</h3>
        <div class="section-actions">
          <el-button text @click="viewAllDocuments('recent')">查看全部</el-button>
        </div>
      </div>
      
      <div class="document-cards">
        <el-card 
          v-for="doc in recentDocuments" 
          :key="doc.id" 
          class="doc-card" 
          shadow="hover"
          @click="openDocument(doc)"
        >
          <div class="doc-card-header">
            <div class="doc-info">
              <div class="doc-type-tag">{{ doc.type }}</div>
              <div v-if="doc.category" 
                   class="doc-category-tag" 
                   :style="{ backgroundColor: doc.category.color || '#67C23A' }"
              >
                {{ doc.category.name }}
              </div>
              <!-- 添加共享状态标签 -->
              <div v-if="doc.is_shared" class="doc-shared-tag">
                <el-icon><User /></el-icon>
                <span>已共享</span>
              </div>
            </div>
            <div class="doc-menu btn-container" @click.stop>
              <el-dropdown trigger="click" @click.stop>
                <el-icon><More /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click.stop="openDocument(doc)">打开</el-dropdown-item>
                    <el-dropdown-item @click.stop="editDocument(doc, $event)">编辑</el-dropdown-item>
                    <el-dropdown-item @click.stop="exportDocument(doc)">下载</el-dropdown-item>
                    <el-dropdown-item @click.stop="shareDocument(doc)">分享</el-dropdown-item>
                    <el-dropdown-item divided @click.stop="deleteDocument(doc)" type="danger">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          
          <div class="card-content-area">
            <h4 class="doc-title" :title="doc.title">{{ doc.title }}</h4>
            <div class="doc-preview" v-html="doc.preview || '无预览内容'"></div>
          </div>
          
          <div class="doc-footer">
            <div class="doc-time">
              <el-icon><Clock /></el-icon>
              <span>{{ formatDate(doc.update_time) }}</span>
            </div>
            <div class="doc-actions btn-container">
              <el-tooltip content="编辑" placement="top">
                <el-button link circle size="small" @click.stop="editDocument(doc, $event)">
                  <el-icon><EditPen /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="分享" placement="top">
                <el-button link circle size="small" @click.stop="shareDocument(doc)">
                  <el-icon><Share /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </el-card>
        
        <!-- 创建新文档卡片 -->
        <div class="doc-card new-doc-card" @click="createNewDocument">
          <div class="new-doc-content">
            <el-icon><Plus /></el-icon>
            <span>新建文档</span>
          </div>
        </div>
      </div>
      
      <div v-if="recentDocuments.length === 0" class="empty-state">
        <!-- 移除暂无最近编辑文档的显示 -->
    </div>
  </div>

    <!-- 创建新文档对话框 -->
  <el-dialog
      v-model="newDocumentDialogVisible"
      title="新建智能文档"
      width="35%"
    >
      <el-tabs v-model="documentCreateType">
        <el-tab-pane label="空白文档" name="blank" />
        <el-tab-pane label="AI生成文档" name="ai" />
      </el-tabs>

      <div v-if="documentCreateType === 'blank'">
        <el-form
          :model="newDocumentForm"
          label-width="80px"
          class="mt-4"
          :rules="blankFormRules"
          ref="blankFormRef"
        >
          <el-form-item label="文档标题" prop="title">
            <el-input v-model="newDocumentForm.title" placeholder="请输入文档标题" />
          </el-form-item>
          <el-form-item label="文档类型">
            <el-input v-model="newDocumentForm.type" placeholder="请输入文档类型" />
            <div class="form-tip">如果未填写，默认为通用类型</div>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="documentCreateType === 'ai'">
        <el-form
          :model="aiDocumentForm"
          label-width="80px"
          class="mt-4"
          :rules="aiFormRules"
          ref="aiFormRef"
        >
          <el-form-item label="文档主题" prop="title">
            <el-input v-model="aiDocumentForm.title" placeholder="简短描述文档主题，如：项目周报" />
          </el-form-item>
          <el-form-item label="文档要求" prop="requirements">
            <el-input
              v-model="aiDocumentForm.requirements"
              type="textarea"
              :rows="3"
              placeholder="详细描述您需要的文档内容和要求"
            />
            <div class="form-tip">人工智能会根据您的描述生成文档内容</div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="newDocumentDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitNewDocument" :loading="createLoading">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 分享文档对话框 -->
    <el-dialog
      v-model="shareDialogVisible"
      title="分享文档"
      width="30%"
      class="share-dialog"
    >
      <div v-if="selectedDocument">
        <p>您即将分享文档: <strong>{{ selectedDocument.title }}</strong></p>
        <el-form label-width="120px" class="mt-4">
          <el-form-item label="分享方式">
            <el-radio-group v-model="shareMode" @change="handleShareModeChange">
              <el-radio v-if="selectedDocument.creator && selectedDocument.creator.id === getCurrentUserId()" :label="'permission'">授予权限</el-radio>
              <el-radio :label="'chat'">发送到聊天</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <!-- 权限分享模式 -->
          <template v-if="shareMode === 'permission'">
            <el-form-item label="已分享用户" v-if="existingSharedUsers.length > 0">
              <div class="user-permissions-list">
                <div v-for="user in existingSharedUsers" :key="user.user_id" class="user-permission-item">
                  <span class="user-name">{{ user.username }}</span>
                  <div class="permission-info">
                    <el-tag type="info" size="small">可编辑</el-tag>
                    <el-button type="danger" link @click="removeSharedUser(user.user_id)" style="margin-left: 10px;">移除</el-button>
                  </div>
                </div>
              </div>
              <div class="form-tip">已有 {{ existingSharedUsers.length }} 个用户拥有此文档的权限</div>
            </el-form-item>
            
            <el-form-item label="添加用户">
              <el-select
                v-model.number="selectedUsers"
                multiple
                placeholder="请选择要添加的用户"
                style="width: 100%"
                popper-class="share-dialog-popper"
                @change="handleUserSelectionChange"
              >
                <el-option
                  v-for="user in availableUsers"
                  :key="user.id"
                  :label="user.username"
                  :value="user.id"
                />
              </el-select>
              <div class="form-tip" v-if="availableUsers.length === 0">没有可添加的用户</div>
            </el-form-item>
            
            <template v-if="selectedUsers.length > 0">
              <el-form-item label="新增权限">
                <div class="user-permissions-list">
                  <div v-for="userPerm in selectedUsersWithPermissions" :key="userPerm.user_id" class="user-permission-item">
                    <span class="user-name">{{ getUsernameById(userPerm.user_id) }}</span>
                    <el-tag type="success">可编辑</el-tag>
                  </div>
                </div>
              </el-form-item>
            </template>
          </template>
          
          <!-- 聊天分享模式 -->
          <template v-if="shareMode === 'chat'">
            <el-form-item label="文档格式">
              <el-radio-group v-model="shareFormat">
                <el-radio label="pdf">PDF格式</el-radio>
                <el-radio label="word">Word格式</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="选择用户">
              <el-select
                v-model="selectedChatUsers"
                multiple
                placeholder="请选择接收用户"
                style="width: 100%"
                popper-class="share-dialog-popper"
              >
                <el-option
                  v-for="user in availableChatUsers"
                  :key="user.id"
                  :label="user.username"
                  :value="user.id"
                />
              </el-select>
              <div class="form-tip">文档将发送到与选中用户的聊天会话中</div>
            </el-form-item>
          </template>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="shareDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmShare" :loading="shareLoading">
            {{ shareMode === 'permission' ? '确定' : '分享' }}
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
      <div v-if="selectedDocument">
        <p>您确定要删除文档 <strong>{{ selectedDocument.title }}</strong> 吗?</p>
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
    
    <!-- 分类管理对话框 -->
    <el-dialog
      v-model="categoryDialogVisible"
      title="管理文档分类"
      width="40%"
    >
      <div class="category-management">
        <div class="category-list">
          <h4>当前类型</h4>
          <el-table :data="documentCategories" style="width: 100%">
            <el-table-column prop="name" label="类型名称" />
            <el-table-column label="颜色" width="120">
              <template #default="scope">
                <div class="color-preview" :style="{ backgroundColor: scope.row.color }"></div>
                {{ scope.row.color }}
              </template>
            </el-table-column>
            <el-table-column label="文档数" width="100">
              <template #default="scope">
                {{ scope.row.document_count || 0 }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button type="primary" link @click="editCategory(scope.row)">编辑</el-button>
                <el-button 
                  type="danger" 
                  link 
                  @click="deleteCategory(scope.row)"
                  :disabled="scope.row.document_count > 0"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <el-divider />
        
        <div class="category-form">
          <h4>{{ editingCategory.id ? '编辑分类' : '新增分类' }}</h4>
          <el-form 
            :model="editingCategory" 
            :rules="categoryFormRules" 
            label-width="80px"
            ref="categoryFormRef"
          >
            <el-form-item label="分类名称" prop="name">
              <el-input v-model="editingCategory.name" placeholder="输入分类名称" />
            </el-form-item>
            <el-form-item label="分类颜色" prop="color">
              <el-color-picker v-model="editingCategory.color" />
              <span class="color-value">{{ editingCategory.color }}</span>
            </el-form-item>
            <el-form-item label="描述">
              <el-input 
                v-model="editingCategory.description" 
                type="textarea" 
                :rows="3" 
                placeholder="输入分类描述（可选）" 
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitCategory" :loading="categoryLoading">
                {{ editingCategory.id ? '更新' : '创建' }}
              </el-button>
              <el-button @click="resetCategoryForm">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-dialog>

    <!-- 添加编辑文档的弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑文档"
      width="35%"
    >
      <el-form 
        :model="editDocumentForm" 
        label-width="80px" 
        class="mt-4"
        :rules="editFormRules"
        ref="editFormRef"
      >
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="editDocumentForm.title" placeholder="请输入文档标题" />
        </el-form-item>
        <el-form-item label="文档类型">
          <el-input v-model="editDocumentForm.type" placeholder="请输入文档类型" />
          <div class="form-tip">如果未填写，默认为通用类型</div>
        </el-form-item>
        <el-form-item label="所属分类">
          <el-select v-model="editDocumentForm.category_id" placeholder="选择文档分类" style="width: 100%">
            <el-option label="无分类" :value="null" />
            <el-option 
              v-for="category in documentCategories" 
              :key="category.id" 
              :label="category.name" 
              :value="category.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEditDocument" :loading="editLoading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, getCurrentInstance, provide, onActivated, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Search, Plus, EditPen, Share, Folder, Close, More, Document, Clock, Upload, User } from '@element-plus/icons-vue'
import _ from 'lodash'
import { 
  getDocuments,
  getRecentDocuments,
  getSharedDocuments,
  getDocumentCategories,
  createDocument,
  deleteDocument as apiDeleteDocument,
  shareDocument as apiShareDocument,
  createDocumentCategory,
  updateDocumentCategory,
  deleteDocumentCategory,
  aiGenerateDocument,
  getDocumentDetail,
  updateDocument,
  importWordDocument
} from '@/api/smartdoc'
import userApi from '@/api/user';
import { createChatSession, getChatSessions } from '@/api/chat';
import request from '@/utils/request';

export default {
  name: 'SmartDocHome',
  components: {
    Search,
    Plus,
    EditPen,
    Share,
    Folder,
    Close,
    More,
    Document,
    Clock,
    Upload,
    User
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const { proxy } = getCurrentInstance() // 获取组件实例
    
    // 判断是否为开发环境
    const $_isDev = process.env.NODE_ENV === 'development'
    
    // 刷新触发器，用于强制组件刷新
    const refreshTrigger = ref(Date.now())
    
    // 状态数据
    const documents = ref([])
    const recentDocuments = ref([])
    const sharedDocuments = ref([])
    const documentCategories = ref([])
    const searchQuery = ref('')
    const searchCategory = ref('all')
    const newDocumentDialogVisible = ref(false)
    const shareDialogVisible = ref(false)
    const deleteDialogVisible = ref(false)
    const documentCreateType = ref('blank')
    const selectedDocument = ref(null)
    const selectedUsers = ref([])
    const selectedUsersWithPermissions = ref([]) // 添加权限控制数组
    const availableUsers = ref([])
    const availableChatUsers = ref([]) // 添加专用于聊天的用户列表
    const createLoading = ref(false)
    const shareLoading = ref(false)
    const deleteLoading = ref(false)
    const existingSharedUsers = ref([])
    
    // 添加分享相关变量
    const shareMode = ref('permission') // 分享方式：permission(授权) 或 chat(发送到聊天)
    const shareFormat = ref('pdf') // 分享文档格式：pdf 或 word
    const selectedChatUsers = ref([]) // 选择的聊天用户
    
    // 分页相关状态
    const page = ref(1)
    const pageSize = 12 // 每页显示12个文档（不包含"新建"卡片）
    const totalCount = ref(0)
    const grandTotalCount = ref(0) // 用于存储真实的文档总数
    // 添加加载更多相关状态
    const hasMore = ref(true)
    const loadingMore = ref(false)
    
    // 添加编辑文档相关状态
    const editDialogVisible = ref(false)
    const editDocumentForm = ref({
      id: null,
      title: '',
      type: '',
      category_id: null
    })
    const editLoading = ref(false)
    
    // 表单数据
    const newDocumentForm = ref({
        title: '',
        type: ''
    })
    
    const aiDocumentForm = ref({
        title: '',
      requirements: ''
    })
    
    // 表单校验规则
    const blankFormRules = {
        title: [
        { required: true, message: '请输入文档标题', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
        ]
    }
    
    const aiFormRules = {
        title: [
        { required: true, message: '请输入文档主题', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
        ],
        requirements: [
        { required: true, message: '请输入文档要求', trigger: 'blur' },
        { min: 10, max: 500, message: '长度在 10 到 500 个字符', trigger: 'blur' }
      ]
    }
    
    // 添加编辑表单验证规则
    const editFormRules = {
      title: [
        { required: true, message: '请输入文档标题', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
      ]
    }
    
    const blankFormRef = ref(null)
    const aiFormRef = ref(null)
    const editFormRef = ref(null)
    
    // 计算属性
    const totalDocuments = computed(() => {
      return grandTotalCount.value;
    });
    
    const recentEditCount = computed(() => {
      return recentDocuments.value.length || 0;
    });
    
    // 分类管理相关状态
    const categoryDialogVisible = ref(false)
    const editingCategory = ref({
      name: '',
      color: '#409EFF',
      description: '',
    })
    const categoryFormRef = ref(null)
    const categoryLoading = ref(false)
    const categoryFormRules = {
      name: [
        { required: true, message: '请输入类型名称', trigger: 'blur' },
        { min: 2, max: 20, message: '长度在2到20个字符', trigger: 'blur' }
      ],
      color: [
        { required: true, message: '请选择颜色', trigger: 'change' }
      ]
    }
    
    // 辅助方法：强制刷新视图
    const forceUpdate = async () => {
      // 创建临时数据，触发深度响应式更新
      documents.value = [...documents.value];
      recentDocuments.value = [...recentDocuments.value]; 
      sharedDocuments.value = [...sharedDocuments.value];
      
      // 使用Vue实例的$forceUpdate方法
      if (proxy && proxy.$forceUpdate) {
        proxy.$forceUpdate();
      }
      
      // 等待DOM更新
      await nextTick();
    };
    
    // 方法
    const fetchDocuments = async (forceRefresh = false, append = false, timestamp = null) => {
      if (forceRefresh) {
        page.value = 1
        hasMore.value = true
      }
      
      // 只有在加载更多模式下才检查hasMore
      if (append && !hasMore.value && !forceRefresh) {
        console.log('没有更多文档，取消获取')
        return
      }
      
      if (!append) {
        createLoading.value = true
      } else {
        loadingMore.value = true
      }
      
      try {
        // 构建过滤条件
        const filters = {}
        
        // 添加分类过滤
        if (searchCategory.value && searchCategory.value !== 'all') {
          filters.category = searchCategory.value
        }
        
        // 添加搜索查询
        if (searchQuery.value) {
          filters.search = searchQuery.value
        }
        
        // API请求参数 - 使用与DRF兼容的page_size参数名
        const params = {
          page: page.value,
          page_size: pageSize, // 将pageSize作为page_size参数传递，与后端REST framework参数保持一致
          _t: timestamp || new Date().getTime() // 添加时间戳，确保不使用缓存
        }
        
        // 合并过滤条件
        Object.assign(params, filters)
        
        console.log(`获取文档列表，页码: ${page.value}，参数:`, params)
        
        const res = await getDocuments(params)
        console.log('文档列表API响应:', res)
        
        let newDocuments = []
        let currentViewCount = 0;
        
        // 处理API可能返回的警告信息
        if (res && res.warning) {
          console.warn('API返回警告:', res.warning)
          ElMessage({
            message: res.warning,
            type: 'warning',
            duration: 5000
          })
          // 如果是页码问题，重置当前页为1
          if (res.warning.includes('页码') && res.warning.includes('无效或超出范围')) {
            setTimeout(() => {
              page.value = 1;
            }, 0);
          }
        }
        
        // 处理不同格式的响应
        if (res && res.data && Array.isArray(res.data)) {
          // 标准格式响应
          newDocuments = res.data
          currentViewCount = res.total || res.count || 0
        } else if (res && res.results && Array.isArray(res.results)) {
          // Django REST格式响应
          newDocuments = res.results
          currentViewCount = res.count || 0
        } else if (res && res.data && res.data.results && Array.isArray(res.data.results)) {
          // 嵌套格式响应
          newDocuments = res.data.results
          currentViewCount = res.data.count || 0
        } else {
          console.warn('API返回的文档数据格式无效:', res)
          documents.value = []
          return
        }
          
        // 更新用于分页的总数
        totalCount.value = currentViewCount;

        // 仅当没有筛选条件时，才更新"全部文档"的真实总数
        if (!filters.category && !filters.search) {
            grandTotalCount.value = currentViewCount;
        }

        // 如果是追加模式
        if (append) {
          // 检查并避免添加重复的文档
          const existingIds = new Set(documents.value.map(doc => doc.id))
          const uniqueNewDocs = newDocuments.filter(doc => !existingIds.has(doc.id))
          
          if (uniqueNewDocs.length > 0) {
            documents.value = [...documents.value, ...uniqueNewDocs]
            console.log(`追加了 ${uniqueNewDocs.length} 个新文档，当前共 ${documents.value.length} 个`)
          } else {
            console.log('没有新的文档被追加')
            // 即使没有新文档，也可能是因为我们在不同的页码上获取了重复数据
            hasMore.value = newDocuments.length > 0
          }
        } else {
          // 非追加模式，直接替换
          documents.value = newDocuments
          console.log(`设置了 ${documents.value.length} 个文档`)
        }
        
        console.log(`当前文档ID列表: [${documents.value.map(d => d.id).join(', ')}]`)
        
        // 计算总页数
        const totalPages = Math.ceil(currentViewCount / pageSize);
        console.log(`分页状态 - 当前页: ${page.value}, 总页数: ${totalPages}, 总文档数: ${currentViewCount}`);
        
        // 检查当前页是否超出范围
        if (page.value > totalPages && totalPages > 0 && !append) {
          console.warn(`当前页 ${page.value} 超出范围，自动修正为最后一页 ${totalPages}`);
          
          // 使用setTimeout避免触发watch事件
          setTimeout(() => {
            page.value = totalPages;
          }, 0);
          
          return;
        }
        
        // 更新是否有更多页标志
        hasMore.value = page.value < totalPages;
        
        // 如果匹配的文档太少（比如低于一屏），并且有更多数据，自动加载更多
        if (!append && documents.value.length < 8 && hasMore.value) {
          console.log('文档数量较少，自动加载下一页')
          // 延迟100ms避免请求过于频繁
          await new Promise(resolve => setTimeout(resolve, 100));
          await fetchDocuments(false, true, timestamp);
        }
          
      } catch (error) {
        console.error('获取文档列表失败', error)
        documents.value = []
        ElMessage.error('获取文档列表失败')
      } finally {
        if (!append) {
          createLoading.value = false
        } else {
          loadingMore.value = false
        }
      }
    }
    
    const fetchRecentDocuments = async (forceRefresh = false, timestamp = null) => {
      console.log('开始获取最近文档...');
      try {
        // 准备参数，如果强制刷新添加时间戳
        const params = forceRefresh ? { _t: timestamp || new Date().getTime() } : {};
        
        const res = await getRecentDocuments(params);
        console.log('最近文档API响应:', res);
        
        if (res && res.data) {
          // 完全替换数组而不是修改引用
          recentDocuments.value = Array.isArray(res.data) ? [...res.data] : [];
          console.log(`设置最近文档: ${recentDocuments.value.length}条记录`);
        } else {
          console.warn('API返回的最近文档数据无效:', res);
          recentDocuments.value = [];
        }
      } catch (error) {
        console.error('获取最近文档失败:', error);
        ElMessage.error('获取最近文档失败');
        recentDocuments.value = [];
      }
    }
    
    const fetchSharedDocuments = async (timestamp = null) => {
      try {
        const params = timestamp ? { _t: timestamp } : {};
        const response = await getSharedDocuments(params)
        sharedDocuments.value = response.data
      } catch (error) {
        console.error('获取共享文档失败', error)
        ElMessage.error('获取共享文档失败')
      }
    }
    
    const fetchDocumentCategories = async (timestamp = null, retryCount = 0) => {
      console.log('开始获取文档分类...');
      try {
        const params = timestamp ? { _t: timestamp } : {};
        const res = await getDocumentCategories(params);
        console.log('文档分类API响应:', res);
        
        if (res && res.data) {
          documentCategories.value = res.data;
          console.log(`设置文档分类: ${documentCategories.value.length}条记录, 数据:`, documentCategories.value);
        } else {
          console.warn('API返回的文档分类数据无效:', res);
          documentCategories.value = [];
          
          // 如果返回空数据且未达到最大重试次数，尝试重试
          if (documentCategories.value.length === 0 && retryCount < 2) {
            console.log(`文档分类数据为空，${retryCount + 1}秒后重试...`);
            setTimeout(() => fetchDocumentCategories(timestamp, retryCount + 1), (retryCount + 1) * 1000);
          }
        }
      } catch (error) {
        console.error('获取文档分类失败:', error);
        
        // 如果是服务器错误且未达到最大重试次数，尝试重试
        if (error.response && error.response.status >= 500 && retryCount < 2) {
          console.log(`服务器错误，${retryCount + 1}秒后重试...`);
          setTimeout(() => fetchDocumentCategories(timestamp, retryCount + 1), (retryCount + 1) * 1000);
        } else {
          ElMessage.error('获取文档分类失败，请刷新页面重试');
          // 初始化空数组
          documentCategories.value = [];
        }
      }
    }
    
    // 监听搜索查询变化，实现实时搜索
    watch(searchQuery, _.debounce(async () => {
      // 重置分页
      page.value = 1
      hasMore.value = true
      
      // 清空现有文档列表，显示加载状态
      documents.value = []
      createLoading.value = true
      
      try {
        // 获取新的搜索结果
        await fetchDocuments(true)
      } catch (error) {
        console.error('搜索失败:', error)
        ElMessage.error('搜索文档失败，请重试')
      } finally {
        createLoading.value = false
      }
    }, 300))
    
    const createNewDocument = () => {
      // 重置表单
      newDocumentForm.value = { title: '', type: '' }
      aiDocumentForm.value = { title: '', requirements: '' }
      documentCreateType.value = 'blank'
      newDocumentDialogVisible.value = true
      
      // 监听对话框关闭事件，清理表单
      nextTick(() => {
        try {
          const dialog = document.querySelector('.el-dialog');
          if (dialog) {
            dialog.addEventListener('closed', () => {
              try {
                if (blankFormRef.value) {
                  blankFormRef.value.clearValidate();
                }
                if (aiFormRef.value) {
                  aiFormRef.value.clearValidate();
                }
              } catch (err) {
                console.error('Error clearing form validation:', err);
              }
            }, { once: true });
          }
        } catch (err) {
          console.error('Error setting up dialog event listener:', err);
        }
      });
    }
    
    const submitNewDocument = async () => {
      if (documentCreateType.value === 'blank') {
        if (!blankFormRef.value) {
          console.warn('表单引用不存在');
          return;
        }
        
        try {
          const valid = await blankFormRef.value.validate()
            .catch(err => {
              console.error('表单验证失败:', err);
              return false;
            });
          
          if (valid) {
            createLoading.value = true;
            try {
              console.log('开始创建文档:', {
                title: newDocumentForm.value.title,
                type: newDocumentForm.value.type || '通用'
              });
              
              const response = await createDocument({ 
                title: newDocumentForm.value.title,
                type: newDocumentForm.value.type || '通用',
                content: ''
              });
              
              console.log('创建文档响应数据：', JSON.stringify(response));
              
              // 关闭对话框
              newDocumentDialogVisible.value = false;
              ElMessage.success('文档创建成功');
              
              // 解析返回的文档ID
              let docId = null;
              if (response && response.data) {
                if (response.data.id) {
                  docId = response.data.id;
                } else if (Array.isArray(response.data) && response.data.length > 0) {
                  docId = response.data[0].id;
                } else if (response.data.results && Array.isArray(response.data.results) && response.data.results.length > 0) {
                  docId = response.data.results[0].id;
                }
              }
              
              // 等待对话框关闭完成后再执行跳转，避免DOM错误
              setTimeout(() => {
                if (docId) {
                  console.log(`准备跳转到文档详情页，ID: ${docId}`);
                  
                  // 先刷新文档列表，确保数据是最新的
                  fetchDocuments();
                  fetchRecentDocuments();
                  
                  // 然后再执行导航
                  setTimeout(() => {
                    router.push({
                      name: 'SmartDocDetail',
                      params: { id: docId }
                    }).then(() => {
                      createLoading.value = false;
                    }).catch(err => {
                      console.error('路由导航失败:', err);
                      ElMessage.error('跳转文档详情页失败，请手动刷新页面');
                      // 尝试路径跳转
                      router.push(`/smartdoc/${docId}`).catch(navErr => {
                        console.error('路径导航也失败:', navErr);
                        ElMessage.error('路径跳转详情页也失败');
                      });
                      createLoading.value = false;
                    });
                  }, 300);
                } else {
                  console.warn('创建文档成功，但返回的数据格式不正确', response);
                  // 刷新文档列表
                  fetchDocuments();
                  fetchRecentDocuments();
                }
              }, 100);
            } catch (error) {
              console.error('创建文档失败', error);
              ElMessage.error('创建文档失败');
            } finally {
              createLoading.value = false;
            }
          }
        } catch (error) {
          console.error('提交表单时发生错误:', error);
          ElMessage.error('表单提交失败');
          createLoading.value = false;
        }
      } else if (documentCreateType.value === 'ai') {
        if (!aiFormRef.value) {
          console.warn('AI表单引用不存在');
          return;
        }
        
        try {
          const valid = await aiFormRef.value.validate()
            .catch(err => {
              console.error('AI表单验证失败:', err);
              return false;
            });
          
          if (valid) {
            createLoading.value = true;
            try {
              // 调用AI生成文档API
              const categoryId = searchCategory.value !== 'all' ? searchCategory.value : null;
              const response = await aiGenerateDocument({
                title: aiDocumentForm.value.title,
                requirement: aiDocumentForm.value.requirements,
                category_id: categoryId,
                doc_type: 'AI'
              });
              console.log('AI生成文档响应数据：', response);
              // 检查超时
              if (response && response.status === 504) {
                ElMessage.error(response.data?.detail || 'AI生成超时，请简化需求或稍后重试');
                createLoading.value = false;
                return;
              }
              if (response && response.data && typeof response.data.detail === 'string' && response.data.detail.includes('超时')) {
                ElMessage.error(response.data.detail);
                createLoading.value = false;
                return;
              }
              newDocumentDialogVisible.value = false;
              ElMessage.success('AI生成文档成功');
              let docId = null;
              if (response && response.data && response.data.id) {
                docId = response.data.id;
              }
              if (docId) {
                // 跳转前打印日志
                console.log('准备跳转到文档详情页，路由名: SmartDocDetail, id:', docId);
                router.push({
                  name: 'SmartDocDetail',
                  params: { id: String(docId) }
                }).then(() => {
                  createLoading.value = false;
                }).catch(err => {
                  console.error('路由导航失败:', err);
                  ElMessage.error('跳转文档详情页失败，请手动刷新页面');
                  // 尝试路径跳转
                  router.push(`/smartdoc/${docId}`).catch(navErr => {
                    console.error('路径导航也失败:', navErr);
                    ElMessage.error('路径跳转详情页也失败');
                  });
                  createLoading.value = false;
                });
                // 异步刷新数据
                fetchDocuments();
                fetchRecentDocuments();
              } else {
                fetchDocuments();
                fetchRecentDocuments();
                createLoading.value = false;
              }
            } catch (error) {
              console.error('AI生成文档失败', error);
              ElMessage.error('AI生成文档失败');
            } finally {
              createLoading.value = false;
            }
          }
        } catch (error) {
          console.error('提交AI表单时发生错误:', error);
          ElMessage.error('表单提交失败');
          createLoading.value = false;
        }
      }
    }
    
    const openDocument = (doc) => {
      router.push({ name: 'SmartDocDetail', params: { id: doc.id } })
    }
    
    const editDocument = (doc, event) => {
      // 阻止事件冒泡，防止触发卡片点击事件
      if (event) {
        event.stopPropagation();
      }
      
      // 确保分类ID是数字类型
      let categoryId = null;
      if (doc.category && doc.category.id) {
        categoryId = Number(doc.category.id);
      }
      
      console.log('编辑文档:', doc.id, '当前分类:', categoryId);
      
      // 设置表单数据
      editDocumentForm.value = {
        id: doc.id,
        title: doc.title,
        type: doc.type || '',
        category_id: categoryId
      };
      
      // 显示编辑对话框
      editDialogVisible.value = true;
    };
    
    // 提交编辑文档
    const submitEditDocument = async () => {
      if (!editFormRef.value) return;
      
      try {
        const valid = await editFormRef.value.validate();
        
        if (valid) {
          editLoading.value = true;
          
          // 准备更新的数据
          const updateData = {
            title: editDocumentForm.value.title,
            type: editDocumentForm.value.type || '通用',
            category_id: editDocumentForm.value.category_id
          };
          
          // 调用API更新文档
          await updateDocument(editDocumentForm.value.id, updateData);
          
          ElMessage.success('文档更新成功');
          editDialogVisible.value = false;
          
          // 强制刷新所有数据以确保视图同步
          await reloadAllData();
        }
      } catch (error) {
        console.error('更新文档失败', error);
        ElMessage.error('更新文档失败');
      } finally {
        editLoading.value = false;
      }
    };
    
    const exportDocument = (doc) => {
      ElMessageBox({
        title: '导出文档',
        message: '请选择导出格式',
        showCancelButton: true,
        confirmButtonText: '导出为PDF',
        cancelButtonText: '导出为Word',
        closeOnClickModal: true,
        callback: (action) => {
          if (action === 'confirm') {
            exportToPdf(doc)
          } else if (action === 'cancel') {
            exportToWord(doc)
          }
        }
      })
    }
    
    // 导出为PDF
    const exportToPdf = async (doc) => {
      if (!doc) {
        ElMessage.error('没有可导出的文档')
        return
      }
      
      // 先获取文档详情内容
      const loading = ElLoading.service({
        lock: true,
        text: '正在加载文档内容...',
        background: 'rgba(255, 255, 255, 0.7)'
      })
      
      try {
        // 获取文档详情
        const response = await getDocumentDetail(doc.id)
        const documentContent = response.data.content
        
        if (!documentContent) {
          loading.close()
          ElMessage.error('文档内容为空，无法导出')
          return
        }
        
        const docTitle = doc.title || '未命名文档'
        const filename = `${docTitle}.pdf`
        
        // 创建临时容器用于导出
        const tempContainer = document.createElement('div')
        tempContainer.innerHTML = documentContent
        tempContainer.className = 'temp-export-container'
        document.body.appendChild(tempContainer)
        
        const options = {
          margin: [15, 15, 15, 15],
          filename: filename,
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        }
        
        // 更新加载提示
        loading.setText('正在生成PDF...')
        
        // 动态导入html2pdf.js
        const html2pdfModule = await import('html2pdf.js')
        const html2pdf = html2pdfModule.default
        
        await html2pdf().from(tempContainer).set(options).save()
        
        // 清理临时元素
        document.body.removeChild(tempContainer)
        
        loading.close()
        ElMessage.success('PDF导出成功')
      } catch (error) {
        console.error('PDF导出失败:', error)
        loading.close()
        ElMessage.error('PDF导出失败: ' + (error.message || '未知错误'))
      }
    }
    
    // 导出为Word（保留图片）
    const exportToWord = async (doc) => {
      if (!doc) {
        ElMessage.error('没有可导出的文档')
        return
      }
      
      const loading = ElLoading.service({
        lock: true,
        text: '正在加载文档内容...',
        background: 'rgba(255, 255, 255, 0.7)'
      })
      
      try {
        // 获取文档详情
        const response = await getDocumentDetail(doc.id)
        const documentContent = response.data.content
        
        if (!documentContent) {
          loading.close()
          ElMessage.error('文档内容为空，无法导出')
          return
        }
        
        const docTitle = doc.title || '未命名文档'
        const filename = `${docTitle}.doc`
        
        // 创建一个临时文档容器处理内容
        const contentContainer = document.createElement('div')
        contentContainer.innerHTML = documentContent
        
        // 更新加载提示
        loading.setText('正在生成Word文档...')
        
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
    
    const shareDocument = async (doc) => {
      selectedDocument.value = doc
      shareLoading.value = true
      
      try {
        console.log('获取文档详情，ID:', doc.id);
        // Fetch document details to get existing permissions
        const detailRes = await getDocumentDetail(doc.id)
        console.log('文档详情响应:', detailRes);
        
        // 尝试从不同可能的响应结构中提取shared_with数据
        let sharedWithData = [];
        if (detailRes && detailRes.data) {
          if (detailRes.data.shared_with && Array.isArray(detailRes.data.shared_with)) {
            sharedWithData = detailRes.data.shared_with;
            console.log('从data.shared_with提取共享用户:', sharedWithData);
          } else if (detailRes.data.permissions && Array.isArray(detailRes.data.permissions)) {
            sharedWithData = detailRes.data.permissions;
            console.log('从data.permissions提取共享用户:', sharedWithData);
          } else if (detailRes.shared_with && Array.isArray(detailRes.shared_with)) {
            sharedWithData = detailRes.shared_with;
            console.log('从直接的shared_with提取共享用户:', sharedWithData);
          }
        }
        
        // 处理不同格式的用户数据
        if (sharedWithData.length > 0) {
          existingSharedUsers.value = sharedWithData.map(item => {
            // 处理可能的不同数据结构
            if (item.user && (item.user.id || item.user.user_id)) {
              return {
                user_id: item.user.id || item.user.user_id,
                username: item.user.username || item.user.name || item.user.email || `用户${item.user.id}`,
                permission: item.permission || 'edit'
              };
            } else if (item.user_id || item.userId) {
              return {
                user_id: item.user_id || item.userId,
                username: item.username || item.name || item.email || `用户${item.user_id || item.userId}`,
                permission: item.permission || 'edit'
              };
            }
            // 默认情况，尝试使用item本身
            return {
              user_id: item.id || item.user_id || 0,
              username: item.username || item.name || item.email || '未知用户',
              permission: item.permission || 'edit'
            };
          });
        } else {
          console.log('没有找到已分享用户数据');
          existingSharedUsers.value = [];
        }
        
        console.log('处理后的已分享用户列表:', existingSharedUsers.value);
        const existingUserIds = new Set(existingSharedUsers.value.map(u => u.user_id));
        console.log('已分享用户ID集合:', Array.from(existingUserIds));
        
        // Get current user and company info
        const currentUserJson = localStorage.getItem('user')
        let currentUserId = null
        let companyId = null
        if (currentUserJson) {
          const currentUser = JSON.parse(currentUserJson)
          currentUserId = currentUser.id
          companyId = currentUser.company_id
          console.log('当前用户ID:', currentUserId, '公司ID:', companyId);
        }
        
        const isCreator = doc.creator && currentUserId && doc.creator.id === currentUserId
        shareMode.value = isCreator ? 'permission' : 'chat'
        console.log('是否为创建者:', isCreator, '分享模式:', shareMode.value);
        
        // Fetch all company users
        const usersRes = await userApi.getCompanyUsers()
        console.log('公司用户列表响应:', usersRes);
        if (usersRes.success && Array.isArray(usersRes.data)) {
          // 权限模式下的用户列表（排除已有权限的用户）
          availableUsers.value = usersRes.data
            .filter(user => 
              user.id !== currentUserId && 
              (!companyId || user.company_id === companyId) &&
              !existingUserIds.has(user.id) // 排除已有权限的用户
            )
            .map(user => ({
              id: user.id,
              username: user.name || user.username || user.email || `用户${user.id}`
            }));
          
          // 聊天模式下的用户列表（包含所有用户，包括已有权限的用户）
          availableChatUsers.value = usersRes.data
            .filter(user => 
              user.id !== currentUserId && 
              (!companyId || user.company_id === companyId)
              // 不排除已有权限的用户
            )
            .map(user => ({
              id: user.id,
              username: user.name || user.username || user.email || `用户${user.id}`
            }));
          
          console.log('授权模式可选用户列表:', availableUsers.value);
          console.log('聊天模式可选用户列表:', availableChatUsers.value);
        } else {
          console.warn('获取公司用户列表失败:', usersRes);
          availableUsers.value = [];
          availableChatUsers.value = [];
        }
      } catch (error) {
        console.error('打开分享对话框失败:', error)
        ElMessage.error('获取分享信息失败')
        existingSharedUsers.value = []
      } finally {
        shareLoading.value = false
        
        // Reset variables for adding new users
        shareFormat.value = 'pdf'
        selectedUsers.value = []
        selectedUsersWithPermissions.value = []
        selectedChatUsers.value = []
        
        shareDialogVisible.value = true
      }
    }
    
    // 通过ID获取用户名
    const getUsernameById = (userId) => {
      const user = availableUsers.value.find(u => u.id === userId)
      return user ? user.username : '未知用户'
    }
    
    // 获取当前用户ID
    const getCurrentUserId = () => {
      try {
        const currentUserJson = localStorage.getItem('user')
        if (currentUserJson) {
          const currentUser = JSON.parse(currentUserJson)
          return currentUser.id
        }
        return null
      } catch (error) {
        console.error('获取当前用户ID失败:', error)
        return null
      }
    }

    // 处理用户选择变化
    const handleUserSelectionChange = (val) => {
      console.log('选择变化 - 原始值:', val);
      console.log('选择变化 - selectedUsers:', selectedUsers.value);
      console.log('选择变化 - 类型:', typeof selectedUsers.value, Array.isArray(selectedUsers.value));
      
      // 确保selectedUsers是数组
      if (!Array.isArray(selectedUsers.value)) {
        console.warn('selectedUsers不是数组，强制转换为数组');
        selectedUsers.value = Array.isArray(val) ? val : [];
      }
      
      // 更新权限控制数组
      selectedUsersWithPermissions.value = selectedUsers.value.map(userId => {
        console.log('处理用户ID:', userId, '类型:', typeof userId);
        return {
          user_id: userId,
          permission: 'edit' // 默认为只读权限
        };
      });
      
      console.log('用户选择变化，已选择用户:', selectedUsers.value);
      console.log('用户权限数组:', selectedUsersWithPermissions.value);
    }

    // 处理分享模式变化
    const handleShareModeChange = () => {
      console.log('分享模式变更为:', shareMode.value);
      // 切换分享模式时清空之前选择的用户
      if (shareMode.value === 'permission') {
        // 切换到权限模式，清空聊天相关的选择
        selectedChatUsers.value = [];
        console.log('已清空聊天用户选择');
      } else if (shareMode.value === 'chat') {
        // 切换到聊天模式，清空权限相关的选择
        selectedUsers.value = [];
        selectedUsersWithPermissions.value = [];
        console.log('已清空权限用户选择');
      }
    }
    
    const confirmShare = async () => {
      // 权限分享方式
      if (shareMode.value === 'permission') {
        // 检查是否为文档创建者
        const currentUserId = getCurrentUserId();
        const isCreator = selectedDocument.value && selectedDocument.value.creator && 
                          currentUserId && selectedDocument.value.creator.id === currentUserId;
        
        if (!isCreator) {
          ElMessage.warning('只有文档创建者才能授予权限')
          return
        }
        
        const finalPermissions = [
          ...existingSharedUsers.value.map(u => ({ user_id: u.user_id, permission: 'edit' })),
          ...selectedUsersWithPermissions.value
        ];
        
        shareLoading.value = true
        try {
          await apiShareDocument(selectedDocument.value.id, finalPermissions)
          ElMessage.success('权限更新成功')
          shareDialogVisible.value = false
        } catch (error) {
          console.error('分享文档失败', error)
          ElMessage.error('权限更新失败')
        } finally {
          shareLoading.value = false
        }
      } 
      // 聊天分享方式
      else if (shareMode.value === 'chat') {
        if (!selectedDocument.value || selectedChatUsers.value.length === 0) {
          ElMessage.warning('请选择至少一个接收用户')
          return
        }
        
        shareLoading.value = true
        try {
          // 获取当前用户信息
          const currentUserJson = localStorage.getItem('user')
          let currentUserId = null
          if (currentUserJson) {
            const currentUser = JSON.parse(currentUserJson)
            currentUserId = currentUser.id
          }
          
          if (!currentUserId) {
            ElMessage.error('无法获取当前用户信息')
            shareLoading.value = false
            return
          }
          
          // 需要获取文档内容
          const docResponse = await getDocumentDetail(selectedDocument.value.id);
          const currentDoc = docResponse.data;
          
          if (!currentDoc || !currentDoc.content) {
            ElMessage.error('无法获取文档内容')
            shareLoading.value = false
            return
          }
          
          // 使用前端导出文件的方式获取文件
          const loading = ElLoading.service({
            lock: true,
            text: `正在准备${shareFormat.value === 'pdf' ? 'PDF' : 'Word'}文件...`,
            background: 'rgba(255, 255, 255, 0.7)'
          });
          
          try {
            // 准备文档内容
            const docTitle = currentDoc.title || '未命名文档';
            const documentContent = currentDoc.content;
            
            // 创建临时容器用于导出
            const tempContainer = document.createElement('div');
            tempContainer.innerHTML = documentContent;
            tempContainer.className = 'temp-export-container';
            document.body.appendChild(tempContainer);
            
            let documentFile = null;
            let fileName = docTitle;
            let fileType = '';
            
            if (shareFormat.value === 'pdf') {
              fileName += '.pdf';
              fileType = 'application/pdf';
              
              loading.setText('正在生成PDF文件...');
              
              // 动态导入html2pdf.js
              const html2pdfModule = await import('html2pdf.js');
              const html2pdf = html2pdfModule.default;
              
              const options = {
                margin: [15, 15, 15, 15],
                filename: fileName,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
              };
              
              // 生成PDF并获取Blob
              documentFile = await html2pdf().from(tempContainer).set(options).outputPdf('blob');
            }
            else {
              fileName += '.doc';
              fileType = 'application/msword';
              
              loading.setText('正在生成Word文件...');
              
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
                  ${tempContainer.innerHTML}
                </body>
                </html>
              `;
              
              // 创建Blob
              documentFile = new Blob([msWordHtml], { type: fileType });
            }
            
            // 清理临时元素
            document.body.removeChild(tempContainer);
            
            // 先获取所有聊天会话列表，只获取一次
            loading.setText('正在查找聊天会话...');
            const sessionsResponse = await getChatSessions();
            let chatSessions = [];
            
            // 处理不同格式的API返回结果
            if (sessionsResponse && sessionsResponse.data && Array.isArray(sessionsResponse.data)) {
              chatSessions = sessionsResponse.data;
            } else if (sessionsResponse && sessionsResponse.results && Array.isArray(sessionsResponse.results)) {
              chatSessions = sessionsResponse.results;
            } else if (sessionsResponse && Array.isArray(sessionsResponse)) {
              chatSessions = sessionsResponse;
            }
            
            console.log(`获取到 ${chatSessions.length} 个会话`);
            loading.setText('正在准备发送...');
            
            // 为每个用户准备会话ID，使用Map存储userId -> chatId的映射
            const userSessionMap = new Map();
            
            // 先批量查找现有会话，减少重复检查
            for (const userId of selectedChatUsers.value) {
              // 查找是否有与该用户的会话
              const existingSession = chatSessions.find(session => {
                // 检查会话是否为双人会话
                if (!session.participants || !Array.isArray(session.participants)) {
                  return false;
                }
                
                // 检查会话是否只有两个参与者
                if (session.participants.length !== 2) {
                  return false;
                }
                
                // 检查会话参与者是否包含当前用户和目标用户
                const hasCurrentUser = session.participants.some(p => 
                  (p.id === currentUserId) || (p.user && p.user.id === currentUserId)
                );
                
                const hasTargetUser = session.participants.some(p => 
                  (p.id === userId) || (p.user && p.user.id === userId)
                );
                
                return hasCurrentUser && hasTargetUser;
              });
              
              if (existingSession) {
                userSessionMap.set(userId, existingSession.id);
                console.log(`用户${userId}有现有会话: ${existingSession.id}`);
              }
            }
            
            // 为没有会话的用户创建新会话
            const newSessionPromises = [];
            for (const userId of selectedChatUsers.value) {
              if (!userSessionMap.has(userId)) {
                console.log(`为用户${userId}创建新会话...`);
                newSessionPromises.push(
                  createChatSession({
                    participant_ids: [currentUserId, userId],
                    title: '文档分享'
                  }).then(response => {
                    if (response && response.data && response.data.id) {
                      userSessionMap.set(userId, response.data.id);
                      console.log(`为用户${userId}创建新会话成功: ${response.data.id}`);
                    } else if (response && response.id) {
                      userSessionMap.set(userId, response.id);
                      console.log(`为用户${userId}创建新会话成功: ${response.id}`);
                    } else {
                      console.error('创建聊天会话失败，返回数据格式不正确:', response);
                      return null;
                    }
                  }).catch(error => {
                    console.error(`为用户${userId}创建会话失败:`, error);
                    return null;
                  })
                );
              }
            }
            
            // 等待所有新会话创建完成
            if (newSessionPromises.length > 0) {
              loading.setText(`正在创建 ${newSessionPromises.length} 个新会话...`);
              await Promise.all(newSessionPromises);
            }
            
            // 准备发送文件
            loading.setText('正在发送文件...');
            const sendPromises = [];
            const failedUsers = [];
            
            // 遍历用户发送文件
            for (const userId of selectedChatUsers.value) {
              const chatId = userSessionMap.get(userId);
              if (!chatId) {
                console.error(`未能找到或创建用户${userId}的会话`);
                failedUsers.push(userId);
                continue;
              }
              
              console.log(`准备向会话 ${chatId} 发送文档...`);
              
              // 创建FormData对象，添加文件和相关信息
              const formData = new FormData();
              formData.append('chat', chatId);
              formData.append('message_type', 'file');
              formData.append('content', `分享了一个${shareFormat.value === 'pdf' ? 'PDF' : 'Word'}文档: ${docTitle}`);
              
              // 将文件Blob转换为File对象 - 为每个用户创建新的File对象
              const file = new File([documentFile], fileName, { type: fileType });
              formData.append('file', file);
              
              // 发送文件消息
              sendPromises.push(
                request({
                  url: '/api/chat/messages/',
                  method: 'post',
                  data: formData,
                  headers: {
                    'Content-Type': 'multipart/form-data'
                  },
                  timeout: 30000 // 增加超时时间
                }).then(response => {
                  console.log(`向用户 ${userId} 发送文档成功:`, response);
                  return { userId, success: true };
                }).catch(error => {
                  console.error(`向用户 ${userId} 发送文档失败:`, error);
                  return { userId, success: false, error };
                })
              );
            }
            
            // 等待所有发送操作完成
            const sendResults = await Promise.all(sendPromises);
            const successCount = sendResults.filter(result => result.success).length;
            const totalAttempted = sendResults.length;
            const totalSelected = selectedChatUsers.value.length;
            
            if (successCount > 0) {
              if (successCount === totalSelected) {
                ElMessage.success(`成功发送文档到所有 ${successCount} 个用户的聊天`);
              } else {
                ElMessage.warning(`部分发送成功: ${successCount}/${totalSelected} 个用户接收到文档`);
              }
              shareDialogVisible.value = false;
            } else if (totalAttempted > 0) {
              ElMessage.error('发送文档失败，请重试');
            } else {
              ElMessage.error('未能创建任何聊天会话，请重试');
            }
          } catch (error) {
            console.error('生成文档文件失败:', error);
            ElMessage.error('生成文档文件失败');
          } finally {
            loading.close();
          }
        } catch (error) {
          console.error('分享文档到聊天失败:', error);
          ElMessage.error('分享文档到聊天失败');
        } finally {
          shareLoading.value = false;
        }
      }
    }
    
    const deleteDocument = (doc) => {
      selectedDocument.value = doc
      deleteDialogVisible.value = true
    }
    
    const confirmDelete = async () => {
      if (!selectedDocument.value) return
      
      deleteLoading.value = true
      try {
        // 记录要删除的文档ID和类别
        const deletedDocId = selectedDocument.value.id;
        const deletedDocCategoryId = selectedDocument.value.category?.id;
        
        // 先关闭对话框，提高用户体验
        deleteDialogVisible.value = false;
        
        // 执行删除操作
        await apiDeleteDocument(deletedDocId)
        ElMessage.success('文档删除成功')
        
        // 强制清除选中的文档
        selectedDocument.value = null;
        
        // 清除可能的缓存数据
        if (window.localStorage) {
          try {
            // 移除可能存在的相关缓存
            localStorage.removeItem(`doc_cache_${deletedDocId}`);
            localStorage.removeItem(`recent_docs_cache`);
            localStorage.removeItem(`doc_list_cache`);
          } catch (e) {
            console.error('清除本地缓存失败:', e);
          }
        }
        
        // 更新刷新触发器
        refreshTrigger.value = Date.now();
        
        // 使用新数组替换原数组，确保Vue能检测到变化 
        documents.value = [...documents.value.filter(doc => doc.id !== deletedDocId)];
        recentDocuments.value = [...recentDocuments.value.filter(doc => doc.id !== deletedDocId)];
        sharedDocuments.value = [...sharedDocuments.value.filter(doc => doc.id !== deletedDocId)];
        
        // 强制更新视图
        await forceUpdate();
        
        // 更新分类中的文档计数
        if (deletedDocCategoryId) {
          const category = documentCategories.value.find(c => c.id === deletedDocCategoryId);
          if (category && category.document_count > 0) {
            category.document_count--;
          }
        }
        
        // 等待DOM更新
        await nextTick();
        
        // 重新导航到文档首页，确保状态全部刷新
        if (router.currentRoute.value.name === 'SmartDocDetail') {
          console.log('从详情页删除文档，重新导航到文档首页');
          
          // 先强制刷新数据，确保导航后数据是最新的
          await reloadAllData();
          
          // 使用replace模式跳转，不留下历史记录，并添加强制刷新参数
          router.replace({ 
            name: 'SmartDoc',
            query: { _refresh: Date.now() } // 添加时间戳参数防止缓存
          });
        } else {
          // 如果已经在文档首页，立即重载数据并强制刷新页面
          await refreshData();
        }
      } catch (error) {
        console.error('删除文档失败', error);
        ElMessage.error('删除文档失败');
        // 如果删除失败，关闭对话框
        deleteDialogVisible.value = false;
      } finally {
        deleteLoading.value = false;
      }
    }
    
    const viewAllDocuments = (type) => {
      if (type === 'recent') {
        // 路由中没有SmartDocList，直接跳转到智能文档首页并滚动到文档列表
        router.push({ name: 'SmartDoc' }).then(() => {
          setTimeout(() => {
            const docSection = document.querySelector('.section');
            if (docSection) {
              docSection.scrollIntoView({ behavior: 'smooth' });
            }
          }, 300);
        });
      }
    }
    
    const selectCategory = (category) => {
      console.log('选择分类:', category);
      
      // 处理不同类型的category参数
      let categoryId;
      if (category === 'all') {
        categoryId = 'all';
      } else if (typeof category === 'string') {
        categoryId = category;
      } else if (typeof category === 'object' && category !== null) {
        categoryId = category.id.toString();
      }
      
      console.log('处理后的分类ID:', categoryId);
      
      // 如果选择的分类与当前分类相同，则不做任何操作
      if (categoryId === searchCategory.value) {
        console.log('分类未变化，不重新加载');
        return;
      }
      
      // 设置新的分类
      searchCategory.value = categoryId;
      
      // 添加动画效果
      documents.value = [];
      createLoading.value = true;
      
      // 重置分页和加载状态
      page.value = 1;
      hasMore.value = true;
      
      // 延迟获取，实现过渡效果
      setTimeout(async () => {
        try {
          // 强制刷新文档列表
          await fetchDocuments(true);
        } catch (error) {
          console.error('获取文档失败:', error);
          ElMessage.error('获取文档列表失败，请刷新页面重试');
        } finally {
          createLoading.value = false;
        }
        
        // 触发一个简单的动画效果，突出显示已筛选的文档
        const docCards = document.querySelectorAll('.doc-card');
        if (docCards && docCards.length > 0) {
          docCards.forEach((card, index) => {
            if (card) {
              card.style.animationDelay = `${index * 50}ms`;
              card.classList.remove('fadeIn');
              setTimeout(() => {
                if (card) {
                  card.classList.add('fadeIn');
                }
              }, 10);
            }
          });
        }
      }, 300);
    };

    // 获取选中分类的颜色
    const getSelectedCategoryColor = () => {
      if (searchCategory.value === 'all') return '#409EFF';
      const selectedCategory = documentCategories.value.find(c => c.id.toString() === searchCategory.value);
      return selectedCategory?.color || '#67C23A';
    };

    // 获取选中分类的名称
    const getSelectedCategoryName = () => {
      if (searchCategory.value === 'all') return '全部文档';
      const selectedCategory = documentCategories.value.find(c => c.id.toString() === searchCategory.value);
      return selectedCategory?.name || '未知分类';
    };
    
    const manageCategories = () => {
      categoryDialogVisible.value = true
      resetCategoryForm()
    }
    
    const editCategory = (category) => {
      editingCategory.value = { ...category }
    }
    
    const resetCategoryForm = () => {
      editingCategory.value = {
        id: '',
        name: '',
        color: '#409EFF',
        description: ''
      }
      if (categoryFormRef.value) {
        categoryFormRef.value.resetFields()
      }
    }
    
    const submitCategory = async () => {
      if (!categoryFormRef.value) return
      
      await categoryFormRef.value.validate(async (valid) => {
        if (valid) {
          categoryLoading.value = true
          try {
            const categoryData = {
              name: editingCategory.value.name,
              color: editingCategory.value.color,
              description: editingCategory.value.description || ''
            }
            
            if (editingCategory.value.id) {
              // 更新分类
              await updateDocumentCategory(editingCategory.value.id, categoryData)
              ElMessage.success('分类更新成功')
            } else {
              // 创建分类
              await createDocumentCategory(categoryData)
              ElMessage.success('分类创建成功')
            }
            
            // 重新获取分类列表
            fetchDocumentCategories()
            resetCategoryForm()
          } catch (error) {
            console.error('保存分类失败:', error)
            ElMessage.error('保存分类失败')
          } finally {
            categoryLoading.value = false
          }
        }
      })
    }
    
    const deleteCategory = (category) => {
      if (category.document_count > 0) {
        ElMessage.warning('该分类下有文档，无法删除')
        return
      }
      
      ElMessageBox.confirm(
        `确定要删除分类"${category.name}"吗？`,
        '删除分类',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          await deleteDocumentCategory(category.id)
          ElMessage.success('分类删除成功')
          fetchDocumentCategories()
        } catch (error) {
          console.error('删除分类失败:', error)
          ElMessage.error('删除分类失败')
        }
      }).catch(() => {})
    }
    
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
    
    const resetCategoryFilter = () => {
      searchCategory.value = 'all'
      page.value = 1
      fetchDocuments(true)
    }
    
    // 添加页面激活钩子，确保从其他页面返回时重新获取数据
    onActivated(() => {
      console.log('SmartDoc组件被激活，重新获取数据');
      reloadAllData();
    });

    // 页面激活后重新加载所有数据的函数
    const reloadAllData = async () => {
      page.value = 1
      try {
        console.log('重新加载所有文档数据...')
        createLoading.value = true
        
        // 添加时间戳防止缓存
        const timestamp = Date.now();
        
        // 清除本地缓存
        try {
          if (window.localStorage) {
            // 清除文档相关的缓存
            localStorage.removeItem('doc_list_cache');
            localStorage.removeItem('recent_docs_cache');
            localStorage.removeItem('doc_categories_cache');
          }
        } catch (e) {
          console.error('清除缓存失败:', e);
        }
        
        // 先获取分类，因为显示文档时需要分类信息
        await fetchDocumentCategories(timestamp)
        
        // 然后并行获取其他数据，但不需要保存返回值
        await Promise.all([
          fetchDocuments(true, false, timestamp),
          fetchRecentDocuments(true, timestamp),
          fetchSharedDocuments(timestamp)
        ])
        
        console.log('数据重新加载完成', {
          分类数量: documentCategories.value.length,
          文档数量: documents.value.length,
          最近文档: recentDocuments.value.length,
          共享文档: sharedDocuments.value.length,
          总计数: totalCount.value,
        })
        
        // 强制更新视图
        await forceUpdate()
        
      } catch (error) {
        console.error('数据重新加载失败:', error)
        ElMessage.error('加载数据失败，请刷新页面')
      } finally {
        createLoading.value = false
      }
    }

    // 提供重载函数给子组件或父组件使用
    provide('reloadDocuments', reloadAllData);
    
    // 监听路由变化，强制刷新数据
    watch(() => route.query._refresh, (newVal) => {
      if (newVal) {
        console.log('检测到路由刷新参数:', newVal);
        refreshTrigger.value = Date.now();
        reloadAllData();
      }
    });

    // 监听路由参数，处理不同情况
    watch(() => route.path, (newPath, oldPath) => {
      console.log('路由变化:', oldPath, '->', newPath);
      if (newPath === '/smartdoc' && oldPath && oldPath.startsWith('/smartdoc/')) {
        // 从文档详情页返回文档列表页，强制刷新
        console.log('从详情页返回列表页，强制刷新数据');
        refreshTrigger.value = Date.now();
        reloadAllData();
      }
    });

    // 手动强制刷新方法
    const refreshData = async () => {
      page.value = 1
      await reloadAllData()
      if (proxy && proxy.$forceUpdate) {
        proxy.$forceUpdate()
      }
    }

    // 处理分页变化的方法 - 简单记录事件
    const onPageChange = (newPage) => {
      console.log(`分页点击事件 - 切换到页面: ${newPage}`);
      
      // 检查页码范围
      const maxPage = Math.ceil(totalCount.value / pageSize);
      if (newPage > maxPage && maxPage > 0) {
        console.warn(`请求的页码 ${newPage} 超出最大页码 ${maxPage}，自动调整为最大页码`);
        setTimeout(() => {
          page.value = maxPage;
        }, 0);
        return;
      }
    }
    
    // 监听页码变化，加载对应页面数据
    watch(() => page.value, async (newPage, oldPage) => {
      console.log(`页码变化: ${oldPage} -> ${newPage}`);
      
      if (newPage === oldPage) return;
      
      // 检查页码范围
      const maxPage = Math.ceil(totalCount.value / pageSize);
      if (newPage > maxPage && maxPage > 0) {
        console.warn(`页码 ${newPage} 超出最大页码 ${maxPage}，自动调整为最大页码`);
        setTimeout(() => {
          page.value = maxPage;
        }, 0);
        return;
      }
      
      try {
        // 显示加载状态
        createLoading.value = true;
        
        // 重置hasMore标志，确保可以加载数据
        hasMore.value = true;
        
        // 获取新页面数据
        await fetchDocuments(false, false, Date.now());
        
        // 滚动到列表顶部
        const docSection = document.querySelector('.section');
        if (docSection) {
          docSection.scrollIntoView({ behavior: 'smooth' });
        }
      } catch (error) {
        console.error('页码变化加载失败:', error);
        ElMessage.error('加载数据失败，请重试');
        
        // 如果是404错误，自动返回有效页码
        if (error.response && error.response.status === 404) {
          console.warn('页码不存在，返回第一页');
          setTimeout(() => {
            page.value = 1;
          }, 0);
        }
      } finally {
        createLoading.value = false;
      }
    });

    // 添加加载更多文档的方法
    const loadMoreDocuments = () => {
      if (loadingMore.value || !hasMore.value) return
      page.value++
      fetchDocuments(false, true)
    }

    // 生命周期钩子
    onMounted(() => {
      console.log('SmartDoc组件mounted，加载数据');
      
      // 检查URL中是否有_refresh参数
      const refreshParam = route.query._refresh;
      if (refreshParam) {
        console.log('检测到URL中的刷新参数:', refreshParam);
        // 强制刷新，确保文档列表是最新的
        refreshTrigger.value = Date.now();
        // 设置一个超短延迟，确保DOM已经完全挂载
        setTimeout(() => {
          reloadAllData();
        }, 10);
      } else {
        // 正常加载数据
        reloadAllData();
      }
    })
    
    const handleImportWord = () => {
      // 创建一个隐藏的文件上传input
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.docx,.doc';
      fileInput.style.display = 'none';
      document.body.appendChild(fileInput);
      
      // 监听文件选择事件
      fileInput.addEventListener('change', async (event) => {
        if (event.target.files.length > 0) {
          const file = event.target.files[0];
          
          // 显示加载中，使用全屏加载，禁止用户操作
          const loadingInstance = ElLoading.service({
            fullscreen: true,
            text: '正在导入Word文档...',
            background: 'rgba(255, 255, 255, 0.8)',
            lock: true // 锁定屏幕，防止用户操作
          });
          
          try {
            // 创建FormData对象
            const formData = new FormData();
            formData.append('file', file);
            
            // 发送请求，调用API
            const response = await importWordDocument(formData);
            
            if (response && response.id) {
              // 先刷新文档首页
              await reloadAllData();
              
              // 显示成功消息
              ElMessage.success('Word文档导入成功');
              
              // 延迟一秒后跳转，确保用户看到刷新效果和成功提示
              setTimeout(() => {
                // 导入成功后跳转到文档详情页
                router.push({
                  name: 'SmartDocDetail',
                  params: { id: response.id },
                  query: { _refresh: Date.now() } // 添加刷新参数，确保详情页刷新
                });
              }, 1000);
            } else {
              ElMessage.error('导入失败：' + (response?.detail || '未知错误'));
            }
          } catch (error) {
            console.error('导入Word文档出错:', error);
            ElMessage.error('导入Word文档失败: ' + (error.message || '未知错误'));
          } finally {
            // 确保一定时间后关闭加载提示，防止界面卡死
            setTimeout(() => {
              loadingInstance.close();
              document.body.removeChild(fileInput);
            }, 500);
          }
        }
      });
      
      // 触发文件选择对话框
      fileInput.click();
    }
    
    const removeSharedUser = (userIdToRemove) => {
      console.log('尝试移除用户权限:', userIdToRemove);
      const userToRemove = existingSharedUsers.value.find(u => u.user_id === userIdToRemove);
      if (userToRemove) {
        console.log('找到要移除权限的用户:', userToRemove);
        // 将用户添加回可选列表
        availableUsers.value.push({ 
          id: userToRemove.user_id, 
          username: userToRemove.username 
        });
        
        // 从已分享列表中移除
        existingSharedUsers.value = existingSharedUsers.value.filter(u => u.user_id !== userIdToRemove);
        console.log('移除后的已分享用户列表:', existingSharedUsers.value);
        
        // 显示提示
        ElMessage({
          message: `已移除用户 ${userToRemove.username} 的权限，点击分享按钮保存更改`,
          type: 'warning'
        });
      } else {
        console.warn('未找到要移除的用户:', userIdToRemove);
      }
    };
    
    return {
      documents,
      recentDocuments,
      sharedDocuments,
      documentCategories,
      searchQuery,
      searchCategory,
      totalDocuments,
      recentEditCount,
      newDocumentDialogVisible,
      shareDialogVisible,
      deleteDialogVisible,
      documentCreateType,
      newDocumentForm,
      aiDocumentForm,
      blankFormRules,
      aiFormRules,
      blankFormRef,
      aiFormRef,
      selectedDocument,
      selectedUsers,
      selectedUsersWithPermissions,
      availableUsers,
      availableChatUsers,
      createLoading,
      shareLoading,
      deleteLoading,
      createNewDocument,
      submitNewDocument,
      openDocument,
      editDocument,
      submitEditDocument,
      exportDocument,
      shareDocument,
      confirmShare,
      deleteDocument,
      confirmDelete,
      viewAllDocuments,
      formatDate,
      categoryDialogVisible,
      editingCategory,
      categoryFormRef,
      categoryLoading,
      categoryFormRules,
      editCategory,
      resetCategoryForm,
      submitCategory,
      deleteCategory,
      resetCategoryFilter,
      selectCategory,
      getSelectedCategoryColor,
      getSelectedCategoryName,
      manageCategories,
      reloadAllData,
      refreshData,
      refreshTrigger,
      hasMore,
      loadingMore,
      loadMoreDocuments,
      exportToPdf,
      exportToWord,
      // 添加编辑对话框相关变量
      editDialogVisible,
      editDocumentForm,
      editFormRef,
      editLoading,
      editFormRules,
      // 添加分页处理方法
      onPageChange,
      page,
      pageSize,
      totalCount,
      // 开发环境标志
      $_isDev,
      // 添加直接API调用函数
      fetchDocuments,
      // 添加分享方式相关变量
      shareMode,
      shareFormat,
      selectedChatUsers,
      handleImportWord,
      getUsernameById,
      handleUserSelectionChange,
      handleShareModeChange,
      getCurrentUserId,
      existingSharedUsers,
      removeSharedUser
    }
  }
}
</script>

<style scoped>
.smartdoc-home-container {
  padding: 20px;
  background-color: var(--el-bg-color-page);
}

/* 页面标题和操作区 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: var(--el-text-color-primary);
}

.page-description {
  color: var(--el-text-color-secondary);
  margin: 4px 0 0 0;
}

.right-section {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input {
  width: 240px;
}

/* 统计卡片 */
.stats-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  transition: all 0.3s;
  background-color: var(--el-bg-color-overlay);
  border-color: var(--el-border-color-lighter);
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--el-box-shadow-light);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 8px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.doc-icon {
  background-color: #409EFF;
}

.edit-icon {
  background-color: #67C23A;
}

.share-icon {
  background-color: #E6A23C;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

/* 区域通用样式 */
.section {
  margin-bottom: 32px;
}

/* 分类区域特殊样式 */
.category-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-tag {
  background-color: #f0f2f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 文档卡片 */
.document-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.doc-card {
  transition: all 0.3s ease;
  height: 230px; /* 设置固定高度 */
  display: flex;
  flex-direction: column;
}

.doc-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  padding: 16px;
  min-height: 0;
}

.doc-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--el-box-shadow-light);
}

/* 鼠标悬浮时显示操作按钮 */
.doc-card:hover .doc-actions {
  opacity: 1;
  transform: translateY(0);
}

.doc-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.doc-info {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.doc-type-tag {
  font-size: 12px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.doc-category-tag {
  font-size: 12px;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
}

/* 共享标签样式 */
.doc-shared-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #E6A23C;
  background-color: #fdf6ec;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  border: 1px solid #f5dab1;
}


:deep([data-theme="dark"]) .doc-shared-tag span,
:deep(body.is-dark) .doc-shared-tag span,
[data-theme="dark"] .doc-shared-tag span,
html[data-theme="dark"] .doc-shared-tag span {
  color: #000000 !important; 
  font-weight: 400; 
}

.doc-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.5;
  height: calc(1.5em * 2); /* 固定两行高度 */
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-all;
}

.doc-preview {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
  height: calc(1.6em * 3); /* 固定三行高度 */
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  word-break: break-all;
  margin-bottom: 12px;
}

.doc-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0 4px;
  border-top: 1px solid var(--el-border-color-lighter);
  margin-top: auto;
  position: relative;
  z-index: 2;
}

.doc-time {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.doc-actions {
  display: flex;
  gap: 8px;
  position: relative;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.2s ease-in-out;
}

.new-doc-card {
  border: 2px dashed var(--el-border-color);
  background-color: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  animation: fadeIn 0.4s ease-in-out;
}

.new-doc-card:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.new-doc-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
}

.new-doc-content .el-icon {
  font-size: 32px;
}

/* 分类卡片 */
.category-cards {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.category-card {
  min-width: 180px;
  height: 80px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
  padding: 12px 16px;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
  background-color: var(--el-fill-color-light);
}

.category-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--el-box-shadow-light);
  background-color: var(--el-color-primary-light-9);
}

.category-active {
  transform: translateY(-2px);
  box-shadow: var(--el-box-shadow-light);
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.category-selected-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: var(--el-color-primary);
  transition: all 0.3s;
}

.category-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
  margin-right: 12px;
  transition: all 0.3s;
}

.category-active .category-icon {
  transform: scale(1.1);
}

.category-info {
  display: flex;
  flex-direction: column;
}

.category-info h4 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  transition: all 0.3s;
}

.category-active .category-info h4 {
  color: var(--el-color-primary);
  font-weight: 600;
}

.category-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.mt-4 {
  margin-top: 16px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.category-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.category-list {
  margin-bottom: 20px;
}

.category-form {
  margin-top: 20px;
}

.color-preview {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  margin-right: 8px;
  vertical-align: middle;
}

.color-value {
  margin-left: 12px;
  color: var(--el-text-color-regular);
}

.category-select {
  width: 200px;
}

.doc-menu {
  color: var(--el-text-color-secondary);
  cursor: pointer;
  position: relative;
}

/* 筛选状态栏样式 */
.filter-status-bar {
  background-color: var(--el-color-primary-light-9);
  padding: 12px 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  transition: all 0.3s ease;
  animation: slideDown 0.3s ease-in-out;
  box-shadow: var(--el-box-shadow-light);
  border-left: 4px solid var(--el-color-primary);
  position: relative;
  overflow: hidden;
}

/* 确保深色模式下的筛选状态栏有足够的对比度 */
:deep(.dark .filter-status-bar) {
  background-color: var(--el-color-primary-dark-2);
  border-left-color: var(--el-color-primary-light-3);
}

.filter-bar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-title {
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-primary);
}

.filter-category {
  padding: 4px 10px;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.filter-actions {
  display: flex;
  align-items: center;
}

.section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--el-text-color-primary);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 添加动画 */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 20;
}

.pagination-container :deep(.el-pagination) {
  user-select: none;
}

.pagination-container :deep(.el-pagination button),
.pagination-container :deep(.el-pagination .el-pager li) {
  cursor: pointer !important;
  z-index: 30;
  position: relative;
}

.pagination-debug {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
  background-color: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
}

/* 添加以下CSS，确保按钮区域独立可点击 */
.btn-container {
  position: relative;
  z-index: 5;
}

.doc-actions .el-button {
  position: relative;
  z-index: 5;
}

/* 确保下拉菜单显示在最上层 */
:deep(.el-dropdown-menu) {
  z-index: 3000 !important;
}

/* 调整卡片内容区域的点击行为 */
.card-content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
  min-height: 0;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 添加文档卡片的动画效果 */
.document-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.doc-card {
  animation: fadeIn 0.4s ease-in-out;
}

.fadeIn {
  animation: fadeIn 0.4s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 临时导出容器样式 */
.temp-export-container {
  position: fixed;
  top: -9999px;
  left: -9999px;
  width: 210mm; /* A4宽度 */
  background: var(--el-bg-color);
  padding: 20px;
  z-index: -1;
  font-family: SimSun, Arial, sans-serif;
  font-size: 12pt;
  line-height: 1.5;
}

.temp-export-container img {
  max-width: 100%;
  height: auto;
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
  background-color: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #eaeaea;
}

.user-name {
  min-width: 60px;
  margin-right: 12px;
  font-weight: 500;
}

.permission-info {
  display: flex;
  align-items: center;
}

/* 确保表单提示文本样式正确 */
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.dialog-tabs {
  position: absolute;
  top: 55px; /* Adjust this value to position the tabs correctly */
  left: 20px;
}
</style> 

<style>
/* --- 深色模式分享弹窗样式 --- */
html[data-theme="dark"] .share-dialog .el-dialog {
  background-color: #2c2c2c;
}

html[data-theme="dark"] .share-dialog .el-dialog__header {
  border-bottom: 1px solid #4f4f4f;
}

html[data-theme="dark"] .share-dialog .el-dialog__title {
  color: #e0e0e0;
}

html[data-theme="dark"] .share-dialog .el-dialog__body {
  color: #cccccc;
}

html[data-theme="dark"] .share-dialog p {
  color: #cccccc;
}

html[data-theme="dark"] .share-dialog .el-form-item__label {
  color: #cccccc;
}

html[data-theme="dark"] .share-dialog .el-radio__label {
  color: #cccccc;
}

html[data-theme="dark"] .share-dialog .el-radio__input .el-radio__inner {
    background-color: transparent;
    border-color: #8c8c8c;
}

html[data-theme="dark"] .share-dialog .el-radio__input.is-checked .el-radio__inner {
    border-color: var(--el-color-primary);
    background-color: var(--el-color-primary);
}

html[data-theme="dark"] .share-dialog .user-permission-item {
  background-color: #383838;
  border-color: #4f4f4f;
}

html[data-theme="dark"] .share-dialog .user-permission-item .user-name {
  color: #e0e0e0;
}

html[data-theme="dark"] .share-dialog .el-tag {
    background-color: #4f4f4f;
    border-color: #6a6a6a;
    color: #cccccc;
}

html[data-theme="dark"] .share-dialog .user-permission-item .el-button--danger.is-link {
  color: #ff7b7b;
}

html[data-theme="dark"] .share-dialog .user-permission-item .el-button--danger.is-link:hover {
  color: #ff5252;
}

html[data-theme="dark"] .share-dialog .form-tip {
  color: #a0a0a0;
}

html[data-theme="dark"] .share-dialog .el-select .el-input__wrapper {
  background-color: #383838;
  box-shadow: none;
  border: 1px solid #4f4f4f;
}

html[data-theme="dark"] .share-dialog .el-select .el-input__inner {
  color: #e0e0e0;
}

/* Select dropdown panel */
html[data-theme="dark"] .share-dialog-popper.el-popper {
  background-color: #2c2c2c;
  border: 1px solid #4f4f4f;
}

html[data-theme="dark"] .share-dialog-popper .el-select-dropdown__item {
  color: #cccccc;
}

html[data-theme="dark"] .share-dialog-popper .el-select-dropdown__item.is-selected {
  color: var(--el-color-primary);
}

html[data-theme="dark"] .share-dialog-popper .el-select-dropdown__item.hover,
html[data-theme="dark"] .share-dialog-popper .el-select-dropdown__item:hover {
  background-color: #383838;
}

html[data-theme="dark"] .share-dialog-popper .el-popper__arrow::before {
  background: #2c2c2c;
  border-right-color: #4f4f4f !important;
  border-bottom-color: #4f4f4f !important;
}
</style>
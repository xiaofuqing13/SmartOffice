<template>
  <div class="management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Collection /></el-icon>
            <span>知识库管理</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索知识库文章..."
              clearable
              @clear="fetchArticles"
              @input="debouncedFetchArticles"
              class="search-input"
            >
              <template #append>
                <el-button :icon="Search" />
              </template>
            </el-input>
            <el-button type="success" @click="openBuildModal">构建知识库</el-button>
            <el-button type="info" @click="openCategoryModal()">管理分类</el-button>
            <el-button type="primary" :icon="Upload" @click="openArticleModal()">上传文件</el-button>
          </div>
        </div>
      </template>
      <!-- Main content will go here -->
      <el-table :data="articles" v-loading="loading" border>
        <el-table-column prop="title" label="标题" min-width="200"></el-table-column>
        <el-table-column prop="original_filename" label="文件名" min-width="200"></el-table-column>
        <el-table-column prop="category_name" label="分类" width="120"></el-table-column>
        <el-table-column prop="company_name" label="所属公司" width="150"></el-table-column>
        <el-table-column prop="creator_name" label="上传者" width="120"></el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
            <template #default="scope">
                {{ new Date(scope.row.created_at).toLocaleString() }}
            </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" :icon="Edit" @click="openArticleModal(scope.row)"></el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="confirmDeleteArticle(scope.row)"></el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pagination.pageSize"
        :current-page="pagination.page"
        @current-change="handlePageChange"
        style="margin-top: 20px; text-align: right;"
      />
    </el-card>

    <!-- Category Management Modal -->
    <el-dialog v-model="isCategoryModalOpen" title="管理分类" width="60%">
      <div class="category-dialog-content">
        <div class="category-list-section">
           <div class="section-header">
            <h5>已有分类</h5>
            <el-button 
              type="primary" 
              size="small" 
              @click="resetCategoryForm">
              <el-icon><Plus /></el-icon> 新增分类
            </el-button>
          </div>
          <div v-if="!categories.length" class="category-items">
             <el-empty description="暂无分类" />
          </div>
          <div v-else class="category-items">
            <div 
                v-for="category in categories" 
                :key="category.id" 
                class="category-list-item"
                :class="{ 'selected': currentCategory.id === category.id }"
                @click="selectCategoryForEdit(category)"
            >
              <div class="category-info">
                 <div class="category-icon" :style="{'background-color': category.color}">
                    <el-icon><component :is="category.icon || 'Document'" /></el-icon>
                 </div>
                <span class="category-name-section">{{ category.name }}</span>
              </div>
               <div class="category-actions">
                    <el-button type="primary" size="small" plain :icon="Edit" @click.stop="selectCategoryForEdit(category)" />
                    <el-button type="danger" size="small" plain :icon="Delete" @click.stop="confirmDeleteCategory(category)" />
                </div>
            </div>
          </div>
        </div>
        <div class="category-form-section">
          <div class="section-header">
             <h5>{{ isEditingCategory ? '编辑分类' : '新增分类' }}</h5>
             <el-button v-if="isEditingCategory" text @click="resetCategoryForm">取消</el-button>
          </div>
          <el-form :model="currentCategory" ref="categoryForm" label-position="top">
            <el-form-item label="分类名称" prop="name" required>
              <el-input v-model="currentCategory.name" />
            </el-form-item>
             <el-form-item label="所属公司" prop="company" required>
              <el-select v-model="currentCategory.company" placeholder="请选择公司" style="width: 100%;">
                <el-option v-for="company in companies" :key="company.id" :label="company.name" :value="company.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="分类描述" prop="description">
              <el-input v-model="currentCategory.description" type="textarea" />
            </el-form-item>
            <el-form-item label="图标" prop="icon">
               <el-select v-model="currentCategory.icon" placeholder="选择一个图标" style="width: 100%;">
                <el-option v-for="icon in availableIcons" :key="icon.name" :label="icon.label" :value="icon.name">
                  <div style="display: flex; align-items: center;">
                    <el-icon style="margin-right: 8px;"><component :is="icon.component" /></el-icon>
                    <span>{{ icon.label }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="颜色" prop="color">
              <el-color-picker v-model="currentCategory.color" />
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="saveCategory">保存</el-button>
                <el-button @click="resetCategoryForm" v-if="!isEditingCategory">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-dialog>

    <!-- Add/Edit Article Modal -->
    <el-dialog v-model="isArticleModalOpen" :title="currentArticle.id ? '编辑文件信息' : '上传新文件'" width="50%">
      <el-form :model="currentArticle" ref="articleForm" label-width="80px">
        <el-form-item label="标题" prop="title" required>
          <el-input v-model="currentArticle.title" />
        </el-form-item>
        <el-form-item label="公司" prop="company" required>
            <el-select v-model="currentArticle.company" placeholder="请选择公司" style="width: 100%;" @change="handleCompanyChange">
              <el-option v-for="company in companies" :key="company.id" :label="company.name" :value="company.id" />
            </el-select>
        </el-form-item>
        <el-form-item label="分类" prop="category">
            <el-select v-model="currentArticle.category" placeholder="可选，请先选择公司" style="width: 100%;" :disabled="!currentArticle.company" clearable>
              <el-option v-for="category in companyCategories" :key="category.id" :label="category.name" :value="category.id" />
            </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="currentArticle.description" type="textarea" />
        </el-form-item>
        <el-form-item label="文件" prop="original_file">
            <div v-if="currentArticle.id && currentArticle.original_filename && !showUpload">
                <span class="file-info">当前文件: {{ currentArticle.original_filename }} ({{ currentArticle.file_size }} KB)</span>
                <el-button @click="showUpload = true" type="primary" link style="margin-left: 10px;">替换文件</el-button>
            </div>
            <el-upload
                v-else
                ref="upload"
                action="#"
                :auto-upload="false"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                :limit="1"
                class="upload-component"
            >
                <template #trigger>
                <el-button type="primary">选择文件</el-button>
                </template>
                <template #tip>
                <div class="el-upload__tip">
                    只能上传单个文件，文件大小不应超过系统限制。
                </div>
                </template>
            </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeArticleModal">取消</el-button>
        <el-button type="primary" @click="saveArticle">保存</el-button>
      </template>
    </el-dialog>

    <!-- Build Knowledge Base Modal -->
    <el-dialog v-model="isBuildModalOpen" title="构建公司知识库" width="70%" @close="stopStatusPolling">
        <el-table 
            :data="buildStatuses" 
            v-loading="isBuildStatusLoading"
            @selection-change="handleSelectionChange"
            border
            row-key="company_id"
        >
            <el-table-column type="selection" width="55" :selectable="isCompanySelectable" />
            <el-table-column prop="company_name" label="公司名称" />
            <el-table-column prop="file_count" label="文件数" width="80" />
            <el-table-column prop="status" label="构建状态">
                <template #default="scope">
                    <el-tooltip v-if="scope.row.file_count === 0" content="没有文件，无法构建" placement="top">
                        <el-tag type="info">
                            无法构建
                        </el-tag>
                    </el-tooltip>
                    <el-tag v-else :type="getStatusTagType(scope.row.status)">
                        {{ getStatusText(scope.row.status) }}
                        <el-icon v-if="scope.row.status === 'processing'" class="is-loading"><Loading /></el-icon>
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="last_built_at" label="上次构建时间">
                 <template #default="scope">
                    {{ scope.row.last_built_at ? new Date(scope.row.last_built_at).toLocaleString() : 'N/A' }}
                </template>
            </el-table-column>
            <el-table-column prop="processing_message" label="消息" show-overflow-tooltip />
            <el-table-column label="操作" width="120">
                <template #default="scope">
                    <el-tooltip content="没有文件，无法构建" :disabled="scope.row.file_count > 0">
                        <div style="display: inline-block"> <!-- Wrapper for tooltip on disabled button -->
                             <el-button 
                                type="primary" 
                                size="small" 
                                @click="triggerBuildForCompanies([scope.row.company_id])"
                                :disabled="isCompanyBuilding(scope.row.company_id) || scope.row.file_count === 0"
                            >
                                构建
                            </el-button>
                        </div>
                    </el-tooltip>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <div class="build-footer">
                <el-button 
                    type="primary" 
                    @click="triggerBuildForCompanies(selectedCompanyIds)"
                    :disabled="selectedCompanyIds.length === 0 || isAnyCompanyBuilding(selectedCompanyIds)"
                >
                    构建选中 ({{ selectedCompanyIds.length }})
                </el-button>
                <el-button @click="fetchBuildStatuses" :icon="Refresh">刷新状态</el-button>
            </div>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import adminApi from '@/api/admin';
import { ElMessage, ElMessageBox, ElCard, ElIcon, ElInput, ElButton, ElTable, ElTableColumn, ElPagination, ElDialog, ElForm, ElFormItem, ElSelect, ElOption, ElUpload, ElColorPicker, ElEmpty, ElTooltip } from 'element-plus';
import { Collection, Search, Upload, Edit, Delete, Plus, Document, Folder, DataAnalysis, TrendCharts, Reading, MagicStick, Loading, Refresh } from '@element-plus/icons-vue';

const articles = ref([]);
const categories = ref([]);
const companies = ref([]);
const loading = ref(true);
const searchQuery = ref('');
const total = ref(0);
const pagination = reactive({
  page: 1,
  pageSize: 10,
});

const isCategoryModalOpen = ref(false);
const isSingleCategoryModalOpen = ref(false);
const currentCategory = ref({});
const categoryForm = ref(null);
const isEditingCategory = computed(() => !!currentCategory.value.id);

const availableIcons = [
  { name: 'Document', label: '文档', component: Document },
  { name: 'Folder', label: '文件夹', component: Folder },
  { name: 'DataAnalysis', label: '数据分析', component: DataAnalysis },
  { name: 'TrendCharts', label: '趋势图', component: TrendCharts },
  { name: 'Reading', label: '阅读', component: Reading },
  { name: 'MagicStick', label: '魔术棒', component: MagicStick },
];

const isArticleModalOpen = ref(false);
const currentArticle = ref({});
const articleForm = ref(null);
const companyCategories = ref([]);
const upload = ref(null);
const showUpload = ref(false);

const isBuildModalOpen = ref(false);
const buildStatuses = ref([]);
const isBuildStatusLoading = ref(false);
const selectedCompanyIds = ref([]);
const buildingCompanyIds = ref(new Set());
let statusPollInterval = null;

let searchTimeout = null;

const fetchCategories = async () => {
  try {
    const response = await adminApi.getKnowledgeCategories({ all: 'true' });
    categories.value = response.data;
  } catch (error) {
    ElMessage.error('获取分类列表失败');
  }
};

const fetchCompanies = async () => {
  try {
    const response = await adminApi.getCompanies({ all: 'true' });
    companies.value = response.data;
  } catch (error) {
    ElMessage.error('获取公司列表失败');
  }
};

const openCategoryModal = async () => {
  await fetchCompanies();
  await fetchCategories();
  resetCategoryForm();
  isCategoryModalOpen.value = true;
};

const closeSingleCategoryModal = () => {
  isSingleCategoryModalOpen.value = false;
  currentCategory.value = {};
  categoryForm.value?.resetFields();
};

const resetCategoryForm = () => {
  currentCategory.value = {
    id: null,
    name: '',
    description: '',
    icon: 'Document',
    color: '#409EFF',
    company: null,
  };
  categoryForm.value?.resetFields();
};

const selectCategoryForEdit = (category) => {
  currentCategory.value = { ...category };
};

const saveCategory = async () => {
  try {
    if (currentCategory.value.id) {
      await adminApi.updateKnowledgeCategory(currentCategory.value.id, currentCategory.value);
    } else {
      await adminApi.createKnowledgeCategory(currentCategory.value);
    }
    ElMessage.success('分类保存成功');
    closeSingleCategoryModal();
    fetchCategories(); // Refresh list in the background
  } catch (error) {
    ElMessage.error('保存分类失败');
  }
};

const confirmDeleteCategory = (category) => {
  ElMessageBox.confirm(`确定要删除分类 "${category.name}" 吗?`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await adminApi.deleteKnowledgeCategory(category.id);
      ElMessage.success('分类删除成功');
      fetchCategories(); // Refresh list
    } catch (error) {
      ElMessage.error('删除分类失败');
    }
  });
};

const debouncedFetchArticles = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    pagination.page = 1;
    fetchArticles();
  }, 300);
};

const fetchArticles = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.page,
      size: pagination.pageSize,
      search: searchQuery.value
    };
    const response = await adminApi.getKnowledgeBases(params);
    articles.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    ElMessage.error('获取文章列表失败');
    articles.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

const openArticleModal = async (article = {}) => {
  await fetchCompanies();
  currentArticle.value = { ...article };

  if (article.id) {
    showUpload.value = false; // 编辑模式下，默认不显示上传组件
  } else {
    showUpload.value = true; // 新建模式下，直接显示上传组件
  }
  
  if (currentArticle.value.company) {
    await fetchCategoriesForCompany(currentArticle.value.company);
  } else {
    companyCategories.value = [];
  }
  isArticleModalOpen.value = true;
};

const closeArticleModal = () => {
  isArticleModalOpen.value = false;
  currentArticle.value = {};
  companyCategories.value = [];
  upload.value?.clearFiles();
  articleForm.value?.resetFields();
};

const saveArticle = async () => {
  try {
    const dataToSave = { ...currentArticle.value };
    if (!dataToSave.id && !dataToSave.original_file) {
        ElMessage.error('请选择一个文件上传');
        return;
    }

    if (dataToSave.id) {
      await adminApi.updateKnowledgeBase(dataToSave.id, dataToSave);
    } else {
      await adminApi.createKnowledgeBase(dataToSave);
    }
    ElMessage.success('文件信息保存成功');
    closeArticleModal();
    fetchArticles();
  } catch (error) {
    const errorMsg = error.response?.data ? JSON.stringify(error.response.data) : '保存文件信息失败';
    ElMessage.error(errorMsg);
  }
};

const confirmDeleteArticle = (article) => {
  ElMessageBox.confirm(`确定要删除文件 "${article.title}" 吗? 这将一并删除关联的文件和数据。`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await adminApi.deleteKnowledgeBase(article.id);
      ElMessage.success('文件删除成功');
      fetchArticles(); // Refresh list
    } catch (error) {
      ElMessage.error('删除文件失败');
    }
  });
};

const handlePageChange = (newPage) => {
  pagination.page = newPage;
  fetchArticles();
};

const handleCompanyChange = async (companyId) => {
  currentArticle.value.category = null;
  companyCategories.value = [];
  if (companyId) {
    await fetchCategoriesForCompany(companyId);
  }
};

const fetchCategoriesForCompany = async (companyId) => {
  try {
    const response = await adminApi.getKnowledgeCategories({ all: 'true', company_id: companyId });
    companyCategories.value = response.data;
  } catch (error) {
    ElMessage.error('获取该公司下的分类失败');
  }
};

const handleFileChange = (file) => {
    currentArticle.value.original_file = file.raw;
};

const handleFileRemove = () => {
    currentArticle.value.original_file = null;
};

const openBuildModal = () => {
    isBuildModalOpen.value = true;
    fetchBuildStatuses();
};

const fetchBuildStatuses = async () => {
    isBuildStatusLoading.value = true;
    try {
        const response = await adminApi.getKnowledgeBuildStatus();
        buildStatuses.value = response.data;
    } catch (error) {
        ElMessage.error('获取构建状态失败');
    } finally {
        isBuildStatusLoading.value = false;
    }
};

const handleSelectionChange = (selection) => {
    selectedCompanyIds.value = selection.map(item => item.company_id);
};

const triggerBuildForCompanies = async (companyIds) => {
    if (companyIds.length === 0) return;
    try {
        const response = await adminApi.buildKnowledgeForCompanies(companyIds);
        ElMessage.success(response.data.message || '构建任务已启动');
        companyIds.forEach(id => buildingCompanyIds.value.add(id));
        fetchBuildStatuses();
        startStatusPolling();
    } catch (error) {
        ElMessage.error('启动构建任务失败');
    }
};

const startStatusPolling = () => {
    if (statusPollInterval) return; // 避免重复启动
    statusPollInterval = setInterval(async () => {
        await fetchBuildStatuses();
        // 检查是否有仍在处理中的构建
        const stillProcessing = buildStatuses.value.some(s => s.status === 'processing' || s.status === 'pending');
        if (!stillProcessing) {
            stopStatusPolling();
            buildingCompanyIds.value.clear();
            ElMessage.info('所有构建任务已完成。');
        }
    }, 5000); // 每5秒轮询一次
};

const stopStatusPolling = () => {
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
        statusPollInterval = null;
    }
};

const getStatusTagType = (status) => {
    switch (status) {
        case 'completed': return 'success';
        case 'processing': return 'primary';
        case 'pending': return 'warning';
        case 'failed': return 'danger';
        default: return 'info';
    }
};

const getStatusText = (status) => {
    const map = {
        'completed': '成功',
        'processing': '构建中',
        'pending': '等待中',
        'failed': '失败',
        'not_built': '未构建'
    };
    return map[status] || '未知';
};

const isCompanyBuilding = (companyId) => {
    const status = buildStatuses.value.find(s => s.company_id === companyId)?.status;
    return status === 'processing' || status === 'pending';
};

const isAnyCompanyBuilding = (companyIds) => {
    // 增加一个检查，确保所选的公司都有文件
    const hasFiles = companyIds.every(id => {
        const company = buildStatuses.value.find(s => s.company_id === id);
        return company && company.file_count > 0;
    });
    if (!hasFiles) return true;

    return companyIds.some(id => isCompanyBuilding(id));
};

const isCompanySelectable = (row) => {
    return row.file_count > 0;
};

onMounted(() => {
  // initial fetch
  fetchArticles();
});
</script>

<style scoped>
@import './shared-styles.css';

.file-info {
    font-size: 14px;
    color: #606266;
}

.upload-component {
    width: 100%;
}

.category-dialog-content {
  display: flex;
  gap: 20px;
  min-height: 400px;
}

.category-list-section, .category-form-section {
  padding: 10px;
  border-radius: 8px;
}

.category-list-section {
  flex: 1;
  border-right: 1px solid #e0e0e0;
  padding-right: 20px;
  display: flex;
  flex-direction: column;
}

.category-form-section {
  flex: 1.2;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.category-items {
  overflow-y: auto;
  max-height: 350px;
}

.category-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-bottom: 5px;
}

.category-list-item:hover {
  background-color: #f5f7fa;
}

.category-list-item.selected {
  background-color: #ecf5ff;
  border: 1px solid #b3d8ff;
}

.category-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.category-color {
  width: 8px;
  height: 20px;
  border-radius: 4px;
  flex-shrink: 0;
}

.category-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.category-icon .el-icon {
  color: white;
}

.build-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}
</style>

<style>
.category-dialog-content .el-form-item {
  margin-bottom: 22px;
}
</style> 
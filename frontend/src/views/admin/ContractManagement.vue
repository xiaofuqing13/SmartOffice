<template>
  <div class="management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header d-flex justify-content-between align-items-center">
          <div class="header-left">
            <el-icon class="header-icon"><DocumentChecked /></el-icon>
            <span>合同管理</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索合同..."
              clearable
              @clear="fetchItems"
              @input="debouncedFetchItems"
              class="search-input"
            >
              <template #append>
                <el-button :icon="Search" />
              </template>
            </el-input>
          </div>
          <div>
            <el-button type="primary" @click="goToTemplateManagement" :icon="DocumentChecked">管理模板</el-button>
          </div>
        </div>
      </template>
      <div class="table-container">
        <el-table :data="items" v-loading="loading" style="width: 100%">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="title" label="合同标题" sortable />
          <el-table-column prop="company_name" label="所属公司" sortable />
          <el-table-column prop="creator_name" label="创建者" sortable />
          <el-table-column prop="created_at" label="创建时间" sortable>
            <template #default="scope">
              {{ new Date(scope.row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button text type="primary" size="small" @click="openPreviewModal(scope.row)">查看</el-button>
              <el-button text type="danger" size="small" @click="confirmDelete(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

       <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>

     <!-- 合同预览模态框 -->
      <el-dialog v-model="isPreviewModalOpen" :title="previewItem.title" width="60%">
        <div v-if="previewItem.id" class="preview-content">
          <div class="preview-header">
            <h3>{{ previewItem.title }}</h3>
            <p>
              <span><strong>公司:</strong> {{ previewItem.company_name }}</span> |
              <span><strong>创建者:</strong> {{ previewItem.creator_name }}</span>
            </p>
          </div>
          <div class="content-body" v-html="previewItem.content"></div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closePreviewModal">关闭</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import adminApi from '@/api/admin';
import { ElMessage, ElMessageBox, ElCard, ElIcon, ElInput, ElButton, ElTable, ElTableColumn, ElPagination, ElDialog } from 'element-plus';
import { DocumentChecked, Search } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';

const items = ref([]);
const loading = ref(true);
const searchQuery = ref('');
const total = ref(0);
const pagination = reactive({
  page: 1,
  pageSize: 10,
});
const isPreviewModalOpen = ref(false);
const previewItem = ref({});
let searchTimeout = null;
const router = useRouter();

const fetchItems = async () => {
  loading.value = true;
  try {
    const params = { 
      search: searchQuery.value,
      page: pagination.page,
      page_size: pagination.pageSize,
    };
    const response = await adminApi.getContracts(params);
    items.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("获取合同列表失败:", error);
    ElMessage.error('获取合同列表失败');
  } finally {
    loading.value = false;
  }
};

const debouncedFetchItems = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    pagination.page = 1;
    fetchItems();
  }, 300);
};

const openPreviewModal = async (item) => {
  try {
    const response = await adminApi.getContractDetail(item.id);
    previewItem.value = response.data;
    isPreviewModalOpen.value = true;
  } catch (error) {
    ElMessage.error('获取合同详情失败');
    console.error('获取合同详情失败:', error);
  }
};

const closePreviewModal = () => {
  isPreviewModalOpen.value = false;
  previewItem.value = {};
};

const confirmDelete = (item) => {
  ElMessageBox.confirm(
    `确定要删除合同【${item.title}】吗？此操作不可恢复。`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await adminApi.deleteContract(item.id);
      ElMessage.success('合同删除成功');
      fetchItems();
    } catch (error) {
      ElMessage.error('删除失败，请稍后重试');
      console.error("删除合同失败:", error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const handleSizeChange = (val) => {
  pagination.pageSize = val;
  fetchItems();
};

const handleCurrentChange = (val) => {
  pagination.page = val;
  fetchItems();
};

const goToTemplateManagement = () => {
  router.push({ name: 'AdminContractTemplateManagement' });
};

onMounted(fetchItems);
</script>

<style scoped>
@import './shared-styles.css';

.management-container {
  padding: 20px;
}

.preview-content {
  max-height: 60vh;
  overflow-y: auto;
}
.preview-header {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 15px;
  margin-bottom: 15px;
  text-align: center;
}
.preview-header h3 {
  margin: 0;
  font-size: 1.5em;
}
.preview-header p {
  margin: 10px 0 0;
  color: #606266;
}
.preview-header p span {
  margin: 0 10px;
}
.content-body {
  padding: 10px;
}

</style> 
<template>
  <div class="management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Document /></el-icon>
            <span>智能文档管理</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索文档..."
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
        </div>
      </template>
      <div class="table-container">
        <el-table :data="items" v-loading="loading" style="width: 100%">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="title" label="文档标题" sortable />
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

     <!-- 文档预览模态框 -->
      <el-dialog v-model="isPreviewModalOpen" :title="previewItem.title" width="60%">
        <div class="preview-content" v-html="previewItem.content"></div>
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
import { Document, Search } from '@element-plus/icons-vue';

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

const fetchItems = async () => {
  loading.value = true;
  try {
    const params = { 
      search: searchQuery.value,
      page: pagination.page,
      page_size: pagination.pageSize,
    };
    const response = await adminApi.getSmartDocs(params);
    items.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("获取文档列表失败:", error);
    ElMessage.error('获取文档列表失败');
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
    const response = await adminApi.getSmartDocDetail(item.id);
    previewItem.value = response.data;
    isPreviewModalOpen.value = true;
  } catch (error) {
    ElMessage.error('获取文档详情失败');
    console.error('获取文档详情失败:', error);
  }
};

const closePreviewModal = () => {
  isPreviewModalOpen.value = false;
  previewItem.value = {};
};

const confirmDelete = (item) => {
  ElMessageBox.confirm(
    `确定要删除文档【${item.title}】吗？此操作不可恢复。`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await adminApi.deleteSmartDoc(item.id);
      ElMessage.success('文档删除成功');
      fetchItems();
    } catch (error) {
      ElMessage.error('删除失败，请稍后重试');
      console.error("删除文档失败:", error);
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
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
</style> 
<template>
  <div class="management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><OfficeBuilding /></el-icon>
            <span>公司管理</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索公司..."
              clearable
              @clear="fetchCompanies"
              @input="debouncedFetchCompanies"
              class="search-input"
            >
              <template #append>
                <el-button :icon="Search" />
              </template>
            </el-input>
            <el-button type="primary" :icon="Plus" @click="openModal()">添加公司</el-button>
          </div>
        </div>
      </template>
      <div class="table-container">
        <el-table :data="companies" v-loading="loading" style="width: 100%">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="name" label="公司名称" sortable />
          <el-table-column prop="industry" label="行业" sortable />
          <el-table-column prop="size" label="规模" sortable />
          <el-table-column prop="address" label="地址" min-width="150" />
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button text type="primary" size="small" @click="openModal(scope.row)">编辑</el-button>
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

      <!-- 添加/编辑模态框 -->
      <el-dialog v-model="isModalOpen" :title="currentItem.id ? '编辑公司' : '添加公司'" width="500px">
        <el-form :model="currentItem" ref="itemForm" label-width="80px">
          <el-form-item label="公司名称" prop="name" :rules="[{ required: true, message: '请输入公司名称' }]">
            <el-input v-model="currentItem.name" />
          </el-form-item>
          <el-form-item label="行业" prop="industry" :rules="[{ required: true, message: '请输入行业' }]">
            <el-input v-model="currentItem.industry" />
          </el-form-item>
          <el-form-item label="规模" prop="size" :rules="[{ required: true, message: '请输入公司规模' }]">
            <el-input v-model="currentItem.size" />
          </el-form-item>
          <el-form-item label="地址" prop="address" :rules="[{ required: true, message: '请输入地址' }]">
            <el-input v-model="currentItem.address" />
          </el-form-item>
          <el-form-item label="网站" prop="website" :rules="[{ required: true, message: '请输入网站' }]">
            <el-input v-model="currentItem.website" />
          </el-form-item>
          <el-form-item label="联系电话" prop="phone" :rules="[{ required: true, message: '请输入联系电话' }]">
            <el-input v-model="currentItem.phone" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeModal">取消</el-button>
            <el-button type="primary" @click="saveItem">保存</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import adminApi from '@/api/admin';
import { ElMessage, ElMessageBox, ElCard, ElIcon, ElInput, ElButton, ElTable, ElTableColumn, ElPagination, ElDialog, ElForm, ElFormItem } from 'element-plus';
import { OfficeBuilding, Search, Plus } from '@element-plus/icons-vue';

const companies = ref([]);
const loading = ref(true);
const searchQuery = ref('');
const total = ref(0);
const pagination = reactive({
  page: 1,
  pageSize: 10,
});
const isModalOpen = ref(false);
const currentItem = ref({});
const itemForm = ref(null);
let searchTimeout = null;

const fetchCompanies = async () => {
  loading.value = true;
  try {
    const params = { 
      search: searchQuery.value,
      page: pagination.page,
      page_size: pagination.pageSize,
    };
    const response = await adminApi.getCompanies(params);
    companies.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("获取公司列表失败:", error);
    ElMessage.error('获取公司列表失败');
  } finally {
    loading.value = false;
  }
};

const debouncedFetchCompanies = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    pagination.page = 1; // Reset on search
    fetchCompanies();
  }, 300);
};

const openModal = (item = {}) => {
  if (item && item.id) {
    currentItem.value = { ...item };
  } else {
    currentItem.value = {
      name: '',
      industry: '',
      size: '',
      address: '',
      website: '',
      phone: ''
    };
  }
  isModalOpen.value = true;
};

const closeModal = () => {
  isModalOpen.value = false;
  itemForm.value?.resetFields();
};

const saveItem = async () => {
  if (!itemForm.value) return;
  await itemForm.value.validate(async (valid) => {
    if (valid) {
      try {
        if (currentItem.value.id) {
          await adminApi.updateCompany(currentItem.value.id, currentItem.value);
        } else {
          await adminApi.createCompany(currentItem.value);
        }
        closeModal();
        fetchCompanies();
        ElMessage.success('公司信息保存成功！');
      } catch (error) {
        console.error("保存公司失败:", error);
        ElMessage.error('保存公司失败，请稍后重试');
      }
    }
  });
};

const confirmDelete = (item) => {
  ElMessageBox.confirm(
    `确定要删除公司【${item.name}】吗？删除后，该公司下的所有用户和部门信息都将丢失，此操作不可恢复。`,
    '严重警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error',
      center: true,
    }
  ).then(async () => {
    try {
      await adminApi.deleteCompany(item.id);
      ElMessage.success('公司删除成功');
      fetchCompanies();
    } catch (error) {
      ElMessage.error('删除失败，请稍后重试');
      console.error("删除公司失败:", error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const handleSizeChange = (val) => {
  pagination.pageSize = val;
  fetchCompanies();
};

const handleCurrentChange = (val) => {
  pagination.page = val;
  fetchCompanies();
};

onMounted(fetchCompanies);
</script>

<style scoped>
@import './shared-styles.css';

.management-container {
  padding: 20px;
}
</style> 
 
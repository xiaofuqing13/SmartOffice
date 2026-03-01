<template>
  <div class="management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Tickets /></el-icon>
            <span>部门管理</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索部门..."
              clearable
              @clear="fetchDepartments"
              @input="debouncedFetchDepartments"
              class="search-input"
            >
              <template #append>
                <el-button :icon="Search" />
              </template>
            </el-input>
            <el-button type="primary" :icon="Plus" @click="openModal()">添加部门</el-button>
          </div>
        </div>
      </template>
      <div class="table-container">
        <el-table :data="departments" v-loading="loading" style="width: 100%">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="name" label="部门名称" sortable />
          <el-table-column prop="company_name" label="所属公司" sortable />
          <el-table-column prop="manager_name" label="部门主管" sortable>
             <template #default="scope">
                {{ scope.row.manager_name || '无' }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" />
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
      <el-dialog v-model="isModalOpen" :title="currentItem.id ? '编辑部门' : '添加部门'" width="500px">
        <el-form :model="currentItem" ref="itemForm" label-width="80px">
          <el-form-item label="部门名称" prop="name" :rules="[{ required: true, message: '请输入部门名称' }]">
            <el-input v-model="currentItem.name" />
          </el-form-item>
          <el-form-item label="所属公司" prop="company" :rules="[{ required: true, message: '请选择公司' }]">
             <el-select v-model="currentItem.company" placeholder="请选择" @change="onCompanyChange">
              <el-option v-for="company in companies" :key="company.id" :label="company.name" :value="company.id" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="currentItem.company" label="部门主管" prop="manager">
             <el-select v-model="currentItem.manager" placeholder="请选择" :disabled="!currentItem.company" clearable>
               <el-option label="-- 不指定 --" :value="null" />
              <el-option 
                v-for="user in companyUsers" 
                :key="user.id" 
                :label="user.name || user.username" 
                :value="user.id"
               />
             </el-select>
          </el-form-item>
          <el-form-item label="描述" prop="description">
            <el-input v-model="currentItem.description" type="textarea" />
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
import { ElMessage, ElMessageBox, ElCard, ElIcon, ElInput, ElButton, ElTable, ElTableColumn, ElPagination, ElDialog, ElForm, ElFormItem, ElSelect, ElOption } from 'element-plus';
import { Tickets, Search, Plus } from '@element-plus/icons-vue';

const departments = ref([]);
const companies = ref([]);
const companyUsers = ref([]);
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

const fetchDepartments = async () => {
  loading.value = true;
  try {
    const params = { 
      search: searchQuery.value,
      page: pagination.page,
      page_size: pagination.pageSize,
    };
    const response = await adminApi.getDepartments(params);
    departments.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("获取部门列表失败:", error);
    ElMessage.error('获取部门列表失败');
  } finally {
    loading.value = false;
  }
};

const debouncedFetchDepartments = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    pagination.page = 1;
    fetchDepartments();
  }, 300);
};
    
const fetchCompaniesForSelect = async () => {
  try {
    const response = await adminApi.getCompanies({ all: 'true' });
    companies.value = response.data;
  } catch (error) {
    console.error("获取公司列表失败:", error);
  }
};

const fetchUsersForCompany = async (companyId) => {
  if (!companyId) {
    companyUsers.value = [];
    return;
  }
  try {
    const response = await adminApi.getUsers({ all: 'true', company_id: companyId });
    companyUsers.value = response.data;
  } catch (error) {
    console.error(`获取公司 ${companyId} 的用户列表失败:`, error);
    companyUsers.value = [];
  }
};
    
const onCompanyChange = async (companyId) => {
  currentItem.value.manager = null;
  await fetchUsersForCompany(companyId);
};

const openModal = async (item = {}) => {
  await fetchCompaniesForSelect();
  companyUsers.value = []; // Reset user list initially

  if (item && item.id) {
    currentItem.value = { ...item };
    if (item.company) {
      await fetchUsersForCompany(item.company);

      const managerId = currentItem.value.manager;
      // If manager is from a different company, reset it
      if (managerId && !companyUsers.value.some(u => u.id === managerId)) {
        currentItem.value.manager = null;
      }
    }
  } else {
    currentItem.value = {
      name: '',
      description: '',
      company: null,
      manager: null
    };
  }
  isModalOpen.value = true;
};

const closeModal = () => {
  isModalOpen.value = false;
  itemForm.value?.resetFields();
  companyUsers.value = [];
};

const saveItem = async () => {
  if (!itemForm.value) return;
  await itemForm.value.validate(async (valid) => {
    if (valid) {
      try {
        const payload = { ...currentItem.value };
        // Ensure manager is null, not empty string, if not selected
        if (payload.manager === '') {
            payload.manager = null;
        }

        if (payload.id) {
          await adminApi.updateDepartment(payload.id, payload);
        } else {
          await adminApi.createDepartment(payload);
        }
        closeModal();
        fetchDepartments();
        ElMessage.success('部门信息保存成功！');
      } catch (error) {
        console.error("保存部门失败:", error);
        ElMessage.error('保存部门失败，请稍后重试');
      }
    }
  });
};

const confirmDelete = (item) => {
  ElMessageBox.confirm(
    `确定要删除部门【${item.name}】吗？这会将部门内的所有员工的部门重置为空。`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await adminApi.deleteDepartment(item.id);
      ElMessage.success('部门删除成功');
      fetchDepartments();
    } catch (error) {
      ElMessage.error('删除失败，请稍后重试');
      console.error("删除部门失败:", error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const handleSizeChange = (val) => {
  pagination.pageSize = val;
  fetchDepartments();
};

const handleCurrentChange = (val) => {
  pagination.page = val;
  fetchDepartments();
};

onMounted(fetchDepartments);
</script>

<style scoped>
@import './shared-styles.css';

.management-container {
  padding: 20px;
}
</style> 
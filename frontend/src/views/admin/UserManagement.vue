<template>
  <div class="management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><User /></el-icon>
            <span>用户管理</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索用户..."
              clearable
              @clear="fetchUsers"
              @input="debouncedFetchUsers"
              class="search-input"
            >
              <template #append>
                <el-button :icon="Search" />
              </template>
            </el-input>
            <el-button type="primary" :icon="Plus" @click="openUserModal()">添加用户</el-button>
          </div>
        </div>
      </template>
      <div class="table-container">
        <el-table :data="users" v-loading="loading" style="width: 100%">
          <el-table-column type="index" :index="index => (pagination.page - 1) * pagination.pageSize + index + 1" label="序号" width="80" />
          <el-table-column prop="name" label="用户名" sortable>
            <template #default="scope">{{ scope.row.name || scope.row.username }}</template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" sortable />
          <el-table-column prop="company_name" label="公司" sortable>
            <template #default="scope">{{ scope.row.company_name || '未分配' }}</template>
          </el-table-column>
          <el-table-column prop="department_name" label="部门" sortable>
            <template #default="scope">{{ scope.row.department_name || '未分配' }}</template>
          </el-table-column>
          <el-table-column prop="position" label="职位">
            <template #default="scope">{{ scope.row.position || '未指定' }}</template>
          </el-table-column>
          <el-table-column label="角色" width="120">
            <template #default="scope">
              <el-tag v-if="scope.row.is_staff" type="danger" size="small">管理员</el-tag>
              <el-tag v-else-if="scope.row.is_department_manager" type="primary" size="small">部门主管</el-tag>
              <el-tag v-else type="success" size="small">员工</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button text type="primary" size="small" @click="openUserModal(scope.row)">编辑</el-button>
              <el-button text type="danger" size="small" @click="confirmDeleteUser(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

       <!-- 分页 -->
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

      <!-- 添加/编辑用户模态框 -->
      <el-dialog v-model="isModalOpen" :title="currentUser.id ? '编辑用户' : '添加用户'" width="500px">
        <el-form :model="currentUser" ref="userForm" label-width="80px">
          <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名' }]">
            <el-input v-model="currentUser.username" />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="currentUser.name" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email" :rules="[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '请输入有效的邮箱地址' }]">
            <el-input v-model="currentUser.email" />
          </el-form-item>
          <el-form-item label="密码" prop="password" :rules="currentUser.id ? [] : [{ required: true, message: '请输入密码' }]">
            <el-input v-model="currentUser.password" type="password" :placeholder="currentUser.id ? '留空则不修改' : ''" />
          </el-form-item>
          <el-form-item label="职位" prop="position">
            <el-input v-model="currentUser.position" />
          </el-form-item>
          <el-form-item label="所属公司" prop="company" :rules="[{ required: true, message: '请选择公司' }]">
            <el-select v-model="currentUser.company" placeholder="请选择" @change="onCompanyChange">
              <el-option v-for="company in companies" :key="company.id" :label="company.name" :value="company.id" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="currentUser.company" label="所属部门" prop="department">
            <el-select v-model="currentUser.department" placeholder="请选择">
              <el-option label="-- 未分配 --" :value="null" />
              <el-option v-for="dept in companyDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeUserModal">取消</el-button>
            <el-button type="primary" @click="saveUser">保存</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import adminApi from '@/api/admin';
import { ElMessage, ElMessageBox, ElCard, ElIcon, ElInput, ElButton, ElTable, ElTableColumn, ElTag, ElPagination, ElDialog, ElForm, ElFormItem, ElSelect, ElOption } from 'element-plus';
import { User, Search, Plus } from '@element-plus/icons-vue';

const users = ref([]);
const companies = ref([]);
const companyDepartments = ref([]);
const searchQuery = ref('');
const total = ref(0);
const pagination = reactive({
  page: 1,
  pageSize: 10,
});
const isModalOpen = ref(false);
const currentUser = ref({});
const userForm = ref(null); // Form reference
let searchTimeout = null;
const loading = ref(true);

const fetchUsers = async () => {
  loading.value = true;
  try {
    const params = { 
      search: searchQuery.value,
      page: pagination.page,
      page_size: pagination.pageSize,
    };
    const response = await adminApi.getUsers(params);
    users.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("获取用户列表失败:", error);
    ElMessage.error('获取用户列表失败');
  } finally {
    loading.value = false;
  }
};

const debouncedFetchUsers = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    pagination.page = 1; // Reset to first page on search
    fetchUsers();
  }, 300);
};

const fetchCompanies = async () => {
    try {
        const response = await adminApi.getCompanies({ all: 'true' });
        companies.value = response.data;
    } catch (error) {
        console.error("获取公司列表失败:", error);
    }
};

const fetchDepartmentsForCompany = async (companyId) => {
  if (!companyId) {
    companyDepartments.value = [];
    return;
  }
  try {
    const params = { all: 'true', company: companyId };
    const response = await adminApi.getDepartments(params);
    companyDepartments.value = response.data;
  } catch (error) {
    console.error(`获取公司 ${companyId} 的部门列表失败:`, error);
    companyDepartments.value = [];
  }
};

const onCompanyChange = async (companyId) => {
  currentUser.value.department = null;
  await fetchDepartmentsForCompany(companyId);
};
    
const openUserModal = async (user = {}) => {
  await fetchCompanies();
  if (user && user.id) {
    currentUser.value = { ...user };
    if (user.company) {
      await fetchDepartmentsForCompany(user.company);
    }
  } else {
    currentUser.value = {
      username: '',
      name: '',
      email: '',
      password: '',
      position: '',
      company: null,
      department: null
    };
  }
  isModalOpen.value = true;
};

const closeUserModal = () => {
  isModalOpen.value = false;
  userForm.value?.resetFields();
};

const saveUser = async () => {
  if (!userForm.value) return;
  await userForm.value.validate(async (valid) => {
    if (valid) {
      try {
        const userData = { ...currentUser.value };
        
        if (!userData.password) {
          delete userData.password;
        }

        if (userData.department === null) {
          delete userData.department;
        }

        if (userData.id) {
          await adminApi.updateUser(userData.id, userData);
        } else {
          await adminApi.createUser(userData);
        }
        closeUserModal();
        fetchUsers();
        ElMessage.success('用户保存成功！');
      } catch (error) {
        console.error("保存用户失败:", error.response?.data || error.message);
        const errorMsg = error.response?.data ? JSON.stringify(error.response.data) : '请检查网络或联系技术支持';
        ElMessage.error(`保存用户失败: ${errorMsg}`);
      }
    }
  });
};

const confirmDeleteUser = (user) => {
  ElMessageBox.confirm(
    `确定要删除用户【${user.name || user.username}】吗？此操作无法撤销。`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await adminApi.deleteUser(user.id);
      ElMessage.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      ElMessage.error('删除用户失败');
      console.error("删除用户失败:", error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const handleSizeChange = (val) => {
  pagination.pageSize = val;
  fetchUsers();
};

const handleCurrentChange = (val) => {
  pagination.page = val;
  fetchUsers();
};

onMounted(() => {
    fetchUsers();
});
</script>

<style scoped>
@import './shared-styles.css';
</style> 
<template>
  <div class="company-container">
    <!-- 企业基本信息 -->
    <el-card class="info-card" shadow="hover">
      <template #header>
        <div class="card-header-flex">
          <div class="card-title">
            <el-icon class="header-icon"><OfficeBuilding /></el-icon>
            <span>企业基本信息</span>
          </div>
        </div>
      </template>
      
      <div class="company-info">
        <div class="company-logo-section">
          <div class="company-logo">
            <span v-if="!companyInfo.logo">{{ companyInfo.shortName?.charAt(0) || companyInfo.fullName?.charAt(0) || '企' }}</span>
            <img v-else :src="companyInfo.logo" alt="公司logo" />
          </div>
          <div class="company-name">
            <h2>{{ companyInfo.fullName }}</h2>
            <p v-if="companyInfo.shortName">{{ companyInfo.shortName }}</p>
          </div>
        </div>

        <el-divider />

        <div class="info-grid">
          <div class="info-item">
            <el-icon><OfficeBuilding /></el-icon>
            <span class="info-label">所属行业:</span>
            <span class="info-value">{{ companyInfo.industry || '未设置' }}</span>
          </div>
          <div class="info-item">
            <el-icon><User /></el-icon>
            <span class="info-label">公司规模:</span>
            <span class="info-value">{{ companyInfo.size || '未设置' }}</span>
          </div>
          <div class="info-item">
            <el-icon><Location /></el-icon>
            <span class="info-label">公司地址:</span>
            <span class="info-value">{{ companyInfo.address || '未设置' }}</span>
          </div>
          <div class="info-item">
            <el-icon><Link /></el-icon>
            <span class="info-label">官方网站:</span>
            <span class="info-value">
              <a v-if="companyInfo.website" :href="formatWebsiteUrl(companyInfo.website)" target="_blank">{{ companyInfo.website }}</a>
              <span v-else>未设置</span>
            </span>
          </div>
          <div class="info-item">
            <el-icon><Phone /></el-icon>
            <span class="info-label">联系电话:</span>
            <span class="info-value">{{ companyInfo.phone || '未设置' }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <div class="card-row">
      <!-- 组织架构 -->
      <el-card class="org-card" shadow="hover">
        <template #header>
          <div class="card-header-flex">
            <div class="card-title">
              <el-icon class="header-icon"><Connection /></el-icon>
              <span>组织架构</span>
            </div>
          </div>
        </template>
        
        <div class="org-chart">
          <el-tree
            :data="orgStructure"
            :props="defaultProps"
            node-key="id"
            default-expand-all
          >
            <template #default="{ node, data }">
              <div class="org-node">
                <el-icon v-if="node.level === 1"><OfficeBuilding /></el-icon>
                <el-icon v-else><Folder /></el-icon>
                <span>{{ node.label }}</span>
                <el-tag size="small" type="info" class="org-count">{{ data.count }}人</el-tag>
              </div>
            </template>
          </el-tree>
        </div>
      </el-card>
      
      <!-- 部门列表 -->
      <el-card class="department-card" shadow="hover">
        <template #header>
          <div class="card-header-flex">
            <div class="card-title">
              <el-icon class="header-icon"><Grid /></el-icon>
              <span>部门列表</span>
            </div>
          </div>
        </template>
        
        <el-empty v-if="!departments.length" description="暂无部门数据" />
        
        <el-table v-else :data="departments" style="width: 100%" border stripe>
          <el-table-column prop="name" label="部门名称">
            <template #default="scope">
              <div class="dept-name">
                <el-icon><Folder /></el-icon>
                <span>{{ scope.row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="manager_name" label="部门主管">
            <template #default="scope">
              <span>{{ scope.row.manager_name || '未设置' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="人数" width="80" align="center">
            <template #default="scope">
              <el-tag size="small" type="info">{{ scope.row.count }}人</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" width="180" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { Edit, Plus, Delete, OfficeBuilding, User, Location, Link, Phone, Connection, Grid, Folder } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { updateCompany, createDepartment, updateDepartment, deleteDepartment as apiDeleteDepartment, getCurrentUserCompany } from '@/api/company'

export default {
  name: 'Company',
  setup() {
    const router = useRouter();
    const store = useStore();
    const currentUser = computed(() => store.getters['user/currentUser']);
    const departmentFormRef = ref(null);
    const companyFormRef = ref(null);

    // 企业基本信息
    const companyInfo = reactive({
      id: null,
      fullName: '',
      shortName: '',
      industry: '',
      size: '',
      address: '',
      website: '',
      phone: '',
      logo: ''
    });
    
    // 编辑中的公司信息
    const editingCompanyInfo = reactive({
      id: null,
      fullName: '',
      shortName: '',
      industry: '',
      size: '',
      address: '',
      website: '',
      phone: ''
    });
    
    // 公司信息对话框
    const companyDialogVisible = ref(false);
    
    // 公司表单校验规则
    const companyRules = {
      fullName: [
        { required: true, message: '请输入公司全称', trigger: 'blur' },
        { min: 2, max: 100, message: '长度在2到100个字符之间', trigger: 'blur' }
      ],
      website: [
        { 
          pattern: /^(https?:\/\/)?(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/[a-zA-Z0-9-._~:/?#[\]@!$&'()*+,;=]*)?$/, 
          message: '请输入合法的URL，例如: http://example.com', 
          trigger: 'blur' 
        }
      ]
    };
    
    // 部门表单校验规则
    const departmentRules = {
      name: [
        { required: true, message: '请输入部门名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在2到50个字符之间', trigger: 'blur' }
      ]
    };
    
    // 组织架构
    const orgStructure = ref([]);
    
    const defaultProps = {
      children: 'children',
      label: 'label'
    }
    
    // 部门列表
    const departments = ref([]);
    
    // 部门选项
    const departmentOptions = ref([]);
    
    // 主管选项 - 实际项目中应该从用户列表API获取
    const managers = ref([
      { value: '张总', label: '张总' },
      { value: '李经理', label: '李经理' },
      { value: '王经理', label: '王经理' },
      { value: '赵经理', label: '赵经理' },
      { value: '钱经理', label: '钱经理' },
      { value: '孙经理', label: '孙经理' },
      { value: '周经理', label: '周经理' }
    ])
    
    // 部门对话框
    const departmentDialogVisible = ref(false)
    const isEdit = ref(false)
    const currentDepartment = reactive({
      id: null,
      name: '',
      manager: '',
      company: null,
      description: ''
    })
    
    // 获取公司数据
    const fetchCompanyData = async () => {
      try {
        // 检查用户是否已登录
        if (!currentUser.value || !currentUser.value.id) {
          ElMessage.warning('请先登录');
          router.push('/login');
          return;
        }

        // 使用当前登录用户所属公司API替代固定公司ID
        const response = await getCurrentUserCompany();
        
        if (response && response.success) {
          const data = response.data;
          
          // 更新公司信息
          const company = data.company;
          Object.assign(companyInfo, {
            id: company.id,
            fullName: company.name,
            shortName: company.short_name || '',
            industry: company.industry || '',
            size: company.size || '',
            address: company.address || '',
            website: company.website || '',
            phone: company.phone || ''
          });
          
          // 更新部门列表
          departments.value = data.departments.map(dept => ({
            id: dept.id,
            name: dept.name,
            manager_name: dept.manager_name || '',
            count: dept.count || 0,
            createTime: new Date(dept.created_at).toLocaleDateString('zh-CN')
          }));
          
          // 保存员工总数，用于计算无部门员工数量
          data.totalEmployeeCount = data.totalEmployeeCount || data.total_employee_count || 0;
          
          // 构建组织架构树
          buildOrgStructure(data.departments, data.totalEmployeeCount);
          
          // 构建部门选项
          buildDepartmentOptions(data.departments);
        } else {
          ElMessage.error('获取公司数据失败');
        }
      } catch (error) {
        console.error('获取公司数据失败:', error);
        ElMessage.error('获取公司数据失败，请刷新重试');
      }
    };
    
    // 构建组织架构树
    const buildOrgStructure = (departments, totalEmployeeCount) => {
      // 简化实现，实际项目中应考虑部门层级关系
      
      // 计算所有部门人数
      const departmentCount = departments.reduce((sum, dept) => sum + (dept.count || 0), 0);
      
      // 获取未分配部门的人数（如果API提供了总人数）
      const noDepCount = totalEmployeeCount ? (totalEmployeeCount - departmentCount) : 0;
      
      const deptChildren = departments.map(dept => ({
        id: dept.id,
        label: dept.name,
        count: dept.count || 0
      }));
      
      // 添加"其它"分类，显示没有部门的用户
      if (noDepCount > 0) {
        deptChildren.push({
          id: -1,
          label: '其它',
          count: noDepCount
        });
      }
      
      const rootDept = {
        id: 0,
        label: companyInfo.shortName || companyInfo.fullName,
        count: departmentCount + noDepCount,
        children: deptChildren
      };
      
      orgStructure.value = [rootDept];
    };
    
    // 构建部门选项
    const buildDepartmentOptions = (departments) => {
      departmentOptions.value = [{
        value: 0,
        label: companyInfo.shortName || companyInfo.fullName,
        children: departments.map(dept => ({
          value: dept.id,
          label: dept.name
        }))
      }];
    };
    
    // 编辑企业信息
    const editCompanyInfo = () => {
      Object.assign(editingCompanyInfo, {
        id: companyInfo.id,
        fullName: companyInfo.fullName,
        shortName: companyInfo.shortName,
        industry: companyInfo.industry,
        size: companyInfo.size,
        address: companyInfo.address,
        website: companyInfo.website,
        phone: companyInfo.phone
      });
      companyDialogVisible.value = true;
    };
    
    // 保存企业信息
    const saveCompanyInfo = async () => {
      try {
        await companyFormRef.value.validate();
        
        // 格式化网站URL，确保以http://或https://开头
        let websiteUrl = editingCompanyInfo.website.trim();
        if (websiteUrl && !websiteUrl.match(/^https?:\/\//)) {
          websiteUrl = 'http://' + websiteUrl;
        }
        
        const companyData = {
          name: editingCompanyInfo.fullName,
          short_name: editingCompanyInfo.shortName,
          industry: editingCompanyInfo.industry,
          size: editingCompanyInfo.size,
          address: editingCompanyInfo.address,
          website: websiteUrl, // 使用格式化后的URL
          phone: editingCompanyInfo.phone
        };
        
        await updateCompany(editingCompanyInfo.id, companyData);
        ElMessage.success('企业信息更新成功');
        companyDialogVisible.value = false;
        fetchCompanyData();
      } catch (error) {
        console.error('更新企业信息失败:', error);
        if (error?.response?.data) {
          // 显示后端返回的具体错误信息
          const errorData = error.response.data;
          const errorMessages = [];
          
          for (const field in errorData) {
            if (Array.isArray(errorData[field])) {
              errorMessages.push(`${field}: ${errorData[field].join(', ')}`);
            } else if (typeof errorData[field] === 'string') {
              errorMessages.push(`${field}: ${errorData[field]}`);
            }
          }
          
          if (errorMessages.length > 0) {
            ElMessage.error(errorMessages.join('\n'));
          } else {
            ElMessage.error('更新企业信息失败，请检查输入内容');
          }
        } else if (error?.message) {
          ElMessage.error(error.message);
        } else {
          ElMessage.error('更新企业信息失败，请稍后重试');
        }
      }
    };
    
    // 添加部门
    const addDepartment = () => {
      isEdit.value = false;
      Object.assign(currentDepartment, {
        id: null,
        name: '',
        manager: '',
        company: companyInfo.id,
        description: ''
      });
      departmentDialogVisible.value = true;
    };
    
    // 编辑部门
    const editDepartment = (row) => {
      isEdit.value = true;
      Object.assign(currentDepartment, {
        id: row.id,
        name: row.name,
        manager: row.manager,
        company: companyInfo.id,
        description: '' // 实际应从API获取
      });
      departmentDialogVisible.value = true;
    };
    
    // 删除部门
    const deleteDepartment = (row) => {
      ElMessageBox.confirm(
        `确定要删除部门"${row.name}"吗？`,
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          await apiDeleteDepartment(row.id);
          ElMessage.success(`删除部门: ${row.name} 成功`);
          fetchCompanyData();
        } catch (error) {
          console.error('删除部门失败:', error);
          ElMessage.error('删除部门失败，请稍后重试');
        }
      }).catch(() => {});
    };
    
    // 保存部门
    const saveDepartment = async () => {
      try {
        await departmentFormRef.value.validate();
        
        const departmentData = {
          name: currentDepartment.name,
          company: currentDepartment.company,
          manager: currentDepartment.manager,
          description: currentDepartment.description
        };
        
        if (isEdit.value) {
          await updateDepartment(currentDepartment.id, departmentData);
          ElMessage.success(`更新部门: ${currentDepartment.name} 成功`);
        } else {
          await createDepartment(departmentData);
          ElMessage.success(`新增部门: ${currentDepartment.name} 成功`);
        }
        
        departmentDialogVisible.value = false;
        fetchCompanyData();
      } catch (error) {
        console.error('保存部门失败:', error);
        if (error?.message) {
          ElMessage.error(error.message);
        } else {
          ElMessage.error('保存部门失败，请稍后重试');
        }
      }
    };
    
    // 格式化网站URL
    const formatWebsiteUrl = (url) => {
      if (url && !url.match(/^https?:\/\//)) {
        return 'http://' + url;
      }
      return url;
    };
    
    onMounted(() => {
      fetchCompanyData();
    });
    
    return {
      companyInfo,
      editingCompanyInfo,
      companyDialogVisible,
      companyFormRef,
      companyRules,
      orgStructure,
      defaultProps,
      departments,
      departmentOptions,
      managers,
      departmentDialogVisible,
      isEdit,
      currentDepartment,
      departmentFormRef,
      departmentRules,
      editCompanyInfo,
      saveCompanyInfo,
      addDepartment,
      editDepartment,
      deleteDepartment,
      saveDepartment,
      formatWebsiteUrl,
      // 图标
      Edit,
      Plus,
      Delete,
      OfficeBuilding,
      User,
      Location,
      Link,
      Phone,
      Connection,
      Grid,
      Folder
    }
  }
}
</script>

<style lang="scss" scoped>
.company-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.info-card {
  margin-bottom: 20px;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-2px);
  }
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
  
  .header-icon {
    margin-right: 8px;
    font-size: 18px;
  }
}

.company-info {
  padding: 10px 0;
}

.company-logo-section {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.company-logo {
  width: 80px;
  height: 80px;
  background-color: var(--el-color-primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 36px;
  font-weight: bold;
  margin-right: 20px;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 8px;
  }
}

.company-name {
  h2 {
    margin: 0 0 5px 0;
    font-size: 24px;
    font-weight: 500;
  }
  
  p {
    margin: 0;
    color: var(--el-text-color-secondary);
    font-size: 16px;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  
  .el-icon {
    margin-right: 10px;
    color: var(--el-color-primary);
    font-size: 18px;
  }
  
  .info-label {
    font-weight: 500;
    color: var(--el-text-color-secondary);
    margin-right: 10px;
    white-space: nowrap;
  }
  
  .info-value {
    color: var(--el-text-color-primary);
    word-break: break-word;
  }
  
  a {
    color: var(--el-color-primary);
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.card-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.org-card,
.department-card {
  height: 100%;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-2px);
  }
}

.org-chart {
  min-height: 300px;
  padding: 10px 0;
}

.org-node {
  display: flex;
  align-items: center;
  
  .el-icon {
    margin-right: 8px;
    color: var(--el-color-primary);
  }
}

.org-count {
  margin-left: 8px;
}

.dept-name {
  display: flex;
  align-items: center;
  
  .el-icon {
    margin-right: 8px;
    color: var(--el-color-primary);
  }
}

/* 响应式布局 */
@media screen and (max-width: 992px) {
  .card-row {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}

/* 深色模式适配 */
:deep(.el-tree) {
  background-color: transparent;
  color: var(--el-text-color-primary);
}

:deep(.el-tree-node__content:hover) {
  background-color: var(--el-fill-color-light);
}

:deep(.el-tree-node__content) {
  background-color: transparent;
}

:deep(.el-table) {
  background-color: var(--el-bg-color) !important;
  
  th.el-table__cell,
  td.el-table__cell {
    background-color: var(--el-bg-color) !important;
    border-bottom-color: var(--el-border-color-lighter) !important;
  }
  
  .el-table__row:hover > td.el-table__cell {
    background-color: var(--el-fill-color-light) !important;
  }
}

:deep(.el-dialog__body) {
  padding-top: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-tag) {
  background: var(--bg-color-tertiary) !important;
  color: var(--text-color) !important;
  border-color: var(--border-color) !important;
}
:deep(.el-tag.el-tag--info) {
  background: var(--bg-color-tertiary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-color) !important;
}
:deep(.el-tag.el-tag--success) {
  background: var(--success-color) !important;
  border-color: var(--success-color) !important;
  color: #fff !important;
}
:deep(.el-tag.el-tag--primary) {
  background: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: #fff !important;
}
:deep(.el-tag.el-tag--warning) {
  background: var(--warning-color) !important;
  border-color: var(--warning-color) !important;
  color: #fff !important;
}
:deep(.el-tag.el-tag--danger) {
  background: var(--danger-color) !important;
  border-color: var(--danger-color) !important;
  color: #fff !important;
}
:deep(.el-tree-node__content:hover) {
  background-color: var(--hover-color) !important;
}
:deep(.el-table__row:hover > td.el-table__cell) {
  background-color: var(--hover-color) !important;
}
</style> 
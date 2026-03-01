<template>
  <div class="contract-container">
    <div class="row">
      <!-- 合同列表 -->
      <div class="col-lg-12">
        <el-card class="contract-list-card" v-loading="isLoading">
          <template #header>
            <div class="card-header-flex">
              <span>合同列表</span>
              <div class="d-flex align-items-center ms-auto me-3"> 
            <el-input 
              v-model="searchQuery" 
                  placeholder="搜索标题或编号..." 
              clearable
              :prefix-icon="Search"
                  class="me-2"
                  style="width: 200px;"
                  @clear="handleFilterChange"
            ></el-input>
            <el-select 
              v-model="sortBy" 
                  placeholder="默认排序" 
                  class="me-2"
                  style="width: 150px;"
                  @change="handleFilterChange"
                >
                  <el-option label="默认排序" value="default"></el-option>
                  <el-option label="合同标题" value="title"></el-option>
                  <el-option label="创建时间" value="created_at"></el-option>
                  <el-option label="合同金额" value="amount"></el-option>
                </el-select>
                <el-select 
                  v-model="sortOrder" 
                  style="width: 100px;"
                  @change="handleFilterChange"
                >
                  <el-option label="升序" value="asc"></el-option>
                  <el-option label="降序" value="desc"></el-option>
            </el-select>
          </div>
              <el-button type="primary" size="small" @click="openContractDialog">
                <el-icon class="mr-1"><Plus /></el-icon> 新建合同
              </el-button>
            </div>
          </template>
          
          <div class="contract-list">
            <div 
              v-for="(contract) in filteredContracts" 
              :key="contract.id"
              class="contract-item"
              :class="{'active': selectedContract && selectedContract.id === contract.id}"
            >
              <div class="contract-main-info" @click="viewContractDetail(contract)">
                <div class="contract-title">
                  {{ contract.title }}
                </div>
                <div class="contract-info">
                  <span>合同编号: {{ contract.number }}</span>
                  <span>创建时间: {{ contract.createdAt }}</span>
                </div>
                <div class="contract-info mt-1">
                  <span>{{ contract.company }}</span>
                  <span>金额: {{ contract.displayAmount }}</span>
                </div>
              </div>
              <div class="contract-actions">
                <el-dropdown trigger="click" @click.stop>
                  <el-button
                    :icon="MoreFilled"
                    class="more-button"
                    text
                    circle
                  />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :icon="Edit" @click="handleEdit(contract)">编辑</el-dropdown-item>
                      <el-dropdown-item :icon="Share" @click="handleShare(contract)">分享</el-dropdown-item>
                      <el-dropdown-item :icon="Delete" divided class="text-danger" @click="handleDelete(contract)">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            
            <el-empty 
              v-if="filteredContracts.length === 0" 
              description="没有找到匹配的合同"
            ></el-empty>
          </div>
          
          <!-- 添加分页组件 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="10"
              layout="total, prev, pager, next, jumper"
              :total="totalItems"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </div>
      </div>
      
    <!-- 创建合同模态框 -->
    <el-dialog
      v-model="showNewContractDialog"
      title="新建合同"
      width="60%"
      center
      class="new-contract-dialog"
    >
      <!-- 创建方式 -->
      <div class="mb-4">
        <el-radio-group v-model="creationMode" size="large">
          <el-radio-button label="manual">手动创建</el-radio-button>
          <el-radio-button label="template">使用模板</el-radio-button>
          <el-radio-button label="ai">AI 生成</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 手动创建 -->
      <el-form v-if="creationMode === 'manual'" :model="newContract" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同名称" required>
              <el-input v-model="newContract.title"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同类型" required>
              <el-input v-model="newContract.type" placeholder="请输入合同类型"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="签约对方" required>
              <el-input v-model="newContract.company"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同金额">
              <el-input v-model="newContract.amount" placeholder="请输入金额" >
                 <template #prepend>¥</template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="签约日期">
              <el-date-picker v-model="newContract.signDate" type="date" placeholder="选择日期" style="width: 100%"></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="生效日期">
              <el-date-picker v-model="newContract.startDate" type="date" placeholder="选择日期" style="width: 100%"></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="到期日期">
              <el-date-picker v-model="newContract.expireDate" type="date" placeholder="选择日期" style="width: 100%"></el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="newContract.remark" type="textarea" :rows="3"></el-input>
        </el-form-item>
      </el-form>

      <!-- 模板选择 -->
      <div v-if="creationMode === 'template'">
        <el-row :gutter="20" class="mb-4">
          <el-col :span="8">
            <el-select v-model="templateForm.contractType" placeholder="合同类型" filterable style="width: 100%">
              <el-option v-for="item in contractTypes" :key="item.value" :label="item.label" :value="item.value"></el-option>
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-select v-model="templateForm.industry" placeholder="行业领域" filterable style="width: 100%">
              <el-option v-for="item in industries" :key="item.value" :label="item.label" :value="item.value"></el-option>
            </el-select>
          </el-col>
          <el-col :span="8">
             <el-select v-model="templateForm.scene" placeholder="交易场景" filterable style="width: 100%">
               <el-option v-for="item in scenes" :key="item.value" :label="item.label" :value="item.value"></el-option>
            </el-select>
          </el-col>
        </el-row>
              
        <div class="mb-4">
          <p class="form-label small text-muted">推荐模板</p>
          <div class="template-list" v-loading="isLoadingTemplates">
            <div 
              v-for="(template, idx) in availableTemplates" 
              :key="idx"
              class="template-item"
              :class="{'active': selectedTemplate === idx}"
              @click="handleTemplateSelect(template, idx)"
            >
              <div class="template-name">{{ template.name }}</div>
              <div class="template-info">
                <span class="template-type">{{ template.contract_type }}</span>
                <span class="template-industry" v-if="template.industry">{{ template.industry }}</span>
              </div>
              <div class="template-desc" v-if="template.description">{{ template.description }}</div>
            </div>
            
            <el-empty 
              v-if="!isLoadingTemplates && availableTemplates.length === 0 && (templateForm.contractType || templateForm.industry || templateForm.scene)"
              description="没有找到匹配的模板"
              :image-size="80"
            ></el-empty>
          </div>
        </div>
                  
        <el-form :model="templateForm" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="合同名称" required>
                <el-input v-model="templateForm.title" placeholder="请选择模板后自动生成"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="签约对方" required>
                <el-input v-model="templateForm.company" placeholder="请输入签约对方名称"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="合同金额">
                <el-input v-model="templateForm.amount" placeholder="请输入金额">
                  <template #prepend>¥</template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="备注">
            <el-input v-model="templateForm.remark" type="textarea" :rows="2"></el-input>
          </el-form-item>
        </el-form>
      </div>

      <!-- AI生成 -->
      <el-form v-if="creationMode === 'ai'" :model="aiForm" label-position="top">
        <el-form-item label="请详细描述您的合同需求" required>
          <el-input 
            v-model="aiForm.coreElements" 
            type="textarea" 
            :rows="5"
            placeholder="例如：请帮我起草一份软件开发服务合同。甲方是'未来科技有限公司'，乙方是'创新软件工作室'。合同需要明确开发周期为3个月，总费用为50万元人民币，分三次支付。第一次支付30%作为启动资金，第二次在完成中期里程碑后支付40%，剩余30%在项目验收通过后支付。还需要包括双方的权利义务、保密条款和违约责任等。"
          ></el-input>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showNewContractDialog = false">取消</el-button>
          <el-button type="primary" @click="submitContract">
            {{ getSubmitButtonText() }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑合同模态框 -->
    <el-dialog v-model="showEditDialog" title="编辑合同" width="70%">
      <el-form :model="editForm" label-width="100px" v-if="editForm">
        <div class="row">
          <div class="col-md-6">
            <el-form-item label="合同名称" required>
              <el-input v-model="editForm.title"></el-input>
            </el-form-item>
            <el-form-item label="合同类型" required>
              <el-input v-model="editForm.type" placeholder="请输入合同类型"></el-input>
            </el-form-item>
            <el-form-item label="签约对方" required>
              <el-input v-model="editForm.company"></el-input>
            </el-form-item>
            <el-form-item label="合同金额" required>
              <el-input v-model="editForm.amount"></el-input>
            </el-form-item>
          </div>
          <div class="col-md-6">
            <el-form-item label="签约日期">
              <el-date-picker 
                v-model="editForm.sign_date" 
                type="date" 
                placeholder="选择日期"
                style="width: 100%">
              </el-date-picker>
            </el-form-item>
            <el-form-item label="生效日期">
              <el-date-picker 
                v-model="editForm.start_date" 
                type="date" 
                placeholder="选择日期"
                style="width: 100%">
              </el-date-picker>
            </el-form-item>
            <el-form-item label="到期日期">
              <el-date-picker 
                v-model="editForm.expire_date" 
                type="date" 
                placeholder="选择日期"
                style="width: 100%">
              </el-date-picker>
            </el-form-item>
          </div>
        </div>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="3"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpdate">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- 分享合同模态框 -->
    <el-dialog v-model="showShareDialog" title="分享合同" width="400px">
      <el-form>
        <el-form-item label="分享给">
          <el-select
            v-model="shareTargetUsers"
            multiple
            filterable
            placeholder="请选择用户"
            style="width: 100%"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showShareDialog = false">取消</el-button>
        <el-button type="primary" @click="submitShare">分享</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { 
  Plus, Search, InfoFilled, MoreFilled, Edit, Share, Delete
} from '@element-plus/icons-vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { 
  getContractList, createContract as createContractAPI,
  getRecommendedTemplates, createContractFromTemplate,
  updateContract, deleteContract, getCompanyUsers
} from '@/api/contract'
import { findOrCreateChatWithUsers, sendFileMessage } from '@/api/chat'
import store from '@/store'
import request from '@/utils/request'

// 格式化日期为YYYY-MM-DD
function formatDate(date) {
  if (!date) return null;
  if (typeof date === 'string') return date;
  return date.toISOString().split('T')[0];
}

export default {
  name: 'Contract',
  setup() {
    const router = useRouter()
    const searchQuery = ref('')
    const sortBy = ref('default')
    const sortOrder = ref('desc')
    const selectedContract = ref(null)
    const showNewContractDialog = ref(false)
    const creationMode = ref('template')
    const selectedTemplate = ref(null)
    const isLoading = ref(false)
    const showEditDialog = ref(false)
    const showShareDialog = ref(false)
    const editForm = ref(null)
    const shareTargetUsers = ref([])
    const availableUsers = ref([])
    let searchTimeout = null;
    
    // 分页相关状态
    const currentPage = ref(1)
    const totalItems = ref(0)
    
    // 新合同表单
    const newContract = reactive({
      title: '',
      type: '',
      company: '',
      amount: '',
        signDate: '',
      startDate: '',
      expireDate: '',
      remark: ''
    })

    // 模板表单
    const templateForm = reactive({
      contractType: '',
      industry: '',
      scene: '',
      title: '',
      company: '',
      amount: '',
      remark: ''
    })

    // AI表单
    const aiForm = reactive({
      coreElements: ''
    })

    // 可用模板列表
    const availableTemplates = ref([])
    const isLoadingTemplates = ref(false)
    const allActiveTemplates = ref([])
    
    // 合同列表 - 从API获取
    const contracts = ref([])
    
    // 下拉框选项
    const contractTypes = ref([])
    const industries = ref([])
    const scenes = ref([])
    
    const filterAvailableTemplates = () => {
      if (allActiveTemplates.value.length === 0) {
        availableTemplates.value = [];
        return;
      }

      let templates = allActiveTemplates.value;
      const hasFilter = templateForm.contractType || templateForm.industry || templateForm.scene;

      if (hasFilter) {
        if (templateForm.contractType) {
          templates = templates.filter(t => t.contract_type === templateForm.contractType);
        }
        if (templateForm.industry) {
          templates = templates.filter(t => t.industry === templateForm.industry);
        }
        if (templateForm.scene) {
          templates = templates.filter(t => t.scene === templateForm.scene);
        }
        availableTemplates.value = templates;
      } else {
        availableTemplates.value = allActiveTemplates.value;
      }
    };

    watch(
      () => [templateForm.contractType, templateForm.industry, templateForm.scene],
      filterAvailableTemplates,
      { deep: true }
    );

    const initializeTemplateData = async () => {
      if (allActiveTemplates.value.length > 0) {
        filterAvailableTemplates();
        return;
      }
      
      isLoadingTemplates.value = true;
      try {
        const response = await getRecommendedTemplates({});
        const allTemplates = response.data.results || response.data || [];
        
        const activeTemplates = allTemplates.filter(t => t.is_active);
        allActiveTemplates.value = activeTemplates;

        const typeSet = new Set(activeTemplates.map(t => t.contract_type).filter(Boolean));
        const industrySet = new Set(activeTemplates.map(t => t.industry).filter(Boolean));
        const sceneSet = new Set(activeTemplates.map(t => t.scene).filter(Boolean));

        contractTypes.value = Array.from(typeSet).map(item => ({ label: item, value: item }));
        industries.value = Array.from(industrySet).map(item => ({ label: item, value: item }));
        scenes.value = Array.from(sceneSet).map(item => ({ label: item, value: item }));
        
        filterAvailableTemplates();
      } catch (error) {
        console.error('获取合同模板失败:', error);
        ElMessage.error("获取合同模板列表失败");
        allActiveTemplates.value = [];
        availableTemplates.value = [];
      } finally {
        isLoadingTemplates.value = false;
      }
    };

    const loadFilterOptions = async () => {
      try {
        // Mock-API-Aufrufe, ersetzen durch echte API-Endpunkte
        const [typesRes, industriesRes, scenesRes] = await Promise.all([
          request({ url: '/api/contract/types/', method: 'get' }),
          request({ url: '/api/contract/industries/', method: 'get' }),
          request({ url: '/api/contract/scenes/', method: 'get' })
        ]);
        contractTypes.value = typesRes.data.map(item => ({ label: item.name, value: item.name }));
        industries.value = industriesRes.data.map(item => ({ label: item.name, value: item.name }));
        scenes.value = scenesRes.data.map(item => ({ label: item.name, value: item.name }));
      } catch (error) {
        console.error("加载筛选选项失败:", error);
        ElMessage.error("加载筛选选项失败，将使用默认值");
        // Fallback-Werte
        contractTypes.value = [
          { label: '采购合同', value: '采购合同' },
          { label: '销售合同', value: '销售合同' },
        ];
        industries.value = [{ label: '信息技术', value: '信息技术' }];
        scenes.value = [{ label: '国内贸易', value: '国内贸易' }];
      }
    };
    
    // 加载合同列表数据
    const loadContracts = async () => {
      try {
        isLoading.value = true
        
        const params = {
          search: searchQuery.value,
          page: currentPage.value,
          page_size: 10
        };

        if (sortBy.value !== 'default') {
          params.ordering = (sortOrder.value === 'desc' ? '-' : '') + sortBy.value;
        }

        const response = await getContractList(params);
        
        // 格式化后端返回的数据
        const formattedContracts = response.results.map(contract => ({
          ...contract,
          createdAt: contract.created_at ? new Date(contract.created_at).toLocaleString('zh-CN') : '',
          displayAmount: `￥${Number(contract.amount || 0).toFixed(2)}`
        }))
        
        contracts.value = formattedContracts
        totalItems.value = response.count
      } catch (error) {
        console.error('加载合同列表失败:', error)
        ElMessage.error('加载合同列表失败，请稍后重试')
      } finally {
        isLoading.value = false
      }
    }
    
    // 根据筛选条件过滤合同
    const filteredContracts = computed(() => {
      // 因为我们现在在API层面做了筛选，这里只是展示返回的数据
      return contracts.value
    })
    
    // 创建合同
    const openContractDialog = () => {
      resetForms()
      showNewContractDialog.value = true
      initializeTemplateData()
    }
    
    // 重置表单
    const resetForms = () => {
      Object.keys(newContract).forEach(key => {
        newContract[key] = ''
      })
      Object.keys(templateForm).forEach(key => {
        templateForm[key] = ''
      })
      aiForm.coreElements = ''
      creationMode.value = 'template'
      selectedTemplate.value = null
    }
    
    // 获取提交按钮文本
    const getSubmitButtonText = () => {
      switch (creationMode.value) {
        case 'template':
          return '使用模板创建'
        case 'ai':
          return 'AI 生成合同'
        default:
          return '創建合同'
      }
    }
    
    // 查看合同详情
    const viewContractDetail = (contract) => {
      if (contract && contract.id) {
        selectedContract.value = contract;
        router.push({ 
          name: 'ContractDetail', 
          params: { id: contract.id } 
        });
      }
    };
    
    // 筛选和排序变化时重新加载数据
    const handleFilterChange = () => {
      currentPage.value = 1 // 重置到第一页
      loadContracts()
    }
    
    // 在 script setup 部分添加处理函数
    const handleContractTypeChange = (value) => {
      // 如果用户选择了"其他"，清空当前值以允许输入
      if (value === '其他') {
        newContract.type = ''
      }
    }

    const handleTemplateSelect = (template, index) => {
      selectedTemplate.value = index;
      const today = new Date();
      const dateStr = `${today.getFullYear()}/${today.getMonth() + 1}/${today.getDate()}`;
      templateForm.title = `${template.name}(${dateStr})`;
    };
    
    // 处理页码变化
    const handleCurrentChange = (newPage) => {
      currentPage.value = newPage
      loadContracts()
    }
    
    const handleEdit = (contract) => {
      editForm.value = { ...contract }
      showEditDialog.value = true
    }
    
    const handleShare = async (contract) => {
      selectedContract.value = contract
      showShareDialog.value = true
      shareTargetUsers.value = []
      try {
        const companyId = store.getters.user?.company
        if (!companyId) {
          ElMessage.error('无法获取公司信息，请重新登录')
          return
        }
        const result = await getCompanyUsers(companyId)
        availableUsers.value = result.data.filter(user => user.id !== store.getters.user?.id)
      } catch (error) {
        ElMessage.error('获取用户列表失败')
        console.error('get user list error', error)
      }
    }
    
    const handleDelete = (contract) => {
      ElMessageBox.confirm(
        `确定要删除合同 "${contract.title}" 吗？此操作不可逆。`,
        '警告',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(async () => {
        try {
          await deleteContract(contract.id)
          ElMessage.success('合同已删除')
          await loadContracts()
        } catch (error) {
          ElMessage.error('删除合同失败')
          console.error(`delete contract ${contract.id} failed`, error)
        }
      }).catch(() => {
        // User canceled
      })
    }

    const submitUpdate = async () => {
      if (!editForm.value) return
      try {
        const { id, title, type, company, amount, sign_date, start_date, expire_date, remark } = editForm.value
        const updateData = {
            title,
            type,
            company,
            amount: Number(String(amount).replace(/[^\d.]/g, '')) || 0,
            sign_date: formatDate(sign_date),
            start_date: formatDate(start_date),
            expire_date: formatDate(expire_date),
            remark: remark || ''
        }
        await updateContract(id, updateData)
        ElMessage.success('合同更新成功')
        showEditDialog.value = false
        await loadContracts()
      } catch (error) {
        ElMessage.error('更新失败')
        console.error('update contract failed', error)
      }
    }

    const submitShare = async () => {
      if (shareTargetUsers.value.length === 0) {
        ElMessage.warning('请选择要分享的用户')
        return
      }

      const loading = ElLoading.service({
        lock: true,
        text: '正在分享...',
        background: 'rgba(0, 0, 0, 0.7)'
      })

      try {
        // 1. 获取或创建聊天
        loading.text = '正在准备聊天...'
        const chatResponse = await findOrCreateChatWithUsers(shareTargetUsers.value)
        console.log('获取聊天响应:', chatResponse);

        // 确保获取到数字类型的聊天ID
        let chatId;
        if (chatResponse && chatResponse.data) {
          if (chatResponse.data.chat_id !== undefined) {
            chatId = parseInt(chatResponse.data.chat_id, 10);
          } else if (chatResponse.data.id !== undefined) {
            chatId = parseInt(chatResponse.data.id, 10);
          }
        }

        if (isNaN(chatId) || !chatId) {
          console.error('获取聊天会话ID失败，API响应:', chatResponse)
          throw new Error('无法获取聊天会话')
        }

        console.log('已获取聊天ID:', chatId, '类型:', typeof chatId);

        // 2. 生成 Word 文档
        loading.text = '正在生成合同文件...'
        const contract = selectedContract.value
        let blob = null
        let filename = ''
        
        try {
          console.log('开始获取合同详情，ID:', contract.id)
          
          // 使用下载API直接获取Word文档，而不是手动构建
          const downloadUrl = `/api/contract/contracts/${contract.id}/download-docx/`
          console.log('使用下载API获取Word文档:', downloadUrl)
          
          // 获取认证令牌
          const token = localStorage.getItem('token')
          
          // 直接调用下载API
          const response = await request({
            url: downloadUrl,
            method: 'GET',
            responseType: 'blob',
            headers: {
              'Authorization': token ? `Bearer ${token}` : ''
            }
          })
          
          console.log('下载API响应:', response)
          
          // 从响应中获取文件内容
          if (response && response.data) {
            blob = new Blob([response.data], {
              type: response.headers['content-type'] || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            })
            
            // 获取文件名
            const docTitle = contract.title || '未命名合同'
            const contentDisposition = response.headers['content-disposition']
            if (contentDisposition && contentDisposition.includes('filename=')) {
              const match = contentDisposition.match(/filename="?([^"]+)"?/)
              if (match && match[1]) {
                filename = match[1]
              } else {
                filename = `${docTitle}.docx`
              }
            } else {
              filename = `${docTitle}.docx`
            }
            
            console.log('成功获取Word文档，大小:', blob.size, '字节', '文件名:', filename)
          } else {
            throw new Error('下载API未返回有效数据')
          }
          
        } catch (error) {
          console.error('获取合同文件失败:', error)
          ElMessage.error('生成合同文件失败，无法获取合同内容')
          loading.close()
          return
        }
        
        if (!blob || blob.size === 0) {
          console.error('生成Word文档失败：blob为空或大小为0')
          ElMessage.error('生成合同文件失败')
          loading.close()
          return
        }

        // 3. 上传文件到聊天
        loading.text = '正在发送文件...'

        // 检查参数类型
        if (typeof chatId !== 'string' && typeof chatId !== 'number') {
          console.error('聊天ID类型错误:', typeof chatId, chatId);
          throw new Error('聊天ID类型错误，期望为字符串或数字');
        }

        if (!(blob instanceof Blob)) {
          console.error('文件类型错误:', typeof blob, blob);
          throw new Error('文件类型错误，期望为Blob');
        }

        console.log('发送文件到聊天:', {
          chatId: chatId,
          filename: filename,
          blobType: blob.type,
          blobSize: blob.size
        });

        // 将Blob转换为File对象
        const fileObject = new File([blob], filename, { type: blob.type });

        // 使用正确的参数调用sendFileMessage
        await sendFileMessage(chatId, `分享了合同: ${filename}`, fileObject);

        ElMessage.success('合同已成功分享')
        showShareDialog.value = false

      } catch (error) {
        console.error('分享合同失败:', error)
        ElMessage.error('分享失败，请重试')
      } finally {
        loading.close()
      }
    }

    // 提交合同
    const submitContract = async () => {
      // 验证必填字段
      if (creationMode.value === 'template' && selectedTemplate.value === null) {
        ElMessage.error('请选择一个模板')
        return
      }
      
      // 启动全屏加载
      const loading = ElLoading.service({
        lock: true,
        text: '提交中...',
        background: 'rgba(0, 0, 0, 0.7)'
      })
      
      try {
        let contractData = {}
        
        // 根据不同的创建模式处理数据
        if (creationMode.value === 'manual') {
          // 验证必填字段
          if (!newContract.title || !newContract.type || !newContract.company) {
            ElMessage.error('请填写必填字段：合同名称、合同类型和签约对方')
            loading.close()
            return
          }
          
          contractData = {
            title: newContract.title,
            type: newContract.type,
            company: newContract.company,
            amount: newContract.amount ? Number(newContract.amount.replace(/[^\d.]/g, '')) : 0,
            sign_date: formatDate(newContract.signDate),
            start_date: formatDate(newContract.startDate),
            expire_date: formatDate(newContract.expireDate),
            remark: newContract.remark || '',
            status: 'pending'
          }
        } else if (creationMode.value === 'template') {
          // 使用模板创建合同
          if (selectedTemplate.value === null) {
            ElMessage.error('请选择一个模板')
            loading.close()
            return
          }
          
          // 验证必填字段
          if (!templateForm.title) {
            ElMessage.error('请填写合同标题')
            loading.close()
            return
          }
          
          if (!templateForm.company) {
            ElMessage.error('请填写签约对方')
            loading.close()
            return
          }
          
          // 获取选择的模板
          const template = availableTemplates.value[selectedTemplate.value]
          
          try {
            // 使用API创建合同
            await createContractFromTemplate(template.id, {
              title: templateForm.title,
              company: templateForm.company,
              type: template.contract_type,
              amount: templateForm.amount || 0,
              remark: templateForm.remark
            })
            
            // 成功创建后直接显示成功信息并返回
            ElMessage.success('合同已成功创建，请在列表中查看。')
            showNewContractDialog.value = false
            
            // 重新加载合同列表
            await loadContracts()
            
            loading.close()
            return
          } catch (error) {
            console.error('使用模板创建合同失败:', error)
            throw error  // 重新抛出错误，会被外层catch捕获
          }
        } else if (creationMode.value === 'ai') {
          // 验证必填字段
          if (!aiForm.coreElements) {
            ElMessage.error('请填写合同需求描述')
            loading.close()
            return
          }
          
          contractData = {
            description: aiForm.coreElements,
            use_ai_agent: true,
            status: 'pending'
          }
        }
        
        // 调用API创建合同 - 添加重试逻辑
        console.log('提交合同数据:', JSON.stringify(contractData))
        let retryCount = 0
        const maxRetries = 3
        
        while (retryCount < maxRetries) {
          try {
            // 对AI生成设置更长的超时时间
            const timeout = creationMode.value === 'ai' ? 180000 : 60000 // AI生成3分钟，其他1分钟
            
            loading.text = creationMode.value === 'ai' 
              ? '正在使用AI生成合同，这可能需要一些时间...'
              : '正在提交...'
            
            // 创建一个可以取消的请求
            const controller = new AbortController()
            const timeoutId = setTimeout(() => {
              controller.abort()
            }, timeout)
            
            // 发送请求
            await createContractAPI({ 
              ...contractData,
              signal: controller.signal
            })
            
            // 清除超时计时器
            clearTimeout(timeoutId)
            
            // 成功获取响应，跳出循环
            break
          } catch (error) {
            console.error(`合同创建尝试 ${retryCount + 1} 失败:`, error)
            retryCount++
            
            if (retryCount >= maxRetries) {
              loading.close()
              throw new Error(`合同创建失败，已达到最大重试次数: ${error.message}`)
            }
            
            // 等待一段时间后重试
            loading.text = `尝试失败，正在重试 (${retryCount}/${maxRetries})...`
            await new Promise(resolve => setTimeout(resolve, 2000))
          }
        }
        
        if (creationMode.value === 'ai') {
          ElMessage.success('AI生成合同任务已提交，请稍后在列表刷新查看。')
        } else {
          ElMessage.success('合同已成功创建，请在列表中查看。')
        }
        
        // 重新加载合同列表
        await loadContracts()

        showNewContractDialog.value = false
        
      } catch (error) {
        console.error('提交合同失败:', error)
        let errorMsg = '提交合同失败，请检查输入内容'
        
        // 提取更详细的错误信息
        if (error.response && error.response.data) {
          const data = error.response.data
          if (typeof data === 'string') {
            errorMsg = data
          } else if (typeof data === 'object') {
            try {
              const errorDetails = Object.entries(data)
                .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
                .join('; ')
              errorMsg = `提交失败: ${errorDetails}`
            } catch (e) {
              console.error('解析错误详情失败:', e)
            }
          }
        } else if (error.message) {
          errorMsg = error.message
        }
        
        ElMessage.error(errorMsg)
      } finally {
        // 确保loading状态在所有情况下都能关闭
        if (loading && loading.visible) {
          loading.close()
        }
      }
    }
    
    // 初始化加载数据
    onMounted(() => {
      loadContracts()
      loadFilterOptions()
    })
    
    // 监听搜索输入，实现防抖搜索
    watch(searchQuery, () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      searchTimeout = setTimeout(() => {
        handleFilterChange();
      }, 500); // 500ms 防抖
    });

    return {
      searchQuery,
      sortBy,
      sortOrder,
      selectedContract,
      contracts,
      filteredContracts,
      showNewContractDialog,
      creationMode,
      newContract,
      templateForm,
      aiForm,
      selectedTemplate,
      availableTemplates,
      isLoading,
      isLoadingTemplates,
      // 分页相关
      currentPage,
      totalItems,
      // 图标
      Plus,
      Search,
      InfoFilled,
      MoreFilled,
      Edit,
      Share,
      Delete,
      // 方法
      openContractDialog,
      getSubmitButtonText,
      submitContract,
      viewContractDetail,
      handleFilterChange,
      handleContractTypeChange,
      handleTemplateSelect,
      handleCurrentChange,
      handleEdit,
      handleShare,
      handleDelete,
      submitUpdate,
      submitShare,
      editForm,
      showEditDialog,
      showShareDialog,
      shareTargetUsers,
      availableUsers,
      contractTypes,
      industries,
      scenes,
    }
  }
}
</script>

<style scoped lang="scss">
.contract-container {
  padding: 20px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 50px);
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.contract-list-card {
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color);
  color: var(--el-text-color-primary);
}

.contract-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 220px);
}

.contract-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid var(--el-border-color-light);
  transition: all 0.2s;
  background-color: transparent;
}

.contract-main-info {
  flex-grow: 1;
  cursor: pointer;
}

.contract-item:hover {
  background-color: var(--el-fill-color-light);
}

.contract-item.active {
  background-color: var(--el-color-primary-light-9);
  border-left: 3px solid var(--el-color-primary);
}

.contract-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 5px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.contract-info {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  font-weight: 500;
}

.contract-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.status-draft {
  background-color: var(--info-color-bg);
  color: var(--info-color);
}

.status-pending {
  background-color: var(--warning-color-bg);
  color: var(--warning-color);
}

.status-signed {
  background-color: var(--success-color-bg);
  color: var(--success-color);
}

.status-expired {
  background-color: var(--danger-color-bg);
  color: var(--danger-color);
}

.status-rejected {
  background-color: var(--info-color-bg);
  color: var(--info-color);
}

.me-2 {
  margin-right: 8px;
}

.mt-1 {
  margin-top: 4px;
}

.mb-3 {
  margin-bottom: 16px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 10px 0;
  border-top: 1px solid var(--el-border-color-light);
}

.template-list {
  height: 150px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.template-item {
  padding: 10px 15px;
  border-bottom: 1px solid var(--el-border-color-light);
  cursor: pointer;
}

.template-item:hover {
  background-color: var(--el-fill-color-light);
}

.template-item.active {
  background-color: var(--el-color-primary-light-9);
  border-left: 2px solid var(--el-color-primary);
}

.template-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 5px;
}

.template-info {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
}

.template-desc {
  color: var(--el-text-color-regular);
  font-size: 12px;
  margin-top: 5px;
}

.template-hint {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  margin-top: 10px;
}

.custom-template-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 5px;
}

.template-preview {
  max-height: 150px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 10px;
  font-size: 13px;
  line-height: 1.5;
  margin-top: 5px;
  background-color: var(--el-fill-color-lighter);
}

/* 移除之前无用的深色模式强制覆盖 */
html[data-theme="dark"] body .contract-container .contract-item,
body.is-dark .contract-container .contract-item,
html[data-theme="dark"] body .contract-container .contract-item:hover,
body.is-dark .contract-container .contract-item:hover,
html[data-theme="dark"] body .contract-container .contract-item.active,
body.is-dark .contract-container .contract-item.active,
html[data-theme="dark"] body .contract-container .contract-title,
body.is-dark .contract-container .contract-title,
html[data-theme="dark"] body .contract-container .contract-info,
body.is-dark .contract-container .contract-info,
html[data-theme="dark"] body .contract-container .contract-info span,
body.is-dark .contract-container .contract-info span {
  background-color: unset !important;
  border-bottom-color: unset !important;
  border-left-color: unset !important;
  color: unset !important;
}

.contract-actions {
  flex-shrink: 0;
  margin-left: 16px;
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.contract-item:hover .contract-actions {
  opacity: 1;
}

.more-button {
  border: none !important;
  background-color: transparent !important;
}

.el-dropdown-menu__item.text-danger {
  color: var(--danger-color);
}

.new-contract-dialog .el-dialog__body {
  padding: 20px 30px;
}

.template-list {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  min-height: 200px;
  max-height: 40vh;
  overflow-y: auto;
}

.form-label.small.text-muted {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
  display: block;
}

.template-item {
  border: 1px solid #dcdfe6;
  padding: 10px 15px;
  margin-bottom: 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  &.active {
    border-color: #409eff;
    background-color: #ecf5ff;
  }
}

.template-name {
  font-weight: bold;
  margin-bottom: 5px;
}

.template-info {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
  .template-type {
    margin-right: 10px;
  }
}

.template-desc {
  font-size: 13px;
  color: #606266;
}

.template-hint {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 150px;
  text-align: center;
  color: #909399;
  .el-icon {
    margin-right: 8px;
  }
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

[data-theme="dark"] {
  .contract-list-card {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color-light);
  }

  .form-label.small.text-muted {
    color: var(--el-text-color-primary) !important;
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 10px;
  }
  
  .el-form-item__label {
    color: var(--el-text-color-primary) !important;
    font-weight: 500 !important;
  }

  .more-button:hover,
  .more-button:focus {
    background-color: var(--el-fill-color-darker) !important;
    color: var(--el-color-primary) !important;
  }
  
  .el-dropdown-menu__item.text-danger:hover {
    background-color: var(--el-color-danger-light-9);
    color: var(--el-color-danger);
  }

  .template-list {
    border-color: var(--el-border-color);
    background-color: var(--el-bg-color) !important;
  }

  .template-item {
    border-color: var(--el-border-color-light);
    background-color: var(--el-bg-color-overlay) !important;
    &:hover {
      border-color: var(--el-color-primary);
      background-color: var(--el-fill-color-darker) !important;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2) !important;
    }
    &.active {
      border-color: var(--el-color-primary) !important;
      border-width: 2px !important;
      background-color: rgba(64, 158, 255, 0.15) !important;
      box-shadow: 0 0 8px rgba(64, 158, 255, 0.3) !important;
    }
  }

  .template-name {
    color: var(--el-text-color-primary) !important;
    font-weight: 600 !important;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  }

  .template-info {
    color: var(--el-text-color-secondary) !important;
  }
  
  .template-type, .template-industry {
    background-color: var(--el-fill-color-darker);
    padding: 2px 8px;
    border-radius: 4px;
    display: inline-block;
    font-weight: 500;
    color: var(--el-color-info-light-3) !important;
  }

  .template-desc {
    color: var(--el-text-color-secondary) !important;
  }
  
  .template-hint {
    color: var(--el-text-color-secondary) !important;
  }
  
  /* 强制应用样式到模板项的所有可能出现状态 */
  .template-item.active .template-name,
  .template-item:hover .template-name {
    color: var(--el-color-primary) !important;
    text-shadow: 0 1px 3px rgba(64, 158, 255, 0.3);
  }
  
  /* 强化被选中项的对比度 */
  .template-item.active .template-desc {
    color: var(--el-text-color-primary) !important;
  }

  /* 改善空白提示在深色模式下的显示效果 */
  .el-empty {
    &__image {
      opacity: 0.8;
      
      svg {
        color: var(--el-text-color-secondary);
        fill: var(--el-fill-color-darker);
      }
    }
    
    &__description {
      color: var(--el-text-color-primary) !important;
    }
  }
  
  /* 确保选择器组件在深色模式下清晰可见 */
  .el-select {
    .el-input__wrapper {
      background-color: var(--el-bg-color-overlay) !important;
    }
    
    .el-input__inner {
      color: var(--el-text-color-primary) !important;
    }
  }
  
  /* 确保日期选择器在深色模式下清晰可见 */
  .el-date-picker {
    .el-input__wrapper {
      background-color: var(--el-bg-color-overlay) !important;
    }
    
    .el-input__inner {
      color: var(--el-text-color-primary) !important;
    }
  }
}
</style> 
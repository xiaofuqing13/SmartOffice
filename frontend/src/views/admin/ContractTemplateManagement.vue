<template>
  <div class="contract-template-management">
    <h1 class="page-title">合同模板管理</h1>

    <div class="actions">
      <router-link :to="{ name: 'AdminContractTemplateNew' }" class="btn btn-primary">
        <i class="bi bi-plus-lg"></i> 新建模板
      </router-link>
    </div>

    <div class="template-list">
      <div v-if="loading" class="loading-spinner">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
      </div>
      <div v-else-if="templates.length === 0" class="empty-state">
        <i class="bi bi-file-earmark-text-fill"></i>
        <p>暂无合同模板</p>
        <span>点击"新建模板"按钮来创建一个吧</span>
      </div>
      <div v-else class="table-responsive">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th>模板名称</th>
              <th>合同类型</th>
              <th>行业领域</th>
              <th>创建人</th>
              <th>创建时间</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="template in filteredTemplates" :key="template.id">
              <td>{{ template.name }}</td>
              <td><span class="badge bg-secondary">{{ template.contract_type }}</span></td>
              <td>{{ template.industry || '-' }}</td>
              <td>{{ template.created_by_name }}</td>
              <td>{{ new Date(template.created_at).toLocaleDateString() }}</td>
              <td>
                <div class="form-check form-switch d-flex align-items-center">
                  <input class="form-check-input" type="checkbox" role="switch" :id="'switch-' + template.id" v-model="template.is_active" @change="toggleStatus(template)">
                  <label class="form-check-label ms-2" :for="'switch-' + template.id">{{ template.is_active ? '已启用' : '已禁用' }}</label>
                </div>
              </td>
              <td>
                <router-link :to="{ name: 'AdminContractTemplateEdit', params: { id: template.id } }" class="btn btn-sm btn-outline-primary me-2">
                  <i class="bi bi-pencil-square"></i> 编辑
                </router-link>
                <button @click="confirmDelete(template)" class="btn btn-sm btn-outline-danger">
                  <i class="bi bi-trash"></i> 删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-danger text-white">
            <h5 class="modal-title"><i class="bi bi-exclamation-triangle me-2"></i>删除确认</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center py-4">
            <h4>确定要删除此模板吗？</h4>
            <p class="mb-1">模板名称: <strong>{{ templateToDelete?.name }}</strong></p>
            <p class="mb-0 text-danger">此操作无法撤销，请确认您的选择。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-danger" @click="executeDelete" :disabled="deleting">
              <span v-if="deleting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除成功弹窗 -->
    <div class="modal fade" id="deleteSuccessModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title"><i class="bi bi-check-circle me-2"></i>操作成功</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center py-4">
            <h4>模板已成功删除</h4>
          </div>
          <div class="modal-footer justify-content-center">
            <button type="button" class="btn btn-success px-4" data-bs-dismiss="modal">确定</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/api/admin';
import { Modal } from 'bootstrap';

export default {
  name: 'ContractTemplateManagement',
  data() {
    return {
      templates: [],
      loading: true,
      templateToDelete: null,
      deleteConfirmModal: null,
      deleteSuccessModal: null,
      deleting: false,
    };
  },
  computed: {
    filteredTemplates() {
      return this.templates.filter(template => template && template.id);
    }
  },
  mounted() {
    this.fetchTemplates();
    this.deleteConfirmModal = new Modal(document.getElementById('deleteConfirmModal'));
    this.deleteSuccessModal = new Modal(document.getElementById('deleteSuccessModal'));
  },
  methods: {
    async fetchTemplates() {
      this.loading = true;
      try {
        const response = await api.getContractTemplates();
        console.log('API响应:', response); // 调试输出

        if (response && response.data) {
          // 检查并处理分页响应
          const templatesData = Array.isArray(response.data.results) ? response.data.results :
                                (Array.isArray(response.data) ? response.data : []);
          this.templates = templatesData.filter(item => item !== null);
        } else {
          console.error('获取合同模板返回了不正确的数据格式:', response);
          this.templates = [];
        }
      } catch (error) {
        console.error('获取合同模板失败:', error);
        this.showErrorModal('获取模板列表失败，请稍后重试。');
        this.templates = [];
      } finally {
        this.loading = false;
      }
    },
    async toggleStatus(template) {
      const originalStatus = !template.is_active;
      try {
        await api.updateContractTemplate(template.id, { is_active: template.is_active });
        // 可以在这里添加一个成功提示
      } catch (error) {
        console.error('更新模板状态失败:', error);
        // 失败时恢复开关状态
        template.is_active = originalStatus;
        this.showErrorModal('更新模板状态失败，请稍后重试。');
      }
    },
    confirmDelete(template) {
      this.templateToDelete = template;
      this.deleteConfirmModal.show();
    },
    async executeDelete() {
      if (!this.templateToDelete) return;
      
      this.deleting = true;
      try {
        await api.deleteContractTemplate(this.templateToDelete.id);
        this.deleteConfirmModal.hide();
        await this.fetchTemplates();
        this.deleteSuccessModal.show();
      } catch (error) {
        console.error('删除模板失败:', error);
        this.deleteConfirmModal.hide();
        this.showErrorModal('删除模板失败，请稍后重试。');
      } finally {
        this.deleting = false;
        this.templateToDelete = null;
      }
    },
    showErrorModal(message) {
      // 创建临时的错误模态框元素
      const modalDiv = document.createElement('div');
      modalDiv.innerHTML = `
        <div class="modal fade" id="tempErrorModal" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
              <div class="modal-header bg-danger text-white">
                <h5 class="modal-title"><i class="bi bi-exclamation-triangle me-2"></i>操作失败</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body text-center py-4">
                <p class="mb-0">${message}</p>
              </div>
              <div class="modal-footer justify-content-center">
                <button type="button" class="btn btn-secondary px-4" data-bs-dismiss="modal">确定</button>
              </div>
            </div>
          </div>
        </div>`;
      document.body.appendChild(modalDiv);
      
      const errorModal = new Modal(document.getElementById('tempErrorModal'));
      errorModal.show();
      
      // 模态框关闭后移除元素
      document.getElementById('tempErrorModal').addEventListener('hidden.bs.modal', function () {
        document.body.removeChild(modalDiv);
      });
    }
  },
};
</script>

<style scoped>
.contract-template-management {
  padding: 2rem;
  background-color: #f8f9fa;
}

.page-title {
  font-weight: 300;
  color: #343a40;
  margin-bottom: 1.5rem;
}

.actions {
  margin-bottom: 1.5rem;
}

.loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
}

.empty-state {
    text-align: center;
    padding: 3rem;
    border: 2px dashed #dee2e6;
    border-radius: .5rem;
    background-color: #fff;
}

.empty-state i {
    font-size: 3rem;
    color: #6c757d;
}

.empty-state p {
    font-size: 1.2rem;
    font-weight: 500;
    margin-top: 1rem;
}

.empty-state span {
    color: #6c757d;
}

.table {
    background-color: #fff;
    border-radius: .5rem;
    box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,.075);
}

.table th {
    font-weight: 500;
}

.badge {
  font-size: 0.8rem;
}

.form-check.form-switch {
  padding-left: 3.5em; /* 调整以适应标签 */
}
.form-check-input {
  cursor: pointer;
}
</style> 
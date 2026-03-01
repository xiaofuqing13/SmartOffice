<template>
  <div class="contract-template-edit">
    <h1 class="page-title">{{ isEditing ? '编辑' : '新建' }}合同模板</h1>

    <div class="card">
      <div class="card-body">
        <form @submit.prevent="saveTemplate">
          <div class="mb-3">
            <label for="templateName" class="form-label">模板名称 <span class="text-danger">*</span></label>
            <input type="text" v-model="template.name" class="form-control" id="templateName" required>
          </div>

          <div class="row">
            <div class="col-md-6 mb-3">
              <label for="contractType" class="form-label">合同类型 <span class="text-danger">*</span></label>
              <input type="text" v-model="template.contract_type" class="form-control" id="contractType" required>
            </div>
            <div class="col-md-6 mb-3">
              <label for="industry" class="form-label">行业领域 <span class="text-danger">*</span></label>
              <input type="text" v-model="template.industry" class="form-control" id="industry" required>
            </div>
          </div>

          <div class="mb-3">
            <label for="scene" class="form-label">交易场景 <span class="text-danger">*</span></label>
            <input type="text" v-model="template.scene" class="form-control" id="scene" required>
          </div>

          <div class="mb-3">
            <label for="description" class="form-label">模板描述 <span class="text-danger">*</span></label>
            <textarea v-model="template.description" class="form-control" id="description" rows="3" required></textarea>
          </div>

          <div class="mb-4">
            <label class="form-label">模板内容 <span class="text-danger">*</span></label>
            <div ref="quillEditor" style="height: 400px;"></div>
            <div class="invalid-feedback" :style="{display: contentError ? 'block' : 'none'}">
              请输入模板内容
            </div>
          </div>

          <div class="mb-3 form-check">
            <input type="checkbox" v-model="template.is_active" class="form-check-input" id="isActive">
            <label class="form-check-label" for="isActive">启用该模板</label>
          </div>

          <div class="actions-footer">
            <button type="button" @click="cancel" class="btn btn-secondary me-3">
              取消
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              {{ saving ? '保存中...' : '保存模板' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 保存成功弹窗 -->
    <div class="modal fade" id="saveSuccessModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">
              <i class="bi bi-check-circle me-2"></i>操作成功
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center py-4">
            <h4>模板保存成功！</h4>
            <p class="mb-0">合同模板已成功{{ isEditing ? '更新' : '创建' }}。</p>
          </div>
          <div class="modal-footer justify-content-center">
            <button type="button" class="btn btn-success px-4" @click="goToList">
              返回列表
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/api/admin';
import Quill from 'quill';
import 'quill/dist/quill.snow.css';
import { Modal } from 'bootstrap';

export default {
  name: 'ContractTemplateEdit',
  data() {
    return {
      template: {
        name: '',
        contract_type: '',
        industry: '',
        scene: '',
        description: '',
        content: '',
        is_active: true,
      },
      quill: null,
      isEditing: false,
      saving: false,
      contentError: false,
      saveSuccessModal: null,
    };
  },
  async created() {
    const templateId = this.$route.params.id;
    if (templateId) {
      this.isEditing = true;
      await this.fetchTemplateData(templateId);
    }
  },
  mounted() {
    this.initializeQuill();
    this.saveSuccessModal = new Modal(document.getElementById('saveSuccessModal'));
  },
  methods: {
    initializeQuill() {
      if (this.$refs.quillEditor) {
        this.quill = new Quill(this.$refs.quillEditor, {
          theme: 'snow',
          modules: {
            toolbar: [
              [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
              ['bold', 'italic', 'underline', 'strike'],
              [{ 'list': 'ordered'}, { 'list': 'bullet' }],
              [{ 'script': 'sub'}, { 'script': 'super' }],
              [{ 'indent': '-1'}, { 'indent': '+1' }],
              [{ 'direction': 'rtl' }],
              [{ 'size': ['small', false, 'large', 'huge'] }],
              [{ 'color': [] }, { 'background': [] }],
              [{ 'font': [] }],
              [{ 'align': [] }],
              ['clean'],
              ['link', 'image']
            ],
          },
        });
        this.quill.root.innerHTML = this.template.content;
        this.quill.on('text-change', () => {
          this.template.content = this.quill.root.innerHTML;
          this.contentError = false;
        });
      }
    },
    async fetchTemplateData(id) {
      try {
        const response = await api.getContractTemplate(id);
        this.template = response.data;
        if (this.quill) {
          this.quill.root.innerHTML = this.template.content;
        }
      } catch (error) {
        console.error('获取模板数据失败:', error);
        this.showErrorModal('加载模板失败，请稍后重试。');
        this.$router.push({ name: 'AdminContractTemplateManagement' });
      }
    },
    async saveTemplate() {
      // 验证Quill编辑器内容
      if (!this.template.content || this.template.content.replace(/<[^>]*>?/gm, '').trim() === '') {
        this.contentError = true;
        return;
      }

      this.saving = true;
      try {
        if (this.isEditing) {
          await api.updateContractTemplate(this.template.id, this.template);
        } else {
          await api.createContractTemplate(this.template);
        }
        this.saveSuccessModal.show();
      } catch (error) {
        console.error('保存模板失败:', error);
        this.showErrorModal('保存模板失败，请检查输入内容并重试。');
      } finally {
        this.saving = false;
      }
    },
    cancel() {
      this.$router.push({ name: 'AdminContractTemplateManagement' });
    },
    goToList() {
      this.saveSuccessModal.hide();
      this.$router.push({ name: 'AdminContractTemplateManagement' });
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
.contract-template-edit {
  padding: 2rem;
  background-color: #f8f9fa;
}

.page-title {
  font-weight: 300;
  color: #343a40;
  margin-bottom: 1.5rem;
}

.card {
  border: none;
  box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,.075);
}

.actions-footer {
  padding-top: 1rem;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
}

.text-danger {
  color: #dc3545 !important;
}

/* Quill编辑器验证样式 */
.ql-container.ql-error {
  border-color: #dc3545;
}

.invalid-feedback {
  display: none;
  width: 100%;
  margin-top: 0.25rem;
  font-size: 80%;
  color: #dc3545;
}
</style> 
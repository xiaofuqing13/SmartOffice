<template>
  <div class="global-search-container">
    <el-select
      v-model="currentQuery"
      filterable
      remote
      reserve-keyword
      placeholder="在所有应用中搜索..."
      :remote-method="search"
      :loading="loading"
      @change="handleSelect"
      @clear="clearSearch"
      clearable
      class="global-search-input"
      popper-class="global-search-popper"
      size="large"
    >
      <el-option-group
        v-for="group in searchResults"
        :key="group.type"
        :label="group.type"
      >
        <el-option
          v-for="item in group.items"
          :key="item.id + item.type"
          :label="item.title"
          :value="item"
        >
          <div class="search-result-item">
            <div class="item-icon">
              <i :class="getIconForType(item.type)"></i>
            </div>
            <div class="item-content">
              <span class="title">{{ item.title }}</span>
              <span class="summary">{{ item.summary }}</span>
            </div>
          </div>
        </el-option>
      </el-option-group>
      <template #empty>
        <div class="search-empty-state">
          <i v-if="loading" class="el-icon is-loading"><el-icon-loading /></i>
          <span v-else-if="currentQuery && currentQuery.trim().length > 0 && currentQuery.trim().length < 2">请输入至少两个字符进行搜索</span>
          <span v-else>无匹配结果</span>
        </div>
      </template>
    </el-select>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { globalSearch } from '@/api/search'; // 需要在api中创建此方法
import { findOrCreateChat } from '@/api/chat';
import { debounce } from 'lodash';
import {
  Loading as ElIconLoading
} from '@element-plus/icons-vue'

export default {
  name: 'GlobalSearch',
  components: {
    ElIconLoading
  },
  setup(props, { expose }) {
    const router = useRouter();
    const selectedValue = ref(''); // 保留用于跟踪最终选择的值，但不再是 v-model
    const currentQuery = ref(''); // 现在是 v-model，跟踪输入框的实时文本
    const searchResults = ref([]);
    const loading = ref(false);
    const searchCounter = ref(0); // 用于处理竞态条件的计数器

    const getIconForType = (type) => {
      const iconMap = {
        '项目': 'bi bi-kanban',
        '任务': 'bi bi-check2-square',
        '日程': 'bi bi-calendar-week',
        '智能文档': 'bi bi-file-earmark-text',
        '合同': 'bi bi-file-earmark-ruled',
        '知识库': 'bi bi-book',
        '聊天记录': 'bi bi-chat-dots',
        '联系人': 'bi bi-person-lines-fill'
      };
      return iconMap[type] || 'bi bi-app';
    };

    // 封装一个清晰的清除状态的函数
    const clearSearchState = () => {
      selectedValue.value = '';
      currentQuery.value = ''; // 清除输入框文本
      searchResults.value = [];
      loading.value = false;
    };

    const search = debounce(async (query) => {
      // currentQuery.value = query; // 不再需要，因为 v-model 会自动更新
      searchCounter.value++; // 为每个新搜索增加计数器
      const localCounter = searchCounter.value;

      if (query && query.trim().length >= 2) {
        loading.value = true;
        try {
          const { data } = await globalSearch(query);
          // 仅当这是最新的搜索时才更新结果
          if (localCounter === searchCounter.value) {
            const grouped = data.reduce((acc, item) => {
              if (!acc[item.type]) {
                acc[item.type] = { type: item.type, items: [] };
              }
              acc[item.type].items.push(item);
              return acc;
            }, {});
            searchResults.value = Object.values(grouped);
          }
        } catch (error) {
          // 仅为最新的搜索报告错误
          if (localCounter === searchCounter.value) {
            console.error('Global search failed:', error);
            searchResults.value = [];
          }
        } finally {
          // 仅为最新的搜索更新加载状态
          if (localCounter === searchCounter.value) {
            loading.value = false;
          }
        }
      } else {
        searchResults.value = [];
        loading.value = false; // 如果输入无效，确保停止加载
      }
    }, 300);

    const handleSelect = async (url) => {
      // The 'url' is now the full item object because we bind :value="item"
      const item = url; 
      if (!item || !item.type) return;

      if (item.type === '联系人') {
        try {
          const { data } = await findOrCreateChat(item.id);
          if (data && data.chat_id) {
            router.push(`/chat?session=${data.chat_id}`);
          }
        } catch (error) {
          console.error('Failed to find or create chat:', error);
          // Optionally show an error message to the user
        }
      } else {
        // Default behavior for all other types
        if(item.url) {
          router.push(item.url);
        }
      }
      
      searchCounter.value++;
      setTimeout(() => {
        clearSearchState();
      }, 0);
    };

    // 从外部或通过 clearable 按钮调用的清除方法
    const clearSearch = () => {
      searchCounter.value++; // 使所有待处理的请求无效
      clearSearchState();
    };

    expose({
      clearSearch
    });

    return {
      selectedValue,
      currentQuery,
      searchResults,
      loading,
      search,
      handleSelect,
      clearSearch, // 暴露给模板
      getIconForType,
    };
  },
};
</script>

<style>
/* 将 popper 的样式提升为全局，以便应用 */
.global-search-popper {
  width: 400px !important; /* 固定宽度，与输入框一致 */
}

.global-search-popper .el-select-group__title {
  padding-left: 15px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 5px;
}

.global-search-popper .el-select-dropdown__item {
  height: auto;
  padding: 8px 15px;
  line-height: 1.4;
  white-space: normal;
  word-break: break-all;
}
</style>

<style scoped>
.global-search-container {
  width: 400px;
}
.global-search-input {
  width: 100%;
}
.search-result-item {
  display: flex;
  align-items: center;
}
.item-icon {
  font-size: 1.5rem;
  margin-right: 15px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}
.item-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.title {
  font-weight: 500;
  color: var(--el-text-color-regular);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.summary {
  font-size: 0.85rem;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.search-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  text-align: center;
  color: #999;
}
.search-empty-state .el-icon {
  margin-right: 8px;
}
</style> 
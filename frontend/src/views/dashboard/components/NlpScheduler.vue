<template>
  <div class="nlp-scheduler">
    <div class="input-area">
      <el-input
        v-model="query"
        placeholder="请输入您的日程安排，例如：明天下午两点和张三开会"
        clearable
        @keyup.enter="handleQuery"
      >
        <template #append>
          <el-button @click="handleQuery()">智能安排</el-button>
        </template>
      </el-input>
    </div>
    <div class="events-display">
      <el-card v-for="event in events" :key="event.id" class="event-card">
        <template #header>
          <div class="clearfix">
            <span>{{ event.title }}</span>
          </div>
        </template>
        <div class="event-details">
          <p><strong>时间:</strong> {{ formatDateTime(event.start) }} - {{ formatDateTime(event.end) }}</p>
          <p v-if="event.location"><strong>地点:</strong> {{ event.location }}</p>
          <p v-if="event.description"><strong>描述:</strong> {{ event.description }}</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import request from '@/utils/request';

export default {
  name: 'NlpScheduler',
  data() {
    return {
      query: '',
      events: [],
    };
  },
  methods: {
    async handleQuery() {
      if (!this.query.trim()) {
        this.$message.warning('请输入内容');
        return;
      }
      try {
        const response = await request.post('/api/calendar/events/nlp/', { query: this.query });
        if (response.data.success) {
          this.events = response.data.data;
          this.$message.success('操作成功');
          this.query = ''; // Clear input after successful command
        } else {
          this.$message.error(response.data.error || '操作失败');
        }
      } catch (error) {
        this.$message.error('请求失败');
        console.error(error);
      }
    },
    formatDateTime(dateTime) {
      if (!dateTime) return '';
      const date = new Date(dateTime);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    },
  },
};
</script>

<style scoped>
.nlp-scheduler {
  padding: 20px;
}
.input-area {
  margin-bottom: 20px;
}
.event-card {
  margin-bottom: 15px;
}
.clearfix:before,
.clearfix:after {
  display: table;
  content: "";
}
.clearfix:after {
  clear: both
}
</style> 
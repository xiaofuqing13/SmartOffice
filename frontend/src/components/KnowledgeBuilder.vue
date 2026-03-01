<template>
  <div class="knowledge-builder">
    <!-- 知识库构建对话框 -->
    <el-dialog
      v-model="visible"
      title="构建知识库"
      width="650px"
      :close-on-click-modal="false"
      :show-close="buildingStatus !== 'processing'"
      class="builder-dialog"
    >
      <div class="building-status" :key="buildingStatus">
        <div class="status-icon">
          <el-icon v-if="buildingStatus === 'processing'" class="spinning"><Loading /></el-icon>
          <el-icon v-else-if="buildingStatus === 'completed'" class="success"><CircleCheckFilled /></el-icon>
          <el-icon v-else-if="buildingStatus === 'failed'" class="error"><CircleCloseFilled /></el-icon>
        </div>
        <div class="status-text">
          <h3>{{ buildingStatus === 'pending' ? '准备构建知识库' : 
                buildingStatus === 'processing' ? '正在构建知识库' : 
                buildingStatus === 'completed' ? '知识库构建完成' : '知识库构建失败' }}</h3>
          <p>{{ buildingMessage }}</p>
          
          <div v-if="buildingStatus === 'processing'" class="progress-container">
            <el-progress :percentage="buildingProgress" :format="p => `${p}%`"></el-progress>
          </div>
          
          <div v-if="buildingStatus === 'pending'" class="info-container">
            <el-alert
              title="构建知识库将处理所有已上传的文档，并将它们整合到一个统一的知识库中"
              type="info"
              :closable="false"
              show-icon
            >
              <p>这个过程可能需要一些时间，取决于文档数量和大小。</p>
              <p>构建完成后，您将能够使用智能问答功能对知识库进行提问。</p>
            </el-alert>
          </div>
          
          <div v-if="buildingStatus === 'completed'" class="success-container">
            <el-alert
              title="知识库已成功构建！"
              type="success"
              :closable="false"
              show-icon
            >
              <p>所有文档已被处理并整合到知识库中，您现在可以使用智能问答功能。</p>
            </el-alert>
          </div>
          
          <div v-if="buildingStatus === 'failed'" class="error-container">
            <el-alert
              title="知识库构建失败"
              type="error"
              :closable="false"
              show-icon
            >
              <p>{{ buildingMessage }}</p>
              <p>请检查日志或联系管理员解决问题。</p>
            </el-alert>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button v-if="buildingStatus !== 'processing'" @click="close">关闭</el-button>
          <el-button 
            v-if="buildingStatus === 'pending'" 
            type="primary" 
            @click="startBuild">开始构建</el-button>
          <el-button 
            v-if="buildingStatus === 'failed'" 
            type="primary" 
            @click="startBuild">重试</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { buildKnowledgeBase, getKnowledgeBaseStatus } from '@/api/knowledge'
import { 
  Loading, 
  CircleCheckFilled, 
  CircleCloseFilled 
} from '@element-plus/icons-vue'

export default {
  name: 'KnowledgeBuilder',
  components: {
    Loading,
    CircleCheckFilled,
    CircleCloseFilled
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'build-completed', 'build-failed'],
  setup(props, { emit }) {
    // 构建相关状态
    const visible = computed({
      get: () => props.modelValue,
      set: (val) => emit('update:modelValue', val)
    })
    const buildingStatus = ref('pending') // pending, processing, completed, failed
    const buildingProgress = ref(0)
    const buildingMessage = ref('正在初始化...') // 初始化消息
    const buildingOutput = ref('') // GraphRAG命令输出
    const fullOutput = ref('') // 完整GraphRAG命令输出 (备用)
    const buildingStats = ref(null) // 构建统计信息
    
    // 定时器ID
    let pollTimer = null
    // 重试计数器
    let buildingRetryCount = 0

    // 清除轮询定时器
    const clearPollTimer = () => {
      if (pollTimer) {
        clearTimeout(pollTimer)
        pollTimer = null
        console.log('Polling timer cleared.');
      }
    }

    // 启动知识库构建
    const startBuild = async () => {
      console.log('startBuild called');
      try {
        buildingStatus.value = 'processing'
        buildingMessage.value = '正在启动知识库构建，请稍候...' // 更明确的启动消息
        buildingProgress.value = 0
        buildingOutput.value = '' // 清空旧输出
        fullOutput.value = ''   // 清空旧输出
        buildingStats.value = null
        buildingRetryCount = 0 // 重置重试计数器
        
        clearPollTimer(); // 开始构建前先清除旧的定时器
        console.log('Calling buildKnowledgeBase API...');
        const response = await buildKnowledgeBase()
        console.log('buildKnowledgeBase API response:', response)
        
        // API调用成功后立即开始轮询，初始延迟短一点
        pollTimer = setTimeout(pollBuildStatus, 100); 
        console.log('Initial pollBuildStatus scheduled.');

      } catch (error) {
        console.error('启动知识库构建时出错:', error)
        buildingStatus.value = 'failed'
        buildingMessage.value = error.response?.data?.message || error.message || '启动构建失败'
        emit('build-failed', error)
        clearPollTimer();
      }
    }

    // 轮询构建状态
    const pollBuildStatus = async () => {
      console.log('pollBuildStatus called. Current status:', buildingStatus.value);
      // 如果已经是完成或失败状态，或者对话框不可见，则不应再轮询
      if ((buildingStatus.value === 'completed' || buildingStatus.value === 'failed') && pollTimer) {
          console.log('Build already completed or failed, clearing timer from pollBuildStatus.')
          clearPollTimer();
          return;
      }
      if (!visible.value && pollTimer) {
          console.log('Dialog not visible, clearing timer from pollBuildStatus.');
          clearPollTimer();
          return;
      }

      try {
        console.log('Calling getKnowledgeBaseStatus API...');
        const response = await getKnowledgeBaseStatus()
        console.log('getKnowledgeBaseStatus API response:', JSON.stringify(response, null, 2));

        // 直接从响应中获取状态数据，不额外嵌套data属性
        const statusData = response || {};
        
        if (statusData && typeof statusData === 'object') { 
          console.log('Status object received:', statusData);
          
          // 获取状态，确保使用正确的字段名
          const status = statusData.status || 'pending';
          buildingStatus.value = status;
          buildingMessage.value = statusData.message || (status === 'processing' ? '正在处理中，请稍候...' : '等待状态更新...');
          buildingProgress.value = statusData.progress || buildingProgress.value;
          
          console.log('Updated frontend status:', buildingStatus.value, 'Progress:', buildingProgress.value, 'Message:', buildingMessage.value);

          // 处理GraphRAG命令输出
          if (statusData.full_output) {
            buildingOutput.value = statusData.full_output;
            fullOutput.value = statusData.full_output;
          } else if (statusData.graphrag_output) {
            buildingOutput.value = statusData.graphrag_output;
          }
          
          // 滚动输出框到底部
          nextTick(() => {
            const outputElem = document.querySelector('.output-content pre')
            if (outputElem) {
              outputElem.scrollTop = outputElem.scrollHeight
            }
          });
          
          // 根据状态决定下一步操作
          if (status === 'completed' || status === 'failed') {
            console.log(`Build ended with status: ${status}. Stopping poll.`);
            clearPollTimer();

            if (status === 'completed') {
              buildingProgress.value = 100; // 确保完成时进度为100%
              // 构建完成，处理统计数据
              const startTime = statusData.started_at ? new Date(statusData.started_at) : null;
              const endTime = statusData.finished_at ? new Date(statusData.finished_at) : new Date();
            
              buildingStats.value = {
                startTime: startTime,
                endTime: endTime,
                duration: startTime && endTime ? calculateDuration(startTime, endTime) : '未知',
                totalDocs: statusData.total_docs || 0,
                totalChunks: statusData.total_chunks || 0
              };
            
              ElMessage.success(statusData.message || '知识库构建完成！');
              emit('build-completed');
            } else { // failed
              ElMessage.error(statusData.message || '知识库构建失败，请查看输出或日志。');
              emit('build-failed', { message: statusData.message, detail: statusData.error_detail });
            }
          } else if (status === 'processing') {
            const pollInterval = 1000; // 统一轮询间隔为1秒
            console.log(`Status is 'processing'. Scheduling next poll in ${pollInterval}ms.`);
            clearPollTimer(); // 清除旧的，避免重复
            pollTimer = setTimeout(pollBuildStatus, pollInterval);
          } else if (status === 'pending') {
            // 对于pending状态，也需要继续轮询，但可以间隔长一些
            const pollInterval = 2000;
            console.log(`Status is 'pending'. Scheduling next poll in ${pollInterval}ms.`);
            clearPollTimer();
            pollTimer = setTimeout(pollBuildStatus, pollInterval);
          } else {
            console.warn('Unknown status from backend:', status, 'Stopping poll.');
            clearPollTimer(); // 未知状态，停止轮询以防意外
          }

        } else {
          console.warn('Invalid or empty response object from getKnowledgeBaseStatus. Response:', JSON.stringify(response));
          buildingMessage.value = '获取状态响应格式无效...';
          
          if (buildingStatus.value === 'processing') {
             const pollInterval = 3000; 
             clearPollTimer();
             pollTimer = setTimeout(pollBuildStatus, pollInterval);
          } else {
            buildingStatus.value = 'failed';
            buildingMessage.value = '获取状态失败，响应无效。';
            emit('build-failed', { message: '获取状态失败，响应无效。'});
            clearPollTimer();
          }
        }
      } catch (error) {
        console.error('获取构建状态时出错 (pollBuildStatus catch):', error)
        buildingMessage.value = '获取构建状态失败: ' + (error.message || '未知错误') + '. 将尝试再次轮询。'
        
        // 在错误情况下，如果当前是processing状态，尝试再次轮询几次
        if (buildingStatus.value === 'processing') {
            // 增加重试计数器，避免无限轮询
            buildingRetryCount = (buildingRetryCount || 0) + 1;
            
            if (buildingRetryCount <= 5) { // 最多重试5次
                const pollInterval = 3000; // 错误后延长轮询间隔
                clearPollTimer();
                pollTimer = setTimeout(pollBuildStatus, pollInterval);
                console.log(`轮询错误，第${buildingRetryCount}次重试，${pollInterval}ms后重试`);
            } else {
                console.error('轮询重试次数已达上限，停止轮询');
                buildingStatus.value = 'failed';
                buildingMessage.value = '获取构建状态失败，已达重试上限。';
                emit('build-failed', error);
                clearPollTimer();
            }
        } else {
            buildingStatus.value = 'failed';
            buildingMessage.value = '获取构建状态失败。';
            emit('build-failed', error);
            clearPollTimer();
        }
      }
    }
    
    // 计算持续时间
    const calculateDuration = (start, end) => {
      const diff = Math.abs(end - start)
      const minutes = Math.floor(diff / 60000)
      const seconds = ((diff % 60000) / 1000).toFixed(0)
      return `${minutes}分${seconds}秒`
    }
    
    // 格式化构建时间
    const formatBuildTime = (dateObj) => {
      if (!dateObj) return '未知'
      return dayjs(dateObj).format('YYYY-MM-DD HH:mm:ss')
    }
    
    // 关闭对话框
    const close = () => {
      visible.value = false
    }
    
    // 组件挂载时
    onMounted(() => {
      console.log('KnowledgeBuilder onMounted. Initial modelValue:', props.modelValue);
      // 不自动开始轮询，等待startBuild被调用
    })
    
    // 组件销毁前清理
    onBeforeUnmount(() => {
      console.log('KnowledgeBuilder onBeforeUnmount. Clearing poll timer.');
      clearPollTimer()
    })

    watch(visible, (newVal) => {
      if (newVal) {
        // 当对话框打开时
        console.log('Dialog became visible. Current status:', buildingStatus.value);
        if (buildingStatus.value !== 'processing') {
          // 如果不是正在处理中 (例如是 completed, failed, 或初始的 pending)，
          // 则重置为初始待构建状态，以便用户可以开始新的构建。
          console.log('Resetting status to pending for new build session.');
          buildingStatus.value = 'pending';
          buildingMessage.value = '准备开始新的知识库构建。'; // 或者更合适的初始消息
          buildingProgress.value = 0;
          buildingOutput.value = '';
          fullOutput.value = '';
          buildingStats.value = null;
          buildingRetryCount = 0; // 重置重试计数器
          clearPollTimer(); // 确保没有意外的轮询
        }
        // 如果是 processing，则什么都不做，让它继续处理或轮询
      } else {
        // 当对话框关闭时
        console.log('Dialog closed. Current status:', buildingStatus.value);
        // 如果正在处理中，用户关闭了对话框，最好停止轮询，避免后台继续请求
        if (buildingStatus.value === 'processing') {
            console.log('Dialog closed during processing, stopping poll timer.');
            clearPollTimer();
        }
      }
    });

    return {
      visible,
      buildingStatus,
      buildingProgress,
      buildingMessage,
      buildingOutput,
      fullOutput,
      buildingStats,
      startBuild,
      formatBuildTime,
      close
    }
  }
}
</script>

<style scoped>
.builder-dialog {
  max-width: 90vw;
}

.building-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.status-icon {
  margin-bottom: 20px;
  font-size: 48px;
  display: flex;
  justify-content: center;
  color: #6c757d;
}

.status-icon .spinning {
  animation: spin 2s linear infinite;
}

.status-icon .success {
  color: #67C23A;
}

.status-icon .error {
  color: #F56C6C;
}

.status-text {
  text-align: center;
  width: 100%;
}

.status-text h3 {
  margin-bottom: 15px;
  font-size: 20px;
  font-weight: 600;
}

.status-text p {
  margin: 5px 0;
}

.progress-container {
  margin: 20px 0;
  width: 100%;
}

.info-container, .success-container, .error-container {
  margin: 20px 0;
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 
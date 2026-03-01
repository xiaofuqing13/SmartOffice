<template>
  <div class="calendar-event-container" v-if="eventData">
    <div class="calendar-event-card">
      <div class="calendar-event-header" :class="'event-type-' + eventData.type">
        <i class="el-icon calendar-icon"><Calendar /></i>
        <span class="event-title">{{ eventData.title }}</span>
      </div>
      <div class="calendar-event-content">
        <div class="event-time">
          <i class="el-icon"><Clock /></i>
          <span>{{ formatDateRange(eventData.start, eventData.end) }}</span>
        </div>
        <div class="event-location" v-if="eventData.location">
          <i class="el-icon"><Location /></i>
          <span>{{ eventData.location }}</span>
        </div>
        <div class="event-description" v-if="eventData.description">
          <i class="el-icon"><InfoFilled /></i>
          <span>{{ eventData.description }}</span>
        </div>
      </div>
      <div class="calendar-event-actions" v-if="!calendarEventAdded">
        <el-button type="primary" size="small" @click="showDetails">详情</el-button>
        <el-button type="success" size="small" @click="addToCalendar">添加</el-button>
        <el-button type="default" size="small" @click="hideCalendarEvent">取消</el-button>
      </div>
      <div class="calendar-event-success" v-else>
        <el-alert
          type="success"
          :closable="false"
          show-icon
        >
          <span>已成功添加到日程</span>
        </el-alert>
      </div>
    </div>

    <!-- 日程详情对话框 -->
    <el-dialog
      v-model="detailsVisible"
      title="日程详情"
      width="500px"
    >
      <el-form :model="editableEvent" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editableEvent.title" placeholder="请输入日程标题"></el-input>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="editableEvent.start"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="editableEvent.end"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="editableEvent.location" placeholder="请输入地点"></el-input>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="editableEvent.type" placeholder="请选择日程类型">
            <el-option label="会议" value="blue"></el-option>
            <el-option label="出差" value="orange"></el-option>
            <el-option label="假期" value="green"></el-option>
            <el-option label="截止日期" value="red"></el-option>
            <el-option label="其他" value="purple"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提醒">
          <el-select v-model="editableEvent.reminder" placeholder="请选择提醒时间">
            <el-option label="不提醒" value="none"></el-option>
            <el-option label="10分钟前" value="10min"></el-option>
            <el-option label="30分钟前" value="30min"></el-option>
            <el-option label="1小时前" value="1hour"></el-option>
            <el-option label="1天前" value="1day"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="全天事件">
          <el-switch v-model="editableEvent.is_all_day"></el-switch>
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="editableEvent.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入描述信息"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailsVisible = false">取消</el-button>
          <el-button type="primary" @click="addToCalendarWithEdits">添加</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, toRefs } from 'vue'
import { ElMessage } from 'element-plus'
import { Calendar, Clock, Location, InfoFilled } from '@element-plus/icons-vue'
import { addCalendarEvent } from '@/api/chat'
import { formatDate } from '@/utils/date'

export default {
  name: 'ChatCalendarEvent',
  
  components: {
    Calendar,
    Clock,
    Location,
    InfoFilled
  },
  
  props: {
    messageId: {
      type: Number,
      required: true
    },
    eventData: {
      type: Object,
      required: true
    }
  },
  
  emits: ['calendar-event-added', 'calendar-event-hidden'],
  
  setup(props, { emit }) {
    const calendarEventAdded = ref(false)
    const detailsVisible = ref(false)
    const { eventData } = toRefs(props)
    
    // 创建可编辑的事件对象
    const editableEvent = reactive({
      title: '',
      start: '',
      end: '',
      location: '',
      type: 'blue',
      reminder: '30min',
      description: '',
      is_all_day: false
    })
    
    // 当打开详情对话框时，初始化可编辑事件
    const initEditableEvent = () => {
      if (eventData.value) {
        editableEvent.title = eventData.value.title || ''
        editableEvent.start = formatDateForPicker(eventData.value.start)
        editableEvent.end = formatDateForPicker(eventData.value.end)
        editableEvent.location = eventData.value.location || ''
        editableEvent.type = eventData.value.type || 'blue'
        editableEvent.reminder = eventData.value.reminder || '30min'
        editableEvent.description = eventData.value.description || ''
        editableEvent.is_all_day = eventData.value.is_all_day || false
      }
    }
    
    // 格式化日期为日期选择器所需格式
    const formatDateForPicker = (dateString) => {
      if (!dateString) return ''
      
      try {
        const date = new Date(dateString)
        return formatDate(date, 'YYYY-MM-DD HH:mm:ss')
      } catch (e) {
        return ''
      }
    }
    
    // 显示详情对话框
    const showDetails = () => {
      initEditableEvent()
      detailsVisible.value = true
    }
    
    // 添加到日历
    const addToCalendar = async () => {
      try {
        await addCalendarEvent(props.messageId)
        calendarEventAdded.value = true
        ElMessage.success('日程添加成功')
        emit('calendar-event-added')
      } catch (error) {
        ElMessage.error('添加日程失败：' + (error.response?.data?.error || error.message))
      }
    }
    
    // 使用编辑后的内容添加到日历
    const addToCalendarWithEdits = async () => {
      try {
        await addCalendarEvent(props.messageId, editableEvent)
        calendarEventAdded.value = true
        detailsVisible.value = false
        ElMessage.success('日程添加成功')
        emit('calendar-event-added')
      } catch (error) {
        ElMessage.error('添加日程失败：' + (error.response?.data?.error || error.message))
      }
    }
    
    // 隐藏日程卡片
    const hideCalendarEvent = () => {
      emit('calendar-event-hidden')
    }
    
    // 格式化日期范围
    const formatDateRange = (start, end) => {
      if (!start) return '时间未指定'
      
      try {
        const startDate = new Date(start)
        const endDate = end ? new Date(end) : null
        
        const startDateStr = formatDate(startDate, 'YYYY年MM月DD日 HH:mm')
        
        if (!endDate) return startDateStr
        
        // 如果是同一天，只显示一次日期
        if (startDate.toDateString() === endDate.toDateString()) {
          return `${formatDate(startDate, 'YYYY年MM月DD日 HH:mm')} - ${formatDate(endDate, 'HH:mm')}`
        }
        
        return `${formatDate(startDate, 'YYYY年MM月DD日 HH:mm')} - ${formatDate(endDate, 'YYYY年MM月DD日 HH:mm')}`
      } catch (e) {
        return '时间格式错误'
      }
    }
    
    return {
      calendarEventAdded,
      detailsVisible,
      editableEvent,
      showDetails,
      addToCalendar,
      addToCalendarWithEdits,
      hideCalendarEvent,
      formatDateRange
    }
  }
}
</script>

<style scoped>
.calendar-event-container {
  margin: 4px 0;
  width: 100%;
}

.calendar-event-card {
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  background-color: #fff;
  border: 1px solid #ebeef5;
}

.calendar-event-header {
  padding: 10px 12px;
  display: flex;
  align-items: center;
  color: #fff;
  font-weight: 500;
  font-size: 14px;
}

.event-type-blue {
  background-color: #409eff;
}

.event-type-orange {
  background-color: #e6a23c;
}

.event-type-green {
  background-color: #67c23a;
}

.event-type-red {
  background-color: #f56c6c;
}

.event-type-purple {
  background-color: #909399;
}

.calendar-icon {
  margin-right: 8px;
}

.event-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.calendar-event-content {
  padding: 12px;
  font-size: 13px;
  color: #606266;
}

.event-time, .event-location, .event-description {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
}

.event-description {
  margin-bottom: 0;
}

.el-icon {
  margin-right: 8px;
  flex-shrink: 0;
  margin-top: 2px;
}

.calendar-event-actions {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px;
  border-top: 1px solid #ebeef5;
  gap: 8px;
}

.calendar-event-success {
  padding: 8px 12px;
}
</style> 
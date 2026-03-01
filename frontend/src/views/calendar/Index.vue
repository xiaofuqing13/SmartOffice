<template>
  <div class="calendar-container" :key="internalRefreshKey">
    <!-- 顶部操作栏 -->
    <div class="calendar-header">
      <div class="date-controls">
        <el-button type="primary" @click="today">今天</el-button>
        <div class="date-nav">
          <el-button :icon="ArrowLeft" plain @click="prev"></el-button>
          <span class="current-date">{{ currentDateLabel }}</span>
          <el-button :icon="ArrowRight" plain @click="next"></el-button>
        </div>
      </div>
      <div class="view-controls">
        <el-radio-group v-model="calendarView" size="small">
          <el-radio-button value="month">月</el-radio-button>
          <el-radio-button value="week">周</el-radio-button>
          <el-radio-button value="day">日</el-radio-button>
        </el-radio-group>
      </div>
      <div class="action-controls">
        <el-button type="primary" @click="e => showAddEventDialog(e)">
          <el-icon><Plus /></el-icon> 新建日程
        </el-button>
      </div>
    </div>

    <!-- 日历主体 -->
    <div class="calendar-main" v-if="calendarView === 'month'">
      <!-- 星期头部 -->
      <div class="calendar-weekdays">
        <div class="weekday" v-for="(day, index) in weekDays" :key="index">{{ day }}</div>
      </div>
      
      <!-- 日历网格 -->
      <div class="calendar-days">
        <div 
          v-for="(day, index) in days" 
          :key="index" 
          class="calendar-day" 
          :class="{ 
            'today': day.isToday, 
            'other-month': !day.isCurrentMonth,
            'has-events': day.events && day.events.length > 0
          }"
          @click="selectDay(day)"
        >
          <div class="day-number">{{ day.date }}</div>
          <div class="event-container">
            <div 
              v-for="(event, eventIndex) in day.events.slice(0, 3)" 
              :key="eventIndex" 
              class="event-item"
              :class="'event-' + event.type"
              @mouseenter="showEventPreview(event, $event)"
              @mouseleave="hideEventPreview"
              @click.stop="showEventDetails(event)"
            >
              <span class="event-color" :style="{background: eventTypeColor(event.type)}"></span>
              {{ event.title }}
            </div>
            <div 
              v-if="day.events && day.events.length > 3" 
              class="more-events-indicator" 
              @click.stop="showAllEvents(day)"
            >
              查看全部 {{ day.events.length }} 个日程
            </div>
          </div>
        </div>
      </div>
      <!-- 日程预览浮层 -->
      <div v-if="eventPreview.visible" class="event-preview-pop" :style="eventPreview.style">
        <div class="event-preview-title">{{ eventPreview.event.title }}</div>
        <div class="event-preview-time">{{ formatEventTime(eventPreview.event) }}</div>
        <div class="event-preview-location" v-if="eventPreview.event.location">
          <i class="bi bi-geo-alt"></i> {{ eventPreview.event.location }}
        </div>
        <div class="event-preview-desc" v-if="eventPreview.event.description">
          {{ eventPreview.event.description }}
        </div>
      </div>
      <!-- 全部日程弹窗 -->
      <el-dialog v-model="allEventsDialog.visible" :title="allEventsDialog.title" width="400px" @close="allEventsDialog.date = null">
        <div v-if="allEventsForDialog.length === 0">暂无日程</div>
        <el-timeline v-else>
          <el-timeline-item
            v-for="(event, idx) in allEventsForDialog"
            :key="idx"
            :color="eventTypeColor(event.type)"
          >
            <div class="all-event-title">{{ event.title }}</div>
            <div class="all-event-time">{{ formatEventTime(event) }}</div>
            <div class="all-event-location" v-if="event.location">
              <i class="bi bi-geo-alt"></i> {{ event.location }}
            </div>
            <div class="all-event-desc" v-if="event.description">
              {{ event.description }}
            </div>
            <el-button size="mini" type="link" @click="showEventDetails(event)">详情</el-button>
          </el-timeline-item>
        </el-timeline>
      </el-dialog>
    </div>

    <!-- 周视图 -->
    <div class="calendar-week" v-if="calendarView === 'week'">
      <div class="week-header">
        <div class="week-time-col"></div>
        <div 
          v-for="(day, index) in weekDates" 
          :key="index" 
          class="week-day-col"
          :class="{ 'today': day.isToday }"
        >
          <div class="week-day-name">{{ day.dayName }}</div>
          <div class="week-day-date">{{ day.date }}</div>
        </div>
      </div>
      
      <div class="week-body">
        <div class="week-time-scale">
          <div v-for="hour in 24" :key="hour" class="time-slot">
            {{ hour - 1 }}:00
          </div>
        </div>
        
        <div class="week-events-container">
          <div 
            v-for="(day, dayIndex) in weekDates" 
            :key="dayIndex" 
            class="week-day-events"
          >
            <!-- 全天事件 -->
            <div class="week-all-day-events">
              <div
                v-for="(event, eventIndex) in day.allDayEvents"
                :key="'all-day-' + eventIndex"
                class="week-all-day-event"
                :class="'event-' + event.type"
                @click="showEventDetails(event)"
                @mouseenter="showEventPreview(event, $event)"
                @mouseleave="hideEventPreview"
              >
                <span class="event-color" :style="{background: eventTypeColor(event.type)}"></span>
                <span class="all-day-event-title">{{ event.title }}</span>
              </div>
            </div>

            <!-- 普通事件 -->
            <div 
              v-for="(eventGroup, groupIndex) in day.eventGroups"
              :key="'group-' + groupIndex"
              class="week-event-group"
              :style="{left: (groupIndex * (100 / day.eventGroups.length)) + '%', 
                      width: (100 / day.eventGroups.length) + '%'}"
            >
              <div 
                v-for="(event, eventIndex) in eventGroup"
                :key="eventIndex"
                class="week-event"
                :class="'event-' + event.type"
                :style="{
                  top: calcEventTop(event) + 'px',
                  height: calcEventHeight(event) + 'px',
                }"
                @click="showEventDetails(event)"
                @mouseenter="showEventPreview(event, $event)"
                @mouseleave="hideEventPreview"
                draggable="true"
                @dragstart="dragStart($event, event)"
                @dragend="dragEnd"
              >
                <span class="event-color" :style="{background: eventTypeColor(event.type)}"></span>
                <div class="week-event-title">{{ event.title }}</div>
                <div class="week-event-time">{{ formatEventTime(event) }}</div>
                <div class="resize-handle bottom" @mousedown="startResize($event, event)"></div>
              </div>
            </div>
          </div>
          
          <!-- 移除当前时间线 -->
        </div>
      </div>
    </div>
    
    <!-- 日视图 -->
    <div class="calendar-day-view" v-if="calendarView === 'day'">
      <div class="day-header">
        <div class="day-date">
          {{ currentDate.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}
        </div>
      </div>
      
      <div class="day-body">
        <div class="day-time-scale">
          <div v-for="hour in 24" :key="hour" class="time-slot">
            {{ hour - 1 }}:00
          </div>
        </div>
        
        <div class="day-events-container">
          <!-- 全天事件 -->
          <div class="day-all-day-events">
            <div
              v-for="(event, eventIndex) in allDayEvents"
              :key="'all-day-' + eventIndex"
              class="day-all-day-event"
              :class="'event-' + event.type"
              @click="showEventDetails(event)"
              @mouseenter="showEventPreview(event, $event)"
              @mouseleave="hideEventPreview"
            >
              <span class="event-color" :style="{background: eventTypeColor(event.type)}"></span>
              <span class="all-day-event-title">{{ event.title }}</span>
            </div>
          </div>
          
          <!-- 移除日视图的当前时间线 -->
          
          <!-- 普通事件 -->
          <div 
            v-for="(eventGroup, groupIndex) in dayEventGroups" 
            :key="'group-' + groupIndex"
            class="day-event-group"
            :style="{left: (groupIndex * (100 / dayEventGroups.length)) + '%', 
                    width: (100 / dayEventGroups.length) + '%'}"
          >
            <div 
              v-for="(event, eventIndex) in eventGroup" 
              :key="eventIndex" 
              class="day-event"
              :class="'event-' + event.type"
              :style="{
                top: calcEventTop(event) + 'px',
                height: calcEventHeight(event) + 'px'
              }"
              @click="showEventDetails(event)"
              @mouseenter="showEventPreview(event, $event)"
              @mouseleave="hideEventPreview"
              draggable="true"
              @dragstart="dragStart($event, event)"
              @dragend="dragEnd"
            >
              <span class="event-color" :style="{background: eventTypeColor(event.type)}"></span>
              <div class="day-event-title">{{ event.title }}</div>
              <div class="day-event-time">{{ formatEventTime(event) }}</div>
              <div class="day-event-location" v-if="event.location">
                <i class="bi bi-geo-alt"></i> {{ event.location }}
              </div>
              <div class="resize-handle bottom" @mousedown="startResize($event, event)"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加日程对话框 -->
    <el-dialog
      v-model="addEventDialogVisible"
      title="新建日程"
      width="500px"
      class="calendar-dialog"
      :append-to-body="true"
      :destroy-on-close="false"
      :close-on-click-modal="false"
    >
      <el-form :model="newEvent" label-width="80px" v-if="addEventDialogVisible" :rules="rules" ref="addEventFormRef">
        <el-form-item label="标题" prop="title" required>
          <el-input v-model="newEvent.title" placeholder="请输入日程标题"></el-input>
        </el-form-item>
        <el-form-item label="开始时间" prop="start" required>
          <el-date-picker
            v-model="newEvent.start"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            @change="handleStartTimeChange(newEvent)"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="结束时间" prop="end" required>
          <el-date-picker
            v-model="newEvent.end"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="地点" prop="location" required>
          <el-input v-model="newEvent.location" placeholder="请输入地点"></el-input>
        </el-form-item>
        <el-form-item label="类型" prop="type" required>
          <el-select v-model="newEvent.type" placeholder="请选择日程类型">
            <el-option label="会议" value="blue"></el-option>
            <el-option label="出差" value="orange"></el-option>
            <el-option label="假期" value="green"></el-option>
            <el-option label="截止日期" value="red"></el-option>
            <el-option label="其他" value="purple"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提醒" prop="reminder" required>
          <el-select v-model="newEvent.reminder" placeholder="请选择提醒时间">
            <el-option label="不提醒" value="none"></el-option>
            <el-option label="10分钟前" value="10min"></el-option>
            <el-option label="30分钟前" value="30min"></el-option>
            <el-option label="1小时前" value="1hour"></el-option>
            <el-option label="1天前" value="1day"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="description" required>
          <el-input 
            v-model="newEvent.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addEventDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addEvent">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 日程详情对话框 -->
    <el-dialog
      v-model="eventDetailsDialogVisible"
      :title="selectedEvent.title"
      width="500px"
      class="calendar-dialog"
    >
      <div class="event-details">
        <div class="event-detail-item">
          <i class="bi bi-clock"></i>
          <span>{{ formatEventDateTime(selectedEvent) }}</span>
        </div>
        <div class="event-detail-item" v-if="selectedEvent.location">
          <i class="bi bi-geo-alt"></i>
          <span>{{ selectedEvent.location }}</span>
        </div>
        <div class="event-detail-item" v-if="selectedEvent.description">
          <i class="bi bi-card-text"></i>
          <div class="event-description">{{ selectedEvent.description }}</div>
        </div>
        <div class="event-detail-item">
          <i class="bi bi-bell"></i>
          <span>{{ formatReminder(selectedEvent.reminder) }}</span>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="eventDetailsDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="showEditEventDialog">编辑</el-button>
          <el-button type="danger" @click="deleteEvent">删除</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑日程对话框 -->
    <el-dialog
      v-model="editEventDialogVisible"
      title="编辑日程"
      width="500px"
      class="calendar-dialog"
    >
      <el-form :model="editingEvent" label-width="80px" :rules="rules" ref="editEventFormRef">
        <el-form-item label="标题" prop="title" required>
          <el-input v-model="editingEvent.title" placeholder="请输入日程标题"></el-input>
        </el-form-item>
        <el-form-item label="开始时间" prop="start" required>
          <el-date-picker
            v-model="editingEvent.start"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            @change="handleStartTimeChange(editingEvent)"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="结束时间" prop="end" required>
          <el-date-picker
            v-model="editingEvent.end"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="地点" prop="location" required>
          <el-input v-model="editingEvent.location" placeholder="请输入地点"></el-input>
        </el-form-item>
        <el-form-item label="类型" prop="type" required>
          <el-select v-model="editingEvent.type" placeholder="请选择日程类型">
            <el-option label="会议" value="blue"></el-option>
            <el-option label="出差" value="orange"></el-option>
            <el-option label="假期" value="green"></el-option>
            <el-option label="截止日期" value="red"></el-option>
            <el-option label="其他" value="purple"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提醒" prop="reminder" required>
          <el-select v-model="editingEvent.reminder" placeholder="请选择提醒时间">
            <el-option label="不提醒" value="none"></el-option>
            <el-option label="10分钟前" value="10min"></el-option>
            <el-option label="30分钟前" value="30min"></el-option>
            <el-option label="1小时前" value="1hour"></el-option>
            <el-option label="1天前" value="1day"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="description" required>
          <el-input 
            v-model="editingEvent.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editEventDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveEditEvent">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick, onActivated, onBeforeUnmount, onUnmounted, getCurrentInstance } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import { getMonthlyEvents, getWeeklyEvents, getDailyEvents, createEvent, updateEvent, deleteCalendarEvent as deleteCalendarEventApi } from '@/api/calendar'

export default {
  name: 'Calendar',
  setup() {
    // 路由相关
    const route = useRoute();
    
    // 日历视图类型：月/周/日
    const calendarView = ref('month')
    
    // 当前日期
    const currentDate = ref(new Date())
    
    // 事件数据
    const events = ref([])
    
    // 表单引用
    const addEventFormRef = ref(null)
    const editEventFormRef = ref(null)
    
    // 表单验证规则
    const rules = {
      title: [
        { required: true, message: '请输入日程标题', trigger: 'blur' }
      ],
      start: [
        { required: true, message: '请选择开始时间', trigger: 'change' }
      ],
      end: [
        { required: true, message: '请选择结束时间', trigger: 'change' }
      ],
      location: [
        { required: true, message: '请输入地点', trigger: 'blur' }
      ],
      type: [
        { required: true, message: '请选择日程类型', trigger: 'change' }
      ],
      reminder: [
        { required: true, message: '请选择提醒时间', trigger: 'change' }
      ],
      description: [
        { required: true, message: '请输入备注信息', trigger: 'blur' }
      ]
    }
    
    // 格式化当前日期标签
    const currentDateLabel = computed(() => {
      const options = { year: 'numeric', month: 'long' }
      if (calendarView.value === 'week') {
        return `${currentDate.value.getFullYear()}年${currentDate.value.getMonth() + 1}月第${Math.ceil((currentDate.value.getDate() + getFirstDayOfMonth(currentDate.value).getDay()) / 7)}周`
      } else if (calendarView.value === 'day') {
        return currentDate.value.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
      }
      return currentDate.value.toLocaleDateString('zh-CN', options)
    })
    
    // 星期数组
    const weekDays = ref(['日', '一', '二', '三', '四', '五', '六'])
    
    // 对话框状态
    const addEventDialogVisible = ref(false)
    const eventDetailsDialogVisible = ref(false)
    const editEventDialogVisible = ref(false)
    
    // 新建日程
    const newEvent = ref({
      title: '',
      start: '',
      end: '',
      location: '',
      type: 'blue',
      reminder: '30min',
      description: ''
    })
    
    // 选中的日程
    const selectedEvent = ref({})
    
    // 正在编辑的日程
    const editingEvent = ref({
      id: '',
      title: '',
      start: '',
      end: '',
      location: '',
      type: 'blue',
      reminder: '30min',
      description: ''
    })
    
    // 生成月视图的日期数据
    const days = computed(() => {
      const result = []
      const today = new Date()
      
      // 获取当月第一天是星期几
      const firstDay = getFirstDayOfMonth(currentDate.value).getDay()
      
      // 获取当月天数
      const daysInMonth = getDaysInMonth(currentDate.value)
      
      // 获取上个月天数
      const daysInLastMonth = getDaysInMonth(
        new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1)
      )
      
      // 添加上个月的日期
      for (let i = firstDay - 1; i >= 0; i--) {
        const day = daysInLastMonth - i
        const date = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, day)
        result.push({
          date: day,
          isCurrentMonth: false,
          isToday: isSameDay(date, today),
          events: getDayEvents(date)
        })
      }
      
      // 添加当月的日期
      for (let i = 1; i <= daysInMonth; i++) {
        const date = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth(), i)
        result.push({
          date: i,
          isCurrentMonth: true,
          isToday: isSameDay(date, today),
          events: getDayEvents(date)
        })
      }
      
      // 添加下个月的日期，补满42个格子（6行7列）
      const remaining = 42 - result.length
      for (let i = 1; i <= remaining; i++) {
        const date = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, i)
        result.push({
          date: i,
          isCurrentMonth: false,
          isToday: isSameDay(date, today),
          events: getDayEvents(date)
        })
      }
      
      return result
    })
    
    // 周视图数据
    const weekDates = computed(() => {
      const result = []
      const date = new Date(currentDate.value)
      const day = date.getDay()
      
      // 设置到本周的周日
      date.setDate(date.getDate() - day)
      
      // 生成一周的日期
      for (let i = 0; i < 7; i++) {
        const currentDate = new Date(date)
        currentDate.setDate(date.getDate() + i)
        
        const dayEvents = getDayEvents(currentDate)
        // 所有事件作为普通事件处理
        const eventGroups = organizeOverlappingEvents(dayEvents)
        
        result.push({
          date: currentDate.getDate(),
          dayName: weekDays.value[i],
          isToday: isSameDay(currentDate, new Date()),
          fullDate: currentDate,
          events: dayEvents,
          allDayEvents: [], // 保留空数组以兼容现有代码
          eventGroups: eventGroups
        })
      }
      
      return result
    })
    
    // 日视图事件
    const dayEvents = computed(() => {
      return getDayEvents(currentDate.value)
    })
    
    // 日视图全天事件 - 保留空数组以兼容现有代码
    const allDayEvents = computed(() => {
      return []
    })
    
    // 日视图普通事件分组 - 所有事件作为普通事件处理
    const dayEventGroups = computed(() => {
      return organizeOverlappingEvents(dayEvents.value)
    })
    
    // 组织重叠事件为不同分组
    const organizeOverlappingEvents = (events) => {
      if (!events.length) return [[]]
      
      // 按开始时间排序
      const sortedEvents = [...events].sort((a, b) => a.start.getTime() - b.start.getTime())
      
      const groups = []
      
      sortedEvents.forEach(event => {
        // 查找可以放置的组
        let placed = false
        
        for (let i = 0; i < groups.length; i++) {
          const group = groups[i]
          const lastEvent = group[group.length - 1]
          
          // 检查当前事件是否与组中最后一个事件不重叠
          if (lastEvent && event.start.getTime() >= lastEvent.end.getTime()) {
            group.push(event)
            placed = true
            break
          }
        }
        
        // 如果没有找到合适的组，创建新组
        if (!placed) {
          groups.push([event])
        }
      })
      
      return groups.length ? groups : [[]]
    }
    
    // 为"查看更多"弹窗创建一个响应式的事件列表
    const allEventsForDialog = computed(() => {
      if (!allEventsDialog.value.date) {
        return [];
      }
      return events.value
        .filter(event => isSameDay(new Date(event.start), allEventsDialog.value.date))
        .sort((a,b) => a.start - b.start);
    });
    
    // 加载状态
    const isLoading = ref(false)
    
    // 记录最后一次请求状态
    const lastRequestTime = ref(0)
    const retryCount = ref(0)
    const maxRetries = 3
    
    // 根据视图类型加载事件，增强版带错误处理和重试
    const loadEvents = async () => {
      if (!isComponentMounted.value) return
      
      // 防止短时间内多次调用
      const currentTime = Date.now()
      if (currentTime - lastRequestTime.value < 300) {
        console.log('请求频率过高，跳过此次加载')
        return
      }
      
      lastRequestTime.value = currentTime
      isLoading.value = true
      console.log('正在加载日程数据...')
      
      try {
        if (calendarView.value === 'month') {
          await loadMonthlyEvents()
        } else if (calendarView.value === 'week') {
          await loadWeeklyEvents()
        } else if (calendarView.value === 'day') {
          await loadDailyEvents()
        }
        // 成功后重置重试计数
        retryCount.value = 0
      } catch (err) {
        console.error('加载日程失败:', err)
        
        // 如果失败且没有超过最大重试次数，尝试重试
        if (retryCount.value < maxRetries) {
          retryCount.value++
          console.log(`正在重试加载日程 (${retryCount.value}/${maxRetries})...`)
          // 稍微延迟后重试
          setTimeout(loadEvents, 500)
        } else {
          ElMessage.error('加载日程失败，请刷新页面重试')
          retryCount.value = 0
        }
      } finally {
        isLoading.value = false
      }
    }
    
    // 加载月视图数据
    const loadMonthlyEvents = async () => {
        const year = currentDate.value.getFullYear()
      const month = currentDate.value.getMonth() + 1
      console.log(`正在加载${year}年${month}月的日程数据...`)
        
      try {
        const response = await getMonthlyEvents(year, month)
        
        if (response && (response.success || response.data)) {
          const eventData = response.data || []
          events.value = parseEventsData(eventData)
          console.log(`成功加载${events.value.length}个月视图日程`)
          return response
        } else {
          throw new Error('返回数据格式不正确')
        }
      } catch (error) {
        console.error('加载月视图日程失败:', error)
        throw error // 继续抛出错误以便外部捕获
      }
    }
    
    // 加载周视图数据
    const loadWeeklyEvents = async () => {
        const date = formatDateString(currentDate.value)
      console.log(`正在加载${date}所在周的日程数据...`)
      
      try {
        const response = await getWeeklyEvents(date)
        
        if (response && (response.success || response.data)) {
          const eventData = response.data || []
          events.value = parseEventsData(eventData)
          console.log(`成功加载${events.value.length}个周视图日程`)
          return response
        } else {
          throw new Error('返回数据格式不正确')
        }
      } catch (error) {
        console.error('加载周视图日程失败:', error)
        throw error // 继续抛出错误以便外部捕获
      }
    }
    
    // 加载日视图数据
    const loadDailyEvents = async () => {
        const date = formatDateString(currentDate.value)
      console.log(`正在加载${date}的日程数据...`)
      
      try {
        const response = await getDailyEvents(date)
        
        if (response && (response.success || response.data)) {
          const eventData = response.data || []
          events.value = parseEventsData(eventData)
          console.log(`成功加载${events.value.length}个日视图日程`)
          return response
        } else {
          throw new Error('返回数据格式不正确')
        }
      } catch (error) {
        console.error('加载日视图日程失败:', error)
        throw error // 继续抛出错误以便外部捕获
      }
    }
    
    // 解析事件数据
    const parseEventsData = (data) => {
      return data.map(item => {
        // 直接使用原始时间字符串，避免时区转换
        return {
          id: item.id,
          title: item.title,
          start: new Date(item.start),
          end: new Date(item.end),
          location: item.location,
          type: item.type,
          reminder: item.reminder,
          description: item.description,
          creator: item.creator,
          creator_name: item.creator_name,
          participants: item.participants,
          participants_info: item.participants_info
        };
      });
    }
    
    // 格式化日期为字符串
    const formatDateString = (date) => {
      const year = date.getFullYear()
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      return `${year}-${month}-${day}`
    }
    
    // 日期选择
    const selectDay = (day) => {
      if (!day.isCurrentMonth) {
        if (day.date > 15) {
          // 前一个月
          prev()
        } else {
          // 后一个月
          next()
        }
      }
    }
    
    // 返回今天
    const today = () => {
      currentDate.value = new Date()
    }
    
    // 上一个时间单位
    const prev = () => {
      const date = new Date(currentDate.value)
      if (calendarView.value === 'month') {
        date.setMonth(date.getMonth() - 1)
      } else if (calendarView.value === 'week') {
        date.setDate(date.getDate() - 7)
      } else if (calendarView.value === 'day') {
        date.setDate(date.getDate() - 1)
      }
      currentDate.value = date
    }
    
    // 下一个时间单位
    const next = () => {
      const date = new Date(currentDate.value)
      if (calendarView.value === 'month') {
        date.setMonth(date.getMonth() + 1)
      } else if (calendarView.value === 'week') {
        date.setDate(date.getDate() + 7)
      } else if (calendarView.value === 'day') {
        date.setDate(date.getDate() + 1)
      }
      currentDate.value = date
    }
    
    // 显示添加日程对话框
    const showAddEventDialog = (event) => {
      // 阻止事件冒泡
      if (event) {
        event.preventDefault()
        event.stopPropagation()
      }
      
      console.log('打开新建日程对话框', new Date().toISOString())
      
      try {
        // 直接重置表单数据，无需等待nextTick
        const now = new Date()
        const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000)
        
        // 先设置对话框为true
        addEventDialogVisible.value = true
        
        // 创建新的事件对象
      newEvent.value = {
        title: '',
          start: formatDateForPicker(now),
          end: formatDateForPicker(oneHourLater),
        location: '',
        type: 'blue',
        reminder: '30min',
        description: ''
      }
        
        console.log('已打开对话框', addEventDialogVisible.value)
      } catch (error) {
        console.error('打开新建日程对话框失败:', error)
        
        // 当出现错误时，强制关闭再打开对话框
        addEventDialogVisible.value = false
        setTimeout(() => {
      addEventDialogVisible.value = true
          console.log('对话框重试打开')
        }, 100)
      }
    }
    
    // 添加日程
    const addEvent = async () => {
      console.log('提交日程表单数据:', newEvent.value)
      
      // 使用表单验证
      if (!addEventFormRef.value) {
        console.error('表单引用不存在')
        return
      }
      
      addEventFormRef.value.validate(async (valid) => {
        if (!valid) {
          ElMessage.error('请填写所有必填项')
          return
        }
        
        try {
          // 验证开始时间不晚于结束时间
          const startTime = new Date(newEvent.value.start).getTime()
          const endTime = new Date(newEvent.value.end).getTime()
          if (isNaN(startTime) || isNaN(endTime)) {
            // 如果日期转换失败，尝试修复
            console.error('日期转换失败，尝试修复', { 
              start: newEvent.value.start, 
              end: newEvent.value.end 
            })
            
            // 使用当前时间和一小时后作为默认值
            const now = new Date()
            const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000)
            newEvent.value.start = formatDateForPicker(now)
            newEvent.value.end = formatDateForPicker(oneHourLater)
            ElMessage.warning('日期格式有误，已重置为当前时间')
            return
          }
          
          if (startTime > endTime) {
            ElMessage.warning('结束时间不能早于开始时间')
            return
          }
          
          // 验证开始和结束日期是同一天
          const startDate = new Date(newEvent.value.start).toDateString()
          const endDate = new Date(newEvent.value.end).toDateString()
          if (startDate !== endDate) {
            ElMessage.warning('开始和结束时间必须在同一天')
            return
          }
          
          // 获取当前用户ID
          const userId = Number(localStorage.getItem('user_id') || 0)
          console.log('当前用户ID:', userId)
          
          // 创建要提交的日程数据
          const eventData = {
            title: newEvent.value.title.trim(),
            start: newEvent.value.start,
            end: newEvent.value.end,
            location: (newEvent.value.location || '').trim(),
            type: newEvent.value.type || 'blue',
            reminder: newEvent.value.reminder || '30min',
            description: (newEvent.value.description || '').trim(),
            participants: userId ? [userId] : [] // 确保把当前用户加入参与者
          }
          
          console.log('正在提交日程数据:', eventData)
          
          // 先关闭对话框，避免用户重复提交
          addEventDialogVisible.value = false
          ElMessage.info('正在创建日程...')
          
          const response = await createEvent(eventData)
          console.log('服务器响应:', response)
          
          if (response.success || (response.data && !response.message)) {
            ElMessage.success('日程添加成功')
            await loadEvents() // 重新加载事件
          } else {
            ElMessage.error(response.message || '日程添加失败')
            console.error('添加失败详情:', response)
          }
        } catch (error) {
          console.error('添加日程失败:', error)
          ElMessage.error('日程添加失败：' + (error.message || '未知错误'))
        }
      })
    }
    
    // 显示日程详情
    const showEventDetails = (event) => {
      selectedEvent.value = event
      eventDetailsDialogVisible.value = true
    }
    
    // 显示编辑日程对话框
    const showEditEventDialog = () => {
      editingEvent.value = {
        id: selectedEvent.value.id,
        title: selectedEvent.value.title,
        start: formatDateForPicker(selectedEvent.value.start),
        end: formatDateForPicker(selectedEvent.value.end),
        location: selectedEvent.value.location || '',
        type: selectedEvent.value.type,
        reminder: selectedEvent.value.reminder,
        description: selectedEvent.value.description || ''
      }
      
      eventDetailsDialogVisible.value = false
      editEventDialogVisible.value = true
    }
    
    // 保存编辑的日程
    const saveEditEvent = async () => {
      // 使用表单验证
      if (!editEventFormRef.value) {
        console.error('表单引用不存在')
        return
      }
      
      editEventFormRef.value.validate(async (valid) => {
        if (!valid) {
          ElMessage.error('请填写所有必填项')
          return
        }
        
        // 验证开始时间不晚于结束时间
        const startTime = new Date(editingEvent.value.start).getTime()
        const endTime = new Date(editingEvent.value.end).getTime()
        if (startTime > endTime) {
          ElMessage.warning('结束时间不能早于开始时间')
          return
        }
        
        // 验证开始和结束日期是同一天
        const startDate = new Date(editingEvent.value.start).toDateString()
        const endDate = new Date(editingEvent.value.end).toDateString()
        if (startDate !== endDate) {
          ElMessage.warning('开始和结束时间必须在同一天')
          return
        }
        
        try {
          // 获取当前用户ID
          const userId = Number(localStorage.getItem('user_id') || 0)
          
          // 直接使用表单填写的时间，不进行时区转换
          const eventData = {
            title: editingEvent.value.title,
            start: editingEvent.value.start,
            end: editingEvent.value.end,
            location: editingEvent.value.location,
            type: editingEvent.value.type,
            reminder: editingEvent.value.reminder,
            description: editingEvent.value.description,
            participants: userId ? [userId] : [] // 确保把当前用户加入参与者
          }
          
          console.log('更新日程数据:', eventData)
          const response = await updateEvent(editingEvent.value.id, eventData)
          
          if (response.success) {
            ElMessage.success('日程更新成功')
            editEventDialogVisible.value = false
            loadEvents() // 重新加载事件
          } else {
            ElMessage.error(response.message || '日程更新失败')
          }
        } catch (error) {
          console.error('更新日程失败:', error)
          ElMessage.error('日程更新失败')
        }
      })
    }
    
    // 删除日程
    const deleteEvent = async () => {
      if (!selectedEvent.value.id || isNaN(selectedEvent.value.id)) {
        ElMessage.error('日程ID无效，无法删除');
        return;
      }
      console.log('尝试删除日程，id=', selectedEvent.value.id);
      try {
        await ElMessageBox.confirm('确定要删除该日程吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        const response = await deleteCalendarEventApi(selectedEvent.value.id)
        
        // 检查HTTP状态码是否为204，或者响应数据是否表示成功
        if (response.status === 204 || response.data?.success) {
          ElMessage.success('日程删除成功')
          eventDetailsDialogVisible.value = false
          loadEvents() // 重新加载事件
        } else {
          ElMessage.error(response.data?.message || '日程删除失败')
          console.error('删除失败详细信息:', response.data)
        }
      } catch (error) {
        if (error !== 'cancel') {
          // Axios错误对象通常在error.response中包含响应信息
          const errorMsg = error.response?.data?.message || error.message || '未知错误';
          console.error('删除日程失败:', error.response || error)
          ElMessage.error('日程删除失败: ' + errorMsg);
        }
      }
    }
    
    // 获取指定日期的事件
    const getDayEvents = (date) => {
      return events.value.filter(event => isSameDay(new Date(event.start), date))
    }
    
    // 判断两个日期是否是同一天
    const isSameDay = (date1, date2) => {
      return date1.getFullYear() === date2.getFullYear() &&
             date1.getMonth() === date2.getMonth() &&
             date1.getDate() === date2.getDate()
    }
    
    // 获取月份的第一天
    const getFirstDayOfMonth = (date) => {
      return new Date(date.getFullYear(), date.getMonth(), 1)
    }
    
    // 获取月份的天数
    const getDaysInMonth = (date) => {
      return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
    }
    
    // 计算事件在时间轴上的位置
    const calcEventTop = (event) => {
      if (!event || !event.start) return 0
      try {
        const hours = event.start.getHours()
        const minutes = event.start.getMinutes()
        // 每小时60px高度，每15分钟15px
        return (hours * 60 + minutes) / 15 * 15
      } catch (error) {
        console.error('计算事件位置错误:', error)
        return 0
      }
    }
    
    // 计算事件的高度
    const calcEventHeight = (event) => {
      if (!event || !event.start || !event.end) return 60 // 默认高度1小时
      try {
        const startTime = event.start.getTime()
        const endTime = event.end.getTime()
        const duration = (endTime - startTime) / (1000 * 60) // 分钟数
        
        // 最小高度30px (30分钟)
        return Math.max(duration / 15 * 15, 30)
      } catch (error) {
        console.error('计算事件高度错误:', error)
        return 60
      }
    }
    
    // 格式化事件时间
    const formatEventTime = (event) => {
      const start = event.start
      const end = event.end
      
      return `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')} - ${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`
    }
    
    // 格式化事件日期时间
    const formatEventDateTime = (event) => {
      if (!event.start || !event.end) return ''
      
      // 使用直接获取年月日时分的方式，避免时区转换问题
      const formatDateTime = (date) => {
        const year = date.getFullYear()
        const month = date.getMonth() + 1
        const day = date.getDate()
        const hours = date.getHours().toString().padStart(2, '0')
        const minutes = date.getMinutes().toString().padStart(2, '0')
        
        return `${year}年${month}月${day}日 ${hours}:${minutes}`
      }
      
      return `${formatDateTime(event.start)} - ${formatDateTime(event.end)}`
    }
    
    // 格式化提醒时间
    const formatReminder = (reminder) => {
      switch (reminder) {
        case 'none':
          return '不提醒'
        case '10min':
          return '10分钟前'
        case '30min':
          return '30分钟前'
        case '1hour':
          return '1小时前'
        case '1day':
          return '1天前'
        default:
          return '未设置'
      }
    }
    
    // 为日期选择器格式化日期
    const formatDateForPicker = (date) => {
      if (!date) return '';
      
      try {
        // 确保使用有效的Date对象
        let dateObj;
        if (date instanceof Date) {
          if (isNaN(date.getTime())) {
            console.error('无效日期对象', date);
            dateObj = new Date(); // 使用当前时间作为回退
          } else {
            dateObj = date;
          }
        } else {
          // 尝试解析字符串日期
          dateObj = new Date(date);
          if (isNaN(dateObj.getTime())) {
            console.error('无效日期字符串', date);
            dateObj = new Date(); // 使用当前时间作为回退
          }
        }
      
      // 使用直接获取年月日时分的方式，不涉及时区转换
      const year = dateObj.getFullYear();
      const month = (dateObj.getMonth() + 1).toString().padStart(2, '0');
      const day = dateObj.getDate().toString().padStart(2, '0');
      const hours = dateObj.getHours().toString().padStart(2, '0');
      const minutes = dateObj.getMinutes().toString().padStart(2, '0');
      
        const formatted = `${year}-${month}-${day} ${hours}:${minutes}`;
        console.log(`格式化日期: ${dateObj} => ${formatted}`);
        return formatted;
      } catch (error) {
        console.error('日期格式化错误:', error);
        // 返回当前时间作为回退选项
        const now = new Date();
        return `${now.getFullYear()}-${(now.getMonth() + 1).toString().padStart(2, '0')}-${now.getDate().toString().padStart(2, '0')} ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      }
    }
    
    // 处理开始时间变化，自动设置结束时间为1小时后
    const handleStartTimeChange = (event) => {
      if (!event.start) return
      
      try {
        // 解析开始时间
        const startTime = new Date(event.start)
        
        // 计算开始时间1小时后的时间
        const endTime = new Date(startTime.getTime() + 60 * 60 * 1000)
        
        // 如果结束时间未设置，或结束时间早于开始时间，或结束时间不在同一天
        // 则自动设置结束时间
        if (!event.end || 
            new Date(event.end) < startTime || 
            new Date(event.end).toDateString() !== startTime.toDateString()) {
          event.end = formatDateForPicker(endTime)
        }
      } catch (error) {
        console.error('处理开始时间变化错误:', error)
      }
    }
    
    // 日程类型颜色
    const eventTypeColor = (type) => {
      const map = {
        blue: '#409EFF',
        orange: '#E6A23C',
        green: '#67C23A',
        red: '#F56C6C',
        purple: '#909399',
        default: '#606266'
      }
      return map[type] || map.default
    }
    
    // 日程预览浮层
    const eventPreview = ref({ visible: false, event: {}, style: {} })
    const showEventPreview = (event, evt) => {
      eventPreview.value = {
        visible: true,
        event,
        style: {
          position: 'fixed',
          left: evt.clientX + 10 + 'px',
          top: evt.clientY + 10 + 'px',
          zIndex: 9999
        }
      }
    }
    const hideEventPreview = () => {
      eventPreview.value.visible = false
    }
    
    // 全部日程弹窗
    const allEventsDialog = ref({ visible: false, date: null, title: '' })
    const showAllEvents = (day) => {
      // 构造当天的完整日期对象
      const year = currentDate.value.getFullYear();
      let month = currentDate.value.getMonth();
      if (!day.isCurrentMonth) {
        month = day.date > 15 ? month - 1 : month + 1;
      }
      const fullDate = new Date(year, month, day.date);

      allEventsDialog.value = {
        visible: true,
        date: fullDate,
        title: `${fullDate.getFullYear()}年${fullDate.getMonth() + 1}月${day.date}日全部日程`
      }
    }
    
    // 拖拽相关状态
    const draggedEvent = ref(null)
    const resizingEvent = ref(null)
    const initialMouseY = ref(0)
    const initialEventHeight = ref(0)
    
    // 开始拖拽
    const dragStart = (e, event) => {
      draggedEvent.value = event
      // 在拖拽图像上显示事件标题
      const dragImage = document.createElement('div')
      dragImage.textContent = event.title
      dragImage.className = 'drag-image'
      document.body.appendChild(dragImage)
      e.dataTransfer.setDragImage(dragImage, 0, 0)
      
      // 记录拖拽数据
      e.dataTransfer.setData('text/plain', JSON.stringify({
        id: event.id,
        startTime: event.start.getTime(),
        endTime: event.end.getTime()
      }))
      
      // 添加拖拽效果
      setTimeout(() => {
        document.querySelectorAll('.week-day-events, .day-events-container').forEach(container => {
          container.addEventListener('dragover', dragOver)
          container.addEventListener('drop', drop)
        })
        document.body.removeChild(dragImage)
      }, 0)
    }
    
    // 拖拽经过
    const dragOver = (e) => {
      e.preventDefault()
      if (!draggedEvent.value) return
      
      // 显示放置位置预览
      const container = e.currentTarget
      const containerRect = container.getBoundingClientRect()
      const offsetY = e.clientY - containerRect.top
      
      // 计算新时间（按15分钟对齐）
      const quarterHours = Math.floor(offsetY / 15)
      const hours = Math.floor(quarterHours / 4)
      const minutes = (quarterHours % 4) * 15
      
      // 更新预览位置
      const previewElement = document.querySelector('.drag-preview') || document.createElement('div')
      if (!previewElement.classList.contains('drag-preview')) {
        previewElement.className = 'drag-preview'
        container.appendChild(previewElement)
      }
      
      // 设置预览元素样式
      previewElement.style.top = (quarterHours * 15) + 'px'
      previewElement.style.height = calcEventHeight(draggedEvent.value) + 'px'
      previewElement.innerHTML = `${hours}:${minutes.toString().padStart(2, '0')}`
    }
    
    // 放置拖拽
    const drop = async (e) => {
      e.preventDefault()
      if (!draggedEvent.value) return
      
      // 移除预览元素
      document.querySelectorAll('.drag-preview').forEach(el => el.remove())
      
      // 计算新的开始时间
      const container = e.currentTarget
      const containerRect = container.getBoundingClientRect()
      const offsetY = e.clientY - containerRect.top
      
      // 计算新时间（按15分钟对齐）
      const quarterHours = Math.floor(offsetY / 15)
      const hours = Math.floor(quarterHours / 4)
      const minutes = (quarterHours % 4) * 15
      
      // 创建新的开始时间
      const newStartDate = new Date(draggedEvent.value.start)
      newStartDate.setHours(hours, minutes, 0, 0)
      
      // 计算时间差
      const timeDiff = newStartDate.getTime() - draggedEvent.value.start.getTime()
      
      // 创建新的结束时间（保持持续时间不变）
      const newEndDate = new Date(draggedEvent.value.end.getTime() + timeDiff)
      
      // 更新事件
      try {
        const eventData = {
          title: draggedEvent.value.title,
          start: formatDateForPicker(newStartDate),
          end: formatDateForPicker(newEndDate),
          location: draggedEvent.value.location,
          type: draggedEvent.value.type,
          reminder: draggedEvent.value.reminder,
          description: draggedEvent.value.description,
          participants: draggedEvent.value.participants || []
        }
        
        const response = await updateEvent(draggedEvent.value.id, eventData)
        
        if (response.success) {
          ElMessage.success('日程时间已更新')
          loadEvents() // 重新加载事件
        } else {
          ElMessage.error(response.message || '更新日程时间失败')
        }
      } catch (error) {
        console.error('更新日程失败:', error)
        ElMessage.error('更新日程时间失败')
      }
    }
    
    // 结束拖拽
    const dragEnd = () => {
      draggedEvent.value = null
      document.querySelectorAll('.week-day-events, .day-events-container').forEach(container => {
        container.removeEventListener('dragover', dragOver)
        container.removeEventListener('drop', drop)
      })
      document.querySelectorAll('.drag-preview').forEach(el => el.remove())
    }
    
    // 开始调整大小
    const startResize = (e, event) => {
      e.stopPropagation()
      resizingEvent.value = event
      initialMouseY.value = e.clientY
      initialEventHeight.value = calcEventHeight(event)
      
      document.addEventListener('mousemove', handleResize)
      document.addEventListener('mouseup', endResize)
    }
    
    // 处理调整大小
    const handleResize = (e) => {
      if (!resizingEvent.value) return
      
      const deltaY = e.clientY - initialMouseY.value
      const newHeight = Math.max(30, initialEventHeight.value + deltaY)
      
      // 计算新的持续时间（分钟）
      const durationMinutes = Math.floor(newHeight / 15) * 15
      
      // 计算新的结束时间
      const newEndTime = new Date(resizingEvent.value.start.getTime() + durationMinutes * 60 * 1000)
      
      // 更新预览
      const eventElement = e.target.closest('.week-event, .day-event')
      if (eventElement) {
        eventElement.style.height = newHeight + 'px'
        
        // 更新时间显示
        const timeElement = eventElement.querySelector('.week-event-time, .day-event-time')
        if (timeElement) {
          const startTime = `${resizingEvent.value.start.getHours().toString().padStart(2, '0')}:${resizingEvent.value.start.getMinutes().toString().padStart(2, '0')}`
          const endTime = `${newEndTime.getHours().toString().padStart(2, '0')}:${newEndTime.getMinutes().toString().padStart(2, '0')}`
          timeElement.textContent = `${startTime} - ${endTime}`
        }
      }
    }
    
    // 结束调整大小
    const endResize = async (e) => {
      if (!resizingEvent.value) return
      
      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', endResize)
      
      const deltaY = e.clientY - initialMouseY.value
      const newHeight = Math.max(30, initialEventHeight.value + deltaY)
      
      // 计算新的持续时间（分钟）
      const durationMinutes = Math.floor(newHeight / 15) * 15
      
      // 计算新的结束时间
      const newEndTime = new Date(resizingEvent.value.start.getTime() + durationMinutes * 60 * 1000)
      
      // 更新事件
      try {
        const eventData = {
          title: resizingEvent.value.title,
          start: formatDateForPicker(resizingEvent.value.start),
          end: formatDateForPicker(newEndTime),
          location: resizingEvent.value.location,
          type: resizingEvent.value.type,
          reminder: resizingEvent.value.reminder,
          description: resizingEvent.value.description,
          participants: resizingEvent.value.participants || []
        }
        
        const response = await updateEvent(resizingEvent.value.id, eventData)
        
        if (response.success) {
          ElMessage.success('日程时长已更新')
          loadEvents() // 重新加载事件
        } else {
          ElMessage.error(response.message || '更新日程时长失败')
        }
      } catch (error) {
        console.error('更新日程失败:', error)
        ElMessage.error('更新日程时长失败')
      }
      
      resizingEvent.value = null
    }
    
    // 组件是否已挂载标志
    const isComponentMounted = ref(false)
    
    // 内部刷新标识
    const internalRefreshKey = ref(Date.now());
    
    // 添加一个强制刷新函数
    const forceRefresh = async () => {
      console.log('强制刷新日历组件');
      
      // 更新内部刷新标识，触发视图更新
      internalRefreshKey.value = Date.now();
      
      // 第一步：清除所有可能的DOM副作用
      try {
        // 清除所有浮层和遮罩
        const overlays = document.querySelectorAll('.el-overlay, .el-overlay-dialog, .el-overlay-message-box, .el-popup-parent--hidden');
        overlays.forEach(el => {
          if (el && el.parentNode) {
            try {
              el.parentNode.removeChild(el);
            } catch (e) {
              console.error('清理浮层元素失败:', e);
            }
          }
        });
        
        // 恢复body样式
        if (document && document.body) {
          document.body.style.overflow = '';
          document.body.classList.remove('el-popup-parent--hidden');
          document.body.style.pointerEvents = 'auto';
        }
        
        // 处理所有可能的下拉菜单
        const dropdowns = document.querySelectorAll('.el-dropdown-menu, .el-select-dropdown');
        dropdowns.forEach(el => {
          if (el && el.parentNode) {
            try {
              el.parentNode.removeChild(el);
            } catch (e) {
              console.error('清理下拉菜单失败:', e);
            }
          }
        });
      } catch (error) {
        console.error('清理DOM元素失败:', error);
      }
      
      // 第二步：重新绑定所有事件
      await nextTick();
      try {
        // 确保所有按钮和交互元素可点击
        const interactiveElements = document.querySelectorAll(
          '.calendar-container button, ' +
          '.el-dropdown-menu__item, ' +
          '.event-item, ' +
          '.calendar-day, ' +
          '.el-dropdown, ' +
          '.week-event, ' +
          '.day-event'
        );
        
        interactiveElements.forEach(el => {
          if (el) {
            // 恢复所有交互元素的点击能力
            el.style.pointerEvents = 'auto';
            if (el.hasAttribute('disabled') && !el.classList.contains('is-disabled')) {
              el.removeAttribute('disabled');
            }
            
            // 重置样式
            try {
              el.style.opacity = '1';
              el.style.visibility = 'visible';
              el.style.display = '';
            } catch (e) {
              console.error('重置元素样式失败:', e);
            }
          }
        });
        
        // 特别处理添加日程按钮
        const addButton = document.querySelector('.action-controls .el-button');
        if (addButton) {
          console.log('重新绑定添加按钮事件');
          addButton.addEventListener('click', (e) => {
            e.stopPropagation();
            showAddEventDialog(e);
          });
        }
      } catch (error) {
        console.error('重置交互元素失败:', error);
      }
      
      // 第三步：强制重新获取数据
      try {
        console.log('重新加载日历数据...');
        
        // 调用事件加载函数
        await loadEvents().catch(err => {
          console.error('强制刷新日历数据失败:', err);
          return [];
        });
        
        console.log('日历数据刷新完成');
      } catch (error) {
        console.error('强制刷新数据失败:', error);
      }
    };
    
    // 监听路由变化，确保每次进入页面都刷新
    watch(() => route.fullPath, (newPath) => {
      if (newPath === '/calendar') {
        console.log('检测到路由变化到日历页面，强制刷新');
        // 延迟执行，确保DOM已经渲染
        setTimeout(() => {
          forceRefresh();
        }, 100);
      }
    });
    
    // 路由变化时重新加载数据
    watch(() => calendarView.value, (newVal) => {
      console.log('日历视图变更为:', newVal)
      nextTick(() => loadEvents())
    })
    
    // 日期变化时重新加载数据
    watch(() => currentDate.value, (newVal) => {
      console.log('当前日期变更为:', newVal.toLocaleDateString())
      nextTick(() => loadEvents())
    })
    
    const { proxy } = getCurrentInstance();
    const emitter = proxy.emitter;
    
    onMounted(() => {
      console.log('Calendar组件挂载');
      isComponentMounted.value = true
      
      // 延迟一点时间再初始化，确保DOM已完全准备好
      setTimeout(() => {
        loadEvents()
        console.log('延迟初始化完成')
      }, 50)
    
      // 监听元素可见性变化
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            console.log('Calendar组件进入可视区域，检查初始化状态')
            // 如果变成可见，重新检查初始化状态
            if (events.value.length === 0) {
              console.log('日程数据为空，尝试重新加载')
              loadEvents()
            }
          }
        })
    })
    
      // 监控组件元素
      const calendarEl = document.querySelector('.calendar-container')
      if (calendarEl) {
        observer.observe(calendarEl)
      }
      
      // 临时解决方案：确保添加按钮事件正确绑定
      const addButton = document.querySelector('.action-controls .el-button')
      if (addButton) {
        console.log('找到添加按钮，增强点击处理')
        addButton.addEventListener('click', (e) => {
          e.stopPropagation()
          showAddEventDialog(e)
        })
      }

      // 添加事件监听器
      console.log('日历组件已挂载，开始监听刷新事件');
      emitter.on('refreshCalendar', loadEvents);
    })

    onUnmounted(() => {
      // 移除事件监听器
      console.log('日历组件将卸载，移除刷新事件监听器');
      emitter.off('refreshCalendar', loadEvents);
    });
    
    // 添加keep-alive激活事件处理
    onActivated(() => {
      console.log('Calendar组件被激活');
      // 组件激活时强制刷新
      forceRefresh();
    });
    
    onBeforeUnmount(() => {
      // 清理工作
    })
    
    return {
      calendarView,
      currentDate,
      currentDateLabel,
      weekDays,
      days,
      weekDates,
      dayEvents,
      addEventDialogVisible,
      eventDetailsDialogVisible,
      editEventDialogVisible,
      newEvent,
      selectedEvent,
      editingEvent,
      addEventFormRef,
      editEventFormRef,
      rules,
      today,
      prev,
      next,
      selectDay,
      showAddEventDialog,
      addEvent,
      showEventDetails,
      showEditEventDialog,
      saveEditEvent,
      deleteEvent,
      calcEventTop,
      calcEventHeight,
      formatEventTime,
      formatEventDateTime,
      formatReminder,
      // Element Plus 图标
      ArrowLeft,
      ArrowRight,
      Plus,
      handleStartTimeChange,
      eventTypeColor,
      eventPreview,
      showEventPreview,
      hideEventPreview,
      allEventsDialog,
      showAllEvents,
      allDayEvents,
      dayEventGroups,
      organizeOverlappingEvents,
      dragStart,
      dragEnd,
      startResize,
      allEventsForDialog,
      internalRefreshKey,
      forceRefresh,
    }
  }
}
</script>

<style scoped>
.calendar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
}

.date-controls {
  display: flex;
  align-items: center;
}

.date-nav {
  display: flex;
  align-items: center;
  margin-left: 15px;
}

.current-date {
  margin: 0 15px;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color);
}

.calendar-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background-color: var(--bg-color-secondary);
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.weekday {
  text-align: center;
  font-weight: 500;
  color: var(--text-color-secondary);
}

.calendar-days {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(6, 1fr);
}

.calendar-day {
  border-right: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  padding: 5px;
  overflow: hidden;
  background-color: var(--bg-color);
}

.calendar-day:nth-child(7n) {
  border-right: none;
}

.calendar-day.today {
  background-color: var(--bg-color-tertiary);
}

.calendar-day.other-month {
  opacity: 0.5;
}

.day-number {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 5px;
}

.calendar-day.today .day-number {
  color: var(--primary-color);
}

.event-container {
  font-size: 12px;
}

.event-item {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background-color 0.3s;
}

.more-events-indicator {
  font-size: 12px;
  text-align: center;
  margin-top: 4px;
  color: var(--el-color-primary);
  cursor: pointer;
  border-radius: 4px;
  padding: 2px 0;
  transition: all 0.2s ease-in-out;
}
.more-events-indicator:hover {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary-dark-2);
  font-weight: 500;
}

.event-color {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  display: inline-block;
}

/* 日程事件颜色 */
.event-blue {
  background-color: rgba(59, 130, 246, 0.15);
  color: var(--primary-color);
  border-left: 3px solid var(--primary-color);
}

.event-orange {
  background-color: rgba(250, 140, 22, 0.15);
  color: #fa8c16;
  border-left: 3px solid #fa8c16;
}

.event-green {
  background-color: rgba(82, 196, 26, 0.15);
  color: var(--success-color);
  border-left: 3px solid var(--success-color);
}

.event-red {
  background-color: rgba(245, 34, 45, 0.15);
  color: var(--error-color);
  border-left: 3px solid var(--error-color);
}

.event-purple {
  background-color: rgba(114, 46, 209, 0.15);
  color: #722ed1;
  border-left: 3px solid #722ed1;
}

/* 周视图样式 */
.calendar-week {
  display: flex;
  flex-direction: column;
  height: 700px;
  border: 1px solid var(--border-color);
}

.week-header {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.week-time-col {
  width: 60px;
  border-right: 1px solid var(--border-color);
}

.week-day-col {
  flex: 1;
  text-align: center;
  padding: 10px;
  border-right: 1px solid var(--border-color);
  background-color: var(--bg-color);
}

.week-day-col:last-child {
  border-right: none;
}

.week-day-col.today {
  background-color: var(--bg-color-tertiary);
}

.week-day-name {
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 5px;
}

.week-day-date {
  color: var(--text-color-secondary);
}

.week-body {
  display: flex;
  flex: 1;
  overflow-y: auto;
  background-color: var(--bg-color);
}

.week-time-scale {
  width: 60px;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
}

.time-slot {
  height: 60px;
  padding: 2px 5px;
  font-size: 12px;
  text-align: right;
  color: var(--text-color-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.week-events-container {
  display: flex;
  flex: 1;
}

.week-day-events {
  flex: 1;
  position: relative;
  border-right: 1px solid var(--border-color);
  background-color: var(--bg-color);
}

.week-day-events:last-child {
  border-right: none;
}

.week-all-day-events {
  display: none;
}

.week-event-group {
  position: absolute;
  height: 100%;
  top: 0;
}

.week-event {
  position: absolute;
  width: 94%;
  left: 3%;
  border-radius: 4px;
  padding: 5px;
  font-size: 12px;
  overflow: hidden;
  cursor: pointer;
  z-index: 1;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.week-event:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.week-event-title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-left: 12px;
  margin-top: -12px;
}

.week-event-time {
  font-size: 11px;
  margin-top: 2px;
  color: rgba(0, 0, 0, 0.6);
}

.all-day-event-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-left: 4px;
}

/* 日视图样式 */
.calendar-day-view {
  display: flex;
  flex-direction: column;
  height: 700px;
  border: 1px solid var(--border-color);
}

.day-header {
  padding: 10px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-color-tertiary);
}

.day-date {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color);
}

.day-body {
  display: flex;
  flex: 1;
  overflow-y: auto;
  background-color: var(--bg-color);
}

.day-time-scale {
  width: 60px;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
}

.day-events-container {
  flex: 1;
  position: relative;
}

.day-all-day-events {
  display: none;
}

.day-event-group {
  position: absolute;
  height: 100%;
  top: 0;
}

.day-event {
  position: absolute;
  width: 94%;
  left: 3%;
  border-radius: 4px;
  padding: 8px;
  font-size: 13px;
  overflow: hidden;
  cursor: pointer;
  z-index: 1;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.day-event:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.day-event-title {
  font-weight: 500;
  margin-bottom: 5px;
  margin-left: 12px;
  margin-top: -12px;
}

.day-event-time {
  font-size: 12px;
  margin-bottom: 5px;
  color: rgba(0, 0, 0, 0.6);
}

.day-event-location {
  font-size: 12px;
  color: #409EFF;
}

/* 日程详情样式 */
.event-details {
  margin-top: 10px;
}

.event-detail-item {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}

.event-detail-item i {
  margin-right: 10px;
  font-size: 16px;
  color: var(--text-color-tertiary);
}

.event-description {
  white-space: pre-line;
}

/* 添加全局样式确保对话框在深色模式下正确显示 */
:deep(.calendar-dialog) {
  .el-dialog {
    background-color: var(--bg-color);
    
    .el-dialog__header {
      color: var(--text-color);
      background-color: var(--bg-color);
      border-bottom: 1px solid var(--border-color);
    }
    
    .el-dialog__body {
      color: var(--text-color);
      background-color: var(--bg-color);
    }
    
    .el-dialog__footer {
      background-color: var(--bg-color);
      border-top: 1px solid var(--border-color);
    }
  }
  
  .el-form-item__label {
    color: var(--text-color);
  }
  
  .el-input__wrapper {
    background-color: var(--bg-color-tertiary) !important;
    box-shadow: 0 0 0 1px var(--border-color) inset !important;
  }
  
  .el-input__inner {
    background-color: transparent !important;
    color: var(--text-color) !important;
  }
  
  .el-textarea__wrapper {
    background-color: var(--bg-color-tertiary) !important;
    box-shadow: 0 0 0 1px var(--border-color) inset !important;
  }
  
  .el-textarea__inner {
    background-color: transparent !important;
    color: var(--text-color) !important;
  }
  
  .el-select-dropdown {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    
    .el-select-dropdown__item {
      color: var(--text-color) !important;
      
      &.hover, &:hover {
        background-color: var(--hover-color) !important;
      }
      
      &.selected {
        color: var(--primary-color) !important;
        background-color: var(--hover-color) !important;
      }
    }
  }
  
  /* 日期选择器深色模式样式修复 */
  .el-date-picker, .el-date-range-picker {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    
    .el-picker-panel__content, .el-date-table {
      background-color: var(--bg-color-secondary) !important;
      color: var(--text-color) !important;
    }
    
    .el-date-range-picker__time-header,
    .el-date-range-picker__header,
    .el-date-picker__header,
    .el-picker-panel__footer {
      background-color: var(--bg-color-secondary) !important;
      color: var(--text-color) !important;
      border-color: var(--border-color) !important;
    }
    
    .el-date-table th {
      color: var(--text-color-secondary) !important;
      border-bottom-color: var(--border-color) !important;
    }
    
    .el-date-table td {
      color: var(--text-color) !important;
    }
    
    .el-date-table td.available:hover {
      color: var(--primary-color) !important;
    }
    
    .el-date-table td.current:not(.disabled) {
      color: #fff !important;
      background-color: var(--primary-color) !important;
    }
    
    .el-date-table td.today {
      color: var(--primary-color) !important;
    }
    
    .el-date-table td.prev-month,
    .el-date-table td.next-month {
      color: var(--text-color-tertiary) !important;
    }
    
    .el-time-panel {
      background-color: var(--bg-color) !important;
      border-color: var(--border-color) !important;
      
      .el-time-panel__content::before,
      .el-time-panel__content::after {
        background-color: var(--border-color) !important;
      }
      
      .el-time-panel__footer {
        border-top-color: var(--border-color) !important;
      }
      
      .el-time-spinner__item {
        color: var(--text-color) !important;
      }
      
      .el-time-spinner__item.active:not(.disabled) {
        color: var(--primary-color) !important;
        font-weight: bold;
      }
    }
    
    .el-picker-panel__icon-btn {
      color: var(--text-color) !important;
    }
    
    .el-date-picker__header-label {
      color: var(--text-color) !important;
    }
  }
}

/* 全局选择器修复，确保下拉菜单在深色模式下显示正确 */
:deep(.el-select-dropdown) {
  background-color: var(--bg-color-secondary) !important;
  border-color: var(--border-color) !important;
  
  .el-select-dropdown__item {
    color: var(--text-color) !important;
    
    &.hover, &:hover {
      background-color: var(--hover-color) !important;
    }
    
    &.selected {
      color: var(--primary-color) !important;
      background-color: var(--hover-color) !important;
    }
  }
}

:deep(.el-popper) {
  background-color: var(--bg-color-secondary) !important;
  border-color: var(--border-color) !important;
  
  .el-popper__arrow::before {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
  }
  
  .el-select-dropdown__item {
    color: var(--text-color) !important;
    
    &.hover, &:hover {
      background-color: var(--hover-color) !important;
    }
    
    &.selected {
      color: var(--primary-color) !important;
      background-color: var(--hover-color) !important;
    }
  }
}

/* 覆盖Element Plus的全局弹出层样式 */
body.is-dark {
  --el-select-dropdown-bg-color: var(--bg-color-secondary) !important;
  --el-bg-color: var(--bg-color-secondary) !important;
  --el-bg-color-overlay: var(--bg-color-secondary) !important;
  --el-text-color-primary: var(--text-color) !important;
  --el-border-color: var(--border-color) !important;
  --el-border-color-lighter: var(--border-color) !important;
  
  .el-popper {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    
    .el-popper__arrow::before {
      background-color: var(--bg-color-secondary) !important;
      border-color: var(--border-color) !important;
    }
  }
  
  .el-select-dropdown {
    background-color: var(--bg-color-secondary) !important;
    
    .el-select-dropdown__item {
      color: var(--text-color) !important;
      
      &.hover, &:hover {
        background-color: var(--hover-color) !important;
      }
      
      &.selected {
        color: var(--primary-color) !important;
        background-color: var(--hover-color) !important;
      }
    }
  }
}

.event-preview-pop {
  min-width: 180px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  border-radius: 4px;
  padding: 8px 12px;
  position: fixed;
  pointer-events: none;
  font-size: 13px;
  color: #333;
}

.event-preview-title {
  font-weight: bold;
  margin-bottom: 4px;
}

.event-preview-time {
  color: #888;
  font-size: 12px;
  margin-bottom: 2px;
}

.event-preview-location {
  color: #409EFF;
  font-size: 12px;
  margin-bottom: 2px;
}

.event-preview-desc {
  color: #666;
  font-size: 12px;
}

.all-event-title {
  font-weight: bold;
  margin-bottom: 2px;
}

.all-event-time {
  color: #888;
  font-size: 12px;
}

.all-event-location {
  color: #409EFF;
  font-size: 12px;
}

.all-event-desc {
  color: #666;
  font-size: 12px;
}

/* 拖拽预览元素 */
.drag-preview {
  position: absolute;
  background-color: rgba(64, 158, 255, 0.3);
  border: 2px dashed #409EFF;
  border-radius: 4px;
  left: 10%;
  width: 80%;
  z-index: 100;
  color: #409EFF;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drag-image {
  position: absolute;
  top: -1000px;
  left: -1000px;
  width: 100px;
  height: 30px;
  background: #409EFF;
  color: white;
  padding: 5px;
  border-radius: 3px;
  font-size: 12px;
  opacity: 0.8;
}

.resize-handle {
  position: absolute;
  width: 100%;
  height: 6px;
  bottom: 0;
  left: 0;
  cursor: ns-resize;
  opacity: 0;
  background-color: rgba(0, 0, 0, 0.1);
  transition: opacity 0.2s;
}

.week-event:hover .resize-handle,
.day-event:hover .resize-handle {
  opacity: 1;
}

.week-event.resizing,
.day-event.resizing {
  opacity: 0.7;
  z-index: 100;
}

/* 拖拽目标样式 */
.week-day-events.drag-over,
.day-events-container.drag-over {
  background-color: rgba(64, 158, 255, 0.05);
}

/* 移除当前时间线样式 */
.current-time-line,
.current-time-dot,
.current-time-line-inner,
.current-time-label {
  display: none !important;
}
</style>
<template>
  <div class="module-card modern-report">
    <div class="module-header">
      <h5 class="module-title">项目数据分析</h5>
      <div class="btn-group">
        <el-button size="small" plain type="primary" class="ai-report-btn" @click="downloadAiReport">
          <el-icon class="btn-icon"><MagicStick /></el-icon>
          导出AI分析报告
        </el-button>
      </div>
    </div>
    <div class="row mb-4">
      <div class="col-md-6">
        <div class="modern-card">
          <h6 class="text-primary">文档上传趋势</h6>
          <div class="chart-center-wrap">
            <div ref="docTrendChart" class="modern-echart" />
            <div v-if="!docTrendHasData" class="chart-empty">暂无数据</div>
          </div>
          <!-- 文档上传趋势AI分析 -->
          <div class="ai-analysis-section" v-if="docTrendHasData">
            <div class="ai-analysis-header" @click="toggleAnalysis('docTrend')">
              <el-icon><MagicStick /></el-icon>
              <span>AI分析</span>
              <el-icon class="toggle-icon" :class="{'is-active': showDocTrendAnalysis}">
                <ArrowDown />
              </el-icon>
            </div>
            <div class="ai-analysis-content" v-if="showDocTrendAnalysis">
              <div v-if="isLoadingAnalysis" class="analysis-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>AI分析中...</span>
              </div>
              <template v-else-if="chartAnalysis.doc_trend_analysis">
                <div class="analysis-section">
                  <h6>关键发现</h6>
                  <ul class="finding-list">
                    <li v-for="(finding, idx) in chartAnalysis.doc_trend_analysis.key_findings" :key="'finding-'+idx">
                      {{ finding }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>建议</h6>
                  <ul class="recommendation-list">
                    <li v-for="(rec, idx) in chartAnalysis.doc_trend_analysis.recommendations" :key="'rec-'+idx">
                      {{ rec }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>洞察</h6>
                  <p class="insights-text">{{ chartAnalysis.doc_trend_analysis.insights }}</p>
                </div>
              </template>
              <div v-else class="analysis-empty">
                <span>暂无分析数据</span>
                <el-button type="text" @click="loadChartAnalysis">点击生成分析</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="modern-card">
          <h6 class="text-primary">需求优先级分布</h6>
          <div class="chart-center-wrap">
            <div ref="reqChart" class="modern-echart" />
            <div v-if="!reqTotal" class="chart-empty">暂无数据</div>
          </div>
          <div class="modern-summary main-value" v-if="reqTotal">共 {{ reqTotal }} 个需求</div>
          <!-- 需求优先级分布AI分析 -->
          <div class="ai-analysis-section" v-if="reqTotal">
            <div class="ai-analysis-header" @click="toggleAnalysis('reqPriority')">
              <el-icon><MagicStick /></el-icon>
              <span>AI分析</span>
              <el-icon class="toggle-icon" :class="{'is-active': showReqPriorityAnalysis}">
                <ArrowDown />
              </el-icon>
            </div>
            <div class="ai-analysis-content" v-if="showReqPriorityAnalysis">
              <div v-if="isLoadingAnalysis" class="analysis-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>AI分析中...</span>
              </div>
              <template v-else-if="chartAnalysis.req_priority_analysis">
                <div class="analysis-section">
                  <h6>关键发现</h6>
                  <ul class="finding-list">
                    <li v-for="(finding, idx) in chartAnalysis.req_priority_analysis.key_findings" :key="'finding-'+idx">
                      {{ finding }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>建议</h6>
                  <ul class="recommendation-list">
                    <li v-for="(rec, idx) in chartAnalysis.req_priority_analysis.recommendations" :key="'rec-'+idx">
                      {{ rec }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>洞察</h6>
                  <p class="insights-text">{{ chartAnalysis.req_priority_analysis.insights }}</p>
                </div>
              </template>
              <div v-else class="analysis-empty">
                <span>暂无分析数据</span>
                <el-button type="text" @click="loadChartAnalysis">点击生成分析</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="row mb-4">
      <div class="col-md-6">
        <div class="modern-card">
          <h6 class="text-primary">需求完成率</h6>
          <div class="chart-center-wrap">
            <div ref="gaugeChart" class="modern-echart" />
            <div v-if="!reqTotal" class="chart-empty">暂无数据</div>
          </div>
          <!-- 需求完成率AI分析 -->
          <div class="ai-analysis-section" v-if="reqTotal">
            <div class="ai-analysis-header" @click="toggleAnalysis('reqCompletion')">
              <el-icon><MagicStick /></el-icon>
              <span>AI分析</span>
              <el-icon class="toggle-icon" :class="{'is-active': showReqCompletionAnalysis}">
                <ArrowDown />
              </el-icon>
            </div>
            <div class="ai-analysis-content" v-if="showReqCompletionAnalysis">
              <div v-if="isLoadingAnalysis" class="analysis-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>AI分析中...</span>
              </div>
              <template v-else-if="chartAnalysis.req_completion_analysis">
                <div class="analysis-section">
                  <h6>关键发现</h6>
                  <ul class="finding-list">
                    <li v-for="(finding, idx) in chartAnalysis.req_completion_analysis.key_findings" :key="'finding-'+idx">
                      {{ finding }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>建议</h6>
                  <ul class="recommendation-list">
                    <li v-for="(rec, idx) in chartAnalysis.req_completion_analysis.recommendations" :key="'rec-'+idx">
                      {{ rec }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>洞察</h6>
                  <p class="insights-text">{{ chartAnalysis.req_completion_analysis.insights }}</p>
                </div>
              </template>
              <div v-else class="analysis-empty">
                <span>暂无分析数据</span>
                <el-button type="text" @click="loadChartAnalysis">点击生成分析</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="modern-card">
          <h6 class="text-primary">任务完成趋势</h6>
          <div class="chart-center-wrap">
            <div ref="trendChart" class="modern-echart" />
            <div v-if="!trendHasData" class="chart-empty">暂无数据</div>
          </div>
          <div class="modern-summary main-value" v-if="taskTotal">共 {{ taskTotal }} 个任务</div>
          <!-- 任务完成趋势AI分析 -->
          <div class="ai-analysis-section" v-if="trendHasData || taskTotal > 0">
            <div class="ai-analysis-header" @click="toggleAnalysis('taskTrend')">
              <el-icon><MagicStick /></el-icon>
              <span>AI分析</span>
              <el-icon class="toggle-icon" :class="{'is-active': showTaskTrendAnalysis}">
                <ArrowDown />
              </el-icon>
            </div>
            <div class="ai-analysis-content" v-if="showTaskTrendAnalysis">
              <div v-if="isLoadingAnalysis" class="analysis-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>AI分析中...</span>
              </div>
              <template v-else-if="chartAnalysis.task_trend_analysis">
                <div class="analysis-section">
                  <h6>关键发现</h6>
                  <ul class="finding-list">
                    <li v-for="(finding, idx) in chartAnalysis.task_trend_analysis.key_findings" :key="'finding-'+idx">
                      {{ finding }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>建议</h6>
                  <ul class="recommendation-list">
                    <li v-for="(rec, idx) in chartAnalysis.task_trend_analysis.recommendations" :key="'rec-'+idx">
                      {{ rec }}
                    </li>
                  </ul>
                </div>
                <div class="analysis-section">
                  <h6>洞察</h6>
                  <p class="insights-text">{{ chartAnalysis.task_trend_analysis.insights }}</p>
                </div>
              </template>
              <div v-else class="analysis-empty">
                <span>暂无分析数据</span>
                <el-button type="text" @click="loadChartAnalysis">点击生成分析</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 导出报告对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="导出AI分析报告"
      width="500px"
      destroy-on-close
    >
      <div class="export-dialog-content">
        <div class="dialog-info-box">
          <p><el-icon><InfoFilled /></el-icon> 系统将自动整合所有图表及AI分析结果生成PDF报告。</p>
        </div>
        
        <div class="export-options">
          <h4>报告内容</h4>
          <el-checkbox-group v-model="exportOptions">
            <el-checkbox label="project_info">项目基本信息</el-checkbox>
            <el-checkbox label="tasks">任务分析</el-checkbox>
            <el-checkbox label="documents">文档分析</el-checkbox>
            <el-checkbox label="requirements">需求分析</el-checkbox>
            <el-checkbox label="ai_insights">AI综合结论</el-checkbox>
          </el-checkbox-group>
        </div>
        
        <div class="report-preview">
          <img src="@/assets/report-preview.svg" alt="报告预览" class="preview-img" />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showExportDialog = false">取消</el-button>
          <el-button type="primary" :loading="isExporting" @click="confirmExport">
            {{ isExporting ? '导出中...' : '开始导出' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { exportProjectAiReport, getProjectChartAnalysis } from '@/api/project'
import { ElMessage } from 'element-plus'
import { MagicStick, ArrowDown, Loading, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  project: Object,
  tasks: Array,
  documents: Array,
  requirements: Array
})

const theme = ref(document.documentElement.getAttribute('data-theme') || 'light');
const isDark = computed(() => theme.value === 'dark');

const textColor = computed(() => isDark.value ? 'rgba(255, 255, 255, 0.9)' : '#333');
const secondaryTextColor = computed(() => isDark.value ? 'rgba(255, 255, 255, 0.7)' : '#666');
const axisLabelColor = computed(() => isDark.value ? 'rgba(255, 255, 255, 0.5)' : '#888');
const chartTooltipBg = computed(() => isDark.value ? '#2c2c2c' : '#fff');
const chartTooltipBorder = computed(() => isDark.value ? '#555' : '#ccc');

watch(isDark, () => {
  // charts need re-rendering on theme change
  nextTick(() => {
    renderCharts();
  });
});

const docTrendChart = ref(null)
const reqChart = ref(null)
const gaugeChart = ref(null)
const trendChart = ref(null)

let docTrendChartInstance = null
let reqChartInstance = null
let gaugeChartInstance = null
let trendChartInstance = null

// 新增：标准化任务数据，兼容"已完成"状态和完成时间
const normalizedTasks = computed(() => {
  if (!Array.isArray(props.tasks)) return []
  return props.tasks.map(task => {
    let status = task.status
    if (status === '已完成') status = 'done'
    // 可扩展更多映射
    return {
      ...task,
      status,
      due_date: task.due_date || task.updated_at || task.update_time || task.end_time || new Date().toISOString()
    }
  })
})

// 统计数据摘要
const reqTotal = computed(() => props.requirements?.length || 0)
const taskTotal = computed(() => normalizedTasks.value.length || 0)

// 图表数据预处理
const docTrendHasData = computed(() => {
  if (!Array.isArray(props.documents) || !props.documents.length) return false
  return props.documents.some(doc => doc.uploaded_at || doc.created_at)
})

const trendHasData = computed(() => {
  if (!Array.isArray(normalizedTasks.value) || !normalizedTasks.value.length) return false
  return normalizedTasks.value.some(task => task.completed_at || task.finish_time || task.status === 'done')
})

// AI分析相关状态
const chartAnalysis = ref({})
const isLoadingAnalysis = ref(false)
const showDocTrendAnalysis = ref(true)
const showReqPriorityAnalysis = ref(true)
const showReqCompletionAnalysis = ref(true)
const showTaskTrendAnalysis = ref(true)

// 导出报告相关状态
const showExportDialog = ref(false)
const isExporting = ref(false)
const exportOptions = ref(['project_info', 'tasks', 'documents', 'requirements', 'ai_insights'])

// 切换分析部分的显示/隐藏
function toggleAnalysis(type) {
  if (type === 'docTrend') {
    showDocTrendAnalysis.value = !showDocTrendAnalysis.value
  } else if (type === 'reqPriority') {
    showReqPriorityAnalysis.value = !showReqPriorityAnalysis.value
  } else if (type === 'reqCompletion') {
    showReqCompletionAnalysis.value = !showReqCompletionAnalysis.value
  } else if (type === 'taskTrend') {
    showTaskTrendAnalysis.value = !showTaskTrendAnalysis.value
  }
}

// 加载图表AI分析
async function loadChartAnalysis() {
  if (!props.project?.id) return
  
  try {
    isLoadingAnalysis.value = true
    const response = await getProjectChartAnalysis(props.project.id)
    chartAnalysis.value = response.data
    console.log('AI分析结果:', chartAnalysis.value)
  } catch (error) {
    console.error('加载AI分析失败:', error)
    ElMessage.error('加载AI分析失败，请稍后重试')
  } finally {
    isLoadingAnalysis.value = false
  }
}

// 图表转换为base64
function chartToBase64(chartInstance) {
  if (!chartInstance) {
    console.warn('图表实例不存在，无法转换为Base64');
    return '';
  }
  try {
    // 确保图表已经渲染完成
    chartInstance.resize();
    // 设置较低的像素比以减小文件大小
    const base64Data = chartInstance.getDataURL({
      pixelRatio: 1.5,
      backgroundColor: isDark.value ? '#282c34' : '#fff'
    });
    
    // 验证Base64数据是否有效
    if (!base64Data || base64Data.length < 100) {
      console.warn('生成的Base64数据可能无效');
      return '';
    }
    
    console.log(`成功转换图表，数据长度: ${base64Data.length}`);
    return base64Data;
  } catch (e) {
    console.error('图表转换为Base64失败:', e);
    return '';
  }
}

// 打开导出对话框
function downloadAiReport() {
  // 检查是否有数据
  if (!props.project?.id) {
    ElMessage.warning('项目信息不完整，无法导出报告')
    return
  }
  
  // 首先加载AI分析数据
  if (Object.keys(chartAnalysis.value).length === 0) {
    loadChartAnalysis()
  }
  
  showExportDialog.value = true
  ElMessage.info('报告导出后将保存到您的下载目录')
}

// 确认导出报告
async function confirmExport() {
  if (!props.project?.id) {
    ElMessage.warning('项目信息不完整，无法导出报告');
    return;
  }
  
  try {
    isExporting.value = true;
    ElMessage.info('正在准备图表数据，请稍候...');
    
    // 确保图表已经完全渲染
    await nextTick();
    
    // 强制重绘图表以确保数据正确
    docTrendChartInstance?.resize();
    reqChartInstance?.resize();
    gaugeChartInstance?.resize();
    trendChartInstance?.resize();
    
    // 延迟执行以确保图表渲染完成
    setTimeout(async () => {
      try {
        // 获取所有图表的base64数据
        const exportData = {
          doc_trend_img: chartToBase64(docTrendChartInstance),
          req_chart_img: chartToBase64(reqChartInstance),
          gauge_chart_img: chartToBase64(gaugeChartInstance),
          trend_chart_img: chartToBase64(trendChartInstance),
          export_options: exportOptions.value
        };
        
        // 检查图表数据是否有效
        const validCharts = Object.entries(exportData)
          .filter(([key]) => key.endsWith('_img'))
          .filter(([, val]) => val && val.length > 100)
          .length;
          
        console.log(`有效图表数量: ${validCharts}/4`);
        
        if (validCharts < 1) {
          ElMessage.warning('图表数据准备失败，将尝试导出不含图表的报告');
        }
        
        ElMessage.info('正在生成报告，请耐心等待...');
        const response = await exportProjectAiReport(props.project.id, exportData);
        
        // 验证响应内容
        if (!response || !response.data) {
          throw new Error('收到的PDF数据无效');
        }
        
        // 创建Blob并下载
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        
        // 创建一个隐藏的a标签来下载
        const link = document.createElement('a');
        link.href = url;
        link.download = `${props.project.name || '项目'}_AI分析报告.pdf`;
        document.body.appendChild(link);
        link.click();
        
        // 清理
        setTimeout(() => {
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }, 100);
        
        ElMessage.success('AI分析报告导出成功');
        showExportDialog.value = false;
      } catch (error) {
        console.error('导出过程中发生错误:', error);
        ElMessage.error(`导出失败: ${error.message || '未知错误'}`);
      } finally {
        isExporting.value = false;
      }
    }, 800); // 增加延时确保图表完全渲染
  } catch (error) {
    console.error('导出AI分析报告失败:', error);
    ElMessage.error(`导出报告失败: ${error.message || '请稍后重试'}`);
    isExporting.value = false;
  }
}

function renderCharts() {
  // 销毁旧实例
  if (docTrendChartInstance) docTrendChartInstance.dispose()
  if (reqChartInstance) reqChartInstance.dispose()
  if (gaugeChartInstance) gaugeChartInstance.dispose()
  if (trendChartInstance) trendChartInstance.dispose()

  // 文档上传趋势
  if (docTrendChart.value) {
    docTrendChartInstance = echarts.init(docTrendChart.value)
    const docMonthMap = {}
    props.documents?.forEach(doc => {
      if (doc.uploaded_at) {
        const month = (doc.uploaded_at + '').slice(0, 7)
        docMonthMap[month] = (docMonthMap[month] || 0) + 1
      }
    })
    const docMonths = Object.keys(docMonthMap).sort()
    const docMonthData = docMonths.map(m => docMonthMap[m])
    docTrendChartInstance.setOption({
      tooltip: { 
        trigger: 'axis',
        backgroundColor: chartTooltipBg.value,
        borderColor: chartTooltipBorder.value,
        textStyle: { color: textColor.value }
      },
      grid: { left: 40, right: 20, top: 30, bottom: 40 },
      xAxis: {
        type: 'category',
        data: docMonths,
        axisLabel: { color: axisLabelColor.value, fontSize: 13 },
        name: docMonths.length ? '' : '暂无数据',
      },
      yAxis: {
        type: 'value',
        min: 0,
        axisLabel: { color: axisLabelColor.value, fontSize: 13 }
      },
      series: [
        {
          name: '上传文档数', type: 'line', data: docMonthData, smooth: true,
          itemStyle: { color: '#4F8CFF' },
          areaStyle: { color: 'rgba(79,140,255,0.1)' },
          symbolSize: 10
        }
      ]
    })
  }
  // 需求优先级分布
  if (reqChart.value) {
    reqChartInstance = echarts.init(reqChart.value)
    const reqPriorityMap = { 高: 0, 中: 0, 低: 0 }
    if (Array.isArray(props.requirements)) {
      props.requirements.forEach(req => {
        let pri = req.priority
        if (typeof pri === 'object' && pri !== null) pri = pri.value || pri.label || JSON.stringify(pri)
        if (typeof pri !== 'string') pri = String(pri || '').trim()
        if (['high', 'High', 'HIGH', '高', '1'].includes(pri)) {
          pri = '高'
        } else if (['medium', 'Medium', 'MEDIUM', '中', '2'].includes(pri)) {
          pri = '中'
        } else if (['low', 'Low', 'LOW', '低', '3'].includes(pri)) {
          pri = '低'
        } else {
          // 不是高/中/低的全部跳过，不计入图表
          return
        }
        reqPriorityMap[pri] = (reqPriorityMap[pri] || 0) + 1
      })
    }
    reqChartInstance.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: chartTooltipBg.value,
        borderColor: chartTooltipBorder.value,
        textStyle: { color: textColor.value }
      },
      legend: { bottom: 0, textStyle: { color: secondaryTextColor.value, fontSize: 13 } },
      color: ['#4F8CFF', '#34C759', '#FF9500'],
      series: [
        {
          name: '优先级分布', type: 'pie', radius: ['60%', '80%'],
          data: Object.keys(reqPriorityMap).map(k => ({ value: reqPriorityMap[k], name: k })),
          label: {
            show: true,
            position: 'outside',
            fontSize: 14,
            color: textColor.value,
            formatter: '{b}: {d}%'
          },
          labelLine: { length: 18, length2: 10 },
          avoidLabelOverlap: false,
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' } }
        }
      ]
    })
  }
  // 需求完成率仪表盘
  if (gaugeChart.value) {
    gaugeChartInstance = echarts.init(gaugeChart.value)
    let reqCompleted = 0
    if (Array.isArray(props.requirements)) {
      // 调试输出原始数据
      console.log('需求原始数据:', props.requirements)
      props.requirements.forEach(req => {
        let status = req.status
        if (typeof status === 'object' && status !== null) status = status.value || status.label || JSON.stringify(status)
        if (typeof status !== 'string') status = String(status || '').trim().toLowerCase()
        if ([
          '已完成', '完成', 'completed', 'done', 'finished', '已关闭', 'closed', '已解决', 'resolved', '1', 'true', '是', 'success'
        ].some(s => status.includes(s))) {
          reqCompleted++
        }
      })
    }
    const percent = reqTotal.value ? Math.round(reqCompleted / reqTotal.value * 100) : 0
    gaugeChartInstance.setOption({
      series: [
        {
          type: 'gauge',
          center: ['50%', '60%'],
          radius: '90%',
          min: 0,
          max: 100,
          progress: { show: true, width: 18 },
          axisLine: { lineStyle: { width: 18, color: [[1, '#4F8CFF']] } },
          pointer: { width: 6, length: '70%' },
          detail: {
            valueAnimation: true,
            fontSize: 32,
            color: '#4F8CFF',
            fontWeight: 'bold',
            offsetCenter: [0, '40%'],
            formatter: '{value}%'
          },
          data: [{ value: percent, name: '完成率' }],
          title: { fontSize: 16, color: axisLabelColor.value, offsetCenter: [0, '80%'] }
        }
      ]
    })
  }
  // 任务完成趋势
  if (trendChart.value) {
    // 调试输出原始任务数据
    console.log('任务原始数据:', normalizedTasks.value)
    trendChartInstance = echarts.init(trendChart.value)
    const monthMap = {}
    let hasCompleted = false
    if (Array.isArray(normalizedTasks.value)) {
      normalizedTasks.value.forEach(task => {
        // 仅根据 status 字段判断是否已完成
        let status = (task.status || '').toLowerCase()
        if ([
          '已完成', '完成', 'done', 'finished', '已关闭', 'closed', 'success', 'true', '1'
        ].some(s => status.includes(s))) {
          hasCompleted = true
          // 取 due_date 或 updated_at 作为完成时间
          let finish = task.due_date || task.updated_at || task.update_time || task.end_time || ''
          if (!finish) {
            // 没有时间字段时，使用当前月
            const now = new Date()
            finish = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
          }
          const month = (finish + '').slice(0, 7)
          monthMap[month] = (monthMap[month] || 0) + 1
        }
      })
    }
    let months = Object.keys(monthMap).sort()
    let monthData = months.map(m => monthMap[m])
    // 如果有任务但都未完成，显示0
    if (Array.isArray(normalizedTasks.value) && normalizedTasks.value.length > 0 && !hasCompleted) {
      const now = new Date()
      const thisMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
      months = [thisMonth]
      monthData = [0]
    }
    trendChartInstance.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: chartTooltipBg.value,
        borderColor: chartTooltipBorder.value,
        textStyle: { color: textColor.value }
      },
      grid: { left: 40, right: 20, top: 30, bottom: 40 },
      xAxis: {
        type: 'category',
        data: months,
        axisLabel: { color: axisLabelColor.value, fontSize: 13 },
        name: months.length ? '' : '暂无数据',
      },
      yAxis: {
        type: 'value',
        min: 0,
        axisLabel: { color: axisLabelColor.value, fontSize: 13 }
      },
      series: [
        {
          name: '完成任务数', type: 'bar', data: monthData,
          itemStyle: { color: '#34C759' },
          barWidth: 32,
          label: { show: true, position: 'top', color: '#34C759', fontSize: 16, fontWeight: 'bold' }
        }
      ]
    })
  }
}

// 调整图表尺寸
const resizeCharts = () => {
  docTrendChartInstance?.resize()
  reqChartInstance?.resize()
  gaugeChartInstance?.resize()
  trendChartInstance?.resize()
}

// 监听窗口尺寸变化
window.addEventListener('resize', resizeCharts)

// 监听属性变化，重新渲染图表
watch(() => [props.tasks, props.documents, props.requirements, props.project], () => {
  // 延迟执行，确保DOM已更新
  nextTick(() => {
    renderCharts()
    
    // 如果有项目ID但尚未加载分析，自动加载
    if (props.project?.id && Object.keys(chartAnalysis.value).length === 0) {
      loadChartAnalysis()
    }
  })
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    renderCharts()
    
    // 如果有项目ID，自动加载分析
    if (props.project?.id) {
      loadChartAnalysis()
    }
  })
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
})

onBeforeUnmount(() => {
  // 清理事件监听器和图表实例
  window.removeEventListener('resize', resizeCharts)
  docTrendChartInstance?.dispose()
  reqChartInstance?.dispose()
  gaugeChartInstance?.dispose()
  trendChartInstance?.dispose()
  observer.disconnect();
})

const observer = new MutationObserver(() => {
  const newTheme = document.documentElement.getAttribute('data-theme') || 'light';
  if (theme.value !== newTheme) {
    theme.value = newTheme;
  }
});
</script>

<style lang="scss" scoped>
.module-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  padding: 20px;
  margin-bottom: 20px;
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  .module-title {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }
}

.modern-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  padding: 16px;
  height: 100%;
  
  h6.text-primary {
    color: #4F8CFF;
    font-weight: 600;
    margin-bottom: 16px;
  }
}

.chart-center-wrap {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.modern-echart {
  width: 100%;
  height: 300px;
}

.chart-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #999;
  font-size: 14px;
}

.modern-summary {
  text-align: center;
  margin-top: 8px;
  color: #666;
  font-size: 14px;
  
  &.main-value {
    font-weight: 600;
    color: #333;
  }
}

.ai-analysis-section {
  margin-top: 16px;
  border-top: 1px dashed #eee;
  padding-top: 12px;
}

.ai-analysis-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 0;
  
  .el-icon {
    color: #4F8CFF;
    margin-right: 6px;
  }
  
  span {
    color: #4F8CFF;
    font-weight: 600;
  }
  
  .toggle-icon {
    margin-left: auto;
    transition: transform 0.3s;
    
    &.is-active {
      transform: rotate(180deg);
    }
  }
}

.ai-analysis-content {
  padding: 12px;
  background: #f9fbfe;
  border-radius: 6px;
  margin-top: 4px;
  
  .analysis-section {
    margin-bottom: 16px;
    
    h6 {
      font-weight: 600;
      color: #333;
      margin-bottom: 10px;
      position: relative;
      padding-left: 12px;
      
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 14px;
        background: #4F8CFF;
        border-radius: 2px;
      }
    }
    
    ul {
      padding-left: 20px;
      margin: 0;
      
      &.finding-list li {
        color: #333;
        margin-bottom: 8px;
        position: relative;
      }
      
      &.recommendation-list li {
        color: #1976D2;
        margin-bottom: 8px;
      }
    }
    
    .insights-text {
      color: #555;
      line-height: 1.6;
      margin: 0;
      padding: 0 6px;
    }
  }
  
  .analysis-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px 0;
    
    .el-icon {
      color: #4F8CFF;
      margin-right: 8px;
      font-size: 18px;
    }
  }
  
  .analysis-empty {
    text-align: center;
    color: #999;
    padding: 16px 0;
    
    .el-button {
      margin-top: 6px;
    }
  }
}

.ai-report-btn {
  display: flex;
  align-items: center;
  
  .btn-icon {
    margin-right: 4px;
  }
}

// 导出对话框样式
.export-dialog-content {
  .dialog-info-box {
    background: #f0f7ff;
    border-left: 4px solid #1976D2;
    padding: 12px;
    margin-bottom: 20px;
    border-radius: 4px;
    
    p {
      margin: 0;
      color: #333;
      display: flex;
      align-items: center;
      
      .el-icon {
        color: #1976D2;
        margin-right: 8px;
      }
    }
  }
  
  .export-options {
    margin-bottom: 20px;
    
    h4 {
      font-size: 16px;
      margin-bottom: 12px;
    }
    
    .el-checkbox-group {
      display: flex;
      flex-wrap: wrap;
      
      .el-checkbox {
        margin-right: 20px;
        margin-bottom: 10px;
      }
    }
  }
  
  .report-preview {
    text-align: center;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 4px;
    
    .preview-img {
      max-width: 100%;
      height: auto;
      max-height: 200px;
      object-fit: contain;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .modern-echart {
    height: 250px;
  }
}

/* 深色模式下的样式修复 */
[data-theme="dark"] {
  .module-card,
  .modern-card {
    background: var(--el-bg-color-overlay);
    color: var(--el-text-color-primary);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  }

  .module-header .module-title,
  .modern-summary.main-value {
    color: var(--el-text-color-primary);
  }

  .modern-card h6.text-primary {
    color: var(--el-color-primary);
  }
  
  .modern-summary {
    color: var(--el-text-color-secondary);
  }

  .ai-analysis-section {
    border-top-color: var(--el-border-color-light);
  }

  .ai-analysis-header span,
  .ai-analysis-header .el-icon {
    color: var(--el-color-primary);
  }

  .ai-analysis-content {
    background: var(--el-bg-color-page);
  }

  .ai-analysis-content .analysis-section h6 {
    color: var(--el-text-color-primary);
    &::before {
      background: var(--el-color-primary);
    }
  }

  .ai-analysis-content .analysis-section ul.finding-list li,
  .ai-analysis-content .analysis-section .insights-text {
    color: var(--el-text-color-regular);
  }

  .ai-analysis-content .analysis-section ul.recommendation-list li {
    color: var(--el-color-primary-light-3);
  }

  .chart-empty,
  .analysis-empty {
    color: var(--el-text-color-secondary);
  }
  
  .export-dialog-content {
    .dialog-info-box {
      background: var(--el-color-primary-light-9);
      border-left-color: var(--el-color-primary);
      p {
        color: var(--el-text-color-primary);
      }
    }
    
    h4 {
      color: var(--el-text-color-primary);
    }
    
    .report-preview {
      background: var(--el-fill-color-light);
    }
  }
}
</style> 
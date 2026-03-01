<template>
  <div class="knowledge-graph-container">
    <!-- 控制面板 -->
    <div class="control-panel">
      <el-card class="control-card">
        <template #header>
          <div class="card-header">
            <span>图谱控制</span>
            <el-button 
              type="text" 
              :icon="isCollapsed ? Expand : Fold" 
              @click="toggleCollapse"
            />
          </div>
        </template>
        
        <div v-show="!isCollapsed" class="control-content">
          <!-- 搜索功能 -->
          <div class="control-section">
            <h6>搜索实体</h6>
            <el-input 
              v-model="searchQuery" 
              placeholder="搜索实体名称..."
              clearable
              :prefix-icon="Search"
              @input="handleSearch"
            />
          </div>
          
          <!-- 实体类型筛选 -->
          <div class="control-section">
            <h6>实体类型</h6>
            <el-select 
              v-model="selectedTypes" 
              multiple 
              placeholder="选择实体类型"
              style="width: 100%"
              @change="handleTypeFilter"
            >
              <el-option 
                v-for="type in entityTypes" 
                :key="type" 
                :label="type" 
                :value="type"
              />
            </el-select>
          </div>
          
          <!-- 布局控制 -->
          <div class="control-section">
            <h6>布局算法</h6>
            <el-select 
              v-model="layoutType" 
              placeholder="选择布局"
              style="width: 100%"
              @change="handleLayoutChange"
            >
              <el-option label="圆形布局" value="circular" />
              <el-option label="力导向布局" value="force" />
            </el-select>
          </div>
          
          <!-- 操作按钮 -->
          <div class="control-section">
            <div class="action-buttons">
              <el-button 
                class="action-btn" 
                type="primary" 
                :icon="Refresh" 
                @click="resetGraph"
              >
                <el-icon><Refresh /></el-icon> 重置视图
              </el-button>
              <el-button 
                class="action-btn" 
                type="success" 
                :icon="Download" 
                @click="exportGraph"
              >
                <el-icon><Download /></el-icon> 导出图片
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
      

    </div>
    
    <!-- 图谱展示区域 -->
    <div class="graph-container">
      <div class="graph-header">
        <div class="header-left">
          <h3>企业知识图谱</h3>
        </div>
        <div class="header-center">
          <!-- 移除文档管理和知识图谱按钮 -->
        </div>
        <div class="header-right">
          <el-button type="text" :icon="FullScreen" @click="toggleFullscreen">全屏</el-button>
        </div>
      </div>
      
      <div class="graph-content">
        <div 
          ref="chartRef" 
          class="chart-canvas"
        ></div>
        
        <!-- 图例说明 - 移到右侧 -->
        <div class="legend-panel">
          <el-card class="legend-card-right">
            <template #header>
              <span>图例说明</span>
            </template>
            <div class="legend-content">
              <div v-for="category in categories" :key="category.name" class="legend-item">
                <div class="legend-color" :style="{backgroundColor: category.color}"></div>
                <span class="legend-label">{{ category.name }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>
      
      <!-- 独立的loading遮罩，不影响chart-canvas尺寸 -->
      <div v-if="loading" class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>正在加载知识图谱...</span>
      </div>
      
      <div v-if="!loading && graphData.nodes.length === 0" class="empty-state">
        <div class="empty-icon">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <h3>暂无知识图谱数据</h3>
        <p>请先构建知识库以生成图谱数据</p>
      </div>
    </div>
    
    <!-- 实体详情抽屉 -->
    <el-drawer 
      v-model="showEntityDetail" 
      title="实体详情" 
      size="400px"
      direction="rtl"
    >
      <div v-if="selectedEntity" class="entity-detail">
        <div class="entity-header">
          <div class="entity-icon" :style="{backgroundColor: getEntityColor(selectedEntity.type)}">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="entity-info">
            <h4>{{ selectedEntity.name }}</h4>
            <el-tag :type="getEntityTagType(selectedEntity.type)">{{ getChineseType(selectedEntity.type) }}</el-tag>
          </div>
        </div>
        
        <div class="entity-content">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="实体ID">{{ selectedEntity.id }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ getChineseType(selectedEntity.type) }}</el-descriptions-item>
            <el-descriptions-item label="描述">
              <div class="description-text">{{ selectedEntity.description || '暂无描述' }}</div>
            </el-descriptions-item>
            <el-descriptions-item label="度数">{{ selectedEntity.symbolSize || 0 }}</el-descriptions-item>
          </el-descriptions>
          
          <div class="relationships-section">
            <h5>关联关系</h5>
            <div v-if="entityRelationships.length === 0" class="no-relationships">
              暂无关联关系
            </div>
            <div v-else class="relationships-list">
              <div 
                v-for="rel in entityRelationships" 
                :key="rel.id" 
                class="relationship-item"
                @click="highlightRelationship(rel)"
              >
                <div class="relationship-info">
                  <span class="relationship-target">
                    <span class="relationship-direction">{{ rel.direction === 'outgoing' ? '→' : '←' }}</span>
                    {{ rel.direction === 'outgoing' ? rel.targetName : rel.sourceName }}
                  </span>
                  <span class="relationship-type">{{ rel.relation }}</span>
                </div>
                <el-icon class="relationship-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { 
  Search, 
  Refresh, 
  Download,
  FullScreen, 
  DataAnalysis,
  Expand,
  Fold,
  ArrowRight,
  Loading
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getKnowledgeGraphData, getEntityDetail } from '@/api/knowledge'

// 响应式数据
const chartRef = ref(null)
const chart = ref(null)
const loading = ref(false)
const isCollapsed = ref(false)
const showEntityDetail = ref(false)
const selectedEntity = ref(null)
const searchQuery = ref('')
const selectedTypes = ref([])
const layoutType = ref('circular')
const showLabels = ref(true)

// 图谱数据
const graphData = reactive({
  nodes: [],
  edges: [],
  categories: []
})

const entityTypes = ref([])
const entityRelationships = ref([])

// 事件处理函数
let handleResize = null
let handleFullscreenChange = null

// 计算属性
const categories = computed(() => {
  return graphData.categories.map(cat => ({
    name: cat.name,
    color: cat.color
  }))
})

// 方法
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleSearch = () => {
  if (!searchQuery.value.trim()) {
    resetHighlight()
    return
  }
  
  const searchTerm = searchQuery.value.toLowerCase()
  const matchedNodes = graphData.nodes.filter(node => 
    node.name.toLowerCase().includes(searchTerm)
  )
  
  if (matchedNodes.length > 0) {
    highlightNodes(matchedNodes)
    // 聚焦到第一个匹配的节点
    if (chart.value) {
      chart.value.dispatchAction({
        type: 'focusNodeAdjacency',
        seriesIndex: 0,
        dataIndex: graphData.nodes.findIndex(node => node.id === matchedNodes[0].id)
      })
    }
  } else {
    ElMessage.warning('未找到匹配的实体')
  }
}

const handleTypeFilter = async () => {
  await updateChart()
}

const handleLayoutChange = async () => {
  console.log('🔄 布局类型改变:', layoutType.value)
  
  // 如果切换到力导向布局，清除所有节点的固定位置
  if (layoutType.value === 'force') {
    console.log('🎯 切换到力导向布局，清除节点固定位置')
    graphData.nodes.forEach(node => {
      // 移除可能存在的固定位置属性
      delete node.fixed
      delete node.x
      delete node.y
    })
  }
  
  // 强制重新渲染图表
  if (chart.value && !chart.value.isDisposed()) {
    chart.value.clear() // 清除当前图表内容
  }
  
  await updateChart()
}

const resetGraph = () => {
  searchQuery.value = ''
  selectedTypes.value = []
  resetHighlight()
  if (chart.value) {
    chart.value.dispatchAction({
      type: 'restore'
    })
  }
}

const exportGraph = () => {
  if (chart.value) {
    const url = chart.value.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    
    const link = document.createElement('a')
    link.href = url
    link.download = '知识图谱.png'
    link.click()
    
    ElMessage.success('图谱导出成功')
  }
}

const toggleFullscreen = async () => {
  const container = chartRef.value.parentElement
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      await container.requestFullscreen()
    }
    // 等待全屏状态改变后重新调整图表大小
    setTimeout(() => {
      if (chart.value && !chart.value.isDisposed()) {
        chart.value.resize()
      }
    }, 100)
  } catch (error) {
    console.error('全屏操作失败:', error)
    ElMessage.error('全屏操作失败')
  }
}

const getEntityColor = (type) => {
  const category = graphData.categories.find(cat => cat.name === type)
  return category ? category.color : '#409EFF'
}

const getEntityTagType = (type) => {
  const typeMap = {
    'ORGANIZATION': 'primary',
    'PERSON': 'success',
    'LOCATION': 'warning',
    'EVENT': 'danger',
    '组织': 'primary',
    '人员': 'success',
    '地点': 'warning',
    '事件': 'danger'
  }
  return typeMap[type] || 'info'
}

// 英文类型转中文映射
const getChineseType = (englishType) => {
  const typeMap = {
    'ORGANIZATION': '组织',
    'PERSON': '人员',
    'LOCATION': '地点',
    'EVENT': '事件'
  }
  return typeMap[englishType] || englishType
}

// 优化圆形布局，确保节点不溢出容器
const optimizeCircularLayout = (nodes, containerWidth, containerHeight) => {
  if (!nodes || nodes.length === 0) return nodes
  
  const centerX = containerWidth / 2
  const centerY = containerHeight / 2
  const maxRadius = Math.min(containerWidth, containerHeight) / 2 - 80 // 留出边距
  
  // 根据节点数量动态调整半径
  const nodeCount = nodes.length
  let radius = maxRadius
  
  if (nodeCount > 20) {
    radius = maxRadius * 0.8 // 节点多时缩小半径
  } else if (nodeCount > 10) {
    radius = maxRadius * 0.9
  }
  
  // 为每个节点计算位置
  return nodes.map((node, index) => {
    const angle = (2 * Math.PI * index) / nodeCount
    const x = centerX + radius * Math.cos(angle)
    const y = centerY + radius * Math.sin(angle)
    
    return {
      ...node,
      x: Math.max(50, Math.min(containerWidth - 50, x)),
      y: Math.max(50, Math.min(containerHeight - 50, y))
    }
  })
}

const highlightNodes = (nodes) => {
  if (!chart.value) return
  
  const nodeIds = nodes.map(node => node.id)
  chart.value.dispatchAction({
    type: 'highlight',
    seriesIndex: 0,
    dataIndex: graphData.nodes.map((node, index) => 
      nodeIds.includes(node.id) ? index : null
    ).filter(index => index !== null)
  })
}

const resetHighlight = () => {
  if (!chart.value) return
  
  chart.value.dispatchAction({
    type: 'downplay',
    seriesIndex: 0
  })
}

const highlightRelationship = (relationship) => {
  // 高亮显示特定关系
  if (!chart.value) return
  
  const sourceIndex = graphData.nodes.findIndex(node => node.id === selectedEntity.value.id)
  const targetIndex = graphData.nodes.findIndex(node => node.name === relationship.targetName)
  
  if (sourceIndex !== -1 && targetIndex !== -1) {
    chart.value.dispatchAction({
      type: 'highlight',
      seriesIndex: 0,
      dataIndex: [sourceIndex, targetIndex]
    })
  }
}

const initChart = async (retryCount = 0) => {
  console.log(`🎯 开始初始化图表... (尝试次数: ${retryCount + 1})`)
  
  // 详细检查DOM元素状态
  console.log('🔍 DOM元素状态检查:', {
    chartRefExists: !!chartRef.value,
    chartRefValue: !!chartRef.value,
    chartRefType: typeof chartRef.value,
    documentReady: document.readyState
  })
  
  // 检查DOM元素是否存在
  let targetElement = chartRef.value
  
  if (!targetElement) {
    console.warn('⚠️ chartRef.value 为空，尝试备用方案')
    
    // 备用方案：直接通过class选择器获取元素
    targetElement = document.querySelector('.chart-canvas')
    console.log('🔍 备用方案查找结果:', {
      foundByClass: !!targetElement,
      elementType: targetElement ? targetElement.tagName : 'N/A'
    })
    
    if (!targetElement) {
      if (retryCount < 10) {
        console.log(`🔄 等待DOM元素就绪，第${retryCount + 1}次重试...`)
        await new Promise(resolve => setTimeout(resolve, 200))
        return initChart(retryCount + 1)
      } else {
        console.error('❌ 达到最大重试次数，DOM元素仍然不存在')
        console.error('🔍 最终状态检查:', {
          allChartCanvas: document.querySelectorAll('.chart-canvas').length,
          bodyChildren: document.body.children.length,
          documentReady: document.readyState
        })
        throw new Error('DOM元素初始化失败')
      }
    } else {
      // 如果通过class找到了元素，更新chartRef
      chartRef.value = targetElement
      console.log('✅ 通过备用方案找到DOM元素')
    }
  }
  
  // 强制触发重排，确保DOM完全渲染
  targetElement.offsetHeight
  await new Promise(resolve => setTimeout(resolve, 50))
  
  // 检查DOM元素是否可见和有尺寸
  const rect = targetElement.getBoundingClientRect()
  const computedStyle = window.getComputedStyle(targetElement)
  const parentRect = targetElement.parentElement?.getBoundingClientRect()
  
  // 放宽可见性检查条件 - 只要元素存在且不是display:none就认为可用
  const isElementUsable = (
    computedStyle.display !== 'none' &&
    computedStyle.visibility !== 'hidden'
  )
  const parentVisible = !parentRect || (parentRect.width > 0 && parentRect.height > 0)
  
  console.log('📊 DOM元素状态检查:', {
    width: rect.width,
    height: rect.height,
    offsetWidth: targetElement.offsetWidth,
    offsetHeight: targetElement.offsetHeight,
    clientWidth: targetElement.clientWidth,
    clientHeight: targetElement.clientHeight,
    display: computedStyle.display,
    visibility: computedStyle.visibility,
    opacity: computedStyle.opacity,
    isElementUsable,
    parentVisible,
    parentRect: parentRect ? { width: parentRect.width, height: parentRect.height } : null
  })
  
  // 如果元素不可用，等待重试
  if (!isElementUsable) {
    if (retryCount < 5) {
      console.log(`🔄 DOM元素不可用，第${retryCount + 1}次重试...`)
      await new Promise(resolve => setTimeout(resolve, 200))
      return initChart(retryCount + 1)
    } else {
      console.warn('⚠️ 元素仍不可用，但继续尝试初始化')
    }
  }
  
  // 最终尺寸确认，优先使用CSS设置的固定尺寸
  let finalWidth = targetElement.offsetWidth || targetElement.clientWidth || rect.width
  let finalHeight = targetElement.offsetHeight || targetElement.clientHeight || rect.height
  
  // 如果无法获取尺寸，使用CSS中设置的默认值
  if (!finalWidth || finalWidth < 100) {
    finalWidth = 800 // 对应CSS中chart-canvas的flex:1计算结果
  }
  if (!finalHeight || finalHeight < 100) {
    finalHeight = 500 // 对应CSS中chart-canvas的固定高度
  }
  
  console.log('📊 目标DOM元素:', targetElement)
  console.log('📊 最终使用尺寸:', {
    width: finalWidth,
    height: finalHeight,
    offsetWidth: targetElement.offsetWidth,
    offsetHeight: targetElement.offsetHeight,
    clientWidth: targetElement.clientWidth,
    clientHeight: targetElement.clientHeight
  })
  
  // 如果已有实例，先销毁
  if (chart.value && !chart.value.isDisposed()) {
    console.log('🗑️ 销毁现有ECharts实例')
    chart.value.dispose()
  }
  
  console.log('🎨 开始初始化ECharts实例...')
  // 明确指定ECharts配置，解决高DPI显示器canvas尺寸异常问题
  chart.value = echarts.init(targetElement, null, {
    renderer: 'canvas',
    devicePixelRatio: 1, // 固定为1，避免高DPI自动缩放导致的显示异常
    width: finalWidth,
    height: finalHeight
  })
  console.log('✅ ECharts 实例已创建:', !!chart.value)
  console.log('✅ ECharts 实例状态:', {
    isDisposed: chart.value ? chart.value.isDisposed() : 'N/A',
    targetElementTag: targetElement.tagName,
    targetElementClass: targetElement.className
  })
  
  // 确保chartRef指向正确的元素
  if (chartRef.value !== targetElement) {
    chartRef.value = targetElement
    console.log('🔧 已更新chartRef引用')
  }
  
  // 绑定节点点击事件处理函数
  bindChartEvents()
  
  console.log('🎉 图表初始化完成')
  
  // 验证图表实例是否正常创建
  if (!chart.value || chart.value.isDisposed()) {
    console.error('❌ ECharts实例创建失败或已被销毁')
    throw new Error('ECharts实例创建失败')
  }
  
  console.log('✅ ECharts实例验证通过，图表初始化成功')
}

// 绑定图表事件处理函数
const bindChartEvents = () => {
  if (!chart.value || chart.value.isDisposed()) {
    console.warn('⚠️ 图表实例不存在，无法绑定事件')
    return
  }
  
  // 清除之前的事件监听器，避免重复绑定
  chart.value.off('click')
  chart.value.off('mousedown')
  chart.value.off('mouseup')
  
  // 监听节点点击事件
  chart.value.on('click', (params) => {
    console.log('🖱️ 节点被点击:', params)
    console.log('🔍 点击事件详情:', {
      dataType: params.dataType,
      componentType: params.componentType,
      seriesType: params.seriesType,
      data: params.data,
      layoutType: layoutType.value
    })
    
    if (params.dataType === 'node' && params.data) {
      console.log('✅ 有效的节点点击，准备显示详情')
      selectedEntity.value = params.data
      loadEntityRelationships(params.data.id)
      showEntityDetail.value = true
      console.log('📋 实体详情已设置:', {
        selectedEntity: selectedEntity.value,
        showEntityDetail: showEntityDetail.value
      })
    } else {
       console.log('❌ 无效的节点点击或缺少数据')
     }
   })
  
  // 监听节点拖拽开始事件
  chart.value.on('mousedown', (params) => {
    if (params.dataType === 'node') {
      console.log('🖱️ 开始拖拽节点:', params.data.name)
      // 添加拖拽时的视觉反馈
      chart.value.setOption({
        series: [{
          emphasis: {
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(64, 158, 255, 0.5)'
            }
          }
        }]
      })
    }
  })
  
  // 监听节点拖拽结束事件
  chart.value.on('mouseup', (params) => {
    if (params.dataType === 'node') {
      console.log('🖱️ 结束拖拽节点:', params.data.name)
      // 检查节点是否超出边界并进行约束
      const chartInstance = chart.value
      const option = chartInstance.getOption()
      const series = option.series[0]
      
      // 获取图表容器尺寸
      const element = chartRef.value
      if (!element) return
      
      const chartWidth = element.offsetWidth
      const chartHeight = element.offsetHeight
      const margin = 50 // 边界边距
      
      // 约束节点位置在容器范围内
      if (series.data) {
        series.data.forEach(node => {
          if (node.x !== undefined && node.y !== undefined) {
            node.x = Math.max(margin, Math.min(chartWidth - margin, node.x))
            node.y = Math.max(margin, Math.min(chartHeight - margin, node.y))
          }
        })
        
        // 更新图表配置
        chartInstance.setOption({
          series: [{
            data: series.data
          }]
        })
      }
    }
  })
}

// 为力导向布局添加初始位置设置
const initializeForceLayoutPositions = (nodes, containerWidth, containerHeight) => {
  if (!nodes || nodes.length === 0) return nodes
  
  const centerX = containerWidth / 2
  const centerY = containerHeight / 2
  const radius = Math.min(containerWidth, containerHeight) / 4
  
  return nodes.map((node, index) => {
    // 如果节点没有初始位置，给它一个随机但合理的初始位置
    if (typeof node.x === 'undefined' || typeof node.y === 'undefined') {
      const angle = (2 * Math.PI * index) / nodes.length
      const r = radius * (0.5 + Math.random() * 0.5) // 随机半径，避免所有节点在同一圆上
      
      return {
        ...node,
        x: centerX + r * Math.cos(angle) + (Math.random() - 0.5) * 50,
        y: centerY + r * Math.sin(angle) + (Math.random() - 0.5) * 50,
        // 确保节点有必要的属性
        id: String(node.id || `node_${index}`), // 确保ID为字符串
        name: node.name || `节点${index}`,
        category: node.category !== undefined ? node.category : (node.type || 0),
        value: node.value || 1,
        symbolSize: node.symbolSize || 30,
        // 确保节点有正确的颜色
        itemStyle: {
          color: getEntityColor(node.type || 'default'),
          borderColor: '#fff',
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      }
    }
    
    return {
      ...node,
      // 确保节点有必要的属性
      id: String(node.id || `node_${index}`), // 确保ID为字符串
      name: node.name || `节点${index}`,
      category: node.category !== undefined ? node.category : (node.type || 0),
      value: node.value || 1,
      symbolSize: node.symbolSize || 30,
      // 确保节点有正确的颜色
      itemStyle: {
        color: getEntityColor(node.type || 'default'),
        borderColor: '#fff',
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.3)'
      }
    }
  })
}

const updateChart = async () => {
  console.log('🎨 updateChart 被调用')
  console.log('📊 当前状态:', {
    hasChart: !!chart.value,
    nodesCount: graphData.nodes.length,
    edgesCount: graphData.edges.length,
    selectedTypes: selectedTypes.value,
    layoutType: layoutType.value
  })
  
  // 检查ECharts实例是否存在或已被dispose
  if (!chart.value || chart.value.isDisposed()) {
    console.warn('⚠️ ECharts实例不存在或已被dispose，重新初始化图表')
    console.log('🔧 chartRef.value状态:', !!chartRef.value)
    await initChart()
    if (!chart.value) {
      console.error('❌ 重新初始化图表失败')
      return
    }
    console.log('✅ ECharts实例重新初始化成功')
  }
  
  if (graphData.nodes.length === 0) {
    console.warn('⚠️ 没有节点数据，无法更新图表')
    return
  }
  
  // 过滤节点
  let filteredNodes = [...graphData.nodes] // 创建副本避免修改原数据
  if (selectedTypes.value.length > 0) {
    filteredNodes = graphData.nodes.filter(node => 
      selectedTypes.value.includes(node.type)
    )
    console.log('🔍 应用类型过滤后的节点数量:', filteredNodes.length)
  }
  
  // 过滤边，确保边的数据格式正确
  const nodeIds = new Set(filteredNodes.map(node => String(node.id))) // 确保节点ID集合为字符串
  let filteredEdges = graphData.edges.filter(edge => 
    nodeIds.has(String(edge.source)) && nodeIds.has(String(edge.target)) // 确保类型匹配
  ).map(edge => ({
    ...edge,
    // 确保边有必要的属性，并统一数据类型
    source: String(edge.source), // 确保source为字符串
    target: String(edge.target), // 确保target为字符串
    value: edge.value || edge.weight || 1,
    lineStyle: {
      color: edge.color || '#999',
      width: edge.width || 1
    }
  }))
  
  console.log('📈 过滤后的数据:', {
    filteredNodes: filteredNodes.length,
    filteredEdges: filteredEdges.length
  })
  
  // 详细检查节点ID和边连接的匹配情况
  if (filteredNodes.length > 0 && filteredEdges.length > 0) {
    const nodeIdSet = new Set(filteredNodes.map(node => String(node.id)))
    const unmatchedEdges = filteredEdges.filter(edge => 
      !nodeIdSet.has(String(edge.source)) || !nodeIdSet.has(String(edge.target))
    )
    
    // 进一步过滤，只保留有效的边
    filteredEdges = filteredEdges.filter(edge => {
      const sourceExists = nodeIdSet.has(String(edge.source))
      const targetExists = nodeIdSet.has(String(edge.target))
      const isValid = sourceExists && targetExists && edge.source !== edge.target
      
      if (!isValid) {
        console.warn('⚠️ 发现无效边:', {
          source: edge.source,
          target: edge.target,
          sourceExists,
          targetExists,
          isSelfLoop: edge.source === edge.target
        })
      }
      
      return isValid
    })
    
    console.log('🔍 节点和边的匹配分析:', {
      nodeIds: Array.from(nodeIdSet).slice(0, 10),
      nodeIdTypes: [...new Set(filteredNodes.map(node => typeof node.id))],
      edgeSourceTargetSample: filteredEdges.slice(0, 5).map(edge => ({
        source: edge.source,
        sourceType: typeof edge.source,
        target: edge.target,
        targetType: typeof edge.target,
        sourceExists: nodeIdSet.has(String(edge.source)),
        targetExists: nodeIdSet.has(String(edge.target))
      })),
      unmatchedEdgesCount: unmatchedEdges.length,
      validEdgesCount: filteredEdges.length,
      unmatchedEdgesSample: unmatchedEdges.slice(0, 3)
    })
  }
  
  // 获取容器尺寸
  const containerWidth = chartRef.value?.offsetWidth || 800
  const containerHeight = chartRef.value?.offsetHeight || 600
  
  // 根据布局类型处理节点位置
  if (layoutType.value === 'circular') {
    filteredNodes = optimizeCircularLayout(filteredNodes, containerWidth, containerHeight)
    console.log('🎯 已优化圆形布局，容器尺寸:', { containerWidth, containerHeight })
  } else if (layoutType.value === 'force') {
    // 为力导向布局初始化节点位置
    filteredNodes = initializeForceLayoutPositions(filteredNodes, containerWidth, containerHeight)
    console.log('🎯 已初始化力导向布局节点位置，容器尺寸:', { containerWidth, containerHeight })
    console.log('🔍 力导向节点示例:', filteredNodes.slice(0, 3))
  }
  
  const option = {
    title: {
      text: '企业知识图谱',
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#303133'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        if (params.dataType === 'node') {
          return `
            <div style="padding: 6px 12px; max-width: 300px; word-wrap: break-word;">
              <strong style="color: #303133;">${params.data.name}</strong><br/>
              <span style="color: #606266;">类型: ${getChineseType(params.data.type)}</span><br/>
              <span style="color: #909399;">${params.data.description || '暂无描述'}</span>
            </div>
          `
        } else if (params.dataType === 'edge') {
          return `
            <div style="padding: 6px 12px; max-width: 300px; word-wrap: break-word;">
              <strong style="color: #303133;">${params.data.source} → ${params.data.target}</strong><br/>
              <span style="color: #606266;">关系: ${params.data.relation}</span><br/>
              <span style="color: #909399;">权重: ${params.data.weight}</span>
            </div>
          `
        }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e4e7ed',
      borderWidth: 1,
      textStyle: {
        fontSize: 12
      },
      extraCssText: 'max-width: 300px; max-height: 120px; overflow: hidden; white-space: normal; word-wrap: break-word; line-height: 1.4;'
    },
    legend: {
      show: false
    },
    series: [{
      type: 'graph',
      layout: layoutType.value,
      data: filteredNodes,
      links: filteredEdges,
      categories: graphData.categories,
      roam: true,
      draggable: true, // 启用节点拖拽
      // 添加边的符号配置，确保连接到节点边缘
      edgeSymbol: layoutType.value === 'force' ? ['none', 'arrow'] : ['none', 'none'],
      edgeSymbolSize: layoutType.value === 'force' ? [0, 8] : [0, 0],
      // 确保边连接到节点边缘而不是中心
      autoCurveness: true,
      label: {
        show: showLabels.value,
        position: 'inside', // 改为内部显示，避免溢出
        formatter: function(params) {
          // 只显示实体名称，不显示任何数字
          const name = params.data.name || params.name
          // 过滤掉纯数字内容，只保留文本
          if (typeof name === 'string' && !/^\d+$/.test(name.trim())) {
            return name.length > 8 ? name.substring(0, 8) + '...' : name
          }
          return '' // 如果是纯数字则不显示
        },
        fontSize: 11,
        color: '#303133',
        fontWeight: 'bold',
        textBorderColor: '#fff',
        textBorderWidth: 1
      },
      edgeLabel: {
        show: false, // 隐藏边标签，避免显示数字
        formatter: function(params) {
          // 只显示关系名称，不显示权重等数字
          return params.data.relation || ''
        },
        fontSize: 10,
        color: '#909399'
      },
      labelLayout: {
        hideOverlap: true,
        moveOverlap: 'shiftY' // 自动调整重叠标签位置
      },
      scaleLimit: {
        min: 0.3,
        max: 3
      },
      ...(layoutType.value === 'force' ? {
        force: {
          // 适中的节点间斥力，防止节点重叠但不过度分散
          repulsion: [200, 600],
          // 适中的重力，保持图形聚合
          gravity: 0.15,
          // 适中的边长，确保连接清晰可见
          edgeLength: [50, 100],
          // 关闭持续动画，避免线条持续移动
          layoutAnimation: false,
          // 增加摩擦力，让布局更快稳定
          friction: 0.95,
          // 设置初始温度，控制布局收敛速度
          initLayout: 'circular',
          // 添加边的连接配置
          edgeSymbol: ['none', 'arrow'], // 添加箭头指示方向
          edgeSymbolSize: [0, 8] // 箭头大小
        }
      } : {}),
      ...(layoutType.value === 'circular' ? {
        circular: {
          rotateLabel: false, // 关闭标签旋转，保持水平
          radius: 180 // 设置圆形布局半径，避免溢出
        }
      } : {}),
      lineStyle: {
        color: 'source',
        curveness: layoutType.value === 'force' ? 0.1 : 0.1, // 减少弯曲度，让连线更直
        opacity: 0.8,
        width: layoutType.value === 'force' ? 2 : 1, // 增加线条宽度，更明显
        type: 'solid', // 确保线条为实线
        cap: 'round', // 圆形端点
        join: 'round' // 圆形连接点
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 3
        },
        label: {
          show: true,
          formatter: '{b}', // 悬停时显示完整名称
          fontSize: 12,
          fontWeight: 'bold'
        }
      },
      // 节点样式现在在每个节点的itemStyle中单独设置
      // 设置节点大小
      symbolSize: function(value, params) {
        if (layoutType.value === 'force') {
          // 力导向布局使用更大的节点，增强视觉效果
          return Math.min(Math.max(25, (params.data.value || 1) * 12), 60)
        }
        return Math.min(Math.max(20, (params.data.value || 1) * 10), 50)
      }
    }]
  }
  
  console.log(' 设置图表配置:', {
    title: option.title.text,
    seriesDataLength: option.series[0].data.length,
    seriesLinksLength: option.series[0].links.length,
    layoutType: option.series[0].layout,
    hasForceConfig: !!option.series[0].force,
    forceConfig: option.series[0].force
  })
  
  // 设置图表配置
  chart.value.setOption(option, true)
  
  // 重新绑定事件处理函数，确保布局切换后点击事件仍然有效
  bindChartEvents()
  
  // 力导向布局已设置为静态模式，无需动画监控
  if (layoutType.value === 'force') {
    console.log('🎯 力导向布局已设置为静态模式，布局将在初始化后保持稳定')
  }
  
  console.log('✅ 图表配置已设置完成，事件已重新绑定')
  console.log('📊 当前图表状态:', {
    isDisposed: chart.value.isDisposed(),
    hasData: option.series[0].data.length > 0,
    layoutType: layoutType.value
  })
}

const loadGraphData = async () => {
  loading.value = true
  console.log('🚀 开始加载知识图谱数据...')
  
  try {
    console.log('📡 调用API: getKnowledgeGraphData')
    const response = await getKnowledgeGraphData({
      node_limit: 100
    })
    
    console.log('✅ API响应成功:', response)
    console.log('📊 响应数据结构:', {
      hasNodes: !!response.nodes,
      nodesCount: response.nodes ? response.nodes.length : 0,
      hasEdges: !!response.edges,
      edgesCount: response.edges ? response.edges.length : 0,
      hasCategories: !!response.categories,
      categoriesCount: response.categories ? response.categories.length : 0,
      responseKeys: Object.keys(response),
      responseType: typeof response
    })
    
    // 详细检查响应数据
    console.log('🔍 API响应原始数据:', JSON.stringify(response, null, 2))
    
    // 检查数据赋值前的状态
    console.log('📋 赋值前graphData状态:', {
      nodesBefore: graphData.nodes.length,
      edgesBefore: graphData.edges.length,
      categoriesBefore: graphData.categories.length
    })
    
    // 修复数据解析：API返回的数据在data字段中
    const responseData = response.data || response
    
    // 确保数据类型一致性：统一转换为字符串类型
    const rawNodes = responseData.nodes || []
    const rawEdges = responseData.edges || []
    
    // 处理节点数据，确保ID为字符串类型并设置正确的category
    graphData.nodes = rawNodes.map((node, index) => {
      // 找到对应的category索引
      const categoryIndex = responseData.categories ? 
        responseData.categories.findIndex(cat => cat.name === node.type) : -1
      
      return {
        ...node,
        id: String(node.id), // 使用后端返回的正确ID
        name: node.name || `节点${index}`,
        type: node.type || 'default',
        category: categoryIndex >= 0 ? categoryIndex : 0, // 设置正确的category索引
        value: node.value || 1,
        // 设置节点颜色，使用getEntityColor函数获取颜色
        itemStyle: {
          color: getEntityColor(node.type || 'default')
        }
      }
    })
    
    // 处理边数据，确保source和target为字符串类型
    graphData.edges = rawEdges.map((edge) => ({
      ...edge,
      source: String(edge.source || ''), // 确保source为字符串
      target: String(edge.target || ''), // 确保target为字符串
      value: edge.value || edge.weight || 1,
      relation: edge.relation || edge.label || '关联'
    }))
    
    graphData.categories = responseData.categories || []
    
    // 检查数据赋值后的状态
    console.log('📈 赋值后graphData状态:', {
      nodesAfter: graphData.nodes.length,
      edgesAfter: graphData.edges.length,
      categoriesAfter: graphData.categories.length,
      nodesType: typeof graphData.nodes,
      nodesIsArray: Array.isArray(graphData.nodes)
    })
    
    console.log('📈 处理后的图谱数据:', {
      nodes: graphData.nodes.length,
      edges: graphData.edges.length,
      categories: graphData.categories.length
    })
    
    if (graphData.nodes.length > 0) {
      console.log('🔍 节点示例:', graphData.nodes.slice(0, 3))
      // 详细检查节点ID的数据类型
      console.log('🆔 节点ID数据类型分析:', {
        firstNodeId: graphData.nodes[0]?.id,
        firstNodeIdType: typeof graphData.nodes[0]?.id,
        allNodeIds: graphData.nodes.slice(0, 5).map(node => ({ id: node.id, type: typeof node.id })),
        nodeIdTypes: [...new Set(graphData.nodes.map(node => typeof node.id))]
      })
    }
    
    if (graphData.edges.length > 0) {
      console.log('🔗 边示例:', graphData.edges.slice(0, 3))
      // 详细检查边的source/target数据类型
      console.log('🔗 边连接数据类型分析:', {
        firstEdgeSource: graphData.edges[0]?.source,
        firstEdgeSourceType: typeof graphData.edges[0]?.source,
        firstEdgeTarget: graphData.edges[0]?.target,
        firstEdgeTargetType: typeof graphData.edges[0]?.target,
        allEdgeConnections: graphData.edges.slice(0, 5).map(edge => ({
          source: edge.source,
          sourceType: typeof edge.source,
          target: edge.target,
          targetType: typeof edge.target
        })),
        edgeSourceTypes: [...new Set(graphData.edges.map(edge => typeof edge.source))],
        edgeTargetTypes: [...new Set(graphData.edges.map(edge => typeof edge.target))]
      })
    }
    
    // 提取实体类型
    entityTypes.value = [...new Set(graphData.nodes.map(node => node.type))]
    console.log('🏷️ 实体类型:', entityTypes.value)
    
    // 数据加载完成后，直接更新图表
    console.log('🎨 开始更新图表...')
    await updateChart()
  } catch (error) {
    console.error('❌ 加载知识图谱数据失败:', error)
    console.error('❌ 错误详情:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    })
    ElMessage.error(`加载知识图谱数据失败: ${error.message}`)
  } finally {
    loading.value = false
    console.log('🏁 数据加载完成')
  }
}

const loadEntityRelationships = async (entityId) => {
  try {
    console.log('🔍 开始加载实体关系，entityId:', entityId)
    const response = await getEntityDetail(entityId)
    console.log('📊 API响应完整数据:', JSON.stringify(response, null, 2))
    console.log('🔗 关系数据详情:', {
      hasRelationships: !!response.data.relationships,
      relationshipsType: typeof response.data.relationships,
      relationshipsLength: response.data.relationships ? response.data.relationships.length : 0,
      relationshipsContent: response.data.relationships
    })
    
    const relationships = response.data.relationships || []
    console.log('📋 准备赋值的关系数据:', relationships)
    entityRelationships.value = relationships
    console.log('✅ 关系数据已赋值，entityRelationships.value:', entityRelationships.value)
    console.log('📈 最终状态检查:', {
      entityRelationshipsLength: entityRelationships.value.length,
      entityRelationshipsContent: entityRelationships.value
    })
  } catch (error) {
    console.error('❌ 加载实体关系失败:', error)
    console.error('❌ 错误详情:', {
      message: error.message,
      stack: error.stack,
      response: error.response
    })
    entityRelationships.value = []
  }
}

// 生命周期
onMounted(() => {
  console.log('🚀 组件已挂载，等待DOM渲染完成...')
  
  // 设置事件监听器
  handleResize = () => {
    if (chart.value && !chart.value.isDisposed()) {
      chart.value.resize()
    }
  }
  
  handleFullscreenChange = () => {
    setTimeout(() => {
      if (chart.value && !chart.value.isDisposed()) {
        chart.value.resize()
      }
    }, 100)
  }
  
  window.addEventListener('resize', handleResize)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  
  // 使用多重延迟确保DOM完全渲染
  nextTick(() => {
    setTimeout(async () => {
      try {
        console.log('✅ DOM渲染完成，开始初始化图表')
        // 先初始化图表，此时loading为false，确保DOM元素有正确尺寸
        await initChart()
        console.log('✅ 图表初始化完成，开始加载数据')
        // 图表初始化完成后再加载数据，此时可以安全地显示loading
        await loadGraphData()
      } catch (error) {
        console.error('❌ 组件初始化失败:', error)
        ElMessage.error(`图表初始化失败: ${error.message}`)
        
        // 如果初始化失败，尝试重新初始化
        setTimeout(async () => {
          try {
            console.log('🔄 尝试重新初始化图表...')
            await initChart()
            await loadGraphData()
          } catch (retryError) {
            console.error('❌ 重新初始化也失败:', retryError)
          }
        }, 1000)
      }
    }, 100) // 额外延迟100ms确保DOM完全渲染
  })
})

onUnmounted(() => {
  if (chart.value) {
    chart.value.dispose()
  }
  // 清理事件监听器
  if (handleResize) {
    window.removeEventListener('resize', handleResize)
  }
  if (handleFullscreenChange) {
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }
})

// 暴露方法给父组件
defineExpose({
  refresh: loadGraphData
})
</script>

<style scoped>
.knowledge-graph-container {
  display: flex;
  height: 600px;
  gap: 20px;
}

.control-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-card {
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-section h6 {
  margin: 0 0 8px 0;
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.action-btn {
  flex: 1;
  justify-content: center;
}



.graph-container {
  flex: 1;
  height: 100%; /* 确保有明确的高度 */
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  position: relative; /* 为loading-overlay提供定位基准 */
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left h3 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.header-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 8px;
}

.graph-content {
  display: flex;
  flex: 1;
  gap: 16px;
  padding: 16px;
}

.chart-canvas {
  flex: 1;
  height: 500px; /* 使用固定高度，避免calc()在loading状态下计算为0 */
  min-height: 400px;
  overflow: hidden; /* 防止内容溢出 */
  position: relative;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  cursor: grab; /* 显示可拖拽光标 */
  /* 确保元素有明确的尺寸 */
  box-sizing: border-box;
  flex-shrink: 0;
}

.legend-panel {
  width: 200px;
  flex-shrink: 0;
}

.legend-card-right {
  height: fit-content;
}

.legend-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-label {
  font-size: 12px;
  color: #606266;
}

.chart-canvas:active {
  cursor: grabbing; /* 拖拽时的光标 */
}

.loading-overlay {
  position: absolute;
  top: 65px; /* 跳过graph-header的高度 */
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  border-radius: 0 0 8px 8px;
}

.loading-icon {
  font-size: 32px;
  color: #409eff;
  margin-bottom: 12px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-weight: 500;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.entity-detail {
  padding: 20px;
}

.entity-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.entity-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.entity-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-weight: 600;
}

.entity-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.description-text {
  line-height: 1.5;
  color: #606266;
}

.relationships-section h5 {
  margin: 0 0 12px 0;
  color: #303133;
  font-weight: 600;
}

.no-relationships {
  color: #909399;
  font-size: 14px;
  text-align: center;
  padding: 20px;
}

.relationships-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relationship-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.relationship-item:hover {
  background-color: #f5f7fa;
  border-color: #409eff;
}

.relationship-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.relationship-target {
  font-weight: 500;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 6px;
}

.relationship-direction {
  font-size: 14px;
  color: #409eff;
  font-weight: bold;
}

.relationship-type {
  font-size: 12px;
  color: #909399;
}

.relationship-arrow {
  color: #409eff;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .knowledge-graph-container {
    flex-direction: column;
    height: auto;
  }
  
  .control-panel {
    width: 100%;
    flex-direction: row;
    overflow-x: auto;
  }
  
  .control-card {
    min-width: 250px;
  }
  
  .graph-container {
    height: 500px;
  }
  
  .graph-content {
    flex-direction: column;
  }
  
  .legend-panel {
    width: 100%;
    order: -1;
  }
  
  .chart-canvas {
    height: 400px;
  }
}
</style>
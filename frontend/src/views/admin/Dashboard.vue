<template>
  <div class="dashboard-container">
    <div class="stats-cards">
      <div class="card">
        <div class="card-icon" style="background-color: #e6f7ff;">
          <i class="bi bi-people-fill" style="color: #1890ff;"></i>
        </div>
        <div class="card-info">
          <span class="label">总员工数</span>
          <span class="value">{{ stats.user_count }}</span>
        </div>
      </div>
      <div class="card">
        <div class="card-icon" style="background-color: #f6ffed;">
          <i class="bi bi-building" style="color: #52c41a;"></i>
        </div>
        <div class="card-info">
          <span class="label">公司总数</span>
          <span class="value">{{ stats.company_count }}</span>
        </div>
      </div>
      <div class="card">
        <div class="card-icon" style="background-color: #fffbe6;">
          <i class="bi bi-diagram-3-fill" style="color: #faad14;"></i>
        </div>
        <div class="card-info">
          <span class="label">部门总数</span>
          <span class="value">{{ stats.department_count }}</span>
        </div>
      </div>
    </div>
    <div class="main-charts-grid">
      <div class="chart-card user-growth-card">
        <div class="chart-header">
          <h4>员工增长趋势</h4>
          <button @click="fetchAnalysis('userGrowth')" class="ai-button" :disabled="analysisLoading.userGrowth">
            <i class="bi bi-robot"></i>
            {{ analysisLoading.userGrowth ? '分析中...' : 'AI智能分析' }}
          </button>
        </div>
        <div ref="userGrowthChartRef" style="height: 300px;"></div>
        <div v-if="analysisLoading.userGrowth" class="analysis-loader"></div>
        <div v-if="analysis.userGrowth" class="analysis-result" v-html="formatAnalysis(analysis.userGrowth)"></div>
      </div>
      <div class="chart-card system-load-card">
        <div class="chart-header">
          <h4>系统资源使用情况</h4>
          <button @click="fetchAnalysis('systemLoad')" class="ai-button" :disabled="analysisLoading.systemLoad">
            <i class="bi bi-robot"></i>
            {{ analysisLoading.systemLoad ? '分析中...' : 'AI智能分析' }}
          </button>
        </div>
        <div ref="systemLoadChartRef" style="height: 300px;"></div>
        <div v-if="analysisLoading.systemLoad" class="analysis-loader"></div>
        <div v-if="analysis.systemLoad" class="analysis-result" v-html="formatAnalysis(analysis.systemLoad)"></div>
      </div>
      <div class="chart-card company-user-card">
        <div class="chart-header">
          <h4>各公司员工数量</h4>
          <button @click="fetchAnalysis('companyUser')" class="ai-button" :disabled="analysisLoading.companyUser">
            <i class="bi bi-robot"></i>
            {{ analysisLoading.companyUser ? '分析中...' : 'AI智能分析' }}
          </button>
        </div>
        <div ref="companyUserChartRef" style="height: 400px;"></div>
        <div v-if="analysisLoading.companyUser" class="analysis-loader"></div>
        <div v-if="analysis.companyUser" class="analysis-result" v-html="formatAnalysis(analysis.companyUser)"></div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import * as echarts from 'echarts';
import adminApi from '@/api/admin';
import { marked } from 'marked';

export default {
  name: 'AdminDashboard',
  setup() {
    const stats = ref({
      user_count: 0,
      company_count: 0,
      department_count: 0,
    });
    const userGrowthChartRef = ref(null);
    const systemLoadChartRef = ref(null);
    const companyUserChartRef = ref(null);

    const chartData = ref({
      userGrowth: null,
      systemLoad: null,
      companyUser: null,
    });

    const analysis = ref({
      userGrowth: '',
      systemLoad: '',
      companyUser: '',
    });

    const analysisLoading = ref({
      userGrowth: false,
      systemLoad: false,
      companyUser: false,
    });

    let userGrowthChartInstance = null;
    let systemLoadChartInstance = null;
    let companyUserChartInstance = null;
    let refreshInterval = null;

    const formatAnalysis = (text) => {
      if (!text) return '';
      // 使用 marked 将 Markdown 格式的文本转换为 HTML
      return marked(text);
    };

    const fetchAnalysis = async (chartName) => {
      const titles = {
        userGrowth: '员工增长趋势',
        systemLoad: '系统资源使用情况',
        companyUser: '各公司员工数量',
      };

      if (!chartData.value[chartName]) {
        console.error('图表数据尚未加载');
        return;
      }

      analysisLoading.value[chartName] = true;
      analysis.value[chartName] = '';

      try {
        const response = await adminApi.getDashboardAnalysis(
          titles[chartName],
          chartData.value[chartName]
        );
        analysis.value[chartName] = response.data.analysis;
      } catch (error) {
        console.error(`获取 ${titles[chartName]} AI分析失败:`, error);
        analysis.value[chartName] = '<p style="color: red;">获取AI分析失败，请稍后重试。</p>';
      } finally {
        analysisLoading.value[chartName] = false;
      }
    };

    const initUserGrowthChart = (data) => {
      chartData.value.userGrowth = data;
      userGrowthChartInstance = echarts.init(userGrowthChartRef.value);

      const series = data.series.map(s => ({
        ...s,
        smooth: true,
        areaStyle: {
          opacity: 0.25
        },
        animationDuration: 1000
      }));

      userGrowthChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: {
          data: data.series.map(s => s.name),
          bottom: 10,
          type: 'scroll'
        },
        grid: { left: '3%', right: '4%', top: '10%', bottom: '15%', containLabel: true },
        xAxis: { type: 'category', data: data.dates },
        yAxis: { type: 'value' },
        series: series
      });
    };

    const initSystemLoadChart = (data) => {
      chartData.value.systemLoad = data;
      systemLoadChartInstance = echarts.init(systemLoadChartRef.value);
      systemLoadChartInstance.setOption({
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}%'
        },
        legend: { top: 'bottom', icon: 'circle' },
        color: ['#5470c6', '#91cc75', '#fac858'],
        series: [
          {
            name: '系统资源',
            type: 'pie',
            radius: ['45%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: true,
              position: 'center',
              formatter: () => {
                if (!chartData.value.systemLoad || chartData.value.systemLoad.length === 0) {
                  return '加载中...';
                }
                return chartData.value.systemLoad.map(item => {
                  const name = item.name.replace('使用率 (%)', '').trim();
                  return `${name}: ${item.value}%`;
                }).join('\n');
              },
              fontSize: '14',
              fontWeight: '600',
              color: '#495057',
              lineHeight: 22,
            },
            emphasis: {
              label: { 
                show: false,
              },
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.2)'
              }
            },
            labelLine: { show: false },
            data: data,
            animationType: 'scale',
            animationEasing: 'elasticOut',
            animationDelay: () => Math.random() * 200
          }
        ]
      });
    };

    const initCompanyUserChart = (data) => {
      chartData.value.companyUser = data;
      companyUserChartInstance = echarts.init(companyUserChartRef.value);

      const series = data.series || [];
      const totals = data.totals || [];

      if (series.length > 0) {
        series[series.length - 1].label = {
          show: true,
          position: 'top',
          formatter: (params) => {
            const total = totals[params.dataIndex];
            return total > 0 ? total : '';
          },
          color: '#464646',
          fontSize: 14,
          fontWeight: 'bold',
        };
      }

      companyUserChartInstance.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        legend: {
          show: true,
          bottom: 10,
          type: 'scroll'
        },
        grid: { left: '3%', right: '4%', top: '10%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.labels,
          axisLabel: { interval: 0, rotate: 30 }
        },
        yAxis: { type: 'value' },
        series: series
      });
    };

    const updateSystemLoadChart = async () => {
      try {
        const response = await adminApi.getDashboardData();
        chartData.value.systemLoad = response.data.system_load;
        if (systemLoadChartInstance) {
          systemLoadChartInstance.setOption({
            series: [{
              data: response.data.system_load
            }]
          });
        }
      } catch (error) {
        console.error("更新系统资源图表失败:", error);
      }
    };

    const fetchDashboardData = async () => {
      try {
        const response = await adminApi.getDashboardData();
        const data = response.data;
        stats.value = data.stats;

        await nextTick();

        if (userGrowthChartRef.value && !userGrowthChartInstance) {
          initUserGrowthChart(data.user_growth);
        }
        if (systemLoadChartRef.value && !systemLoadChartInstance) {
          initSystemLoadChart(data.system_load);
          if (refreshInterval) clearInterval(refreshInterval);
          refreshInterval = setInterval(updateSystemLoadChart, 5000);
        }
        if (companyUserChartRef.value && !companyUserChartInstance) {
          initCompanyUserChart(data.company_user_distribution);
        }
      } catch (error) {
        console.error("获取仪表盘数据失败:", error);
      }
    };

    const resizeCharts = () => {
      userGrowthChartInstance?.resize();
      systemLoadChartInstance?.resize();
      companyUserChartInstance?.resize();
    };

    onMounted(() => {
      fetchDashboardData();
      window.addEventListener('resize', resizeCharts);
    });

    onBeforeUnmount(() => {
      clearInterval(refreshInterval);
      userGrowthChartInstance?.dispose();
      systemLoadChartInstance?.dispose();
      companyUserChartInstance?.dispose();
      window.removeEventListener('resize', resizeCharts);
    });

    return {
      stats,
      userGrowthChartRef,
      systemLoadChartRef,
      companyUserChartRef,
      analysis,
      analysisLoading,
      fetchAnalysis,
      formatAnalysis,
    };
  },
};
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f0f2f5;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.card {
  display: flex;
  align-items: center;
  background-color: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.09);
  transition: all 0.3s ease;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  transform: translateY(-4px);
}

.card-icon {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
}

.card-icon i {
  font-size: 28px;
}

.card-info {
  display: flex;
  flex-direction: column;
}

.card-info .label {
  color: #8c8c8c;
  font-size: 14px;
  margin-bottom: 8px;
}

.card-info .value {
  color: #333;
  font-size: 26px;
  font-weight: 600;
}

.main-charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

@media (min-width: 992px) {
  .main-charts-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .user-growth-card {
    grid-column: span 2;
  }
  .system-load-card {
    grid-column: span 1;
  }
  .company-user-card {
    grid-column: span 3;
  }
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.charts-container-full {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.chart-card {
  background-color: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.09);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.ai-button {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
  padding: 6px 12px;
  border-radius: 16px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.ai-button:hover:not(:disabled) {
  background-color: #dcf1ff;
  border-color: #69c0ff;
}

.ai-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.analysis-loader {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 20px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.analysis-result {
  margin-top: 20px;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.analysis-result :deep(h1),
.analysis-result :deep(h2),
.analysis-result :deep(h3) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
}
.analysis-result :deep(p) {
  margin-bottom: 1em;
}
.analysis-result :deep(ul),
.analysis-result :deep(ol) {
  padding-left: 20px;
}
</style> 
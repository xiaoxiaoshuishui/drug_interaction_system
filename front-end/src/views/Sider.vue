<template>
  <div class="sider-container">
    <div class="control-panel">
      <div class="header">
        <h2>药物不良反应 (DSA)</h2>
        <p class="subtitle">基于 MFGNN-DSA 多视图异质网络</p>
      </div>

      <div class="form-container">
        <div class="form-group">
          <label>药物名称 / SMILES:</label>
          <input 
            v-model="form.drug_identifier" 
            type="text" 
            placeholder="例如: Cetrorelix" 
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label>副作用名称:</label>
          <input 
            v-model="form.se_name" 
            type="text" 
            placeholder="例如: rash" 
            :disabled="loading"
          />
        </div>

        <button class="predict-btn" @click="handlePredict" :disabled="loading">
          {{ loading ? '🌐 图谱特征提取与推理中...' : '开始智能预测' }}
        </button>
      </div>

      <div v-if="errorMessage" class="error-msg">
        ⚠️ {{ errorMessage }}
      </div>

      <div v-if="result" class="result-card">
        <h3>核心预测结论</h3>
        <div class="result-item">
          <span>识别药物:</span>
          <strong>{{ result.drug_name }}</strong> 
          <span class="index-tag">(Idx: {{ result.drug_index }})</span>
        </div>
        <div class="result-item">
          <span>识别副作用:</span>
          <strong>{{ result.se_name }}</strong>
          <span class="index-tag">(Idx: {{ result.se_index }})</span>
        </div>
        
        <div class="divider"></div>

        <div class="result-item">
          <span>系统评级:</span>
          <strong :class="result.prediction === 1 ? 'risk-high' : 'risk-safe'">
            {{ result.prediction === 1 ? '⚠️ 存在不良反应风险' : '✅ 相对安全' }}
          </strong>
        </div>
        <div class="result-item">
          <span>风险概率得分:</span>
          <strong>{{ (result.score * 100).toFixed(2) }}%</strong>
        </div>
      </div>
    </div>

    <div class="visualization-panel" v-show="result">
      
      <div class="chart-box">
        <h3>特征激活强度 (Attention/Norm)</h3>
        <div ref="radarChartRef" class="echarts-container"></div>
      </div>

      <div class="chart-box">
        <h3>局部异质网络拓扑 (Local HIN)</h3>
        <div ref="graphChartRef" class="echarts-container"></div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
// 保持您原本的接口引用路径
import { dsaPredict } from '../apis/dsas';

const form = reactive({
  drug_identifier: '',
  se_name: ''
});

const loading = ref(false);
const result = ref(null);
const errorMessage = ref('');

// ECharts 容器 DOM 引用与实例
const radarChartRef = ref(null);
const graphChartRef = ref(null);
let radarChartInstance = null;
let graphChartInstance = null;

const handlePredict = async () => {
  errorMessage.value = '';
  result.value = null;
  
  if (!form.drug_identifier.trim() || !form.se_name.trim()) {
    errorMessage.value = '请完整填写药物标识和副作用名称！';
    return;
  }

  loading.value = true;
  try {
    const res = await dsaPredict(form.drug_identifier, form.se_name);
    
    if (res && res.success !== false) {
      result.value = res;
      
      // 等待 Vue 将 v-show 的 DOM 渲染出来后，再初始化图表
      await nextTick();
      if (res.radar_data) renderRadar(res.radar_data);
      if (res.graph_data) renderGraph(res.graph_data, res.prediction);
    } else {
      errorMessage.value = res?.error_message || '预测失败，请重试';
    }
  } catch (error) {
    errorMessage.value = error.message || '网络或服务器错误';
  } finally {
    loading.value = false;
  }
};

// ==============================
// ECharts 渲染逻辑
// ==============================

// 渲染雷达图
const renderRadar = (radarData) => {
  if (!radarChartRef.value) return;
  if (!radarChartInstance) radarChartInstance = echarts.init(radarChartRef.value);

  // 解析后端传来的 radar_data
  const indicators = radarData.map(item => ({ 
    name: item.name, 
    max: item.max || undefined 
  }));
  const values = radarData.map(item => item.value);

  const option = {
    tooltip: { trigger: 'item' },
    radar: {
      indicator: indicators,
      shape: 'circle',
      splitNumber: 4,
      axisName: { color: '#495057', fontWeight: 'bold' },
      splitArea: {
        areaStyle: { 
          color: ['#f8f9fa', '#e9ecef', '#dee2e6', '#ced4da'], 
          shadowColor: 'rgba(0, 0, 0, 0.05)', 
          shadowBlur: 10 
        }
      },
      axisLine: { lineStyle: { color: '#adb5bd' } },
      splitLine: { lineStyle: { color: '#adb5bd' } }
    },
    series: [{
      name: '特征贡献度',
      type: 'radar',
      data: [{
        value: values,
        name: '特征激活 L2 Norm',
        itemStyle: { color: '#339af0' },
        areaStyle: { 
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { offset: 0, color: 'rgba(51, 154, 240, 0.1)' },
            { offset: 1, color: 'rgba(51, 154, 240, 0.6)' }
          ])
        }
      }]
    }]
  };
  radarChartInstance.setOption(option);
};

// 渲染力导向知识图谱
const renderGraph = (graphData, prediction) => {
  if (!graphChartRef.value) return;
  if (!graphChartInstance) graphChartInstance = echarts.init(graphChartRef.value);

  // 1=高危风险(红线)，0=安全(绿线)
  const isRisk = prediction === 1;
  const mainLinkColor = isRisk ? '#fa5252' : '#40c057';

  const option = {
    tooltip: { formatter: '{b}' },
    legend: { 
      data: ['当前查询药物', '当前查询副作用', '底层特征相似节点'], 
      bottom: 0 
    },
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph',
      layout: 'force',
      force: { 
        repulsion: 400, 
        edgeLength: 120,
        gravity: 0.1
      },
      roam: true, // 允许鼠标缩放和平移
      label: { show: true, position: 'right', formatter: '{b}' },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [4, 10],
      categories: [
        { name: '当前查询药物', itemStyle: { color: '#4dabf7' } },
        { name: '当前查询副作用', itemStyle: { color: '#ff8787' } },
        { name: '底层特征相似节点', itemStyle: { color: '#ffd43b' } }
      ],
      data: graphData.nodes,
      links: graphData.links.map(link => {
        // 判断是否是主查询节点之间的连线
        const isMainLink = link.source.includes('Drug_') && link.target.includes('SE_');
        return {
          ...link,
          lineStyle: {
            color: isMainLink ? mainLinkColor : '#ced4da',
            width: isMainLink ? 3 : 1,
            curveness: 0.2,
            type: isMainLink ? 'solid' : 'dashed'
          }
        };
      })
    }]
  };
  graphChartInstance.setOption(option);
};

// 监听窗口缩放，自适应图表大小
window.addEventListener('resize', () => {
  if (radarChartInstance) radarChartInstance.resize();
  if (graphChartInstance) graphChartInstance.resize();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', () => {});
  if (radarChartInstance) radarChartInstance.dispose();
  if (graphChartInstance) graphChartInstance.dispose();
});
</script>

<style scoped>
/* 整体双栏容器 */
.sider-container {
  display: flex;
  gap: 24px;
  padding: 24px;
  background-color: #f1f3f5;
  min-height: calc(100vh - 48px);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  align-items: flex-start;
}

/* 左侧控制台 */
.control-panel {
  width: 360px;
  background-color: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

/* 右侧图表区 */
.visualization-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 600px; /* 防止屏幕太小时图表挤压 */
}

.chart-box {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  height: 380px; 
  display: flex;
  flex-direction: column;
}

.chart-box h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #495057;
  border-bottom: 2px solid #f8f9fa;
  padding-bottom: 8px;
}

.echarts-container {
  flex: 1;
  width: 100%;
}

/* 原始表单与卡片样式调整 */
.header { margin-bottom: 24px; }
.header h2 { margin: 0 0 8px 0; font-size: 20px; color: #2c3e50; }
.subtitle { margin: 0; font-size: 13px; color: #6c757d; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: 500; color: #495057; font-size: 14px; }
.form-group input { width: 100%; padding: 10px 12px; border: 1px solid #ced4da; border-radius: 6px; font-size: 14px; box-sizing: border-box; transition: border-color 0.2s; }
.form-group input:focus { outline: none; border-color: #4dabf7; box-shadow: 0 0 0 3px rgba(77, 171, 247, 0.2); }
.predict-btn { width: 100%; padding: 12px; background-color: #228be6; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background-color 0.2s; margin-top: 8px; }
.predict-btn:hover:not(:disabled) { background-color: #1c7ed6; }
.predict-btn:disabled { background-color: #a5d8ff; cursor: not-allowed; }
.error-msg { margin-top: 16px; padding: 12px; background-color: #fff5f5; color: #e03131; border-left: 4px solid #e03131; border-radius: 4px; font-size: 14px; }

.result-card { margin-top: 24px; padding: 16px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; }
.result-card h3 { margin: 0 0 16px 0; font-size: 16px; color: #343a40; border-bottom: 2px solid #e9ecef; padding-bottom: 8px; }
.result-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 14px; }
.result-item span:first-child { color: #868e96; }
.index-tag { font-size: 12px; color: #adb5bd; margin-left: 4px; }
.divider { height: 1px; background-color: #dee2e6; margin: 16px 0; }
.risk-high { color: #e03131; }
.risk-safe { color: #2b8a3e; }
</style>
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
          <input v-model="form.drug_identifier" type="text" placeholder="例如: Cetrorelix(西曲瑞克)" :disabled="loading" />
        </div>

        <div class="form-group">
          <label>副作用名称:</label>
          <input v-model="form.se_name" type="text" placeholder="例如: rash(皮疹)" :disabled="loading" />
        </div>

        <button class="predict-btn" @click="handlePredict" :disabled="loading">
          {{ loading ? '🌐 图谱特征提取与推理中...' : '开始智能预测' }}
        </button>
      </div>

      <div v-if="statusMsg" class="status-msg" :class="statusType">
        {{ statusMsg }}
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
import { ref, reactive, nextTick, onBeforeUnmount, onMounted, watch } from 'vue';
import * as echarts from 'echarts';
import { dsaPredict } from '../apis/dsas';
import { useDsaPredictStore } from '../store/dsa';

const store = useDsaPredictStore();

const form = reactive({
  drug_identifier: store.lastFormData?.drug_identifier || '',
  se_name: store.lastFormData?.se_name || ''
});

const loading = ref(false);
const result = ref(store.lastResult);
const statusMsg = ref('');
const statusType = ref(''); // 可选值：'loading', 'success', 'error'

// ECharts 容器 DOM 引用与实例
const radarChartRef = ref(null);
const graphChartRef = ref(null);
let radarChartInstance = null;
let graphChartInstance = null;

// 组件挂载时从 store 恢复图表
onMounted(async () => {
  if (result.value) {
    await nextTick();

    if (store.lastRadarData) {
      renderRadar(store.lastRadarData);
    }
    if (store.lastGraphData) {
      renderGraph(store.lastGraphData, store.lastPrediction);
    }
  }
});

const handlePredict = async () => {
  statusMsg.value = '';
  
  if (!form.drug_identifier.trim() || !form.se_name.trim()) {
    statusMsg.value = '⚠️ 请完整填写药物和副作用名称！';
    statusType.value = 'error';
    return;
  }

  loading.value = true;
  statusMsg.value = '🔄 预测中...';
  statusType.value = 'loading';
  
  try {
    const res = await dsaPredict(form.drug_identifier, form.se_name);
    
    if (res && res.success !== false) {
      statusMsg.value = '✅ 预测完成！';
      statusType.value = 'success';
      setTimeout(() => {
        if (statusType.value === 'success') statusMsg.value = '';
      }, 3000);
      
      result.value = res;
      store.setResult(res, form);
      
      await nextTick();
      if (res.radar_data) renderRadar(res.radar_data);
      if (res.graph_data) renderGraph(res.graph_data, res.prediction);
    } else {
      statusMsg.value = '❌ ' + (res?.error_message || '预测失败');
      statusType.value = 'error';
    }
  } catch (error) {
    statusMsg.value = '❌ 网络或服务器错误';
    statusType.value = 'error';
  } finally {
    loading.value = false;
  }
};

// 清除历史数据
const clearHistory = () => {
  store.clearResult();
  result.value = null;
  form.drug_identifier = '';
  form.se_name = '';

  // 销毁图表实例
  if (radarChartInstance) {
    radarChartInstance.dispose();
    radarChartInstance = null;
  }
  if (graphChartInstance) {
    graphChartInstance.dispose();
    graphChartInstance = null;
  }
};

// 渲染雷达图
const renderRadar = (radarData) => {
  if (!radarChartRef.value) return;
  if (!radarChartInstance) radarChartInstance = echarts.init(radarChartRef.value);

  const indicators = radarData.map(item => ({
    name: item.name,
    max: 1,
  }));

  const values = radarData.map(item => item.value);

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: function (params) {
        // 自定义 formatter：将 indicator 的名称与 params.value 数组中的值一一对应
        let result = `<strong>${params.name || '特征激活强度'}</strong><br/>`;
        indicators.forEach((indicator, index) => {
          result += `${indicator.name}: ${params.value[index]}<br/>`;
        });
        return result;
      }
    },
    radar: {
      indicator: indicators,
      shape: 'circle',
      splitNumber: 4,
      center: ['50%', '50%'],
      radius: '65%',
      axisName: {
        color: '#495057',
        fontSize: 11
      },
      splitArea: {
        areaStyle: {
          color: ['#f8f9fa', '#e9ecef']
        }
      },
      axisLabel: {
        formatter: (value) => value.toFixed(2)
      }
    },
    series: [{
      type: 'radar',
      data: [{
        name: '特征激活强度', // 👈 增加数据组的名称
        value: values,
        areaStyle: {
          color: 'rgba(51, 154, 240, 0.3)'
        },
        lineStyle: {
          color: '#339af0',
          width: 2
        },
        itemStyle: {
          color: '#228be6'
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
      roam: true,
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

// 窗口缩放处理
const handleResize = () => {
  if (radarChartInstance) radarChartInstance.resize();
  if (graphChartInstance) graphChartInstance.resize();
};

window.addEventListener('resize', handleResize);

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (radarChartInstance) {
    radarChartInstance.dispose();
    radarChartInstance = null;
  }
  if (graphChartInstance) {
    graphChartInstance.dispose();
    graphChartInstance = null;
  }
});

// 暴露方法给模板使用
defineExpose({
  clearHistory
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
  justify-content: center;
  /* 未渲染图表时，内容整体居中 */
}

/* 左侧控制台 */
.control-panel {
  width: 360px;
  background-color: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  transition: margin 0.3s ease;
  /* 平滑过渡 */
}

/* 右侧图表区 */
.visualization-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 700px;
  /* 增加最小宽度，给图表更多空间 */
}

/* 图表盒子 - 双栏布局 */
.chart-box {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

/* 特征激活强度图 - 高度稍小 */
.chart-box:first-child {
  height: 320px;
  /* 减小高度 */
}

/* 局部异质网络拓扑图 - 高度增大，获得更多空间 */
.chart-box:last-child {
  height: 500px;
  /* 增大高度，让网络拓扑图有更多展示空间 */
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
.header {
  margin-bottom: 24px;
}

.header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #2c3e50;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #6c757d;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #4dabf7;
  box-shadow: 0 0 0 3px rgba(77, 171, 247, 0.2);
}

.predict-btn {
  width: 100%;
  padding: 12px;
  background-color: #228be6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 8px;
}

.predict-btn:hover:not(:disabled) {
  background-color: #1c7ed6;
}

.predict-btn:disabled {
  background-color: #a5d8ff;
  cursor: not-allowed;
}

.status-msg { margin-top: 16px; padding: 10px 12px; border-radius: 4px; font-size: 14px; font-weight: 500; }
.status-msg.error { background-color: #fff5f5; color: #e03131; border-left: 4px solid #e03131; }
.status-msg.loading { background-color: #e7f5ff; color: #1971c2; border-left: 4px solid #339af0; }
.status-msg.success { background-color: #ebfbee; color: #2b8a3e; border-left: 4px solid #40c057; }

.result-card {
  margin-top: 24px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.result-card h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #343a40;
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 8px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
}

.result-item span:first-child {
  color: #868e96;
}

.index-tag {
  font-size: 12px;
  color: #adb5bd;
  margin-left: 4px;
}

.divider {
  height: 1px;
  background-color: #dee2e6;
  margin: 16px 0;
}

.risk-high {
  color: #e03131;
}

.risk-safe {
  color: #2b8a3e;
}
</style>
<template>
  <div class="dsa-wrapper">
    <van-tabs v-model:active="activeTab" type="card" color="#228be6" class="main-tabs">

      <van-tab title="单条精准预测">
        <div class="sider-container">
          <div class="control-panel">
            <div class="header">
              <h2>药物不良反应 (DSA)</h2>
              <p class="subtitle">基于 MFGNN-DSA 多视图异质网络</p>
            </div>

            <div class="form-container">
              <div class="form-group relative-wrap">
                <label>药物名称 / SMILES:</label>
                <input v-model="form.drug_identifier" type="text" placeholder="例如: Cetrorelix(西曲瑞克)" :disabled="loading"
                  @input="onDrugInput" @focus="showDrugList = true" @blur="hideDrugList" autocomplete="off" />
                <ul class="suggestion-list" v-show="showDrugList && drugSuggestions.length > 0">
                  <li v-for="(item, index) in drugSuggestions" :key="index" @mousedown="selectDrug(item)">
                    <span class="main-text">{{ item.value }}</span>
                    <span class="sub-text" v-if="item.smiles" :title="item.smiles">{{ item.smiles.substring(0, 15)
                      }}...</span>
                  </li>
                </ul>
              </div>

              <div class="form-group relative-wrap">
                <label>副作用名称:</label>
                <input v-model="form.se_name" type="text" placeholder="例如: rash(皮疹)" :disabled="loading"
                  @input="onSeInput" @focus="showSeList = true" @blur="hideSeList" autocomplete="off" />
                <ul class="suggestion-list" v-show="showSeList && seSuggestions.length > 0">
                  <li v-for="(item, index) in seSuggestions" :key="index" @mousedown="selectSe(item)">
                    <span class="main-text">{{ item.value }}</span>
                    <span class="sub-text" v-if="item.en_name">{{ item.en_name }}</span>
                  </li>
                </ul>
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
      </van-tab>

      <van-tab title="批量极速筛查">
        <div class="batch-container">
          <div class="batch-header">
            <h2>批量数据导入</h2>
          </div>

          <div class="batch-layout">
            <div class="batch-form-area">
              <div class="batch-scroll-box">
                <div v-for="(item, index) in batchForm" :key="index" class="batch-row-card">
                  <div class="batch-row-header">
                    <span>💊 预测组合 #{{ index + 1 }}</span>
                    <span class="delete-btn" @click="removeRow(index)" v-if="batchForm.length > 1">✖ 删除</span>
                  </div>
                  <div class="batch-inputs">
                    <div class="form-group relative-wrap" style="margin-bottom: 0;">
                      <input v-model="item.drug_identifier" placeholder="药物名称或 SMILES" @input="onBatchDrugInput(index)"
                        @focus="onBatchFocus(index, 'drug')" @blur="hideBatchList" autocomplete="off" />
                      <ul class="suggestion-list"
                        v-show="activeBatchRow === index && activeBatchField === 'drug' && batchDrugSuggestions.length > 0">
                        <li v-for="(sug, sIdx) in batchDrugSuggestions" :key="sIdx"
                          @mousedown="selectBatchDrug(index, sug)">
                          <span class="main-text">{{ sug.value }}</span>
                          <span class="sub-text" v-if="sug.smiles" :title="sug.smiles">{{ sug.smiles.substring(0, 10)
                            }}...</span>
                        </li>
                      </ul>
                    </div>

                    <div class="form-group relative-wrap" style="margin-bottom: 0;">
                      <input v-model="item.se_name" placeholder="副作用名称" @input="onBatchSeInput(index)"
                        @focus="onBatchFocus(index, 'se')" @blur="hideBatchList" autocomplete="off" />
                      <ul class="suggestion-list"
                        v-show="activeBatchRow === index && activeBatchField === 'se' && batchSeSuggestions.length > 0">
                        <li v-for="(sug, sIdx) in batchSeSuggestions" :key="sIdx"
                          @mousedown="selectBatchSe(index, sug)">
                          <span class="main-text">{{ sug.value }}</span>
                          <span class="sub-text" v-if="sug.en_name">{{ sug.en_name }}</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div class="batch-actions">
                <button class="add-btn" @click="addRow">➕ 添加一行组合</button>
                <button class="predict-btn" @click="submitBatch" :disabled="batchLoading">
                  {{ batchLoading ? '🚀 矩阵批量运算中...' : `🚀 提交批量预测 (共 ${batchForm.length} 条)` }}
                </button>
              </div>
            </div>

            <div class="batch-result-area">
              <h3>预测结果看板</h3>
              <div v-if="batchResults.length === 0" class="empty-results">
                等待提交预测...
              </div>
              <div v-else class="batch-results-list">
                <div v-for="(res, idx) in batchResults" :key="idx" class="batch-res-item">
                  <div class="res-pair">
                    <strong>{{ res.drug_name || res.drug_identifier }}</strong>
                    <van-icon name="arrow" class="arrow-icon" />
                    <strong style="color: #495057;">{{ res.se_name_cn || res.se_name }}</strong>
                  </div>
                  <div class="res-outcome">
                    <span :class="res.risk_level === 'High' ? 'risk-high' : 'risk-safe'" style="font-weight: bold;">
                      {{ res.risk_level === 'High' ? '高风险' : '安全' }}
                    </span>
                    <span class="res-score">得分: {{ res.score?.toFixed(4) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onBeforeUnmount, onMounted } from 'vue';
import * as echarts from 'echarts';
import { showToast, showSuccessToast, showFailToast } from 'vant';

import { dsaPredict, searchDsaDrugs, searchDsaSideEffects, predictDsaBatch } from '../apis/dsas';
import { useDsaPredictStore } from '../store/dsa';

const store = useDsaPredictStore();

const activeTab = ref(0);

const form = reactive({
  drug_identifier: store.lastFormData?.drug_identifier || '',
  se_name: store.lastFormData?.se_name || ''
});
const loading = ref(false);
const result = ref(store.lastResult);
const statusMsg = ref('');
const statusType = ref('');
const radarChartRef = ref(null);
const graphChartRef = ref(null);
let radarChartInstance = null;
let graphChartInstance = null;
const showDrugList = ref(false);
const showSeList = ref(false);
const drugSuggestions = ref([]);
const seSuggestions = ref([]);
let drugTimer = null;
let seTimer = null;

onMounted(async () => {
  if (result.value) {
    await nextTick();
    if (store.lastRadarData) renderRadar(store.lastRadarData);
    if (store.lastGraphData) renderGraph(store.lastGraphData, store.lastPrediction);
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
      setTimeout(() => { if (statusType.value === 'success') statusMsg.value = ''; }, 3000);
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

const clearHistory = () => {
  store.clearResult();
  result.value = null;
  form.drug_identifier = '';
  form.se_name = '';
  if (radarChartInstance) { radarChartInstance.dispose(); radarChartInstance = null; }
  if (graphChartInstance) { graphChartInstance.dispose(); graphChartInstance = null; }
};

const renderRadar = (radarData) => {
  if (!radarChartRef.value) return;
  if (!radarChartInstance) radarChartInstance = echarts.init(radarChartRef.value);
  const indicators = radarData.map(item => ({ name: item.name, max: 1 }));
  const values = radarData.map(item => item.value);
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: function (params) {
        let result = `<strong>${params.name || '特征激活强度'}</strong><br/>`;
        indicators.forEach((indicator, index) => { result += `${indicator.name}: ${params.value[index]}<br/>`; });
        return result;
      }
    },
    radar: {
      indicator: indicators, shape: 'circle', splitNumber: 4, center: ['50%', '50%'], radius: '65%',
      axisName: { color: '#495057', fontSize: 11 }, splitArea: { areaStyle: { color: ['#f8f9fa', '#e9ecef'] } },
      axisLabel: { formatter: (value) => value.toFixed(2) }
    },
    series: [{ type: 'radar', data: [{ name: '特征激活强度', value: values, areaStyle: { color: 'rgba(51, 154, 240, 0.3)' }, lineStyle: { color: '#339af0', width: 2 }, itemStyle: { color: '#228be6' } }] }]
  };
  radarChartInstance.setOption(option);
};

const renderGraph = (graphData, prediction) => {
  if (!graphChartRef.value) return;
  if (!graphChartInstance) graphChartInstance = echarts.init(graphChartRef.value);
  const isRisk = prediction === 1;
  const mainLinkColor = isRisk ? '#fa5252' : '#40c057';
  const option = {
    tooltip: { formatter: '{b}' }, legend: { data: ['当前查询药物', '当前查询副作用', '底层特征相似节点'], bottom: 0 },
    animationDurationUpdate: 1500, animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph', layout: 'force', force: { repulsion: 400, edgeLength: 120, gravity: 0.1 }, roam: true,
      label: { show: true, position: 'right', formatter: '{b}' }, edgeSymbol: ['none', 'arrow'], edgeSymbolSize: [4, 10],
      categories: [{ name: '当前查询药物', itemStyle: { color: '#4dabf7' } }, { name: '当前查询副作用', itemStyle: { color: '#ff8787' } }, { name: '底层特征相似节点', itemStyle: { color: '#ffd43b' } }],
      data: graphData.nodes,
      links: graphData.links.map(link => {
        const isMainLink = link.source.includes('Drug_') && link.target.includes('SE_');
        return { ...link, lineStyle: { color: isMainLink ? mainLinkColor : '#ced4da', width: isMainLink ? 3 : 1, curveness: 0.2, type: isMainLink ? 'solid' : 'dashed' } };
      })
    }]
  };
  graphChartInstance.setOption(option);
};

const handleResize = () => {
  if (radarChartInstance) radarChartInstance.resize();
  if (graphChartInstance) graphChartInstance.resize();
};
window.addEventListener('resize', handleResize);

const onDrugInput = () => {
  showDrugList.value = true;
  if (drugTimer) clearTimeout(drugTimer);
  const keyword = form.drug_identifier.trim();
  if (!keyword) { drugSuggestions.value = []; return; }
  drugTimer = setTimeout(async () => {
    const res = await searchDsaDrugs(keyword);
    if (res && res.data) drugSuggestions.value = res.data;
  }, 300);
};

const onSeInput = () => {
  showSeList.value = true;
  if (seTimer) clearTimeout(seTimer);
  const keyword = form.se_name.trim();
  if (!keyword) { seSuggestions.value = []; return; }
  seTimer = setTimeout(async () => {
    const res = await searchDsaSideEffects(keyword);
    if (res && res.data) seSuggestions.value = res.data;
  }, 300);
};

const selectDrug = (item) => { form.drug_identifier = item.identifier; showDrugList.value = false; };
const selectSe = (item) => { form.se_name = item.value; showSeList.value = false; };
const hideDrugList = () => { showDrugList.value = false; };
const hideSeList = () => { showSeList.value = false; };


const batchLoading = ref(false);
const batchForm = ref([
  { drug_identifier: '', se_name: '' },
  { drug_identifier: '', se_name: '' }
]);
const batchResults = ref([]);

// 记录当前聚焦的是哪一行的哪一个输入框
const activeBatchRow = ref(-1);
const activeBatchField = ref(''); // 'drug' 或 'se'

// 批量专用的下拉联想数据和定时器
const batchDrugSuggestions = ref([]);
const batchSeSuggestions = ref([]);
let batchDrugTimer = null;
let batchSeTimer = null;

// 当输入框获得焦点时
const onBatchFocus = (index, field) => {
  activeBatchRow.value = index;
  activeBatchField.value = field;
  // 聚焦时清空之前的联想残留
  if (field === 'drug') batchDrugSuggestions.value = [];
  if (field === 'se') batchSeSuggestions.value = [];
};

// 失去焦点时隐藏 (使用 setTimeout 防止 blur 先于 mousedown 触发导致无法点击列表)
const hideBatchList = () => {
  setTimeout(() => {
    activeBatchRow.value = -1;
    activeBatchField.value = '';
  }, 150);
};

// 批量：药物输入防抖处理
const onBatchDrugInput = (index) => {
  if (batchDrugTimer) clearTimeout(batchDrugTimer);
  
  const keyword = batchForm.value[index].drug_identifier.trim();
  if (!keyword) {
    batchDrugSuggestions.value = [];
    return;
  }
  
  batchDrugTimer = setTimeout(async () => {
    const res = await searchDsaDrugs(keyword);
    if (res && res.data) batchDrugSuggestions.value = res.data;
  }, 300);
};

// 批量：副作用输入防抖处理
const onBatchSeInput = (index) => {
  if (batchSeTimer) clearTimeout(batchSeTimer);
  
  const keyword = batchForm.value[index].se_name.trim();
  if (!keyword) {
    batchSeSuggestions.value = [];
    return;
  }
  
  batchSeTimer = setTimeout(async () => {
    const res = await searchDsaSideEffects(keyword);
    if (res && res.data) batchSeSuggestions.value = res.data;
  }, 300);
};

// 批量：选中下拉药物
const selectBatchDrug = (index, item) => {
  batchForm.value[index].drug_identifier = item.identifier; // 填充名字或SMILES
  batchDrugSuggestions.value = []; // 清空联想
};

// 批量：选中下拉副作用
const selectBatchSe = (index, item) => {
  batchForm.value[index].se_name = item.value;
  batchSeSuggestions.value = [];
};

const addRow = () => {
  if (batchForm.value.length >= 10) {
    showToast('手填建议不超过10条');
    return;
  }
  batchForm.value.push({ drug_identifier: '', se_name: '' });
};

const removeRow = (index) => {
  batchForm.value.splice(index, 1);
};

const submitBatch = async () => {
  const validPairs = batchForm.value.filter(item => item.drug_identifier.trim() && item.se_name.trim());
  if (validPairs.length === 0) {
    showToast('请至少填写一组完整的药物和副作用');
    return;
  }
  batchLoading.value = true;
  batchResults.value = [];
  try {
    const res = await predictDsaBatch({ pairs: validPairs });

    if (res.code === 200 || res.success) {
      showSuccessToast(`成功预测 ${res.data.length} 条`);
      batchResults.value = res.data;
    } else {
      showFailToast(res.message || '批量预测包含错误');
      if (res.data) batchResults.value = res.data;
    }
  } catch (error) {
    showFailToast('批量预测请求失败');
    console.error(error);
  } finally {
    batchLoading.value = false;
  }
};

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (radarChartInstance) { radarChartInstance.dispose(); radarChartInstance = null; }
  if (graphChartInstance) { graphChartInstance.dispose(); graphChartInstance = null; }
});

defineExpose({ clearHistory });
</script>

<style scoped>
.dsa-wrapper {
  background-color: #f1f3f5;
  min-height: calc(100vh - 48px);
  padding: 16px;
}

.main-tabs :deep(.van-tabs__nav--card) {
  margin: 0 auto 20px;
  width: 400px;
}

.sider-container {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  justify-content: center;
}

.control-panel {
  width: 360px;
  background-color: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.visualization-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 700px;
}

.chart-box {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.chart-box:first-child {
  height: 320px;
}

.chart-box:last-child {
  height: 500px;
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

.status-msg {
  margin-top: 16px;
  padding: 10px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.status-msg.error {
  background-color: #fff5f5;
  color: #e03131;
  border-left: 4px solid #e03131;
}

.status-msg.loading {
  background-color: #e7f5ff;
  color: #1971c2;
  border-left: 4px solid #339af0;
}

.status-msg.success {
  background-color: #ebfbee;
  color: #2b8a3e;
  border-left: 4px solid #40c057;
}

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

.relative-wrap {
  position: relative;
}

.suggestion-list {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  max-height: 200px;
  overflow-y: auto;
  background-color: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin: 4px 0 0 0;
  padding: 0;
  list-style: none;
  z-index: 1000;
}

.suggestion-list li {
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f8f9fa;
  transition: background-color 0.2s;
}

.suggestion-list li:last-child {
  border-bottom: none;
}

.suggestion-list li:hover {
  background-color: #f1f3f5;
}

.suggestion-list .main-text {
  font-size: 14px;
  color: #343a40;
  font-weight: 500;
}

.suggestion-list .sub-text {
  font-size: 12px;
  color: #adb5bd;
  font-family: monospace;
}

/* ================= 新增：批量模式样式 ================= */
.batch-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1000px;
  margin: 0 auto;
}

.batch-header {
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.batch-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #2c3e50;
}

.batch-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.batch-form-area {
  flex: 1;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.batch-scroll-box {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

.batch-scroll-box::-webkit-scrollbar {
  width: 6px;
}

.batch-scroll-box::-webkit-scrollbar-thumb {
  background: #dee2e6;
  border-radius: 3px;
}

.batch-row-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background-color: #f8f9fa;
}

.batch-row-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.delete-btn {
  color: #fa5252;
  font-size: 12px;
  cursor: pointer;
}

.batch-inputs {
  display: flex;
  gap: 12px;
}

.batch-inputs .form-group {
  flex: 1;
}

.batch-actions {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-btn {
  width: 100%;
  padding: 10px;
  background-color: white;
  color: #228be6;
  border: 1px dashed #228be6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  background-color: #e7f5ff;
}

.batch-result-area {
  flex: 1;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  min-height: 400px;
}

.batch-result-area h3 {
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #e9ecef;
}

.empty-results {
  text-align: center;
  color: #adb5bd;
  margin-top: 60px;
  font-size: 14px;
}

.batch-results-list {
  max-height: 500px;
  overflow-y: auto;
}

.batch-res-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f1f3f5;
}

.res-pair {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.arrow-icon {
  color: #adb5bd;
}

.res-outcome {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.res-score {
  font-size: 12px;
  color: #868e96;
}
</style>
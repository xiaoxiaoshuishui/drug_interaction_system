<template>
  <div class="prediction-container">
    <div class="page-header">
      <h2>药物相互作用预测 (DDI)</h2>
      <p class="subtitle">基于 DSN-DDI 模型的药物相互作用分析</p>
    </div>

    <van-tabs v-model:active="activeTab" type="card" color="#4361ee" class="main-tabs">
      
      <van-tab title="单条分析">
        <div class="single-mode-wrapper">
          <div class="input-section">
            <h3>输入药物信息</h3>
            <div class="form-grid">
              <div class="form-group">
                <label>药物A名称</label>
                <input type="text" v-model="formData.drug_a_name" placeholder="请输入药物A名称" class="form-input" />
              </div>
              <div class="form-group">
                <label>药物B名称</label>
                <input type="text" v-model="formData.drug_b_name" placeholder="请输入药物B名称" class="form-input" />
              </div>
              <div class="form-group">
                <label>药物A SMILES *</label>
                <input type="text" v-model="formData.smiles_a" placeholder="请输入药物A的SMILES字符串" class="form-input" />
              </div>
              <div class="form-group">
                <label>药物B SMILES *</label>
                <input type="text" v-model="formData.smiles_b" placeholder="请输入药物B的SMILES字符串" class="form-input" />
              </div>

              <div class="form-group full-width">
                <label>反应类型</label>
                <select v-model="formData.interaction_type_id" class="form-select">
                  <option value="">请选择反应类型（可选）</option>
                  <option v-for="(reactionText, typeId) in REACTION_TYPE_MAP" :key="typeId" :value="Number(typeId)">
                    {{ typeId }}. {{ reactionText }}
                  </option>
                </select>
                <div class="select-arrow">▼</div>
              </div>

              <div class="form-group full-width">
                <button class="btn-predict" @click="handlePredict" :disabled="loading">
                  <span v-if="!loading">开始预测</span>
                  <van-loading v-else type="spinner" size="20px">深度图谱提取中...</van-loading>
                </button>
              </div>
            </div>
          </div>

          <div v-if="predictionResult" class="result-section">
            <h3>预测结果</h3>

            <div class="result-card" :class="getResultClass(predictionResult.prediction)">
              <div class="result-header">
                <span class="result-label">预测结果：</span>
                <span class="result-value">{{ predictionResult.prediction }}</span>
              </div>
              <div class="confidence-badge" :class="predictionResult.confidence">
                {{ getConfidenceText(predictionResult.confidence) }}
              </div>
            </div>

            <div class="probability-card">
              <div class="probability-header">
                <span class="label">相互作用概率</span>
                <span class="value">{{ formatProbability(predictionResult.probability) }}</span>
              </div>
              <div class="probability-bar">
                <div class="probability-fill" :style="{ width: getProbabilityPercentage(predictionResult.probability) + '%' }"></div>
              </div>
            </div>

            <div class="drug-info-grid">
              <div class="drug-card">
                <h4>药物A: {{ predictionResult.drug_a_info.name }}</h4>
                <div class="drug-details">
                  <p><span class="label">SMILES:</span> <span class="smiles-text" :title="predictionResult.drug_a_info.smiles">{{ predictionResult.drug_a_info.smiles }}</span></p>
                  <p><span class="label">原子数量:</span> {{ predictionResult.drug_a_info.num_atoms }}</p>
                  <p><span class="label">键数量:</span> {{ predictionResult.drug_a_info.num_bonds }}</p>
                </div>
              </div>
              <div class="drug-card">
                <h4>药物B: {{ predictionResult.drug_b_info.name }}</h4>
                <div class="drug-details">
                  <p><span class="label">SMILES:</span> <span class="smiles-text" :title="predictionResult.drug_b_info.smiles">{{ predictionResult.drug_b_info.smiles }}</span></p>
                  <p><span class="label">原子数量:</span> {{ predictionResult.drug_b_info.num_atoms }}</p>
                  <p><span class="label">键数量:</span> {{ predictionResult.drug_b_info.num_bonds }}</p>
                </div>
              </div>
            </div>

            <div v-if="predictionResult?.attention_analysis" class="attention-section">
              <h4>🔬 注意力机制分析 - 原子重要性可视化</h4>
              <div class="attention-visualization">
                <div class="molecule-row">
                  <AttentionMoleculeViewer :smiles="predictionResult.drug_a_info.smiles" :drug-name="predictionResult.drug_a_info.name" drug-label="药物 A" :atom-weights="getAtomWeightsForDrug('A')" :height="300" />
                  <AttentionMoleculeViewer :smiles="predictionResult.drug_b_info.smiles" :drug-name="predictionResult.drug_b_info.name" drug-label="药物 B" :atom-weights="getAtomWeightsForDrug('B')" :height="300" />
                </div>
              </div>
              <div class="attention-matrix">
                <h5>注意力权重矩阵热力图</h5>
                <div class="matrix-container">
                  <div v-for="(row, i) in attentionMatrix" :key="i" class="matrix-row">
                    <div v-for="(value, j) in row" :key="j" class="matrix-cell" :style="{ backgroundColor: getMatrixColor(value) }" :title="`药物A[${i}] ↔ 药物B[${j}]: ${value.toFixed(4)}`">
                      <span class="cell-value">{{ value.toFixed(2) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- <div v-if="predictionResult.layer_activations" class="layer-section">
                <h4>网络层激活信息</h4>
                <div class="layer-grid">
                  <div v-for="layer in predictionResult.layer_activations" :key="layer.layer_name" class="layer-card">
                    <h5>{{ layer.layer_name }}</h5>
                    <div class="layer-details">
                      <p v-if="layer.shape"><span class="label">形状:</span> {{ layer.shape.join(' × ') }}</p>
                      <p v-if="layer.value_range"><span class="label">值范围:</span> [{{ layer.value_range[0].toFixed(2) }}, {{ layer.value_range[1].toFixed(2) }}]</p>
                      <p v-if="layer.mean !== null && layer.mean !== undefined"><span class="label">均值:</span> {{ layer.mean.toFixed(4) }}</p>
                    </div>
                  </div>
                </div>
              </div> -->
              <div class="model-info">
                <div class="info-item"><span class="label">使用模型：</span><span class="value">{{ predictionResult.model_used }}</span></div>
                <div class="info-item"><span class="label">处理时间：</span><span class="value">{{ predictionResult.processing_time_ms }} ms</span></div>
                <div class="info-item"><span class="label">时间戳：</span><span class="value">{{ formatTimestamp(predictionResult.timestamp) }}</span></div>
              </div>
            </div>
          </div>
        </div>
      </van-tab>

      <van-tab title="批量筛查">
        <div class="batch-layout">
          <div class="batch-form-area">
            <div class="batch-header-info">
              <h3>批量数据导入 <span style="font-size: 13px; color: #666; font-weight: normal;"></span></h3>
            </div>
            <div class="batch-scroll-box">
              <div v-for="(item, index) in batchForm" :key="index" class="batch-row-card">
                <div class="batch-row-header">
                  <span>🧪 药物组合 #{{ index + 1 }}</span>
                  <span class="delete-btn" @click="removeBatchRow(index)" v-if="batchForm.length > 1">✖ 删除</span>
                </div>
                
                <div class="batch-inputs-grid">
                  <div class="form-group mini-group">
                    <input v-model="item.drug_a_name" placeholder="药物A 名称" class="form-input mini-input" />
                  </div>
                  <div class="form-group mini-group">
                    <input v-model="item.smiles_a" placeholder="SMILES A *" class="form-input mini-input" />
                  </div>
                  
                  <div class="form-group mini-group">
                    <input v-model="item.drug_b_name" placeholder="药物B 名称" class="form-input mini-input" />
                  </div>
                  <div class="form-group mini-group">
                    <input v-model="item.smiles_b" placeholder="SMILES B *" class="form-input mini-input" />
                  </div>

                  <div class="form-group mini-group full-width-mini">
                    <select v-model="item.interaction_type_id" class="form-select mini-input">
                      <option value="">默认类型 (0)</option>
                      <option v-for="(reactionText, typeId) in REACTION_TYPE_MAP" :key="typeId" :value="Number(typeId)">
                        {{ typeId }}. {{ reactionText.substring(0, 15) }}...
                      </option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div class="batch-actions">
              <button class="add-btn" @click="addBatchRow">➕ 添加一组新药物</button>
              <button class="btn-predict" style="max-width: 100%; margin-top: 12px;" @click="submitBatch" :disabled="batchLoading">
                <span v-if="!batchLoading">🚀 提交批量预测 (共 {{ batchForm.length }} 条)</span>
                <span v-else>🚀 GPU 矩阵运算中...</span>
              </button>
            </div>
          </div>

          <div class="batch-result-area">
            <h3>预测结果看板</h3>
            <div v-if="batchResults.length === 0" class="empty-results">
              <van-empty description="暂无预测结果，请在左侧添加数据并提交" />
            </div>
            <div v-else class="batch-results-list">
              <div v-for="(res, idx) in batchResults" :key="idx" class="batch-res-item">
                <div class="res-pair-header">
                  <span class="drug-name-badge">{{ truncateName(res.drug_a_name || 'Drug A') }}</span>
                  <van-icon name="exchange" class="exchange-icon" />
                  <span class="drug-name-badge">{{ truncateName(res.drug_b_name || 'Drug B') }}</span>
                </div>
                
                <div class="res-pair-smiles" :title="res.smiles_a + '\n' + res.smiles_b">
                  {{ truncateSmiles(res.smiles_a) }}<br/>{{ truncateSmiles(res.smiles_b) }}
                </div>

                <div class="res-outcome">
                  <div class="outcome-left">
                    <van-tag :type="res.risk_level === 'High' ? 'danger' : 'success'" size="medium">
                      {{ res.risk_level === 'High' ? '⚠️ 存在风险' : '✅ 安全' }}
                    </van-tag>
                  </div>
                  <div class="outcome-right">
                    <span class="res-score">发生概率: {{ (res.score * 100).toFixed(2) }}%</span>
                  </div>
                </div>
                
                <div v-if="!res.success" class="res-error">
                  ❌ 预测失败: {{ res.error_message }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </van-tab>

    </van-tabs>

    <van-toast v-model:show="showError" type="fail" :message="errorMessage" />
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { showToast, showSuccessToast, showFailToast } from 'vant'
import { standardPredict, batchPredict } from '../apis/ddis' 
import { useDdiStore } from '../store/ddi'
import { REACTION_TYPE_MAP } from '../utils/reactionType'
import AttentionMoleculeViewer from '../components/AttentionMoleculeViewer.vue'

// === 顶层状态 ===
const activeTab = ref(0)
const showError = ref(false)
const errorMessage = ref('')

const loading = ref(false)
const ddiStore = useDdiStore()
const formData = ddiStore.formData.drug_a_name ? reactive(ddiStore.formData) : reactive({
  smiles_a: 'OC(C(=O)O[C@H]1C[N+]2(CCCOC3=CC=CC=C3)CCC1CC2)(C1=CC=CS1)C1=CC=CS1',
  smiles_b: 'C[N+]1(C)[C@H]2C[C@@H](C[C@@H]1[C@H]1O[C@@H]21)OC(=O)[C@H](CO)C1=CC=CC=C1',
  drug_a_name: '阿地溴铵',
  drug_b_name: '甲基东莨菪碱',
  interaction_type_id: '0'
})

const predictionResult = ref(ddiStore.predictionResult || null);

const handlePredict = async () => {
  if (!formData.smiles_a || !formData.smiles_b) {
    showToast('请输入药物SMILES字符串')
    return
  }
  const params = { ...formData }
  if (!params.interaction_type_id) delete params.interaction_type_id

  loading.value = true
  showError.value = false

  try {
    const result = await standardPredict(params)
    predictionResult.value = result
    ddiStore.predictionResult = result;
    ddiStore.formData = { ...formData };
    showSuccessToast('预测完成')
  } catch (error) {
    errorMessage.value = error.message || '预测失败，请重试'
    showError.value = true
  } finally {
    loading.value = false
  }
}

// 辅助方法 (样式、转换等)
const getResultClass = (prediction) => {
  if (prediction.includes('No Interaction') || prediction.includes('安全')) return 'result-safe'
  if (prediction.includes('Interaction') || prediction.includes('相互作用')) return 'result-danger'
  return 'result-warning'
}
const getConfidenceText = (confidence) => {
  const map = { 'high': '高置信度', 'medium': '中等置信度', 'low': '低置信度' }
  return map[confidence] || confidence
}
const formatProbability = (prob) => (prob < 0.0001) ? prob.toExponential(4) : (prob * 100).toFixed(4) + '%'
const getProbabilityPercentage = (prob) => {
  if (prob < 1e-10) return 0.1
  if (prob < 1e-6) return 1
  if (prob < 1e-4) return 5
  return Math.min(prob * 100, 100)
}
const formatTimestamp = (timestamp) => new Date(timestamp).toLocaleString('zh-CN')

// 注意力矩阵计算
const attentionMatrix = computed(() => {
  if (!predictionResult.value?.attention_analysis?.top_connections) return [];
  const matrix = Array(4).fill().map(() => Array(4).fill(0));
  predictionResult.value.attention_analysis.top_connections.forEach(conn => {
    if (conn.drug_a_atom < 4 && conn.drug_b_atom < 4) matrix[conn.drug_a_atom][conn.drug_b_atom] = conn.weight;
  });
  return matrix;
});

const getAtomWeightsForDrug = (drug) => {
  if (!predictionResult.value?.attention_analysis?.top_connections) return [];
  const connections = predictionResult.value.attention_analysis.top_connections;
  const weights = [];
  const atomWeightMap = new Map();
  connections.forEach(conn => {
    const atomIndex = drug === 'A' ? conn.drug_a_atom : conn.drug_b_atom;
    const currentWeight = atomWeightMap.get(atomIndex) || 0;
    atomWeightMap.set(atomIndex, Math.max(currentWeight, conn.weight));
  });
  atomWeightMap.forEach((weight, atomIndex) => weights.push({ atomIndex, weight }));
  return weights.sort((a, b) => b.weight - a.weight);
};

const getMatrixColor = (value) => {
  if (value === 0) return '#f0f0f0';
  const normalized = Math.min(value / 35, 1);
  const r = Math.floor(200 + 55 * normalized);
  const g = Math.floor(200 - 150 * normalized);
  const b = Math.floor(255 - 200 * normalized);
  return `rgb(${r}, ${g}, ${b})`;
};


const batchLoading = ref(false)
const batchForm = ref([
  { drug_a_name: '', smiles_a: '', drug_b_name: '', smiles_b: '', interaction_type_id: '' },
  { drug_a_name: '', smiles_a: '', drug_b_name: '', smiles_b: '', interaction_type_id: '' }
])
const batchResults = ref([])

const addBatchRow = () => {
  if (batchForm.value.length >= 10) {
    showToast('手填模式建议不超过 10 条组合')
    return
  }
  batchForm.value.push({ drug_a_name: '', smiles_a: '', drug_b_name: '', smiles_b: '', interaction_type_id: '' })
}

const removeBatchRow = (index) => {
  batchForm.value.splice(index, 1)
}

const submitBatch = async () => {
  const validPairs = batchForm.value.filter(item => item.smiles_a.trim() && item.smiles_b.trim())
  
  if (validPairs.length === 0) {
    showToast('请至少填写一组完整的药物 SMILES 结构式')
    return
  }

  batchLoading.value = true
  batchResults.value = []

  try {
    const payloadPairs = validPairs.map(p => ({
      ...p,
      interaction_type_id: p.interaction_type_id ? Number(p.interaction_type_id) : 0
    }))

    const res = await batchPredict({ pairs: payloadPairs })
    
    if (res.code === 200 || res.success) {
      showSuccessToast(`成功预测 ${res.data.length} 条数据`)
      batchResults.value = res.data
    } else {
      showFailToast(res.message || '批量预测包含错误')
      if (res.data) batchResults.value = res.data
    }
  } catch (error) {
    console.error(error)
    showFailToast('网络或服务器错误')
  } finally {
    batchLoading.value = false
  }
}

const truncateName = (name) => name && name.length > 12 ? name.substring(0, 12) + '...' : name
const truncateSmiles = (str) => str && str.length > 25 ? str.substring(0, 25) + '...' : str
</script>

<style scoped>
.prediction-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}
.page-header h2 { font-size: 28px; font-weight: 600; color: #1a1a1a; margin-bottom: 8px; }
.page-header .subtitle { color: #666; font-size: 16px; }

.main-tabs :deep(.van-tabs__nav--card) {
  margin: 0 auto 24px;
  width: 400px;
}

.input-section {
  background: white; border-radius: 16px; padding: 24px; margin-bottom: 32px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}
.input-section h3 { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #333; }
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.form-group { display: flex; flex-direction: column; position: relative; }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { font-size: 14px; font-weight: 500; color: #555; margin-bottom: 8px; }
.form-input { padding: 12px 16px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: all 0.3s; }
.form-input:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1); }
.form-select { padding: 12px 16px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: all 0.3s; background-color: white; cursor: pointer; appearance: none; -webkit-appearance: none; padding-right: 40px; width: 100%; max-width: 600px; }
.form-select:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1); }
.select-arrow { position: absolute; left: 44%; bottom: 12px; color: #666; pointer-events: none; font-size: 12px; }
.form-select optgroup { font-weight: 600; color: #4361ee; background-color: #f8f9fa; }
.form-select option { padding: 8px; font-size: 13px; }

.btn-predict { background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; border: none; border-radius: 8px; padding: 14px 24px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.3s; width: 100%; max-width: 200px; margin: 0 auto; display: block; }
.btn-predict:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3); }
.btn-predict:disabled { opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none; }

.result-section { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05); }
.result-section h3 { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #333; }
.result-card { display: flex; justify-content: space-between; align-items: center; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
.result-safe { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-left: 4px solid #4caf50; }
.result-danger { background: linear-gradient(135deg, #ffebee, #ffcdd2); border-left: 4px solid #f44336; }
.result-warning { background: linear-gradient(135deg, #fff3e0, #ffe0b2); border-left: 4px solid #ff9800; }
.result-header { display: flex; align-items: center; gap: 12px; }
.result-label { font-size: 18px; font-weight: 500; color: #333; }
.result-value { font-size: 24px; font-weight: 700; }
.confidence-badge { padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; }
.confidence-badge.high { background: #4caf50; color: white; }
.confidence-badge.medium { background: #ff9800; color: white; }
.confidence-badge.low { background: #f44336; color: white; }

.probability-card { padding: 20px; background: #f8f9fa; border-radius: 12px; margin-bottom: 24px; }
.probability-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
.probability-header .label { font-size: 16px; font-weight: 500; color: #555; }
.probability-header .value { font-size: 18px; font-weight: 600; color: #4361ee; }
.probability-bar { height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }
.probability-fill { height: 100%; background: linear-gradient(90deg, #4361ee, #4cc9f0); border-radius: 4px; transition: width 0.3s ease; }

.drug-info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 24px; }
.drug-card { padding: 20px; background: #f8f9fa; border-radius: 12px; border: 1px solid #e9ecef; }
.drug-card h4 { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #4361ee; }
.drug-details p { margin-bottom: 10px; font-size: 14px; }
.drug-details .label { font-weight: 500; color: #666; width: 80px; display: inline-block; }
.smiles-text { font-family: monospace; color: #555; word-break: break-all; }

.attention-section { margin-bottom: 24px; padding: 20px; background: #f8f9fa; border-radius: 12px; }
.attention-section h4 { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #4361ee; }
.attention-visualization { margin-bottom: 24px; }
.molecule-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.attention-matrix { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #e9ecef; }
.attention-matrix h5 { margin: 0 0 16px 0; color: #4361ee; font-size: 16px; }
.matrix-container { display: inline-block; background: white; border-radius: 8px; overflow: hidden; border: 1px solid #dee2e6; }
.matrix-row { display: flex; }
.matrix-cell { width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-right: 1px solid rgba(0, 0, 0, 0.05); border-bottom: 1px solid rgba(0, 0, 0, 0.05); transition: all 0.2s; cursor: pointer; }
.matrix-cell:hover { transform: scale(1.05); box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); z-index: 1; }
.cell-value { font-size: 11px; font-weight: 600; color: rgba(0, 0, 0, 0.7); text-shadow: 0 0 2px white; }

.layer-section { margin-bottom: 24px; }
.layer-section h4 { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #4361ee; }
.layer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.layer-card { padding: 16px; background: white; border-radius: 12px; border: 1px solid #e9ecef; }
.layer-card h5 { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #4361ee; }
.layer-details p { margin-bottom: 8px; font-size: 13px; }
.model-info { display: flex; gap: 24px; padding: 16px; background: white; border-radius: 8px; font-size: 14px; border: 1px solid #e9ecef; }
.model-info .label { font-weight: 500; color: #666; }
.model-info .value { color: #333; font-weight: 500; }

.batch-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.batch-form-area {
  flex: 1;
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  max-width: 600px;
}

.batch-header-info {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e9ecef;
}
.batch-header-info h3 { margin: 0 0 8px 0; font-size: 18px; color: #333; }
.batch-header-info p { margin: 0; font-size: 13px; color: #868e96; }

.batch-scroll-box {
  max-height: 550px;
  overflow-y: auto;
  padding-right: 8px;
}
.batch-scroll-box::-webkit-scrollbar { width: 6px; }
.batch-scroll-box::-webkit-scrollbar-thumb { background: #dee2e6; border-radius: 3px; }

.batch-row-card {
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  background-color: #f8f9fa;
  transition: box-shadow 0.2s;
}
.batch-row-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border-color: #ced4da;
}

.batch-row-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.delete-btn { color: #fa5252; font-size: 12px; cursor: pointer; transition: opacity 0.2s; }
.delete-btn:hover { opacity: 0.7; }

.batch-inputs-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.mini-group { margin-bottom: 0; }
.full-width-mini { grid-column: 1 / -1; }
.mini-input { padding: 8px 12px; font-size: 13px; border-radius: 6px; }

.batch-actions {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
}

.add-btn {
  width: 100%; padding: 12px; background-color: white; color: #4361ee; border: 1px dashed #4361ee; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-weight: 500;
}
.add-btn:hover { background-color: #f8f9fa; }

.batch-result-area {
  flex: 1;
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  min-height: 500px;
}
.batch-result-area h3 { margin: 0 0 20px 0; padding-bottom: 16px; border-bottom: 1px solid #e9ecef; font-size: 18px; }

.empty-results { margin-top: 80px; }

.batch-results-list {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.batch-res-item {
  padding: 16px;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  margin-bottom: 16px;
  background-color: #fff;
  transition: transform 0.2s;
}
.batch-res-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

.res-pair-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.drug-name-badge { font-size: 14px; font-weight: 600; color: #333; background: #f1f3f5; padding: 4px 8px; border-radius: 4px; }
.exchange-icon { color: #adb5bd; }

.res-pair-smiles {
  font-family: monospace;
  font-size: 12px;
  color: #868e96;
  margin-bottom: 12px;
  background: #f8f9fa;
  padding: 8px;
  border-radius: 6px;
}

.res-outcome { display: flex; justify-content: space-between; align-items: center; }
.res-score { font-size: 13px; color: #495057; font-weight: 500; }
.res-error { margin-top: 8px; font-size: 12px; color: #e03131; background: #fff5f5; padding: 8px; border-radius: 6px; }
</style>
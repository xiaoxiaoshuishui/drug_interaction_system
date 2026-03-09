<template>
  <div class="prediction-container">
    <div class="page-header">
      <h2>药物相互作用预测</h2>
      <p class="subtitle">基于DSN-DDI模型的药物相互作用分析</p>
    </div>

    <!-- 输入表单区域 -->
    <div class="input-section">
      <h3>输入药物信息</h3>
      <div class="form-grid">
        <div class="form-group">
          <label>药物A SMILES</label>
          <input type="text" v-model="formData.smiles_a" placeholder="请输入药物A的SMILES字符串" class="form-input" />
        </div>
        <div class="form-group">
          <label>药物B SMILES</label>
          <input type="text" v-model="formData.smiles_b" placeholder="请输入药物B的SMILES字符串" class="form-input" />
        </div>
        <div class="form-group">
          <label>药物A名称</label>
          <input type="text" v-model="formData.drug_a_name" placeholder="请输入药物A名称" class="form-input" />
        </div>
        <div class="form-group">
          <label>药物B名称</label>
          <input type="text" v-model="formData.drug_b_name" placeholder="请输入药物B名称" class="form-input" />
        </div>

        <!-- 新增：反应类型选择 -->
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
            <van-loading v-else type="spinner" size="20px">预测中...</van-loading>
          </button>
        </div>
      </div>
    </div>

    <!-- 预测结果区域 -->
    <div v-if="predictionResult" class="result-section">
      <h3>预测结果</h3>

      <!-- 主要预测结果卡片 -->
      <div class="result-card" :class="getResultClass(predictionResult.prediction)">
        <div class="result-header">
          <span class="result-label">预测结果：</span>
          <span class="result-value">{{ predictionResult.prediction }}</span>
        </div>
        <div class="confidence-badge" :class="predictionResult.confidence">
          {{ getConfidenceText(predictionResult.confidence) }}
        </div>
      </div>

      <!-- 概率信息 -->
      <div class="probability-card">
        <div class="probability-header">
          <span class="label">相互作用概率</span>
          <span class="value">{{ formatProbability(predictionResult.probability) }}</span>
        </div>
        <div class="probability-bar">
          <div class="probability-fill"
            :style="{ width: getProbabilityPercentage(predictionResult.probability) + '%' }"></div>
        </div>
      </div>

      <!-- 药物信息网格 -->
      <div class="drug-info-grid">
        <div class="drug-card">
          <h4>药物A: {{ predictionResult.drug_a_info.name }}</h4>
          <div class="drug-details">
            <p><span class="label">SMILES:</span> {{ predictionResult.drug_a_info.smiles }}</p>
            <p><span class="label">原子数量:</span> {{ predictionResult.drug_a_info.num_atoms }}</p>
            <p><span class="label">键数量:</span> {{ predictionResult.drug_a_info.num_bonds }}</p>
          </div>
        </div>

        <div class="drug-card">
          <h4>药物B: {{ predictionResult.drug_b_info.name }}</h4>
          <div class="drug-details">
            <p><span class="label">SMILES:</span> {{ predictionResult.drug_b_info.smiles }}</p>
            <p><span class="label">原子数量:</span> {{ predictionResult.drug_b_info.num_atoms }}</p>
            <p><span class="label">键数量:</span> {{ predictionResult.drug_b_info.num_bonds }}</p>
          </div>
        </div>
      </div>

      <div v-if="predictionResult?.attention_analysis" class="attention-section">
        <h4>🔬 注意力机制分析 - 原子重要性可视化</h4>

        <!-- 双分子注意力对比 -->
        <div class="attention-visualization">
          <div class="molecule-row">
            <AttentionMoleculeViewer :smiles="predictionResult.drug_a_info.smiles"
              :drug-name="predictionResult.drug_a_info.name" drug-label="药物 A"
              :atom-weights="getAtomWeightsForDrug('A')" :height="300" />

            <AttentionMoleculeViewer :smiles="predictionResult.drug_b_info.smiles"
              :drug-name="predictionResult.drug_b_info.name" drug-label="药物 B"
              :atom-weights="getAtomWeightsForDrug('B')" :height="300" />
          </div>
        </div>

        <!-- 注意力热力图矩阵（可选） -->
        <div class="attention-matrix">
          <h5>注意力权重矩阵热力图</h5>
          <div class="matrix-container">
            <div v-for="(row, i) in attentionMatrix" :key="i" class="matrix-row">
              <div v-for="(value, j) in row" :key="j" class="matrix-cell"
                :style="{ backgroundColor: getMatrixColor(value) }"
                :title="`药物A[${i}] ↔ 药物B[${j}]: ${value.toFixed(4)}`">
                <span class="cell-value">{{ value.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 层激活信息 -->
        <div v-if="predictionResult.layer_activations" class="layer-section">
          <h4>网络层激活信息</h4>
          <div class="layer-grid">
            <div v-for="layer in predictionResult.layer_activations" :key="layer.layer_name" class="layer-card">
              <h5>{{ layer.layer_name }}</h5>
              <div class="layer-details">
                <p v-if="layer.shape">
                  <span class="label">形状:</span>
                  {{ layer.shape.join(' × ') }}
                </p>
                <p v-if="layer.value_range">
                  <span class="label">值范围:</span>
                  [{{ layer.value_range[0].toFixed(2) }}, {{ layer.value_range[1].toFixed(2) }}]
                </p>
                <p v-if="layer.mean !== null && layer.mean !== undefined">
                  <span class="label">均值:</span>
                  {{ layer.mean.toFixed(4) }}
                </p>
                <p v-if="layer.tensor_count">
                  <span class="label">张量数量:</span>
                  {{ layer.tensor_count }}
                </p>
                <div v-if="layer.tensor_shapes" class="tensor-shapes">
                  <span class="label">张量形状:</span>
                  <ul>
                    <li v-for="(shape, idx) in layer.tensor_shapes" :key="idx">
                      Tensor {{ idx + 1 }}: [{{ shape.join(', ') }}]
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 模型信息 -->
        <div class="model-info">
          <div class="info-item">
            <span class="label">使用模型：</span>
            <span class="value">{{ predictionResult.model_used }}</span>
          </div>
          <div class="info-item">
            <span class="label">处理时间：</span>
            <span class="value">{{ predictionResult.processing_time_ms }} ms</span>
          </div>
          <div class="info-item">
            <span class="label">时间戳：</span>
            <span class="value">{{ formatTimestamp(predictionResult.timestamp) }}</span>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <van-toast v-model:show="showError" type="fail" :message="errorMessage" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { showToast } from 'vant'
import { standardPredict } from '../apis/ddis'
import { useDdiStore } from '../store/ddi'
import { REACTION_TYPE_MAP } from '../utils/reactionType'
import AttentionMoleculeViewer from '../components/AttentionMoleculeViewer.vue'

const loading = ref(false)
const showError = ref(false)
const errorMessage = ref('')

const ddiStore = useDdiStore()
// 表单数据
const formData = ddiStore.formData.drug_a_name ? reactive(ddiStore.formData) : reactive({
  smiles_a: 'OC(C(=O)O[C@H]1C[N+]2(CCCOC3=CC=CC=C3)CCC1CC2)(C1=CC=CS1)C1=CC=CS1',
  smiles_b: 'C[N+]1(C)[C@H]2C[C@@H](C[C@@H]1[C@H]1O[C@@H]21)OC(=O)[C@H](CO)C1=CC=CC=C1',
  drug_a_name: '阿地溴铵',
  drug_b_name: '甲基东莨菪碱',
  interaction_type_id: '0'
})

const predictionResult = ref(ddiStore.predictionResult || null);
// 处理预测
const handlePredict = async () => {
  // 表单验证
  if (!formData.smiles_a || !formData.smiles_b) {
    showToast('请输入药物SMILES字符串')
    return
  }

  // 如果用户没有选择反应类型，则不传递该参数
  const params = { ...formData }
  if (!params.interaction_type_id) {
    delete params.interaction_type_id
  }

  loading.value = true
  showError.value = false

  try {
    const result = await standardPredict(params)
    predictionResult.value = result
    ddiStore.predictionResult = result;
    ddiStore.formData = { ...formData };
    showToast({
      type: 'success',
      message: '预测完成'
    })
  } catch (error) {
    console.error('预测失败:', error)
    errorMessage.value = error.message || '预测失败，请重试'
    showError.value = true
  } finally {
    loading.value = false
  }
}

// 根据结果返回不同的样式类
const getResultClass = (prediction) => {
  if (prediction.includes('No Interaction') || prediction.includes('安全')) {
    return 'result-safe'
  } else if (prediction.includes('Interaction') || prediction.includes('相互作用')) {
    return 'result-danger'
  }
  return 'result-warning'
}

// 获取置信度文本
const getConfidenceText = (confidence) => {
  const map = {
    'high': '高置信度',
    'medium': '中等置信度',
    'low': '低置信度'
  }
  return map[confidence] || confidence
}

// 格式化概率值（科学计数法转百分比）
const formatProbability = (prob) => {
  if (prob < 0.0001) {
    return prob.toExponential(4)
  }
  return (prob * 100).toFixed(4) + '%'
}

// 获取概率百分比（用于进度条）
const getProbabilityPercentage = (prob) => {
  // 对极小概率取对数缩放，避免显示为0
  if (prob < 1e-10) return 0.1
  if (prob < 1e-6) return 1
  if (prob < 1e-4) return 5
  return Math.min(prob * 100, 100)
}

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 计算注意力矩阵（4x4）
const attentionMatrix = computed(() => {
  if (!predictionResult.value?.attention_analysis?.top_connections) {
    return [];
  }

  // 创建一个 4x4 的矩阵（假设有4个重要原子）
  const matrix = Array(4).fill().map(() => Array(4).fill(0));

  predictionResult.value.attention_analysis.top_connections.forEach(conn => {
    if (conn.drug_a_atom < 4 && conn.drug_b_atom < 4) {
      matrix[conn.drug_a_atom][conn.drug_b_atom] = conn.weight;
    }
  });

  return matrix;
});

// 获取药物A的原子权重
const getAtomWeightsForDrug = (drug) => {
  if (!predictionResult.value?.attention_analysis?.top_connections) {
    return [];
  }

  const connections = predictionResult.value.attention_analysis.top_connections;
  const weights = [];
  const atomWeightMap = new Map();

  connections.forEach(conn => {
    const atomIndex = drug === 'A' ? conn.drug_a_atom : conn.drug_b_atom;
    const currentWeight = atomWeightMap.get(atomIndex) || 0;
    // 对于每个原子，取最大注意力权重
    atomWeightMap.set(atomIndex, Math.max(currentWeight, conn.weight));
  });

  atomWeightMap.forEach((weight, atomIndex) => {
    weights.push({ atomIndex, weight });
  });

  return weights.sort((a, b) => b.weight - a.weight);
};

// 获取矩阵单元格颜色
const getMatrixColor = (value) => {
  if (value === 0) return '#f0f0f0';

  // 归一化到 0-1 范围（基于已知的最大值约35）
  const normalized = Math.min(value / 35, 1);

  // 使用蓝色到红色的渐变
  const r = Math.floor(200 + 55 * normalized);
  const g = Math.floor(200 - 150 * normalized);
  const b = Math.floor(255 - 200 * normalized);

  return `rgb(${r}, ${g}, ${b})`;
};
</script>

<style scoped>
.prediction-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.page-header .subtitle {
  color: #666;
  font-size: 16px;
}

/* 输入表单样式 */
.input-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.input-section h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #333;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  position: relative;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #555;
  margin-bottom: 8px;
}

.form-input {
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s;
}

.form-input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

/* 下拉选择框样式 */
.form-select {
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s;
  background-color: white;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  padding-right: 40px;
  width: 100%;
  max-width: 600px;
}

.form-select:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

.select-arrow {
  position: absolute;
  right: 12px;
  bottom: 12px;
  color: #666;
  pointer-events: none;
  font-size: 12px;
}

/* 选项分组样式 */
.form-select optgroup {
  font-weight: 600;
  color: #4361ee;
  background-color: #f8f9fa;
}

.form-select option {
  padding: 8px;
  font-size: 13px;
}

.btn-predict {
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 14px 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
  max-width: 200px;
  margin: 0 auto;
}

.btn-predict:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
}

.btn-predict:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 结果区域样式 */
.result-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.result-section h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #333;
}

/* 结果卡片 */
.result-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
}

.result-safe {
  background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
  border-left: 4px solid #4caf50;
}

.result-danger {
  background: linear-gradient(135deg, #ffebee, #ffcdd2);
  border-left: 4px solid #f44336;
}

.result-warning {
  background: linear-gradient(135deg, #fff3e0, #ffe0b2);
  border-left: 4px solid #ff9800;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-label {
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.result-value {
  font-size: 24px;
  font-weight: 700;
}

.confidence-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.confidence-badge.high {
  background: #4caf50;
  color: white;
}

.confidence-badge.medium {
  background: #ff9800;
  color: white;
}

.confidence-badge.low {
  background: #f44336;
  color: white;
}

/* 概率卡片 */
.probability-card {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 24px;
}

.probability-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.probability-header .label {
  font-size: 16px;
  font-weight: 500;
  color: #555;
}

.probability-header .value {
  font-size: 18px;
  font-weight: 600;
  color: #4361ee;
}

.probability-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.probability-fill {
  height: 100%;
  background: linear-gradient(90deg, #4361ee, #4cc9f0);
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* 药物信息网格 */
.drug-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.drug-card {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.drug-card h4 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #4361ee;
}

.drug-details p {
  margin-bottom: 10px;
  font-size: 14px;
}

.drug-details .label {
  font-weight: 500;
  color: #666;
  width: 100px;
  display: inline-block;
}

/* 注意力分析 */
.attention-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.attention-section h4 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #4361ee;
}

.attention-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  padding: 12px;
  background: white;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.top-connections h5 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #555;
}

.connections-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.connections-table th {
  background: #f1f3f5;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.connections-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #e9ecef;
  font-size: 14px;
}

.connections-table tr.top-connection {
  background: rgba(67, 97, 238, 0.05);
}

.connections-table tr.top-connection td:first-child {
  font-weight: 700;
  color: #4361ee;
}

/* 层激活信息 */
.layer-section {
  margin-bottom: 24px;
}

.layer-section h4 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #4361ee;
}

.layer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.layer-card {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.layer-card h5 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #4361ee;
}

.layer-details p {
  margin-bottom: 8px;
  font-size: 13px;
}

.tensor-shapes {
  margin-top: 8px;
}

.tensor-shapes ul {
  margin-top: 4px;
  padding-left: 20px;
}

.tensor-shapes li {
  font-size: 12px;
  color: #555;
  margin-bottom: 2px;
}

/* 模型信息 */
.model-info {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 14px;
}

.model-info .label {
  font-weight: 500;
  color: #666;
}

.model-info .value {
  color: #333;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .prediction-container {
    padding: 16px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .drug-info-grid {
    grid-template-columns: 1fr;
  }

  .attention-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .model-info {
    flex-direction: column;
    gap: 12px;
  }

  .btn-predict {
    max-width: 100%;
  }

  .form-select {
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .attention-stats {
    grid-template-columns: 1fr;
  }

  .result-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

.attention-visualization {
  margin-bottom: 24px;
}

.molecule-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.attention-matrix {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #e9ecef;
}

.attention-matrix h5 {
  margin: 0 0 16px 0;
  color: #4361ee;
  font-size: 16px;
}

.matrix-container {
  display: inline-block;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #dee2e6;
}

.matrix-row {
  display: flex;
}

.matrix-cell {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  cursor: pointer;
}

.matrix-cell:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1;
}

.cell-value {
  font-size: 11px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
  text-shadow: 0 0 2px white;
}

@media (max-width: 768px) {
  .molecule-row {
    grid-template-columns: 1fr;
  }

  .matrix-cell {
    width: 40px;
    height: 40px;
  }

  .cell-value {
    font-size: 9px;
  }
}
</style>
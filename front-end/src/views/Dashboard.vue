<template>
  <div class="dashboard">
    <!-- 主要内容区域：左右两列布局 -->
    <div class="main-content">
      <!-- 左侧：用户输入区域 -->
      <div class="left-column">
        <div class="input-section">
          <h3>🔍 自定义分子查询</h3>
          <div class="input-card">
            <div class="input-group">
              <label for="smiles-input">输入SMILES化学式：</label>
              <div class="input-wrapper">
                <input 
                  id="smiles-input"
                  v-model="userSmiles" 
                  placeholder="例如: CCO (乙醇)"
                  @keyup.enter="renderUserMolecule"
                />
                <button @click="renderUserMolecule" :disabled="!userSmiles">
                  <span v-if="isRendering">渲染中...</span>
                  <span v-else>绘制</span>
                </button>
              </div>
              <p class="input-hint">💡 输入有效的SMILES字符串</p>
            </div>
            
            <!-- 用户绘制的分子图 -->
            <div v-if="currentUserSmiles" class="user-molecule">
              <h4>你的分子：</h4>
              <div class="molecule-display">
                <MoleculeViewer 
                  :smiles="currentUserSmiles" 
                  :height="250"
                  key="user-molecule"
                />
              </div>
              <div class="molecule-actions">
                <button class="secondary-btn" @click="clearUserMolecule">清除</button>
              </div>
            </div>
            
            <!-- 输入提示示例 -->
            <div class="example-smiles">
              <p>📋 示例：</p>
              <div class="example-tags">
                <span 
                  v-for="drug in drugs.slice(0, 4)" 
                  :key="drug.name"
                  @click="selectDrug(drug)"
                >
                  {{ drug.name }}
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- 右侧：预设药物库（横向排列，自动换行） -->
      <div class="right-column">
        <div class="preset-section">
          <div class="section-header">
            <h3>📋 常用药物分子库</h3>
            <p class="section-desc">点击卡片使用该分子</p>
          </div>
          
          <div class="drug-grid">
            <div 
              v-for="drug in drugs" 
              :key="drug.name" 
              class="drug-card"
              :class="{ 'active': currentUserSmiles === drug.smiles }"
              @click="selectDrug(drug)"
            >
              <h4>{{ drug.name }}</h4>
              <p class="drug-formula">{{ drug.formula }}</p>
              <div class="molecule-container" @click.stop>
                <MoleculeViewer 
                  :smiles="drug.smiles" 
                  :width="180" 
                  :height="140"
                  :key="'preset-'+drug.name"
                />
              </div>
              <div class="drug-tags">
                <span class="tag" v-for="adr in drug.adrs.slice(0, 2)" :key="adr">
                  {{ adr }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import MoleculeViewer from '../components/MoleculeViewer.vue';

// 用户输入相关
const userSmiles = ref('');
const currentUserSmiles = ref('');
const isRendering = ref(false);

// 预设药物数据
const drugs = ref([
  {
    name: '阿司匹林',
    formula: 'C₉H₈O₄',
    smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O',
    usage: '解热镇痛、抗血小板聚集',
    adrs: ['胃肠道刺激', '出血风险', '过敏反应']
  },
  {
    name: '布洛芬',
    formula: 'C₁₃H₁₈O₂',
    smiles: 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
    usage: '非甾体抗炎药',
    adrs: ['胃肠道不适', '肾功能损伤', '头痛']
  },
  {
    name: '对乙酰氨基酚',
    formula: 'C₈H₉NO₂',
    smiles: 'CC(=O)NC1=CC=C(C=C1)O',
    usage: '解热镇痛药',
    adrs: ['肝损伤', '皮疹', '恶心']
  },
  {
    name: '青霉素',
    formula: 'C₁₆H₁₉N₂O₄S',
    smiles: 'CC1(C(N2C(S1)C(C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C',
    usage: '抗生素',
    adrs: ['过敏反应', '腹泻', '恶心']
  },
  {
    name: '二甲双胍',
    formula: 'C₄H₁₁N₅',
    smiles: 'CN(C)C(=N)NC(=N)N',
    usage: '降糖药',
    adrs: ['胃肠道反应', '乳酸酸中毒', '维生素B12缺乏']
  },
  {
    name: '阿托伐他汀',
    formula: 'C₃₃H₃₅FN₂O₅',
    smiles: 'CC(C)C1=C(C(=C(N1CCC(CC(CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4',
    usage: '降血脂药',
    adrs: ['肌肉疼痛', '肝功能异常', '头痛']
  }
]);

// 渲染用户输入的分子
const renderUserMolecule = async () => {
  if (!userSmiles.value.trim()) return;
  isRendering.value = true;
  await new Promise(resolve => setTimeout(resolve, 100));
  currentUserSmiles.value = userSmiles.value.trim();
  isRendering.value = false;
};

// 清空用户分子
const clearUserMolecule = () => {
  userSmiles.value = '';
  currentUserSmiles.value = '';
};

// 选择预设药物
const selectDrug = (drug) => {
  userSmiles.value = drug.smiles;
  currentUserSmiles.value = drug.smiles;
};
</script>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 主要内容：左右两列布局 */
.main-content {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

/* 左侧列 - 固定宽度 */
.left-column {
  flex: 0 0 360px;
  position: sticky;
  top: 24px;
}

/* 右侧列 - 自适应 */
.right-column {
  flex: 1;
  min-width: 0; /* 防止flex溢出 */
}

/* 输入区域 */
.input-section {
  margin-bottom: 24px;
}

.input-section h3 {
  color: #2c3e50;
  margin: 0 0 12px 0;
  font-size: 1.2em;
}

.input-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}

.input-group {
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  margin-bottom: 6px;
  color: #495057;
  font-weight: 500;
  font-size: 0.9em;
}

.input-wrapper {
  display: flex;
  gap: 8px;
}

.input-wrapper input {
  flex: 1;
  padding: 10px 12px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 0.9em;
}

.input-wrapper input:focus {
  outline: none;
  border-color: #42b983;
}

.input-wrapper button {
  padding: 10px 16px;
  background: linear-gradient(135deg, #42b983 0%, #35495e 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.input-wrapper button:hover:not(:disabled) {
  opacity: 0.9;
}

.input-wrapper button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hint {
  margin: 8px 0 0;
  color: #6c757d;
  font-size: 0.8em;
}

/* 示例标签 */
.example-smiles {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
}

.example-smiles p {
  margin: 0 0 8px 0;
  color: #495057;
  font-size: 0.9em;
}

.example-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-tags span {
  padding: 4px 10px;
  background: #e9ecef;
  border-radius: 20px;
  font-size: 0.8em;
  color: #495057;
  cursor: pointer;
  transition: all 0.2s;
}

.example-tags span:hover {
  background: #42b983;
  color: white;
}

/* 用户分子显示 */
.user-molecule {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 2px dashed #e9ecef;
}

.user-molecule h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 1em;
}

.molecule-display {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e9ecef;
}

.molecule-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.secondary-btn {
  padding: 6px 12px;
  background: white;
  color: #6c757d;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 0.85em;
  cursor: pointer;
}

.secondary-btn:hover {
  background: #f8f9fa;
  border-color: #42b983;
  color: #42b983;
}

/* 预设药物区域 */
.preset-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}

.section-header {
  margin-bottom: 20px;
}

.section-header h3 {
  color: #2c3e50;
  margin: 0 0 4px 0;
  font-size: 1.2em;
}

.section-desc {
  color: #6c757d;
  margin: 0;
  font-size: 0.85em;
}

/* 药物网格 - 横向排列，自动换行 */
.drug-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.drug-card {
  flex: 0 0 calc(33.333% - 11px); /* 三列布局 */
  min-width: 200px;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  transition: all 0.2s;
  cursor: pointer;
  border: 2px solid transparent;
  border: 1px solid #e9ecef;
}

.drug-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border-color: #42b983;
}

.drug-card.active {
  border-color: #42b983;
  background: #f0fff4;
}

.drug-card h4 {
  margin: 0 0 2px 0;
  color: #2c3e50;
  font-size: 1.1em;
}

.drug-formula {
  color: #6c757d;
  font-family: monospace;
  margin: 0 0 8px 0;
  font-size: 0.8em;
}

.molecule-container {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 8px;
  border: 1px solid #e9ecef;
  display: flex;
  justify-content: center;
}

.drug-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  padding: 2px 6px;
  background: #e9ecef;
  border-radius: 12px;
  font-size: 0.7em;
  color: #495057;
}

.adr-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.adr-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.adr-item span:first-child {
  width: 90px;
  color: #495057;
  font-size: 0.9em;
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-column {
    flex: auto;
    width: 100%;
    position: static;
  }
  
  .drug-card {
    flex: 0 0 calc(50% - 8px); /* 平板：两列 */
  }
}
</style>
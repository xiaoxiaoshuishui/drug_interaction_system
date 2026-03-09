<template>
  <div class="attention-molecule-viewer">
    <div class="viewer-header" v-if="title">
      <h4>{{ title }}</h4>
    </div>
    <div class="molecule-container" ref="moleculeContainer"></div>
    
    <div v-if="atomWeights.length > 0" class="atom-stats">
      <div class="stat-row">
        <span class="stat-label">最高注意力原子:</span>
        <span class="stat-value">原子 #{{ topAtoms[0]?.atomIndex }} (权重: {{ topAtoms[0]?.weight.toFixed(2) }})</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Top 3 原子:</span>
        <span class="stat-value">
          {{ topAtoms.slice(0, 3).map(a => `#${a.atomIndex}`).join(', ') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed, onUnmounted } from 'vue';
import rdkitLoader from '../utils/rdkitLoader'; // 导入单例

const props = defineProps({
  smiles: {
    type: String,
    required: true
  },
  drugName: {
    type: String,
    default: ''
  },
  // 注意力权重数组，格式：[{ atomIndex: 0, weight: 0.5 }]
  atomWeights: {
    type: Array,
    default: () => []
  },
  width: {
    type: [Number, String],
    default: '100%'
  },
  height: {
    type: [Number, String],
    default: 300
  },
  drugLabel: {
    type: String,
    default: ''
  },
});

const moleculeContainer = ref(null);
const topAtoms = ref([]);
let currentMol = null; // 用于清理

// 计算标题
const title = computed(() => {
  if (props.drugName && props.drugLabel) {
    return `${props.drugLabel}: ${props.drugName}`;
  }
  return props.drugName || props.drugLabel || '';
});

// 生成带高亮的 SVG
const renderHighlightedMolecule = async () => {
  if (!props.smiles || !moleculeContainer.value) return;
  
  console.log('渲染分子:', props.smiles.substring(0, 30) + '...');
  console.log('原子权重数据:', props.atomWeights);
  
  try {
    // 使用全局单例加载 RDKit
    const RDKit = await rdkitLoader.load('https://unpkg.com/@rdkit/rdkit/dist/RDKit_minimal.js');
    
    // 清理之前的分子
    if (currentMol) {
      currentMol.delete();
      currentMol = null;
    }
    
    // 创建分子对象
    currentMol = RDKit.get_mol(props.smiles);
    
    // 找出 Top 原子
    topAtoms.value = props.atomWeights
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 5);
    
    // 生成基础 SVG
    const svg = currentMol.get_svg();
    
    // 解析 SVG
    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svg, 'image/svg+xml');
    
    // 添加全局样式
    const style = svgDoc.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = `
      circle {
        transition: all 0.2s ease;
        cursor: pointer;
      }
      circle:hover {
        filter: brightness(1.2);
        stroke: #000 !important;
        stroke-width: 2.5 !important;
      }
      g:hover circle {
        filter: brightness(1.2);
      }
    `;
    svgDoc.documentElement.appendChild(style);
    
    // 序列化并显示
    const serializer = new XMLSerializer();
    const highlightedSvg = serializer.serializeToString(svgDoc);
    
    moleculeContainer.value.innerHTML = highlightedSvg;
    
  } catch (error) {
    console.error('分子渲染失败:', error);
    moleculeContainer.value.innerHTML = `<p class="error">渲染失败: ${error.message}</p>`;
  }
};

// 组件卸载时清理
onUnmounted(() => {
  if (currentMol) {
    currentMol.delete();
    currentMol = null;
  }
});

// 监听 props 变化
watch([() => props.smiles, () => props.atomWeights], async () => {
  await nextTick();
  renderHighlightedMolecule();
}, { deep: true });

onMounted(() => {
  renderHighlightedMolecule();
});
</script>

<style scoped>
/* 样式保持不变 */
.attention-molecule-viewer {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 10px;
}

.viewer-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1em;
  font-weight: 600;
}

.gradient-sample {
  width: 40px;
  height: 12px;
  background: linear-gradient(90deg, #4a90e2, #e24a4a);
  border-radius: 3px;
}

.molecule-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: v-bind('typeof height === "number" ? height + "px" : height');
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e9ecef;
  overflow: auto;
}

.molecule-container :deep(svg) {
  max-width: 100%;
  height: auto;
  display: block;
}

.atom-stats {
  margin-top: 12px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9em;
  border: 1px solid #e9ecef;
}

.stat-row {
  display: flex;
  margin-bottom: 4px;
}

.stat-row:last-child {
  margin-bottom: 0;
}

.stat-label {
  width: 100px;
  color: #666;
  font-weight: 500;
  flex-shrink: 0;
}

.stat-value {
  color: #2c3e50;
  font-weight: 600;
  word-break: break-word;
}

.error {
  color: #dc3545;
  text-align: center;
  padding: 20px;
}
</style>
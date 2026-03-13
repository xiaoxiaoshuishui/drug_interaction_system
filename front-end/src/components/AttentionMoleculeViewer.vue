<template>
  <div class="attention-molecule-viewer">
    <div class="viewer-header" v-if="title">
      <h4>{{ title }}</h4>
    </div>
    
    <div 
      class="molecule-container" 
      ref="moleculeContainer"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
    ></div>
    
    <div v-if="atomWeights.length > 0" class="atom-stats">
      <div class="stat-row">
        <span class="stat-label">最高注意力原子:</span>
        <span class="stat-value">原子 #{{ topAtoms[0]?.atomIndex }} (权重: {{ topAtoms[0]?.weight.toFixed(4) }})</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Top 3 原子:</span>
        <span class="stat-value">
          {{ topAtoms.slice(0, 3).map(a => `#${a.atomIndex}`).join(', ') }}
        </span>
      </div>
    </div>

    <Teleport to="body">
      <div 
        v-if="hoverTooltip" 
        class="atom-tooltip"
        :style="{ top: hoverTooltip.y + 'px', left: hoverTooltip.x + 'px' }"
      >
        <div class="tooltip-header">
          <span class="atom-symbol">{{ hoverTooltip.symbol }}</span> 原子 (Index: {{ hoverTooltip.idx }})
        </div>
        <div class="tooltip-body">
          <div class="feature-item highlight">
            <span>🎯 <b>注意力权重</b> (Attention):</span>
            <strong>{{ hoverTooltip.attention }}</strong>
          </div>
          <div class="feature-divider"></div>
          <div class="feature-item">
            <span>⚛️ <b>芳香性</b> (Aromatic):</span>
            <strong>{{ hoverTooltip.isAromatic }}</strong>
          </div>
          <div class="feature-item">
            <span>⚡ <b>形式电荷</b> (Formal Charge):</span>
            <strong>{{ hoverTooltip.charge }}</strong>
          </div>
          <div class="feature-item">
            <span>🧬 <b>杂化方式</b> (Hybridization):</span>
            <strong>{{ hoverTooltip.hybridization }}</strong>
          </div>
          <div class="feature-item">
            <span>🔗 <b>隐式/总氢数</b> (Hs):</span>
            <strong>{{ hoverTooltip.degree }}</strong>
          </div>
          <div class="feature-item">
            <span>🌀 <b>自由基电子</b> (Radical):</span>
            <strong>{{ hoverTooltip.radical }}</strong>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed, onUnmounted } from 'vue';
import rdkitLoader from '../utils/rdkitLoader';

const props = defineProps({
  smiles: { type: String, required: true },
  drugName: { type: String, default: '' },
  atomWeights: { type: Array, default: () => [] },
  width: { type: [Number, String], default: '100%' },
  height: { type: [Number, String], default: 300 },
  drugLabel: { type: String, default: '' },
});

const moleculeContainer = ref(null);
const topAtoms = ref([]);
const atomFeaturesMap = ref([]);
const hoverTooltip = ref(null);
let currentMol = null;

const ATOM_SYMBOLS = {
  1: 'H', 3: 'Li', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 11: 'Na', 12: 'Mg', 
  13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 19: 'K', 20: 'Ca', 22: 'Ti', 
  23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni', 29: 'Cu', 30: 'Zn', 
  32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 
  50: 'Sn', 51: 'Sb', 53: 'I', 70: 'Yb', 78: 'Pt', 79: 'Au', 80: 'Hg', 81: 'Tl', 82: 'Pb'
};

const title = computed(() => {
  if (props.drugName && props.drugLabel) return `${props.drugLabel}: ${props.drugName}`;
  return props.drugName || props.drugLabel || '';
});

const renderHighlightedMolecule = async () => {
  if (!props.smiles || !moleculeContainer.value) return;
  
  try {
    const RDKit = await rdkitLoader.load('https://unpkg.com/@rdkit/rdkit/dist/RDKit_minimal.js');
    
    if (currentMol) {
      currentMol.delete();
      currentMol = null;
    }
    
    currentMol = RDKit.get_mol(props.smiles);
    
    topAtoms.value = props.atomWeights
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 5);
      
    // 提取 RDKit 底层 JSON 特征
    const details = JSON.parse(currentMol.get_json());
    if (details && details.molecules && details.molecules.length > 0) {
      atomFeaturesMap.value = details.molecules[0].atoms || [];
    }
    
    const highlightOptions = {
      addAtomIndices: false,
      addStereoAnnotation: true,
      width: 400,
      height: 300
    };
    
    if (props.atomWeights.length > 0) {
      const atomsToHighlight = props.atomWeights.filter(a => a.weight > 0.05).map(a => a.atomIndex);
      if (atomsToHighlight.length > 0) {
        highlightOptions.atoms = atomsToHighlight;
      }
    }
    
    const svg = currentMol.get_svg_with_highlights(JSON.stringify(highlightOptions));
    
    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svg, 'image/svg+xml');
    
    const style = svgDoc.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = `
      path, ellipse, text { transition: all 0.2s ease; }
      ellipse[class^="atom-"]:hover, ellipse[class*=" atom-"]:hover,
      text[class^="atom-"]:hover, text[class*=" atom-"]:hover {
        filter: drop-shadow(0 0 4px rgba(67, 97, 238, 0.8));
        cursor: crosshair;
      }
    `;
    svgDoc.documentElement.appendChild(style);
    
    const serializer = new XMLSerializer();
    moleculeContainer.value.innerHTML = serializer.serializeToString(svgDoc);
    
  } catch (error) {
    console.error('分子渲染失败:', error);
    moleculeContainer.value.innerHTML = `<p class="error">渲染失败: ${error.message}</p>`;
  }
};

const handleMouseMove = (e) => {
  if (!moleculeContainer.value || atomFeaturesMap.value.length === 0) return;
  
  let target = e.target;
  
  if (target.tagName && target.tagName.toLowerCase() === 'path') {
    hoverTooltip.value = null;
    return;
  }

  let atomClass = null;

  while (target && target !== moleculeContainer.value) {
    if (target.className && typeof target.className === 'string' || target.className.baseVal) {
      const classStr = typeof target.className === 'string' ? target.className : target.className.baseVal;
      const match = classStr.match(/atom-(\d+)/);
      if (match) {
        atomClass = match[0];
        break;
      }
    }
    target = target.parentNode;
  }

  if (atomClass) {
    const atomIdx = parseInt(atomClass.replace('atom-', ''));
    const feature = atomFeaturesMap.value[atomIdx];
    
    if (feature) {
      const weightObj = props.atomWeights.find(w => w.atomIndex === atomIdx);
      const weight = weightObj ? weightObj.weight : 0;
      const atomicNumber = feature.z !== undefined ? feature.z : 6;
      
      // 映射 data_preprocessing.py 中的高级特征
      hoverTooltip.value = {
        x: e.clientX + 15,
        y: e.clientY + 15,
        idx: atomIdx,
        symbol: ATOM_SYMBOLS[atomicNumber] || '未知',
        isAromatic: feature.arom ? 'True' : 'False',
        charge: feature.chg || 0,
        degree: feature.impHs || 0,
        hybridization: feature.hyb || 'SP3',     // 杂化方式
        radical: feature.rad || 0,               // 自由基电子
        attention: weight.toFixed(2) + '%'
      };
      return;
    }
  }
  
  hoverTooltip.value = null;
};

const handleMouseLeave = () => { hoverTooltip.value = null; };

onUnmounted(() => {
  if (currentMol) {
    currentMol.delete();
    currentMol = null;
  }
});

watch([() => props.smiles, () => props.atomWeights], async () => {
  await nextTick();
  renderHighlightedMolecule();
}, { deep: true });

onMounted(() => { renderHighlightedMolecule(); });
</script>

<style scoped>
.attention-molecule-viewer { background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; }
.viewer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.viewer-header h4 { margin: 0; color: #2c3e50; font-size: 1.1em; font-weight: 600; }
.molecule-container { flex: 1; display: flex; justify-content: center; align-items: center; min-height: v-bind('typeof height === "number" ? height + "px" : height'); background: #f8f9fa; border-radius: 8px; padding: 12px; border: 1px solid #e9ecef; overflow: hidden; }
.molecule-container :deep(svg) { max-width: 100%; max-height: 100%; display: block; }
.atom-stats { margin-top: 12px; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 0.9em; border: 1px solid #e9ecef; }
.stat-row { display: flex; margin-bottom: 4px; }
.stat-row:last-child { margin-bottom: 0; }
.stat-label { width: 100px; color: #666; font-weight: 500; flex-shrink: 0; }
.stat-value { color: #2c3e50; font-weight: 600; }
.error { color: #dc3545; text-align: center; padding: 20px; }

.atom-tooltip { position: fixed; z-index: 9999; background: rgba(255, 255, 255, 0.96); backdrop-filter: blur(8px); border: 1px solid rgba(67, 97, 238, 0.3); border-radius: 10px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12); width: 240px; pointer-events: none; transform: translateZ(0); }
.tooltip-header { background: #4361ee; color: white; padding: 8px 12px; border-radius: 9px 9px 0 0; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.atom-symbol { background: white; color: #4361ee; padding: 2px 6px; border-radius: 4px; font-size: 14px; font-weight: bold; }
.tooltip-body { padding: 12px; }
.feature-item { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; color: #555; }
.feature-item b { color: #333; }
.feature-item.highlight strong { color: #e03131; font-weight: bold; font-size: 13px; }
.feature-divider { height: 1px; background: #e9ecef; margin: 8px 0; }
</style>
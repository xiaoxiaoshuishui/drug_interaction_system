<template>
  <div ref="moleculeContainer" class="molecule-viewer"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import rdkitLoader from '../utils/rdkitLoader';

const props = defineProps({
  smiles: String,
  width: { type: Number, default: 400 },
  height: { type: Number, default: 300 },
});

const moleculeContainer = ref(null);
let currentMol = null;

const renderMolecule = async () => {
  if (!props.smiles || !moleculeContainer.value) return;
  
  try {
    // 使用单例加载器
    const RDKit = await rdkitLoader.load('/rdkit/RDKit_minimal.js');
    
    // 清理之前的分子
    if (currentMol) {
      currentMol.delete();
      currentMol = null;
    }
    
    // 创建新分子
    currentMol = RDKit.get_mol(props.smiles);
    const svg = currentMol.get_svg();
    
    moleculeContainer.value.innerHTML = svg;
    
    // 设置尺寸
    const svgElement = moleculeContainer.value.querySelector('svg');
    if (svgElement) {
      svgElement.setAttribute('width', '100%');
      svgElement.setAttribute('height', '100%');
      svgElement.style.maxWidth = '100%';
      svgElement.style.maxHeight = '100%';
    }
  } catch (error) {
    console.error('分子渲染失败:', error);
    moleculeContainer.value.innerHTML = '<p style="color: red;">渲染失败</p>';
  }
};

// 组件卸载时清理
onUnmounted(() => {
  if (currentMol) {
    currentMol.delete();
    currentMol = null;
  }
});

onMounted(renderMolecule);
watch(() => props.smiles, renderMolecule);
</script>

<style scoped>
.molecule-viewer {
  width: v-bind(width + 'px');
  height: v-bind(height + 'px');
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.molecule-viewer :deep(svg) {
  width: 100%;
  height: 100%;
}
</style>
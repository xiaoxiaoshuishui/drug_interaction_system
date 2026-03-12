<template>
  <div class="history-container">
    <div class="page-header">
      <h2>DDI 预测历史记录</h2>
      <p class="subtitle">查看和管理您的药物相互作用预测历史</p>
    </div>

    <div v-if="loading" class="loading-state">
      数据加载中...
    </div>

    <div v-else class="table-wrapper">
      <table class="history-table">
        <thead>
          <tr>
            <th>收藏</th>
            <th>药物组合</th>
            <th>预测结果</th>
            <th>置信度</th>
            <th>反应类型</th>
            <th>预测时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in historyList" :key="record.id">
            <td class="action-cell">
              <span 
                class="star-icon" 
                :class="{ active: record.is_favorite }"
                @click="toggleFavorite(record)"
              >
                {{ record.is_favorite ? '★' : '☆' }}
              </span>
            </td>
            
            <td>
              <div class="drug-info-cell">
                <div class="drug-names">
                  <span class="drug-a">{{ record.drug_a_name || '未知药物A' }}</span>
                  <span class="cross-icon">×</span>
                  <span class="drug-b">{{ record.drug_b_name || '未知药物B' }}</span>
                </div>
                <div class="smiles-group">
                  <span class="smiles-text" :title="record.smiles_a">
                    A: {{ truncateSmiles(record.smiles_a) }}
                  </span>
                  <span class="smiles-text" :title="record.smiles_b">
                    B: {{ truncateSmiles(record.smiles_b) }}
                  </span>
                </div>
              </div>
            </td>

            <td>
              <span class="status-tag" :class="record.prediction_label">
                {{ record.prediction_label === 'risk' ? '存在风险 (Risk)' : '安全 (Safe)' }}
              </span>
            </td>

            <td>
              <span class="confidence-text" :class="record.confidence">
                {{ formatConfidence(record.confidence) }}
              </span>
            </td>

            <td>
              <span class="reaction-type">
                {{ getReactionTypeName(record.interaction_type_id) }}
              </span>
            </td>

            <td class="date-cell">
              {{ formatDate(record.created_at) }}
            </td>

            <td class="action-cell">
              <button class="btn-delete" @click="handleDelete(record.id)">删除</button>
            </td>
          </tr>
          
          <tr v-if="historyList.length === 0">
            <td colspan="7" class="empty-state">暂无预测历史记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="total > 0">
      <button :disabled="currentPage === 1" @click="changePage(currentPage - 1)">上一页</button>
      <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页 (总计 {{ total }} 条)</span>
      <button :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getDdiHistory, updatePrediction, deletePrediction } from '../apis/ddis';
import { REACTION_TYPE_MAP } from '../utils/reactionType';

// 状态定义
const historyList = ref([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

const totalPages = computed(() => Math.ceil(total.value / pageSize.value));

// 加载历史记录数据
const loadData = async () => {
  loading.value = true;
  try {
    const res = await getDdiHistory({
      page: currentPage.value,
      page_size: pageSize.value
    });
    historyList.value = res.data || [];
    total.value = res.total || 0;
  } catch (error) {
    alert('获取历史记录失败，请确保已登录');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 分页切换
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  loadData();
};

// 切换收藏状态
const toggleFavorite = async (record) => {
  const newStatus = !record.is_favorite;
  try {
    await updatePrediction(record.id, { is_favorite: newStatus });
    record.is_favorite = newStatus; // 本地更新状态
  } catch (error) {
    alert('操作失败');
  }
};

// 删除记录
const handleDelete = async (id) => {
  if (!confirm('确定要删除这条预测记录吗？')) return;
  try {
    await deletePrediction(id);
    alert('删除成功');
    // 如果当前页只有一条数据且不是第一页，删除后跳回上一页
    if (historyList.value.length === 1 && currentPage.value > 1) {
      currentPage.value -= 1;
    }
    loadData(); // 重新加载列表
  } catch (error) {
    alert('删除失败');
  }
};

// 根据 ID 获取字典里的反应类型中文名称
const getReactionTypeName = (typeId) => {
  if (typeId === null || typeId === undefined) return '未指定分类';
  return REACTION_TYPE_MAP[typeId] || `未知分类 (ID: ${typeId})`;
};

// 格式化置信度
const formatConfidence = (conf) => {
  const map = { high: '高', medium: '中', low: '低' };
  return map[conf] || conf;
};

// 格式化时间 (ISO 转 YYYY-MM-DD HH:mm)
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

const truncateSmiles = (smiles) => {
  if (!smiles) return '未知分子式';
  return smiles.length > 20 ? smiles.substring(0, 20) + '...' : smiles;
};

// 页面加载时自动请求数据
onMounted(() => {
  loadData();
});
</script>

<style scoped>
.history-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  color: #2b3a4a;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #6c757d;
  font-size: 14px;
  margin: 0;
}

.table-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  overflow: hidden;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.history-table th, .history-table td {
  padding: 16px;
  border-bottom: 1px solid #e9ecef;
}

.history-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.history-table tr:hover {
  background-color: #f8f9fa;
}

.drug-names {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.cross-icon {
  color: #adb5bd;
  font-size: 18px;
}

/* 标签样式 */
.status-tag {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

.status-tag.safe {
  background-color: #d1e7dd;
  color: #0f5132;
}

.status-tag.risk {
  background-color: #f8d7da;
  color: #842029;
}

.confidence-text.high { color: #198754; font-weight: bold; }
.confidence-text.medium { color: #fd7e14; font-weight: bold; }
.confidence-text.low { color: #dc3545; font-weight: bold; }

.reaction-type {
  color: #495057;
  font-size: 14px;
}

.date-cell {
  color: #6c757d;
  font-size: 13px;
}

/* 交互按钮 */
.action-cell {
  text-align: center;
}

.star-icon {
  cursor: pointer;
  font-size: 20px;
  color: #dee2e6;
  transition: color 0.2s;
}

.star-icon.active {
  color: #ffc107;
}

.btn-delete {
  background: transparent;
  border: 1px solid #dc3545;
  color: #dc3545;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: #dc3545;
  color: white;
}

.empty-state, .loading-state {
  text-align: center;
  padding: 40px !important;
  color: #6c757d;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 24px;
  gap: 16px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  background: #e9ecef;
  color: #adb5bd;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #495057;
}

.drug-info-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.smiles-group {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #868e96;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}

.smiles-text {
  cursor: help; 
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 250px;
}
</style>
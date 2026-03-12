<template>
  <div class="history-container">
    <div class="page-header">
      <h2>DSA 预测历史记录</h2>
      <p class="subtitle">查看和管理您的药物不良反应预测历史</p>
    </div>

    <div v-if="loading" class="loading-state">
      数据加载中...
    </div>

    <div v-else class="table-wrapper">
      <table class="history-table">
        <thead>
          <tr>
            <th>收藏</th>
            <th>药物 (名称或SMILES)</th>
            <th>副作用</th>
            <th>预测结果</th>
            <th>风险概率</th>
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
                title="点击收藏/取消"
              >
                {{ record.is_favorite ? '★' : '☆' }}
              </span>
            </td>
            
            <td>
              <span class="drug-name" :title="record.drug_identifier">
                {{ truncateSmiles(record.drug_identifier) }}
              </span>
            </td>

            <td>
              <span class="se-name">
                {{ record.se_name || '未知副作用' }}
              </span>
            </td>

            <td>
              <span class="status-tag" :class="record.prediction_label">
                {{ record.prediction_label === 'risk' ? '存在风险 (Risk)' : '安全 (Safe)' }}
              </span>
            </td>

            <td>
              <span class="probability-text" :class="getProbabilityClass(record.probability)">
                {{ formatProbability(record.probability) }}
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
            <td colspan="7" class="empty-state">暂无 DSA 预测历史记录</td>
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
import { getDsaHistory, updateDsaPrediction, deleteDsaPrediction } from '../apis/dsas';

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
    const res = await getDsaHistory({
      page: currentPage.value,
      page_size: pageSize.value
    });
    
    // 兼容不同的 Axios 拦截器返回格式
    
    historyList.value = res.data || [];
    total.value = res.total || 0;
  } catch (error) {
    alert('获取 DSA 历史记录失败，请确保已登录');
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
    await updateDsaPrediction(record.id, { is_favorite: newStatus });
    record.is_favorite = newStatus; // 本地更新状态
  } catch (error) {
    alert('操作失败');
  }
};

// 删除记录
const handleDelete = async (id) => {
  if (!confirm('确定要删除这条预测记录吗？')) return;
  try {
    await deleteDsaPrediction(id);
    // 如果当前页只有一条数据且不是第一页，删除后跳回上一页
    if (historyList.value.length === 1 && currentPage.value > 1) {
      currentPage.value -= 1;
    }
    loadData(); // 重新加载列表
  } catch (error) {
    alert('删除失败');
  }
};

// ===== 工具函数 =====

// 截断过长的药物标识符 (应对用户输入长 SMILES 的情况)
const truncateSmiles = (str) => {
  if (!str) return '未知';
  return str.length > 25 ? str.substring(0, 25) + '...' : str;
};

// 格式化概率得分为百分比
const formatProbability = (prob) => {
  if (prob === null || prob === undefined) return '-';
  return (prob * 100).toFixed(2) + '%';
};

// 根据概率返回颜色类名
const getProbabilityClass = (prob) => {
  if (prob >= 0.8) return 'high-risk';
  if (prob >= 0.5) return 'medium-risk';
  return 'low-risk';
};

// 格式化时间
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
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

.drug-name {
  font-weight: 600;
  color: #339af0;
  cursor: help;
}

.se-name {
  font-weight: 500;
  color: #495057;
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

/* 概率颜色 */
.probability-text { font-weight: bold; font-family: monospace; font-size: 14px; }
.probability-text.high-risk { color: #e03131; }
.probability-text.medium-risk { color: #fd7e14; }
.probability-text.low-risk { color: #2b8a3e; }

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
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #ced4da;
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
</style>
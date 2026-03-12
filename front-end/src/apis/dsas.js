import request from "../utils/request";

export const dsaPredict = async (drug_identifier, se_name) => {
  try {
    // 验证必要参数
    if (!drug_identifier || !se_name) {
      throw new Error('药物标识和副作用名称不能为空');
    }

    // 调用我们在后端写好的 /api/dsa/predict 接口
    const response = await request.post('/api/dsa/predict', {
      drug_identifier,
      se_name,
    });
    
    // 返回预测结果
    return response.data || response; 
  } catch (error) {
    console.error('DSA预测请求失败:', error);
    
    // 统一错误处理提取
    if (error.response) {
      const { status, data } = error.response;
      let errorMessage = '预测失败';
      
      if (status === 404) {
        errorMessage = data.detail || '未找到该药物或副作用，请检查拼写';
      } else if (status === 500) {
        errorMessage = '模型服务器内部异常，请稍后再试';
      } else {
        errorMessage = data.detail || errorMessage;
      }
      throw new Error(errorMessage);
    }
    throw error;
  }
};

// 获取 DSA 预测历史记录列表
export const getDsaHistory = async (params) => {
  try {
    const response = await request.get('/api/dsa/predictions', { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// 更新 DSA 预测记录（切换收藏状态等）
export const updateDsaPrediction = async (id, updateData) => {
  try {
    const response = await request.put(`/api/dsa/predictions/${id}`, updateData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

// 删除 DSA 预测记录
export const deleteDsaPrediction = async (id) => {
  try {
    const response = await request.delete(`/api/dsa/predictions/${id}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};
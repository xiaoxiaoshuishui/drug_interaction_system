import request from "../utils/request";

export const simplePredict = async (smiles_a, smiles_b, interaction_type_id) => {
  try {
    const response = await request.post(`/api/ddi/simple-predict`, {
      smiles_a,
      smiles_b,
      interaction_type_id,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
}

export const standardPredict = async (params) => {
  try {
    // 设置默认值
    const requestData = {
      interaction_type_id: 0,
      include_attention: true,
      include_activations: true,
      ...params, // 用户参数覆盖默认值
    };

    // 验证必要参数
    if (!requestData.smiles_a || !requestData.smiles_b) {
      throw new Error('药物A和药物B的SMILES字符串不能为空');
    }

    const response = await request.post('/api/ddi/predict', requestData);
    return response.data;
  } catch (error) {
    // 统一错误处理
    console.error('标准预测请求失败:', error);
    
    if (error.response) {
      const { status, data } = error.response;
      let errorMessage = '预测失败';
      
      if (status === 400) {
        errorMessage = `输入参数错误: ${data.detail || '请检查输入格式'}`;
      } else if (status === 503) {
        errorMessage = '模型服务暂时不可用，请稍后重试';
      } else if (status === 504) {
        errorMessage = '请求超时，请稍后重试';
      } else if (data?.detail) {
        errorMessage = data.detail;
      } else {
        errorMessage = `服务器错误 (${status})`;
      }
      
      throw new Error(errorMessage);
    } else if (error.request) {
      throw new Error('无法连接到服务器，请检查网络连接');
    } else {
      throw new Error(`请求失败: ${error.message}`);
    }
  }
};
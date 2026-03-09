import { defineStore } from 'pinia';

export const useDdiStore = defineStore('ddi', {
  state: () => ({
    // 缓存用户输入的表单数据
    formData: {
      smiles_a: '',
      smiles_b: '',
      drug_a_name: '',
      drug_b_name: '',
      interaction_type: '',
      include_activations: true,
      include_attention: true
    },
    predictionResult: null 
  }),
  actions: {
    // 预测成功后，保存结果
    setPredictionResult(result) {
      this.predictionResult = result;
    },
    // 提供一个清除历史记录的方法（对应页面上的“重置”按钮）
    clearData() {
      this.formData = {
        smiles_a: '',
        smiles_b: '',
        drug_a_name: '',
        drug_b_name: '',
        interaction_type: '0',
        include_activations: true,
        include_attention: true
      };
      this.predictionResult = null;
    }
  },
  // 开启持久化，数据会自动序列化存入浏览器的 localStorage
  persist: true 
});
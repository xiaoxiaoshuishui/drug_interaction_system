import { defineStore } from 'pinia'

export const useDsaPredictStore = defineStore('dsaPredict', {
  state: () => ({
    lastResult: null,
    lastFormData: {
      drug_identifier: '',
      se_name: ''
    },
    lastRadarData: null,
    lastGraphData: null,
    lastPrediction: null
  }),
  
  actions: {
    setResult(result, formData) {
      this.lastResult = result
      this.lastFormData = { ...formData }
      
      // 保存图表数据
      if (result?.radar_data) {
        this.lastRadarData = result.radar_data
      }
      if (result?.graph_data) {
        this.lastGraphData = result.graph_data
        this.lastPrediction = result.prediction
      }
    },
    
    clearResult() {
      this.lastResult = null
      this.lastFormData = {
        drug_identifier: '',
        se_name: ''
      }
      this.lastRadarData = null
      this.lastGraphData = null
      this.lastPrediction = null
      
      // 同时清除 localStorage
      localStorage.removeItem('dsa-predict')
    }
  },

  persist: {
    key: 'dsa-predict',
    storage: localStorage,
    paths: ['lastResult', 'lastFormData', 'lastRadarData', 'lastGraphData', 'lastPrediction']
  }
})
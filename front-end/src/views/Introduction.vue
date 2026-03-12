<template>
  <div class="introduction-container">
    <!-- 英雄区域 / 平台概览 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">药物不良反应预测平台</span>
        </h1>
        <p class="hero-subtitle">
          基于深度学习的药物相互作用与不良反应智能预测系统
        </p>
        <div class="hero-buttons">
          <van-button type="primary" size="large" round @click="scrollToModels">
            了解更多
          </van-button>
        </div>
      </div>
      <div class="hero-image">
        <img :src="heroIllustration" alt="平台示意图" @error="handleImageError">
      </div>
    </section>

    <!-- 平台特色卡片 -->
    <section class="features-section">
      <h2 class="section-title">核心功能</h2>
      <div class="features-grid">
        <div class="feature-card" v-for="feature in features" :key="feature.title">
          <div class="feature-icon" :style="{ background: feature.iconBg }">
            <van-icon :name="feature.icon" />
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <!-- 双模型架构展示 -->
    <section class="models-section" ref="modelsSection">
      <h2 class="section-title">双引擎智能预测模型</h2>
      <p class="section-subtitle">融合两种先进深度学习架构，提供全面精准的药物分析</p>

      <div class="models-grid">
        <!-- DSN-DDI 模型 -->
        <div class="model-card">
          <div class="model-header dsn">
            <div class="model-icon">
              <van-icon name="cluster" />
            </div>
            <h3>DSN-DDI</h3>
            <span class="model-badge">药物相互作用</span>
          </div>
          <div class="model-content">
            <p class="model-description">
              基于深度序列网络的药物相互作用预测模型，专注于分析两种药物同时使用时的相互影响。
            </p>
            <div class="model-features">
              <div class="model-feature">
                <van-icon name="passed" color="#42b983" />
                <span>注意力机制可视化</span>
              </div>
              <div class="model-feature">
                <van-icon name="passed" color="#42b983" />
                <span>原子级别重要性分析</span>
              </div>
              <div class="model-feature">
                <van-icon name="passed" color="#42b983" />
                <span>相互作用概率预测</span>
              </div>
            </div>
            <van-button type="primary" block to="/ddi/prediction">进入预测</van-button>
          </div>
        </div>

        <!-- MFGNN-DSA 模型 -->
        <div class="model-card">
          <div class="model-header mfgnn">
            <div class="model-icon">
              <van-icon name="share" />
            </div>
            <h3>MFGNN-DSA</h3>
            <span class="model-badge">不良反应预测</span>
          </div>
          <div class="model-content">
            <p class="model-description">
              多视图异质图神经网络模型，通过知识图谱分析药物与不良反应之间的潜在关联。
            </p>
            <div class="model-features">
              <div class="model-feature">
                <van-icon name="passed" color="#42b983" />
                <span>异质网络拓扑分析</span>
              </div>
              <div class="model-feature">
                <van-icon name="passed" color="#42b983" />
                <span>多视图特征融合</span>
              </div>
              <div class="model-feature">
                <van-icon name="passed" color="#42b983" />
                <span>不良反应风险评级</span>
              </div>
            </div>
            <van-button type="primary" block to="/dsa/sider">进入预测</van-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 技术流程 -->
    <div class="workflow-container">
      <section class="workflow-section">
        <h2 class="section-title">DSN-DDI预测流程</h2>
        <div class="workflow-steps">
          <div class="step" v-for="(step, index) in ddiWorkflowSteps" :key="index">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <h4>{{ step.title }}</h4>
              <p>{{ step.description }}</p>
            </div>
          </div>
        </div>
      </section>
      <section class="workflow-section">
        <h2 class="section-title">MFGNN-DSA预测流程</h2>
        <div class="workflow-steps">
          <div class="step" v-for="(step, index) in dsaWorkflowSteps" :key="index">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <h4>{{ step.title }}</h4>
              <p>{{ step.description }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import ADR from '../assets/ADR.png';

const router = useRouter();

const heroIllustration = ref(ADR);

// 平台特色数据
const features = ref([
  {
    icon: 'exchange',
    iconBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    title: '药物相互作用预测',
    description: '基于深度序列网络，精准预测两种药物联合使用时的相互作用类型和概率。'
  },
  {
    icon: 'warning',
    iconBg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    title: '不良反应分析',
    description: '通过多视图异质图神经网络，识别药物与不良反应之间的潜在关联。'
  },
  {
    icon: 'eye',
    iconBg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    title: '注意力可视化',
    description: '直观展示模型关注的原子区域，帮助理解预测结果的化学基础。'
  },
  {
    icon: 'bar-chart-o',
    iconBg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    title: '多维度分析',
    description: '提供概率、置信度、注意力权重等多维度评估指标，全面解读预测结果。'
  }
]);

// 工作流程步骤
const ddiWorkflowSteps = ref([
  {
    title: '输入药物信息',
    description: '输入药物SMILES字符串'
  },
  {
    title: '模型分析',
    description: '深度学习模型自动提取分子特征，进行多维度计算分析'
  },
  {
    title: '生成预测结果',
    description: '输出相互作用类型、概率、置信度等核心指标'
  },
  {
    title: '可视化解读',
    description: '通过注意力热力图、分子高亮等方式直观展示预测依据'
  }
]);

const dsaWorkflowSteps = ref([
  {
    title: '输入查询条件',
    description: '输入药物名称/SMILES和不良反应名称'
  },
  {
    title: '模型分析',
    description: '多视图异质图神经网络提取药物-不良反应图谱特征'
  },
  {
    title: '风险预测',
    description: '输出不良反应风险评级（高风险/安全）和概率得分'
  },
  {
    title: '图谱可视化',
    description: '展示局部异质网络拓扑结构，揭示潜在关联路径'
  }
]);

// 滚动到模型区域
const modelsSection = ref(null);
const scrollToModels = () => {
  if (modelsSection.value) {
    modelsSection.value.scrollIntoView({ behavior: 'smooth' });
  }
};

// 图片加载失败处理
const handleImageError = () => {
  console.log('图片加载失败，使用占位图');
  // 可以设置默认占位图
};
</script>

<style scoped>
.introduction-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
}

/* 英雄区域 */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 24px;
  gap: 40px;
}

.hero-content {
  flex: 1;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 20px;
  line-height: 1.2;
}

.gradient-text {
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 18px;
  color: #6c757d;
  margin-bottom: 30px;
  line-height: 1.6;
}

.hero-stats {
  display: flex;
  gap: 40px;
  margin-bottom: 30px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #4361ee;
}

.stat-label {
  font-size: 14px;
  color: #6c757d;
  margin-top: 4px;
}

.hero-buttons {
  display: flex;
  position: relative;
  left: 15%;
  gap: 16px;
}

.hero-buttons .van-button {
  max-width: 280px;
}

.hero-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.hero-image img {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
}

/* 通用章节样式 */
section {
  padding: 60px 24px;
}

.section-title {
  text-align: center;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 16px;
  color: #2c3e50;
}

.section-subtitle {
  text-align: center;
  font-size: 16px;
  color: #6c757d;
  margin-bottom: 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

/* 特色卡片 */
.features-section {
  background: white;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  padding: 32px 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  text-align: center;
  border: 1px solid #e9ecef;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-icon .van-icon {
  font-size: 28px;
  color: white;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #2c3e50;
}

.feature-card p {
  color: #6c757d;
  line-height: 1.6;
  margin: 0;
}

/* 模型卡片 */
.models-section {
  max-width: 1200px;
  margin: 0 auto;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  margin-top: 40px;
}

.model-card {
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.model-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.model-header {
  padding: 30px 24px;
  text-align: center;
  color: white;
}

.model-header.dsn {
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
}

.model-header.mfgnn {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.model-icon {
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.model-icon .van-icon {
  font-size: 30px;
  color: white;
}

.model-header h3 {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px;
}

.model-badge {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  font-size: 12px;
}

.model-content {
  padding: 24px;
}

.model-description {
  color: #6c757d;
  line-height: 1.6;
  margin-bottom: 20px;
  min-height: 60px;
}

.model-features {
  margin-bottom: 20px;
}

.model-feature {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #495057;
}

.model-feature .van-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.workflow-container {
  display: flex;
  flex-direction: row;
  gap: 20px;
  justify-content: center;
  background-color: #ffffff;
}

.workflow-steps {
  max-width: 800px;
  margin: 0 auto;
}

.step {
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  margin-bottom: 20px;
}

.step:last-child {
  margin-bottom: 0;
}

.step-number {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #4361ee, #3a0ca3);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  padding: 20px;
  border-radius: 12px;
}

.step-content h4 {
  margin: 0 0 8px;
  color: #2c3e50;
  font-size: 16px;
}

.step-content p {
  margin: 0;
  color: #6c757d;
  font-size: 14px;
}

.step-arrow {
  color: #4361ee;
  font-size: 20px;
  margin: 0 10px;
}

/* 应用场景 */
.use-cases-section {
  max-width: 1200px;
  margin: 0 auto;
}

.use-cases-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
}

.use-case-card {
  padding: 24px;
  background: white;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.use-case-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.use-case-icon {
  font-size: 36px;
  color: #4361ee;
  margin-bottom: 16px;
}

.use-case-card h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #2c3e50;
}

.use-case-card p {
  color: #6c757d;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

/* 技术栈 */
.tech-stack-section {
  background: white;
}

.tech-stack-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
  max-width: 1000px;
  margin: 0 auto;
}

.tech-category {
  text-align: center;
}

.tech-category h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #2c3e50;
}

.tech-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.tech-tag {
  padding: 6px 12px;
  background: #f8f9fa;
  border-radius: 20px;
  font-size: 12px;
  color: #495057;
  border: 1px solid #e9ecef;
  transition: all 0.2s;
}

.tech-tag:hover {
  background: #4361ee;
  color: white;
  border-color: #4361ee;
}

/* 联系区域 */
.contact-section {
  background: linear-gradient(135deg, #2c3e50, #1a1a2e);
  color: white;
}

.contact-section .section-title {
  color: white;
}

.contact-content {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.contact-content p {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 30px;
  opacity: 0.9;
}

.contact-links {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.contact-links a {
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 30px;
  transition: all 0.3s;
}

.contact-links a:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}
</style>
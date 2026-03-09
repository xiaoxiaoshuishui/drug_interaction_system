<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-logo">
        <van-image
          width="80"
          height="80"
          :src="ADR2"
          round
        />
        <h2>药物不良反应预测平台</h2>
      </div>
      
      <van-form @submit="onSubmit" class="login-form">
        <van-cell-group inset>
          <van-field
            v-model="username"
            name="username"
            label="用户名"
            placeholder="请输入用户名"
            :rules="[{ required: true, message: '请填写用户名' }]"
          />
          <van-field
            v-model="password"
            type="password"
            name="password"
            label="密码"
            placeholder="请输入密码"
            :rules="[{ required: true, message: '请填写密码' }]"
          />
        </van-cell-group>
        
        <div class="submit-btn">
          <van-button round block type="primary" native-type="submit" size="large">
            登录
          </van-button>
        </div>

         <div class="register-link">
          <span>没有账号？</span>
          <a href="javascript:;" @click="goToRegister">点击注册</a>
        </div>
        
        <div class="login-tips">
          <p>测试账号：admin</p>
          <p>测试密码：123456</p>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { useUserStore } from '../store/user';
import ADR2 from '../assets/ADR2.png';

const router = useRouter();
const userStore = useUserStore();

const username = ref('');
const password = ref('');

const onSubmit = async (values) => {
  // 显示加载提示
  showToast({
    type: 'loading',
    message: '登录中...',
    forbidClick: true,
    duration: 0
  });
  
  try {
    // 调用API登录
    const result = await userStore.login({
      username: username.value,
      password: password.value
    });
    
    if (result.success) {
      showToast({
        type: 'success',
        message: result.message
      });
      console.log('登录成功，跳转首页');
      router.push('/');
    } else {
      showToast({
        type: 'fail',
        message: result.message
      });
    }
  } catch (error) {
    showToast({
      type: 'fail',
      message: '登录失败，请稍后再试'
    });
  }
};

const onClickLeft = () => {
  router.back();
};

const goToRegister = () => {
  router.push('/register');
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background-color: #f7f8fa;
  background-image: url('../assets/ADR.png');
  background-size: cover;
}

.login-container {
  padding-top: 150px;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 30%;
  position: relative;
  left: 50%;
}

.login-logo {
  text-align: center;
}

.login-logo h2 {
  margin-top: 16px;
  color: #0000CD;
  font-size: 22px;
}

.login-form {
  width: 75%;
  padding: 20px 20px;
  border-radius: 5%;
  background-color: rgba(0, 0, 0, 0.8);
}

.submit-btn {
  margin: 24px 16px;
}

.login-tips {
  text-align: center;
  color: #e3e3e3;
  font-size: 14px;
  margin-top: 16px;
}

.login-tips p {
  margin: 8px 0;
}

.register-link {
  text-align: center;
  margin: 16px 0;
  font-size: 14px;
  color: #e3e3e3;
}

.register-link a {
  color: #68acf0;
  text-decoration: none;
  margin-left: 4px;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>
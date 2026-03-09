<template>
  <div class="register-page">
    <!-- <van-nav-bar
      title="用户注册"
      left-arrow
      @click-left="onClickLeft"
      fixed
    /> -->
    
    <div class="register-container">
      <div class="register-logo">
        <van-image
          width="80"
          height="80"
          :src="ADR2"
          round
        />
        <h2>药物不良反应预测平台</h2>
      </div>
      
    <van-form @submit="onSubmit" class="register-form">
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
          <van-field
            v-model="confirmPassword"
            type="password"
            name="confirmPassword"
            label="确认密码"
            placeholder="请再次输入密码"
            :rules="[
              { required: true, message: '请确认密码' },
              { validator: validatePassword, message: '两次密码不一致' }
            ]"
          />
        </van-cell-group>
        
        <div class="submit-btn">
          <van-button round block type="primary" native-type="submit" size="large">
            注册
          </van-button>
        </div>
        
        <div class="login-link">
          已有账号？<span @click="goToLogin">去登录</span>
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
const confirmPassword = ref('');

// 验证两次密码是否一致
const validatePassword = () => {
  return password.value === confirmPassword.value;
};

const onSubmit = async () => {
  // 显示加载提示
  showToast({
    type: 'loading',
    message: '注册中...',
    forbidClick: true,
    duration: 0
  });
  
  try {
    // 调用API注册
    const result = await userStore.register({
      username: username.value,
      password: password.value
    });
    
    if (result.success) {
      showToast({
        type: 'success',
        message: result.message
      });
      
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
      message: '注册失败，请稍后再试'
    });
  }
};

const onClickLeft = () => {
  router.back();
};

const goToLogin = () => {
  router.push('/login');
};
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background-color: #f7f8fa;
  background-image: url('../assets/ADR.png');
  background-size: cover;
}

.register-container {
  padding-top: 150px;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 30%;
  position: relative;
  left: 50%;
}

.register-logo {
  text-align: center;
}

.register-logo h2 {
  margin-top: 16px;
  color: #0000CD;
  font-size: 22px;
}

.register-form {
  width: 75%;
  padding: 20px 20px;
  border-radius: 5%;
  background-color: rgba(0, 0, 0, 0.8);
}

.submit-btn {
  margin: 24px 16px;
}

.login-link {
  text-align: center;
  margin-top: 16px;
  color: #e3e3e3;
  font-size: 14px;
}

.login-link span {
  color: #68acf0;
  cursor: pointer;
  &:hover {
    text-decoration: underline;
  }
}
</style>
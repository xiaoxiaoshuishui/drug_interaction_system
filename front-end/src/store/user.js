import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import userService from '../apis/users';

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null);
  const token = ref('');
  const isLogin = ref(false);
  const userBio = ref('这是我的个人简介');
  const getUserInfo = computed(() => userInfo.value);
  const getToken = computed(() => token.value);
  const getLoginStatus = computed(() => isLogin.value);
  const getUserBio = computed(() => userInfo.value?.bio || userBio.value);

  const login = async (userData) => {
    try {
      const res = await userService.login(userData);
      if (res.code === 200) {
        userInfo.value = res.data.userInfo;
        token.value = res.data.token;
        isLogin.value = true;
        return { success: true, message: '登录成功' };
      } else {
        return { success: false, message: res.message || '登录失败' };
      }
    } catch (error) {
      console.error('登录请求失败:', error);
      return {
        success: false,
        message: error.response?.data?.message || '登录请求失败，请稍后再试'
      };
    }
  };

  const register = async (userData) => {
    try {
      const res = await userService.register(userData);
      if (res.code === 200) {
        userInfo.value = res.data.userInfo;
        token.value = res.data.token;
        isLogin.value = true;
        return { success: true, message: '注册成功' };
      } else {
        return { success: false, message: res.message || '注册失败' };
      }
    } catch (error) {
      console.error('注册请求失败:', error);
      return {
        success: false,
        message: error.response?.data?.message || '注册请求失败，请稍后再试'
      };
    }
  };

  const logout = () => {
    userInfo.value = null;
    token.value = '';
    isLogin.value = false;
  };

  const getUserInfoDetail = async () => {
    if (!token.value) {
      return { success: false, message: '未登录' };
    }
    try {
      const res = await userService.getUserInfo(token.value);
      if (res.code === 200) {
        userInfo.value = res.data;
        return { success: true, message: '获取用户信息成功', data: res.data };
      } else {
        return { success: false, message: res.message || '获取用户信息失败' };
      }
    } catch (error) {
      console.error('获取用户信息请求失败:', error);
      return {
        success: false,
        message: error.response?.data?.message || '获取用户信息请求失败，请稍后再试'
      };
    }
  };

  const updateUserBio = async (bio) => {
    if (!token.value) {
      return { success: false, message: '未登录' };
    }
    try {
      const res = await userService.updateUserBio(token.value, bio);
      if (res.code === 200) {
        if (userInfo.value) userInfo.value.bio = bio;
        return { success: true, message: '更新个人简介成功' };
      } else {
        return { success: false, message: res.message || '更新个人简介失败' };
      }
    } catch (error) {
      console.error('更新个人简介请求失败:', error);
      return {
        success: false,
        message: error.response?.data?.message || '更新个人简介请求失败，请稍后再试'
      };
    }
  };

  const updatePassword = async (oldPassword, newPassword) => {
    if (!token.value) {
      return { success: false, message: '未登录' };
    }
    try {
      const res = await userService.updatePassword(token.value, oldPassword, newPassword);
      if (res.code === 200) {
        return { success: true, message: '密码修改成功' };
      } else {
        return { success: false, message: res.message || '密码修改失败' };
      }
    } catch (error) {
      console.error('修改密码请求失败:', error);
      return {
        success: false,
        message: error.response?.data?.message || '修改密码请求失败，请稍后再试'
      };
    }
  };

  return {
    userInfo,
    token,
    isLogin,
    userBio,
    getUserInfo,
    getToken,
    getLoginStatus,
    getUserBio,
    login,
    register,
    logout,
    getUserInfoDetail,
    updateUserBio,
    updatePassword
  };
}, {
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'user-store',
        storage: localStorage
      }
    ]
  }
});
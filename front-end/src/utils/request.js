import axios from 'axios';
import { apiConfig } from '../config/api';
import { useUserStore } from '../store/user';

// 创建 axios 实例
const request = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: 10000, // 10秒超时
  headers: {
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器
request.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    try {
      const userStore = useUserStore();
      const token = userStore.getToken;
      if (token) {
        config.headers.Authorization = `${token}`;
      }
    } catch (error) {
      console.warn('获取token失败，可能Store未初始化:', error);
    }
    
    // 2. 添加请求时间戳（防止缓存）
    config.headers['X-Request-Timestamp'] = Date.now();
    
    // 3. 对于某些特定请求可以特殊处理
    const url = config.url || '';
    
    // 登录/注册请求不需要token
    if (url.includes('/login') || url.includes('/register')) {
      delete config.headers.Authorization;
    }
    
    // 公开接口不需要token
    if (url.includes('/ddi/simple-predict')) {
      delete config.headers.Authorization;
    }
    
    return config;
  },
  (error) => {
    // 对请求错误做些什么
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器
request.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        const userStore = useUserStore();
        userStore.logout();
        
        // 如果logout()没把localStorage删干净，再补上这句
        // localStorage.removeItem('user');

        showFailToast('登录状态已过期，请重新登录');
        
        router.push('/login');
      }
    }
    return Promise.reject(error);
  }
);

// 导出默认的 request 实例
export default request;


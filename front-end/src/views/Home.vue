<template>
  <div class="admin-container">
    <!-- 侧边栏 -->
     <SideBar 
      :collapsed="sidebarCollapsed" 
      :activeMenu="activeMenu" 
      :menuSections="menuSections"
      @menu-click="setActiveMenu"
    />
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <TopBar 
        :sidebarCollapsed="sidebarCollapsed" 
        :userName="userName" 
        :userAvatar="userAvatar" 
        :darkMode="darkMode" 
        :showNotifications="showNotifications" 
        :unreadNotifications="unreadNotifications"
        :currentMenuTitle="currentMenuTitle"
        @toggle-sidebar="toggleSidebar" 
        @toggle-dark-mode="toggleDarkMode" 
        @toggle-notifications="toggleNotifications" 
        @toggle-user-dropdown="toggleUserDropdown" 
        @mark-all-as-read="markAllAsRead" 
        @logout="logout"
      />
      <router-view></router-view>
      </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, shallowRef, watch } from 'vue'
import { useUserStore } from '../store/user'
import SideBar from '../components/SideBar.vue'
import TopBar from '../components/TopBar.vue'
import ADR2 from '../assets/ADR2.png'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'

const router = useRouter()
const route = useRoute()
// 侧边栏状态
const sidebarCollapsed = ref(false)
const activeMenu = ref('dashboard')

// 用户信息
const userStore = useUserStore()
const userName = ref(userStore.userInfo?.username || '管理员')
const userAvatar = ref(userStore.userInfo?.avatar || ADR2)

// 顶部导航栏状态
const darkMode = ref(false)
const showNotifications = ref(false)
const unreadNotifications = ref(3)
const showUserDropdown = ref(false)
const currentMenuTitle = ref('仪表板')
const menuTitleMap = {
  'dashboard': '仪表板',
  'data': '数据分析',
  'prediction': '药物预测',
  'profile': '个人资料',
  'sider': '不良预测',
  'record': '预测记录'
}

// 菜单数据
const menuSections = ref([
  {
    id: 1,
    title: '主导航',
    items: [
      { id: 'dashboard', text: '仪表板', icon: 'home-o', badge: '' },
      { id: 'data', text: '数据分析', icon: 'bar-chart-o', badge: '新' },
    ]
  },
  {
    id: 2,
    title: 'DNS-DDI',
    items: [
      { id: 'prediction', text: '药物预测', icon: 'setting-o', badge: '' },
      { id: 'profile', text: '个人资料', icon: 'user-o', badge: '' },
    ]
  },
  {
    id: 3,
    title: 'MFGNN-DSA',
    items: [
      { id: 'sider', text: '不良预测', icon: 'records', badge: '' },
      { id: 'record', text: '预测记录', icon: 'question-o', badge: '' },
    ]
  }
])

// 通知数据
const notifications = ref([
  { id: 1, title: '新用户注册', time: '10分钟前', icon: 'fas fa-user-plus', read: false },
  { id: 2, title: '订单支付成功', time: '30分钟前', icon: 'fas fa-check-circle', read: false },
  { id: 3, title: '系统备份完成', time: '2小时前', icon: 'fas fa-save', read: true },
  { id: 4, title: '安全提醒', time: '5小时前', icon: 'fas fa-exclamation-triangle', read: false },
  { id: 5, title: '版本更新', time: '昨天', icon: 'fas fa-upload', read: true },
])

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const setActiveMenu = (menuId) => {
  activeMenu.value = menuId
  currentMenuTitle.value = menuTitleMap[menuId] || '仪表板'
  const routeMap = {
    'dashboard': '/home/dashboard',
    'data': '/home/data',
    'prediction': '/ddi/prediction',
    'profile': '/ddi/profile',
    'sider': '/dsa/sider',
    'record': '/dsa/record'
  };
  
  const targetRoute = routeMap[menuId];
  
  if (targetRoute) {
    router.push(targetRoute);
  } else {
    console.warn(`未找到菜单项 ${menuId} 对应的路由`);
    // 默认跳转到仪表板
    router.push('/home/dashboard');
  }
}

const toggleDarkMode = () => {
  darkMode.value = !darkMode.value
  if (darkMode.value) {
    document.body.classList.add('dark-mode')
  } else {
    document.body.classList.remove('dark-mode')
  }
}

const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  // 关闭用户下拉菜单
  showUserDropdown.value = false
}

const toggleUserDropdown = () => {
  showUserDropdown.value = !showUserDropdown.value
  // 关闭通知下拉菜单
  showNotifications.value = false
}

const markAllAsRead = () => {
  notifications.value.forEach(notification => {
    notification.read = true
  })
  unreadNotifications.value = 0
}

const logout = async () => {
  if (confirm('确定要退出登录吗？')) {
    try {
      // 显示退出中的提示
      const toast = showLoadingToast({
        message: '退出登录中...',
        forbidClick: true,
        duration: 0
      })
      
      // 执行退出登录的逻辑
      userStore.logout()
      console.log('用户退出登录')
      
      // 关闭加载提示
      closeToast()
      
      // 显示成功提示
      showToast({
        type: 'success',
        message: '退出登录成功',
        duration: 1000
      })
      router.push('/login')
      
    } catch (error) {
      console.error('退出登录失败:', error)
      closeToast() // 确保关闭加载提示
      
      // 显示错误提示
      showToast({
        type: 'fail',
        message: '退出登录失败，请重试',
        duration: 2000
      })
    }
  }
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event) => {
  if (!event.target.closest('.notification-wrapper')) {
    showNotifications.value = false
  }
  if (!event.target.closest('.user-dropdown-wrapper')) {
    showUserDropdown.value = false
  }
}

// 检查用户登录状态
const checkLoginStatus = () => {
  if (!userStore.token || !userStore.isLogin) {
    console.log('用户未登录或token无效，跳转到登录页')
    router.push('/login')
    return false
  }
  
  console.log('用户已登录，token:', userStore.token.substring(0, 10) + '...')
  return true
}

// 生命周期钩子
onMounted(async() => {
  document.addEventListener('click', handleClickOutside)

  try {
    // 检查登录状态
    if (!checkLoginStatus()) {
      return
    }} catch (error) {
    console.error('检查登录状态时出错:', error)
    router.push('/login')
  }
  // 计算未读通知数量
  unreadNotifications.value = notifications.value.filter(n => !n.read).length
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 监听路由变化，更新当前菜单标题
watch(() => route.path, (newPath) => {
  // 根据路由路径更新当前菜单标题
  if (newPath.includes('/home/dashboard')) {
    currentMenuTitle.value = '仪表板';
    activeMenu.value = 'dashboard';
  } else if (newPath.includes('/home/data')) {
    currentMenuTitle.value = '数据分析';
    activeMenu.value = 'data';
  } else if (newPath.includes('/ddi/prediction')) {
    currentMenuTitle.value = '药物预测';
    activeMenu.value = 'prediction';
  } else if (newPath.includes('/ddi/profile')) {
    currentMenuTitle.value = '个人资料';
    activeMenu.value = 'profile';
  } else if (newPath.includes('/dsa/sider')) {
    currentMenuTitle.value = '不良预测';
    activeMenu.value = 'sider';
  } else if (newPath.includes('/dsa/record')) {
    currentMenuTitle.value = '预测记录';
    activeMenu.value = 'record';
  }
}, { immediate: true })
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

:root {
  --primary-color: #4361ee;
  --secondary-color: #3a0ca3;
  --accent-color: #4cc9f0;
  --light-color: #f8f9fa;
  --dark-color: #212529;
  --success-color: #4ade80;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
  --sidebar-width: 250px;
  --sidebar-collapsed-width: 70px;
  --topbar-height: 70px;
  --border-radius: 8px;
  --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
}

body.dark-mode {
  --light-color: #1a1a1a;
  --dark-color: #f8f9fa;
  background-color: #121212;
  color: #f8f9fa;
}

.admin-container {
  display: flex;
  min-height: 100vh;
  background-color: #f5f7fb;
}

/* 侧边栏样式 */
.sidebar {
  width: var(--sidebar-width);
  background: #4361ee;
  color: white;
  display: flex;
  flex-direction: column;
  transition: var(--transition);
  z-index: 100;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-header {
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  font-weight: 700;
  display: flex;
  align-items: center;
}

.logo-collapsed {
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  justify-content: center;
}

.collapse-btn {
  /* 三角形箭头核心代码 */
  width: 0;
  height: 0;
  border: 6px solid transparent;
  border-right-color: #007bff; /* 右箭头 */
  background: none;
  cursor: pointer;
  padding: 0;
  transition: all 0.3s ease;
}
.collapse-btn.collapsed {
  transform: rotate(180deg);
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.sidebar-menu {
  flex: 1;
  padding: 20px 0;
  overflow-y: auto;
}

.menu-section {
  margin-bottom: 25px;
}

.section-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  opacity: 0.7;
  padding: 0 20px;
  margin-bottom: 10px;
  letter-spacing: 1px;
}

.menu-items {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
}

.menu-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.menu-item.active {
  background-color: rgba(255, 255, 255, 0.15);
  border-left: 3px solid var(--accent-color);
}

.menu-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-text {
  margin-left: 15px;
  flex: 1;
}

.menu-badge {
  background-color: var(--accent-color);
  color: white;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.user-details {
  margin-left: 10px;
}

.user-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.system-info {
  font-size: 0.8rem;
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部导航栏样式 */
.topbar {
  height: var(--topbar-height);
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 25px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  z-index: 90;
}

body.dark-mode .topbar {
  background-color: #1a1a1a;
  color: white;
}

.topbar-left {
  display: flex;
  align-items: center;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breadcrumb-item {
  font-size: 0.9rem;
  color: #6c757d;
}

.breadcrumb-item.active {
  color: var(--primary-color);
  font-weight: 600;
}

.breadcrumb-separator {
  color: #adb5bd;
}

.topbar-right {
  display: flex;
  align-items: center;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.action-btn {
  background: none;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6c757d;
  transition: var(--transition);
  position: relative;
}

.action-btn:hover {
  background-color: #f8f9fa;
  color: var(--primary-color);
}

body.dark-mode .action-btn:hover {
  background-color: #2a2a2a;
}

.notification-indicator {
  position: absolute;
  top: 5px;
  right: 5px;
  background-color: var(--danger-color);
  color: white;
  font-size: 0.7rem;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-wrapper {
  position: relative;
}

.notification-dropdown {
  position: absolute;
  top: 50px;
  right: 0;
  width: 350px;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  z-index: 1000;
}

body.dark-mode .notification-dropdown {
  background-color: #2a2a2a;
  color: white;
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

body.dark-mode .notification-header {
  border-bottom-color: #444;
}

.notification-header h4 {
  font-size: 1rem;
  font-weight: 600;
}

.mark-all-read {
  background: none;
  border: none;
  color: var(--primary-color);
  font-size: 0.8rem;
  cursor: pointer;
  transition: var(--transition);
}

.mark-all-read:hover {
  text-decoration: underline;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  padding: 15px 20px;
  gap: 15px;
  border-bottom: 1px solid #f5f5f5;
  transition: var(--transition);
}

body.dark-mode .notification-item {
  border-bottom-color: #444;
}

.notification-item:hover {
  background-color: #f9f9f9;
}

body.dark-mode .notification-item:hover {
  background-color: #333;
}

.notification-item.unread {
  background-color: rgba(67, 97, 238, 0.05);
}

body.dark-mode .notification-item.unread {
  background-color: rgba(67, 97, 238, 0.2);
}

.notification-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(67, 97, 238, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 5px;
}

.notification-time {
  font-size: 0.8rem;
  color: #6c757d;
}

body.dark-mode .notification-time {
  color: #aaa;
}

.notification-footer {
  padding: 15px 20px;
  text-align: center;
  border-top: 1px solid #eee;
}

body.dark-mode .notification-footer {
  border-top-color: #444;
}

.notification-footer a {
  color: var(--primary-color);
  text-decoration: none;
  font-size: 0.9rem;
}

.notification-footer a:hover {
  text-decoration: underline;
}

.user-dropdown-wrapper {
  position: relative;
}

.user-dropdown-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: none;
  padding: 8px 12px;
  border-radius: 30px;
  cursor: pointer;
  transition: var(--transition);
}

.user-dropdown-btn:hover {
  background-color: #f8f9fa;
}

body.dark-mode .user-dropdown-btn:hover {
  background-color: #2a2a2a;
}

.user-avatar-small {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  object-fit: cover;
}

.user-name-small {
  font-weight: 500;
}

.user-dropdown {
  position: absolute;
  top: 55px;
  right: 0;
  width: 250px;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  z-index: 1000;
}

body.dark-mode .user-dropdown {
  background-color: #2a2a2a;
  color: white;
}

.dropdown-header {
  display: flex;
  align-items: center;
  padding: 20px;
  gap: 15px;
  border-bottom: 1px solid #eee;
}

body.dark-mode .dropdown-header {
  border-bottom-color: #444;
}

.dropdown-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
}

.dropdown-user-info {
  flex: 1;
}

.dropdown-user-name {
  font-weight: 600;
  margin-bottom: 5px;
}

.dropdown-menu {
  padding: 10px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  color: #333;
  text-decoration: none;
  transition: var(--transition);
}

body.dark-mode .dropdown-item {
  color: white;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

body.dark-mode .dropdown-item:hover {
  background-color: #333;
}

.dropdown-item i {
  width: 20px;
  text-align: center;
}

.dropdown-divider {
  height: 1px;
  background-color: #eee;
  margin: 10px 0;
}

body.dark-mode .dropdown-divider {
  background-color: #444;
}

.dropdown-item.logout {
  color: var(--danger-color);
}

/* 主要内容区域样式 */
.content-area {
  flex: 1;
  padding: 25px;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--dark-color);
}

.page-actions {
  display: flex;
  gap: 15px;
}

.btn {
  padding: 10px 20px;
  border-radius: var(--border-radius);
  border: none;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: var(--transition);
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background-color: var(--secondary-color);
}

.btn-secondary {
  background-color: #e9ecef;
  color: var(--dark-color);
}

.btn-secondary:hover {
  background-color: #dee2e6;
}

body.dark-mode .btn-secondary {
  background-color: #333;
  color: white;
}

body.dark-mode .btn-secondary:hover {
  background-color: #444;
}

.content-placeholder {
  background-color: white;
  border-radius: var(--border-radius);
  padding: 50px;
  box-shadow: var(--box-shadow);
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

body.dark-mode .content-placeholder {
  background-color: #1a1a1a;
}

.placeholder-content {
  text-align: center;
  max-width: 500px;
}

.placeholder-icon {
  font-size: 4rem;
  color: var(--primary-color);
  margin-bottom: 20px;
}

.placeholder-content h2 {
  font-size: 1.8rem;
  margin-bottom: 15px;
  color: var(--dark-color);
}

body.dark-mode .placeholder-content h2 {
  color: white;
}

.placeholder-content p {
  color: #6c757d;
  margin-bottom: 10px;
  line-height: 1.6;
}

body.dark-mode .placeholder-content p {
  color: #aaa;
}

.placeholder-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 30px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.stat-item i {
  font-size: 2rem;
  color: var(--primary-color);
}

.stat-item span {
  font-weight: 500;
}

/* 页脚样式 */
.footer {
  padding: 20px 25px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  color: #6c757d;
}

body.dark-mode .footer {
  border-top-color: #444;
  color: #aaa;
}

.footer-links {
  display: flex;
  gap: 20px;
}

.footer-links a {
  color: #6c757d;
  text-decoration: none;
  transition: var(--transition);
}

body.dark-mode .footer-links a {
  color: #aaa;
}

.footer-links a:hover {
  color: var(--primary-color);
}

/* 响应式设计 */
@media (max-width: 992px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    transform: translateX(0);
  }
  
  .sidebar.collapsed {
    transform: translateX(-100%);
  }
  
  .main-content {
    margin-left: 0;
  }
  
  .notification-dropdown {
    right: -100px;
    width: 300px;
  }
}

@media (max-width: 768px) {
  .topbar {
    padding: 0 15px;
  }
  
  .user-name-small {
    display: none;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .page-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .footer {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .notification-dropdown {
    width: 280px;
    right: -140px;
  }
}
</style>
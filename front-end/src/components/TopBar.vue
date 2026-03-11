<template>
  <header class="topbar">
    <div class="topbar-left">
      <div class="breadcrumb">
        <button class="collapse-btn" @click="onToggleSidebar" :class="{ 'collapsed': sidebarCollapsed }">
        </button>
        <span class="breadcrumb-item active">{{ currentMenuTitle }}</span>
      </div>
    </div>

    <div class="topbar-right">
      <div class="topbar-actions">
        <div class="user-dropdown-wrapper">
          <button class="user-dropdown-btn" @click="toggleUserDropdown">
            <img :src="userAvatar" alt="用户头像" class="user-avatar-small">
            <span class="user-name-small">{{ userName }}</span>
            <i class="fas fa-chevron-down"></i>
          </button>
          <div class="user-dropdown" v-if="showUserDropdown">
            <div class="dropdown-header">
              <img :src="userAvatar" alt="用户头像" class="dropdown-avatar">
              <div class="dropdown-user-info">
                <p class="dropdown-user-name">{{ userName }}</p>
              </div>
            </div>
            <div class="dropdown-menu">
              <a href="javascript:void(0)" class="dropdown-item" @click="router.push('/profile')">
                <i class="fas fa-user"></i>
                <span>个人资料</span>
              </a>

              <a href="javascript:void(0)" class="dropdown-item" @click="router.push('/account')">
                <i class="fas fa-cog"></i>
                <span>账户设置</span>
              </a>

              <div class="dropdown-divider"></div>

              <a href="javascript:void(0)" class="dropdown-item text-danger" @click="handleLogout">
                <i class="fas fa-sign-out-alt"></i>
                <span>退出登录</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, defineProps, defineEmits, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import ADR2 from '../assets/ADR2.png';
const router = useRouter()
const props = defineProps({
  sidebarCollapsed: {
    type: Boolean,
    default: false
  },
  userName: {
    type: String,
    default: '管理员'
  },
  userAvatar: {
    type: String,
    default: ADR2
  },
  currentMenuTitle: {
    type: String,
    default: '仪表板'
  }
})

const emit = defineEmits(['toggle-sidebar', 'logout'])

const showUserDropdown = ref(false)

const onToggleSidebar = () => {
  emit('toggle-sidebar')
}

const toggleUserDropdown = () => {
  showUserDropdown.value = !showUserDropdown.value
}

const handleLogout = () => {
  localStorage.removeItem('user')
  emit('logout')
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event) => {
  if (!event.target.closest('.user-dropdown-wrapper')) {
    showUserDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.topbar {
  height: 70px;
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

.collapse-btn {
  width: 0;
  height: 0;
  border: 6px solid transparent;
  border-right-color: #007bff;
  background: none;
  cursor: pointer;
  padding: 0;
  transition: all 0.3s ease;
}

.collapse-btn.collapsed {
  transform: rotate(180deg);
}

.collapse-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.breadcrumb-item {
  font-size: 0.9rem;
  color: #6c757d;
}

.breadcrumb-item.active {
  color: #4361ee;
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
  transition: all 0.3s ease;
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
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
  transition: all 0.3s ease;
}

.text-danger {
  color: #ef4444;
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

.dropdown-divider {
  height: 1px;
  background-color: #eee;
  margin: 10px 0;
}

body.dark-mode .dropdown-divider {
  background-color: #444;
}

.dropdown-item.logout {
  color: #ef4444;
}

@media (max-width: 768px) {
  .topbar {
    padding: 0 15px;
  }

  .user-name-small {
    display: none;
  }
}
</style>
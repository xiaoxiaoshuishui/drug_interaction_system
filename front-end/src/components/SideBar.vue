<template>
  <aside class="sidebar" :class="{ collapsed: collapsed }">
    <div class="sidebar-header">
      <h2 v-if="!collapsed" class="logo">
        药物不良反应预测
      </h2>
    </div>
    
    <div class="sidebar-menu">
      <div class="menu-section" v-for="section in menuSections" :key="section.id">
        <h3 v-if="!collapsed" class="section-title">{{ section.title }}</h3>
        <div class="menu-items">
          <div 
            class="menu-item" 
            v-for="item in section.items" 
            :key="item.id"
            :class="{ active: activeMenu === item.id }"
            @click="onMenuClick(item.id)"
          >
            <div class="menu-icon">
              <van-icon :name="item.icon"></van-icon>
            </div>
            <span v-if="!collapsed" class="menu-text">{{ item.text }}</span>
            <div v-if="!collapsed && item.badge" class="menu-badge">{{ item.badge }}</div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  },
  activeMenu: {
    type: String,
    default: 'dashboard'
  },
  menuSections: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['menu-click'])

const onMenuClick = (menuId) => {
  emit('menu-click', menuId)
}
</script>

<style scoped>
.sidebar {
  width: 250px;
  background: #4361ee;
  color: white;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  z-index: 100;
}

.sidebar.collapsed {
  width: 70px;
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
  transition: all 0.3s ease;
  position: relative;
}

.menu-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.menu-item.active {
  background-color: rgba(255, 255, 255, 0.15);
  border-left: 3px solid #4cc9f0;
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
  background-color: #4cc9f0;
  color: white;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

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
}
</style>
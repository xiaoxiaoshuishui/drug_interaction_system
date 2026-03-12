<template>
  <div class="profile-container">
    <van-nav-bar :title="isSelf ? '个人资料' : '用户主页'" left-text="返回" left-arrow @click-left="router.back()" fixed
      placeholder />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <van-skeleton title avatar :row="8" />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <van-empty description="加载失败">
        <van-button round type="primary" size="small" @click="refreshData">
          重试
        </van-button>
      </van-empty>
    </div>

    <!-- 主要内容 -->
    <template v-else>
      <!-- 头部：封面 + 头像 -->
      <div class="profile-header">
        <div class="cover-image">
          <img :src="coverImage" alt="cover" @error="handleCoverError">
          <div v-if="isSelf" class="edit-cover">
            <van-uploader :after-read="afterCoverRead" accept="image/*">
              <van-icon name="photograph" />
              <span>更换封面</span>
            </van-uploader>
          </div>
        </div>

        <div class="avatar-section">
          <div class="avatar-wrapper" @click="previewAvatar">
            <van-image round width="80" height="80" :src="userAvatar" @error="handleAvatarError">
              <template v-slot:error>
                <img :src="defaultAvatar" alt="默认头像" style="width:100%;height:100%;border-radius:50%;">
              </template>
            </van-image>
            <div v-if="isSelf" class="edit-avatar">
              <van-uploader :after-read="afterAvatarRead" accept="image/*" max-size="5 * 1024 * 1024"
                @oversize="onAvatarOversize">
                <van-icon name="photograph" />
              </van-uploader>
            </div>
          </div>
        </div>
      </div>

      <!-- 用户基本信息 -->
      <div class="user-info-section">
        <div class="user-name-wrapper">
          <h2 class="nickname">{{ displayName }}</h2>
          <van-tag v-if="isSelf" type="primary" size="small">我的主页</van-tag>
          <van-tag v-else type="success" size="small">访客模式</van-tag>
        </div>

        <p class="username">@{{ userInfo?.username || '用户名' }}</p>

        <!-- 个人简介 -->
        <div class="bio-section">
          <template v-if="!isEditingBio">
            <p class="bio-text" :class="{ 'empty-bio': !getUserBio }">
              {{ getUserBio }}
            </p>
            <van-icon v-if="isSelf" name="edit" class="edit-icon" @click="startEditBio" />
          </template>
          <template v-else>
            <van-field v-model="editingBio" type="textarea" maxlength="500" show-word-limit autosize
              placeholder="填写你的个人简介..." @blur="saveBio" @keyup.enter="saveBio" />
          </template>
        </div>
      </div>

      <!-- 账户设置区域 -->
      <div v-if="isSelf" class="settings-section">
        <!-- 账户安全分组 -->
        <van-cell-group inset title="账户安全">
          <van-cell title="修改密码" is-link @click="showPasswordDialog = true">
            <template #icon>
              <van-icon name="lock" class="cell-icon" />
            </template>
          </van-cell>
        </van-cell-group>

        <!-- 危险区域 -->
        <van-cell-group inset title="危险区域" class="danger-zone">
          <van-cell title="注销账户" title-class="danger-text" is-link @click="showLogoutDialog = true" />
        </van-cell-group>

        <!-- 退出登录按钮 -->
        <div class="logout-button">
          <van-button type="danger" block round @click="handleLogout">
            退出登录
          </van-button>
        </div>
      </div>

      <!-- 用户动态/预测列表 -->
      <div class="user-predictions" :class="{ 'no-settings': !isSelf }">
        <div class="section-title">
          <span>最近的预测记录</span>
        </div>

        <van-tabs v-model:active="activeTab" animated swipeable color="#1989fa">

          <van-tab title="药物相互作用 (DDI)">
            <div v-if="predictionsLoading" class="predictions-skeleton">
              <van-skeleton title :row="2" v-for="n in 3" :key="n" />
            </div>

            <van-empty v-else-if="ddiPredictions.length === 0" description="暂无DDI预测记录">
              <van-button v-if="isSelf" round type="primary" size="small" to="/home/chat">去预测</van-button>
            </van-empty>

            <div v-else class="predictions-list">
              <div v-for="record in ddiPredictions" :key="'ddi-' + record.id" class="prediction-card">
                <div class="drug-pair">
                  <span class="drug">{{ truncateName(record.drug_a_name) }}</span>
                  <van-icon name="exchange" class="arrow-icon" />
                  <span class="drug">{{ truncateName(record.drug_b_name) }}</span>
                  <van-icon name="arrow" class="arrow-icon" style="font-size: 12px; margin: 0 4px;" />
                  <div class="prediction-info se-text">
                    <span class="ddi-desc" :title="getDdiTypeName(record)">
                      {{ getDdiTypeName(record) }}
                    </span>
                  </div>
                </div>
                <div class="prediction-info" style="margin-bottom: 6px;">
                  <van-tag :type="getDdiRiskType(record)" size="small">
                    {{ getDdiRiskLabel(record) }}
                  </van-tag>
                </div>
                <span class="time">{{ formatRelativeTime(record.created_at) }}</span>
              </div>
              <div class="view-more-btn" @click="router.push('/ddi/history')">
                查看全部 DDI 记录 <van-icon name="arrow" />
              </div>
            </div>
          </van-tab>

          <van-tab title="药物不良反应 (DSA)">
            <div v-if="predictionsLoading" class="predictions-skeleton">
              <van-skeleton title :row="2" v-for="n in 3" :key="n" />
            </div>

            <van-empty v-else-if="dsaPredictions.length === 0" description="暂无DSA预测记录">
              <van-button v-if="isSelf" round type="primary" size="small" to="/home/introduction">去预测</van-button>
            </van-empty>

            <div v-else class="predictions-list">
              <div v-for="record in dsaPredictions" :key="'dsa-' + record.id" class="prediction-card">
                <div class="drug-pair">
                  <span class="drug">{{ truncateName(record.drug_identifier) }}</span>
                  <van-icon name="arrow" class="arrow-icon" style="font-size: 12px; margin: 0 4px;" />
                  <span class="drug se-text">{{ record.se_name }}</span>
                </div>
                <div class="prediction-info">
                  <van-tag :type="record.prediction_label === 'risk' ? 'danger' : 'success'" size="small">
                    {{ record.prediction_label === 'risk' ? '存在风险' : '安全' }}
                  </van-tag>
                </div>
                <span class="time">{{ formatRelativeTime(record.created_at) }}</span>

              </div>
              <div class="view-more-btn" @click="router.push('/dsa/record')">
                查看全部 DSA 记录 <van-icon name="arrow" />
              </div>
            </div>
          </van-tab>

        </van-tabs>
      </div>
    </template>

    <!-- 修改密码弹窗 -->
    <van-dialog v-model:show="showPasswordDialog" title="修改密码" show-cancel-button confirm-button-text="确认"
      cancel-button-text="取消" @confirm="updatePassword" :before-close="beforePasswordClose">
      <div class="dialog-content">
        <van-field v-model="passwordForm.oldPassword" type="password" label="旧密码" placeholder="请输入旧密码"
          :error-message="passwordErrors.oldPassword" @blur="validateOldPassword" />
        <van-field v-model="passwordForm.newPassword" type="password" label="新密码" placeholder="请输入新密码"
          :error-message="passwordErrors.newPassword" @blur="validateNewPassword" />
        <van-field v-model="passwordForm.confirmPassword" type="password" label="确认密码" placeholder="请再次输入新密码"
          :error-message="passwordErrors.confirmPassword" @blur="validateConfirmPassword" />
        <div class="password-rule">
          <p>密码必须包含：</p>
          <ul>
            <li :class="{ valid: passwordRules.length }">至少8位字符</li>
            <li :class="{ valid: passwordRules.letter }">包含字母</li>
            <li :class="{ valid: passwordRules.number }">包含数字</li>
          </ul>
        </div>
      </div>
    </van-dialog>

    <!-- 注销确认弹窗 -->
    <van-dialog v-model:show="showLogoutDialog" title="注销账户" message="注销后，您的所有数据将被永久删除，且无法恢复。确定要继续吗？" show-cancel-button
      confirm-button-text="确认注销" confirm-button-color="#ee0a24" @confirm="logoutAccount" />

    <!-- 图片预览弹窗 -->
    <van-image-preview v-model:show="showPreview" :images="previewImages" />
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { showConfirmDialog, showSuccessToast, showFailToast, showToast } from 'vant';
import { useUserStore } from '../store/user';
import userService from '../apis/users';
import { getDsaHistory } from '../apis/dsas';
import { getDdiHistory } from '../apis/ddis';
import ADR from '../assets/ADR.png';
import ADR2 from '../assets/ADR2.png';
import { REACTION_TYPE_MAP } from '../utils/reactionType';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 状态变量
const loading = ref(true);
const error = ref(false);
const userInfo = ref(null);
const predictions = ref([]);
const predictionsLoading = ref(false);
const isEditingBio = ref(false);
const editingBio = ref('');
const showPreview = ref(false);
const previewImages = ref([]);

const activeTab = ref(0);
const ddiPredictions = ref([]);
const dsaPredictions = ref([]);

// 账户设置相关状态
const showPasswordDialog = ref(false);
const showLogoutDialog = ref(false);

// 密码表单
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const passwordErrors = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const passwordRules = computed(() => ({
  length: passwordForm.newPassword.length >= 8,
  letter: /[a-zA-Z]/.test(passwordForm.newPassword),
  number: /[0-9]/.test(passwordForm.newPassword)
}));

// 统计数据
const statistics = computed(() => ({
  predictionCount: predictions.value.length,
}));

// 默认图片
const defaultAvatar = ADR2;
const defaultCover = ADR;

// 封面图片
const coverImage = ref(defaultCover);

// 计算属性
const targetUserId = computed(() => route.params.id || userStore.userInfo?.id);
const isSelf = computed(() => {
  return !route.params.id || route.params.id === String(userStore.userInfo?.id);
});

const userAvatar = computed(() => {
  return userInfo.value?.avatar || defaultAvatar;
});

const displayName = computed(() => {
  return userInfo.value?.nickname || userInfo.value?.username || '用户';
});

const getUserBio = computed(() => {
  return userInfo.value?.bio || '这个人很懒，什么都没留下';
});

// 方法
const loadUserData = async () => {
  if (!targetUserId.value) {
    error.value = true;
    loading.value = false;
    return;
  }
  loading.value = true;
  error.value = false;

  try {
    if (isSelf.value) {
      userInfo.value = userStore.userInfo;
      if (!userInfo.value) {
        const res = await userService.getUserInfo(userStore.token);
        if (res.code === 200) userInfo.value = res.data;
      }
    } else {
      const res = await userService.getUserInfoById(targetUserId.value);
      if (res.code === 200) userInfo.value = res.data;
    }

    await loadUserPredictions();
  } catch (err) {
    error.value = true;
  } finally {
    loading.value = false;
  }
};

const truncateName = (name) => {
  if (!name) return '未知';
  return name.length > 15 ? name.substring(0, 15) + '...' : name;
};

const loadUserPredictions = async () => {
  if (!targetUserId.value) return;

  predictionsLoading.value = true;
  try {
    const [ddiRes, dsaRes] = await Promise.allSettled([
      getDdiHistory({ page: 1, page_size: 5 }),
      getDsaHistory({ page: 1, page_size: 5 })
    ]);

    // 处理 DDI 响应
    if (ddiRes.status === 'fulfilled') {
      const ddiData = ddiRes.value.data || ddiRes.value;
      console.log('DDI历史记录:', ddiData);
      ddiPredictions.value = ddiData || [];
    }

    // 处理 DSA 响应
    if (dsaRes.status === 'fulfilled') {
      const dsaData = dsaRes.value.data || dsaRes.value;
      dsaPredictions.value = dsaData || [];
    }
  } catch (err) {
    console.error('加载预测列表失败:', err);
  } finally {
    predictionsLoading.value = false;
  }
};

const refreshData = () => {
  loadUserData();
};

// 头像相关
const handleAvatarError = () => {
  if (userInfo.value) {
    userInfo.value.avatar = defaultAvatar;
  }
};

const previewAvatar = () => {
  previewImages.value = [userAvatar.value];
  showPreview.value = true;
};

const afterAvatarRead = async (file) => {
  try {
    showToast('头像上传功能开发中');

    /* 实际调用示例：
    const formData = new FormData();
    formData.append('avatar', file.file);
    
    const res = await userService.uploadAvatar(userStore.token, formData);
    if (res.code === 200) {
      userInfo.value.avatar = res.data.avatarUrl;
      if (isSelf.value) {
        userStore.userInfo.avatar = res.data.avatarUrl;
      }
      showSuccessToast('头像更新成功');
    } else {
      throw new Error(res.message);
    }
    */
  } catch (err) {
    showFailToast('头像上传失败');
  }
};

const onAvatarOversize = () => {
  showToast('图片大小不能超过5MB');
};

// 封面相关
const handleCoverError = () => {
  coverImage.value = defaultCover;
};

const afterCoverRead = async (file) => {
  try {
    showToast('封面上传功能开发中');

    /* 实际调用示例：
    const formData = new FormData();
    formData.append('cover', file.file);
    
    const res = await userService.uploadCover(userStore.token, formData);
    if (res.code === 200) {
      coverImage.value = res.data.coverUrl;
      showSuccessToast('封面更新成功');
    }
    */
  } catch (err) {
    showFailToast('封面上传失败');
  }
};

// 简介编辑
const startEditBio = () => {
  editingBio.value = userInfo.value?.bio || '';
  isEditingBio.value = true;
};

const saveBio = async () => {
  if (!isEditingBio.value) return;

  if (editingBio.value === userInfo.value?.bio) {
    isEditingBio.value = false;
    return;
  }

  try {
    const res = await userStore.updateUserBio(editingBio.value);
    if (res.success) {
      userInfo.value.bio = editingBio.value;
      showSuccessToast('更新成功');
    } else {
      showFailToast(res.message);
    }
  } catch (err) {
    showFailToast('更新失败');
  } finally {
    isEditingBio.value = false;
  }
};

// 密码相关
const validateOldPassword = () => {
  if (!passwordForm.oldPassword) {
    passwordErrors.oldPassword = '请输入旧密码';
    return false;
  }
  passwordErrors.oldPassword = '';
  return true;
};

const validateNewPassword = () => {
  if (!passwordForm.newPassword) {
    passwordErrors.newPassword = '请输入新密码';
    return false;
  }
  if (passwordForm.newPassword.length < 8) {
    passwordErrors.newPassword = '密码长度不能少于8位';
    return false;
  }
  if (!/(?=.*[a-zA-Z])(?=.*[0-9])/.test(passwordForm.newPassword)) {
    passwordErrors.newPassword = '密码必须包含字母和数字';
    return false;
  }
  passwordErrors.newPassword = '';
  return true;
};

const validateConfirmPassword = () => {
  if (!passwordForm.confirmPassword) {
    passwordErrors.confirmPassword = '请确认新密码';
    return false;
  }
  if (passwordForm.confirmPassword !== passwordForm.newPassword) {
    passwordErrors.confirmPassword = '两次输入的密码不一致';
    return false;
  }
  passwordErrors.confirmPassword = '';
  return true;
};

const beforePasswordClose = (action) => {
  if (action === 'confirm') {
    if (!validateOldPassword() || !validateNewPassword() || !validateConfirmPassword()) {
      return false;
    }
  }
  return true;
};

const updatePassword = async () => {
  if (!validateOldPassword() || !validateNewPassword() || !validateConfirmPassword()) {
    return;
  }

  try {
    const res = await userStore.updatePassword(passwordForm.oldPassword, passwordForm.newPassword);
    if (res.success) {
      showSuccessToast('密码修改成功');
      showPasswordDialog.value = false;
      // 清空表单
      passwordForm.oldPassword = '';
      passwordForm.newPassword = '';
      passwordForm.confirmPassword = '';
    } else {
      showFailToast(res.message);
    }
  } catch (err) {
    showFailToast('密码修改失败');
  }
};

// 退出登录
const handleLogout = () => {
  showConfirmDialog({
    title: '退出登录',
    message: '确定要退出当前账号吗？'
  }).then(() => {
    userStore.logout();
    router.push('/login');
    showSuccessToast('已退出登录');
  }).catch(() => { });
};

// 注销账户
const logoutAccount = () => {
  // 调用注销接口
  showSuccessToast('账户已注销');
  userStore.logout();
  router.push('/register');
};

// 格式化时间
const formatRelativeTime = (date) => {
  if (!date) return '';

  const now = new Date();
  const past = new Date(date);
  const diff = now - past;

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;

  return past.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};

const getDdiTypeName = (record) => {
  const typeId = record.interaction_type_id;
  return REACTION_TYPE_MAP[typeId] || '未知机制';
};

const getDdiRiskLabel = (record) => {
  const label = record.prediction_label;
  if (label === 'safe') return '安全';
  if (label === 'risk') return '存在风险';
};

const getDdiRiskType = (record) => {
  const label = getDdiRiskLabel(record);
  return label === '安全' ? 'success' : 'danger';
};
// 监听路由参数变化
watch(() => route.params.id, () => {
  loadUserData();
});

// 初始化
onMounted(() => {
  loadUserData();
});
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 20px;
}

.loading-state,
.error-state {
  padding: 20px;
  background: white;
  min-height: 100vh;
}

/* 头部区域 */
.profile-header {
  position: relative;
  background: white;
}

.cover-image {
  height: 200px;
  position: relative;
  overflow: hidden;
}

.cover-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.edit-cover {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.avatar-section {
  padding: 0 16px;
  position: relative;
}

.avatar-wrapper {
  position: relative;
  width: 90px;
  margin-top: -45px;
  margin-bottom: 8px;
  cursor: pointer;
}

.avatar-wrapper :deep(.van-image) {
  border: 4px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.edit-avatar {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 2px solid white;
}

/* 用户信息区域 */
.user-info-section {
  padding: 0 16px 16px;
  background: white;
  margin-bottom: 8px;
}

.user-name-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.nickname {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
}

.username {
  color: #969799;
  font-size: 14px;
  margin: 0 0 12px;
}

/* 个人简介 */
.bio-section {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #f7f8fa;
  padding: 12px;
  border-radius: 8px;
  margin-top: 8px;
}

.bio-text {
  flex: 1;
  margin: 0;
  color: #323233;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.bio-text.empty-bio {
  color: #969799;
}

.edit-icon {
  color: #1989fa;
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
}

.edit-icon:hover {
  opacity: 0.8;
}

/* 账户设置区域 */
.settings-section {
  margin: 12px 0;
}

:deep(.van-cell-group__title) {
  padding-left: 16px;
  padding-right: 16px;
  color: #969799;
  font-size: 14px;
}

:deep(.van-cell-group--inset) {
  margin: 12px 16px;
  border-radius: 12px;
  overflow: hidden;
}

.cell-icon {
  margin-right: 8px;
  color: #1989fa;
  font-size: 18px;
}

/* 危险区域 */
.danger-zone :deep(.van-cell) {
  color: #ee0a24;
}

.danger-text {
  color: #ee0a24 !important;
}

/* 退出登录按钮 */
.logout-button {
  margin: 20px 16px;
}

/* 预测列表 */
.user-predictions {
  background: white;
  padding: 16px;
  margin: 12px 16px;
  border-radius: 12px;
}

.user-predictions.no-settings {
  margin-top: 0;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  color: #323233;
}

.section-title .view-all {
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 2px;
}

.predictions-skeleton {
  padding: 8px 0;
}

.predictions-list {
  margin-top: 8px;
}

.prediction-card {
  padding: 16px 0;
  border-bottom: 1px solid #ebedf0;
  cursor: pointer;
  transition: background 0.2s;
}

.prediction-card:last-child {
  border-bottom: none;
}

.prediction-card:hover {
  background: #f7f8fa;
}

.drug-pair {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 16px;
}

.drug-pair .drug {
  font-weight: 500;
}

.arrow-icon {
  color: #969799;
  font-size: 14px;
}

.prediction-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.prediction-info .time {
  color: #969799;
}

.dialog-content {
  padding: 20px;
}

.password-rule {
  margin-top: 12px;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 8px;
  font-size: 12px;
}

.password-rule p {
  margin: 0 0 8px;
  color: #646566;
}

.password-rule ul {
  margin: 0;
  padding-left: 20px;
  list-style: none;
}

.password-rule li {
  margin-bottom: 4px;
  color: #969799;
  position: relative;
}

.password-rule li::before {
  content: '○';
  position: absolute;
  left: -16px;
  color: #969799;
}

.password-rule li.valid {
  color: #07c160;
}

.password-rule li.valid::before {
  content: '●';
  color: #07c160;
}

.user-predictions {
  background: white;
  padding: 16px 0;
  margin: 12px 16px;
  border-radius: 12px;
  overflow: hidden;
}

.section-title {
  padding: 0 16px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #323233;
}

.predictions-skeleton {
  padding: 16px;
}

.predictions-list {
  padding: 0 16px;
  margin-top: 8px;
}

.prediction-card {
  padding: 16px 0;
  border-bottom: 1px solid #ebedf0;
  transition: background 0.2s;
}

.drug-pair {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 15px;
}

.drug-pair .drug {
  font-weight: 600;
  color: #323233;
}

.drug-pair .se-text {
  color: #e03131;
  font-weight: 500;
}

.arrow-icon {
  color: #969799;
  font-size: 14px;
}

.prediction-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
}

.prediction-info .time {
  color: #969799;
}

.view-more-btn {
  text-align: center;
  padding: 16px 0 4px 0;
  font-size: 13px;
  color: #1989fa;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
}

.view-more-btn:active {
  opacity: 0.7;
}
</style>
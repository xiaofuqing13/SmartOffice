<template>
  <div class="profile-page">
    <el-card class="profile-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <el-icon><User /></el-icon>
            <h3>个人中心</h3>
          </div>
          <span class="sub-title">查看和管理您的个人信息</span>
        </div>
      </template>
      
      <profile-card />
    </el-card>
  </div>
</template>

<script>
import { User } from '@element-plus/icons-vue'
import ProfileCard from '@/components/profile/ProfileCard.vue'

export default {
  name: 'ProfilePage',
  components: {
    User,
    ProfileCard
  }
}
</script>

<style lang="scss" scoped>
.profile-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.profile-card {
  flex: 1;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  }
}

.card-header {
  padding: 8px 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
  
  .el-icon {
    font-size: 22px;
    color: var(--el-color-primary);
    background-color: var(--el-color-primary-light-9);
    border-radius: 50%;
    padding: 8px;
  }
  
  h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.sub-title {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-left: 46px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .profile-page {
    padding: 15px;
  }
}
</style> 
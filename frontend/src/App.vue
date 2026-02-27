<template>
  <div class="app-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <el-icon size="28"><Connection /></el-icon>
          <span class="title">ClawMultiDeploy</span>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="menu"
          background-color="transparent"
          text-color="#b0bcc8"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/instances">
            <el-icon><Box /></el-icon>
            <span>实例管理</span>
          </el-menu-item>
          <el-menu-item index="/backups">
            <el-icon><Folder /></el-icon>
            <span>备份管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container class="main-wrapper" direction="vertical">
        <el-header class="header">
          <div class="header-left">
            <span class="page-title">{{ $route.meta.title || '仪表盘' }}</span>
          </div>
          <div class="header-right">
            <el-tag v-if="store.systemStatus?.docker_running" type="success">Docker 运行中</el-tag>
            <el-tag v-else type="danger">Docker 未运行</el-tag>
          </div>
        </el-header>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useInstanceStore } from './stores/instances'

const store = useInstanceStore()

onMounted(() => {
  store.fetchSystemStatus()
})
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
}
/* 扁平化：卡片无阴影、小圆角、细边框 */
.app-container .el-card {
  border-radius: 4px;
  border: 1px solid var(--el-border-color);
  box-shadow: none;
}
.app-container .el-card__header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}
.app-container .el-card__body {
  padding: 16px;
}
/* 扁平化：按钮、输入框弱化阴影 */
.app-container .el-button {
  border-radius: 4px;
}
.app-container .el-table {
  --el-table-border-color: var(--el-border-color-lighter);
}
.app-container .el-tag {
  border-radius: 2px;
}
.app-container .el-input__wrapper,
.app-container .el-textarea__inner {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
}
.app-container .el-input__wrapper:hover,
.app-container .el-textarea__inner:hover {
  box-shadow: 0 0 0 1px var(--el-border-color-hover) inset;
}
.app-container .el-dialog {
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
</style>

<style scoped>
.app-container {
  height: 100vh;
  min-height: 100%;
}

.app-container :deep(.el-container) {
  height: 100%;
  min-height: 0;
}

.main-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.sidebar {
  background: #37474f;
  height: 100%;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
}

.logo {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  padding: 0 16px;
}

.logo .el-icon {
  font-size: 22px;
  opacity: 0.9;
}

.logo .title {
  margin-left: 10px;
  font-size: 14px;
  font-weight: 600;
}

.menu {
  border-right: none;
  height: calc(100% - 52px);
  padding: 6px 0;
}

.menu :deep(.el-menu-item) {
  margin: 0 8px;
  border-radius: 0;
  height: 42px;
  line-height: 42px;
}

.menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.1);
  color: #81d4fa;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
  height: 48px;
}

.page-title {
  font-size: 15px;
  font-weight: 600;
  color: #212121;
}

.main-content {
  flex: 1;
  min-height: 0;
  background: #fafafa;
  padding: 16px 20px;
  overflow-y: auto;
}
</style>

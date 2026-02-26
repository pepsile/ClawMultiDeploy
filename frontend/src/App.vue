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
          background-color="#304156"
          text-color="#bfcbd9"
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
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <span class="page-title">{{ $route.meta.title || '仪表盘' }}</span>
          </div>
          <div class="header-right">
            <el-tag v-if="systemStatus?.docker_running" type="success">Docker 运行中</el-tag>
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

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #1f2d3d;
}

.logo .title {
  margin-left: 10px;
  font-size: 16px;
  font-weight: bold;
}

.menu {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.page-title {
  font-size: 18px;
  font-weight: 500;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>

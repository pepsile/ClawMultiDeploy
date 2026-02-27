<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon blue">
              <el-icon size="36"><Box /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ instanceCount }}</div>
              <div class="stat-label">实例总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon green">
              <el-icon size="36"><VideoPlay /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ runningCount }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon orange">
              <el-icon size="36"><VideoPause /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stoppedCount }}</div>
              <div class="stat-label">已停止</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon purple">
              <el-icon size="36"><Folder /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ backups.length }}</div>
              <div class="stat-label">备份数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card class="quick-actions">
      <template #header>
        <div class="card-header">
          <span>快捷操作</span>
        </div>
      </template>
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="$router.push('/instances')">
          <el-icon><Plus /></el-icon>
          创建实例
        </el-button>
        <el-button type="success" size="large" @click="handleBackup">
          <el-icon><Folder /></el-icon>
          创建备份
        </el-button>
      </div>
    </el-card>

    <!-- 系统状态 -->
    <el-card class="system-card">
      <template #header>
        <div class="card-header">
          <span>系统状态</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Docker 状态">
          <el-tag v-if="systemStatus?.docker_running" type="success">运行中</el-tag>
          <el-tag v-else type="danger">未运行</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="基础端口">{{ systemStatus?.base_port || 18789 }}</el-descriptions-item>
        <el-descriptions-item label="运行实例">{{ systemStatus?.running_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="总实例数">{{ systemStatus?.instance_count || 0 }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useInstanceStore } from '../stores/instances'
import { ElMessage } from 'element-plus'

const store = useInstanceStore()

const instanceCount = computed(() => store.instanceCount)
const runningCount = computed(() => store.runningCount)
const stoppedCount = computed(() => store.stoppedCount)
const systemStatus = computed(() => store.systemStatus)
const backups = computed(() => store.backups)

onMounted(() => {
  store.fetchInstances()
  store.fetchSystemStatus()
  store.fetchBackups()
})

const handleBackup = async () => {
  try {
    await store.createBackup()
    ElMessage.success('备份创建成功')
  } catch (error) {
    ElMessage.error('备份创建失败')
  }
}
</script>

<style scoped>
.stat-card {
  cursor: pointer;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px;
}

.stat-icon.blue {
  background: #e3f2fd;
  color: #1976d2;
}

.stat-icon.green {
  background: #e8f5e9;
  color: #388e3c;
}

.stat-icon.orange {
  background: #fff3e0;
  color: #f57c00;
}

.stat-icon.purple {
  background: #f3e5f5;
  color: #7b1fa2;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #212121;
}

.stat-label {
  font-size: 13px;
  color: #757575;
  margin-top: 2px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-row {
  margin-bottom: 20px;
}
.stat-row .el-col {
  margin-bottom: 20px;
}
.quick-actions,
.system-card {
  margin-top: 20px;
}
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>

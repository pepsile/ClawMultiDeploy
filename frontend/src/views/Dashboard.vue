<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon blue">
              <el-icon size="40"><Box /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ instanceCount }}</div>
              <div class="stat-label">实例总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon green">
              <el-icon size="40"><VideoPlay /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ runningCount }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon orange">
              <el-icon size="40"><VideoPause /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stoppedCount }}</div>
              <div class="stat-label">已停止</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon purple">
              <el-icon size="40"><Folder /></el-icon>
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
    <el-card class="quick-actions" style="margin-top: 20px;">
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
    <el-card style="margin-top: 20px;">
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
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-icon.blue {
  background-color: #ecf5ff;
  color: #409eff;
}

.stat-icon.green {
  background-color: #f0f9eb;
  color: #67c23a;
}

.stat-icon.orange {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.stat-icon.purple {
  background-color: #f5f0ff;
  color: #9254de;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.action-buttons {
  display: flex;
  gap: 15px;
}
</style>

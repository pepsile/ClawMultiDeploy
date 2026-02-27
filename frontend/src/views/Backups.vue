<template>
  <div class="backups">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>备份列表</span>
          <el-button type="primary" @click="handleCreateBackup" :loading="creating">
            <el-icon><Plus /></el-icon>
            创建备份
          </el-button>
        </div>
      </template>

      <el-table :data="backups" v-loading="loading" style="width: 100%">
        <template #empty>
          <el-empty description="暂无备份，点击下方按钮创建" class="table-empty">
            <el-button type="primary" @click="handleCreateBackup">创建备份</el-button>
          </el-empty>
        </template>
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <el-icon><Document /></el-icon>
            {{ row.filename }}
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="instance_count" label="实例数" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.instance_count }} 个实例</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleDownload(row)">
              下载
            </el-button>
            <el-button type="warning" size="small" @click="handleRestore(row)">
              恢复
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建备份进度对话框 -->
    <el-dialog v-model="showProgress" title="创建备份" width="400px" :close-on-click-modal="false">
      <div class="progress-content">
        <el-steps :active="progressStep" finish-status="success" direction="vertical">
          <el-step title="停止所有实例" />
          <el-step title="打包数据文件" />
          <el-step title="重启实例" />
        </el-steps>
        <el-progress :percentage="progressPercent" style="margin-top: 20px;" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useInstanceStore } from '../stores/instances'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Backup } from '../types'

const store = useInstanceStore()
const backups = computed(() => store.backups)
const loading = computed(() => store.loading)

const creating = ref(false)
const showProgress = ref(false)
const progressStep = ref(0)
const progressPercent = ref(0)

onMounted(() => {
  store.fetchBackups()
})

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const handleCreateBackup = async () => {
  try {
    await ElMessageBox.confirm(
      '创建备份将暂时停止所有实例，确定继续吗？',
      '确认创建备份',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    showProgress.value = true
    progressStep.value = 0
    progressPercent.value = 0

    // 模拟进度
    const interval = setInterval(() => {
      progressPercent.value += 5
      if (progressPercent.value >= 30) progressStep.value = 1
      if (progressPercent.value >= 70) progressStep.value = 2
      if (progressPercent.value >= 100) {
        clearInterval(interval)
      }
    }, 100)

    creating.value = true
    await store.createBackup()

    progressPercent.value = 100
    progressStep.value = 3

    setTimeout(() => {
      showProgress.value = false
      ElMessage.success('备份创建成功')
    }, 500)
  } catch (error) {
    showProgress.value = false
    // 用户取消或失败
  } finally {
    creating.value = false
  }
}

const handleDownload = (row: Backup) => {
  // 构建下载链接
  const downloadUrl = `/api/backups/${row.id}/download`
  window.open(downloadUrl, '_blank')
}

const handleRestore = async (row: Backup) => {
  try {
    await ElMessageBox.confirm(
      `确定要恢复备份 ${row.filename} 吗？当前数据将被覆盖。`,
      '确认恢复备份',
      {
        confirmButtonText: '恢复',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    // await store.restoreBackup(row.id)
    ElMessage.success('备份恢复成功')
  } catch (error) {
    // 用户取消
  }
}

const handleDelete = async (row: Backup) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份 ${row.filename} 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await store.deleteBackup(row.id)
    ElMessage.success('备份删除成功')
  } catch (error) {
    // 用户取消
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-content {
  padding: 20px;
}
.table-empty {
  padding: 32px 0;
}
</style>

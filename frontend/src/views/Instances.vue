<template>
  <div class="instances">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>实例列表</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建实例
          </el-button>
        </div>
      </template>

      <el-table :data="instances" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="实例ID" width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/instances/${row.id}`)">
              {{ row.id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="port" label="端口" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.port }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== 'running'"
              type="success"
              size="small"
              @click="handleStart(row)"
              :loading="actionLoading[row.id]"
            >
              启动
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              type="warning"
              size="small"
              @click="handleStop(row)"
              :loading="actionLoading[row.id]"
            >
              停止
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="handleInit(row)"
              :loading="actionLoading[row.id]"
            >
              初始化
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建实例对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建新实例"
      width="500px"
    >
      <el-form :model="createForm" label-width="100px" :rules="createRules" ref="createFormRef">
        <el-form-item label="实例ID" prop="id">
          <el-input v-model="createForm.id" placeholder="如: zhangsan (英文/数字/下划线)" />
        </el-form-item>
        <el-form-item label="显示名称" prop="name">
          <el-input v-model="createForm.name" placeholder="如: 张三" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 初始化输出对话框 -->
    <el-dialog
      v-model="showInitDialog"
      title="实例初始化"
      width="700px"
    >
      <div class="init-output">
        <pre>{{ initOutput }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { useInstanceStore } from '../stores/instances'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Instance } from '../types'

const store = useInstanceStore()
const instances = computed(() => store.instances)
const loading = computed(() => store.loading)

const showCreateDialog = ref(false)
const showInitDialog = ref(false)
const creating = ref(false)
const initOutput = ref('')
const actionLoading = reactive<Record<string, boolean>>({})

const createForm = reactive({
  id: '',
  name: ''
})

const createFormRef = ref()

const createRules = {
  id: [
    { required: true, message: '请输入实例ID', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含英文、数字、下划线和横线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ]
}

onMounted(() => {
  store.fetchInstances()
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    created: 'info',
    running: 'success',
    stopped: 'warning',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    created: '已创建',
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return map[status] || status
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const handleCreate = async () => {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await store.createInstance(createForm.id, createForm.name)
    ElMessage.success('实例创建成功')
    showCreateDialog.value = false
    createForm.id = ''
    createForm.name = ''
  } catch (error) {
    ElMessage.error('实例创建失败')
  } finally {
    creating.value = false
  }
}

const handleStart = async (row: Instance) => {
  actionLoading[row.id] = true
  try {
    await store.startInstance(row.id)
    ElMessage.success('实例启动成功')
  } catch (error) {
    ElMessage.error('实例启动失败')
  } finally {
    actionLoading[row.id] = false
  }
}

const handleStop = async (row: Instance) => {
  actionLoading[row.id] = true
  try {
    await store.stopInstance(row.id)
    ElMessage.success('实例停止成功')
  } catch (error) {
    ElMessage.error('实例停止失败')
  } finally {
    actionLoading[row.id] = false
  }
}

const handleInit = async (row: Instance) => {
  actionLoading[row.id] = true
  initOutput.value = '正在初始化...'
  showInitDialog.value = true
  try {
    const res = await store.initInstance(row.id)
    initOutput.value = res.data.data.result || '初始化完成'
  } catch (error) {
    initOutput.value = '初始化失败: ' + error
  } finally {
    actionLoading[row.id] = false
  }
}

const handleDelete = async (row: Instance) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除实例 ${row.name} (${row.id}) 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await store.deleteInstance(row.id)
    ElMessage.success('实例删除成功')
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

.init-output {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}

.init-output pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', monospace;
  font-size: 13px;
}
</style>

<template>
  <div class="instance-detail">
    <el-page-header @back="$router.push('/instances')" :title="`实例: ${instance?.name}`" />

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <!-- 配置编辑器 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>OpenClaw 配置 (openclaw.json)</span>
              <div>
                <el-button @click="loadConfig">刷新</el-button>
                <el-button type="primary" @click="saveConfig" :loading="saving">保存</el-button>
              </div>
            </div>
          </template>
          <div class="editor-container">
            <textarea ref="editorRef" v-model="configContent" class="config-editor"></textarea>
          </div>
          <el-alert
            v-if="configError"
            :title="configError"
            type="error"
            :closable="false"
            style="margin-top: 10px;"
          />
        </el-card>
      </el-col>

      <el-col :span="8">
        <!-- 实例信息 -->
        <el-card>
          <template #header>
            <span>实例信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="ID">{{ instance?.id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ instance?.name }}</el-descriptions-item>
            <el-descriptions-item label="端口">{{ instance?.port }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(instance?.status)">
                {{ getStatusText(instance?.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="访问地址">
              <el-link :href="`http://localhost:${instance?.port}`" target="_blank" type="primary">
                http://localhost:{{ instance?.port }}
              </el-link>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(instance?.created_at) }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="action-buttons" style="margin-top: 15px;">
            <el-button
              v-if="instance?.status !== 'running'"
              type="success"
              @click="handleStart"
              :loading="actionLoading"
            >
              启动
            </el-button>
            <el-button
              v-if="instance?.status === 'running'"
              type="warning"
              @click="handleStop"
              :loading="actionLoading"
            >
              停止
            </el-button>
            <el-button @click="showLogs = true">查看日志</el-button>
          </div>
        </el-card>

        <!-- 快速帮助 -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <span>配置说明</span>
          </template>
          <el-collapse>
            <el-collapse-item title="gateway 配置">
              <p>gateway.mode: 运行模式 (local/server)</p>
              <p>gateway.token: 访问令牌</p>
              <p>gateway.port: 内部端口 (保持 18789)</p>
            </el-collapse-item>
            <el-collapse-item title="agents 配置">
              <p>配置智能体默认行为和模型</p>
            </el-collapse-item>
            <el-collapse-item title="channels 配置">
              <p>配置消息渠道 (WhatsApp/Telegram/Discord)</p>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>

    <!-- 日志对话框 -->
    <el-dialog v-model="showLogs" title="实例日志" width="800px">
      <div class="logs-container">
        <pre>{{ logs }}</pre>
      </div>
      <template #footer>
        <el-button @click="showLogs = false">关闭</el-button>
        <el-button type="primary" @click="fetchLogs">刷新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useInstanceStore } from '../stores/instances'
import { ElMessage } from 'element-plus'
import type { Instance } from '../types'

const route = useRoute()
const store = useInstanceStore()
const instanceId = route.params.id as string

const instance = computed(() =>
  store.instances.find(i => i.id === instanceId)
)

const configContent = ref('')
const configError = ref('')
const saving = ref(false)
const actionLoading = ref(false)
const showLogs = ref(false)
const logs = ref('日志加载中...')

onMounted(() => {
  store.fetchInstances()
  loadConfig()
})

const loadConfig = async () => {
  try {
    configContent.value = await store.getInstanceConfig(instanceId)
    configError.value = ''
  } catch (error) {
    configError.value = '加载配置失败'
  }
}

const saveConfig = async () => {
  // 简单验证 JSON5 语法
  try {
    JSON.parse(configContent.value)
  } catch (e) {
    configError.value = 'JSON 格式错误: ' + (e as Error).message
    return
  }

  saving.value = true
  try {
    await store.updateInstanceConfig(instanceId, configContent.value)
    ElMessage.success('配置保存成功')
    configError.value = ''
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

const handleStart = async () => {
  actionLoading.value = true
  try {
    await store.startInstance(instanceId)
    ElMessage.success('实例启动成功')
  } catch (error) {
    ElMessage.error('实例启动失败')
  } finally {
    actionLoading.value = false
  }
}

const handleStop = async () => {
  actionLoading.value = true
  try {
    await store.stopInstance(instanceId)
    ElMessage.success('实例停止成功')
  } catch (error) {
    ElMessage.error('实例停止失败')
  } finally {
    actionLoading.value = false
  }
}

const fetchLogs = async () => {
  // 这里可以实现 WebSocket 实时日志
  logs.value = '实时日志功能需要 WebSocket 连接'
}

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    created: 'info',
    running: 'success',
    stopped: 'warning',
    error: 'danger'
  }
  return map[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    created: '已创建',
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return map[status || ''] || status
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.config-editor {
  width: 100%;
  min-height: 400px;
  padding: 15px;
  border: none;
  background-color: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
}

.config-editor:focus {
  outline: none;
}

.logs-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
}

.logs-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', monospace;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}
</style>

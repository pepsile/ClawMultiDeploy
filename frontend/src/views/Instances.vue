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

      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="control-tip"
      >
        连接控制台请使用「控制台」或「复制令牌链接」打开带 token 的地址；直接访问
        <code>http://主机:端口</code>
        会提示 “gateway password missing”，需在地址后加
        <code>?token=令牌</code>
        或使用上方按钮获取。
      </el-alert>

      <el-table :data="instances" v-loading="loading" style="width: 100%" class="instances-table">
        <template #empty>
          <el-empty description="暂无实例，点击下方按钮创建" class="table-empty">
            <el-button type="primary" @click="showCreateDialog = true">创建实例</el-button>
          </el-empty>
        </template>
        <el-table-column prop="id" label="实例ID" width="140">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push(`/instances/${row.id}`)">
              {{ row.id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column prop="port" label="端口" width="88">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.port }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small" round>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right" class-name="actions-column">
          <template #default="{ row }">
            <div class="table-actions">
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
                v-if="row.status === 'running'"
                type="info"
                size="small"
                plain
                @click="openGateway(row)"
              >
                控制台
              </el-button>
              <el-button
                type="primary"
                size="small"
                plain
                @click="handleInit(row)"
                :loading="actionLoading[row.id]"
              >
                初始化
              </el-button>
              <el-dropdown trigger="click" @command="(cmd: string) => handleMoreCommand(cmd, row)">
                <el-button size="small" plain>
                  更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="copyToken">
                      <el-icon><CopyDocument /></el-icon>
                      复制令牌链接
                    </el-dropdown-item>
                    <el-dropdown-item command="regenToken">
                      <el-icon><RefreshRight /></el-icon>
                      重新生成令牌
                    </el-dropdown-item>
                    <el-dropdown-item command="config">
                      <el-icon><Edit /></el-icon>
                      配置文件
                    </el-dropdown-item>
                    <el-dropdown-item command="logs">
                      <el-icon><Document /></el-icon>
                      实例日志
                    </el-dropdown-item>
                    <el-dropdown-item v-if="row.status === 'running'" command="devices">
                      <el-icon><Connection /></el-icon>
                      设备配对
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      <span class="danger-text">删除实例</span>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
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
      <el-form :model="createForm" label-width="110px" :rules="createRules" ref="createFormRef">
        <el-form-item label="实例ID" prop="id">
          <el-input v-model="createForm.id" placeholder="如: zhangsan (英文/数字/下划线)" />
        </el-form-item>
        <el-form-item label="显示名称" prop="name">
          <el-input v-model="createForm.name" placeholder="如: 张三" />
        </el-form-item>
        <el-form-item label="网关密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            show-password
            placeholder="用于控制台登录，请牢记"
            autocomplete="new-password"
          />
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

    <!-- 实例日志对话框 -->
    <InstanceLogsDialog v-model="showLogsDialog" :instance-id="logsInstanceId" />

    <!-- 配置文件编辑对话框 -->
    <el-dialog
      v-model="showConfigDialog"
      :title="`配置文件 · ${configInstanceName} (openclaw.json)`"
      width="720px"
      class="config-dialog"
      destroy-on-close
      @open="loadConfigContent"
      @closed="configContent = ''; configError = ''"
    >
      <div v-loading="configLoading" class="config-dialog-body">
        <el-input
          v-model="configContent"
          type="textarea"
          :rows="18"
          placeholder="加载中..."
          class="config-textarea"
          spellcheck="false"
        />
        <el-alert v-if="configError" :title="configError" type="error" :closable="false" show-icon class="config-error" />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showConfigDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConfigContent" :loading="configSaving">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 设备配对对话框：解决 pairing required -->
    <el-dialog
      v-model="showDevicesDialog"
      :title="`设备配对 · ${devicesInstanceName}`"
      width="560px"
      @open="loadDevices"
    >
      <el-alert type="info" :closable="false" show-icon class="devices-tip">
        从非本机（如手机、另一台电脑）连接控制台时需在此批准设备，否则会提示「pairing required」。
      </el-alert>
      <div v-loading="devicesLoading" class="devices-content">
        <template v-if="pendingList.length">
          <div class="devices-section">
            <div class="section-title">待批准</div>
            <el-table :data="pendingList" size="small" max-height="200">
              <el-table-column label="请求 ID" prop="requestId" min-width="180">
                <template #default="{ row }">
                  {{ row.requestId || row.id || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="90">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    size="small"
                    :loading="approvingId === (row.requestId || row.id)"
                    @click="handleApprove(row)"
                  >
                    批准
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
        <template v-else-if="!devicesLoading">
          <el-empty description="暂无待批准设备" />
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { useInstanceStore } from '../stores/instances'
import { getGatewayToken, getInstanceDevices, approveDevice, regenerateGatewayToken } from '../api/instances'
import { ElMessage, ElMessageBox } from 'element-plus'
import JSON5 from 'json5'
import type { Instance } from '../types'
import InstanceLogsDialog from '../components/InstanceLogsDialog.vue'

const store = useInstanceStore()
const instances = computed(() => store.instances)
const loading = computed(() => store.loading)

const showCreateDialog = ref(false)
const showInitDialog = ref(false)
const showLogsDialog = ref(false)
const logsInstanceId = ref('')
const showDevicesDialog = ref(false)
const devicesInstanceId = ref('')
const devicesInstanceName = ref('')
const devicesData = ref<Record<string, unknown>>({})
const devicesLoading = ref(false)
const approvingId = ref('')
const showConfigDialog = ref(false)
const configInstanceId = ref('')
const configInstanceName = ref('')
const configContent = ref('')
const configError = ref('')
const configLoading = ref(false)
const configSaving = ref(false)
const creating = ref(false)
const initOutput = ref('')
const actionLoading = reactive<Record<string, boolean>>({})

const openLogs = (instanceId: string) => {
  logsInstanceId.value = instanceId
  showLogsDialog.value = true
}

const openDevicesDialog = (row: Instance) => {
  devicesInstanceId.value = row.id
  devicesInstanceName.value = row.name
  showDevicesDialog.value = true
}

const pendingList = computed(() => {
  const d = devicesData.value
  const arr =
    (d?.pending as unknown[]) ||
    (d?.pendingRequests as unknown[]) ||
    (d?.pending_requests as unknown[]) ||
    (Array.isArray(d) ? d : [])
  return arr.map((item: any) => ({
    ...item,
    requestId: item?.requestId ?? item?.id ?? item?.request_id,
  }))
})

async function loadDevices() {
  if (!devicesInstanceId.value) return
  devicesLoading.value = true
  try {
    const res = await getInstanceDevices(devicesInstanceId.value)
    devicesData.value = (res.data as any)?.data ?? {}
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '获取设备列表失败')
    devicesData.value = {}
  } finally {
    devicesLoading.value = false
  }
}

async function handleApprove(row: { requestId?: string; id?: string; request_id?: string }) {
  const rid = row.requestId ?? row.id ?? row.request_id
  if (!rid || !devicesInstanceId.value) return
  approvingId.value = rid
  try {
    await approveDevice(devicesInstanceId.value, rid)
    ElMessage.success('已批准，设备可重新连接控制台')
    await loadDevices()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '批准失败')
  } finally {
    approvingId.value = ''
  }
}

function buildTokenUrl(row: Instance, token: string | null) {
  const base = `http://${window.location.hostname}:${row.port}`
  return token ? `${base}/?token=${encodeURIComponent(token)}` : base
}

function handleMoreCommand(cmd: string, row: Instance) {
  switch (cmd) {
    case 'copyToken':
      copyTokenUrl(row)
      break
    case 'regenToken':
      handleRegenerateToken(row)
      break
    case 'config':
      openConfigDialog(row)
      break
    case 'logs':
      openLogs(row.id)
      break
    case 'devices':
      openDevicesDialog(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

function openConfigDialog(row: Instance) {
  configInstanceId.value = row.id
  configInstanceName.value = row.name
  showConfigDialog.value = true
}

async function loadConfigContent() {
  if (!configInstanceId.value) return
  configLoading.value = true
  configError.value = ''
  try {
    configContent.value = await store.getInstanceConfig(configInstanceId.value)
  } catch {
    configError.value = '加载配置失败'
    configContent.value = ''
  } finally {
    configLoading.value = false
  }
}

async function saveConfigContent() {
  if (!configInstanceId.value) return
  try {
    JSON5.parse(configContent.value)
  } catch (e) {
    configError.value = 'JSON/JSON5 格式错误: ' + (e as Error).message
    return
  }
  configSaving.value = true
  configError.value = ''
  try {
    await store.updateInstanceConfig(configInstanceId.value, configContent.value)
    ElMessage.success('配置已保存，实例重启后将生效')
    showConfigDialog.value = false
  } catch {
    configError.value = '保存失败'
  } finally {
    configSaving.value = false
  }
}

const openGateway = async (row: Instance) => {
  try {
    const res = await getGatewayToken(row.id)
    const token = res.data?.data?.token
    const url = buildTokenUrl(row, token)
    window.open(url, '_blank', 'noopener,noreferrer')
    if (!token) ElMessage.warning('未找到令牌，请点击「重新生成令牌」或配置 gateway.auth.token')
  } catch {
    window.open(buildTokenUrl(row, null), '_blank', 'noopener,noreferrer')
    ElMessage.warning('获取令牌失败')
  }
}

const copyTokenUrl = async (row: Instance) => {
  try {
    const res = await getGatewayToken(row.id)
    const token = res.data?.data?.token
    const url = buildTokenUrl(row, token)
    await navigator.clipboard.writeText(url)
    ElMessage.success(token ? '令牌链接已复制到剪贴板' : '当前无令牌，已复制控制台地址，请先「重新生成令牌」')
  } catch {
    ElMessage.warning('复制失败')
  }
}

const handleRegenerateToken = async (row: Instance) => {
  const key = `regen-${row.id}`
  actionLoading[key] = true
  try {
    const res = await regenerateGatewayToken(row.id)
    const token = (res.data as any)?.data?.token
    const port = (res.data as any)?.data?.port ?? row.port
    const url = token
      ? `http://${window.location.hostname}:${port}/?token=${encodeURIComponent(token)}`
      : ''
    if (url) {
      await navigator.clipboard.writeText(url)
      ElMessage.success('新令牌已生成并已复制链接。请重启实例后使用新链接连接（可解决「too many failed attempts」）')
    } else {
      ElMessage.success('令牌已重新生成，请重启实例后在「复制令牌链接」中获取新链接')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '重新生成令牌失败')
  } finally {
    actionLoading[key] = false
  }
}

const createForm = reactive({
  id: '',
  name: '',
  password: ''
})

const createFormRef = ref()

const createRules = {
  id: [
    { required: true, message: '请输入实例ID', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含英文、数字、下划线和横线', trigger: 'blur' },
    { pattern: /.*[a-zA-Z].*/, message: '实例ID不能为纯数字，请至少包含一个字母', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入网关密码（用于控制台登录）', trigger: 'blur' },
    { min: 1, message: '密码不能为空', trigger: 'blur' }
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
    const res = await store.createInstance(createForm.id, createForm.name, createForm.password)
    showCreateDialog.value = false
    createForm.id = ''
    createForm.name = ''
    createForm.password = ''
    const instance = res?.data?.instance
    const gatewayToken = res?.data?.gateway_token
    if (instance && gatewayToken) {
      const url = `http://${window.location.hostname}:${instance.port}/?token=${encodeURIComponent(gatewayToken)}`
      try {
        await navigator.clipboard.writeText(url)
        ElMessage.success('实例创建成功，带令牌的控制台链接已复制到剪贴板')
      } catch {
        ElMessageBox.alert(
          `实例创建成功。请保存此链接（含令牌，仅显示一次）：\n\n${url}`,
          '控制台链接',
          { confirmButtonText: '知道了' }
        )
      }
    } else {
      ElMessage.success('实例创建成功')
    }
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
    const tip = row.status === 'running'
      ? `实例正在运行，将先停止并删除容器，再删除实例数据。确定要删除 ${row.name} (${row.id}) 吗？此操作不可恢复。`
      : `确定要删除实例 ${row.name} (${row.id}) 吗？此操作不可恢复。`
    await ElMessageBox.confirm(
      tip,
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

.control-tip {
  margin-bottom: 12px;
  border-radius: 4px;
}
.control-tip code {
  padding: 0 4px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 2px;
  font-size: 12px;
}

.devices-tip {
  margin-bottom: 12px;
}
.devices-content {
  min-height: 80px;
}
.devices-section {
  margin-top: 8px;
}
.section-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 13px;
}

.init-output {
  background: #263238;
  color: #b0bec5;
  padding: 12px 16px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
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

.table-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.table-actions .el-dropdown {
  margin-left: 2px;
}
.danger-text {
  color: var(--el-color-danger);
}
.table-empty {
  padding: 32px 0;
}
.instances-table :deep(.el-table__empty-block) {
  width: 100%;
}

.config-dialog-body {
  min-height: 200px;
}
.config-textarea {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
}
.config-textarea :deep(textarea) {
  font-family: inherit;
}
.config-error {
  margin-top: 10px;
}
</style>

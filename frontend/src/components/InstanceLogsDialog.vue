<template>
  <el-dialog
    :model-value="modelValue"
    :title="`实例日志 · ${instanceId || ''}`"
    width="85%"
    max-width="900px"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
    @closed="disconnect"
  >
    <div class="logs-wrapper">
      <div ref="logContainerRef" class="logs-container">
        <pre>{{ logText }}</pre>
      </div>
      <div v-if="wsStatus" class="logs-status">
        {{ wsStatus }}
      </div>
    </div>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">关闭</el-button>
      <el-button v-if="!connected" type="primary" @click="connect" :loading="connecting">
        重新连接
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    instanceId: string
  }>(),
  { modelValue: false, instanceId: '' }
)
const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()

const logText = ref('')
const logContainerRef = ref<HTMLElement | null>(null)
const wsStatus = ref('')
const connected = ref(false)
const connecting = ref(false)
let ws: WebSocket | null = null

function getWsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/api/instances/${props.instanceId}/logs`
}

function connect() {
  if (!props.instanceId) return
  ws?.close()
  ws = null
  connected.value = false
  connecting.value = true
  wsStatus.value = '正在连接…'
  logText.value = ''

  try {
    const url = getWsUrl()
    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      connecting.value = false
      wsStatus.value = '已连接，实时输出中'
      logText.value = '(等待容器日志…)\n'
    }

    ws.onmessage = (event) => {
      const line = typeof event.data === 'string' ? event.data : ''
      logText.value += line + (line.endsWith('\n') ? '' : '\n')
      nextTick(() => scrollToBottom())
    }

    ws.onerror = () => {
      wsStatus.value = '连接异常'
      connecting.value = false
    }

    ws.onclose = () => {
      connected.value = false
      connecting.value = false
      if (wsStatus.value === '正在连接…' || wsStatus.value === '已连接，实时输出中') {
        wsStatus.value = '连接已关闭'
      }
      ws = null
    }
  } catch (e) {
    wsStatus.value = '连接失败: ' + (e as Error).message
    connecting.value = false
  }
}

function scrollToBottom() {
  const el = logContainerRef.value
  if (el) el.scrollTop = el.scrollHeight
}

function disconnect() {
  ws?.close()
  ws = null
  connected.value = false
  connecting.value = false
  wsStatus.value = ''
}

watch(
  () => [props.modelValue, props.instanceId] as const,
  ([visible, id]) => {
    if (visible && id) {
      connect()
    } else {
      disconnect()
    }
  }
)

</script>

<style scoped>
.logs-wrapper {
  min-height: 320px;
}

.logs-container {
  background-color: #1e1e1e;
  color: #e0e0e0;
  padding: 12px 16px;
  border-radius: 6px;
  max-height: 70vh;
  overflow-y: auto;
}

.logs-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.logs-status {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>

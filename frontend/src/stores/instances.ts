import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Instance, Backup, SystemStatus } from '../types'
import {
  getInstances as apiGetInstances,
  createInstance as apiCreateInstance,
  deleteInstance as apiDeleteInstance,
  startInstance as apiStartInstance,
  stopInstance as apiStopInstance,
  initInstance as apiInitInstance,
  getInstanceConfig as apiGetInstanceConfig,
  updateInstanceConfig as apiUpdateInstanceConfig
} from '../api/instances'
import {
  getBackups as apiGetBackups,
  createBackup as apiCreateBackup,
  deleteBackup as apiDeleteBackup
} from '../api/backups'
import { getSystemStatus as apiGetSystemStatus } from '../api/system'

export const useInstanceStore = defineStore('instances', () => {
  // State
  const instances = ref<Instance[]>([])
  const backups = ref<Backup[]>([])
  const systemStatus = ref<SystemStatus | null>(null)
  const loading = ref(false)

  // Getters
  const instanceCount = computed(() => instances.value.length)
  const runningCount = computed(() =>
    instances.value.filter(i => i.status === 'running').length
  )
  const stoppedCount = computed(() =>
    instances.value.filter(i => i.status === 'stopped').length
  )

  // Actions
  async function fetchInstances() {
    loading.value = true
    try {
      const res = await apiGetInstances()
      instances.value = res.data.data.instances
    } finally {
      loading.value = false
    }
  }

  async function createInstance(id: string, name: string) {
    const res = await apiCreateInstance(id, name)
    await fetchInstances()
    return res.data
  }

  async function deleteInstance(id: string, keepData: boolean = false) {
    await apiDeleteInstance(id, keepData)
    await fetchInstances()
  }

  async function startInstance(id: string) {
    await apiStartInstance(id)
    await fetchInstances()
  }

  async function stopInstance(id: string) {
    await apiStopInstance(id)
    await fetchInstances()
  }

  async function initInstance(id: string) {
    return await apiInitInstance(id)
  }

  async function getInstanceConfig(id: string) {
    const res = await apiGetInstanceConfig(id)
    return res.data.data.content
  }

  async function updateInstanceConfig(id: string, content: string) {
    await apiUpdateInstanceConfig(id, content)
  }

  async function fetchBackups() {
    const res = await apiGetBackups()
    backups.value = res.data.data.backups
  }

  async function createBackup() {
    await apiCreateBackup()
    await fetchBackups()
  }

  async function deleteBackup(id: number) {
    await apiDeleteBackup(id)
    await fetchBackups()
  }

  async function fetchSystemStatus() {
    const res = await apiGetSystemStatus()
    systemStatus.value = res.data.data.status
  }

  return {
    instances,
    backups,
    systemStatus,
    loading,
    instanceCount,
    runningCount,
    stoppedCount,
    fetchInstances,
    createInstance,
    deleteInstance,
    startInstance,
    stopInstance,
    initInstance,
    getInstanceConfig,
    updateInstanceConfig,
    fetchBackups,
    createBackup,
    deleteBackup,
    fetchSystemStatus
  }
})

// 类型定义

export interface Instance {
  id: string
  name: string
  port: number
  status: 'created' | 'running' | 'stopped' | 'error'
  created_at: string
  updated_at: string
}

export interface Backup {
  id: number
  filename: string
  size: number
  instance_count: number
  created_at: string
}

export interface SystemStatus {
  docker_running: boolean
  base_port: number
  instance_count: number
  running_count: number
}

export interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
}

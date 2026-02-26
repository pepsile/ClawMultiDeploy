import request from './request'
import type { ApiResponse } from '../types'

export const getSystemStatus = () => {
  return request.get<ApiResponse>('/system/status')
}

export const getAvailablePorts = () => {
  return request.get<ApiResponse>('/system/ports')
}
